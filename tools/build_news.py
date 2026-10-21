#!/usr/bin/env python3
"""data/news.json から お知らせ一覧・記事詳細・トップの最新お知らせ を生成する。

記事を足したり直したりしたら、サイト直下で `python3 tools/build_news.py` を実行する。
ヘッダー・フッター等の共通部分は company.html から取り込むので、各ページとずれない。
"""
import html, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
news = json.loads((ROOT / "data/news.json").read_text(encoding="utf-8"))
news.sort(key=lambda o: o["date"], reverse=True)

# ---------- 入力の検査 ----------
# 記事データはHTMLに埋め込まれるので、生成する前に形を確かめる。
# おかしい値があればここで止めて、どの記事の何が悪いかを日本語で知らせる。
ALLOWED_CAT = {"お知らせ", "トピックス"}
MEDIA_RE = re.compile(r"media/[\w./-]+")
URL_RE = re.compile(r"https://[\w./:%-]+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _stop(msg):
    raise SystemExit(f"data/news.json を直してください — {msg}")


_ids = [o.get("id") for o in news]
_dup = sorted({i for i in _ids if _ids.count(i) > 1}, key=str)
if _dup:
    _max = max((i for i in _ids if isinstance(i, int)), default=0)
    _stop(f"id が重複しています: {_dup}。id は記事ごとに別の数にしてください（いまの最大は {_max} なので次は {_max + 1}）")

for _o in news:
    _t = _o.get("title", "(タイトル未設定)")
    if not isinstance(_o.get("id"), int):
        _stop(f"「{_t}」の id は数字にしてください（いまは {_o.get('id')!r}）")
    if not DATE_RE.fullmatch(str(_o.get("date", ""))):
        _stop(f"「{_t}」の date は 2026-10-25 の形にしてください（いまは {_o.get('date')!r}）")
    if _o.get("cat") not in ALLOWED_CAT:
        _stop(f"「{_t}」の cat は お知らせ か トピックス にしてください（いまは {_o.get('cat')!r}）")
    for _im in _o.get("images", []):
        if not MEDIA_RE.fullmatch(str(_im.get("src", ""))):
            _stop(f"「{_t}」の画像は media/ の中のファイルを指してください（いまは {_im.get('src')!r}）")
        if not (isinstance(_im.get("w"), int) and isinstance(_im.get("h"), int) and _im["h"] > 0):
            _stop(f"「{_t}」の画像の w と h は正の数にしてください（いまは {_im.get('w')!r}, {_im.get('h')!r}）")
    for _v in _o.get("videos", []):
        if not (MEDIA_RE.fullmatch(str(_v)) or URL_RE.fullmatch(str(_v))):
            _stop(f"「{_t}」の動画は media/ の中か https:// のURLにしてください（いまは {_v!r}）")

tpl = (ROOT / "company.html").read_text(encoding="utf-8")
def grab(pattern):
    return re.search(pattern, tpl, re.S).group(0)

HEAD_LINKS = grab(r'<meta name="theme-color".*?<link rel="stylesheet" href="css/company.css">')
LOADER = grab(r'<div class="loader".*?\n</div>\n')
CHROME = grab(r'<div class="cursor-dot".*?<div class="progress"[^>]*></div>')
HEADER = grab(r'<header class="site-header".*?</header>')
MOBILE = grab(r'<div class="mobile-menu".*?\n</div>')
FOOTER = grab(r'<footer class="site-footer">.*?</footer>')
TOTOP = grab(r'<button class="to-top".*?</button>')

HEADER = HEADER.replace(' class="active"', "").replace('<a href="news.html">お知らせ</a>', '<a href="news.html" class="active">お知らせ</a>')
LOADER = re.sub(r'<div class="loader-sub">[^<]*</div>', '<div class="loader-sub">NEWS</div>', LOADER)

e = html.escape
def fmt(d):
    y, m, dd = d.split("-")
    return f"{y}.{m}.{dd}"
def linkify(t):
    t = e(t).replace("\n", "<br>")
    return re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)

