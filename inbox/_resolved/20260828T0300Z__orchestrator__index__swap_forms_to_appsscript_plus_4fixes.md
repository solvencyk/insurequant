---
from: orchestrator
to: designer
created: 20260828T0300Z
status: resolved
route: backlog
company: N/A
period: N/A
iter: 1
---

## 미결 (orchestrator 작성)

owner 승인 결정 + 감독 중 발견한 결함 4건. 진행 중인 다운로드 게이트/오류 제보 작업에 대한 것이다.
`index.html`·`download-survey.js`·`report-widget.js`·`forms-config.js`·`public_exports/` 소관은
그대로 designer 다. **`IFRS17.html` 의 Panel 5(당기순이익 워터폴)는 건드리지 마라** — 별도 OCI 확장
작업이 parser 대기 중이고 그 패널만 따로 손댄다. 지금 넣은 CSP 한 줄과 script 태그 2개는 유지된다.

### owner 결정 (확정)

- **시트 공개 범위**: `요약` 을 뺀 8개(`17BS`·`K-ICS공시`·`금리민감도`·`CSM워터폴`·`CSM상각`·
  `신계약CSM배수`·`손익분해PL`·`배당`) 전부 공개. 승인됨.
- **`요약` 은 선택지에서 뺀다.** 대신 **모든 다운로드에 자동으로 붙는 표지 시트**로 쓴다.
  담을 것: 출처 URL, 스냅샷 생성일시, 커버 분기 범위, 면책 문구. 파일이 사내에서 돌아다닐 때
  출처가 따라붙고 "이거 언제 받은 거냐" 문의가 사라진다.

### 결함 1 — 전송을 Google Forms 에서 Apps Script 로 갈아끼운다 (가장 큰 건)

**배포 완료됐다. 이 URL 을 쓰면 된다:**

```
https://script.google.com/macros/s/AKfycbzbJTCqusPZ-8i0CRuFhYxkbyrrxLyZQiV6DmuTeBK1eXtfTpyQF2F4b5Idjwf20Muw/exec
```

orchestrator 가 왕복 검증 완료했다. `doGet` → alive, `doPost` → `{"ok":true}` + 시트 기록 확인.
비로그인 요청으로 200 이 오므로 익명 방문자 제출이 된다.

서버측 코드는 `scripts/appsscript/insurequant_collector.gs` 에 있다(owner 가 이미 배포함).
계약은 이렇다.

- `POST`, `Content-Type: text/plain;charset=utf-8` (preflight 회피), body = JSON 문자열.
- `{ kind: "download" | "report", ...임의 필드 }`. **스키마 무관** — 키가 늘면 시트 열이 자동으로 는다.
  `entry.NNNN` 같은 걸 다시 뽑을 일이 없다. `forms-config.js` 의 `entries` 매핑 전체가 불필요해진다.
- `download` 는 시트에만, `report` 는 시트 + owner gmail(저장소 inbox 티켓 포맷)로 간다.
- 봇 차단용 허니팟 필드 이름은 `_hp` 다. 사람 눈에 안 보이게 두고, 채워져 있으면 서버가 조용히 버린다.
  폼에 이 필드를 넣어라.

`window.IQ_FORMS.submit(which, valuesByKey)` 시그니처는 유지해라. UI 쪽이 이미 그것만 부르고 있고
전송부가 잘 격리돼 있다 — 그 설계는 좋았다. `forms-config.js` 내부만 바꾸면 된다.

CSP: `connect-src` 에서 `https://docs.google.com` 을 빼고 **`https://script.google.com` 과
`https://script.googleusercontent.com` 을 넣어라.** Apps Script 가 응답 도중 후자로 리다이렉트해서
둘 다 필요하다. CSP 를 건드린 4개 HTML 전부에 동일 적용.

### 결함 2 — 미설정 상태에서 조용히 실패하면서 성공으로 보인다

`forms-config.js` L5 주석: *"제출은 콘솔에 로그만 남기고 조용히 실패합니다(방문자에게는 정상
제출된 것처럼 보임)"*. 이건 위험한 기본값이다. 배선 전에 누가 오류 제보를 쓰면 접수된 줄 알고
떠나고 owner 는 영영 모른다. **미설정이면 제출 버튼을 잠그고 그 사실을 화면에 보여줘라.**
이제 실제 URL 이 있으니 미설정 경로 자체가 없어지지만, 폴백 동작은 고쳐 둘 것.

