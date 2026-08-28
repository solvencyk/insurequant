// InsureQuant — 오류 제보 팝업 (site-wide, 4 페이지 공통).
// 사용: <script src="report-widget.js" data-sheet-hint="K-ICS공시"></script>
// forms-config.js를 먼저 로드해야 함(window.IQ_FORMS).
(function () {
  "use strict";

  var SHEETS = ["17BS", "K-ICS공시", "금리민감도", "CSM워터폴", "CSM상각", "신계약CSM배수", "손익분해PL", "배당"];
  var QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
    "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"];
  var COMPANIES = ["메리츠화재해상보험", "한화손해보험", "롯데손해보험", "예별손해보험", "흥국화재",
    "삼성화재해상보험", "현대해상", "KB손해보험", "DB손해보험", "AIG손해보험", "NH농협손해보험",
    "악사손해보험", "하나손해보험", "신한이지손해보험", "카카오페이손해보험", "서울보증보험", "코리안리재보험",
    "한화생명", "삼성생명보험", "에이비엘생명보험", "흥국생명보험", "케이디비생명보험", "교보생명보험",
    "라이나생명보험", "비엔피파리바카디프생명보험", "아이엠라이프생명보험", "미래에셋생명보험",
    "에이아이에이생명보험", "DB생명보험", "푸본현대생명보험", "동양생명", "신한라이프생명보험",
    "메트라이프생명보험", "하나생명보험", "KB라이프생명", "처브라이프생명보험", "농협생명보험",
    "교보라이프플래닛생명보험", "IBK연금보험"];

  var scriptEl = document.currentScript;
  var sheetHint = scriptEl && scriptEl.dataset ? scriptEl.dataset.sheetHint || "" : "";

  function shortName(n) {
    // index.html의 NAME_ABBR 표시 규칙과 동일 접미사만 — 이 위젯은 체크박스 라벨용 가벼운 버전.
    if (!n) return n;
    return String(n)
      .replace(/화재해상보험$/, "화재").replace(/해상화재보험$/, "해상")
      .replace(/손해보험$/, "손보").replace(/생명보험$/, "생명")
      .replace(/재보험$/, "").replace(/보증보험$/, "보증");
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

  function checkGrid(name, items, labelFn) {
    var grid = el("div", { class: "iq-check-grid", style: "max-height:160px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--r-sm);padding:8px" });
    items.forEach(function (val) {
      var id = name + "-" + val;
      var cb = el("input", { type: "checkbox", id: id, value: val });
      var row = el("label", { class: "iq-check-row", for: id }, [cb, document.createTextNode(labelFn ? labelFn(val) : val)]);
      grid.appendChild(row);
    });
    return grid;
  }

  function buildModal() {
    var sheetSelect = el("select", { class: "iq-select", id: "iqrep-sheet" },
      SHEETS.map(function (s) { return el("option", { value: s, text: s }); }));
    if (sheetHint && SHEETS.indexOf(sheetHint) !== -1) sheetSelect.value = sheetHint;

    var companyGrid = checkGrid("iqrep-co", COMPANIES, shortName);
    var quarterGrid = checkGrid("iqrep-q", QUARTERS);
    var detail = el("textarea", { class: "iq-textarea", id: "iqrep-detail", placeholder: "어떤 값이 왜 이상한지 적어주세요 (예: 2025.4Q 지급여력비율이 실제 공시보다 낮게 나옵니다)" });
    var honeypot = el("input", { type: "text", name: "website", tabindex: "-1", autocomplete: "off", style: "position:absolute;left:-9999px;width:1px;height:1px;opacity:0" });
    var errorMsg = el("div", { class: "iq-form-error", id: "iqrep-error", text: "오류 대상 시트와 오류 사항은 필수입니다." });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "제보 제출" });

    var form = el("form", { id: "iqrep-form" }, [
      el("div", { class: "iq-field" }, [el("label", { text: "오류 대상 시트" }), sheetSelect]),
      el("div", { class: "iq-field" }, [el("label", { text: "오류 대상 회사 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), companyGrid]),
      el("div", { class: "iq-field" }, [el("label", { text: "오류 대상 분기 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), quarterGrid]),
      el("div", { class: "iq-field" }, [el("label", { text: "오류 사항" }), detail]),
      honeypot, errorMsg, submitBtn
    ]);

    var panel = el("div", {
      class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqrep-title"
    }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqrep-title", text: "숫자 오류 제보" }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": "닫기", text: "×" })
      ]),
      el("p", { class: "small-muted", style: "margin-top:0" }, [document.createTextNode("발견하신 오류를 알려주시면 확인 후 반영하겠습니다.")]),
      form
    ]);
    var backdrop = el("div", { class: "iq-modal-backdrop", id: "iqrep-backdrop", style: "display:none" }, [panel]);
    document.body.appendChild(backdrop);

    var closeBtn = panel.querySelector(".iq-modal-close");
    var lastFocused = null;

    function open() {
      lastFocused = document.activeElement;
      backdrop.style.display = "flex";
      sheetSelect.focus();
      document.addEventListener("keydown", onKeydown);
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
      submitBtn.textContent = "제출 중…";
      window.IQ_FORMS.submit("report", {
        sheet: sheet, company: companies.join(", "), period: quarters.join(", "), detail: detailVal
      }).then(function () {
        submitBtn.textContent = "제출 완료 — 감사합니다";
        setTimeout(function () {
          close();
          form.reset();
          submitBtn.disabled = false;
          submitBtn.textContent = "제보 제출";
        }, 1200);
      });
    });

    return { open: open };
  }

  function init() {
    var modal = buildModal();
    var fab = el("button", { class: "iq-report-fab", type: "button" }, [document.createTextNode("⚑ 오류 제보")]);
    fab.addEventListener("click", modal.open);
    document.body.appendChild(fab);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
