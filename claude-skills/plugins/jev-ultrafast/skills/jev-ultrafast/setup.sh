#!/usr/bin/env bash
# jev-ultrafast（browser-use × TypeSafe Jev のブラウザエージェント）を
# Claude Code のクラウド環境に入れる。冪等なので何度実行してもよい。
#
#   bash "$(dirname "$0")/setup.sh"
#
# このスキルディレクトリ以外には何も依存しない。プロジェクトを問わず動く。
#
# 使う環境変数（環境設定のUIで設定しておく）:
#   TYPESAFE_API_KEY    … 必須
#   TEXT_MODEL_API_KEY  … TYPE_TEXT（文字入力）にだけ必要。無いとそこだけ落ちる
#   TEXT_MODEL_BASE_URL … 省略時は Gemini の OpenAI 互換エンドポイント
#   TEXT_MODEL          … 省略時は gemini-3.6-flash（gemini-2.5-flash は新規ユーザーに 404）
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${JEV_ROOT:-$HOME/jev-ultrafast}"
CDP_PORT="${JEV_CDP_PORT:-9222}"

echo "==> clone / update"
if [ -d "$ROOT/.git" ]; then
  git -C "$ROOT" pull --ff-only
else
  git clone --depth 1 https://github.com/browser-use/jev-ultrafast.git "$ROOT"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "==> uv を入れる"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> uv sync (Python 3.12 は uv が自前で用意する)"
( cd "$ROOT" && uv sync )

echo "==> Gemini 対応パッチ"
python3 "$HERE/gemini_fix.py" "$ROOT/jev_ultrafast/model.py"

echo "==> .env を書く（環境変数が入っていればそれを使う）"
cat > "$ROOT/.env" <<EOF
TYPESAFE_API_KEY=${TYPESAFE_API_KEY:-}
TYPESAFE_MODEL=${TYPESAFE_MODEL:-jev-latest}
TEXT_MODEL_API_KEY=${TEXT_MODEL_API_KEY:-}
TEXT_MODEL_BASE_URL=${TEXT_MODEL_BASE_URL:-https://generativelanguage.googleapis.com/v1beta/openai}
TEXT_MODEL=${TEXT_MODEL:-gemini-3.6-flash}
TEXT_MODEL_REASONING=${TEXT_MODEL_REASONING:-none}
EOF
chmod 600 "$ROOT/.env"

echo "==> プロキシCAをブラウザのNSSストアに登録"
# Chromium は CA バンドルの環境変数を読まない。これを入れないと
# 外部サイトが全部 net_error -202 (ERR_CERT_AUTHORITY_INVALID) で落ちる。
if [ -f /root/.ccr/agent-proxy-ca.crt ]; then
  command -v certutil >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y -qq libnss3-tools; }
  mkdir -p "$HOME/.pki/nssdb"
  certutil -d "sql:$HOME/.pki/nssdb" -A -t "C,," -n ccr-agent-proxy \
    -i /root/.ccr/agent-proxy-ca.crt 2>/dev/null || true
else
  echo "    プロキシCAが無いので飛ばす"
fi

echo "==> chrome ランチャと jev-run を作る"
cp "$HERE/selftest.py" "$ROOT/selftest.py"

