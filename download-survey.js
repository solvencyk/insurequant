// InsureQuant — 마스터 데이터 다운로드 방명록 (index.html 전용).
// GitHub Pages는 서버 없는 정적 호스팅이라 마스터 데이터 자체는 접근 제한이 없다(다른 페이지들도
// 이미 fetch로 그대로 공개). 그래서 이 폼은 접근 통제가 아니라 방명록이다 — 정직하게 그렇게
// 안내한다(inbox/designer/20260828T0300Z, orchestrator+owner).
// 짧은 방명록(소속/업권/데이터 목록) 남기면 선택 시트 + 출처 표지가 담긴 xlsx 1개를 바로 받는다.
(function () {
  "use strict";

  // name = 화면 표시·설문 응답용 라벨. file = public_exports/ 스냅샷(루트 마스터 JSON을 그대로
  // 읽지 않음 — 공유 워킹트리에서 다른 세션이 그 파일을 수정 중일 수 있어, 커밋된 상태로 미리
  // 떠둔 스냅샷만 공개한다. scripts/export_public_sheets.py 참조).
  // code = 파일명에 박는 축약(예: insurequant_20260828_KICS_PL.xlsx).
  var SHEETS = [
    { name: "17BS", file: "public_exports/17BS.json", code: "BS", label: "재무상태표 (17BS)" },
    { name: "K-ICS공시", file: "public_exports/K-ICS공시.json", code: "KICS", label: "K-ICS 지급여력 공시" },
    { name: "금리민감도", file: "public_exports/금리민감도.json", code: "RATE", label: "K-ICS 금리민감도" },
    { name: "CSM워터폴", file: "public_exports/CSM워터폴.json", code: "CSMWF", label: "CSM 워터폴" },
    { name: "CSM상각", file: "public_exports/CSM상각.json", code: "CSMAM", label: "CSM 상각 스케줄" },
    { name: "신계약CSM배수", file: "public_exports/신계약CSM배수.json", code: "NBCSM", label: "신계약 CSM 배수" },
    { name: "손익분해PL", file: "public_exports/손익분해PL.json", code: "PL", label: "손익분해 (PL)" },
    { name: "배당", file: "public_exports/배당.json", code: "DIV", label: "배당에 관한 사항" }
  ];
  var MANIFEST_FILE = "public_exports/manifest.json";
  // build_master_xlsx.py coerce()의 NUMERIC_COLS와 동일 — 공식 마스터 xlsx와 같은 컬럼만
  // 숫자 셀로, 나머지(티커 등)는 텍스트 유지(안 그러면 "000060"의 앞자리 0이 날아감).
  var NUMERIC_COLS = { "값": 1, "-100bp": 1, "-50bp": 1, "base": 1, "+50bp": 1, "+100bp": 1,
    "상각액": 1, "신계약CSM_연누계": 1, "월납월초보험료_연누계": 1, "신계약CSM배수_연누계": 1 };

  function shortName(n) {
    if (!n) return n;
    return String(n)
      .replace(/화재해상보험$/, "화재").replace(/해상화재보험$/, "해상")
      .replace(/손해보험$/, "손보").replace(/생명보험$/, "생명")
      .replace(/재보험$/, "").replace(/보증보험$/, "보증");
  }
  var NAME_ABBR_EXTRA = {
    "신한이지손해보험": "신한EZ손해", "에이비엘생명보험": "ABL생명", "케이디비생명보험": "KDB생명",
    "아이엠라이프생명보험": "iM라이프", "에이아이에이생명보험": "AIA생명",
    "비엔피파리바카디프생명보험": "BNP카디프생명", "교보라이프플래닛생명보험": "교보라이프플래닛",
    "처브라이프생명보험": "처브라이프", "메트라이프생명보험": "메트라이프", "악사손해보험": "악사손보",
    "신한라이프생명보험": "신한라이프", "푸본현대생명보험": "푸본현대"
  };
  var AFFIL_OPTIONS = [
    "메리츠화재해상보험", "한화손해보험", "롯데손해보험", "예별손해보험", "흥국화재",
    "삼성화재해상보험", "현대해상", "KB손해보험", "DB손해보험", "AIG손해보험", "NH농협손해보험",
    "악사손해보험", "하나손해보험", "신한이지손해보험", "카카오페이손해보험", "서울보증보험", "코리안리재보험",
    "한화생명", "삼성생명보험", "에이비엘생명보험", "흥국생명보험", "케이디비생명보험", "교보생명보험",
    "라이나생명보험", "비엔피파리바카디프생명보험", "아이엠라이프생명보험", "미래에셋생명보험",
    "에이아이에이생명보험", "DB생명보험", "푸본현대생명보험", "동양생명", "신한라이프생명보험",
    "메트라이프생명보험", "하나생명보험", "KB라이프생명", "처브라이프생명보험", "농협생명보험",
    "교보라이프플래닛생명보험", "IBK연금보험"
  ].map(function (n) { return NAME_ABBR_EXTRA[n] || shortName(n); });
  // 익명이어도 쓸모 있는 정보가 남게(오케스트레이터 결정 — 익명에 마찰을 주면 사람들이 익명을
  // 포기하는 게 아니라 아무 회사나 골라 소속 통계가 오염된다). 소속을 밝히든 안 밝히든 공통.
  var SECTORS = ["개인", "보험사", "증권·운용", "컨설팅·회계", "학계", "언론", "감독기관", "기타"];
  // 주 타겟층(계리사) 감안 — 보험사 내 부서 구분. 선택 항목(필수 아님).
  var DEPARTMENTS = ["결산(Valuation)", "리스크관리(RM)", "기획", "상품개발", "계리", "자산운용", "언더라이팅", "재무/회계", "기타"];
  var PURPOSES = ["리서치/애널리스트 업무", "투자 참고", "학업/논문", "개인 관심", "기타"];
  var DONE_KEY = "iqSurveyDone_v1";
  var AFFIL_KEY = "iqSurveyAffil_v1";
  var SECTOR_KEY = "iqSurveySector_v1";
  var DEPT_KEY = "iqSurveyDept_v1";
  var DISCLAIMER_TEXT = "본 데이터는 공시자료를 자동으로 수집·가공한 것으로 오류가 있을 수 있으며, 투자 판단의 근거로 사용할 수 없습니다. 오류 발견 시 화면의 우측 하단 버튼을 통해 제보 부탁드립니다.";
  var SOURCE_URL = "https://www.insurequant.com";

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

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0");
  }

  function sheetChecklist() {
    var grid = el("div", { class: "iq-check-grid" });
    SHEETS.forEach(function (s) {
      var id = "iqdl-sheet-" + s.name;
      var cb = el("input", { type: "checkbox", id: id, value: s.name });
      grid.appendChild(el("label", { class: "iq-check-row", for: id }, [cb, document.createTextNode(s.label)]));
    });
    return grid;
  }

  function optionSelect(id, options) {
    return el("select", { class: "iq-select", id: id },
      [el("option", { value: "", text: "선택 안 함" })].concat(options.map(function (s) { return el("option", { value: s, text: s }); })));
  }

  function selectedSheets(grid) {
    return Array.prototype.slice.call(grid.querySelectorAll("input:checked")).map(function (c) { return c.value; });
  }

  function coerceRow(row) {
    var out = {};
    for (var k in row) {
      var v = row[k];
      if (v != null && NUMERIC_COLS[k]) {
        var n = Number(v);
        out[k] = Number.isFinite(n) ? n : v;
      } else {
        out[k] = v;
      }
    }
    return out;
  }

  function buildCoverSheet(names, manifest) {
    var metas = names.map(function (n) { return manifest && manifest.sheets ? manifest.sheets[n] : null; }).filter(Boolean);
    var mins = metas.map(function (m) { return m.quarter_min; }).filter(Boolean).sort();
    var maxs = metas.map(function (m) { return m.quarter_max; }).filter(Boolean).sort();
    var rows = [
      { 항목: "출처", 내용: SOURCE_URL },
      { 항목: "스냅샷 생성일시(UTC)", 내용: manifest ? manifest.generated_at_utc : "" },
      { 항목: "다운로드 생성일시(로컬)", 내용: new Date().toLocaleString("ko-KR") },
      { 항목: "포함 시트", 내용: names.join(", ") },
      { 항목: "커버 분기 범위", 내용: (mins[0] && maxs[maxs.length - 1]) ? (mins[0] + " ~ " + maxs[maxs.length - 1]) : "" },
      { 항목: "안내", 내용: DISCLAIMER_TEXT }
    ];
    var ws = XLSX.utils.json_to_sheet(rows, { skipHeader: true });
    ws["!cols"] = [{ wch: 20 }, { wch: 70 }];
    return ws;
  }

  // 선택 시트 + 표지("요약")를 시트 탭 여러 개짜리 xlsx 1개로 묶어 다운로드(zip 아님).
  // public_exports/ 스냅샷을 fetch — 클라이언트에서 새로 만드는 값-스냅샷이라
  // insurequant_master_tables.xlsx(수식 캐시 있는 원본)는 전혀 건드리지 않는다.
  async function downloadSheets(names) {
    var manifest = await fetch(MANIFEST_FILE).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, buildCoverSheet(names, manifest), "요약");
    var dataList = await Promise.all(names.map(function (name) {
      var meta = SHEETS.filter(function (s) { return s.name === name; })[0];
      return fetch(meta.file).then(function (r) { return r.json(); });
    }));
    names.forEach(function (name, i) {
      var rows = dataList[i].map(coerceRow);
      var ws = XLSX.utils.json_to_sheet(rows);
      XLSX.utils.book_append_sheet(wb, ws, name);
    });
    var codes = names.map(function (name) { return SHEETS.filter(function (s) { return s.name === name; })[0].code; });
    XLSX.writeFile(wb, "insurequant_" + todayStr() + "_" + codes.join("_") + ".xlsx");
  }

  function buildBackdrop() {
    var backdrop = el("div", { class: "iq-modal-backdrop", id: "iqdl-backdrop", style: "display:none" });
    document.body.appendChild(backdrop);
    return backdrop;
  }

  function closeModal(backdrop, opener) {
    backdrop.style.display = "none";
    backdrop.innerHTML = "";
    if (opener && opener.focus) opener.focus();
  }

  function openFullSurvey(backdrop, opener) {
    var affilInput = el("input", { class: "iq-input", id: "iqdl-affil", list: "iqdl-affil-list", placeholder: "회사명을 입력하세요 (예: 삼성화재)", autocomplete: "off" });
    var datalist = el("datalist", { id: "iqdl-affil-list" }, AFFIL_OPTIONS.map(function (n) { return el("option", { value: n }); }));
    // 익명은 다른 선택지와 동등한 정상 옵션 — 확인 절차 없음(오케스트레이터 결정, 2026-08-28:
    // 마찰을 주면 사람들이 진짜 소속을 숨기는 대신 아무 회사나 골라버려 통계가 더 나빠진다).
    var anonCb = el("input", { type: "checkbox", id: "iqdl-anon" });
    var anonLabel = el("label", { class: "iq-check-row", for: "iqdl-anon", style: "margin-top:6px" }, [anonCb, document.createTextNode("회사명은 비공개로 할게요")]);
    var deptSel = optionSelect("iqdl-dept", DEPARTMENTS);
    var sectorSel = optionSelect("iqdl-sector", SECTORS);

    anonCb.addEventListener("change", function () {
      affilInput.disabled = anonCb.checked;
      if (anonCb.checked) affilInput.value = "";
    });

    var sheetGrid = sheetChecklist();
    var purposeSelect = el("select", { class: "iq-select", id: "iqdl-purpose" },
      [el("option", { value: "", text: "선택 안 함" })].concat(PURPOSES.map(function (p) { return el("option", { value: p, text: p }); })));
    var consentCb = el("input", { type: "checkbox", id: "iqdl-consent" });
    var errorMsg = el("div", { class: "iq-form-error", id: "iqdl-error", text: "소속 또는 익명 체크, 시트 1개 이상, 안내사항 확인이 필요합니다(비공개 선택 시 업권도 알려주세요)." });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "남기고 다운로드" });
    var honeypot = el("input", { type: "text", name: "website", tabindex: "-1", autocomplete: "off", style: "position:absolute;left:-9999px;width:1px;height:1px;opacity:0" });

    var form = el("form", { id: "iqdl-form" }, [
      el("div", { class: "iq-field" }, [el("label", { text: "소속" }), affilInput, datalist, anonLabel]),
      el("div", { class: "iq-field" }, [el("label", { text: "부서 " }, [el("span", { class: "iq-hint", text: "(선택)" })]), deptSel]),
      el("div", { class: "iq-field" }, [el("label", { text: "업권 " }, [el("span", { class: "iq-hint", text: "(비공개 선택 시 필수)" })]), sectorSel]),
      el("div", { class: "iq-field" }, [el("label", { text: "다운로드할 데이터 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), sheetGrid]),
      el("div", { class: "iq-field" }, [el("label", { text: "사용 목적 " }, [el("span", { class: "iq-hint", text: "(선택)" })]), purposeSelect]),
      el("div", { class: "iq-disclaimer" }, [document.createTextNode(DISCLAIMER_TEXT)]),
      el("div", { class: "iq-field", style: "margin-bottom:12px" }, [
        el("label", { class: "iq-check-row", for: "iqdl-consent" }, [consentCb, document.createTextNode("위 안내사항을 확인했습니다")])
      ]),
      honeypot, errorMsg, submitBtn
    ]);

    var panel = el("div", { class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqdl-title" }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqdl-title", text: "테이블 다운로드(.xlsx)" }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": "닫기", text: "×" })
      ]),
      el("p", { class: "small-muted", style: "margin-top:0" }, [document.createTextNode("파일 자체엔 접근 제한이 없습니다 — 아래는 방명록입니다. 남겨주시면 바로 다운로드가 시작됩니다.")]),
      form
    ]);
    backdrop.appendChild(panel);
    backdrop.style.display = "flex";
    affilInput.focus();

    if (!window.IQ_FORMS.isConfigured()) {
      submitBtn.disabled = true;
      submitBtn.textContent = "일시적으로 제출을 받을 수 없습니다";
    }

    panel.querySelector(".iq-modal-close").addEventListener("click", function () { closeModal(backdrop, opener); });
    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeModal(backdrop, opener); });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!window.IQ_FORMS.isConfigured()) return;
      if (honeypot.value) return; // bot
      var isAnon = anonCb.checked;
      var affilVal = isAnon ? "익명" : affilInput.value.trim();
      var sheets = selectedSheets(sheetGrid);
      var ok = (affilVal !== "") && sheets.length > 0 && consentCb.checked && (!isAnon || sectorSel.value !== "");
      if (!ok) { errorMsg.classList.add("show"); return; }
      errorMsg.classList.remove("show");
      submitBtn.disabled = true;
      submitBtn.textContent = "처리 중…";
      window.IQ_FORMS.submit("download", {
        affiliation: affilVal, department: deptSel.value, sector: sectorSel.value, sheets: sheets.join(", "), purpose: purposeSelect.value, consent: "동의함"
      }).then(function () {
        try {
          localStorage.setItem(DONE_KEY, "1");
          localStorage.setItem(AFFIL_KEY, affilVal);
          localStorage.setItem(SECTOR_KEY, sectorSel.value || "");
          localStorage.setItem(DEPT_KEY, deptSel.value || "");
        } catch (e2) { /* private mode 등 — 다음에 다시 물어봄, 무시 */ }
        return downloadSheets(sheets);
      }).then(function () {
        closeModal(backdrop, opener);
      }).catch(function (err) {
        console.error("[download-survey] 다운로드 실패:", err);
        submitBtn.disabled = false;
        submitBtn.textContent = "남기고 다운로드";
        errorMsg.textContent = "다운로드 중 문제가 발생했습니다. 다시 시도해 주세요.";
        errorMsg.classList.add("show");
      });
    });
  }

  function openSlimPicker(backdrop, opener) {
    var sheetGrid = sheetChecklist();
    var errorMsg = el("div", { class: "iq-form-error", text: "시트를 1개 이상 선택해 주세요." });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "다운로드" });
    var again = el("button", { type: "button", class: "iq-anon-link", text: "방명록 다시 작성" });
    var form = el("form", {}, [
      el("p", { class: "small-muted", style: "margin-top:0" }, [document.createTextNode("이전에 남겨주신 정보로 진행합니다(매번 기록됩니다).")]),
      el("div", { class: "iq-field" }, [el("label", { text: "다운로드할 데이터 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), sheetGrid]),
      errorMsg, submitBtn,
      el("div", { style: "text-align:center;margin-top:10px" }, [again])
    ]);
    var panel = el("div", { class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqdl-title2" }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqdl-title2", text: "테이블 다운로드(.xlsx)" }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": "닫기", text: "×" })
      ]),
      form
    ]);
    backdrop.appendChild(panel);
    backdrop.style.display = "flex";

    panel.querySelector(".iq-modal-close").addEventListener("click", function () { closeModal(backdrop, opener); });
    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeModal(backdrop, opener); });
    again.addEventListener("click", function () {
      try { localStorage.removeItem(DONE_KEY); } catch (e) { /* ignore */ }
      backdrop.innerHTML = "";
      openFullSurvey(backdrop, opener);
    });

    // localStorage로 방명록을 스킵해도 다운로드 이벤트 자체는 매번 기록한다(재방문자 다운로드가
    // 통째로 안 잡히는 걸 막기 위해 — inbox/designer/20260828T0300Z 추가요청) — 이전 응답을
    // 조용히 재전송, 다운로드를 막지는 않음(fire-and-forget).
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var sheets = selectedSheets(sheetGrid);
      if (!sheets.length) { errorMsg.classList.add("show"); return; }
      errorMsg.classList.remove("show");
      submitBtn.disabled = true;
      submitBtn.textContent = "처리 중…";
      var affilVal = "익명", sectorVal = "", deptVal = "";
      try {
        affilVal = localStorage.getItem(AFFIL_KEY) || "익명";
        sectorVal = localStorage.getItem(SECTOR_KEY) || "";
        deptVal = localStorage.getItem(DEPT_KEY) || "";
      } catch (e3) { /* ignore */ }
      window.IQ_FORMS.submit("download", { affiliation: affilVal, department: deptVal, sector: sectorVal, sheets: sheets.join(", "), purpose: "", consent: "재방문(방명록 생략)" });
      downloadSheets(sheets).then(function () {
        closeModal(backdrop, opener);
      }).catch(function (err) {
        console.error("[download-survey] 다운로드 실패:", err);
        submitBtn.disabled = false;
        submitBtn.textContent = "다운로드";
      });
    });
  }

  function init() {
    var btn = document.getElementById("downloadMasterBtn");
    if (!btn) return;
    var backdrop = buildBackdrop();
    btn.addEventListener("click", function () {
      backdrop.innerHTML = "";
      var done = false;
      try { done = localStorage.getItem(DONE_KEY) === "1"; } catch (e) { /* ignore */ }
      if (done) openSlimPicker(backdrop, btn);
      else openFullSurvey(backdrop, btn);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && backdrop.style.display === "flex") closeModal(backdrop, btn);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