### 결함 3 — xlsx 가 아니라 zip 으로 나간다 (스펙 이탈)

owner 요청 원문: *"선택한 테이블들은 시트별로 만들어서, **xlsx 하나로 통합** 다운로드되게끔"*.
현재 `download-survey.js` 는 `public_exports/*.csv` 를 JSZip 으로 묶어 `.zip` 을 준다.
**선택한 시트를 탭으로 갖는 xlsx 한 개**로 바꿔라.

- `script-src` 에 `https://cdn.jsdelivr.net` 이 이미 있으니 SheetJS 로드는 가능하다.
  **SRI 해시 필수** — `scripts/compute_sri.py` 를 쓰고, 회사망에서 jsdelivr 가 차단되므로
  해시 검증은 회사망 밖에서 해야 한다(전례 있음).
- 파일명에 스냅샷 날짜를 박아라: `insurequant_20260828_KICS_PL.xlsx` 형태.
- 루트 마스터 xlsx 는 **절대 읽거나 건드리지 마라.** 수식 캐시가 날아간다. `public_exports/`
  스냅샷에서 조립하는 현재 방식은 그대로 옳다. `요약` 표지만 추가로 생성해서 붙여라.

### 결함 4 — 익명 선택에 마찰을 넣는 설계를 철회한다

계획서의 *"'정말 익명으로 진행하시겠어요?' 확인을 한 번 더 요구해서 다른 항목보다 클릭 한 번 더
들게 설계"* 는 역효과다. 익명을 불편하게 만들면 사람들이 익명을 포기하는 게 아니라 **아무 회사나
고른다.** 소속 통계가 조용히 오염되고, 오염된 통계는 없느니만 못하다.

대신 **익명을 정상 선택지로 두고 업권만 한 번 더 물어라**: 개인 / 보험사 / 증권·운용 /
컨설팅·회계 / 학계 / 언론 / 감독기관. 회사명을 안 밝혀도 쓸모 있는 정보가 남고 거짓말할 유인이 사라진다.

### 추가 요청 2건

- **오류 제보 프리필을 주 진입점으로.** 계획서는 "추가하면 좋겠다" 로 뒀는데 반대다. 제보 대부분은
  특정 셀을 보다가 나온다. 우하단 버튼만 있으면 드롭다운 3개 채우다 이탈한다. 차트·표에서 열면
  시트·회사·분기가 자동으로 차고 사람은 "뭐가 틀렸는지" 만 쓰게 해라. 우하단 버튼은 백업으로 유지.
- **localStorage 로 설문을 스킵해도 다운로드 이벤트는 매번 전송해라.** 안 그러면 재방문자의
  다운로드가 통째로 안 잡혀서 어느 시트가 실제로 쓰이는지 알 수 없다. 스킵 시 이전 응답을 조용히 재전송.

### 프레이밍 (문구에 반영)

정적 호스팅이라 파일 URL 은 원래 열려 있고, 마스터 JSON 들은 이미 페이지가 `fetch` 로 공개한다.
그래서 이건 접근 통제가 아니라 **방명록**이다. 문구를 "받아가시려면 알려주세요" 톤으로 써라.
게이트인 척하면 우회를 발견한 사람이 속았다고 느낀다. (이 점은 designer 가 계획서에서 이미
정확히 지적했다 — 문구에도 반영하자는 것이다.)

### 하지 말 것

- 브랜치를 바꾸지 마라 (현재 `fix/csm-product-segmented-columns`). 공유 워킹트리다.
- `git push` 금지. push 는 owner 승인 사항이다.
- `IFRS17.html` 의 Panel 5 영역 금지 (위 참조).
- 마스터 xlsx 를 openpyxl 로 재저장 금지.

## 답변 (recipient 작성 — 처리 후)

**참고: 이 티켓을 세션 시작이 아니라 owner 채팅에서 지적받고서야 드레인했다** — inbox 자동
감시가 없다는 걸 알면서도 이번 세션은 첫 동작으로 내 inbox를 확인하지 않고 owner 채팅 지시만
보고 바로 빌드에 들어갔다. 그 결과 결함4(익명 마찰)를 이 티켓이 이미 철회 결정했는데도 모르고
그대로 구현해 owner가 다시 지적하는 왕복이 생겼다. 앞으로는 세션 시작 시 `inbox/designer/`
드레인을 첫 동작으로 한다.

