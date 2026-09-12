---
from: owner
to: designer
created: 20260912T0830Z
status: resolved
route: html
company: ALL
period: -
track: analytics
---

## 미결 (owner) — GA4 에서 owner 본인 방문을 제외: 브라우저 플래그 → `traffic_type=internal`

**배경.** 하루 방문 15명 안팎인데 owner 확인 접속이 상당수라 통계가 왜곡된다. IP 기반 내부 트래픽 규칙은 회사망·집·폰으로
IP 가 바뀌어 새므로 쓰지 않는다. 대신 **브라우저에 한 번 표시**해 두면 그 브라우저의 모든 방문이 GA4 내부 트래픽으로
분류되게 한다(GA4 쪽 "Internal Traffic" 데이터 필터를 owner 가 활성화하면 보고서에서 제외됨).

**대상.** gtag 스니펫이 있는 5 페이지 전부: `index.html`, `K-ICS.html`, `IFRS17.html`, `공시보고서.html`, `privacy.html`
(`grep -c G-F8NSCQZBZK` 로 각 3건 확인됨). 인라인 `gtag('config', 'G-F8NSCQZBZK');` 를 아래처럼 바꾼다(5곳 동일):

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  // owner 본인 방문 제외(2026-09-12): ?iq_internal=1 로 한 번 접속하면 이 브라우저는 내부로 기억,
  // ?iq_internal=0 이면 해제. GA4 Admin > Data filters > Internal Traffic 을 Active 로 둬야 실제 제외된다.
  (function(){
    var cfg = {};
    try {
      var q = new URLSearchParams(location.search).get('iq_internal');
      if (q === '1') localStorage.setItem('iq_internal', '1');
      else if (q === '0') localStorage.removeItem('iq_internal');
      if (localStorage.getItem('iq_internal') === '1') cfg.traffic_type = 'internal';
    } catch (e) {}
    gtag('config', 'G-F8NSCQZBZK', cfg);
  })();
</script>
```

**규칙.**
- CSP meta 는 손대지 않는다(새 호스트 없음, 인라인은 기존 `'unsafe-inline'` 으로 실행). gtag `<script async src>` 줄과 그 위 주석 블록은 그대로.
- 5 페이지 외 다른 부분 수정 금지. `jp/index.html` 은 GA 태그 자체가 없으니 대상 아님(다른 designer 에이전트가 지금 그 파일을 고치는 중 — 건드리지 마라).
- `privacy.html` 의 GA 설명 문단에 한 줄 추가: "운영자 본인의 확인 접속은 내부 트래픽으로 분류해 통계에서 제외합니다."
- 검증: 로컬 서버에서 `index.html?iq_internal=1` 접속 후 `localStorage.iq_internal === '1'` 확인, 이어서 파라미터 없이 재접속해
  `dataLayer` 에 push 된 config 인자에 `traffic_type:'internal'` 이 있는지 확인(gtag.js 자체는 이 PC 에서 CDN 차단이라 네트워크
  전송은 못 본다 — dataLayer 검사로 대체). `?iq_internal=0` 으로 해제되는지도. 5 페이지 전부 `tests/test_deploy_assets.py` 통과.
- 서브에이전트 생성 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음. 끝나면 답변란에 5 파일 diff 요약, `status: answered`,
  `TODO_designer.md`·`docs/changelog_designer.md` 갱신. 보고문 한국어 존댓말 5줄 이내.

## 답변 (designer, 2026-09-12)

5 파일 전부 인라인 `gtag('config', 'G-F8NSCQZBZK');` 를 티켓 스니펫(IIFE, `iq_internal` 플래그)
으로 그대로 교체했다. `git diff --stat`:

```
IFRS17.html    | 13 ++++++++++++-
K-ICS.html     | 13 ++++++++++++-
index.html     | 13 ++++++++++++-
privacy.html   | 14 +++++++++++++-
공시보고서.html | 13 ++++++++++++-
5 files changed, 61 insertions(+), 5 deletions(-)
```

5 파일 모두 diff 는 "`gtag('config', 'G-F8NSCQZBZK');` 1줄 삭제 → IIFE 12줄 삽입"으로 동일
(privacy.html 만 GA 문단에 "운영자 본인의 확인 접속은 내부 트래픽으로 분류해 통계에서
제외합니다." 한 줄 추가로 +1). CSP meta·`<script async src>` 줄·그 위 SRI 예외 주석은
전부 무수정. `jp/index.html` 은 손대지 않았다(다른 designer 세션이 동시 작업 중).

**함정 1건**: `index.html` 만 파일 전체가 CRLF 라 최초 LF 기준 치환이 실패했고, 급히 쓴
`sed -i` 우회가 파일 전체를 LF 로 재작성해버렸다. `git diff --stat` 로 즉시 발견해 Python
`io.open(newline='')` 로 CRLF 를 전량 복원, 최종 diff 는 위 표대로 5 파일 모두 정상 범위로
좁혀진 것을 재확인했다. 5 파일 전부 BOM 없음 확인.

**검증**: `python -m http.server 8901` + Claude Browser 로 `index.html` 실측 —
`?iq_internal=1` → `localStorage.iq_internal==='1'`·`dataLayer` config 인자
`{traffic_type:'internal'}` / 파라미터 없는 재접속 → 유지 / `?iq_internal=0` → `localStorage`
null·config 인자 `{}`. `K-ICS.html` 스팟체크 동일 결과. `pytest tests/test_deploy_assets.py`
11 passed. gtag.js 네트워크 전송은 CDN 차단으로 미관측(티켓 지시대로 dataLayer 로 대체).

**잔여**: 커밋만, push 는 owner 승인 후 publishing 소관. GA4 Admin 의 Internal Traffic
필터 Active 전환은 owner 본인 조치.

## 종결 재확인 (orchestrator 2026-09-12)

5 페이지 diff 각 +13줄(privacy +14)로 티켓 스니펫과 일치, CSP·`<script async src>` 무변경, 줄바꿈 형식 보존
(index.html CRLF 1455/1455 등 전 파일 일치). `tests/test_deploy_assets.py` 11 passed. owner 쪽 남은 일 = GA4 Admin
> Data filters > Internal Traffic 을 Testing → Active, 그리고 쓰는 브라우저마다 `?iq_internal=1` 로 1회 접속.

status: **resolved**
