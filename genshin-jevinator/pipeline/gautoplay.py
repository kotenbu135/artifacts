# -*- coding: utf-8 -*-
"""自動対局。出題者役は「そのキャラをよく知っているプレイヤー」を模す:
  客観質問（元素・武器・出身・星・性別・実装時期）→ 公式データから正確に答える
  主観質問（見た目・性格・役割）                  → 表を作ったのとは別の聞き方でJevに聞く
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asyncio, json, os, random, sys, time
import typesafe_sdk as ts
from gdata import QUESTIONS, OBJECTIVE, SUBJECTIVE, GROUND, objective_row
from gengine import Table, Game, ANSWERS

ORACLE = ("あなたは原神のキャラ当てゲームの出題者で、あるキャラクターを思い浮かべている。"
          "相手の質問に、そのキャラクターについて正直に答える。"
          "言い切れるなら はい／いいえ、自信がなければ たぶんそう／たぶん違う、"
          "判断がつかないなら わからない を選ぶ。")
LABELS = [ANSWERS[k][0] for k in ["yes","probably","unknown","probably_no","no"]]
INV = {ANSWERS[k][0]: k for k in ANSWERS}

async def oracle(client, name, qid):
    if qid in OBJECTIVE:                      # 正解が公式データにあるので迷わない
        return ("yes" if objective_row(name)[qid] > 0.5 else "no"), 1.0, False
    r = await client.system_one(
        {"あなたが思い浮かべているキャラクター": name,
         "英語表記": GROUND[name]["en"], "相手からの質問": SUBJECTIVE[qid]},
        {"a": ts.Choice(instructions=ORACLE, criteria={l: None for l in LABELS})})
    return INV[r.answers["a"].choice], r.answers["a"].confidence, True

async def play(client, sem, table, secret, noise=0.0, max_guesses=3, rng=None):
    rng = rng or random.Random(0)
    g = Game(table); turns, guesses, calls = 0, [], 0
    while True:
        if g.should_guess(turns):
            top = g.top(1)
            if not top: break
            nm = top[0][0]; guesses.append((nm, top[0][1], turns))
            if nm == secret or len(guesses) >= max_guesses: break
            g.reject(nm); continue
        qid, _ = g.next_question()
        if qid is None: break
        turns += 1
        async with sem:
            kind, conf, used = await oracle(client, secret, qid)
        calls += used
        if noise and rng.random() < noise:
            kind = rng.choice([k for k in ANSWERS if k != kind])
        g.update(qid, kind)
    return dict(secret=secret, turns=turns, calls=calls,
                guesses=guesses, hit1=bool(guesses) and guesses[0][0] == secret,
                hitn=any(n == secret for n, _, _ in guesses),
                history=g.history, top3=g.top(3))

async def run(client, sem, table_path, label, chars, noise=0.0, seed=1):
    t0 = time.perf_counter()
    res = await asyncio.gather(*[play(client, sem, Table(table_path), s, noise,
                                      rng=random.Random(seed + i)) for i, s in enumerate(chars)])
    wall = time.perf_counter() - t0
    n = len(chars); h1 = sum(r["hit1"] for r in res); hn = sum(r["hitn"] for r in res)
    print(f"{label:<28} 1回目 {h1:>2}/{n} ({h1/n:4.0%})  3回以内 {hn:>2}/{n} ({hn/n:4.0%})  "
          f"平均質問 {sum(r['turns'] for r in res)/n:4.1f}  {wall:.1f}秒")
    return res

async def main():
    noise = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    from gdata import CHARS
    c = ts.AsyncTypeSafeClient(); sem = asyncio.Semaphore(16)
    print(f"=== 全{len(CHARS)}キャラを1回ずつ出題 / 出題者のノイズ {noise:.0%} ===")
    a = await run(c, sem, "table_hybrid.json", "公式データ＋Jev（本番）", CHARS, noise)
    b = await run(c, sem, "table_jev.json",    "98問ぜんぶJev（比較）",   CHARS, noise)
    await c.aclose()
    print("\n--- 本番の表で外したキャラ ---")
    for r in a:
        if not r["hitn"]:
            print(f"  {r['secret']} → {[g[0] for g in r['guesses']]}  最終 {[f'{n}{p:.0%}' for n,p in r['top3']]}")
    json.dump([{k: v for k, v in r.items()} for r in a],
              open(f"autoplay_hybrid_{int(noise*100)}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

if __name__ == "__main__":
    asyncio.run(main())
