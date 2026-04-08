"""Entry point — python -m spaceengine_mcp [--transport stdio|sse|streamable-http] [--port 8765]"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="SpaceEngine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for SSE/HTTP transport (default: 8765)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for SSE/HTTP transport (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    from spaceengine_mcp.server import mcp

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport in ("sse", "streamable-http"):
        # SSE/HTTP 모드: api_layer를 통해 REST 엔드포인트 + MCP SSE 결합
        mcp.settings.port = args.port
        mcp.settings.host = args.host

        import asyncio
        import uvicorn
        from spaceengine_mcp.api_layer import create_api_app

        app = create_api_app(mcp)
        print(f"SpaceEngine MCP Server starting on {args.host}:{args.port} ({args.transport})")
        print(f"  MCP SSE endpoint: http://{args.host}:{args.port}/sse")
        print(f"  Health check:     http://{args.host}:{args.port}/health")
        print(f"  Tool list:        http://{args.host}:{args.port}/api/tools")
        print(f"  Resource list:    http://{args.host}:{args.port}/api/resources")

        config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
        server = uvicorn.Server(config)
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()
