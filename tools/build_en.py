#!/usr/bin/env python3
"""英語版（en/）の共通部分をそろえ、日本語版に言語切替えを付ける。

en/*.html の本文（<head> の説明文と <main>）は人が訳して置く。このスクリプトは
次の機械的な部分だけを受け持つ。何度実行しても結果は同じになる。

  英語版:  lang="en" にする / ヘッダー・メニュー・フッターを英語の共通版に差し替える /
           css・js・media のパスを ../ 付きにする / 英語版の無いページへのリンクを ../ に向ける /
           「日本語」への切替えリンクを付ける
  日本語版: ヘッダーに「EN」の切替えリンクを付ける（英語版が無いページは en/index.html へ）

お知らせ（news*.html）は tools/build_news.py が company.html のヘッダーを写すので、ここでは触らない。

使い方: サイト直下で `python3 tools/build_en.py`
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "en"

# 英語版があるページ（en/ に同名で置く）
EN_PAGES = [
    "index.html", "company.html", "sustainability.html", "office.html", "links.html",
    "wood.html", "logistics.html", "transport.html", "tire.html", "weaving.html",
    "hotel.html", "realestate.html", "solar.html",
]
# 日本語だけのページ（英語版から ../ で日本語版へ飛ばす）
JA_ONLY = ["recruit.html", "workstyle.html", "news.html"]

# ナビの現在地（英語版）
ACTIVE = {
    "company.html": "company.html", "office.html": "office.html", "links.html": "links.html",
    "sustainability.html": "sustainability.html",
    **{p: "index.html#business" for p in [
        "wood.html", "logistics.html", "transport.html", "tire.html", "weaving.html",
        "hotel.html", "realestate.html", "solar.html"]},
}

EXT = ' target="_blank" rel="noopener"'
SNS = [
    ("YouTube", "https://youtube.com/@forest_kumamoto_ymg"),
    ("Instagram", "https://www.instagram.com/1950.8.16_forest"),
    ("TikTok", "https://www.tiktok.com/@forest_kumamoto_ymg"),
]


def lang_switch_ja(page):
    """日本語版のヘッダーに置く「EN」"""
    href = f"en/{page}" if page in EN_PAGES else "en/index.html"
    return f'<a class="lang-switch" href="{href}" hreflang="en" lang="en" aria-label="English">EN</a>'


def lang_switch_en(page):
    """英語版のヘッダーに置く「日本語」"""
    return f'<a class="lang-switch" href="../{page}" hreflang="ja" lang="ja" aria-label="日本語のページへ">日本語</a>'


def header_en(page):
    items = [
        ("company.html", "Company"),
        ("index.html#business", "Our Business"),
        ("office.html", "Locations"),
        ("sustainability.html", "Safety &amp; Environment"),
        ("links.html", "Links"),
    ]
    act = ACTIVE.get(page)
    nav = "\n".join(
        '    <a href="%s"%s>%s</a>' % (h, ' class="active"' if h == act else "", t) for h, t in items)
    return f"""<header class="site-header" id="header">
  <a class="brand" href="index.html" aria-label="FOREST Co., Ltd.">
    <img class="brand-logo" src="../media/logo.png" width="1220" height="295" alt="FOREST Co., Ltd.">
  </a>
  <nav class="gnav" aria-label="Main navigation">
{nav}
  </nav>
  {lang_switch_en(page)}
  <a class="header-cta magnetic" href="index.html#contact">Contact</a>
  <button class="menu-btn" id="menuBtn" aria-label="Open menu" aria-expanded="false"><span></span><span></span></button>
</header>"""


def mobile_en(page):
    items = [
        ("company.html", "Company"),
        ("index.html#business", "Our Business"),
        ("office.html", "Locations"),
        ("sustainability.html", "Safety &amp; Environment"),
        ("links.html", "Links"),
        ("index.html#contact", "Contact"),
        (f"../{page}", "日本語"),
    ]
    nav = "\n".join(
        '    <a href="%s"%s><em>%02d</em>%s</a>' % (h, ' lang="ja" hreflang="ja"' if h.startswith("../") else "", i, t)
        for i, (h, t) in enumerate(items, 1))
    return f"""<div class="mobile-menu" id="mobileMenu">
  <nav aria-label="Mobile navigation">
{nav}
  </nav>
  <p class="mm-foot">FOREST CO., LTD. — YAMAGA, KUMAMOTO</p>
