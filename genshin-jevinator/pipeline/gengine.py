# -*- coding: utf-8 -*-
"""原神ジェビネーターの中身。前作 /mnt/project-files/jevinator/engine.py と同じ骨。
ベイズ更新と期待情報利得はコード側。Jevは(1)自由文の返事の解釈 (2)未知キャラのその場学習 だけ。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, os
import numpy as np
import typesafe_sdk as ts
from gdata import QUESTIONS, SUBJECTIVE, GROUND, objective_row

HERE = os.path.dirname(os.path.abspath(__file__))
ANSWERS = {
    "yes":         ("はい", 1.0, 1.0),
    "probably":    ("たぶんそう", 1.0, 0.55),
    "unknown":     ("わからない", 0.0, 0.0),
    "probably_no": ("たぶん違う", 0.0, 0.55),
    "no":          ("いいえ", 0.0, 1.0),
}
CLIP = 0.04

class Table:
    def __init__(self, path):
        raw = json.load(open(path, encoding="utf-8"))
        self.qids = list(QUESTIONS)
        self.subjects = list(raw["subjects"])
        self.P = np.clip(np.array([[raw["subjects"][s][q] for q in self.qids]
                                   for s in self.subjects]), CLIP, 1 - CLIP)
    def add(self, name, row):
        self.subjects.append(name)
        self.P = np.vstack([self.P, np.clip([row[q] for q in self.qids], CLIP, 1 - CLIP)])

class Game:
    def __init__(self, table):
        self.t = table
        self.belief = np.ones(len(table.subjects)) / len(table.subjects)
        self.asked, self.rejected, self.history = set(), set(), []
    def update(self, qid, kind):
        _, d, s = ANSWERS[kind]
        p = self.t.P[:, self.t.qids.index(qid)]
        lik = p if d == 1.0 else 1 - p
        lik = s * lik + (1 - s) * 0.5
        self.belief *= lik
        tot = self.belief.sum()
        self.belief = self.belief / tot if tot > 0 else np.ones_like(self.belief) / len(self.belief)
        self.asked.add(qid); self.history.append((qid, kind))
    @staticmethod
    def _H(b):
        b = b[b > 0]
        return float(-(b * np.log2(b)).sum())
    def next_question(self):
        b, H0 = self.belief, self._H(self.belief)
        best, bg = None, -1.0
        for j, qid in enumerate(self.t.qids):
            if qid in self.asked: continue
            p = self.t.P[:, j]; py = float((b * p).sum())
            if py < 1e-6 or py > 1 - 1e-6: continue
            g = H0 - (py * self._H(b * p / py) + (1 - py) * self._H(b * (1 - p) / (1 - py)))
            if g > bg: best, bg = qid, g
        return best, bg
    def top(self, n=5):
        out = []
        for i in np.argsort(-self.belief):
            nm = self.t.subjects[i]
            if nm in self.rejected: continue
            out.append((nm, float(self.belief[i])))
            if len(out) == n: break
        return out
    def should_guess(self, n, threshold=0.55):
        t = self.top(1)
        return bool(t) and (t[0][1] >= threshold or n >= 20)
    def reject(self, nm):
        self.rejected.add(nm)
        self.belief[self.t.subjects.index(nm)] = 0.0
        s = self.belief.sum()
        if s > 0: self.belief /= s

PARSE = ("原神のキャラ当てゲームの最中である。出題者が思い浮かべているキャラクターについて"
         "こちらが質問し、出題者が自由な言葉で答えた。その返事が "
         "はい・いいえ・たぶんそう・たぶん違う・わからない のどれに当たるかを選ぶ。")
async def parse_reply(client, qtext, reply):
    r = await client.system_one({"こちらの質問": qtext, "出題者の返事": reply},
        {"k": ts.Choice(instructions=PARSE,
                        criteria={ANSWERS[k][0]: None for k in
                                  ["yes","probably","unknown","probably_no","no"]})})
    inv = {ANSWERS[k][0]: k for k in ANSWERS}
    return inv[r.answers["k"].choice], r.answers["k"].confidence