cat > "$ROOT/chrome-up.sh" <<'SH'
#!/usr/bin/env bash
# CDP 付きヘッドレス Chromium を上げ直す。ループバックは Chrome 既定でプロキシ迂回。
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${JEV_CDP_PORT:-9222}"
PIDF="$ROOT/.chrome.pid"
[ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null && { kill "$(cat "$PIDF")"; sleep 2; }
BIN=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux*/chrome "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | head -1)
[ -n "$BIN" ] || BIN=$(command -v chromium chromium-browser google-chrome 2>/dev/null | head -1)
[ -n "$BIN" ] || { echo "Chromium が見つからない" >&2; exit 1; }
ARGS=( --headless=new --no-sandbox --disable-gpu
       --remote-debugging-port="$PORT" --remote-debugging-address=127.0.0.1
       --user-data-dir="$ROOT/.chrome-profile" )
[ -n "${HTTPS_PROXY:-}" ] && ARGS+=( --proxy-server="$HTTPS_PROXY" )
nohup "$BIN" "${ARGS[@]}" about:blank > "$ROOT/.chrome.log" 2>&1 &
echo $! > "$PIDF"
for _ in $(seq 1 40); do
  curl -s --noproxy 127.0.0.1 --max-time 3 "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -s --noproxy 127.0.0.1 --max-time 5 "http://127.0.0.1:$PORT/json/version" | sed -n '2p'
SH
chmod +x "$ROOT/chrome-up.sh"

# jev-run と jev-selftest は同じ前置き（Chrome を確かめて環境を整える）を共有する。
for pair in "jev-run:examples/run.py" "jev-selftest:selftest.py"; do
  name="${pair%%:*}"; script="${pair##*:}"
  cat > "$ROOT/$name" <<SH
#!/usr/bin/env bash
# Chrome が落ちていれば勝手に上げ直す。
set -u
ROOT="\$(cd "\$(dirname "\$0")" && pwd)"
PORT="\${JEV_CDP_PORT:-$CDP_PORT}"
curl -s --noproxy 127.0.0.1 --max-time 3 "http://127.0.0.1:\$PORT/json/version" >/dev/null 2>&1 \\
  || bash "\$ROOT/chrome-up.sh" >/dev/null
export BU_CDP_URL="http://127.0.0.1:\$PORT"
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
export ANONYMIZED_TELEMETRY=false
exec uv run --project "\$ROOT" --env-file "\$ROOT/.env" python "\$ROOT/$script" "\$@"
SH
  chmod +x "$ROOT/$name"
done

echo "==> PATH に置く（source 無しでも叩けるように）"
# 別セッションの Claude は毎回まっさらなシェルでコマンドを打つので、
# 環境ファイルを source させる前提にすると必ず忘れられる。
BINDIR=""
for d in /usr/local/bin "$HOME/.local/bin"; do
  if mkdir -p "$d" 2>/dev/null && [ -w "$d" ]; then BINDIR="$d"; break; fi
done
if [ -n "$BINDIR" ]; then
  for cmd in jev-run jev-selftest; do
    printf '#!/usr/bin/env bash\nexec "%s/%s" "$@"\n' "$ROOT" "$cmd" > "$BINDIR/$cmd"
    chmod +x "$BINDIR/$cmd"
  done
  echo "    $BINDIR/{jev-run,jev-selftest}"
  case ":$PATH:" in *":$BINDIR:"*) ;; *) echo "    注意: $BINDIR が PATH に無い" ;; esac
else
  echo "    書き込める bin ディレクトリが無いので飛ばす。$ROOT/jev-run を直に叩くこと"
fi

# 人間向けの逃げ道。Claude は上の PATH 経由で使う。
cat > /tmp/jev-ultrafast.env <<EOF
export JEV_ROOT="$ROOT"
export PATH="\$PATH:$ROOT"
export BU_CDP_URL="http://127.0.0.1:$CDP_PORT"
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost
export ANONYMIZED_TELEMETRY=false
EOF

# アカウント同期のスキルやプラグインとして置かれている場合は自分自身をコピーしない。
case "$HERE" in
  "$HOME/.claude/skills"/*|"$HOME/.claude/plugins"/*) ;;
  *)
    echo "==> スキルを入れる（新しいセッションが自力で見つけられるように）"
    mkdir -p "$HOME/.claude/skills/jev-ultrafast"
    cp "$HERE"/SKILL.md "$HERE"/setup.sh "$HERE"/gemini_fix.py "$HERE"/selftest.py \
      "$HOME/.claude/skills/jev-ultrafast/"
    echo "    $HOME/.claude/skills/jev-ultrafast/"
    ;;
esac

echo "==> chrome 起動"
bash "$ROOT/chrome-up.sh"

echo
echo "完了。source は不要:"
echo "  jev-selftest                     # クリック/文字入力/拒否の3件を実測"
echo "  jev-run --url http://127.0.0.1:3000 --goal 'ログインボタンを押す'"
echo "  cd $ROOT && uv run jev           # インスペクタ http://127.0.0.1:8766"
