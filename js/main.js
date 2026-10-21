/* ============================================================
   FOREST Co., Ltd. — interactions
   ============================================================ */
(() => {
  "use strict";

  const prefersReduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = matchMedia("(pointer: coarse)").matches;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

  /* ---------- Split text ---------- */
  $$("[data-split]").forEach((el) => {
    const base = parseFloat(el.dataset.delay || 0);
    const text = el.textContent;
    el.textContent = "";
    [...text].forEach((ch, i) => {
      const s = document.createElement("span");
      s.className = "ch";
      s.textContent = ch === " " ? " " : ch;
      s.style.transitionDelay = `${(base + i * 0.05).toFixed(2)}s`;
      el.appendChild(s);
    });
  });

  /* ---------- Reveal observers（ローダー完了後に起動） ---------- */
  function startObservers() {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const el = e.target;
          const d = parseFloat(el.dataset.delay || 0);
          if (el.hasAttribute("data-reveal") && d) el.style.transitionDelay = `${d}s`;
          el.classList.add("is-in");
          io.unobserve(el);
        });
      },
      { threshold: 0.18, rootMargin: "0px 0px -6% 0px" }
    );
    $$("[data-reveal], [data-split]").forEach((el) => io.observe(el));

    const ioCount = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          animateCount(e.target);
          ioCount.unobserve(e.target);
        });
      },
      { threshold: 0.6 }
    );
    $$("[data-count]").forEach((el) => ioCount.observe(el));
  }

  function animateCount(el) {
    const target = parseInt(el.dataset.count, 10);
    const dur = 1600;
    const t0 = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 4);
    (function tick(now) {
      const p = clamp((now - t0) / dur, 0, 1);
      const v = Math.round(ease(p) * target);
      el.textContent = target >= 1000 ? v.toLocaleString("en-US") : v;
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }

  /* ---------- Loader ---------- */
  const loader = $("#loader");
  const loadNum = $("#loadNum");
  let loaderDone = false;

  function finishLoader() {
    if (loaderDone) return;
    loaderDone = true;
    loader.classList.add("done");
    document.body.classList.remove("is-loading");
    startObservers();
    setTimeout(() => loader.remove(), 1400);
  }

  if (prefersReduced) {
    loadNum.textContent = "100";
    finishLoader();
  } else {
    const dur = 1700;
    const t0 = performance.now();
    (function tick(now) {
      const p = clamp((now - t0) / dur, 0, 1);
      loadNum.textContent = Math.round((1 - Math.pow(1 - p, 3)) * 100);
      if (p < 1) requestAnimationFrame(tick);
      else setTimeout(finishLoader, 250);
    })(t0);
    setTimeout(finishLoader, 4000); // フェイルセーフ
  }

  /* ---------- Custom cursor ---------- */
  if (!isTouch && !prefersReduced) {
    const dot = $("#cursorDot");
    const ring = $("#cursorRing");
    let mx = -100, my = -100, rx = -100, ry = -100, shown = false;

    addEventListener("mousemove", (e) => {
      mx = e.clientX; my = e.clientY;
      if (!shown) { shown = true; document.body.classList.add("has-cursor"); rx = mx; ry = my; }
    }, { passive: true });

    (function cursorLoop() {
      rx += (mx - rx) * 0.16;
      ry += (my - ry) * 0.16;
      dot.style.transform = `translate(${mx}px, ${my}px)`;
      ring.style.transform = `translate(${rx}px, ${ry}px)${ring.classList.contains("is-active") ? " scale(1.7)" : ""}`;
      requestAnimationFrame(cursorLoop);
    })();

    document.addEventListener("mouseover", (e) => {
      if (e.target.closest("a, button, [data-tilt]")) ring.classList.add("is-active");
    });
    document.addEventListener("mouseout", (e) => {
      if (e.target.closest("a, button, [data-tilt]")) ring.classList.remove("is-active");
    });
  }

  /* ---------- Magnetic buttons ---------- */
  if (!isTouch && !prefersReduced) {
    $$(".magnetic").forEach((el) => {
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${x * 0.22}px, ${y * 0.3}px)`;
      });
      el.addEventListener("mouseleave", () => {
        el.style.transition = "transform .5s cubic-bezier(.22,1,.36,1)";
        el.style.transform = "";
        setTimeout(() => (el.style.transition = ""), 500);
      });
    });
  }

  /* ---------- Tilt cards ---------- */
  if (!isTouch && !prefersReduced) {
    $$("[data-tilt]").forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `perspective(1200px) rotateY(${px * 3}deg) rotateX(${-py * 3}deg) translateY(-3px)`;
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      });
    });
  }

  /* ---------- Fireflies canvas ---------- */
  (function fireflies() {
    const c = $("#fireflies");
    if (!c || prefersReduced) return;
    const ctx = c.getContext("2d");
    let w = 0, h = 0, running = true;
    const N = innerWidth < 768 ? 38 : 85;
    const P = [];

    function resize() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      w = c.clientWidth; h = c.clientHeight;
      c.width = w * dpr; c.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    addEventListener("resize", resize, { passive: true });

    function spawn(fromBottom) {
      return {
        x: Math.random() * w,
        y: fromBottom ? h + 10 : Math.random() * h,
        r: 0.6 + Math.random() * 2,
        vx: (Math.random() - 0.5) * 0.22,
        vy: -(0.06 + Math.random() * 0.34),
        tw: Math.random() * Math.PI * 2,
        ts: 0.008 + Math.random() * 0.022,
        green: Math.random() < 0.45,
      };
    }
    for (let i = 0; i < N; i++) P.push(spawn(false));

    new IntersectionObserver(([e]) => (running = e.isIntersecting), { threshold: 0 }).observe(c);

    (function tick() {
      requestAnimationFrame(tick);
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      for (const p of P) {
        p.x += p.vx; p.y += p.vy; p.tw += p.ts;
        if (p.y < -12 || p.x < -12 || p.x > w + 12) Object.assign(p, spawn(true));
        const a = (Math.sin(p.tw) * 0.5 + 0.5) * 0.4 + 0.04;
        const R = p.r * 5;
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, R);
        const col = p.green ? "103,169,78" : "78,134,210";
        g.addColorStop(0, `rgba(${col},${a})`);
        g.addColorStop(1, `rgba(${col},0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, R, 0, 7);
        ctx.fill();
      }
    })();
  })();

  /* ---------- Scroll-driven effects ---------- */
  const header = $("#header");
  const progress = $("#progress");
  const heroVideoWrap = $(".hero-video");
  const heroContent = $(".hero-content");
  const giantWords = $$(".giant-word");
  const biz = $(".biz");
  const bizTrack = $("#bizTrack");
  const bizGiant = $("#bizGiant");
  const bizBar = $("#bizBar");
  const bizIdx = $("#bizIdx");
  const timeline = $("#timeline");
  const hLine = $("#hLine");

  let lastY = scrollY;
  let ticking = false;
  const bizState = { x: 0 };

  function onScroll() {
    const y = scrollY;
    const docH = document.documentElement.scrollHeight - innerHeight;

    // プログレスバー
    progress.style.transform = `scaleX(${docH > 0 ? y / docH : 0})`;

    // ヘッダー表示制御
    header.classList.toggle("scrolled", y > 50);
    if (y > 140 && y > lastY + 5) header.classList.add("hidden");
    else if (y < lastY - 5 || y < 140) header.classList.remove("hidden");
    lastY = y;

    // ヒーロー：動画はゆっくり沈み、テキストは先に抜ける
    if (y < innerHeight * 1.2 && !prefersReduced) {
      if (heroVideoWrap) heroVideoWrap.style.transform = `translateY(${y * 0.22}px) scale(1.06)`;
      if (heroContent) {
        heroContent.style.transform = `translateY(${y * -0.1}px)`;
        heroContent.style.opacity = String(clamp(1 - y / (innerHeight * 0.72), 0, 1));
      }
    }

    // セクション背景の巨大ワード
    if (!prefersReduced) {
      giantWords.forEach((el) => {
        const r = el.getBoundingClientRect();
        const offset = (r.top + r.height / 2 - innerHeight / 2) * parseFloat(el.dataset.speed || 0.08);
        const baseX = el.classList.contains("giant-word--center") ? "translateX(-50%) " : "";
        el.style.transform = `${baseX}translateY(${offset}px)`;
      });
    }

    // 事業紹介：横スクロール（デスクトップのみ）
    if (biz && bizTrack && matchMedia("(min-width: 901px)").matches) {
      const total = biz.offsetHeight - innerHeight;
      const p = clamp((y - biz.offsetTop) / total, 0, 1);
      const max = bizTrack.scrollWidth - innerWidth;
      bizState.x = -p * max;
      if (prefersReduced) bizTrack.style.transform = `translate3d(${bizState.x}px, 0, 0)`;
      if (bizGiant) bizGiant.style.transform = `translateX(${-p * 42}vw)`;
      if (bizBar) bizBar.style.transform = `scaleX(${p})`;
      if (bizIdx) bizIdx.textContent = String(1 + Math.round(p * 7)).padStart(2, "0");
    }

    // 沿革：ライン描画
    if (timeline && hLine) {
      const r = timeline.getBoundingClientRect();
      const p = clamp((innerHeight * 0.72 - r.top) / r.height, 0, 1);
      hLine.style.transform = `scaleY(${p})`;
    }

    ticking = false;
  }

  addEventListener("scroll", () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(onScroll);
    }
  }, { passive: true });
  addEventListener("resize", () => requestAnimationFrame(onScroll), { passive: true });
  onScroll();

  // 横スクロールは素直に動かす（傾きなどの慣性表現は酔うので付けない）
  if (bizTrack && !prefersReduced) {
    let applied = null;
    (function bizLoop() {
      requestAnimationFrame(bizLoop);
      if (!matchMedia("(min-width: 901px)").matches) return;
      if (bizState.x === applied) return;
      applied = bizState.x;
      bizTrack.style.transform = `translate3d(${bizState.x}px, 0, 0)`;
    })();
  }

  /* ---------- Hero video ---------- */
  const heroVideo = $("#heroVideo");
  if (heroVideo) {
    if (prefersReduced) {
      heroVideo.removeAttribute("autoplay");
      heroVideo.pause();
    } else {
      // iOS / Android / 省電力モードなど、自動再生が拒否されうる環境すべてで
      // 最終的に再生されるよう、多段で復帰を仕掛ける
      let inView = true;
      let unlocked = false;

      const tryPlay = () => {
        heroVideo.muted = true;            // 消音でないと多くの端末が自動再生を拒む
        heroVideo.setAttribute("muted", "");
        const p = heroVideo.play();
        if (p && p.catch) p.catch(() => {});
      };

      // <source media> を無視するブラウザ向けに、実際に読む src をここで確定させる
      (() => {
        const want = innerWidth <= 820 ? "media/hero-mobile.mp4" : "media/hero.mp4";
        const current = heroVideo.currentSrc || "";
        if (current && !current.endsWith(want)) {
          heroVideo.src = want;
          heroVideo.load();
        }
      })();

      // 最初のユーザー操作で解除（iOS 低電力モードはこれが必須）
      const unlock = () => {
        if (unlocked) return;
        unlocked = true;
        tryPlay();
        ["touchstart", "touchend", "pointerdown", "click", "keydown", "scroll"].forEach((ev) =>
          removeEventListener(ev, unlock)
        );
      };
      ["touchstart", "touchend", "pointerdown", "click", "keydown", "scroll"].forEach((ev) =>
        addEventListener(ev, unlock, { passive: true })
      );

      // 読み込み進行に応じて何度でも試す
      ["loadedmetadata", "loadeddata", "canplay", "canplaythrough", "stalled", "suspend"].forEach((ev) =>
        heroVideo.addEventListener(ev, tryPlay)
      );
      // 端末側が勝手に止めた場合も、画面内なら戻す
      heroVideo.addEventListener("pause", () => {
        if (!document.hidden && inView) setTimeout(tryPlay, 120);
      });
      // ループの取りこぼし対策（loop 属性が効かない端末向け）
      heroVideo.addEventListener("ended", () => {
        heroVideo.currentTime = 0;
        tryPlay();
      });

      document.addEventListener("visibilitychange", () => {
        if (!document.hidden && inView) tryPlay();
      });
      addEventListener("pageshow", tryPlay);

      new IntersectionObserver(([e]) => {
        inView = e.isIntersecting;
        if (inView) tryPlay();
        else heroVideo.pause();
      }, { threshold: 0 }).observe(heroVideo);

      // 最後の保険：画面内なのに止まっていたら拾い直す
      setInterval(() => {
        if (!document.hidden && inView && heroVideo.paused) tryPlay();
      }, 1000);

      tryPlay();
    }
  }

  /* ---------- Scrollspy（ナビの現在地ハイライト） ---------- */
  const spyLinks = $$(".gnav a[data-spy]");
  if (spyLinks.length) {
    const spyIO = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const id = e.target.id;
          spyLinks.forEach((a) => a.classList.toggle("active", a.dataset.spy === id));
        });
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: 0 }
    );
    ["about", "business", "history", "network", "news", "recruit", "contact"].forEach((id) => {
      const sec = document.getElementById(id);
      if (sec) spyIO.observe(sec);
    });
  }

  /* ---------- Back to top ---------- */
  const toTop = $("#toTop");
  if (toTop) {
    addEventListener("scroll", () => {
      toTop.classList.toggle("show", scrollY > innerHeight * 0.9);
    }, { passive: true });
    toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" }));
  }

  /* ---------- Mobile menu ---------- */
  const menuBtn = $("#menuBtn");
  const mobileMenu = $("#mobileMenu");
  function closeMenu() {
    menuBtn.classList.remove("open");
    mobileMenu.classList.remove("open");
    menuBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }
  menuBtn.addEventListener("click", () => {
    const open = mobileMenu.classList.toggle("open");
    menuBtn.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    document.body.style.overflow = open ? "hidden" : "";
    if (open) header.classList.remove("hidden");
  });
  $$("a", mobileMenu).forEach((a) => a.addEventListener("click", closeMenu));
})();

/* ---------- お知らせ一覧：カテゴリで絞り込み（news.html だけで動く） ---------- */
(() => {
  const empty = document.getElementById("nwEmpty");
  if (!empty) return;
  const tabs = document.querySelectorAll(".nw-tab");
  const cards = document.querySelectorAll(".nw-card");
  tabs.forEach((t) =>
    t.addEventListener("click", () => {
      const f = t.dataset.filter;
      tabs.forEach((x) => {
        const on = x === t;
        x.classList.toggle("is-active", on);
        x.setAttribute("aria-pressed", on);
      });
      let n = 0;
      cards.forEach((c) => {
        const show = f === "all" || c.dataset.cat === f;
        c.hidden = !show;
        if (show) {
          n++;
          c.classList.add("is-in");
        }
      });
      empty.hidden = n > 0;
    })
  );
})();

