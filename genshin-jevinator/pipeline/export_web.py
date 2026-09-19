# -*- coding: utf-8 -*-
"""ブラウザで遊ぶための data.js を書き出す。
確率は 0〜100 の整数に落とす（表の値の差はそこまで細かくない）。
2つの表を両方入れる: 公式データ＋Jev（本番）と、98問ぜんぶJev（比較モード）。
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdata import QUESTIONS, OBJECTIVE, GROUND, CHARS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/user/artifacts/genshin-jevinator/data.js"

qids = list(QUESTIONS)
def mat(path):
    t = json.load(open(os.path.join(HERE, path), encoding="utf-8"))["subjects"]
    return [[round(t[c][q] * 100) for q in qids] for c in CHARS]

data = {
    "chars": CHARS,
    "meta": [[GROUND[c][k] for k in ("元素", "武器", "地域", "体型")] +
             [GROUND[c]["星"], GROUND[c]["実装日"][:7], GROUND[c]["en"]] for c in CHARS],
    "qids": qids,
    "qtext": [QUESTIONS[q] for q in qids],
    "qobj": [1 if q in OBJECTIVE else 0 for q in qids],
    "hybrid": mat("table_hybrid.json"),
    "jevonly": mat("table_jev.json"),
}
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 自動生成: export_web.py。手で編集しない。\n")
    f.write("window.JEVINATOR_DATA = ")
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print(f"{OUT} を書き出した: {len(CHARS)}キャラ x {len(qids)}問 / "
      f"{os.path.getsize(OUT)/1024:.0f} KB")
