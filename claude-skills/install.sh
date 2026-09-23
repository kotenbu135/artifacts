#!/usr/bin/env bash
# kotenbu-skills マーケットプレイスと4つのスキルを、ユーザー設定 (~/.claude/settings.json) に登録する。
# ユーザー設定なので、どのリポジトリ・プロジェクトを開いても効く。冪等なので何度実行してもよい。
#
#   curl -fsSL https://raw.githubusercontent.com/kotenbu135/artifacts/main/claude-skills/install.sh | bash
#
# 既存の設定は消さずにマージする。実際のダウンロードは次に Claude Code を起動したときに行われる。
set -euo pipefail

SETTINGS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
mkdir -p "$(dirname "$SETTINGS")"

python3 - "$SETTINGS" <<'PY'
import json, pathlib, sys

path = pathlib.Path(sys.argv[1])
settings = json.loads(path.read_text(encoding="utf-8") or "{}") if path.exists() else {}

settings.setdefault("extraKnownMarketplaces", {})["kotenbu-skills"] = {
    "source": {"source": "github", "repo": "kotenbu135/artifacts"}
}
enabled = settings.setdefault("enabledPlugins", {})
for plugin in ("security-audit", "natural-japanese", "taste-skill", "jev-ultrafast"):
    enabled[f"{plugin}@kotenbu-skills"] = True

path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"登録した: {path}")
PY

# CLI があれば今すぐ取り込む。無ければ次回起動時に Claude Code が自動で入れる。
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add kotenbu135/artifacts >/dev/null 2>&1 \
    || claude plugin marketplace update kotenbu-skills >/dev/null 2>&1 || true
  for plugin in security-audit natural-japanese taste-skill jev-ultrafast; do
    claude plugin install "$plugin@kotenbu-skills" --scope user >/dev/null 2>&1 || true
  done
fi
