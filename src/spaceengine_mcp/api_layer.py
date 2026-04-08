"""
REST API Layer — Electron 프론트엔드를 위한 HTTP 엔드포인트.

MCP SSE transport 위에 추가적인 편의 API를 제공합니다:
- GET  /health             — 서버 상태 확인
- GET  /api/tools          — 사용 가능한 도구 목록
- POST /api/tools/execute  — 도구 실행
- GET  /api/resources      — 사용 가능한 리소스 목록
- GET  /api/prompts        — 사용 가능한 프롬프트 목록

이 모듈은 FastMCP의 SSE Starlette 앱에 추가 라우트를 마운트합니다.
"""

import json
import asyncio
import traceback
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


def create_api_app(mcp_instance) -> Starlette:
    """
    FastMCP 인스턴스의 SSE 앱에 REST API 엔드포인트를 추가하여 반환.
    """
    # MCP 서버 내부 참조
    server = mcp_instance._mcp_server

    async def health(request: Request) -> JSONResponse:
        """서버 상태 확인"""
        from spaceengine_mcp import __version__
        return JSONResponse({
            "status": "ok",
            "server": "spaceengine-mcp",
            "version": __version__,
            "transport": "sse",
            "tools_count": len(mcp_instance._tool_manager._tools),
        })

    async def list_tools(request: Request) -> JSONResponse:
        """등록된 도구 목록 (Ollama function calling 포맷 포함)"""
        tools = []
        for name, tool in mcp_instance._tool_manager._tools.items():
            tool_info = {
                "name": name,
                "description": tool.description or "",
            }
            # input schema가 있으면 포함
            if hasattr(tool, 'parameters') and tool.parameters:
                tool_info["parameters"] = tool.parameters
            elif hasattr(tool, 'fn'):
                # 함수 시그니처에서 파라미터 추출 시도
                import inspect
                sig = inspect.signature(tool.fn)
                params = {}
                for pname, param in sig.parameters.items():
                    if pname == 'self':
                        continue
                    p_info = {"type": "string"}
                    if param.annotation != inspect.Parameter.empty:
                        ann = str(param.annotation)
                        if 'float' in ann:
                            p_info["type"] = "number"
                        elif 'int' in ann:
                            p_info["type"] = "integer"
                        elif 'bool' in ann:
                            p_info["type"] = "boolean"
                        elif 'list' in ann:
                            p_info["type"] = "array"
                    if param.default != inspect.Parameter.empty:
                        p_info["default"] = param.default if not callable(param.default) else None
                    params[pname] = p_info
                if params:
                    tool_info["parameters"] = {
                        "type": "object",
                        "properties": params,
                    }
            tools.append(tool_info)
        return JSONResponse({"tools": tools, "count": len(tools)})

    async def list_resources(request: Request) -> JSONResponse:
        """등록된 리소스 목록"""
        resources = []
        for uri, resource in mcp_instance._resource_manager._resources.items():
            resources.append({
                "uri": str(uri),
                "name": resource.name if hasattr(resource, 'name') else str(uri),
                "description": resource.description if hasattr(resource, 'description') else "",
            })
        return JSONResponse({"resources": resources, "count": len(resources)})

    async def list_prompts(request: Request) -> JSONResponse:
        """등록된 프롬프트 목록"""
        prompts = []
        for name, prompt in mcp_instance._prompt_manager._prompts.items():
            prompts.append({
                "name": name,
                "description": prompt.description if hasattr(prompt, 'description') else "",
            })
        return JSONResponse({"prompts": prompts, "count": len(prompts)})

    async def execute_tool(request: Request) -> JSONResponse:
        """
        도구 실행 엔드포인트.
        POST body: { "name": "tool_name", "arguments": { ... } }
        """
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

        tool_name = body.get("name")
        arguments = body.get("arguments", {})

        if not tool_name:
            return JSONResponse({"status": "error", "message": "Missing 'name' field"}, status_code=400)

        # 도구 존재 확인
        tool = mcp_instance._tool_manager._tools.get(tool_name)
        if tool is None:
            return JSONResponse(
                {"status": "error", "message": f"Unknown tool: {tool_name}"},
                status_code=404,
            )

        # 타임아웃 (쿼리 파라미터 또는 기본 30초)
        timeout = float(body.get("timeout", 30))

        # 도구 실행 (timeout 적용)
        try:
            result = tool.fn(**arguments)
            if asyncio.iscoroutine(result):
                result = await asyncio.wait_for(result, timeout=timeout)

            # Tool이 내부적으로 에러/부분실패를 반환한 경우 — 외부 status도 전파
            if isinstance(result, dict) and result.get('status') in ('error', 'partial'):
                return JSONResponse(
                    {"status": result['status'], "tool": tool_name, "result": result,
                     "message": result.get('message', 'Tool execution failed')},
                )
            return JSONResponse({"status": "ok", "tool": tool_name, "result": result})
        except asyncio.TimeoutError:
            return JSONResponse(
                {"status": "error", "error_type": "timeout", "tool": tool_name,
                 "message": f"Tool '{tool_name}' timed out after {timeout}s"},
                status_code=408,
            )
        except Exception as e:
            # 구조화된 에러 유형 지원
            from spaceengine_mcp.errors import MCPError
            if isinstance(e, MCPError):
                return JSONResponse(
                    {"status": "error", "error_type": e.error_type,
                     "tool": tool_name, "message": str(e)},
                    status_code=e.http_status,
                )
            return JSONResponse(
                {"status": "error", "error_type": "execution", "tool": tool_name,
                 "message": str(e)},
                status_code=500,
            )

    # SSE 앱 가져오기
    sse_app = mcp_instance.sse_app()

    # 추가 API 라우트
    api_routes = [
        Route("/health", health, methods=["GET"]),
        Route("/api/tools", list_tools, methods=["GET"]),
        Route("/api/tools/execute", execute_tool, methods=["POST"]),
        Route("/api/resources", list_resources, methods=["GET"]),
        Route("/api/prompts", list_prompts, methods=["GET"]),
    ]

    # SSE 앱의 기존 라우트에 API 라우트 추가
    all_routes = api_routes + list(sse_app.routes)

    # CORS 미들웨어 (Electron localhost 허용)
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:3000",
                "http://localhost:8765",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8765",
            ],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    app = Starlette(routes=all_routes, middleware=middleware)

    return app
