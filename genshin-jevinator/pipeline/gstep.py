# -*- coding: utf-8 -*-
"""1手ずつ進める版。これまでの返事を質問idで渡すと、次の一手だけ表示して止まる。
  python3 gstep.py --kv "元素_氷=そう,武器_弓=うん"
返事は自由な日本語でよい（Jevが5択に落とす）。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, sys, time
import typesafe_sdk as ts
from gdata import QUESTIONS
from gengine import Table, Game, parse_reply, ANSWERS

async def main():
    kv = {}
    if len(sys.argv) > 2 and sys.argv[1] == "--kv":
        for p in sys.argv[2].split(","):
            if "=" in p:
                k, v = p.split("=", 1); kv[k.strip()] = v.strip()
    path = sys.argv[3] if len(sys.argv) > 3 else "table_hybrid.json"
    g = Game(Table(path)); c = ts.AsyncTypeSafeClient(); turns = 0
    while True:
        if g.should_guess(turns):
            nm, p = g.top(1)[0]
            print(f"\n★ Q{turns+1}. それは「{nm}」ですね？（確信 {p:.0%}）")
            a = kv.get("GUESS:" + nm)
            if a is None:
                print(f"   ↑ --kv に 'GUESS:{nm}=はい' などを足して再実行"); break
            kind, conf = await parse_reply(c, f"それは「{nm}」ですか", a)
            print(f"   > {a}  →「{ANSWERS[kind][0]}」")
            if kind in ("yes", "probably"):
                print(f"\n=== 当たり。質問 {turns} 回 ==="); break
            g.reject(nm)
            if len(g.rejected) >= 3:
                print("\n=== 降参 ==="); break
            continue
        qid, gain = g.next_question(); turns += 1
        alive = int((g.belief > 1e-4).sum())
        print(f"\nQ{turns}. {QUESTIONS[qid]}？  〔候補 {alive} / 利得 {gain:.2f}bit〕")
        a = kv.get(qid)
        if a is None:
            print(f"   ↑ --kv に '{qid}=<返事>' を足して再実行"); break
        t0 = time.perf_counter()
        kind, conf = await parse_reply(c, QUESTIONS[qid], a)
        print(f"   > {a}  →「{ANSWERS[kind][0]}」確信{conf:.0%} / {time.perf_counter()-t0:.2f}秒")
        g.update(qid, kind)
        print("   上位:", "  ".join(f"{n} {p:.0%}" for n, p in g.top(3)))
    await c.aclose()

asyncio.run(main())