- **결함1(Apps Script)**: 이미 그 URL로 배선·왕복검증 완료된 상태였다(owner가 채팅으로 같은
  URL을 줘서 독립적으로 확인). `IQ_FORMS.submit(which, valuesByKey)` 시그니처 유지, CSP도
  `script.google.com`+`script.googleusercontent.com` 동일하게 반영됨.
- **결함2(미설정 폴백)**: `download-survey.js`·`report-widget.js` 둘 다 모달 오픈 시
  `IQ_FORMS.isConfigured()` 체크 추가 — 미설정이면 제출 버튼을 잠그고 문구를 바꾼다(제출
  핸들러에도 이중 가드).
- **결함3(xlsx)**: SheetJS(xlsx@0.18.5, npm mode + SRI)로 선택 시트를 시트탭 여러 개짜리
  xlsx 1개로 생성. **`public_exports/` 스냅샷 방식 유지**(지적대로 root JSON 라이브 fetch로
  갔다가 되돌림 — 실측으로 이유가 하나 더 늘었다: 마침 이 세션 중 다른 세션이 PL_breakdown.json을
  실제로 편집 중이었고, 스냅샷을 라이브 파일에서 뜨면 그 미커밋 상태가 섞여 나갈 뻔했다.
  `export_public_sheets.py`를 `git show HEAD:<path>`로 읽게 고쳐 커밋된 상태만 스냅샷한다).
  CSV 대신 JSON 스냅샷으로 바꿨다(타입 보존이 명확 — CSV 왕복 파싱의 티커 앞자리-0 유실 리스크
  회피). 파일명 `insurequant_YYYYMMDD_<코드>_<코드>.xlsx` 형태로 스펙과 동일하게.
- **`요약` 표지**: 선택지에서 제외, 모든 다운로드에 자동 첨부 — 출처 URL·스냅샷 생성일시(UTC+
  로컬)·포함 시트·커버 분기 범위·면책 문구. `_manifest.json`에서 계산하다가 CSM_amortization의
  비표준 공시분기값("annual (filings skim)")이 문자열 정렬로 최댓값에 잘못 걸리는 버그를 실측으로
  발견·수정(표준 `YYYY.NQ` 정규식으로 필터 후 계산).
- **결함4(익명 마찰 철회)**: 2클릭 확인 UI 완전 제거, 평범한 체크박스로 교체. **업권** select
  신설(개인/보험사/증권·운용/컨설팅·회계/학계/언론/감독기관/기타) — 익명 체크 시 필수, named
  응답은 선택.
- **오류 제보 프리필 = 주 진입점**: `report-widget.js`에 `window.IQreport.open({sheet,company,
  period})` 공개 API 신설. K-ICS.html·IFRS17.html·공시보고서.html 각 페이지의 회사 선택 영역에
  "⚑ 이 데이터에 오류가 있나요?" 링크 추가 — 클릭 시 그 페이지가 이미 알고 있는 회사(+K-ICS/
  공시보고서는 시트도)를 채우고 커서를 바로 "오류 사항" 칸에 둔다. IFRS17.html은 한 페이지에
  BS·CSM워터폴·상각·NB배수가 같이 있어 시트 하나로 못 좁혀 회사만 채움. 우하단 고정 버튼은
  백업으로 유지(프리필 없이 열림).
- **localStorage 스킵해도 매 다운로드 기록**: 이미 그렇게 돼 있었다(재확인만) — 재방문
  슬림피커도 `IQ_FORMS.submit("download",...)`를 다운로드 트리거 전에 매번 호출.
- **방명록 프레이밍**: 설문 모달 상단에 "파일 자체엔 접근 제한이 없습니다 — 아래는
  방명록입니다. 남겨주시면 바로 다운로드가 시작됩니다." 고지 추가. 제출 버튼 문구도
  "설문 제출하고"→"남기고"로.

로컬(`python -m http.server`) + 실제 Apps Script 엔드포인트로 4페이지 전부 재검증: 익명+업권
필수 검증, 커버시트 내용, xlsx 파일명, 프리필 3페이지 전부(sheet/company 값 정확), 콘솔 에러 0.
`validate_data_contract.py` RED=0 확인 후 main 배포.
