import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge

SE_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
config = SpaceEngineConfig(install_path=SE_PATH)
bridge = ScriptBridge(config, templates_dir="templates")

cmds = bridge.build_navigation_commands("Mars", mode="goto", distance_rad=3.0)
path = bridge.generate_script(cmds, filename="mcp_test_mars.se")
print("생성된 파일:", path)
print("내용:")
print(path.read_text(encoding="utf-8"))
print("폴더 내 .se 파일:")
for f in config.scripts_dir.glob("*.se"):
    print(" -", f.name)