def page(title, desc, og_image, body):
    return f"""<!DOCTYPE html>
<html lang="ja" class="no-js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)} | 株式会社フォレスト</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)} | 株式会社フォレスト">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(og_image)}">
{HEAD_LINKS}
<link rel="stylesheet" href="css/news.css">
</head>
<body class="is-loading">

{LOADER}
{CHROME}

{HEADER}

{MOBILE}

<main id="top">
{body}
</main>

{FOOTER}

{TOTOP}

<script src="js/main.js"></script>
</body>
</html>
"""

def thumb(o, cls="nw-thumb"):
    if o["images"]:
        im = o["images"][0]
        wide = im["w"] / im["h"] > 2
        return (f'<figure class="{cls}{" is-banner" if wide else ""}"><img src="{e(im["src"])}" width="{int(im["w"])}" '
                f'height="{int(im["h"])}" loading="lazy" decoding="async" alt=""></figure>')
    return (f'<figure class="{cls} is-blank" aria-hidden="true"><img src="media/logo.png" width="1220" height="295" '
            f'loading="lazy" decoding="async" alt=""></figure>')

# ---------- 一覧 ----------
cats = ["お知らせ", "トピックス"]
counts = {c: sum(1 for o in news if o["cat"] == c) for c in cats}
tabs = [f'<button type="button" class="nw-tab is-active" data-filter="all" aria-pressed="true">すべて<span>{len(news)}</span></button>']
tabs += [f'<button type="button" class="nw-tab" data-filter="{c}" aria-pressed="false">{c}<span>{counts[c]}</span></button>' for c in cats]
cards = []
for i, o in enumerate(news):
    d = f' data-delay="{min(i, 5) * 0.05:.2f}"' if i else ""
    cards.append(f"""        <li class="nw-card" data-cat="{e(o['cat'])}" data-reveal{d}>
          <a href="news-{int(o['id'])}.html">
            {thumb(o)}
            <div class="nw-card-body">
              <p class="nw-meta"><time datetime="{e(o['date'])}">{e(fmt(o['date']))}</time><span class="nw-cat">{e(o['cat'])}</span></p>
              <h2>{e(o['title'])}</h2>
              <p class="nw-excerpt">{e(o['excerpt'])}</p>
            </div>
          </a>
        </li>""")

list_body = f"""
  <section class="cp-head">
    <div class="container">
      <p class="s-eyebrow" data-reveal><span class="dot"></span>NEWS</p>
      <h1 class="cp-title" data-split>お知らせ</h1>
      <div class="nw-tabs" role="group" aria-label="カテゴリで絞り込む" data-reveal data-delay="0.4">
        {''.join(tabs)}
      </div>
    </div>
  </section>

  <section class="nw-list-sec section">
    <div class="container">
      <ul class="nw-grid" id="nwGrid">
{chr(10).join(cards)}
      </ul>
      <p class="nw-empty" id="nwEmpty" hidden>該当するお知らせはありません。</p>
    </div>
  </section>

<script>
(() => {{
  const tabs = document.querySelectorAll(".nw-tab");
  const cards = document.querySelectorAll(".nw-card");
  tabs.forEach((t) => t.addEventListener("click", () => {{
    const f = t.dataset.filter;
    tabs.forEach((x) => {{ const on = x === t; x.classList.toggle("is-active", on); x.setAttribute("aria-pressed", on); }});
    let n = 0;
    cards.forEach((c) => {{ const show = f === "all" || c.dataset.cat === f; c.hidden = !show; if (show) {{ n++; c.classList.add("is-in"); }} }});
    document.getElementById("nwEmpty").hidden = n > 0;
  }}));
}})();
</script>
"""
(ROOT / "news.html").write_text(
    page("お知らせ", "株式会社フォレストのお知らせ一覧。新倉庫の竣工、地域活動、スポーツ支援などの最新情報をお届けします。",
         "media/hero-poster.jpg", list_body), encoding="utf-8")

