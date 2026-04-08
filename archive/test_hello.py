"""ShowMessage 테스트 — 스크립트가 실제로 실행되는지 확인"""
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge
from spaceengine_mcp.bridges.console_bridge import run_script_via_console

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir="templates")

# ShowMessage만 있는 단순 스크립트
cmds = ['ShowMessage "MCP 테스트 성공!" 5']
path = bridge.generate_script(cmds, filename="mcp_hello.se")
print("스크립트:", path)
print("내용:", path.read_text(encoding="utf-8"))

scripts_base = SE_PATH / "data" / "scripts"
relative = path.relative_to(scripts_base).as_posix()
print("RunScript 경로:", relative)

result = run_script_via_console(relative)
print("결과:", result)
