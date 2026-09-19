# -*- coding: utf-8 -*-
"""まず確かめること: Jev は原神を本当に知っているのか。
元素・武器種・出身・レアリティ・体型には客観的な正解があるので、正面から突き合わせられる。
stateの中身を4通り試し、実装時期で切って「新しいキャラほど知らない」かどうかも見る。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, sys, time
import typesafe_sdk as ts
from gdata import GROUND, ELEMS, WEAPONS, NATIONS, BODIES

HERE = os.path.dirname(os.path.abspath(__file__))
INSTR = "原神（Genshin Impact）に登場するプレイアブルキャラクターについて答える。"

def questions():
    return {
        "元素": ts.Choice(instructions=INSTR + " このキャラクターの元素はどれか。",
                          criteria={e: None for e in ELEMS}),
        "武器": ts.Choice(instructions=INSTR + " このキャラクターが使う武器種はどれか。",
                          criteria={w: None for w in WEAPONS}),
        "地域": ts.Choice(instructions=INSTR + " このキャラクターの出身・所属はどの国か。",
                          criteria={n: None for n in NATIONS}),
        "体型": ts.Choice(instructions=INSTR + " このキャラクターの見た目の年齢・体格はどれか。",
                          criteria={b: None for b in BODIES}),
        "星5":  ts.Noul(instructions=INSTR + " このキャラクターは星5（最高レアリティ）である。"),
    }

VARIANTS = {
    "日本語名だけ":     lambda n, g: {"キャラクター名": n},
    "英語名だけ":       lambda n, g: {"character name": g["en"]},
    "日本語名＋英語名": lambda n, g: {"キャラクター名": n, "英語表記": g["en"]},
}
KEYS = ["元素", "武器", "地域", "体型", "星5"]

async def one(c, sem, n, st):
    async with sem:
        return n, await c.system_one(st, questions())

def grade(name, r):
    g = GROUND[name]; out = {}
    for k in ["元素", "武器", "地域", "体型"]:
        a = r.answers[k]
        out[k] = (a.choice == g[k], a.confidence, a.choice)
    a = r.answers["星5"]
    out["星5"] = ((a.noul > 0.5) == (g["星"] == 5), max(a.noul, 1 - a.noul), f"{a.noul:.2f}")
    return out

async def run(c, sem, label, build, chars):
    t0 = time.perf_counter()
    res = await asyncio.gather(*[one(c, sem, n, build(n, GROUND[n])) for n in chars])
    wall = time.perf_counter() - t0
    grades = {n: grade(n, r) for n, r in res}
    sc = {k: sum(grades[n][k][0] for n in chars) / len(chars) for k in KEYS}
    hi = [(g[k][0]) for n, g in grades.items() for k in KEYS if g[k][1] >= 0.7]
    print(f"  {label:<16} " + "  ".join(f"{k} {sc[k]:5.1%}" for k in KEYS)
          + f"   確信0.7以上 {sum(hi)}/{len(hi)}"
          + (f" ({sum(hi)/len(hi):.0%})" if hi else "") + f"   {wall:.1f}秒")
    return grades

async def main():
    chars = list(GROUND)
    old = [n for n in chars if GROUND[n]["実装日"] < "2024-10-01"]
    new = [n for n in chars if GROUND[n]["実装日"] >= "2024-10-01"]
    c = ts.AsyncTypeSafeClient(); sem = asyncio.Semaphore(14)
    print(f"=== Jevの原神知識 / {len(chars)}キャラ x 5項目 ===")
    print(f"でたらめに答えた場合: 元素 14% 武器 20% 地域 12% 体型 20% 星5 57%\n")
    best = None
    for label, build in VARIANTS.items():
        g = await run(c, sem, label, build, chars)
        if label == "日本語名＋英語名": best = g
    print(f"\n=== 実装時期で切る（日本語名＋英語名の結果を分けたもの） ===")
    for lbl, group in [(f"2024年9月までの{len(old)}キャラ", old), (f"2024年10月以降の{len(new)}キャラ", new)]:
        sc = {k: sum(best[n][k][0] for n in group) / len(group) for k in KEYS}
        print(f"  {lbl:<22} " + "  ".join(f"{k} {sc[k]:5.1%}" for k in KEYS))
    print(f"\n--- 元素を外した例（新しいほうから） ---")
    for n in sorted(new, key=lambda x: GROUND[x]["実装日"], reverse=True)[:12]:
        ok, conf, ch = best[n]["元素"]
        print(f"  {GROUND[n]['実装日']} {n:<10} Jev={ch}({conf:.0%}) 正={GROUND[n]['元素']} {'○' if ok else '×'}")
    json.dump({n: {k: [bool(v[0]), v[1], v[2]] for k, v in g.items()} for n, g in best.items()},
              open(os.path.join(HERE, "knowledge_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    await c.aclose()

if __name__ == "__main__":
    asyncio.run(main())
