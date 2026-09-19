# -*- coding: utf-8 -*-
"""遊ぶ側。原神のキャラを1人思い浮かべて、質問に自由な言葉で答えるだけ。
  python3 gplay.py                    # 公式データ＋Jevの表（本番）
  python3 gplay.py table_jev.json     # 98問ぜんぶJevの表（比較用）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, sys, time
import typesafe_sdk as ts
from gdata import QUESTIONS, GROUND
from gengine import Table, Game, parse_reply, ANSWERS

async def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "table_hybrid.json"
    t = Table(path); g = Game(t); c = ts.AsyncTypeSafeClient()
    print(f"＝ 原神ジェビネーター ＝  キャラ {len(t.subjects)}人／質問 {len(QUESTIONS)}問")
    print("原神のキャラを1人思い浮かべてください。ふつうの言葉で答えて大丈夫です。\n")
    turns, lat = 0, []
    while True:
        if g.should_guess(turns):
            top = g.top(1)
            if not top:
                print("降参です。"); break
            nm, p = top[0]
            print(f"Q{turns+1}. それは「{nm}」ですね？（確信 {p:.0%}）")
            a = input("> ")
            t0 = time.perf_counter()
            kind, _ = await parse_reply(c, f"それは「{nm}」ですか", a)
            lat.append(time.perf_counter() - t0)
            if kind in ("yes", "probably"):
                print(f"\n当たりました。質問 {turns} 回、Jev呼び出し {len(lat)} 回、"
                      f"Jevの合計時間 {sum(lat):.1f}秒。")
                break
            g.reject(nm)
            if len(g.rejected) >= 3:
                print("\n降参です。"); break
            continue
        qid, _ = g.next_question()
        if qid is None:
            print("聞くことがなくなりました。"); break
        turns += 1
        print(f"Q{turns}. {QUESTIONS[qid]}？   〔候補 {int((g.belief > 1e-4).sum())}〕")
        a = input("> ")
        t0 = time.perf_counter()
        kind, conf = await parse_reply(c, QUESTIONS[qid], a)
        lat.append(time.perf_counter() - t0)
        print(f"   （{ANSWERS[kind][0]} と受け取りました・確信 {conf:.0%}・{lat[-1]:.2f}秒）")
        g.update(qid, kind)
        print("   いまの上位:", "  ".join(f"{n} {p:.0%}" for n, p in g.top(3)), "\n")
    await c.aclose()

asyncio.run(main())
