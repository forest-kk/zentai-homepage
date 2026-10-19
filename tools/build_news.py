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
<meta property="og:image" content="{og_image}">
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
        return (f'<figure class="{cls}{" is-banner" if wide else ""}"><img src="{im["src"]}" width="{im["w"]}" '
                f'height="{im["h"]}" loading="lazy" decoding="async" alt=""></figure>')
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
    cards.append(f"""        <li class="nw-card" data-cat="{o['cat']}" data-reveal{d}>
          <a href="news-{o['id']}.html">
            {thumb(o)}
            <div class="nw-card-body">
              <p class="nw-meta"><time datetime="{o['date']}">{fmt(o['date'])}</time><span class="nw-cat">{o['cat']}</span></p>
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
                % (cls, im["src"], im["w"], im["h"], e(alt))
            )
        gallery = '\n        <div class="nw-gallery nw-gallery--%d">\n%s\n        </div>' % (
            min(len(o["images"]), 4), "\n".join(figs))
    videos = ""
    if o.get("videos"):
        videos = "\n        <div class=\"nw-videos\">\n" + "\n".join(
            f'          <video controls preload="metadata" playsinline src="{v}"></video>' for v in o["videos"]) + "\n        </div>"
    def pager(x, label, cls):
        if not x:
            return f'<span class="nw-pager-item {cls} is-empty"></span>'
        return (f'<a class="nw-pager-item {cls}" href="news-{x["id"]}.html"><span>{label}</span>'
                f'<strong>{e(x["title"])}</strong></a>')
    body = f"""
  <section class="nw-article-head">
    <div class="container nw-narrow">
      <p class="wd-breadcrumb" data-reveal><a href="index.html">HOME</a><span>/</span><a href="news.html">お知らせ</a><span>/</span><em>記事</em></p>
      <p class="nw-meta" data-reveal data-delay="0.05"><time datetime="{o['date']}">{fmt(o['date'])}</time><span class="nw-cat">{o['cat']}</span></p>
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
    latest.append(f"""        <li data-reveal{d}><a href="news-{o['id']}.html">{thumb(o, 'n-thumb')}<time datetime="{o['date']}">{fmt(o['date'])}</time><span class="n-cat">{o['cat']}</span><p>{e(o['title'])}</p><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a></li>""")
index, n1 = re.subn(r'<ul class="news-list">.*?</ul>', '<ul class="news-list">\n' + "\n".join(latest) + "\n      </ul>", index, count=1, flags=re.S)
index = re.sub(r'(<a class="link-more magnetic" href=")#news(">一覧を見る)', r'\1news.html\2', index)
(ROOT / "index.html").write_text(index, encoding="utf-8")

print(f"news.html + 記事 {len(news)}本 を生成 / トップ最新 {len(latest)}件（置換 {n1}）")
