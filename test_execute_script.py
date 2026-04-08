"""execute_script 수정 검증: 직접 콘솔 전송 방식 테스트"""
import asyncio
from pathlib import Path
from spaceengine_mcp.config import SpaceEngineConfig
from spaceengine_mcp.bridges.script_bridge import ScriptBridge

async def test():
    config = SpaceEngineConfig(
        install_path=Path(r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine")
    )
    bridge = ScriptBridge(config, templates_dir=str(Path("templates")))

    # 1. 기본 모드 (직접 콘솔 전송)
    cmds = bridge.build_navigation_commands("Jupiter", "goto", 5.0)
    path = bridge.generate_script(cmds, filename="mcp_test_jupiter.se")
    print(f"=== 직접 전송 모드 (use_run=False) ===")
    result = await bridge.execute_script(path)
    print(f"Result: {result}")
    print()

    # 2. Run 모드 (스플라인 등 멀티라인 블록용)
    print(f"=== Run 모드 (use_run=True) ===")
    cmds2 = bridge.build_navigation_commands("Saturn", "goto", 8.0)
    path2 = bridge.generate_script(cmds2, filename="mcp_test_saturn.se")
    result2 = await bridge.execute_script(path2, use_run=True)
    print(f"Result: {result2}")

asyncio.run(test())
