import win32gui, win32api, win32con
print("pywin32 OK")

# SE 창 목록 출력
def enum_cb(hwnd, results):
    title = win32gui.GetWindowText(hwnd)
    if title:
        results.append((hwnd, title))

wins = []
win32gui.EnumWindows(enum_cb, wins)
se_wins = [(h, t) for h, t in wins if "SpaceEngine" in t or "space" in t.lower()]
print("SE 창:", se_wins if se_wins else "못 찾음")
print("\n전체 창 목록 (상위 20개):")
for h, t in wins[:20]:
    print(f"  hwnd={h:#010x} title={t!r}")
