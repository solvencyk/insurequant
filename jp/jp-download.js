// InsureQuant /jp/ - xlsx download gate (front end).
// Flow: request -> owner approval -> download. No e-mail is collected; a request code lives in this browser.
// Spec: docs/domains/jp_download_gate_ui.md (screens, copy) and docs/domains/jp_download_gate.md (API, blob format).
// Backend: scripts/appsscript/insurequant_collector.gs, reached through window.IQ_FORMS.submit (../forms-config.js).
// Usage: <script src="../forms-config.js"></script><script src="jp-download.js"></script>
// The page must contain <button id="downloadMasterBtn" class="download-cta">; this script adds the status dot and the modals.
// Security notes: all text is written with textContent (no HTML string sinks); the decryption key is never logged or stored;
// object URLs are revoked; approval is decided by the server only (the stored code is just a bearer token).
(function () {
  "use strict";

  var SCRIPT_URL = (document.currentScript && document.currentScript.src) || "";
  var BLOB_URL = (function () {
    try { return new URL("jp_tables.enc", SCRIPT_URL || location.href).href; } catch (e) { return "jp_tables.enc"; }
  })();
  var XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

  var CODE_KEY = "iqJpDlCode_v1";
  var SEEN_KEY = "iqJpDlSeen_v1";
  var POLL_MS = 15000;
  var POLL_MAX = 40;
  var QUIET_DELAY_MS = 800;
  var FRESH_MS = 60000;
  var GATE_TIMEOUT_MS = 30000;    // a gate call that takes longer is treated like a network failure
  var BLOB_TIMEOUT_MS = 60000;
  var STATUSES = ["pending", "approved", "denied", "revoked", "unknown"];

  // ---- copy (source of truth: UI spec section 3) ----
  var T = {
    btnTitle: "データのダウンロード(.xlsx)",
    close: "閉じる",
    intro: "ダウンロードは申請制です。以下をご入力のうえ、承認を申請してください。運営者が確認し、承認されるとこの画面からダウンロードできます(承認までお時間をいただく場合があります)。",
    sectorLabel: "業種", required: "(必須)", optional: "(任意)", choose: "選択してください",
    purposeLabel: "利用目的",
    affilLabel: "所属", affilPh: "例: ○○損害保険",
    affilNote: "会社名・団体名のみをご入力ください。個人のお名前は入力しないでください。",
    disclaimer: "本データは各社の開示資料を自動的に収集・加工したもので、誤りを含む場合があります。投資判断の根拠としてご利用いただけません。誤りを見つけた場合は、画面右下の「誤りを報告」ボタンからお知らせください。",
    privacyA: "ご入力いただいた業種・利用目的・所属は、承認の可否の判断と利用状況の把握にのみ使用し、第三者には提供しません。氏名・メールアドレス等の連絡先はお尋ねしません。申請後、承認状況を確認するための「申請番号」をこの端末のブラウザに保存します(詳しくは",
    privacyLink: "プライバシーポリシー",
    privacyB: "をご覧ください)。",
    termsLink: "利用規約",
    consentTail: "(データの利用条件)を確認し、同意します。",
    submit: "承認を申請する", sending: "送信中…",
    errValidate: "業種と利用目的を選択し、利用規約への同意にチェックを入れてください。",
    errNet: "送信に失敗しました。通信環境をご確認のうえ、もう一度お試しください。",
    errBusy: "現在、申請が集中しています。時間をおいて、もう一度お試しください。",
    errNotConfigured: "現在、申請を受け付けていません。",
    restoreLink: "申請番号をお持ちの方はこちら →",
    restoreLabel: "申請番号", restorePh: "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx", restoreBtn: "確認",
    errRestore: "申請番号が見つかりません。入力内容をご確認ください。",
    statePrefix: "状況: ",
    stPending: "承認待ち", stApproved: "承認済み",
    stDenied: "承認されませんでした", stRevoked: "承認が取り消されました", stUnknown: "申請番号が見つかりません",
    pendingBody: "申請を受け付けました。承認されるまでお待ちください。承認されると、このボタンからダウンロードできるようになります。",
    codeLabel: "申請番号", copy: "コピー", copied: "コピーしました",
    codeNote: "この番号は、この端末のブラウザに保存されています。別の端末やブラウザで承認状況を確認する場合や、ブラウザのデータを消去した場合は、この番号を入力してください。番号は他の方に教えないでください。",
    // not in the spec tables: shown only when the browser refuses to store the code (private mode etc.)
    codeNotSaved: "このブラウザでは申請番号を保存できません。下の番号を必ず控えてください。",
    check: "状況を確認",
    notYet: function (hhmm) { return "まだ承認されていません(最終確認: " + hhmm + ")"; },
    forget: "この端末の申請番号を削除する",
    forgetAsk: "削除すると、この端末では承認状況を確認できなくなります(申請の記録は残ります)。",
    forgetYes: "削除する", forgetNo: "やめる",
    approvedBody: "承認されました。下のボタンからダウンロードできます。",
    fileInfo: function (name) { return "ファイル: " + name + "(Excel ブック1ファイル)"; },
    termsTail: "利用条件は",
    termsTail2: "に従います。",
    dl: "ダウンロード(.xlsx)", dlBusy: "準備中…", dlStarted: "ダウンロードを開始しました。",
    errLimit: "本日のダウンロード回数の上限に達しました。時間をおいて、もう一度お試しください。",
    errUpdating: "ファイルを更新中です。しばらくしてから、もう一度お試しください。",
    errOpen: "ファイルを開けませんでした。ページを再読み込みして、もう一度お試しください。",
    errDlNet: "ダウンロードに失敗しました。通信環境をご確認のうえ、もう一度お試しください。",
    deniedBody: "今回の申請は承認されませんでした。",
    revokedBody: "承認が取り消されました。",
    unknownBody: "この申請番号は見つかりません。",
    renew: "新しく申請する"
  };
  var SECTORS = [
    ["life", "生命保険会社"], ["nonlife", "損害保険会社"], ["reinsurer", "再保険会社"], ["securities", "証券・資産運用"],
    ["consulting", "コンサルティング・会計"], ["academia", "学術・研究"], ["media", "報道"], ["regulator", "監督当局"], ["other", "その他"]
  ];
  var PURPOSES = [
    ["trend", "業界動向・課題の把握"], ["benchmark", "競合比較・社内報告"], ["sourcing", "取引先の探索・選別"], ["investment", "投資判断の参考"],
    ["research", "学術研究・論文"], ["article", "記事・レポートの作成"], ["personal", "個人的な関心"], ["other", "その他"]
  ];
  var ENDED = {
    denied: { state: T.stDenied, body: T.deniedBody },
    revoked: { state: T.stRevoked, body: T.revokedBody },
    unknown: { state: T.stUnknown, body: T.unknownBody }
  };
  var BTN_STATE = {
    pending: T.stPending, approved: T.stApproved,
    denied: T.stDenied, revoked: T.stRevoked, unknown: T.stUnknown
  };

  // ---- small helpers ----
  function el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "class") e.className = attrs[k];
      else if (k === "text") e.textContent = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function todayStr() { var d = new Date(); return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()); }
  function hhmm() { var d = new Date(); return pad2(d.getHours()) + ":" + pad2(d.getMinutes()); }
  function normalizeCode(s) { return String(s == null ? "" : s).toLowerCase().replace(/[^0-9a-z]/g, ""); }
  function validCode(s) { return /^[0-9a-f]{30}$/.test(s); }
  function formatCode(c) { return c.match(/.{5}/g).join("-"); }
  function pageName() { return location.pathname.split("/").filter(Boolean).slice(-2).join("/"); }
  function hex(bytes) { var s = ""; for (var i = 0; i < bytes.length; i++) s += (bytes[i] < 16 ? "0" : "") + bytes[i].toString(16); return s; }

  // ---- storage: localStorage with an in-memory fallback (private mode etc.) ----
  var mem = {};
  var persisted = true;
  function sGet(k) {
    var v = null;
    try { v = window.localStorage.getItem(k); } catch (e) { v = null; }
    if (v === null || v === undefined) v = Object.prototype.hasOwnProperty.call(mem, k) ? mem[k] : null;
    return v;
  }
  function sSet(k, v) {
    mem[k] = v;
    try { window.localStorage.setItem(k, v); return window.localStorage.getItem(k) === v; }
    catch (e) { return false; }
  }
  function sDel(k) {
    delete mem[k];
    try { window.localStorage.removeItem(k); } catch (e) { /* ignore */ }
  }
  function getCode() { var c = normalizeCode(sGet(CODE_KEY)); return validCode(c) ? c : ""; }
  function setCode(c) { persisted = sSet(CODE_KEY, c); }
  function readSeen() {
    try {
      var o = JSON.parse(sGet(SEEN_KEY) || "null");
      // a record written for another code (c = first 8 characters) is ignored; records without c (older ones) stay valid
      if (o && STATUSES.indexOf(o.s) >= 0 && typeof o.t === "number" && (typeof o.c !== "string" || o.c === getCode().slice(0, 8))) return o;
    } catch (e) { /* ignore */ }
    return null;
  }

  // ---- gate calls (window.IQ_FORMS.submit never rejects, but answers {ok:true} for non-JSON bodies) ----
  function callGate(kind, values) {
    var F = window.IQ_FORMS;
    if (!F || typeof F.submit !== "function") return Promise.resolve({ ok: false, reason: "not_configured" });
    var p;
    try { p = Promise.resolve(F.submit(kind, values)); } catch (e) { return Promise.resolve({ ok: false, reason: "network" }); }
    var timer = null;
    var late = new Promise(function (resolve) { timer = setTimeout(function () { resolve({ ok: false, reason: "network" }); }, GATE_TIMEOUT_MS); });
    var settled = p.then(function (r) { return (r && typeof r === "object") ? r : { ok: false, reason: "network" }; },
                         function () { return { ok: false, reason: "network" }; });
    return Promise.race([settled, late]).then(function (r) { clearTimeout(timer); return r; });
  }
  // -> {status} | {error: reason}
  function fetchStatus(code) {
    return callGate("jp_dl_status", { code: code }).then(function (r) {
      if (r.ok === true && STATUSES.indexOf(r.status) >= 0) return { status: r.status };
      return { error: r.reason || "network" };
    });
  }

  // ---- state ----
  var btn = null, dot = null, baseLabel = "";
  var backdrop = null, opener = null;
  var viewTok = 0;           // bumped on every view change and on close; late async results compare against it
  var pollTimer = null, pollCount = 0, pollBusy = false;
  var dlBusy = false, dlBtnLive = null;   // dlBtnLive = the download button of the view that is on screen now

  function setBtnState(state) {
    if (!btn) return;
    btn.setAttribute("data-state", state);
    if (state === "none" || !BTN_STATE[state]) { btn.removeAttribute("title"); btn.removeAttribute("aria-label"); return; }
    btn.setAttribute("title", BTN_STATE[state]);
    btn.setAttribute("aria-label", baseLabel + "、" + T.statePrefix + BTN_STATE[state]);
  }
  function recordStatus(s) {
    sSet(SEEN_KEY, JSON.stringify({ s: s, t: Date.now(), c: getCode().slice(0, 8) }));
    setBtnState(s);
  }

  function isOpen() { return !!backdrop && backdrop.style.display === "flex"; }
  function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } pollCount = 0; pollBusy = false; }

  function ensureBackdrop() {
    if (backdrop) return;
    backdrop = el("div", { class: "iq-modal-backdrop iqjp-modal", id: "iqjpdl-backdrop", style: "display:none" });
    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeModal(); });
    document.body.appendChild(backdrop);
  }
  function closeModal() {
    stopPoll();
    viewTok++;
    if (backdrop) { backdrop.style.display = "none"; backdrop.textContent = ""; }
    if (opener && opener.focus) opener.focus();
  }

  function focusables() {
    if (!backdrop) return [];
    var list = backdrop.querySelectorAll('a[href],button,input,select,textarea,[tabindex]');
    return Array.prototype.filter.call(list, function (n) {
      return !n.disabled && n.getAttribute("tabindex") !== "-1" && n.type !== "hidden" && (n.offsetWidth || n.offsetHeight || n.getClientRects().length);
    });
  }
  document.addEventListener("keydown", function (e) {
    if (!isOpen()) return;
    if (e.key === "Escape") { e.preventDefault(); closeModal(); return; }
    if (e.key === "Tab") {
      var f = focusables();
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1], a = document.activeElement;
      if (!backdrop.contains(a)) { e.preventDefault(); first.focus(); }
      else if (e.shiftKey && a === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && a === last) { e.preventDefault(); first.focus(); }
    }
  });

  // Replace the panel; returns after moving focus to focusEl (or the first control).
  function mount(panelChildren, opts) {
    ensureBackdrop();
    opts = opts || {};
    var wasOpen = isOpen();
    // a disabled control (a button just pressed) drops focus to <body>; treat that as "focus was in the dialog"
    var active = document.activeElement;
    var hadFocus = wasOpen && (!active || active === document.body || backdrop.contains(active));
    var panel = el("div", {
      class: "iq-modal-panel" + (opts.split ? " iq-modal-split" : ""), role: "dialog", "aria-modal": "true", "aria-labelledby": "iqjpdl-title"
    }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqjpdl-title", text: T.btnTitle }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": T.close, text: "×" })
      ])
    ].concat(panelChildren));
    panel.querySelector(".iq-modal-close").addEventListener("click", closeModal);
    backdrop.textContent = "";
    backdrop.appendChild(panel);
    backdrop.style.display = "flex";
    if (!wasOpen || hadFocus) {
      var target = opts.focus || focusables()[1] || focusables()[0];
      if (target && target.focus) target.focus();
    }
    return panel;
  }

  function stateLine(text) { return el("p", { class: "iqjp-state", text: T.statePrefix + text }); }
  function alertBox() { return el("div", { class: "iq-form-error", role: "alert" }); }
  function showMsg(box, text) { box.textContent = text; box.classList.add("show"); }
  function hideMsg(box) { box.textContent = ""; box.classList.remove("show"); }
  function termsLink(text) { return el("a", { href: "terms.html", target: "_blank", rel: "noopener", text: text }); }

  // ---- routing by status ----
  function route(status) {
    if (status === "pending") showPending();
    else if (status === "approved") showApproved();
    else showEnded(status);
  }

  // Quiet-or-visible status check bound to the current view token.
  // cb(res, stillCurrent) is called only when the view is still the one that asked.
  function checkNow(code, tok, cb) {
    fetchStatus(code).then(function (res) {
      if (res.status) recordStatus(res.status);
      if (tok !== viewTok || !isOpen()) return;
      cb(res);
    });
  }

  // ===== View A: request form =====
  function showRequest() {
    stopPoll();
    var tok = ++viewTok;

    var sectorSel = el("select", { class: "iq-select", id: "iqjpdl-sector", required: "required" },
      [el("option", { value: "", text: T.choose })].concat(SECTORS.map(function (o) { return el("option", { value: o[0], text: o[1] }); })));
    var purposeSel = el("select", { class: "iq-select", id: "iqjpdl-purpose", required: "required" },
      [el("option", { value: "", text: T.choose })].concat(PURPOSES.map(function (o) { return el("option", { value: o[0], text: o[1] }); })));
    var affil = el("input", { class: "iq-input", id: "iqjpdl-affil", type: "text", maxlength: "80", autocomplete: "organization", placeholder: T.affilPh, "aria-describedby": "iqjpdl-affil-note" });
    var consent = el("input", { type: "checkbox", id: "iqjpdl-consent" });
    var honeypot = el("input", { type: "text", name: "iqjp_trap", tabindex: "-1", autocomplete: "off", "aria-hidden": "true", class: "iqjp-hp" });
    var err = alertBox(); err.id = "iqjpdl-error";
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: T.submit });

    var scroll = el("div", { class: "iq-modal-scroll" }, [
      // the privacy notice comes first so it is visible on narrow screens without scrolling inside the box
      el("div", { class: "iq-disclaimer" }, [T.privacyA, el("a", { href: "terms.html#privacy", target: "_blank", rel: "noopener", text: T.privacyLink }), T.privacyB]),
      el("div", { class: "iq-field" }, [el("label", { for: "iqjpdl-sector", text: T.sectorLabel }, [el("span", { class: "iq-hint", text: T.required })]), sectorSel]),
      el("div", { class: "iq-field" }, [el("label", { for: "iqjpdl-purpose", text: T.purposeLabel }, [el("span", { class: "iq-hint", text: T.required })]), purposeSel]),
      el("div", { class: "iq-field" }, [
        el("label", { for: "iqjpdl-affil", text: T.affilLabel }, [el("span", { class: "iq-hint", text: T.optional })]),
        affil,
        el("div", { class: "iq-hint iqjp-note", id: "iqjpdl-affil-note", text: T.affilNote })
      ]),
      el("div", { class: "iq-disclaimer", text: T.disclaimer })
    ]);
    // the consent row sits in the fixed footer so it is always visible next to the submit button
    var consentRow = el("div", { class: "iqjp-consent" }, [
      el("label", { class: "iq-check-row", for: "iqjpdl-consent" }, [consent, el("span", {}, [termsLink(T.termsLink), T.consentTail])])
    ]);
    var form = el("form", { id: "iqjpdl-form", novalidate: "novalidate" }, [scroll, el("div", { class: "iq-modal-footer" }, [consentRow, honeypot, err, submitBtn])]);

    // restore-by-code
    var rInput = el("input", { class: "iq-input", id: "iqjpdl-restore-code", type: "text", autocomplete: "off", autocapitalize: "none", spellcheck: "false", placeholder: T.restorePh, maxlength: "64" });
    var rErr = alertBox();
    var rBtn = el("button", { class: "iq-btn", type: "submit", text: T.restoreBtn });
    var rForm = el("form", { class: "iqjp-restore-form", id: "iqjpdl-restore", novalidate: "novalidate" }, [
      el("div", { class: "iq-field" }, [el("label", { for: "iqjpdl-restore-code", text: T.restoreLabel }), rInput]),
      rErr, rBtn
    ]);
    rForm.hidden = true;
    var rToggle = el("button", { class: "iq-anon-link iqjp-link", type: "button", "aria-expanded": "false", "aria-controls": "iqjpdl-restore", text: T.restoreLink });
    rToggle.addEventListener("click", function () {
      var open = rForm.hidden;
      rForm.hidden = !open;
      rToggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) rInput.focus();
    });

    var panel = mount([
      el("p", { class: "small-muted", style: "margin-top:0", text: T.intro }),
      el("div", { class: "iqjp-restore" }, [rToggle, rForm]),
      form
    ], { split: true, focus: sectorSel });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      hideMsg(err);
      sectorSel.removeAttribute("aria-invalid"); purposeSel.removeAttribute("aria-invalid"); consent.removeAttribute("aria-invalid");
      var bad = [];
      if (!sectorSel.value) bad.push(sectorSel);
      if (!purposeSel.value) bad.push(purposeSel);
      if (!consent.checked) bad.push(consent);
      if (bad.length) {
        bad.forEach(function (n) { n.setAttribute("aria-invalid", "true"); });
        showMsg(err, T.errValidate);
        bad[0].focus();
        return;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = T.sending;
      callGate("jp_dl_request", {
        sector: sectorSel.value, purpose: purposeSel.value, affil: affil.value.trim(), page: pageName(), consent: "1", _hp: honeypot.value
      }).then(function (r) {
        var code = r.ok === true ? normalizeCode(r.code) : "";
        if (tok !== viewTok) {
          // The visitor left this view while the request was in flight. The server row and the owner mail already exist,
          // so keep the issued code (unless a code was stored meanwhile) instead of forcing a duplicate request.
          if (validCode(code) && !getCode()) { setCode(code); recordStatus("pending"); }
          return;
        }
        if (validCode(code)) {
          setCode(code);
          recordStatus("pending");
          showPending();
          return;
        }
        submitBtn.disabled = false;
        submitBtn.textContent = T.submit;
        if (r.reason === "busy") showMsg(err, T.errBusy);
        else if (r.reason === "not_configured") showMsg(err, T.errNotConfigured);
        else if (r.reason === "invalid") showMsg(err, T.errValidate);
        else showMsg(err, T.errNet);
      });
    });

    rForm.addEventListener("submit", function (e) {
      e.preventDefault();
      hideMsg(rErr);
      var code = normalizeCode(rInput.value);
      if (!validCode(code)) { showMsg(rErr, T.errRestore); rInput.focus(); return; }
      rBtn.disabled = true;
      fetchStatus(code).then(function (res) {
        if (tok !== viewTok) return;
        rBtn.disabled = false;
        if (res.status && res.status !== "unknown") {
          setCode(code);
          recordStatus(res.status);
          route(res.status);
        } else if (res.status === "unknown") {
          showMsg(rErr, T.errRestore);
        } else if (res.error === "not_configured") {
          showMsg(rErr, T.errNotConfigured);
        } else {
          showMsg(rErr, T.errNet);
        }
      });
    });
    return panel;
  }

  // ===== View B: pending =====
  function showPending() {
    stopPoll();
    var tok = ++viewTok;
    var code = getCode();
    var note = el("p", { class: "small-muted iqjp-note-line" });
    var err = alertBox();
    var checkBtn = el("button", { class: "iq-btn", type: "button", text: T.check });
    var closeBtn = el("button", { class: "iq-btn iq-btn-ghost", type: "button", text: T.close });
    var copyBtn = el("button", { class: "iq-btn iq-btn-ghost iqjp-copy", type: "button", "aria-live": "polite", text: T.copy });
    var codeEl = el("span", { class: "iqjp-code" + (persisted ? "" : " iqjp-code-big"), id: "iqjpdl-code", text: code ? formatCode(code) : "" });
    var forgetAsk = el("div", { class: "iq-anon-confirm iqjp-forget-ask" }, [
      el("p", { style: "margin:0 0 8px", text: T.forgetAsk }),
      el("div", { class: "iqjp-actions" }, [
        el("button", { class: "iq-btn", type: "button", "data-act": "forget-yes", text: T.forgetYes }),
        el("button", { class: "iq-btn iq-btn-ghost", type: "button", "data-act": "forget-no", text: T.forgetNo })
      ])
    ]);
    forgetAsk.hidden = true;
    var forgetLink = el("button", { class: "iq-anon-link iqjp-link", type: "button", "aria-expanded": "false", text: T.forget });

    var kids = [
      el("div", { class: "iqjp-status", role: "status", "aria-live": "polite" }, [stateLine(T.stPending), note]),
      el("p", { class: "iqjp-body", text: T.pendingBody }),
      el("div", { class: "iqjp-codebox" }, [
        el("div", { class: "iqjp-code-label", text: T.codeLabel }),
        el("div", { class: "iqjp-code-row" }, [codeEl, copyBtn])
      ])
    ];
    if (!persisted) kids.push(el("p", { class: "iqjp-warn", text: T.codeNotSaved }));
    kids.push(el("p", { class: "small-muted", text: T.codeNote }));
    kids.push(err);
    kids.push(el("div", { class: "iqjp-actions" }, [checkBtn, closeBtn]));
    kids.push(el("div", { class: "iqjp-forget" }, [forgetLink, forgetAsk]));
    mount(kids, { focus: checkBtn });

    closeBtn.addEventListener("click", closeModal);
    copyBtn.addEventListener("click", function () {
      var text = codeEl.textContent;
      var done = function (ok) {
        if (ok) {
          copyBtn.textContent = T.copied;
          setTimeout(function () { copyBtn.textContent = T.copy; }, 2500);
        } else {
          try { var r = document.createRange(); r.selectNodeContents(codeEl); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); } catch (e) { /* ignore */ }
        }
      };
      var fallback = function () {
        var ok = false;
        try {
          var r = document.createRange(); r.selectNodeContents(codeEl);
          var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
          ok = document.execCommand("copy");
        } catch (e) { ok = false; }
        done(ok);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
      } else fallback();
    });
    forgetLink.addEventListener("click", function () {
      forgetAsk.hidden = false;
      forgetLink.setAttribute("aria-expanded", "true");
      forgetAsk.querySelector('[data-act="forget-no"]').focus();
    });
    forgetAsk.querySelector('[data-act="forget-no"]').addEventListener("click", function () {
      forgetAsk.hidden = true;
      forgetLink.setAttribute("aria-expanded", "false");
      forgetLink.focus();
    });
    forgetAsk.querySelector('[data-act="forget-yes"]').addEventListener("click", function () {
      sDel(CODE_KEY); sDel(SEEN_KEY);
      setBtnState("none");
      showRequest();
    });

    var manual = false;
    function apply(res) {
      if (res.status === "pending") {
        note.textContent = T.notYet(hhmm());
        hideMsg(err);
      } else if (res.status) {
        route(res.status);
      } else if (manual) {
        showMsg(err, res.error === "not_configured" ? T.errNotConfigured : T.errNet);
      }
    }
    checkBtn.addEventListener("click", function () {
      if (!code || checkBtn.disabled) return;
      manual = true;
      checkBtn.disabled = true;
      hideMsg(err);
      fetchStatus(code).then(function (res) {
        if (res.status) recordStatus(res.status);
        if (tok !== viewTok || !isOpen()) return;
        checkBtn.disabled = false;
        apply(res);
        manual = false;
      });
    });

    // auto-check every 15 s (max 40 times) while this view is open
    if (code) {
      pollTimer = setInterval(function () {
        if (tok !== viewTok || !isOpen()) { stopPoll(); return; }
        if (pollBusy) return;
        if (++pollCount > POLL_MAX) { clearInterval(pollTimer); pollTimer = null; return; }
        pollBusy = true;
        fetchStatus(code).then(function (res) {
          pollBusy = false;
          if (res.status) recordStatus(res.status);
          if (tok !== viewTok || !isOpen()) return;
          apply(res);
        });
      }, POLL_MS);
    }
    return { apply: apply };
  }

  // ===== View C: approved =====
  function showApproved() {
    stopPoll();
    var tok = ++viewTok;
    var code = getCode();
    var note = el("p", { class: "small-muted iqjp-note-line" });
    var err = alertBox();
    var dlBtn = el("button", { class: "iq-btn", type: "button", id: "iqjpdl-download", text: T.dl });
    var closeBtn = el("button", { class: "iq-btn iq-btn-ghost", type: "button", text: T.close });
    mount([
      el("div", { class: "iqjp-status", role: "status", "aria-live": "polite" }, [stateLine(T.stApproved), note]),
      el("p", { class: "iqjp-body", text: T.approvedBody }),
      el("p", { class: "small-muted", text: T.fileInfo("insurequant_jp_tables_" + todayStr() + ".xlsx") }),
      el("div", { class: "iq-disclaimer" }, [T.disclaimer + " ", T.termsTail, termsLink(T.termsLink), T.termsTail2]),
      err,
      el("div", { class: "iqjp-actions" }, [dlBtn, closeBtn])
    ], { focus: dlBtn });
    closeBtn.addEventListener("click", closeModal);
    dlBtnLive = dlBtn;
    if (dlBusy) { dlBtn.disabled = true; dlBtn.textContent = T.dlBusy; }   // a download started in an earlier view is still running

    function failWith(msg) { showMsg(err, msg); }
    function recheck() {
      checkNow(code, tok, function (res) { if (res.status && res.status !== "approved") route(res.status); else failWith(T.errDlNet); });
    }
    dlBtn.addEventListener("click", function () {
      if (dlBusy || !code) return;
      dlBusy = true;
      dlBtn.disabled = true;
      dlBtn.textContent = T.dlBusy;
      hideMsg(err);
      note.textContent = "";
      download(code).then(function (out) {
        dlBusy = false;
        // a download that outlived its view still frees the button of the view that replaced it
        if (dlBtnLive && dlBtnLive.isConnected) { dlBtnLive.disabled = false; dlBtnLive.textContent = T.dl; }
        if (tok !== viewTok || !isOpen()) return;
        dlBtn.disabled = false;
        dlBtn.textContent = T.dl;
        if (out === "ok") note.textContent = T.dlStarted;
        else if (out === "limit") failWith(T.errLimit);
        else if (out === "updating") failWith(T.errUpdating);
        else if (out === "open") failWith(T.errOpen);
        else if (out === "recheck") recheck();
        else failWith(T.errDlNet);
      });
    });
  }

  // ===== View D: denied / revoked / unknown =====
  function showEnded(status) {
    stopPoll();
    ++viewTok;
    var info = ENDED[status] || ENDED.unknown;
    var renew = el("button", { class: "iq-btn", type: "button", text: T.renew });
    var closeBtn = el("button", { class: "iq-btn iq-btn-ghost", type: "button", text: T.close });
    mount([
      el("div", { class: "iqjp-status", role: "status", "aria-live": "polite" }, [stateLine(info.state)]),
      el("p", { class: "iqjp-body", text: info.body }),
      el("div", { class: "iqjp-actions" }, [renew, closeBtn])
    ], { focus: renew });
    closeBtn.addEventListener("click", closeModal);
    renew.addEventListener("click", function () {
      sDel(CODE_KEY); sDel(SEEN_KEY);
      setBtnState("none");
      showRequest();
    });
  }

  // ===== download: blob -> key -> AES-GCM -> xlsx =====
  // Returns "ok" | "limit" | "updating" | "open" | "recheck" | "net".
  // The blob is fetched before the key is requested so that a missing file never burns the daily key quota.
  async function download(code) {
    var subtle = window.crypto && window.crypto.subtle;
    if (!subtle || typeof subtle.importKey !== "function" || typeof subtle.decrypt !== "function") return "open";

    var buf;
    var ctl = (typeof AbortController === "function") ? new AbortController() : null;
    var abortTimer = ctl ? setTimeout(function () { ctl.abort(); }, BLOB_TIMEOUT_MS) : null;
    try {
      var resp = await fetch(BLOB_URL, ctl ? { cache: "no-cache", signal: ctl.signal } : { cache: "no-cache" });
      if (resp.status === 404) return "updating";
      if (!resp.ok) return "net";
      buf = new Uint8Array(await resp.arrayBuffer());
    } catch (e) { return "net"; }
    finally { if (abortTimer) clearTimeout(abortTimer); }
    if (buf.length < 8 + 12 + 16 || String.fromCharCode(buf[0], buf[1], buf[2], buf[3]) !== "IQJ1") return "open";
    var blobKid = hex(buf.subarray(4, 8));

    var r = await callGate("jp_dl_key", { code: code });
    if (r.ok !== true) {
      if (r.reason === "limit") return "limit";
      if (r.reason === "not_approved" || r.reason === "unknown") return "recheck";
      return "net";
    }
    if (typeof r.key !== "string" || typeof r.kid !== "string") return "net";
    if (r.kid.toLowerCase() !== blobKid) return "updating";

    var keyBytes = null;
    try {
      var bin = atob(r.key);
      keyBytes = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) keyBytes[i] = bin.charCodeAt(i);
      if (keyBytes.length !== 32) return "open";
      var cryptoKey = await subtle.importKey("raw", keyBytes, { name: "AES-GCM" }, false, ["decrypt"]);
      var plain = await subtle.decrypt({ name: "AES-GCM", iv: buf.subarray(8, 20), additionalData: buf.subarray(0, 8) }, cryptoKey, buf.subarray(20));
    } catch (e) {
      return "open";
    } finally {
      if (keyBytes) keyBytes.fill(0);
    }

    var url = URL.createObjectURL(new Blob([plain], { type: XLSX_MIME }));
    var a = el("a", { href: url, download: "insurequant_jp_tables_" + todayStr() + ".xlsx" });
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    return "ok";
  }

  // ===== init =====
  function injectFallbackCss() {
    // pages that do not load jp.css (index.html) get the same few rules from here; the marker below is defined in jp.css
    var marker = "";
    try { marker = getComputedStyle(document.documentElement).getPropertyValue("--iqjp-css").trim(); } catch (e) { /* ignore */ }
    if (marker) return;
    var css = "#downloadMasterBtn .iqjp-dot{display:none;position:relative;width:12px;height:12px;margin-left:6px;vertical-align:-1px;border-radius:50%;box-sizing:border-box;border:2px solid var(--on-primary)}#downloadMasterBtn[data-state=\"pending\"] .iqjp-dot{display:inline-block;background:var(--warn)}#downloadMasterBtn[data-state=\"approved\"] .iqjp-dot{display:inline-block;width:15px;height:15px;background:var(--pos)}#downloadMasterBtn[data-state=\"approved\"] .iqjp-dot::after{content:\"\";position:absolute;left:50%;top:46%;width:3px;height:6px;border:solid var(--on-primary);border-width:0 2px 2px 0;transform:translate(-50%,-62%) rotate(45deg)}.iqjp-modal #iqjpdl-form{display:flex;flex-direction:column;flex:1;min-height:0}.iqjp-modal a{color:var(--primary)}.iqjp-consent{margin-bottom:var(--sp-3)}.iqjp-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}.iqjp-note{margin-top:6px;line-height:1.5}.iqjp-restore{margin:0 0 var(--sp-3)}.iqjp-restore-form{margin-top:var(--sp-2);padding:var(--sp-3);border:1px dashed var(--border);border-radius:var(--r-sm)}.iqjp-restore-form .iq-field{margin-bottom:var(--sp-2)}.iqjp-restore-form[hidden],.iqjp-forget-ask[hidden]{display:none}.iqjp-state{margin:0 0 var(--sp-2);font-size:14px;font-weight:700;color:var(--text)}.iqjp-note-line{margin:0 0 var(--sp-3)}.iqjp-note-line:empty{display:none}.iqjp-body{margin:0 0 var(--sp-3);font-size:14px;line-height:1.7;color:var(--text)}.iqjp-codebox{margin:0 0 var(--sp-3)}.iqjp-code-label{margin-bottom:var(--sp-1);font-size:13px;font-weight:600;color:var(--text)}.iqjp-code-row{display:flex;align-items:center;gap:var(--sp-2);flex-wrap:wrap}.iqjp-code{flex:1 1 220px;min-width:0;box-sizing:border-box;padding:8px 10px;border:1px solid var(--control-border);border-radius:var(--r-md);background:var(--card);color:var(--text);font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace;font-size:13px;letter-spacing:.02em;user-select:all;overflow-wrap:anywhere}.iqjp-code-big{font-size:15px;font-weight:700;border:2px solid var(--warn)}.iqjp-modal .iq-btn.iqjp-copy{width:auto;flex:0 0 auto;padding:8px 14px}.iqjp-warn{margin:0 0 var(--sp-3);padding:var(--sp-2) var(--sp-3);border-left:4px solid var(--warn);background:var(--card);color:var(--text);font-size:13px;font-weight:700}.iqjp-actions{display:flex;gap:var(--sp-2);flex-wrap:wrap}.iqjp-actions .iq-btn{flex:1 1 120px;width:auto}.iqjp-actions .iq-btn:first-child{flex:2 1 170px}.iqjp-forget{margin-top:var(--sp-3);text-align:center}.iqjp-forget-ask{margin-top:var(--sp-2);text-align:left}@media (max-width:640px){#downloadMasterBtn{min-height:44px}#downloadMasterBtn .iqjp-dot{width:10px;height:10px;margin-left:4px}#downloadMasterBtn[data-state=\"approved\"] .iqjp-dot{width:13px;height:13px}.iqjp-modal .iq-btn,.iqjp-modal .iq-select,.iqjp-modal .iq-input{min-height:44px}.iqjp-modal .iq-modal-close{min-width:44px;min-height:44px}.iqjp-modal .iq-check-row{min-height:44px;align-items:center}.iqjp-modal .iqjp-link{min-height:44px;display:inline-flex;align-items:center}.iqjp-code{font-size:12px}}";
    var s = document.createElement("style");
    s.id = "iqjp-fallback-css";
    s.textContent = css;
    document.head.appendChild(s);
  }

  function init() {
    btn = document.getElementById("downloadMasterBtn");
    if (!btn) return;
    injectFallbackCss();
    var full = btn.querySelector(".dl-full");
    baseLabel = (full ? full.textContent : btn.textContent).trim();
    dot = btn.querySelector(".iqjp-dot");
    if (!dot) { dot = el("span", { class: "iqjp-dot", "aria-hidden": "true" }); btn.appendChild(dot); }
    btn.setAttribute("aria-haspopup", "dialog");

    var code = getCode();
    var seen = code ? readSeen() : null;
    setBtnState(code && seen ? seen.s : "none");

    btn.addEventListener("click", function () {
      opener = btn;
      var c = getCode();
      if (!c) { showRequest(); return; }
      var s = (readSeen() || { s: "pending" }).s;
      route(s);
      var tok = viewTok;
      fetchStatus(c).then(function (res) {
        if (!res.status) return;
        recordStatus(res.status);
        if (tok !== viewTok || !isOpen()) return;
        if (res.status !== s) route(res.status);
        else if (res.status === "pending") {
          var n = backdrop.querySelector(".iqjp-note-line");
          if (n) n.textContent = T.notYet(hhmm());
        }
      });
    });

    // another tab stored or deleted the code / status: refresh the dot (no network)
    window.addEventListener("storage", function (e) {
      if (e.key !== null && e.key !== CODE_KEY && e.key !== SEEN_KEY) return;
      var c = getCode();
      var s = c ? readSeen() : null;
      setBtnState(c && s ? s.s : "none");
    });

    // quiet check once per page load (skipped when the last check is fresh)
    if (code && !(seen && Date.now() - seen.t < FRESH_MS)) {
      setTimeout(function () {
        if (isOpen()) return;
        fetchStatus(code).then(function (res) { if (res.status) recordStatus(res.status); });
      }, QUIET_DELAY_MS);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
