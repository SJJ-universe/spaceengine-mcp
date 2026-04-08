import subprocess

exe = r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine\system\SpaceEngine.exe"
script = r"C:\Program Files (x86)\Steam\steamapps\common\SpaceEngine\data\scripts\mcp\mcp_test_mars.se"

proc = subprocess.Popen([exe, script])
print("PID:", proc.pid)
print("SpaceEngine에 스크립트 전달 완료 ->", script)
