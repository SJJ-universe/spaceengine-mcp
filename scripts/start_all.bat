@echo off
REM ============================================================
REM SpaceEngine MCP — 테스트 플레이 시작 스크립트
REM 1) MCP 서버 (SSE, port 8765)
REM 2) Electron 프론트엔드 (dev mode)
REM ============================================================

echo [1/3] SpaceEngine이 실행 중인지 확인합니다...
tasklist /FI "IMAGENAME eq SpaceEngine.exe" 2>NUL | find /I "SpaceEngine.exe" >NUL
if %ERRORLEVEL%==0 (
    echo       ✓ SpaceEngine 실행 중
) else (
    echo       ✗ SpaceEngine이 실행되지 않았습니다!
    echo       먼저 SpaceEngine을 실행해주세요.
    echo       (Steam → SpaceEngine → Play)
    pause
    exit /b 1
)

echo.
echo [2/3] MCP 서버를 SSE 모드로 시작합니다 (port 8765)...
start "MCP Server" cmd /c "cd /d %~dp0.. && python -m spaceengine_mcp --transport sse --port 8765"

REM 서버 시작 대기
timeout /t 3 /nobreak >NUL

REM 서버 상태 확인
curl -s http://127.0.0.1:8765/health >NUL 2>NUL
if %ERRORLEVEL%==0 (
    echo       ✓ MCP 서버 정상 기동
) else (
    echo       ✗ MCP 서버 연결 실패 — 로그를 확인하세요
)

echo.
echo [3/3] Electron 프론트엔드를 시작합니다...
start "Electron App" cmd /c "cd /d %~dp0..\frontend && npm run dev"

echo.
echo ============================================================
echo   테스트 플레이 준비 완료!
echo.
echo   MCP 서버:  http://127.0.0.1:8765/health
echo   도구 목록: http://127.0.0.1:8765/api/tools
echo   Electron:  자동으로 열립니다
echo.
echo   Ollama가 실행 중이어야 LLM 채팅이 가능합니다:
echo     ollama serve
echo     ollama run llama3:8b
echo ============================================================
pause
