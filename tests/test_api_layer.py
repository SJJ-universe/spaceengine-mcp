"""API Layer 테스트 — Starlette TestClient로 REST 엔드포인트 검증"""
import pytest
from starlette.testclient import TestClient

from spaceengine_mcp.server import mcp
from spaceengine_mcp.api_layer import create_api_app


@pytest.fixture(scope="module")
def client():
    """Starlette TestClient (서버 기동 없이 HTTP 요청 테스트)"""
    app = create_api_app(mcp)
    return TestClient(app)


# ── GET /health ──────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["server"] == "spaceengine-mcp"


def test_health_includes_version(client):
    data = client.get("/health").json()
    assert "version" in data
    assert data["version"]  # 비어있지 않음


def test_health_includes_tools_count(client):
    data = client.get("/health").json()
    assert data["tools_count"] >= 50  # 최소 50개 이상 (현재 59)


# ── GET /api/tools ───────────────────────────────────────────────────────────

def test_tools_returns_list(client):
    data = client.get("/api/tools").json()
    assert "tools" in data
    assert "count" in data
    assert data["count"] >= 50


def test_tools_have_name_and_description(client):
    tools = client.get("/api/tools").json()["tools"]
    for tool in tools:
        assert "name" in tool
        assert "description" in tool


def test_tools_includes_navigate_to(client):
    tools = client.get("/api/tools").json()["tools"]
    names = [t["name"] for t in tools]
    assert "navigate_to" in names


# ── POST /api/tools/execute ──────────────────────────────────────────────────

def test_execute_unknown_tool_returns_404(client):
    resp = client.post("/api/tools/execute", json={"name": "nonexistent_tool", "arguments": {}})
    assert resp.status_code == 404
    assert resp.json()["status"] == "error"


def test_execute_missing_name_returns_400(client):
    resp = client.post("/api/tools/execute", json={"arguments": {}})
    assert resp.status_code == 400


def test_execute_invalid_json_returns_400(client):
    resp = client.post("/api/tools/execute", content=b"not json", headers={"content-type": "application/json"})
    assert resp.status_code == 400


# ── GET /api/resources ───────────────────────────────────────────────────────

def test_resources_returns_list(client):
    data = client.get("/api/resources").json()
    assert "resources" in data
    assert data["count"] == 4


def test_resources_include_config(client):
    resources = client.get("/api/resources").json()["resources"]
    uris = [r["uri"] for r in resources]
    assert "spaceengine://config" in uris


# ── GET /api/prompts ─────────────────────────────────────────────────────────

def test_prompts_returns_list(client):
    data = client.get("/api/prompts").json()
    assert "prompts" in data
    assert data["count"] == 3


def test_prompts_include_explore_space(client):
    prompts = client.get("/api/prompts").json()["prompts"]
    names = [p["name"] for p in prompts]
    assert "explore_space" in names
