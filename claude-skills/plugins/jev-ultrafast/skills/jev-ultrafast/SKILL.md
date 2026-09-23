---
name: jev-ultrafast
description: Drive a real headless browser to carry out one small, concrete goal - click a link or button, type into a field, pick a dropdown value, and verify what the page then shows. Uses jev-ultrafast (browser-use x TypeSafe Jev), driven by the `jev-run` command; the skill installs itself on first use if the command is missing. Use when asked to operate a web page, fill in or submit a form, click through a site, check that a locally running web app actually works in a browser, or reach content that only appears after interaction. Also covers requests phrased as ブラウザ操作, ブラウザ自動化, 画面を操作, フォーム入力, クリックして確認. Not for plain HTTP fetching - use curl or WebFetch when no interaction is needed.
---

# jev-ultrafast

ヘッドレス Chrome を自然言語のゴール1つで動かす。ページの要素表を作り、TypeSafe の Jev に
「どの操作を、どの要素に」を1リクエストで選ばせる。文字入力が要るときだけ小さな LLM が値を書く。
1操作あたり 0.5〜1秒。

## はじめに一度だけ

`jev-run` が無ければ入れる。1分ほどかかる。入っていれば何もしない（冪等）。

```bash
command -v jev-run >/dev/null || bash "$(find ~/.claude/skills ~/.claude/plugins -path '*/jev-ultrafast/setup.sh' 2>/dev/null | head -1)"
```

環境によってはセッション開始時に導入済みで、この行は即座に終わる。

WSL などローカルでは `uv` と Chromium（または Google Chrome）が要る。`uv` が無ければ setup.sh が入れる。
Chromium が無ければ `npx playwright install chromium` で入れておく。

## 使い方

```bash
jev-run --url <URL> --goal '<ひとつの具体的なゴール>'
```

`--goal` は繰り返せる。順番に実行される。

```bash
jev-run --url http://127.0.0.1:3000 \
  --goal 'Type alice@example.com into the email field, then submit.' \
  --goal 'Open the settings page.'
```

出力はこの形。最後の行が最終 URL。

```
  769 ms  1 actions  ready
  944 ms  1 actions  done
http://127.0.0.1:3000/settings
```

`status` は `done`（達成）/ `blocked`（できないので何もしなかった）/ `max_steps`。

## 大事な性質

- **できないことは勝手にやらない。** ページに無い選択肢を指示すると、近いもので代用せず
  `0 actions / blocked` を返す。これが売りなので、blocked は失敗ではなく正しい答えのことが多い。
  まず「ページに本当にその要素があるか」を疑うこと。
- 操作の語彙は `CLICK` / `TYPE_TEXT` / `SELECT` / `SCROLL_UP` / `SCROLL_DOWN` / `WAIT` / `DONE` / `BLOCKED` のみ。
  ドラッグ、ファイルアップロード、キーボードショートカット、iframe をまたぐ操作はできない。
- **ゴールは1つの短い操作単位で書く。** 「ログインして注文履歴をCSVにして」のような複合タスクは
  `--goal` を分けるか、そもそも別の手段を使う。
- 判断はテキストのみ。Jev は画像を見ないので、canvas やアイコンだけのUIは苦手。
- ローカルホスト（`127.0.0.1` / `localhost`）はプロキシを迂回する設定済み。外部サイトも CA 登録済みで開ける。

## 結果の確認

`jev-run` は最終 URL しか出さない。**「done と言った＝タスクが成功した」ではない。**
中身まで確かめるときは Python から使い、履歴と最終ページテキストを見る。

```bash
cd "${JEV_ROOT:-$HOME/jev-ultrafast}" && uv run --env-file .env python - <<'PY'
import json
from jev_ultrafast import Agent
with Agent("http://127.0.0.1:8799/fixture.html", ["Type Kyoto into the destination search box, then press Find stays."]) as agent:
    for state in agent.run():
        pass
print(state["status"], state["page"]["url"])
print([{k: h.get(k) for k in ("action", "text", "confidence")} for h in state["history"]])
print(state["page"]["text"][:800])
PY
```

## 動作確認

```bash
jev-selftest
```

同梱のモックサイトを立てて、クリック / 文字入力 / 拒否の3件を実行する。3件 OK なら環境は正常。

## うまくいかないとき

- **`RuntimeError: Model provider returned HTTP 404`** … 文字入力に使う Gemini のモデル名が古い。
  `$JEV_ROOT/.env` の `TEXT_MODEL` を現行モデル（`gemini-3.6-flash`）にする。
  `gemini-2.5-flash` は新規ユーザーには提供されていない。
- **`ValueError: TYPE_TEXT needs TEXT_MODEL_API_KEY`** … 文字入力にだけ別の小 LLM の鍵が要る。
  クリックや選択だけなら鍵なしで動く。環境変数 `TEXT_MODEL_API_KEY` を設定する。
- **`400 Unknown name "reasoning"`** … Gemini 対応パッチが当たっていない。
  スキル同梱の `setup.sh` を実行し直す（冪等）。
- **ブラウザが落ちた / つながらない** … `jev-run` が自動で上げ直す。手動なら `bash $JEV_ROOT/chrome-up.sh`。
  **`pkill -f` や `pgrep -f` を jev / chrome に対して使わないこと**（自分のシェルに一致して exit 144 で死ぬ）。
  Chrome の PID は `$JEV_ROOT/.chrome.pid` にある。
- **要素表と各操作の確率を見たい** … `cd $JEV_ROOT && uv run jev` でインスペクタが
  http://127.0.0.1:8766 に立つ。どの要素が候補に入っていたかが分かるので blocked の原因究明に使える。

## 環境の中身

- 実体は `$JEV_ROOT`（既定 `~/jev-ultrafast`）。入れ直すのはこのスキル同梱の `setup.sh`（冪等）。
- 鍵は環境変数 `TYPESAFE_API_KEY` と `TEXT_MODEL_API_KEY` から `$JEV_ROOT/.env` に書かれる。
  **値を出力しないこと。**
