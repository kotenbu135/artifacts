# claude-skills

どのリポジトリ・クラウド環境・WSL ローカルでも同じスキルを使うための Claude Code プラグインマーケットプレイス
`kotenbu-skills`。定義はリポジトリ直下の [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json)。

| プラグイン | 中身 | 取得元 |
| --- | --- | --- |
| `security-audit` | セキュリティ監査・脆弱性レビュー | [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill)（上流を直接参照） |
| `natural-japanese` | 読みやすい日本語の文書を書く・直す | [coji/natural-japanese](https://github.com/coji/natural-japanese)（上流を直接参照） |
| `taste-skill` | フロントエンドのデザインセンス系スキル14本 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)（上流を直接参照） |
| `jev-ultrafast` | ヘッドレス Chrome を自然言語で操作 | [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) 用のスキルを [`plugins/jev-ultrafast`](plugins/jev-ultrafast) に同梱 |

上流の3つはこのリポジトリにコピーしていない。Claude Code が各リポジトリのデフォルトブランチから取ってくるので、
`/plugin marketplace update kotenbu-skills` で常に最新になる。
jev-ultrafast だけは上流にスキルが無いので、`SKILL.md` とセットアップスクリプトをここに置いている。

## 入れ方

どの方法でもユーザー設定 (`~/.claude/settings.json`) に入るので、以後どのリポジトリを開いても効く。

### WSL / ローカル

```bash
curl -fsSL https://raw.githubusercontent.com/kotenbu135/artifacts/main/claude-skills/install.sh | bash
```

既存の設定は残したまま、マーケットプレイスと4プラグインを登録する（何度実行してもよい）。
Claude Code の中から手で入れるなら:

```
/plugin marketplace add kotenbu135/artifacts
/plugin install security-audit@kotenbu-skills
/plugin install natural-japanese@kotenbu-skills
/plugin install taste-skill@kotenbu-skills
/plugin install jev-ultrafast@kotenbu-skills
```

### クラウド環境（Claude Code on the web）

クラウドのコンテナは毎回まっさらなので、環境の **Setup script** に上と同じ1行を足す
（セッションのタイトルバーの環境メニュー → Edit → Setup script）。

```bash
curl -fsSL https://raw.githubusercontent.com/kotenbu135/artifacts/main/claude-skills/install.sh | bash
```

新しいセッションから効く。ネットワークポリシーで `github.com` と `raw.githubusercontent.com` が通る必要がある。

### 特定のリポジトリだけ（チームで共有したいとき）

そのリポジトリの `.claude/settings.json` に書けば、そのリポジトリを開いた人全員に入る。

```json
{
  "extraKnownMarketplaces": {
    "kotenbu-skills": { "source": { "source": "github", "repo": "kotenbu135/artifacts" } }
  },
  "enabledPlugins": {
    "security-audit@kotenbu-skills": true,
    "natural-japanese@kotenbu-skills": true,
    "taste-skill@kotenbu-skills": true,
    "jev-ultrafast@kotenbu-skills": true
  }
}
```

## jev-ultrafast の前提

- 初回に使ったとき `setup.sh` が `~/jev-ultrafast` に本体を入れ、`jev-run` / `jev-selftest` を PATH に置く（冪等）。
- 環境変数 `TYPESAFE_API_KEY`（必須）と `TEXT_MODEL_API_KEY`（文字入力にだけ要る）を設定しておく。
  クラウドなら環境の環境変数、WSL なら `~/.bashrc` など。
- WSL では `uv` が無ければ setup.sh が入れる。Chromium が無ければ `npx playwright install chromium` で入れておく。
- claude.ai のアカウントのスキルとしても jev-ultrafast を入れている場合、クラウドでは同じスキルが2つ見える。
  片方で足りるなら `/plugin disable jev-ultrafast@kotenbu-skills`。

## 外す

```
/plugin uninstall <名前>@kotenbu-skills
/plugin marketplace remove kotenbu-skills
```
