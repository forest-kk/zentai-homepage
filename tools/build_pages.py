#!/usr/bin/env python3
"""Cloudflare Pages 用に、公開するファイルだけを dist/ に集める。

Cloudflare Pages の設定：
  ビルドコマンド      python3 tools/build_pages.py
  ビルド出力ディレクトリ  dist

- 公開しないファイルは .vercelignore と同じ（serve.py・tools/・data/・CLAUDE.md・.claude/・.github/・*.bak など）。
  Vercel と Cloudflare で同じ中身が出るように、除外の一覧は .vercelignore の1か所だけで管理する。
- 応答ヘッダー（検索に出さない・セキュリティ・写真のキャッシュ）は vercel.json から dist/_headers を作る。
  ヘッダーを変えるときは vercel.json だけを直せばよい。
- 1ファイル 25MiB を超えると Cloudflare Pages に載らないので、ここで止める。
- 手元で試すときは出力先を指定する：python3 tools/build_pages.py /tmp/pages-test
  （出力先がすでにあって空でなければ止まる。古い中身を消さないため）
"""
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = 25 * 1024 * 1024  # Cloudflare Pages の1ファイルの上限
ALWAYS_SKIP = {'vercel.json', '.vercelignore', '.gitignore', '.gitattributes'}


def ignore_patterns():
    pats = []
    with open(os.path.join(ROOT, '.vercelignore'), encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                pats.append(line)
    return pats


def ignored(path, pats):
    parts = path.split('/')
    for p in pats:
        if p.endswith('/'):  # フォルダ
            if p.rstrip('/') in parts[:-1]:
                return True
        elif fnmatch.fnmatch(parts[-1], p) or fnmatch.fnmatch(path, p):
            return True
    return False


def tracked_files():
    """リポジトリに入っているファイル（git が無ければフォルダをたどる）"""
    try:
        out = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
        return [p for p in out.decode('utf-8').split('\0') if p]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for d, dirs, names in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x not in ('.git', 'dist', 'node_modules')]
            for n in names:
                files.append(os.path.relpath(os.path.join(d, n), ROOT).replace(os.sep, '/'))
        return files


def to_glob(source):
    """vercel.json の source（/(.*) や /media/(.*)）を _headers の形（/* や /media/*）にする"""
    g = source.replace('(.*)', '*')
    if re.search(r'[()\[\]?+]', g):
        sys.exit(f'vercel.json の source を _headers に直せません：{source}')
    return g


def headers_file():
    with open(os.path.join(ROOT, 'vercel.json'), encoding='utf-8') as f:
        cfg = json.load(f)
    unknown = set(cfg) - {'headers'}
    if unknown:
        sys.exit(f'vercel.json に _headers へ移せない設定があります：{", ".join(sorted(unknown))}')
    lines = ['# tools/build_pages.py が vercel.json から作ったファイル。直すときは vercel.json を直す', '']
    for rule in cfg.get('headers', []):
        lines.append(to_glob(rule['source']))
        for h in rule['headers']:
            lines.append(f"  {h['key']}: {h['value']}")
        lines.append('')
    return '\n'.join(lines)


def main():
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist'))
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f'出力先が空ではありません：{out}（中身を確かめて、別の場所を指定してください）')
    pats = ignore_patterns()
    files = [p for p in tracked_files() if p not in ALWAYS_SKIP and not p.startswith('dist/') and not ignored(p, pats)]
    too_big = [(p, os.path.getsize(os.path.join(ROOT, p))) for p in files if os.path.getsize(os.path.join(ROOT, p)) > LIMIT]
    if too_big:
        sys.exit('25MiB を超えるファイルは Cloudflare Pages に載りません：' + '、'.join(f'{p}（{s / 1048576:.1f}MiB）' for p, s in too_big))
    total = 0
    for p in files:
        src, dst = os.path.join(ROOT, p), os.path.join(out, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        total += os.path.getsize(src)
    with open(os.path.join(out, '_headers'), 'w', encoding='utf-8') as f:
        f.write(headers_file())
    print(f'{len(files)} ファイル（{total / 1048576:.1f}MiB）と _headers を {out} に出しました')


if __name__ == '__main__':
    main()
