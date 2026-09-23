"""3件の実測チェック: クリック / 文字入力 / 拒否。同梱フィクスチャだけで完結する。"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from jev_ultrafast import Agent

STATIC = Path(__file__).resolve().parent / "jev_ultrafast" / "static"
URL = "http://127.0.0.1:8799/fixture.html"


def fixture_up():
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        return True
    except Exception:
        return False


def run(goal):
    with Agent(URL, [goal]) as agent:
        for state in agent.run():
            pass
    return state


if not fixture_up():
    subprocess.Popen(
        [sys.executable, "-m", "http.server", "8799", "--bind", "127.0.0.1"],
        cwd=STATIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    for _ in range(20):
        time.sleep(0.5)
        if fixture_up():
            break
    else:
        sys.exit("フィクスチャサーバ (127.0.0.1:8799) が立ち上がらない")

fails = []

s = run("Open the Reading room section.")
ok = s["status"] == "done" and s["page"]["url"].endswith("#reading")
print(f"[{'OK  ' if ok else 'FAIL'}] CLICK      {s['elapsed_ms']}ms {len(s['history'])} actions {s['status']} {s['page']['url']}")
ok or fails.append("CLICK")

try:
    s = run("Type Kyoto into the destination search box, then press Find stays.")
    ok = s["status"] == "done" and "Kyoto" in s["page"]["text"]
    typed = [h.get("text") for h in s["history"] if h.get("text")]
    print(f"[{'OK  ' if ok else 'FAIL'}] TYPE_TEXT  {s['elapsed_ms']}ms {len(s['history'])} actions {s['status']} typed={typed}")
    ok or fails.append("TYPE_TEXT")
except Exception as exc:  # 文字入力だけは別プロバイダの鍵に依存するので理由を残す
    print(f"[FAIL] TYPE_TEXT  {type(exc).__name__}: {exc}")
    fails.append("TYPE_TEXT")

s = run("Choose Cabins in the stay category dropdown.")
ok = s["status"] == "blocked" and not s["history"]
print(f"[{'OK  ' if ok else 'FAIL'}] BLOCKED    {s['elapsed_ms']}ms {len(s['history'])} actions {s['status']}")
ok or fails.append("BLOCKED")

print()
if fails:
    sys.exit(f"NG: {', '.join(fails)} が期待どおりでない。SKILL.md の「うまくいかないとき」を見ること。")
print("すべて期待どおり。jev-run が使える。")
