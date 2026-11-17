#!/usr/bin/env python3
"""英語版（en/）の直し忘れを防ぐフック。

- PostToolUse（Edit / Write の後）: 英語版のある日本語ページを直したら、英語版も直すよう Claude に伝える
- Stop（作業を終えようとしたとき）: tools/check_en.py で確かめ、英語版が遅れていたら作業を続けさせる

フック自体の不具合で作業を止めないよう、想定外のことが起きたら何もせずに通す。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "tools"))


def post_tool_use(data):
    from build_en import EN_PAGES
    path = Path(str((data.get("tool_input") or {}).get("file_path", "")))
    if path.parent.resolve() != ROOT.resolve() or path.name not in EN_PAGES:
        return
    msg = (f"{path.name} には英語版 en/{path.name} があります。この作業の中で、英語版の対応する箇所も同じ内容に英訳して直してください"
           "（訳し方と用語は tools/en_glossary.md）。直したら python3 tools/build_en.py と python3 tools/check_en.py --update を実行してください。")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}, ensure_ascii=False))


def stop(data):
    if data.get("stop_hook_active"):
        return  # 一度止めて続けさせた後は、繰り返し止めない（GitHub のチェックが最後の砦）
    r = subprocess.run([sys.executable, str(ROOT / "tools/check_en.py")], cwd=ROOT,
                       capture_output=True, text=True, timeout=30)
    if r.returncode == 1:
        print(json.dumps({"decision": "block", "reason": r.stdout.strip()}, ensure_ascii=False))


def main():
    try:
        data = json.load(sys.stdin)
        event = data.get("hook_event_name")
        if event == "PostToolUse":
            post_tool_use(data)
        elif event == "Stop":
            stop(data)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
