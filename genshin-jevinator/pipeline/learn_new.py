# -*- coding: utf-8 -*-
"""新しいキャラを1人足すのに何が要るか。
表から8人を抜いて当てられないことを確かめ、
  ・公式データ6項目（元素・武器・出身・星・体型・実装日）を入れる ＝ 客観29問が埋まる
  ・Jevに1リクエスト ＝ 主観69問が埋まる
の2つだけで復帰するかを見る。手でラベルを98個書く必要はない。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, time
import typesafe_sdk as ts
from gdata import GROUND, QUESTIONS, SUBJECTIVE, objective_row
from gengine import Table, Game
from gautoplay import play
from build_tables import qs, state

HOLDOUT = ["胡桃", "ナヒーダ", "雷電将軍", "鍾離", "コロンビーナ", "オデット", "ファルカ", "リンネア"]

class Partial(Table):
    def __init__(self, path, drop):
        super().__init__(path)
        keep = [i for i, s in enumerate(self.subjects) if s not in drop]
        self.subjects = [self.subjects[i] for i in keep]
        self.P = self.P[keep]

async def main():
    c = ts.AsyncTypeSafeClient(); sem = asyncio.Semaphore(12)
    print(f"=== 1. 8人を表から抜いた状態（{118-len(HOLDOUT)}人）で出題 ===")
    before = await asyncio.gather(*[play(c, sem, Partial("table_hybrid.json", HOLDOUT), s)
                                    for s in HOLDOUT])
    for r in before:
        print(f"  {r['secret']:<10} → {[g[0] for g in r['guesses']]}  {'○' if r['hitn'] else '×'}")

    print(f"\n=== 2. 足す（公式データ6項目 ＋ Jevに1リクエスト69判断） ===")
    t0 = time.perf_counter()
    got = await asyncio.gather(*[c.system_one(state(n), qs(SUBJECTIVE)) for n in HOLDOUT])
    wall = time.perf_counter() - t0
    full = json.load(open("table_hybrid.json", encoding="utf-8"))
    t = Partial("table_hybrid.json", HOLDOUT)
    for n, r in zip(HOLDOUT, got):
        row = {**objective_row(n), **{q: float(a.noul) for q, a in r.answers.items()}}
        full["subjects"][n] = row
    json.dump(full, open("table_plus.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  8人ぶんの主観69問 x 8 = {69*8}判断を並列で {wall:.2f}秒。手で書いたラベルは0個。")

    print(f"\n=== 3. 足したあと、同じ出題をもう一度 ===")
    after = await asyncio.gather(*[play(c, sem, Table("table_plus.json"), s) for s in HOLDOUT])
    for r in after:
        print(f"  {r['secret']:<10} → {[g[0] for g in r['guesses']]}  {'○' if r['hitn'] else '×'}"
              f" （質問 {r['turns']} 回）")
    print(f"\n抜いた状態 {sum(r['hitn'] for r in before)}/{len(HOLDOUT)} "
          f"→ 足したあと {sum(r['hit1'] for r in after)}/{len(HOLDOUT)}（1回目の推測で）")
    await c.aclose()

if __name__ == "__main__":
    asyncio.run(main())
