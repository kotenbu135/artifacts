# -*- coding: utf-8 -*-
"""表を2つ作る。
  table_hybrid.json : 客観23問=公式データ / 主観69問=Jev   ← 本番で使う
  table_jev.json    : 92問ぜんぶJev                        ← 比較用（前回のやり方）
stateには日本語名と英語名の両方を入れる。英語名を足すと当たるようになることは
knowledge_variants.py で測った（元素 63%→83%、武器 48%→67%）。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, sys, time
import typesafe_sdk as ts
from gdata import QUESTIONS, OBJECTIVE, SUBJECTIVE, CHARS, GROUND, objective_row

HERE = os.path.dirname(os.path.abspath(__file__))
INSTR = ("原神（Genshin Impact）のプレイアブルキャラクターについて、"
         "次の記述が当てはまるかどうかを、原作の設定と一般的なプレイヤーの受け取り方にもとづいて判断する。")

def qs(bank):
    return {qid: ts.Noul(instructions={"判断のしかた": INSTR, "記述": text})
            for qid, text in bank.items()}

def state(name):
    return {"キャラクター名": name, "英語表記": GROUND[name]["en"]}

async def one(c, sem, name, questions):
    async with sem:
        for a in range(3):
            try:
                r = await c.system_one(state(name), questions)
                return name, {q: round(v.noul, 4) for q, v in r.answers.items()}, r.usage
            except Exception as e:
                if a == 2:
                    print(f"!! {name}: {e}", file=sys.stderr); return name, None, None
                await asyncio.sleep(1.5 * (a + 1))

async def build(c, sem, bank, label):
    t0 = time.perf_counter()
    got = await asyncio.gather(*[one(c, sem, n, qs(bank)) for n in CHARS])
    wall = time.perf_counter() - t0
    tok = sum(u.input_tokens for _, _, u in got if u)
    print(f"{label}: {len(CHARS)}キャラ x {len(bank)}問 = {len(CHARS)*len(bank)}判断 / "
          f"{wall:.1f}秒 / 入力 {tok:,}トークン")
    return {n: r for n, r, _ in got if r}

async def main():
    c = ts.AsyncTypeSafeClient(); sem = asyncio.Semaphore(12)
    sub = await build(c, sem, SUBJECTIVE, "主観69問をJevで")
    allj = await build(c, sem, QUESTIONS, "98問ぜんぶJevで")
    await c.aclose()

    hybrid = {n: {**objective_row(n), **sub[n]} for n in sub}
    json.dump({"subjects": hybrid, "questions": list(QUESTIONS)},
              open(os.path.join(HERE, "table_hybrid.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"subjects": allj, "questions": list(QUESTIONS)},
              open(os.path.join(HERE, "table_jev.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"できあがり: table_hybrid.json（{len(hybrid)}キャラ）/ table_jev.json（{len(allj)}キャラ）")

if __name__ == "__main__":
    asyncio.run(main())
