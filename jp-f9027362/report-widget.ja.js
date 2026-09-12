// InsureQuant /jp/ — 誤り報告ポップアップ(日本語版)。ルート report-widget.js を複製して文字列・選択肢を jp 向けに
// 差し替えたもの(inbox/designer/20260912T1215Z 追加5)。
// 使用: <script src="../forms-config.js"></script><script src="report-widget.ja.js" data-sheet-hint="jesr_esr"></script>
// バックエンドはルート forms-config.js(同じ Apps Script)をそのまま再利用し、payload の sheet 値に "JP:" 接頭辞を
// 付けて韓国側と区別する(バックエンド無変更)。
(function () {
  "use strict";

  // 対象シート: jp の公開データ 2 本(jp/jesr_esr.json = ESRランキング, jp/jesr_detail.json = 会社別詳細)。
  var SHEETS = [
    { value: "jesr_esr", label: "ESRランキング (jesr_esr)" },
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

  function init() {
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
