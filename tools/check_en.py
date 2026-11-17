#!/usr/bin/env python3
"""日本語ページと英語版（en/）がそろっているかを確かめる。

英語版を最後に直したときの日本語ページの中身（<head> の説明文と <main>）を
data/en-sync.json に指紋（ハッシュ）として残しておき、いまの日本語ページと比べる。
日本語ページだけが変わっていたら「英語版の更新が必要」として終了コード1で止まる。

  python3 tools/check_en.py            確かめるだけ（GitHub のチェックと Claude Code が使う）
  python3 tools/check_en.py --update   英語版を直し終えたあとに、いまの状態を記録する

--update の前に、英語版に日本語が残っていないかも確かめる。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "data/en-sync.json"
sys.path.insert(0, str(ROOT / "tools"))
from build_en import EN_PAGES  # noqa: E402  英語版のあるページの一覧は1か所で持つ

JP = re.compile(r"[぀-ヿ一-鿿]")


def fingerprint(page):
    """英語版に訳すべき部分（ページの説明と本文）だけの指紋"""
    s = (ROOT / page).read_text(encoding="utf-8")
    head = re.findall(r"<title>.*?</title>|<meta (?:name=\"description\"|property=\"og:[^\"]+\")[^>]*>", s, re.S)
    main = re.search(r"<main\b.*?</main>", s, re.S)
    body = "\n".join(head) + (main.group(0) if main else "")
    body = re.sub(r"\s+", " ", body).strip()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def leftover_japanese(page):
    s = (ROOT / "en" / page).read_text(encoding="utf-8")
    s = re.sub(r'<a [^>]*lang="ja".*?</a>|query=[^"&]*', "", s, flags=re.S)
    return "".join(sorted(set(JP.findall(s))))


def main():
    saved = json.loads(SYNC.read_text(encoding="utf-8")) if SYNC.exists() else {}
    now = {p: fingerprint(p) for p in EN_PAGES}

    if "--update" in sys.argv:
        bad = {p: j for p in EN_PAGES if (j := leftover_japanese(p))}
        if bad:
            for p, j in bad.items():
                print(f"en/{p} に日本語が残っています: {j[:30]}")
            sys.exit("英語版を直してから、もう一度 --update してください")
        SYNC.write_text(json.dumps(now, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"英語版の状態を記録しました（{len(now)} ページ）")
        return

    stale = [p for p in EN_PAGES if saved.get(p) != now[p]]
    if not stale:
        print("英語版はそろっています")
        return
    print("日本語ページが変わったのに、英語版がまだ直っていません:")
    for p in stale:
        print(f"  {p}  →  en/{p}")
    print("英語版を同じ内容に訳して直し、python3 tools/build_en.py と python3 tools/check_en.py --update を実行してください。")
    print("訳し方は tools/en_glossary.md を参照。")
    sys.exit(1)


if __name__ == "__main__":
    main()
