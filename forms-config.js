// InsureQuant — 다운로드 설문 + 오류 제보 제출 대상.
// 백엔드: Google Apps Script Web App (수집기).
// action = 그 스크립트를 "웹 앱"으로 배포했을 때 나오는 /exec URL.
// 아직 실제 URL을 안 넣어서 PLACEHOLDER — 이 값을 바꾸기 전까지 제출은 콘솔에 로그만
// 남기고 조용히 실패합니다(방문자에게는 정상 제출된 것처럼 보임 — 다운로드는 그대로 동작).
window.IQ_FORMS = {
  action: "https://script.google.com/macros/s/AKfycbzbJTCqusPZ-8i0CRuFhYxkbyrrxLyZQiV6DmuTeBK1eXtfTpyQF2F4b5Idjwf20Muw/exec"
};

window.IQ_FORMS.isConfigured = function () {
  return !!(window.IQ_FORMS.action && !window.IQ_FORMS.action.startsWith("PLACEHOLDER"));
};

// kind: "download" | "report" — 수집기 doPost()의 kind 분기와 맞춰야 함.
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

// GA4 사용 이벤트(owner 2026-11-24): 링크 복사·스크린샷·xlsx 다운로드·오류 제보 횟수만 센다. jp 레인과 한 GA4 속성을 공용하므로
// 이벤트 이름·params 를 맞춘다(market:'kr' 고정). params 에는 개인정보·자유서술·회사명·분기·시트 목록 문자열을 넣지 않는다.
// 내부 방문 판정은 여기서 하지 않는다 — 각 페이지 head 의 gtag('config',{traffic_type:'internal'}) 가 표시하고 GA4 데이터 필터가 거른다.
// gtag 가 없으면 아무것도 보내지 않고, 어떤 예외도 호출한 쪽(복사·다운로드·제보) 동작에 닿지 않는다.
window.IQ_FORMS.track = function (name, params) {
  try {
    if (typeof window.gtag !== "function") return;
    window.gtag("event", name, params || {});
  } catch (e) { /* 분석 실패는 사용자 동작에 영향 없음 */ }
};