</div>"""


def footer_en(ja_footer):
    # SNS のアイコン（SVG）は日本語版のフッターから流用する
    icons = dict(re.findall(r'aria-label="(\w+)（新しいタブで開きます）">(<svg.*?</svg>)', ja_footer, re.S))
    sns = "\n".join(
        f'          <li><a href="{u}"{EXT} aria-label="{n} (opens in a new tab)">{icons[n]}</a></li>'
        for n, u in SNS)
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="foot-top">
      <a class="brand brand--footer" href="index.html">
        <img class="brand-logo" src="../media/logo-white.png" width="1220" height="295" alt="FOREST Co., Ltd.">
      </a>
      <nav class="foot-nav" aria-label="Footer navigation">
        <a href="company.html">Company</a>
        <a href="sustainability.html">Safety &amp; Environment</a>
        <a href="index.html#business">Our Business</a>
        <a href="office.html">Locations</a>
        <a href="../news.html" hreflang="ja">News (Japanese)</a>
        <a href="../recruit.html" hreflang="ja">Careers (Japanese)</a>
        <a href="../workstyle.html" hreflang="ja">Working at FOREST (Japanese)</a>
        <a href="links.html">Links</a>
        <a href="index.html#contact">Contact</a>
      </nav>
      <div class="foot-sns-wrap">
        <p class="foot-sns-label">Follow us</p>
        <ul class="foot-sns">
{sns}
        </ul>
      </div>
    </div>
    <div class="foot-bottom">
      <p>© 2026 FOREST Co., Ltd. All Rights Reserved.</p>
      <a href="https://www.forest-kk.co.jp/privacy/"{EXT} hreflang="ja">Privacy Policy (Japanese)</a>
    </div>
  </div>
</footer>"""


TOTOP_EN = """<button class="to-top" id="toTop" aria-label="Back to top">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M6 11l6-6 6 6"/></svg>
</button>"""

BLOCKS = {
    "header": r'<header class="site-header".*?</header>',
    "mobile": r'<div class="mobile-menu".*?\n</div>',
    "footer": r'<footer class="site-footer">.*?</footer>',
    "totop": r'<button class="to-top".*?</button>',
}
LANG_SW = re.compile(r'\s*<a class="lang-switch"[^>]*>[^<]*</a>')


def sub1(pattern, repl, s, what):
    s2, n = re.subn(pattern, lambda _m: repl, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{what} が見つかりません")
    return s2


def fix_paths(s):
    # 素材は1つ上の階層にある
    s = re.sub(r'((?:src|href|content|poster)=")(?=(?:css|js|media)/)', r"\1../", s)
    # 英語版が無いページは日本語版へ
    for p in JA_ONLY + ["news-"]:
        s = re.sub(rf'(href=")(?={re.escape(p)})', r"\1../", s)
    return s


def build_en(page, ja_footer):
    path = EN / page
    s = path.read_text(encoding="utf-8")
    s = re.sub(r'<html lang="[^"]*"', '<html lang="en"', s, count=1)
    # パスを直してから共通部分を差し込む（2回目以降の実行で ../../ にならないよう、いったん外して付け直す）
    s = fix_paths(s.replace('="../', '="'))
    s = sub1(BLOCKS["header"], header_en(page), s, f"en/{page} のヘッダー")
    s = sub1(BLOCKS["mobile"], mobile_en(page), s, f"en/{page} のメニュー")
    s = sub1(BLOCKS["footer"], footer_en(ja_footer), s, f"en/{page} のフッター")
    s = sub1(BLOCKS["totop"], TOTOP_EN, s, f"en/{page} の上へ戻るボタン")
    s = re.sub(r'(<div class="loader-logo"[^>]*>\s*<img [^>]*alt=")[^"]*"', r'\1FOREST Co., Ltd."', s)
    path.write_text(s, encoding="utf-8")


def build_ja(page):
    path = ROOT / page
    s = path.read_text(encoding="utf-8")
    s = LANG_SW.sub("", s)
    s, n = re.subn(r'(\n  )(<a class="header-cta)', rf"\1{lang_switch_ja(page)}\1\2", s, count=1)
    if n != 1:
        raise SystemExit(f"{page} のヘッダーにお問い合わせボタンが見つかりません")
    path.write_text(s, encoding="utf-8")


ja_footer = re.search(BLOCKS["footer"], (ROOT / "company.html").read_text(encoding="utf-8"), re.S).group(0)
missing = [p for p in EN_PAGES if not (EN / p).exists()]
if missing:
    raise SystemExit(f"en/ に訳したページがありません: {missing}")
for p in EN_PAGES:
    build_en(p, ja_footer)
for p in EN_PAGES + ["recruit.html", "workstyle.html"]:
    build_ja(p)

# 取り残しの確認：英語版の本文に日本語が残っていないか
JP = re.compile(r"[぀-ヿ一-鿿]")
for p in EN_PAGES:
    s = (EN / p).read_text(encoding="utf-8")
    s = re.sub(r'<a [^>]*lang="ja".*?</a>|query=[^"&]*', "", s, flags=re.S)
    left = sorted(set(JP.findall(s)))
    if left:
        print(f"注意: en/{p} に日本語が残っています: {''.join(left)[:40]}")
print(f"英語版 {len(EN_PAGES)} ページ・日本語版 {len(EN_PAGES) + 2} ページを更新")
