#!/usr/bin/env python3
"""guard-main.py が期待どおり止める／通すかを確かめる。

使い方: python3 .claude/hooks/test-guard-main.py
使い捨ての git リポジトリを一時フォルダに作って試すので、このリポジトリには触らない。
guard-main.py を直したら、これを実行して 22 件すべて OK になることを確かめること。

Claude Code のフックは 終了コード2 = ブロック、それ以外 = 通過。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "guard-main.py"


def sh(args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


def make_repo(path, branch):
    path.mkdir(parents=True)
    sh(["git", "init", "-q", "-b", "main"], path)
    sh(["git", "config", "user.email", "test@example.invalid"], path)
    sh(["git", "config", "user.name", "test"], path)
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    sh(["git", "add", "a.txt"], path)
    sh(["git", "commit", "-q", "-m", "init"], path)
    if branch != "main":
        sh(["git", "switch", "-q", "-c", branch], path)
    return str(path)


def run(tmp):
    on_main = make_repo(Path(tmp) / "on-main", "main")
    on_feature = make_repo(Path(tmp) / "on-feature", "work-branch")

    # (名前, コマンド, 期待する終了コード, 実行フォルダ, 確かめたいこと)
    cases = [
        ("main_commit",          "git commit -m x",                    2, on_main,    "main でのコミット"),
        ("main_dashC_commit",    "git -C . commit -m x",               2, on_main,    "-C を挟んでも検知する"),
        ("main_dashc_commit",    "git -c user.name=a commit -m x",     2, on_main,    "-c を挟んでも検知する"),
        ("main_wrapped_bash",    'bash -c "git commit -m x"',          2, on_main,    "別コマンドで包んでも検知する"),
        ("main_piped",           "echo x | git commit -m y",           2, on_main,    "パイプでつないでも検知する"),
        ("main_merge",           "git merge feature",                  2, on_main,    "main でのマージ"),
        ("push_main",            "git push origin main",               2, on_feature, "main への push"),
        ("push_main_quoted",     'git push origin "main"',             2, on_feature, "引用符つきでも検知する"),
        ("push_head_main",       "git push origin HEAD:main",          2, on_feature, "HEAD:main 形式"),
        ("force_push",           "git push --force origin feature",    2, on_feature, "強制 push"),
        ("switch_then_commit",   "git switch main && git commit -m x", 2, on_feature, "main へ切り替えてからコミット"),
        ("checkout_then_push",   "git checkout main && git push",      2, on_feature, "同上（checkout 版）"),
        ("broken_quote",         'git push origin "main',              2, on_feature, "解釈できない形は止める"),
        ("not_a_repo",           "git commit -m x",                    2, tmp,        "ブランチを確認できないときは止める"),
        ("feature_commit",       "git commit -m x",                    0, on_feature, "作業ブランチでのコミットは通す"),
        ("feature_dashC_commit", "git -C . commit -m x",               0, on_feature, "-C つきでも作業ブランチなら通す"),
        ("push_feature",         "git push -u origin feature-x",       0, on_feature, "作業ブランチの push は通す"),
        ("switch_new_branch",    "git switch -c new-branch",           0, on_feature, "ブランチ作成は通す"),
        ("status",               "git status",                         0, on_main,    "読み取り系は main でも通す"),
        ("log",                  "git log --oneline -3",               0, on_main,    "同上"),
        ("add",                  "git add data/news.json",             0, on_main,    "add は対象外"),
        ("plain_ls",             "ls -la",                             0, on_main,    "git 以外は対象外"),
    ]

    ok = fail = 0
    print(f"{'ケース':<22} {'期待':<5} {'結果':<5} 判定  確かめたこと")
    print("-" * 92)
    for name, cmd, expect, cwd, why in cases:
        payload = json.dumps({"tool_input": {"command": cmd}, "cwd": cwd}, ensure_ascii=False)
        r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                           capture_output=True, text=True, timeout=30)
        got = r.returncode
        good = (got == 2) if expect == 2 else (got != 2)
        ok, fail = (ok + 1, fail) if good else (ok, fail + 1)
        print(f"{name:<22} {expect:<5} {got:<5} {'OK ' if good else 'NG '}  {why}")
    print("-" * 92)
    print(f"成功 {ok} / 失敗 {fail}")
    return 1 if fail else 0


with tempfile.TemporaryDirectory() as tmp:
    sys.exit(run(tmp))
