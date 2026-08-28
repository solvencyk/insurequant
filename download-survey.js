// InsureQuant — 마스터 데이터 다운로드 게이트 (index.html 전용).
// 짧은 설문(소속/데이터 목록/사용목적/동의) 제출 시 선택한 시트만 다운로드.
// 주의: GitHub Pages는 서버가 없는 정적 호스팅이라 public_exports/*.csv 파일 자체는
// URL을 아는 사람 누구나 접근 가능 — 이 설문은 실제 접근제어가 아니라 정중한 소속 확인 절차.
(function () {
  "use strict";

  var SHEETS = [
    { name: "17BS", label: "재무상태표 (17BS)" },
    { name: "K-ICS공시", label: "K-ICS 지급여력 공시" },
    { name: "금리민감도", label: "K-ICS 금리민감도" },
    { name: "CSM워터폴", label: "CSM 워터폴" },
    { name: "CSM상각", label: "CSM 상각 스케줄" },
    { name: "신계약CSM배수", label: "신계약 CSM 배수" },
    { name: "손익분해PL", label: "손익분해 (PL)" },
    { name: "배당", label: "배당에 관한 사항" }
  ];
  var AFFIL_OPTIONS = [
    "메리츠화재해상보험", "한화손해보험", "롯데손해보험", "예별손해보험", "흥국화재",
    "삼성화재해상보험", "현대해상", "KB손해보험", "DB손해보험", "AIG손해보험", "NH농협손해보험",
    "악사손해보험", "하나손해보험", "신한이지손해보험", "카카오페이손해보험", "서울보증보험", "코리안리재보험",
    "한화생명", "삼성생명보험", "에이비엘생명보험", "흥국생명보험", "케이디비생명보험", "교보생명보험",
    "라이나생명보험", "비엔피파리바카디프생명보험", "아이엠라이프생명보험", "미래에셋생명보험",
    "에이아이에이생명보험", "DB생명보험", "푸본현대생명보험", "동양생명", "신한라이프생명보험",
    "메트라이프생명보험", "하나생명보험", "KB라이프생명", "처브라이프생명보험", "농협생명보험",
    "교보라이프플래닛생명보험", "IBK연금보험",
    "자산운용/증권", "컨설팅/회계법인", "학계/연구", "언론", "감독기관/공공", "기타 금융기관"
  ];
  var PURPOSES = ["리서치/애널리스트 업무", "투자 참고", "학업/논문", "개인 관심", "기타"];
  var DONE_KEY = "iqSurveyDone_v1";
  var AFFIL_KEY = "iqSurveyAffil_v1";

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

  function selectedSheets(grid) {
    return Array.prototype.slice.call(grid.querySelectorAll("input:checked")).map(function (c) { return c.value; });
  }

  async function downloadSheets(names) {
    if (names.length === 1) {
      var a1 = el("a", { href: "public_exports/" + encodeURIComponent(names[0]) + ".csv", download: names[0] + ".csv" });
      document.body.appendChild(a1); a1.click(); a1.remove();
      return;
    }
    var zip = new JSZip();
    await Promise.all(names.map(async function (name) {
      var res = await fetch("public_exports/" + encodeURIComponent(name) + ".csv");
      var blob = await res.blob();
      zip.file(name + ".csv", blob);
    }));
    var zipBlob = await zip.generateAsync({ type: "blob" });
    var url = URL.createObjectURL(zipBlob);
    var a = el("a", { href: url, download: "insurequant_data_" + todayStr() + ".zip" });
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
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
    var anonState = { value: false };
    var anonLink = el("button", { type: "button", class: "iq-anon-link", text: "소속을 밝히고 싶지 않습니다" });
    var anonConfirmBox = el("div", { class: "iq-anon-confirm", style: "display:none" });
    var anonYes = el("button", { type: "button", class: "iq-btn-ghost", style: "width:auto;padding:4px 10px;font-size:12px", text: "예, 익명으로 진행" });
    var anonCancel = el("button", { type: "button", class: "iq-btn-ghost", style: "width:auto;padding:4px 10px;font-size:12px;margin-left:6px", text: "취소" });
    anonConfirmBox.appendChild(document.createTextNode("정말 소속 없이 진행하시겠어요? "));
    anonConfirmBox.appendChild(anonYes);
    anonConfirmBox.appendChild(anonCancel);
    var anonStatus = el("div", { class: "small-muted", style: "display:none;margin-top:4px" }, [document.createTextNode("✓ 익명으로 진행합니다 — ")]);
    var anonRevert = el("button", { type: "button", class: "iq-anon-link", text: "취소" });
    anonStatus.appendChild(anonRevert);

    anonLink.addEventListener("click", function () { anonConfirmBox.style.display = "block"; });
    anonCancel.addEventListener("click", function () { anonConfirmBox.style.display = "none"; });
    anonYes.addEventListener("click", function () {
      anonState.value = true;
      affilInput.value = ""; affilInput.disabled = true;
      anonConfirmBox.style.display = "none";
      anonLink.style.display = "none";
      anonStatus.style.display = "block";
    });
    anonRevert.addEventListener("click", function () {
      anonState.value = false;
      affilInput.disabled = false;
      anonLink.style.display = "inline";
      anonStatus.style.display = "none";
    });

    var sheetGrid = sheetChecklist();
    var purposeSelect = el("select", { class: "iq-select", id: "iqdl-purpose" },
      [el("option", { value: "", text: "선택 안 함" })].concat(PURPOSES.map(function (p) { return el("option", { value: p, text: p }); })));
    var consentCb = el("input", { type: "checkbox", id: "iqdl-consent" });
    var errorMsg = el("div", { class: "iq-form-error", id: "iqdl-error", text: "소속(또는 익명 확인)과 시트 1개 이상, 안내사항 동의가 필요합니다." });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "설문 제출하고 다운로드" });
    var honeypot = el("input", { type: "text", name: "website", tabindex: "-1", autocomplete: "off", style: "position:absolute;left:-9999px;width:1px;height:1px;opacity:0" });

    var form = el("form", { id: "iqdl-form" }, [
      el("div", { class: "iq-field" }, [el("label", { text: "소속" }), affilInput, datalist,
        el("div", { class: "iq-anon" }, [anonLink, anonConfirmBox, anonStatus])]),
      el("div", { class: "iq-field" }, [el("label", { text: "다운로드할 데이터 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), sheetGrid]),
      el("div", { class: "iq-field" }, [el("label", { text: "사용 목적 " }, [el("span", { class: "iq-hint", text: "(선택)" })]), purposeSelect]),
      el("div", { class: "iq-disclaimer" }, [document.createTextNode("본 데이터는 공시자료를 자동으로 수집·가공한 것으로 오류가 있을 수 있으며, 투자 판단의 근거로 사용할 수 없습니다.")]),
      el("div", { class: "iq-field", style: "margin-bottom:12px" }, [
        el("label", { class: "iq-check-row", for: "iqdl-consent" }, [consentCb, document.createTextNode("위 안내사항을 확인했습니다")])
      ]),
      honeypot, errorMsg, submitBtn
    ]);

    var panel = el("div", { class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqdl-title" }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqdl-title", text: "마스터 데이터 다운로드" }),
        el("button", { class: "iq-modal-close", type: "button", "aria-label": "닫기", text: "×" })
      ]),
      form
    ]);
    backdrop.appendChild(panel);
    backdrop.style.display = "flex";
    affilInput.focus();

    panel.querySelector(".iq-modal-close").addEventListener("click", function () { closeModal(backdrop, opener); });
    backdrop.addEventListener("click", function (e) { if (e.target === backdrop) closeModal(backdrop, opener); });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (honeypot.value) return; // bot
      var affilVal = anonState.value ? "익명" : affilInput.value.trim();
      var sheets = selectedSheets(sheetGrid);
      var ok = (affilVal !== "") && sheets.length > 0 && consentCb.checked;
      if (!ok) { errorMsg.classList.add("show"); return; }
      errorMsg.classList.remove("show");
      submitBtn.disabled = true;
      submitBtn.textContent = "처리 중…";
      window.IQ_FORMS.submit("download", {
        affiliation: affilVal, sheets: sheets.join(", "), purpose: purposeSelect.value, consent: "동의함"
      }).then(function () {
        try {
          localStorage.setItem(DONE_KEY, "1");
          if (!anonState.value) localStorage.setItem(AFFIL_KEY, affilVal);
        } catch (e2) { /* private mode 등 — 다음에 다시 물어봄, 무시 */ }
        return downloadSheets(sheets);
      }).then(function () {
        closeModal(backdrop, opener);
      }).catch(function (err) {
        console.error("[download-survey] 다운로드 실패:", err);
        submitBtn.disabled = false;
        submitBtn.textContent = "설문 제출하고 다운로드";
        errorMsg.textContent = "다운로드 중 문제가 발생했습니다. 다시 시도해 주세요.";
        errorMsg.classList.add("show");
      });
    });
  }

  function openSlimPicker(backdrop, opener) {
    var sheetGrid = sheetChecklist();
    var errorMsg = el("div", { class: "iq-form-error", text: "시트를 1개 이상 선택해 주세요." });
    var submitBtn = el("button", { class: "iq-btn", type: "submit", text: "다운로드" });
    var again = el("button", { type: "button", class: "iq-anon-link", text: "설문 다시 작성" });
    var form = el("form", {}, [
      el("p", { class: "small-muted", style: "margin-top:0" }, [document.createTextNode("이전에 남겨주신 소속 정보로 진행합니다.")]),
      el("div", { class: "iq-field" }, [el("label", { text: "다운로드할 데이터 " }, [el("span", { class: "iq-hint", text: "(중복 선택 가능)" })]), sheetGrid]),
      errorMsg, submitBtn,
      el("div", { style: "text-align:center;margin-top:10px" }, [again])
    ]);
    var panel = el("div", { class: "iq-modal-panel", role: "dialog", "aria-modal": "true", "aria-labelledby": "iqdl-title2" }, [
      el("div", { class: "iq-modal-head" }, [
        el("div", { class: "iq-modal-title", id: "iqdl-title2", text: "마스터 데이터 다운로드" }),
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

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var sheets = selectedSheets(sheetGrid);
      if (!sheets.length) { errorMsg.classList.add("show"); return; }
      errorMsg.classList.remove("show");
      submitBtn.disabled = true;
      submitBtn.textContent = "처리 중…";
      var affilVal = "익명";
      try { affilVal = localStorage.getItem(AFFIL_KEY) || "익명"; } catch (e3) { /* ignore */ }
      window.IQ_FORMS.submit("download", { affiliation: affilVal, sheets: sheets.join(", "), purpose: "", consent: "재방문(설문 생략)" });
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
