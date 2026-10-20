#!/usr/bin/env python3
"""総務の作業で main を直接変えないためのガード（Claude Code の PreToolUse フック）。

GitHub の無料プランでは Private リポジトリに main の保護を掛けられないので、
Claude Code が main のままコミット・push・マージしようとしたら止める。
止めたときは理由を Claude に返し、ブランチを作り直すよう促す。
"""
import json
import re
import subprocess
import sys

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")
cwd = data.get("cwd") or "."


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


# 1つのコマンドに && や ; で複数つないでいる場合も、それぞれを確かめる
for part in re.split(r"&&|\|\||;|\n", cmd):
    words = part.split()
    if len(words) < 2 or words[0] != "git":
        continue
    sub = words[1]
    args = words[2:]

    positional = [a for a in args if not a.startswith("-")]
    if sub == "push":
        if any(a in ("-f", "--mirror", "--all", "--delete", "-d") or a.startswith("--force") for a in args):
            block("強制 push・まとめて push・ブランチ削除の push は禁止です。管理者に相談してください。")
        if any(re.search(r"(^|:|\+)(refs/heads/)?(main|HEAD)$", a) for a in positional[1:]):
            block("main への push は禁止です。作業用ブランチを push して、プルリクエストを作ってください。")
        if len(positional) >= 2:
            continue  # 送り先のブランチ名を明示している（main 以外）

    if sub in ("push", "commit", "merge", "rebase", "cherry-pick", "revert", "am"):
        branch = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True,
        ).stdout.strip()
        if branch == "main":
            block(
                f"いまは main ブランチにいるので git {sub} は止めました。"
                "`git switch -c 作業用ブランチ名` でブランチを作ってから続けてください。"
            )

sys.exit(0)
