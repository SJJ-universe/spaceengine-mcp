# 테스트 플레이 가이드

## 사전 준비

### 필수 구성요소
1. **SpaceEngine** — Steam에서 실행 (메인 화면에서 대기)
2. **MCP 서버** — SSE 모드로 기동
3. **Ollama** — 로컬 LLM (선택: LLM 없이 직접 도구 실행 가능)
4. **Electron 앱** — 프론트엔드 (선택: MCP API만으로도 테스트 가능)

### 준비 상태 점검
```bash
python scripts/check_ready.py
```

### 원클릭 시작 (Windows)
```bash
scripts\start_all.bat
```

---

## 방법 1: CLI 직접 테스트 (MCP 서버만)

```bash
# 서버 기동
python -m spaceengine_mcp --transport sse --port 8765

# 다른 터미널에서:
# 기본 탐색
python test_send.py mars
python test_send.py saturn

# Phase 5 명령어
python test_send.py set_var
python test_send.py fade_out
python test_send.py fade_in
python test_send.py fly_forward
python test_send.py stop_fly

# 투어
python test_send.py tour
```

## 방법 2: HTTP API 테스트 (curl)

```bash
# 상태 확인
curl http://127.0.0.1:8765/health

# 도구 목록
curl http://127.0.0.1:8765/api/tools

# 도구 직접 실행
curl -X POST http://127.0.0.1:8765/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"navigate_to","arguments":{"target":"Mars","mode":"goto"}}'

# SE 상태 읽기
curl -X POST http://127.0.0.1:8765/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"read_se_state","arguments":{}}'

# 스크린샷
curl -X POST http://127.0.0.1:8765/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"name":"take_screenshot","arguments":{}}'
```

## 방법 3: Electron 앱 (Full Stack)

```bash
# 터미널 1: MCP 서버
python -m spaceengine_mcp --transport sse --port 8765

# 터미널 2: Ollama (LLM 채팅용)
ollama serve
# (다른 터미널에서) ollama pull llama3:8b

# 터미널 3: Electron
cd frontend
npm run dev
```

### 테스트 시나리오

| 시나리오 | 입력 | 기대 결과 |
|---------|------|----------|
| 기본 탐색 | "Take me to Mars" | navigate_to 실행 → 화성으로 이동 |
| 스크린샷 | "Screenshot" | take_screenshot 실행 |
| 시간 가속 | "Speed up time 1000x" | set_time(rate=1000) 실행 |
| 투어 | "Solar system tour" | create_tour 실행 |
| 시네마틱 | "Cinematic view of Saturn" | smart_navigation(purpose="cinematic") |
| Quick Action | 좌측 "Go to Earth" 클릭 | navigate_to("Earth") |
| Command Palette | Ctrl+K → "screenshot" | 도구 검색 + 실행 |
| 채팅 클리어 | Ctrl+L | 대화 초기화 |

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| "SE 창을 찾을 수 없음" | SE 미실행 | SpaceEngine 먼저 실행 |
| MCP 연결 빨간불 | MCP 서버 미기동 | `--transport sse --port 8765` 확인 |
| Ollama 노란불 | Ollama 미실행 | `ollama serve` 실행 |
| 채팅 응답 없음 | 모델 미설치 | `ollama pull llama3:8b` |
| Tool timeout | SE 무응답 | SE 창이 포어그라운드인지 확인 |
