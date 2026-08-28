// InsureQuant — 다운로드 설문 + 오류 제보 제출 대상.
// 백엔드: scripts/appsscript/insurequant_collector.gs (Google Apps Script Web App).
// action = 그 스크립트를 "웹 앱"으로 배포했을 때 나오는 /exec URL.
// 아직 실제 URL을 안 넣어서 PLACEHOLDER — 이 값을 바꾸기 전까지 제출은 콘솔에 로그만
// 남기고 조용히 실패합니다(방문자에게는 정상 제출된 것처럼 보임 — 다운로드는 그대로 동작).
window.IQ_FORMS = {
  action: "PLACEHOLDER_APPS_SCRIPT_EXEC_URL"
};

window.IQ_FORMS.isConfigured = function () {
  return !!(window.IQ_FORMS.action && !window.IQ_FORMS.action.startsWith("PLACEHOLDER"));
};

// kind: "download" | "report" — insurequant_collector.gs doPost()의 kind 분기와 맞춰야 함.
// download는 시트에만 기록(메일 없음), report는 시트 기록 + owner Gmail 알림.
window.IQ_FORMS.submit = async function (kind, valuesByKey) {
  if (!window.IQ_FORMS.isConfigured()) {
    console.warn("[IQ_FORMS] collector 미설정 — 실제 전송 생략, 값만 로그:", kind, valuesByKey);
    return { ok: false, reason: "not_configured" };
  }
  var payload = Object.assign({ kind: kind, _hp: "" }, valuesByKey);
  try {
    // body를 순수 문자열로 주면 fetch가 Content-Type: text/plain을 붙인다 — Apps Script는
    // application/json에 대해 CORS preflight(OPTIONS)를 처리하지 못해 text/plain이 필수.
    var res = await fetch(window.IQ_FORMS.action, { method: "POST", body: JSON.stringify(payload) });
    return await res.json().catch(function () { return { ok: true }; });
  } catch (e) {
    console.error("[IQ_FORMS] " + kind + " 제출 실패:", e);
    return { ok: false, reason: "network" };
  }
};