# ---------- 詳細 ----------
for i, o in enumerate(news):
    newer = news[i - 1] if i > 0 else None
    older = news[i + 1] if i + 1 < len(news) else None
    paras = []
    for p in o["paras"]:
        tag = "h2" if p["tag"] in ("h2", "h3", "h4") else "p"
        paras.append(f"        <{tag}>{linkify(p['text'])}</{tag}>")
    gallery = ""
    if o["images"]:
        figs = []
        for n, im in enumerate(o["images"], 1):
            # ロゴなど切り抜きたくない画像は fit: "contain" を指定する
            cls = ' class="is-contain"' if im.get("fit") == "contain" else ""
            alt = im.get("alt") or (o["title"] + " の写真 " + str(n))
            figs.append(
                '          <figure%s><img src="%s" width="%s" height="%s" loading="lazy" decoding="async" alt="%s"></figure>'
                % (cls, e(im["src"]), int(im["w"]), int(im["h"]), e(alt))
            )
        gallery = '\n        <div class="nw-gallery nw-gallery--%d">\n%s\n        </div>' % (
            min(len(o["images"]), 4), "\n".join(figs))
    videos = ""
    if o.get("videos"):
        videos = "\n        <div class=\"nw-videos\">\n" + "\n".join(
            f'          <video controls preload="metadata" playsinline src="{e(v)}"></video>' for v in o["videos"]) + "\n        </div>"
    def pager(x, label, cls):
        if not x:
            return f'<span class="nw-pager-item {cls} is-empty"></span>'
        return (f'<a class="nw-pager-item {cls}" href="news-{int(x["id"])}.html"><span>{label}</span>'
                f'<strong>{e(x["title"])}</strong></a>')
    body = f"""
  <section class="nw-article-head">
    <div class="container nw-narrow">
      <p class="wd-breadcrumb" data-reveal><a href="index.html">HOME</a><span>/</span><a href="news.html">お知らせ</a><span>/</span><em>記事</em></p>
      <p class="nw-meta" data-reveal data-delay="0.05"><time datetime="{e(o['date'])}">{e(fmt(o['date']))}</time><span class="nw-cat">{e(o['cat'])}</span></p>
      <h1 class="nw-title" data-reveal data-delay="0.1">{e(o['title'])}</h1>
    </div>
  </section>

  <article class="nw-article section">
    <div class="container nw-narrow">
      <div class="nw-body" data-reveal>
{chr(10).join(paras)}{gallery}{videos}
      </div>

      <nav class="nw-pager" aria-label="前後の記事">
        {pager(older, "前の記事", "is-prev")}
        {pager(newer, "次の記事", "is-next")}
      </nav>
      <p class="nw-back"><a class="btn btn-ghost magnetic" href="news.html">お知らせ一覧へ戻る</a></p>
    </div>
  </article>
"""
    og = o["images"][0]["src"] if o["images"] else "media/hero-poster.jpg"
    (ROOT / f"news-{o['id']}.html").write_text(page(o["title"], o["excerpt"], og, body), encoding="utf-8")

# ---------- トップの最新お知らせ ----------
index = (ROOT / "index.html").read_text(encoding="utf-8")
latest = []
for i, o in enumerate(news[:5]):
    d = f' data-delay="{i * 0.06:.2f}"' if i else ""
    latest.append(f"""        <li data-reveal{d}><a href="news-{int(o['id'])}.html">{thumb(o, 'n-thumb')}<time datetime="{e(o['date'])}">{e(fmt(o['date']))}</time><span class="n-cat">{e(o['cat'])}</span><p>{e(o['title'])}</p><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a></li>""")
index, n1 = re.subn(r'<ul class="news-list">.*?</ul>', '<ul class="news-list">\n' + "\n".join(latest) + "\n      </ul>", index, count=1, flags=re.S)
index = re.sub(r'(<a class="link-more magnetic" href=")#news(">一覧を見る)', r'\1news.html\2', index)
(ROOT / "index.html").write_text(index, encoding="utf-8")

print(f"news.html + 記事 {len(news)}本 を生成 / トップ最新 {len(latest)}件（置換 {n1}）")
