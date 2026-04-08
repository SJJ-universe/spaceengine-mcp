# SpaceEngine MCP Server

AI 에이전트가 SpaceEngine 우주 시뮬레이터를 제어할 수 있게 해주는 MCP 서버.

## Quick Start

```bash
# 설치
pip install -e ".[dev]"

# MCP 서버 (stdio — Claude Desktop 연동)
python -m spaceengine_mcp

# MCP 서버 (SSE — Electron 프론트엔드 연동)
python -m spaceengine_mcp --transport sse --port 8765

# 테스트
pytest
```

## 구성

- **59 MCP Tools** — 10 Phase에 걸쳐 구현
- **8 Bridges** — Console, Script, Catalog, Log, Keyboard, Config, State, Flight
- **Electron Frontend** — React + Ollama 에이전트 통합
- **REST API** — /health, /api/tools, /api/tools/execute
