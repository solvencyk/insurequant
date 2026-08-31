/**
 * insurequant — 다운로드 설문 + 오류 제보 수집기 (Google Apps Script Web App)
 *
 * 배포 (스탠드얼론 — 스프레드시트를 미리 만들 필요 없다. 모바일에서도 이 경로가 짧다):
 *       script.google.com > 새 프로젝트 > 이 코드 붙여넣기 > 저장
 *       > 배포 > 새 배포 > 유형 "웹 앱"
 *       > 실행 계정 "나", 액세스 권한 "모든 사용자"  <-- 익명 방문자가 POST 하려면 필수
 *       > 배포 후 나오는 /exec URL 을 사이트에 배선한다.
 *
 * 응답을 담을 스프레드시트는 첫 제출 때 스크립트가 알아서 만들고 그 id 를 기억한다.
 * 만들어진 파일은 소유자의 구글 드라이브 최상위에 'insurequant_collector' 로 생긴다.
 * 이미 쓰던 시트에 붙이고 싶으면 SHEET_ID 에 그 시트 id 를 직접 넣으면 된다.
 *
 * 스키마 무관 설계 — payload 의 키가 늘거나 바뀌어도 헤더를 자동으로 확장한다.
 * 폼 항목이 확정되기 전에 배포해도 되고, 나중에 항목을 바꿔도 재배포가 필요 없다.
 *
 * payload: { kind: "download" | "report", ...임의 필드 }
 *   download -> 시트에만 기록 (건마다 메일 보내면 스팸이 된다)
 *   report   -> 시트 기록 + owner 에게 메일
 */

var NOTIFY_EMAIL = 'qoclrl960@gmail.com';   // 오류 제보 수신 주소
var MAX_FIELD_LEN = 4000;                   // 한 필드 길이 상한 (본문 폭탄 방지)
var SHEET_ID = '';                          // 비워두면 첫 제출 때 새로 만들어 기억한다
var SHEET_NAME = 'insurequant_collector';

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);                   // 동시 제출 시 행이 겹쳐 쓰이는 것 방지
    var body = JSON.parse(e.postData.contents);

    // 허니팟: 사람 눈에 안 보이는 필드가 채워져 있으면 봇이다. 조용히 성공으로 응답한다.
    if (body._hp) return _ok();

    var kind = (body.kind === 'report') ? 'report' : 'download';
    delete body.kind;
    delete body._hp;

    var row = { received_at: new Date(), ua: (e.parameter && e.parameter.ua) || '' };
    Object.keys(body).forEach(function (k) {
      var v = body[k];
      if (Array.isArray(v)) v = v.join(', ');
      else if (v && typeof v === 'object') v = JSON.stringify(v);
      row[k] = String(v == null ? '' : v).slice(0, MAX_FIELD_LEN);
    });

    _append(kind === 'report' ? 'reports' : 'downloads', row);
    if (kind === 'report') _notify(row);
    return _ok();
  } catch (err) {
    console.error(err);
    return ContentService.createTextOutput(JSON.stringify({ ok: false }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    try { lock.releaseLock(); } catch (e2) {}
  }
}

function doGet() {
  return ContentService.createTextOutput('insurequant collector: alive — ' + _book().getUrl());
}

/**
 * 응답 스프레드시트를 돌려준다. 스탠드얼론 배포여도 동작하도록,
 * 없으면 새로 만들고 그 id 를 스크립트 속성에 기억한다(다음 호출부터 재사용).
 */
function _book() {
  var props = PropertiesService.getScriptProperties();
  var id = SHEET_ID || props.getProperty('SHEET_ID');
  if (id) {
    try { return SpreadsheetApp.openById(id); } catch (e) { /* 지워졌으면 새로 만든다 */ }
  }
  var ss = SpreadsheetApp.create(SHEET_NAME);
  props.setProperty('SHEET_ID', ss.getId());
  return ss;
}

/** 헤더를 자동 확장하며 한 행 추가. 새 키가 오면 열을 만든다. */
function _append(tabName, row) {
  var ss = _book();
  var sh = ss.getSheetByName(tabName) || ss.insertSheet(tabName);
  var lastCol = sh.getLastColumn();
  var header = lastCol > 0 ? sh.getRange(1, 1, 1, lastCol).getValues()[0] : [];

  Object.keys(row).forEach(function (k) {
    if (header.indexOf(k) === -1) header.push(k);
  });
  sh.getRange(1, 1, 1, header.length).setValues([header]);
  sh.setFrozenRows(1);

  var out = header.map(function (k) { return row.hasOwnProperty(k) ? row[k] : ''; });
  sh.appendRow(out);
}

/** 오류 제보를 저장소 inbox 티켓 포맷으로 메일 발송 — 복붙만으로 parser 레인에 넣을 수 있다. */
function _notify(row) {
  var stamp = Utilities.formatDate(new Date(), 'UTC', "yyyyMMdd'T'HHmm'Z'");
  var sheet = row.sheet || row.대상시트 || 'UNKNOWN';
  var company = row.company || row.대상회사 || 'MULTI';
  var period = row.period || row.대상분기 || 'MULTI';

  var lines = [
    '---',
    'from: site_report',
    'to: parser',
    'created: ' + stamp,
    'status: open',
    'route: reparse',
    'company: ' + company,
    'period: ' + period,
    'lane: ifrs17   # kics 면 고칠 것',
    'iter: 1',
    '---',
    '',
    '## 미결 (사이트 오류 제보)',
    ''
  ];
  Object.keys(row).forEach(function (k) {
    if (k === 'received_at' || k === 'ua') return;
    lines.push('- **' + k + '**: ' + row[k]);
  });
  lines.push('', '접수: ' + row.received_at, '', '## 답변 (recipient 작성 — 처리 후)', '');

  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: '[insurequant] 오류 제보 — ' + sheet + ' / ' + company + ' / ' + period,
    body: lines.join('\n')
  });
}

function _ok() {
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
