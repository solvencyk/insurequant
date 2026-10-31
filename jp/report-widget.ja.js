// InsureQuant /jp/ — 誤り報告ポップアップ(日本語版)。ルート report-widget.js を複製して文字列・選択肢を jp 向けに
// 差し替えたもの(inbox/designer/20260912T1215Z 追加5)。
// 使用: <script src="../forms-config.js"></script><script src="report-widget.ja.js" data-sheet-hint="jesr_esr"></script>
// バックエンドはルート forms-config.js(同じ Apps Script)をそのまま再利用し、payload の sheet 値に "JP:" 接頭辞を
// 付けて韓国側と区別する(バックエンド無変更)。
(function () {
  "use strict";

  // 対象シート: jp の公開データ 2 本(jp/jesr_esr.json = ESRランキング, jp/jesr_detail.json = 会社別詳細)。
  var SHEETS = [
    { value: "jesr_esr", label: "ESRマップ・ESRランキング・損害率一覧 (jesr_esr)" },
    { value: "jesr_detail", label: "会社別詳細 (jesr_detail)" }
  ];
  var SHEET_PREFIX = "JP:";

  // 会社・期の選択肢は jesr_esr.json(13社 + _meta.as_of)と jesr_detail.json(詳細 2社)から動的に組み立てる —
  // 四半期リテラルをハードコードすると更新漏れが起きる(claude-agent-designer.md「분기 리터럴 하드코딩 금지」)。
  // fetch に失敗したときだけ下の静的リストにフォールバックする(2026-09-12 時点の値)。
  var FALLBACK_COMPANIES = ["au損害保険", "ライフネット生命保険", "SOMPOホールディングス", "朝日生命保険", "富国生命保険",
    "東京海上ホールディングス", "T&Dホールディングス", "かんぽ生命保険", "MS&ADインシュアランスグループHD",
    "明治安田生命保険", "住友生命保険", "日本生命保険", "ソニーフィナンシャルグループ", "明治安田損害保険"];
  var FALLBACK_PERIODS = ["2025年度 4Q"];

  var scriptEl = document.currentScript;
  var sheetHint = scriptEl && scriptEl.dataset ? scriptEl.dataset.sheetHint || "" : "";

  // jp/index.html・jp/jesr.html の jaFiscalQuarter と同じ規則(日本の会計年度は 4 月開始: 1~3 月=前年度 4Q)。
  function jaFiscalQuarter(iso) {
    if (!iso) return null;
    var p = String(iso).split("-");
    var y = parseInt(p[0], 10), m = parseInt(p[1], 10);
    if (!isFinite(y) || !isFinite(m)) return null;
    var fy, q;
    if (m >= 1 && m <= 3) { fy = y - 1; q = 4; }
    else if (m <= 6) { fy = y; q = 1; }
    else if (m <= 9) { fy = y; q = 2; }
    else { fy = y; q = 3; }
    return fy + "年度 " + q + "Q";
  }

  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }

  function fillCheckGrid(grid, name, items) {
    grid.innerHTML = "";
    items.forEach(function (val) {
      var id = name + "-" + val;
      var cb = el("input", { type: "checkbox", id: id, value: val });
      var row = el("label", { class: "iq-check-row", for: id });
      row.dataset.search = String(val).toLowerCase();
      row.appendChild(cb);
      row.appendChild(document.createTextNode(val));
      grid.appendChild(row);
    });
  }

  function checkGrid(name, items) {
    var grid = el("div", { class: "iq-check-grid", style: "max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--r-sm);padding:8px" });
    fillCheckGrid(grid, name, items);
    return grid;
  }

  function filterableCheckGrid(name, items, placeholder, filterId) {
    var grid = checkGrid(name, items);
    var filterInput = el("input", { class: "iq-input", type: "text", id: filterId, placeholder: placeholder, autocomplete: "off", style: "margin-bottom:6px" });
    filterInput.addEventListener("input", function () {
      var q = filterInput.value.trim().toLowerCase();
      Array.prototype.forEach.call(grid.children, function (row) {
        row.style.display = (!q || row.dataset.search.indexOf(q) !== -1) ? "" : "none";
      });
    });
    return { wrap: el("div", {}, [filterInput, grid]), grid: grid };
  }

  function fetchJson(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) { if (!r.ok) throw new Error("http " + r.status); return r.json(); });
  }

  // 会社一覧(ランキング 13 社 + 詳細ページの会社、重複除去)と期(_meta.as_of → 会計年度四半期)。
  function loadOptions() {
    var esrP = fetchJson("jesr_esr.json").catch(function () { return null; });
    var detP = fetchJson("jesr_detail.json").catch(function () { return null; });
    return Promise.all([esrP, detP]).then(function (res) {
      var esr = res[0], det = res[1];
      var companies = [], seen = {};
      function add(n) { if (n && !seen[n]) { seen[n] = 1; companies.push(n); } }
      if (esr && Array.isArray(esr.records)) esr.records.forEach(function (r) { add(r.company_jp); });
      if (det && Array.isArray(det.companies)) det.companies.forEach(function (c) { add(c.company_jp); });
      var periods = [];
      var asOf = (esr && esr._meta && esr._meta.as_of) || (det && det._meta && det._meta.as_of);
      var fq = jaFiscalQuarter(asOf);
      if (fq) periods.push(fq);
      return {
        companies: companies.length ? companies : FALLBACK_COMPANIES,
        periods: periods.length ? periods : FALLBACK_PERIODS
      };
    });
  }

  function buildModal() {
    var sheetSelect = el("select", { class: "iq-select", id: "iqrep-sheet" },
      SHEETS.map(function (s) { return el("option", { value: s.value, text: s.label }); }));
    var hintOk = SHEETS.some(function (s) { return s.value === sheetHint; });
    if (hintOk) sheetSelect.value = sheetHint;

    var companyBuilt = filterableCheckGrid("iqrep-co", FALLBACK_COMPANIES, "会社名で絞り込み(例: 日本生命)", "iqrep-co-filter");
    var companyGrid = companyBuilt.grid;
    var quarterGrid = checkGrid("iqrep-q", FALLBACK_PERIODS);
    loadOptions().then(function (o) {
      fillCheckGrid(companyGrid, "iqrep-co", o.companies);
      fillCheckGrid(quarterGrid, "iqrep-q", o.periods);
    });

    var detail = el("textarea", { class: "iq-textarea", id: "iqrep-detail", placeholder: "どの数値がどのように異なるかをご記入ください(例: 2025年度 4Q の ESR が開示資料の値より低く表示されています)" });
    var honeypot = el("input", { type: "text", name: "website", tabindex: "-1", autocomplete: "off", "aria-hidden": "true", style: "position:absolute;left:-9999px;width:1px;height:1px;opacity:0" });
    var errorMsg = el("div", { class: "iq-form-error", id: "iqrep-error", role: "alert", text: "対象シートと誤りの内容は必須です。" });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "送信" });

    var form = el("form", { id: "iqrep-form" }, [
      el("div", { class: "iq-field" }, [el("label", { for: "iqrep-sheet", text: "対象シート" }), sheetSelect]),
      el("div", { class: "iq-field" }, [el("label", { for: "iqrep-co-filter", text: "対象会社 " }, [el("span", { class: "iq-hint", text: "(複数選択可)" })]), companyBuilt.wrap]),
      el("div", { class: "iq-field" }, [el("label", { text: "対象期 " }, [el("span", { class: "iq-hint", text: "(複数選択可)" })]), quarterGrid]),
      el("div", { class: "iq-field" }, [el("label", { for: "iqrep-detail", text: "誤りの内容" }), detail]),
      honeypot, errorMsg, submitBtn
    ]);

    var panel = el("div", {
      class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqrep-title"
    }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqrep-title", text: "数値の誤りを報告" }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": "閉じる", text: "×" })
      ]),
      el("p", { class: "small-muted", style: "margin-top:0" }, [document.createTextNode("お気づきの誤りをお知らせください。確認のうえ修正します。氏名・メールアドレスは不要です。")]),
      form
    ]);
    var backdrop = el("div", { class: "iq-modal-backdrop", id: "iqrep-backdrop", style: "display:none" }, [panel]);
    document.body.appendChild(backdrop);

    var closeBtn = panel.querySelector(".iq-modal-close");
    var lastFocused = null;

    function open(prefill) {
      lastFocused = document.activeElement;
      backdrop.style.display = "flex";
      document.addEventListener("keydown", onKeydown);
      if (!window.IQ_FORMS || !window.IQ_FORMS.isConfigured()) {
        submitBtn.disabled = true;
        submitBtn.textContent = "一時的に送信できません";
      }
      if (prefill && prefill.sheet && SHEETS.some(function (s) { return s.value === prefill.sheet; })) sheetSelect.value = prefill.sheet;
      if (prefill && prefill.company) {
        var coCb = document.getElementById("iqrep-co-" + prefill.company);
        if (coCb) coCb.checked = true;
      }
      if (prefill && prefill.period) {
        var qCb = document.getElementById("iqrep-q-" + prefill.period);
        if (qCb) qCb.checked = true;
      }
      if (prefill && (prefill.sheet || prefill.company || prefill.period)) detail.focus();
      else sheetSelect.focus();
    }
    function close() {
      backdrop.style.display = "none";
      document.removeEventListener("keydown", onKeydown);
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }
    function onKeydown(e) { if (e.key === "Escape") close(); }

    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) close(); });
    closeBtn.addEventListener("click", close);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!window.IQ_FORMS || !window.IQ_FORMS.isConfigured()) return;
      if (honeypot.value) return; // bot
      var sheet = sheetSelect.value;
      var companies = Array.prototype.slice.call(companyGrid.querySelectorAll("input:checked")).map(function (c) { return c.value; });
      var quarters = Array.prototype.slice.call(quarterGrid.querySelectorAll("input:checked")).map(function (c) { return c.value; });
      var detailVal = detail.value.trim();
      if (!sheet || !detailVal) {
        errorMsg.classList.add("show");
        return;
      }
      errorMsg.classList.remove("show");
      submitBtn.disabled = true;
      submitBtn.textContent = "送信中…";
      window.IQ_FORMS.submit("report", {
        sheet: SHEET_PREFIX + sheet, company: companies.join(", "), period: quarters.join(", "), detail: detailVal
      }).then(function () {
        submitBtn.textContent = "送信完了 — ありがとうございます";
        setTimeout(function () {
          close();
          form.reset();
          submitBtn.disabled = false;
          submitBtn.textContent = "送信";
        }, 1200);
      });
    });

    return { open: open };
  }

  // 共有メニュー(ヘッダー右上)とセクション別スクリーンショット(2026-10-31 owner: 韓国サイトと同じ機能に)。
  // ルート theme.js の共有(リンクコピー・ページ全体/セクション別スクリーンショット)を jp 用に移植したもの —
  // theme.js は lang=ja で共有を出さないため、全 jp ページが読むこのファイルから日本語で組み立てる。
  // html2canvas はスクリーンショットを押した時だけ SRI 付きで読み込む(ルート theme.js と同じ URL・ハッシュ。
  // scripts/compute_sri.py の html2canvas@1.4.1 と同一)。画像はすべて閲覧者のブラウザ内で作り、利用記録は送らない。
  // 長いページはキャンバス上限(1辺約16,384px・iOS Safari は総面積約1,677万px)を超えると無言で白紙になるため、
  // 作る前に高さを測って倍率を自動で下げる(shPlan)。読める下限(SH_MIN_SCALE)を割る極端に長いページは上部のみ収録する。
  // 画面側の契約: マークアップに data-share-section="セクション名" を付けた要素(パネル)の右上にボタンが付く。
  var H2C_URL = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
  var H2C_SRI = "sha384-ZZ1pncU3bQe8y31yfZdMFdSpttDoPmOZg2wguVK9almUodir1PghgT0eY7Mrty8H";
  var SH_MAX_DIM = 16000;
  var SH_MAX_AREA_COARSE = 16000000;
  var SH_MAX_AREA_FINE = 64000000;
  var SH_MIN_SCALE = 0.75;
  var SH_SOURCE = "出所: 各社開示資料(決算短信・決算説明資料・ディスクロージャー誌 等)";
  // 画像から外す要素(共有・誤り報告ボタン・各種ポップアップ・「もっと見る」・国ドロップダウンなど)。
  var SH_IGNORE = ".iq-report-fab, .iq-share, .iq-sec-share, .iq-toast, .iq-modal-backdrop, .theme-toggle, .iq-help, .iq-anon-link, .li-more-btn, .country-sw, .esr-map-tip";
  var shToastTimer = null, shBusy = false;

  function shToast(t) {
    var n = document.getElementById("iqToast");
    if (!n) {
      n = el("div", { class: "iq-toast", id: "iqToast", role: "status", "aria-live": "polite" });
      n.hidden = true;
      document.body.appendChild(n);
    }
    n.textContent = t; n.hidden = false;
    clearTimeout(shToastTimer);
    shToastTimer = setTimeout(function () { n.hidden = true; }, 2600);
  }
  function shCssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }
  function shColors() {
    return { bg: shCssVar("--bg", "#ffffff"), border: shCssVar("--border", "#e4e4e2"), text: shCssVar("--text", "#18181b"), muted: shCssVar("--muted", "#63666b") };
  }
  function shareUrl() {
    var u = new URL(location.href);
    u.searchParams.delete("iq_internal");
    return u.toString().replace(/%2C/gi, ",");
  }
  function shCopyLink() {
    var link = shareUrl();
    var done = function () { shToast("リンクをコピーしました"); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(link).then(done, function () { window.prompt("リンクをコピーしてください", link); });
    else window.prompt("リンクをコピーしてください", link);
  }
  function shLoadH2C(ok, fail) {
    if (window.html2canvas) { ok(); return; }
    var s = document.createElement("script");
    s.src = H2C_URL; s.integrity = H2C_SRI; s.crossOrigin = "anonymous";
    s.onload = ok;
    s.onerror = function () { shToast("画像作成ツールを読み込めませんでした"); if (fail) fail(); };
    document.head.appendChild(s);
  }
  function shSave(blob, tag) {
    var page = location.pathname.split("/").pop().replace(/\.html$/, "") || "index";
    var name = "insurequant-jp-" + page + (tag ? "-" + tag : "") + "-" + new Date().toISOString().slice(0, 10) + ".png";
    function download() {
      var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
      shToast("画像を保存しました");
    }
    var file = null; try { file = new window.File([blob], name, { type: "image/png" }); } catch (e) {}
    var touch = window.matchMedia && window.matchMedia("(pointer:coarse)").matches;
    if (touch && file && navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      navigator.share({ files: [file], title: document.title }).then(function () {}, function (e) { if (!e || e.name !== "AbortError") download(); });
    } else download();
  }
  // 画像の見出し・出所に使う文脈: ページ名(現在のタブ)・対象会社(会社ピッカー)・出所(フッターの文言)。
  function shCtx() {
    var co = "", sel = document.getElementById("companySelect");
    if (sel && sel.value && sel.selectedIndex >= 0) co = (sel.options[sel.selectedIndex].textContent || "").trim();
    var tab = document.querySelector('.tab[aria-current="page"]'), ft = document.querySelector("footer");
    var m = ft ? /出所:[^—\n]*/.exec(ft.textContent || "") : null;
    return { page: tab ? (tab.textContent || "").trim() : (document.title || "").split("|")[0].trim(), company: co, source: m ? m[0].replace(/\s+/g, " ").trim() : SH_SOURCE };
  }
  // 文字単位で折り返す(日本語は空白が無いので、幅を超えたら1文字ずつ詰める)。
  function shWrap(c, text, maxW) {
    var out = [], line = "", words = String(text).split(" "), i, t, k, w;
    for (i = 0; i < words.length; i++) {
      w = words[i]; t = line ? line + " " + w : w;
      if (c.measureText(t).width <= maxW) { line = t; continue; }
      if (line) { out.push(line); line = ""; }
      if (c.measureText(w).width <= maxW) { line = w; continue; }
      for (k = 0; k < w.length; k++) {
        t = line + w.charAt(k);
        if (line && c.measureText(t).width > maxW) { out.push(line); line = w.charAt(k); } else line = t;
      }
    }
    if (line) out.push(line);
    return out;
  }
  // キャンバス上限の範囲で最大の倍率を選ぶ。下限を割るなら上部だけ(cropH)。純関数。
  function shPlan(cssW, bodyH, overhead, base, coarse) {
    var maxArea = coarse ? SH_MAX_AREA_COARSE : SH_MAX_AREA_FINE;
    function fit(H) { return Math.min(SH_MAX_DIM / H, Math.sqrt(maxArea / (cssW * H))); }
    var H = overhead + bodyH, s = Math.min(base, fit(H));
    if (s >= SH_MIN_SCALE) return { scale: s, cropH: 0, truncated: false, cssH: H };
    s = Math.min(base, SH_MIN_SCALE);
    var maxH = Math.floor(Math.min(SH_MAX_DIM / s, maxArea / (cssW * s * s)));
    return { scale: s, cropH: Math.max(200, maxH - overhead), truncated: true, cssH: maxH };
  }
  // target を画像にする。上に見出し(ページ・セクション・会社)、下に出所をキャンバスへ直接描く。
  function shRender(target, o) {
    o = o || {};
    var coarse = !!(window.matchMedia && window.matchMedia("(pointer:coarse)").matches);
    var ch = shColors(), cs = getComputedStyle(document.body), bg = cs.backgroundColor;
    if (!bg || bg === "transparent" || /rgba\(0, 0, 0, 0\)/.test(bg)) bg = ch.bg;
    var fam = cs.fontFamily, cx = document.createElement("canvas").getContext("2d"), info = shCtx();
    var rect = target.getBoundingClientRect(), cw0 = Math.ceil(rect.width), bodyH = Math.ceil(Math.max(rect.height, target.scrollHeight));
    // セクション画像: 横スクロールする表はその幅だけ画像を広げて右の列まで収める(広い画面のみ)。
    var extra = 0, phone = coarse || document.documentElement.clientWidth < 520;
    if (o.widen && !phone) [].forEach.call(target.querySelectorAll(".table-container, .table-wrap"), function (t) { extra = Math.max(extra, Math.ceil(t.scrollWidth - t.clientWidth)); });
    var cw = cw0 + extra;
    var PAD = (o.pad != null) ? o.pad : 12, W = cw + PAD * 2, narrow = W < 520, LH = 17;
    cx.font = "700 15px " + fam;
    var head = [info.page, o.title, info.company].filter(Boolean).join(" · ") || "InsureQuant";
    var headLines = shWrap(cx, head, W - PAD * 2).slice(0, 3), titleH = headLines.length * 21 + 10;
    cx.font = "12px " + fam;
    var dt = new Date(), date = dt.getFullYear() + "-" + ("0" + (dt.getMonth() + 1)).slice(-2) + "-" + ("0" + dt.getDate()).slice(-2), path = location.pathname.replace(/\/index\.html$/, "/");
    var src = narrow ? "出所: 各社開示資料" : info.source;
    var paras = [
      "InsureQuant · " + (narrow ? "insurequant.com" : "www.insurequant.com" + path) + " · " + date,
      [src, info.company].filter(Boolean).join(" · "),
      narrow ? "公表資料を加工した値で、誤りを含む可能性があります" : "公表資料を加工した値で、誤りを含む可能性があります。投資判断の根拠としてご使用いただけません。"
    ];
    var noteLine = "※ ページが非常に長いため、上部の一部のみを収録しました。セクション別の共有ボタンをご利用ください。";
    function footLines(withNote) {
      var ls = [], i; for (i = 0; i < paras.length; i++) ls = ls.concat(shWrap(cx, paras[i], W - PAD * 2));
      return withNote ? ls.concat(shWrap(cx, noteLine, W - PAD * 2)) : ls;
    }
    var lines = footLines(false), GAP = 12;
    var plan = shPlan(W, bodyH, PAD * 2 + titleH + GAP + lines.length * LH + 8, Math.min(2, window.devicePixelRatio || 1), coarse);
    if (plan.truncated) {
      lines = footLines(true);
      plan = shPlan(W, bodyH, PAD * 2 + titleH + GAP + lines.length * LH + 8, Math.min(2, window.devicePixelRatio || 1), coarse);
    }
    var s = plan.scale, footH = lines.length * LH + 8;
    var fz = document.createElement("style"); fz.id = "iqShotFreeze";
    fz.textContent = "*,*::before,*::after{animation:none !important;transition:none !important}";
    document.head.appendChild(fz);
    function unfreeze() { if (fz.parentNode) fz.parentNode.removeChild(fz); target.removeAttribute("data-iq-shot-root"); }
    target.setAttribute("data-iq-shot-root", "1");
    var opt = {
      backgroundColor: bg, scale: s, useCORS: true, logging: false, windowWidth: document.documentElement.clientWidth,
      ignoreElements: function (n) { return !!(n.matches && n.matches(SH_IGNORE)); },
      onclone: function (doc) {
        var st = doc.createElement("style");
        st.textContent = "*,*::before,*::after{animation:none !important;transition:none !important}.sr-only{display:none !important}";
        doc.head.appendChild(st);
        if (extra) {
          var rt = doc.querySelector("[data-iq-shot-root]"), isSec = rt.hasAttribute("data-share-section"), secs = isSec ? [rt] : [].slice.call(rt.querySelectorAll("[data-share-section]"));
          secs.forEach(function (sc) { sc._w0 = sc.getBoundingClientRect().width; sc._need = 0; });
          [].forEach.call(rt.querySelectorAll(".table-container, .table-wrap"), function (t) {
            var ov = Math.ceil(t.scrollWidth - t.clientWidth); if (ov <= 0) return;
            t.style.overflow = "visible"; t.style.maxWidth = "none";
            var sc = t.closest("[data-share-section]"); if (sc && sc._need < ov) sc._need = ov;
          });
          secs.forEach(function (sc) { sc.style.width = Math.ceil(sc._w0 + sc._need) + "px"; });
          if (!isSec) rt.style.width = cw + "px";
        }
      }
    };
    opt.width = cw;
    if (plan.cropH) opt.height = plan.cropH;
    var settle = Promise.resolve(document.fonts && document.fonts.ready).then(function () { return new Promise(function (r) { setTimeout(r, o.settle || 1200); }); });
    return settle.then(function () { return window.html2canvas(target, opt); }).then(function (cv) {
      unfreeze();
      var shown = Math.round(cv.height / s);
      var outW = Math.round(W * s), outH = Math.round((PAD * 2 + titleH + GAP + shown + footH) * s);
      var out = document.createElement("canvas"); out.width = outW; out.height = outH;
      var c = out.getContext("2d"); c.fillStyle = bg; c.fillRect(0, 0, outW, outH);
      c.setTransform(s, 0, 0, s, 0, 0); c.textBaseline = "top";
      c.fillStyle = ch.text; c.font = "700 15px " + fam;
      headLines.forEach(function (l, i) { c.fillText(l, PAD, PAD + 3 + i * 21); });
      var by = PAD + titleH;
      c.drawImage(cv, PAD, by, cv.width / s, cv.height / s);
      var fy = by + shown + GAP;
      c.fillStyle = ch.border; c.fillRect(PAD, fy - 6, W - PAD * 2, 1);
      c.fillStyle = ch.muted; c.font = "12px " + fam;
      lines.forEach(function (l, i) { c.fillText(l, PAD, fy + 2 + i * LH); });
      return { canvas: out, meta: { truncated: plan.truncated } };
    }, function (e) { unfreeze(); throw e; });
  }
  function shDo(target, o) {
    if (shBusy) { shToast("画像を作成中です"); if (o.btn) o.btn.removeAttribute("aria-busy"); return; }
    shBusy = true; shToast("画像を作成中…");
    function done() { shBusy = false; [].forEach.call(document.querySelectorAll(".iq-sec-share[aria-busy]"), function (b) { b.removeAttribute("aria-busy"); }); }
    shLoadH2C(function () {
      shRender(target, o).then(function (r) {
        r.canvas.toBlob(function (b) {
          done();
          if (!b) { shToast("画像を作成できませんでした"); return; }
          shSave(b, o.tag);
          if (r.meta.truncated) setTimeout(function () { shToast("ページが非常に長いため上部のみ収録しました。セクション別共有をご利用ください"); }, 700);
        }, "image/png");
      }, function () { done(); shToast("画像を作成できませんでした"); });
    }, function () { done(); });
  }
  function shRoot() {
    return document.querySelector("main.container") || document.querySelector(".container") || document.body;
  }
  // ヘッダーの共有メニュー: ページ全体(全セクション)を1枚の縦長画像に。
  function shShot() { shDo(shRoot(), { tag: "full" }); }
  // セクション右上のボタン: そのセクションだけ。
  function shSection(sec, btn) {
    var sel = document.getElementById("companySelect");
    if (sel && !sel.value) { shToast("先に会社を選択してください"); return; }
    if (btn) btn.setAttribute("aria-busy", "true");
    var h = sec.querySelector("h2, h3"), id = (sec.id || (h && h.id) || "section").replace(/[^A-Za-z0-9_-]/g, "");
    shDo(sec, { title: sec.getAttribute("data-share-section") || "", tag: id, pad: 12, settle: 500, widen: true, btn: btn });
  }
  var SHARE_ICON_SM = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path d="M8.4 10.9l7.2-4.1M8.4 13.1l7.2 4.1" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/><g fill="currentColor"><circle cx="18" cy="5.5" r="2.7"/><circle cx="6" cy="12" r="2.7"/><circle cx="18" cy="18.5" r="2.7"/></g></svg>';
  function mountSectionShare() {
    var els = document.querySelectorAll("[data-share-section]"), i, j, sec, has, head, b, name;
    for (i = 0; i < els.length; i++) {
      sec = els[i]; has = false; head = null;
      for (j = 0; j < sec.children.length; j++) {
        if (sec.children[j].classList.contains("iq-sec-share")) has = true;
        else if (!head && /^H[23]$/.test(sec.children[j].tagName)) head = sec.children[j];
      }
      if (has) continue;
      name = (sec.getAttribute("data-share-section") || "このセクション") + " スクリーンショットを共有";
      b = el("button", { type: "button", class: "iq-sec-share", "aria-label": name, title: name });
      b.innerHTML = SHARE_ICON_SM;
      b.addEventListener("click", (function (s2, btn) { return function (e) { e.preventDefault(); e.stopPropagation(); shSection(s2, btn); }; })(sec, b));
      if (head) head.parentNode.insertBefore(b, head.nextSibling); else sec.insertBefore(b, sec.firstChild);
    }
  }
  function mountShare() {
    if (document.getElementById("iqShareBtn")) return;
    var h = document.querySelector("header");
    if (!h) return;
    var wrap = el("div", { class: "iq-share", id: "iqShare" });
    var btn = el("button", { type: "button", id: "iqShareBtn", class: "iq-share-btn", "aria-haspopup": "menu", "aria-expanded": "false", "aria-controls": "iqShareMenu", "aria-label": "共有", title: "共有" });
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path d="M8.4 10.9l7.2-4.1M8.4 13.1l7.2 4.1" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linecap="round"/><g fill="currentColor"><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="6" r="2.6"/><circle cx="18" cy="18" r="2.6"/></g></svg>';
    var menu = el("ul", { class: "iq-share-menu", id: "iqShareMenu", role: "menu", "aria-label": "共有" });
    menu.hidden = true;
    [["リンクをコピー", shCopyLink], ["ページ全体のスクリーンショット", shShot]].forEach(function (it) {
      var li = el("li", { role: "none" });
      var b = el("button", { type: "button", role: "menuitem", text: it[0] });
      b.addEventListener("click", function () { close(); btn.focus(); it[1](); });
      li.appendChild(b); menu.appendChild(li);
    });
    function items() { return [].slice.call(menu.querySelectorAll("[role=menuitem]")); }
    function close() { menu.hidden = true; btn.setAttribute("aria-expanded", "false"); }
    function open() { menu.hidden = false; btn.setAttribute("aria-expanded", "true"); items()[0].focus(); }
    btn.addEventListener("click", function (e) { e.stopPropagation(); if (menu.hidden) open(); else close(); });
    document.addEventListener("click", function (e) { if (!menu.hidden && !wrap.contains(e.target)) close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !menu.hidden) { close(); btn.focus(); } });
    menu.addEventListener("keydown", function (e) {
      if (e.key === "Tab") { close(); btn.focus(); return; }
      if (["ArrowDown", "ArrowUp", "Home", "End"].indexOf(e.key) < 0) return;
      e.preventDefault();
      var it = items(), k = it.indexOf(document.activeElement);
      var to = e.key === "Home" ? 0 : e.key === "End" ? it.length - 1 : (k + (e.key === "ArrowDown" ? 1 : it.length - 1)) % it.length;
      it[to].focus();
    });
    wrap.appendChild(btn); wrap.appendChild(menu); h.appendChild(wrap);
    h.classList.add("has-share");
  }

  function init() {
    mountShare();
    mountSectionShare();
    var modal = buildModal();
    var fab = el("button", { class: "iq-report-fab", type: "button" }, [document.createTextNode("⚑ 誤りを報告")]);
    fab.addEventListener("click", function () { modal.open(); });
    document.body.appendChild(fab);
    window.IQreport = { open: modal.open };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
