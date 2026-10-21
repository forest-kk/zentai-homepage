#!/usr/bin/env python3
"""総務の作業で main を直接変えないためのガード（Claude Code の PreToolUse フック）。

GitHub の無料プランでは Private リポジトリに main の保護を掛けられないので、
Claude Code が main のままコミット・push・マージしようとしたら止める。
止めたときは理由を Claude に返し、ブランチを作り直すよう促す。

これは「うっかり防止」であって、セキュリティ上の防御ではない。
このフックが効くのは、このリポジトリで Claude Code の Bash を使うときだけ。
普通のターミナル、別のパソコン、GitHub の Web 画面からの操作には効かない。
確実に止めるには GitHub 側のブランチ保護が要る。

判断できないときは通さずに止める（fail-closed）。
"""
import json
import re
import shlex
import subprocess
import sys

# main 上で実行させたくない git の部分コマンド
GUARDED = ("push", "commit", "merge", "rebase", "cherry-pick", "revert", "am")
# git 本体の前置オプションのうち、後ろに値を取るもの（読み飛ばすときに2つ進める）
OPTS_WITH_VALUE = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")
# git を包む形で呼ぶことがあるコマンド（中身も調べる）
WRAPPERS = ("bash", "sh", "zsh", "env", "command", "nohup", "time", "sudo", "doas")
# ブランチを切り替える部分コマンド
SWITCHERS = ("switch", "checkout")


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def tokenize(part):
    """コマンドの一部を単語に分ける。引用符は外す（"main" と main を同じに扱うため）。"""
    try:
        return shlex.split(part)
    except ValueError:
        # 引用符が閉じていないなど、形を解釈できない。安全側に倒して止める
        block("コマンドの形を解釈できませんでした。main を触っていないか確かめて、短く分けて実行してください。")


def unwrap(words, depth=0):
    """bash -c "git ..." のように包まれている場合、中身の git コマンドを取り出す。"""
    if depth > 3 or not words:
        return words
    head = words[0].rsplit("/", 1)[-1]  # /bin/bash → bash
    if head not in WRAPPERS:
        return words
    for i, w in enumerate(words[1:], 1):
        if w == "-c" and i + 1 < len(words):
            return unwrap(tokenize(words[i + 1]), depth + 1)
    # env FOO=bar git ... のように -c が無い形は、先頭から剥がして続きを見る
    rest = [w for w in words[1:] if "=" not in w.split(" ")[0] or not w[0].isalpha()]
    return unwrap(rest, depth + 1) if rest != words else words


def git_subcommand(words):
    """git の前置オプションを読み飛ばして、実際の部分コマンドと残りの引数を返す。"""
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in OPTS_WITH_VALUE else 1
    if i >= len(words):
        return None, []
    return words[i], words[i + 1:]


def current_branch(cwd):
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception as ex:  # git が無い、権限がない等
        block(f"いまのブランチを確認できませんでした（{ex}）。"
              "`git switch -c 作業用ブランチ名` でブランチを作ってから続けてください。")
    if r.returncode != 0:
        block("いまのブランチを確認できませんでした。このフォルダが作業用の clone か確認してください。")
    return r.stdout.strip()


def main():
    data = json.load(sys.stdin)
    cmd = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd") or "."

    # 同じコマンド列の中で main へ切り替えた場合、その後のコミットは main 上になる
    switched_to_main = False

    for part in re.split(r"&&|\|\||\||;|&|\n", cmd):
        words = unwrap(tokenize(part))
        if len(words) < 2 or words[0].rsplit("/", 1)[-1] != "git":
            continue
        sub, args = git_subcommand(words)
        if sub is None:
            continue

        if sub in SWITCHERS:
            # git switch main / git checkout main を検知しておく
            if any(a == "main" for a in args if not a.startswith("-")):
                switched_to_main = True
            continue

        positional = [a for a in args if not a.startswith("-")]
        if sub == "push":
            if any(a in ("-f", "--mirror", "--all", "--delete", "-d") or a.startswith("--force") for a in args):
                block("強制 push・まとめて push・ブランチ削除の push は禁止です。管理者に相談してください。")
            if any(re.search(r"(^|:|\+)(refs/heads/)?(main|HEAD)$", a) for a in positional[1:]):
                block("main への push は禁止です。作業用ブランチを push して、プルリクエストを作ってください。")
            if len(positional) >= 2:
                continue  # 送り先のブランチ名を明示している（main 以外）

        if sub in GUARDED:
            branch = "main" if switched_to_main else current_branch(cwd)
            if branch == "main":
                block(
                    f"いまは main ブランチにいるので git {sub} は止めました。"
                    "`git switch -c 作業用ブランチ名` でブランチを作ってから続けてください。"
                )

    sys.exit(0)


try:
    main()
except SystemExit:
    raise
except Exception as ex:
    # 想定外の失敗で素通りさせない
    block(f"ガードの処理に失敗しました（{ex}）。main を触っていないか確かめてから、もう一度実行してください。")
