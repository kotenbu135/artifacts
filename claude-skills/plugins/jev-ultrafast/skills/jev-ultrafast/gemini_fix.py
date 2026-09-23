"""jev_ultrafast/model.py の text helper を Gemini でも通るようにする。冪等。

素の実装は OpenRouter 方言の {"reasoning": {...}} を送るが、Gemini の OpenAI 互換
エンドポイントは 400 Unknown name "reasoning" で弾く。同義の "reasoning_effort" に振り分ける。
"""

import pathlib
import sys

path = pathlib.Path(sys.argv[1])
src = path.read_text(encoding="utf-8")

if "reasoning_effort" in src:
    print("    適用済み")
    raise SystemExit(0)

old_branch = (
    '    reasoning = {"thinking": {"type": "disabled"}} if "api.deepseek.com/" in base'
    ' else {"reasoning": {"effort": "low"}}\n'
)
new_branch = (
    '    # Gemini\'s OpenAI-compatible endpoint rejects the "reasoning" object outright\n'
    '    # (400 Unknown name "reasoning"); it spells the same control "reasoning_effort".\n'
    '    gemini = "generativelanguage.googleapis.com" in base\n'
    "    if gemini:\n"
    '        reasoning = {"reasoning_effort": "low"}\n'
    '    elif "api.deepseek.com/" in base:\n'
    '        reasoning = {"thinking": {"type": "disabled"}}\n'
    "    else:\n"
    '        reasoning = {"reasoning": {"effort": "low"}}\n'
)
old_none = '        reasoning = {"reasoning": {"enabled": False}}\n'
new_none = (
    '        reasoning = {"reasoning_effort": "none"} if gemini else {"reasoning": {"enabled": False}}\n'
    '    if os.environ.get("TEXT_MODEL_REASONING") == "omit":\n'
    "        reasoning = {}\n"
)

for old in (old_branch, old_none):
    if src.count(old) != 1:
        raise SystemExit(
            f"    上流が変わっていて当てられない: {path}\n"
            "    field_text() の reasoning の組み立てを手で直すこと"
        )

path.write_text(src.replace(old_branch, new_branch).replace(old_none, new_none), encoding="utf-8")
print("    適用した")
