# Insurequant Designer TODO (Stage 5)

> Last updated: 2026-08-28 · Stage 5/5 — designer
> Prompt: docs/agents/claude-agent-designer.md (§5 design system formalized 2026-06-16) · Changelog: docs/changelog_designer.md

Session start: read this file + `claude-agent-designer.md` + the page(s) in scope (root HTML files). Publishing ([`TODO_publishing.md`](TODO_publishing.md)) owns master JSONs; designer only reads them and decides how they render. English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

Stage 5 = HTML structure / styling / responsive breakpoints / A11y / chart layout. Desktop pages are in production; KEYCOLOR-V1 K-ICS cancelled by owner (IFRS17 구현 불만족). Mobile scope confirmed; M1 foundation done; full mobile pass open.

**Recent (2026-08-28j):** owner 재지적 — K-ICS 히트맵 호버 시 회사명이 abbr 안 됨. 원인: 트리맵
칸의 시각 라벨(`name.textContent`)엔 `shortName()`이 있었는데 같은 칸의 `.title`(호버 툴팁)은
원수사명 그대로였던 누락. 같은 페이지에서 CSM 버블맵도 동일 패턴(ECharts tooltip formatter +
모바일 리스트)이라 같이 수정 — 트리맵 4곳 + 버블맵 2곳, 총 6곳. 배포 완료.

**Recent (2026-08-28i, [긴급] owner):** "원보험사코드가 코리안리 내부 코드라 공개하면 안 된다"
— `export_public_sheets.py`가 스냅샷 생성 시 그 컬럼을 드롭하도록 수정, 8개 시트 전부
재생성해 이미 배포됐던 값을 덮어씀(main 배포 완료, 라이브 curl로 8개 시트 전부 컬럼 목록에서
빠진 것 확인). **루트 마스터 JSON은 안 건드림** — 대시보드 4페이지가 그 필드를 회사 선택
조회 키로 쓰고 있어 거기서 빼면 사이트 기능이 깨진다(다운로드 스냅샷 레이어에서만 제외).

**Recent (2026-08-28h):** 모바일 탭바 "공시/보고서" 잘림 → "기타공시"로 4페이지 전부 교체(제목/
og:title/브랜드 힌트는 안 건드림, 탭 라벨만). **IFRS17.html은 같은 파일에 다른 세션의 미커밋
Panel 5(OCI 확장) 작업이 섞여 있어 `git apply --cached`로 이 1줄 hunk만 스테이징**, 워킹트리의
나머지 12-hunk는 그대로 둠 — 커밋 직후 그 세션이 자기 몫을 `eec64e0`으로 정상 커밋(내 커밋
위에 깨끗하게 얹힘, 데이터 유실 없음). main에는 탭 라벨 4개만 배포, Panel 5 확장은 그쪽 소관이라
안 건드림(배포 여부는 그 세션/owner 결정).

**Recent (2026-08-28g):** 부서 옵션 "결산(Valuation)"→"계리(Valuation)"로 정정(계리=Valuation이
맞는 대응, 결산은 회계 마감이라 다른 개념 — owner 지적), 중복이던 별도 "계리" 항목 제거. 배포 완료.

**Recent (2026-08-28f):** disclaimer 문구 끝에 "오류 발견 시 화면의 우측 하단 버튼을 통해
제보 부탁드립니다." 추가(`DISCLAIMER_TEXT` 단일 소스라 설문 모달·xlsx 표지 시트 둘 다 자동
반영). 배포 완료.

**Recent (2026-08-28e, owner 피드백 — 완료·배포됨):** owner가 "json은 계리사가 다룰줄 아냐"고
지적 — 실제로는 다운로드 산출물이 처음부터 xlsx만이었고(public_exports/*.json은 서버 내부
스냅샷일 뿐 사용자 노출 없음), 내가 "JSON 스냅샷"이라고 계속 언급한 설명 방식이 오해를 만든
것으로 판단. 코드 변경은 불필요, 문구만 명확히: 버튼·모달 타이틀 "마스터 데이터 다운로드"→
"테이블 다운로드(.xlsx)"로 xlsx임을 명시. 그 외 2건도 반영: 모바일에서 버튼이 풀폭으로 크게
보이던 것 → 탭과 같은 줄 유지, 탭 바로 옆 pill(11px·999px 라운드)로(데스크탑은 그대로).
소속 밑에 **부서** select 신설(결산(Valuation)/RM/기획/상품개발/계리/자산운용/언더라이팅/
재무회계/기타, 선택). 라이브 재검증 중 이 Browser 세션 자체의 브라우저 캐시(GH Pages
`Cache-Control: max-age=600`)로 새 탭에서도 구버전이 잠깐 보이는 현상 확인 — `fetch(...,
{cache:'no-store'})`로 origin이 이미 최신임을 확인, 실사용자는 캐시가 없어 문제 없음(10분 내
자연 해소, 배포 실패 아님).

**Recent (2026-08-28d, inbox 20260828T0300Z 반영 — 완료·배포됨):** owner가 "너 inbox 다
drain한거 맞아?"로 지적 — 정곡. `inbox/designer/20260828T0300Z`(orchestrator, owner 결정
포함)를 세션 시작 때 안 읽고 채팅 지시만으로 바로 빌드 시작했음(이번 세션 전체의 근본 원인).
결과: 결함4(익명 2클릭 마찰)를 그 티켓이 이미 철회 결정했는데 모르고 그대로 구현 → owner가
채팅에서 다시 지적하는 왕복 발생. **교훈: 세션 첫 동작 = `inbox/<내 stage>/` 드레인, owner
채팅 지시가 있어도 생략하지 않는다.**
- 티켓 반영: 익명 마찰 철회(체크박스로, 확인단계 없음) + 업권 select 신설(익명 시 필수).
  다운로드마다 "요약" 표지 자동 첨부(출처·스냅샷일시·분기범위·면책, 파일명도
  `insurequant_YYYYMMDD_<코드>_<코드>.xlsx`). xlsx 조립을 root JSON 라이브 fetch에서
  `public_exports/` 스냅샷(JSON, `git show HEAD:`로 커밋된 상태만 — 공유 워킹트리에서 다른
  세션의 미커밋 PL_breakdown 확장이 섞여 나갈 뻔한 걸 실측으로 확인)으로 되돌림. 오류 제보
  프리필을 주 진입점으로(3페이지에 "이 데이터에 오류가 있나요?" 링크, `window.IQreport.open`
  공개 API 신설, 우하단 버튼은 백업).
- 부수 버그 2건 실측 발견·수정: ① 분기범위 계산이 CSM_amortization의 비표준 라벨("annual
  (filings skim)")을 문자열정렬로 최댓값 오판 ② **`public_exports/_manifest.json`이 라이브에서
  404** — 이 저장소 main에 `.nojekyll`이 없어 GitHub Pages 기본 Jekyll이 밑줄 시작 파일을
  조용히 배포 제외. `manifest.json`으로 개명 + 재발방지로 `.nojekyll` 추가(사이트가 Jekyll
  기능 전혀 안 써서 안전).
- inbox 답변 작성 + `_resolved/`로 이동, main 배포 완료(로컬+라이브 둘 다 재검증).

**Recent (2026-08-28d, inbox 20260828T0500Z — Panel 5를 총포괄손익까지 연장, 완료·미배포):**
- `IFRS17.html` Panel 5 워터폴을 `당기순이익`에서 끊지 않고 **총포괄손익(항목 31)까지** 잇도록 확장.
  스텝 `… 법인세 → [당기순이익(anchor)] → 26 → 27 → 28 → 30 → (잔차) → 29 → [31(end)]`. 항목 25는
  26~30과 중복이라 막대로 안 그린다. **29(FVOCI 지분증권)를 맨 끝에 둔 것이 Y축 설계의 전제** —
  삼성생명은 순이익 1.70조인데 지분증권 평가손익이 +25.32조(2026.2Q 반기누계 +78.70조)라, 29·31만
  잘리게 하고 앞 열넷을 정상 스케일로 남기려면 순서가 그래야 한다.
- **Y축은 29·31을 뺀 range로 고정**(Panel 2 `wfYMin/wfYMax` 방식), 넘치는 막대만 `params.coordSys`로
  캔버스 끝에서 클램프해 톱니 마감 + 안쪽 값 라벨(`+25.32조 ↑`). **axis break는 안 씀**(누적 브리지에서
  압축하면 뒤 막대 위치가 전부 왜곡). 1/2/2.5/5 눈금 스냅으로 경계 눈금 겹침 제거.
- **초기 창** = `el.clientWidth ÷ 56px`, 단 오른쪽 끝은 당기순이익 인덱스 이상 강제. dataZoom 슬라이더를
  데스크톱에도 노출, `grid.bottom` 38→58(두 줄 라벨과 슬라이더 충돌 수정). 리사이즈는 `.resize()`만 하므로
  창 계산은 렌더당 1회 = 밀어둔 위치 유지.
- **결측 3유형** = `plOciMode()` full/total/none. 전 분기 결측 12사 → OCI 구간 통째 생략 + 캡션에
  "총포괄손익 미공시" / 2023.1Q·2Q → 같은 경로 자동 / 세부만 결측 → 총액 1막대(`기타포괄손익(세부 미공시)`),
  일부만 없으면 그 항목만 회색 "미공시" 막대. 표는 창 제한 없이 OCI 행 전부 노출.
- **⚠ 스펙 밖 판단 2건 (orchestrator 확인 대기, 티켓 `## 답변`에 근거 기록):** ① 티켓의 "25=26~30 합"
  전제가 근사라 ABL생명 58%·코리안리 63%가 세부에 안 잡힘 → 브리지가 31에 도달 못 함. `25−Σ(26..30)`이
  총액 1% 이상일 때만 `기타 포괄손익(미분류)` 잔차 막대 추가. ② **`ix.plx` 빌더의 `Number(null)→0` 버그
  수정** — 미공시 셀 `값` 1,347·`값_당분기` 2,377개가 진짜 0으로 둔갑하고 있었음(진짜 0도 836개 존재).
  안 고치면 이 티켓의 결측 요구가 구현 불가. **화면 변화**: 표 미공시칸 `0`→`—`, 분기모드에서 연1회
  공시사 12사가 가짜 0 브리지 대신 기존 stub으로. YTD 폴백 여부는 owner 판단 대기.
- **안 고침(스코프 밖, 별도 티켓 요청):** 같은 `Number(null)→0`이 **Panel 1/2 `ix.wfx`·Panel 1 BS `ix.eqx`**
  에도 있다. Panel 2의 `missing` 회색 시리즈를 무력화하고 있을 가능성 높음. 고치면 CSM 워터폴·BS T자
  숫자가 바뀌므로 별도 검증 필요.
- 실측: (a) 삼성생명 2025.4Q 1440px 클리핑·라벨·나머지 정상스케일 / (b) 결측 3유형 각각(AIG·라이나 /
  메리츠 2023.2Q / 삼성화재 2025.3Q·ABL생명) / (c) 760px·375px 창이 당기순이익에서 끊기고 슬라이더 노출 /
  (d) 1440px 17막대 한 번에. 전 39사×2모드 순회 **JS 에러 0**, `pytest tests/test_deploy_assets.py` 10/10.
  **배포·push 안 함.** 상세: [changelog_designer.md](docs/changelog_designer.md) 2026-08-28d.
- 검증 팁(재사용): UI가 최신 분기만 고르므로 과거 분기는 `PL_breakdown.json`을 그 분기까지 잘라 서빙하는
  로컬 서버로 확인. Browser pane 미compositing으로 `screenshot`이 또 실패 → ECharts `getDataURL()`을
  같은 오리진(`connect-src 'self'`)으로 POST해 PNG로 떨구는 방식으로 실렌더 이미지 확보.

**Recent (2026-08-28c, owner 피드백 3건 — 완료·배포됨):** 위 2026-08-28b 배포 직후 owner 피드백:
① 다운로드 버튼이 footer라 안 보임 → header 우측(탭과 같은 높이)으로 이동, primary 파란색.
② "csv 여러개 zip 말고 xlsx로 만들라고 했잖아" → JSZip+CSV 폐기, SheetJS로 선택 시트를 시트 탭
여러 개짜리 xlsx 1개로 직접 생성(마스터 JSON 그대로 fetch, `build_master_xlsx.py`의
NUMERIC_COLS와 동일 컬럼만 숫자 coerce). `public_exports/*.csv`·`export_public_sheets.py` 삭제.
③ "AIA생명 검색해도 안 나와" → download-survey.js 소속 datalist·report-widget.js 오류대상회사
체크박스 둘 다 NAME_ABBR 명시매핑이 빠져 원수사명 그대로 노출되던 버그(대시보드 페이지들과
다른 코드경로라 그 매핑을 안 물려받았음) — 매핑 추가 + 회사 체크박스에 검색창 신설.
로컬+라이브 둘 다 실측 재확인(버튼 높이 픽셀단위 일치, xlsx를 SheetJS로 역파싱해 시트/타입
검증, "AIA" 검색 결과 1건). main 배포 완료(`caf0691`).

**Recent (2026-08-28b, 채팅 발주 — 마스터 다운로드 설문게이트 + 오류제보 팝업, 완료·배포됨):**
- **완결.** owner가 `insurequant_collector.gs` 배포 `/exec` URL 제공 → `forms-config.js` 배선 →
  브라우저로 download/report 두 kind 다 실제 엔드포인트에 POST해 `{ok:true}` + 실제 테스트 메일
  1통 수신 확인 → **CSP가 `script.google.com`만 허용하고 `script.googleusercontent.com`(Apps
  Script가 실행을 리다이렉트하는 실제 도메인)을 안 허용해서 막혔던 것 발견·수정**(콘솔 CSP
  violation으로 실측) → main 배포(`c9e707d`) → 라이브(www.insurequant.com)에서도 실제 POST
  재확인, `{ok:true}` + 콘솔 에러 0. 상세: [changelog_designer.md](docs/changelog_designer.md#2026-08-28b).
- owner: index.html에 마스터 xlsx 다운로드 버튼 신설, 짧은 설문(소속/데이터목록/목적/disclaimer) 제출해야 다운로드. 4페이지 공통 우하단 "오류 제보" 팝업(시트/회사/분기 중복선택+자유서술)도 owner Gmail로 도착하게.
- **GitHub Pages는 서버 없는 정적 호스팅이라 게이트는 실접근제어가 아니라 매너 절차** — public_exports/*.csv는 URL 아는 사람 누구나 접근 가능, owner에게 명시적으로 알림.
- 빌드: `scripts/export_public_sheets.py`(마스터 JSON 8개 → `public_exports/*.csv`, 마스터 xlsx는 안 건드림 — 수식캐시 리스크 회피) · `common.css`에 모달 디자인시스템 추가 · `download-survey.js`(index.html 전용 — 소속 datalist 타이핑검색+"기타(익명)" 2클릭 마찰 설계, 시트 체크박스 전체선택버튼 없음, JSZip으로 복수시트 zip 다운로드, localStorage로 재방문자는 슬림 피커) · `report-widget.js`(4페이지 공통 플로팅 버튼, 페이지별 `data-sheet-hint`로 시트 사전선택) · JSZip 3.10.1 CDN(npm mode, SRI, `compute_sri.py`에 등재).
- **중간에 발견**: 처음엔 Google Form proxy-POST로 설계했는데, 같은 공유 워킹트리에서 **다른 세션이 동시에** `scripts/appsscript/insurequant_collector.gs`(Apps Script Web App, 스키마무관 단일엔드포인트, kind로 download/report 분기, report만 owner Gmail+저장소 inbox 티켓 포맷 자동변환, 락 처리)를 만들어놓은 걸 발견 — owner 확인 후 그쪽으로 갈아탐(`forms-config.js`를 Form 2개 방식에서 단일 `/exec` URL 방식으로 재작성, payload 키를 그 스크립트의 `_notify()`가 찾는 `sheet/company/period` 이름에 맞춤, CSP `connect-src`도 `docs.google.com`→`script.google.com`).
- 로컬 브라우저 실측(JS 직접 호출 — read_page/find 도구가 이 페이지의 동적 삽입 버튼을 못 찾는 이슈 있어 `javascript_tool`로 우회): 4페이지 오류제보 위젯 전부 정상, index.html 다운로드 설문 최초/재방문 양쪽 플로우+JSZip 번들링+localStorage 게이트 전부 실동작 확인, 모바일 375px 레이아웃 확인, 콘솔 에러 0. **주의**: 이 세션에서 로컬 static 서버 브라우저 미리보기가 여러 번 "denied/failed"·CSS 캐시 stale로 헤맴 — `preview_start`를 `url` 파라미터로(아닌 `name`으로) 부르면 우회됨, CSS 확인은 `fetch(...,{cache:'no-store'})`로.
- **블로킹**: `insurequant_collector.gs`의 실제 배포 `/exec` URL 대기 중 — `forms-config.js`의 `action`이 아직 PLACEHOLDER라 제출은 콘솔 로그만 남고(다운로드 자체는 정상 동작) 실제 전송이 안 됨. URL 받으면 그 한 줄만 바꾸고 로컬 재확인 후 owner GO 받아 main 배포.
- 아직 git commit 전(로컬만) — 공유 워킹트리에 다른 세션 미커밋 파일(OCI PL_breakdown 확장 관련, `inbox/parser/20260828T0113Z...`) 섞여있어 내 파일만 명시적으로 골라 커밋 예정.

**Recent (2026-08-28, 채팅 발주 — 회사명 표시 정리 4페이지 확장 + main 배포):**
- owner: "영어 회사명들을 한글로 쓰다보니까 지저분해 보인다(에이아이에이생명·에이비엘생명 등), 원천데이터는 안 건드리고 표시만 정리해라. 뭘 어떻게 바꿀지 먼저 말해봐라." → 조사 후 표로 보고, owner가 "BNP카디프생명으로 모든 html에 적용 & push까지" 승인.
- 진단: `index.html`에만 `NAME_ABBR`+`shortName()` 축약 로직이 있고([index.html:540](index.html)) `K-ICS.html`은 AIA 1개사만 부분 적용(`COMPANY_DISPLAY`), `IFRS17.html`·`공시보고서.html`은 전무 — 드롭다운이 원수사명 그대로 노출. `kics_disclosure.json`/`CSM_waterfall.json`/`kics_tier1_utilization.json` 등에서 전사 39개사 원수사명을 직접 뽑아 대조.
- 4개 파일 전체에 동일 `NAME_ABBR`(17개 명시 매핑 + 접미사 정규식 fallback) 이식. `K-ICS.html`은 JS 폴백뿐 아니라 **정적 `<option>` 마크업 28개**(L90-119)도 손으로 텍스트만 교체(`value`는 원수사명 유지). BNP파리바카디프생명보험은 'BNP카디프생명'으로 확정.
- **함정 회피**: `IFRS17.html`의 `coName`은 `keyColorOf(coName)`(브랜드 컬러맵, 원수사명 키)·`PAA_ONLY.has(coName)`(신한이지손해보험 예외 Set) 두 곳의 조회 키로도 쓰여서, `coName` 자체를 줄이면 안 됨 — 드롭다운/차트 타이틀 등 **순수 표시 3곳만** `shortName(coName)`으로 감싸고 로직에 쓰이는 `coName` 원본은 그대로 둠.
- 브라우저 실측(로컬 `python -m http.server` + 라이브 둘 다): 4페이지 드롭다운 전부 짧은 표시명, `value`/코드 조회 정상(AIA·ABL 선택 시 데이터 정상 렌더), 콘솔 에러 0.
- 격리 워크트리(`../insurequant-main-deploy`)로 main cherry-push, `validate_data_contract.py` RED=0 확인 후 owner 승인 하에 `git push origin main`(72ab093). 라이브 캐시버스트 재확인 완료.
- (참고, 안 건드림) `KR0097 하나생명`이 데이터소스마다 "하나생명"/"하나생명보험" 두 철자로 갈려 드롭다운에 중복 표시됨 — 이번 표시명 정리와 무관한 기존 데이터 이슈, 스코프 밖이라 기록만.

**Recent (2026-08-20, inbox 처리 — 준비금/AOCI 표기 오독 수정):**
- `inbox/designer/20260819T0620Z`(owner, 악사손해보험 실사례) + `20260820T0033Z`(orchestrator 전체 상태 점검, 같은 건 재확인 + amort-schedule 경고문구 유지 지시) 2건 드레인. 이익잉여금(항목31) 앵커가 없는 회사에서 법정준비금 3~4항목이 시계열 표의 자본 세부 끝에 평행 배치되는데, 그 섹션에 AOCI 하나만 남아있으면 화면상 "AOCI의 하위 항목"처럼 오독됨(분류가 틀린 게 아니라 배치가 오해를 부름). T자 패널(L1090)엔 이미 있던 구분 라벨("법정준비금 — 이익잉여금 내부 적립, 자본총계 합계에는 미포함")을 표의 폴백 경로에도 `colspan` 전체폭 구분행으로 추가, 준비금이 없는 회사는 이 행 자체가 안 붙게 가드. 브라우저 실측(악사손해보험/KR0049): AOCI → 구분행 → 준비금 항목들 순으로 정상 분리 확인, 앵커 있는 회사(삼성화재)는 회귀 없음(기존처럼 이익잉여금 하위로만). `IFRS17_BS.json`은 parser가 재빌드 중이라던 경고대로 읽기만 함.
- amort-schedule 경고 문구(TODO L16 아래)는 지시대로 미변경 — parser 답변 대기.

**Recent (2026-08-19, owner 채팅 — CSM 상각 스케줄 단위 어긋남):**
- owner가 라이브에서 AIA생명을 보다 지적: "CSM상각스케줄 y축은 억원인데 커서 대면 나오는 숫자(1년차 88,446)는 백만원 단위인 것 같다, 위 CSM 워터폴이랑 단위가 완전 다르다." → 실제로 `IFRS17.html` amort 차트에 **tooltip 콜백이 아예 없어** Chart.js 기본 툴팁이 원시 백만원 값을 그대로 뿌리고 있었음(축·타이틀만 억/조로 환산). 같은 페이지 CSM 워터폴은 억원이라 패널 간 단위도 어긋남.
- 부수 발견: `amDiv`의 조원 임계가 `amMax>=100000 ? 100000` — data가 백만원이므로 1조=1,000,000백만원인데 100,000으로 나눠 **10배 과대**. 삼성화재가 실제로 이 분기를 타서 10.6조로 표시되던 중(정답 1.06조).
- 수정: 조 divisor 100000→1000000, tooltip 콜백 추가(기존 `fmtEok()` 재사용 → 워터폴과 같은 **억원**·음수 △). 브라우저 실측: AIA 축 "900억"/툴팁 "884억원" 일치, 삼성화재 축 "1.2조"/툴팁 "10,586억원" 일치, 교보 "60억원", 콘솔 에러 0.
- **표시층만 고친 것 — 데이터는 여전히 틀림.** `csm_amort_schedule.json`이 단위 정규화 없이 원표 값을 담고 있어(교보=억원·라이나/IBK연금=천원·나머지 백만원) 화면 숫자가 회사별로 100~1,000배 어긋난다. parser inbox 발주: `20260819T0058Z__owner__MULTI_2025.4Q__amort_schedule_unit_not_normalized.md`. 그 티켓이 닫히기 전엔 이 패널 숫자를 신뢰하지 말 것.

**Recent (2026-08-19, 채팅 발주 — IFRS17.html BS 원천 테이블 시계열 신설):**
- owner: "상단 BS부분 만든건 좋은데, 그 밑에 원천 테이블도 시계열로 넣어놓자." T자(Panel 1, 최신 1개 분기 스냅샷) 바로 밑에 다분기 표를 신설 — 기준 셀렉터(`#wfPeriod`)를 그대로 따라감: 분기=직전5분기(`selectPeriods` 재사용, CSM Panel 2와 완전히 동일한 윈도잉 함수 — 하드코딩 없이 데이터에서 도출), 연도=최신+직전3개년말(4Q). 분기 미제공사는 CSM 패널과 동일한 문구("분기 공시 미제공...연도로 바꾸면...")로 처리 — 신규 문구 발명 안 함.
- 행 구조는 owner 목업 그대로: 자산[+]/부채[+]/자본[+] 총계 행(각자 토글로 세부 펼침) → 자본 세부 중 "이익잉여금"은 **자체 중첩 토글**로 법정준비금(섹션="준비금") 항목을 한 겹 더 하위에(D-4 T자와 달리 이번엔 항상 노출이 아니라 접혀 있다가 별도 클릭으로 펼침 — owner가 목업에 `[+]`를 명시적으로 그려서 그대로 반영). 항목 존재 여부는 회사·분기마다 다를 수 있어 선택된 기간 전체에 걸친 **항목명 유니온**으로 행을 잡음(`eqUnionNames` 신설) — 항목번호 하드코딩 없음.
- **부수 발견(브라우저 실측 중)**: `IFRS17_BS.json`에 준비금 4번째 항목(`보증준비금 기적립액`, 항목번호8)이 이 세션 사이에 파서 쪽에서 새로 추가돼 있었음(오전 D-4 작업 때는 3개뿐이었음) — 생보 16개사에만 존재(비상장 포함, 손보는 0사, 업권 특성상 정상: 보증준비금은 변액/연금 보증형 상품 개념). owner 목업의 "보증준비금 적립액"과 실제 항목명("보증준비금 기적립액")이 살짝 다른데, 항목명을 하드코딩하지 않고 데이터 그대로 표시하는 설계라 자동으로 올바른 이름이 뜬다.
- 접기/펼치기 상태 관리: 상위 토글(자본)을 접으면 하위 중첩 토글(이익잉여금→준비금)도 재귀적으로 같이 접고 버튼 상태를 리셋(`collapseGroup` — 안 그러면 다시 펼쳤을 때 하위가 이미 펼쳐진 채로 나오는 혼란). 브라우저 실측으로 왕복 확인(펼침→중첩펼침→상위접기→하위도같이접힘+버튼 "+"로 리셋).
- 캡션에 표시 기간 범위 + 모드 + 단위, 아래에 owner 요청 각주 "* 법정준비금은 당분기 기적립액 + 적립(환입)예정금액 기준" 고정 표시.
- **브라우저 실측**: 삼성화재(KR0008, 손보) 연도모드 헤더 `[2023,2024,2025,2026.2Q]` 정확 일치(owner 예시와 동일), 준비금 3항목(보증준비금 없음 — 손보라 정상). 삼성생명(KR0069, 생보) 준비금 4항목 전부 표시. 분기모드 헤더 `[2025.2Q,2025.3Q,2025.4Q,2026.1Q,2026.2Q]` owner 예시와 정확 일치. AIG손보(KR0029, 분기 BS 미제공)에서 분기모드 stub 메시지 정상, 연도모드 전환 시 정상 표로 복귀. 카카오페이(KR1098, BS 데이터 전무)에서 T자 자체 stub만 뜨고 신규 표는 조용히 비어있음(중복 메시지 없음). 375px에서 `.table-wrap{overflow:auto}`가 6열 표를 컨테이너 안에 가둬 페이지 가로 스크롤 없음 확인. 콘솔 에러 0 전 케이스. `pytest tests/test_deploy_assets.py` 10/10.
- (참고, 안 건드림) `EQ_SECTION_LEVEL_BRIDGE`(항목 1-7 임시 매핑)가 실 섹션/레벨 컬럼이 전 행에 채워진 지금은 사실상 죽은 코드로 보임(폴백 분기가 한 번도 안 걸림) — owner가 스코프 준 적 없어 이번엔 안 건드리고 기록만.

**Recent (2026-08-18d, 같은 대화 연속 — legend 토글 재스케일 복원):**
- owner가 바로 이어서: "왼쪽부분이 또 너무 휑하게 비는데? 원래는 연1회 공시사들 체크 해제하면 x축 왼쪽이 자동으로 rescaling되면서 버블끼리 덜 겹치는게 됐는데 지금은 그 기능이 날아갔어." — 원인: `xAxis.min/max`를 `setOption(...,true)`(notMerge)로 명시 고정한 순간, ECharts의 "범례에서 끈 시리즈는 축 auto-range 계산에서 제외"하던 기본 동작이 죽었다(고정값이 항상 이김). 실측(정확한 재현법 `dispatchAction({type:'legendToggleSelect',...})` — 처음 `legendUnSelect`/`legendSelect`로 테스트했을 땐 거의 변화가 없어 오진할 뻔했는데, 실제 클릭과 동일한 `legendToggleSelect`로 재현하니 "추정" 끄면 [4.05,27219.9]→[443.5,27219.9]로 확 바뀜 — 최솟값 6개(비엔피파리바카디프·교보라이프플래닛·카카오페이·처브라이프·악사·AIG, 전부 est:true)가 실제로 X축 왼쪽을 끌어내리고 있었다는 게 데이터로 확인됨).
- `renderBubble()`에 `legendselectchanged` 리스너 추가 — 토글마다 `rows`를 현재 범례 선택 상태로 다시 필터링해 min/max 재계산 후 `setOption({xAxis:{min,max}})`(merge, notMerge 아님)로 축만 갱신. 클릭 핸들러와 동일하게 `off()`+`on()`으로 재등록(중복 리스너 방지).
- 브라우저 실측: "추정" 토글 [4.05,27219.9]↔[443.5,27219.9] 정상 왕복, "생명보험" 토글 [4.05,27219.9]↔[4.05,19689.9](삼성생명 최댓값 제외되며 반응)도 확인. 콘솔 에러 0, `pytest tests/test_deploy_assets.py` 10/10.

**Recent (2026-08-18c, 채팅 피드백 — 버블 X축 log 범위 고정 제거):**
- owner 채팅: "버블끼리 다닥다닥 붙어있다, x축 범위를 log(10조)로 fix하지 말고 그때그때 바뀌게" — 코드엔 `xAxis.max` 하드코딩이 없었지만(직접 확인), ECharts 로그축 auto-range가 실데이터 최댓값을 **다음 10의 거듭제곱으로 반올림**해버려(실측: 데이터 최댓값 1.72조인데 축은 10조까지) 결과적으로 같은 증상(버블이 왼쪽에 몰리고 오른쪽 절반 이상이 빈 채로 남음).
- `renderBubble()`에서 매 렌더마다 현재 필터된 `rows`(업권 필터 반영)의 실제 min/max에 로그 패딩(×10^0.2≈1.58, 양옆 대칭)만 줘서 `xAxis.min`/`max`로 명시 — 하드코딩 없이 데이터 바뀔 때마다 자동 재계산. 브라우저 실측: 전체 [1, 100000] → [4.05, 27219.9](로그 스팬 5.0→3.83), 손해보험만 필터하면 [6.37, 19689.9]로 더 좁혀짐(정상 동작). 콘솔 에러 0, `pytest tests/test_deploy_assets.py` 10/10.
- 이 세션은 owner와 직접 채팅 중 나온 요청이라 inbox 티켓 생성 없이 바로 처리(비동기 핸드오프가 필요한 상황이 아님).

**Recent (2026-08-18b, D-2 follow-up — bubble X축 실제로 2026.2Q로 이동):**
- owner가 D-2 캡션 수정을 라이브에서 재확인하고 지적(`inbox/_resolved/20260818T0210Z__owner__MULTI__bubble_x_axis_to_2026q2.md`): D-2는 **표기만** 정직하게 고쳤을 뿐, index.html 버블맵 X축(신계약 CSM)이 여전히 `NB_CSM_multiple.json`(배수와 묶여 2026.1Q 고정)에서 나와 **기준 자체**는 안 옮겨져 있었음. owner 요구는 X축을 진짜 2026.2Q로 옮기라는 것.
- `buildBubbleData()`를 재작성 — X(신계약CSM)와 Y(배수)를 완전히 분리된 소스로: **X는 `wfNbItem`(CSM_waterfall 항목2)에서 "회사별 최신"**(크기/`closing`과 동일 패턴, 고정 리터럴 없음 — 전사 최신(`xGlobalMaxK`)과 다른 회사만 자기 최근 마감연도 값을 대신 쓰는 "추정"), **Y는 기존 그대로 `NB_CSM_multiple.json`에서 `NB_TARGET_Q`(2026.1Q) 고정**(KIDI 월납초회 재수집 보류, 변경 없음). owner 실측대로 23사 전부 유지(0사 탈락).
- **⚠ 스케일 함정 수정**: 연1회 공시사 추정값이 전엔 "연간누계 ÷4"(1분기 스케일 가정)였는데, X 기준이 반기누계(2026.2Q)로 바뀌었으니 ÷2가 맞다(owner 계산) — 안 고치면 추정사 버블만 절반으로 찌그러짐. 실측(AIG손보): raw 986.8 → 493.4(정확히 ÷2).
- 캡션(`.section-desc`)·`metaEl`·툴팁을 X/Y 분리 표기로 재작성("X축(신계약CSM)=회사별 최신 · Y축(배수)=2026.1Q 고정 · 크기=회사별 최신"). 툴팁도 X/Y 각 줄이 자기 분기를 직접 표기(`d.srcQ` vs `d.multPeriod`)하도록 if/else 통합 제거.
- **부수 발견·수정**: 커버리지표의 "직전값 이월" 분기(`closingK !== TARGET_QKEY`)가 신계약CSM/기말이 둘 다 "회사별 최신"이 된 지금은 성립하지 않아 **더 최신인 2026.2Q 실공시 회사들을 "이월"로 오표시**하고 있었음(브라우저 실측으로 발견 — 삼성생명 등 6개사 전부 잘못된 라벨). 그 분기·이제 안 쓰는 `TARGET_QKEY` 상수 삭제, "실공시"로 정상화.
- 잔여 하드코딩(`period: estimated ? srcQ : '2026.1Q'`)도 제거 — X는 이제 항상 실제 조회된 분기를 씀.
- 브라우저 실측: 삼성화재(KR0008) X=12,423.5억(CSM_waterfall 2026.2Q 원값과 일치, raw fetch로 대조 확인), 표시 33社 불변(census 37사 중), ECharts 시리즈 13+9+11=33 정합, 콘솔 에러 0, 375px(모바일 리스트는 애초에 X를 안 보여줘 무변경) 확인. `pytest tests/test_deploy_assets.py` 10/10.

**Recent (2026-08-18, owner live-QA 4건 — D-1~D-5):**
- **D-1 민감도 캡션**: FY2025는 stale이 아니라 무설명이었음 — IFRS17 가정민감도(할인율·손해율·사업비율)는 사업보고서 연1회 주석, 반기·분기보고서엔 표 자체가 없음(원문 XML 라벨 출현횟수로 재검증: 한화생명/삼성화재/DB손보 3사). `#senCap`에 "보험계약 가정민감도는 사업보고서 연 1회 공시 — 반기·분기보고서 미공시 항목" 상시 표기.
- **D-2 분기 하드코딩 전수 제거 + PL 실버그 발견**: IFRS17.html 3곳(h2/aria-label/커버리지줄)의 "2023.1Q~2026.1Q" 복붙을 `ix.wfx` 전사 최소~최대에서 도출하는 `CSM_RANGE_LABEL` 하나로 통합. index.html 버블 캡션도 "2026.1Q" 리터럴 5곳(TARGET/캡션/메타/툴팁/커버리지표)을 `NB_TARGET_Q` 상수로 통합하고 문구를 "X·Y=2026.1Q 고정(배수 분모 재수집 보류) / 크기=회사별 최신(2026.1Q~2026.2Q 혼재)"로 정정. 푸터 "최신 공시 분기"를 IFRS17·index·공시보고서 3파일에서 데이터 기반 `<span id="footerQ">`로 교체(K-ICS.html은 owner 지시대로 미변경 — 실측 2026.2Q 행 0건, 아직 2026.1Q가 맞음). **PL 워터폴에서 실제 버그 발견**: `plPeriod()`가 `qs.find(4Q)`로 최신 반기(2026.2Q)보다 직전 마감연도(FY2025)를 우선해서 연도 모드가 상시 1년 stale이었음(owner가 신고한 "PL breakdown이 25회기 기준" 증상의 근본원인) — 최신 우선으로 뒤집고 비4Q 최신은 "2026.2Q(반기누계)"로 라벨링(`fyPartialLabel`, PL 표 헤더도 동일 적용). 브라우저 실측(KR0008): `plCap`="당기순이익 워터폴 · 2026.2Q(반기누계) · …" 정상 확인(수정 전이었다면 "FY2025 (연 누계)"로 표시됐을 것).
- **D-3 🔴 BS T자 + 버튼 무반응 버그 수정**: `.bs-l2-rows{display:flex}`가 UA `[hidden]{display:none}`을 cascade에서 이겨 `box.hidden` 토글이 화면에 반영 안 됐음(aria-expanded는 바뀌어 접근성 트리·실표시 불일치). `.bs-l2-rows[hidden]{display:none}` 한 줄로 수정. 4개 HTML 파일 전수 `hidden` grep 감사 — 이 클래스 외 display+hidden 충돌 없음(K-ICS/index/공시보고서는 `hidden` 속성 자체를 안 씀, PL 재보험 세부 토글은 `style.display` 방식이라 무관). 브라우저 실측(KR0008): 자산/부채/자본 3구역 전부 클릭 후 `hidden:false`+computed `display:flex` 확인.
- **D-4 법정준비금 재배치**: 별도 `#bsReserveNote` 블록(HTML+렌더코드+CSS) 삭제, `renderReserveSubrows()` 신설 — 자본 세부 렌더 시 항목명("이익잉여금", 번호 아님) 매칭으로 앵커를 찾아 준비금 3항목(해약환급금·비상위험·대손)을 들여쓴 하위 행으로 삽입. 합계(잔차 "기타·미표시") 계산에서는 계속 제외(별도 배열로 분리 렌더 — owner 이중계상 경고 유지). 이익잉여금 행이 없는 회사(비상장 등)는 잔차 행 앞에 폴백 삽입(잔차가 항상 마지막 줄이도록). 브라우저 실측: 삼성화재(KR0008, 이익잉여금 有)에서 준비금 3행이 이익잉여금 바로 아래·잔차 위에 정확히 배치되고 잔차가 △81억(소액)으로 준비금이 합계에서 안 빠졌음을 확인, 라이나생명보험(KR0074, 이익잉여금 無)에서 폴백 경로도 정상.
- **Real-viewport 재확인 — 3세션째 carried-over 항목 종결**: 이전 세션들(08-14b/c/d)이 겪던 Browser pane 미compositing이 이번엔 `window.innerWidth`가 실제로 375를 반환해 `resize_window`+JS 쿼리로 실측 가능했음(스크린샷 자체는 여전히 pane 비표시로 실패, DOM/computed-style 쿼리로 대체). 375px에서 `.bs-t` flex-column 전환, 준비금 하위행 1열 grid, 가로 오버플로우 없음(`body.scrollWidth`=`innerWidth`), 콘솔 0건 확인.
- **DIVIDEND-PAGE D-5 개편**: 항목1 주당액면가액 제거. K-ICS.html 패턴을 딴 기간 선택(분기/연도) 신설 — 컬럼은 회사별이 아니라 **전사 공통 윈도**(`GLOBAL_QUARTERS`, dividend.json 전체에서 도출)로 고정해 "이 회사 이 분기 미공시"가 헤더는 유지한 채 셀만 정보없음으로 읽히게 함. 분기=직전5분기, 연도=최신+직전3개년말(4Q, 안 닫힌 최신 회기는 "…누계" 라벨). KPI 카드는 조회기간과 별개로 "최신 4Q 우선 앵커" 그대로 유지하기로 결정, 캡션에 명시(D-5 4번 항목 대응). 브라우저 실측(KR0008): 분기모드 헤더 2025.2Q~2026.2Q, 연도모드 2023/2024/2025/2026.2Q누계 정확히 일치, 0(현금배당금총액 3개분기)과 정보없음(현금배당성향 비4Q) 구분 유지 확인.
- **부수 처리**: publishing 티켓(`inbox/designer/20260803T0900Z`, UH-7) — `K-ICS.html:1090` baseline 키 폴백을 `row.baseline || row.baseline_2025_4Q`로 갱신(HTML 만지는 김에 처리, 급하지 않던 건). validation 티켓(`20260815T0130Z`, 분기 라벨)은 이 owner 티켓 D-2가 흡수해 `_resolved/`로 이동.
- `python -m pytest tests/test_deploy_assets.py` 10/10 (구조적 변경 없음 — keep-list·인라인금지·BOM 영향 없음). 4페이지(IFRS17/index/K-ICS/공시보고서) 전부 데스크톱+375px 0 console errors. K-ICS.html 푸터·`kics_disclosure.json` 등 owner "건드리지 말 것" 대상 미변경 확인. Detail: `docs/changelog_designer.md` 2026-08-18.

**Recent (2026-08-15, 공시보고서.html filled in — 배당현황):**
- **`공시보고서.html`'s "준비 중" shell replaced with a dividend-disclosure screen** (inbox `20260814T2230Z__parser__MULTI__dividend_json_ready_for_gongsi_page.md`, resolved). Owner's C-4 chain confirmed: fill the *existing* page, no new tab/page. Company selector (same UX as the other 3 pages) populated straight from `dividend.json`'s own 24-company registry — not the 39-company kics_disclosure universe, since this DART endpoint structurally never covers the other 15 (non-listed) and a permanent "no data" stub for those adds no value. KPI strip (latest-4Q anchored, since payout ratio/yield are mostly annual-only disclosures) + a company-level table (items 1-7 × all quarters) + one mini-table per 종류주 actually present in the data (보통주/우선주 — auto-detected, no hardcoded 4-company preferred-stock list). Explicit `0` (real no-dividend quarter) kept distinct from absent-row `"정보없음"` (that quarter/item never disclosed) throughout — the exact trap owner flagged twice in the upstream orders. Verified against real data: a company with both share classes showing genuinely different per-class figures (삼성화재, 보통주 16,000원/6.50% vs 우선주 16,005원/8.60% at 2023.4Q), a company with no class-level disclosure at all (롯데손해보험 — real data gap, not a bug, confirmed via direct JSON inspection), 0 console errors. `pytest tests/test_deploy_assets.py` — fixed the designer half of the doc-table gap (`claude-agent-designer.md` §1 row added), publishing half + git-tracking + validation-gate wiring are pre-existing, already-ticketed, out-of-scope blockers (`inbox/publishing/20260814T2230Z` P-1~P-4) — not touched. No push. Detail: `docs/changelog_designer.md` 2026-08-15.

**Recent (2026-08-14d, owner-requested redesign — T-account):**
- **BS panel rebuilt as T-account, moved to top of IFRS17.html** (inbox `20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md`, answered). Owner's own words this time (not an orchestrator paraphrase): move the BS panel above CSM panel 1, draw it like an actual T-account (자산 left / 부채 right-top / 자본 right-bottom, height proportional to value), `+` toggle per zone for a 2-level drill-down. Panels renumbered 1→7 (BS is now 1, CSM waterfall etc. shifted to 2-7). Render logic groups by `섹션`/`레벨` fields data-contract-style — no item-number branching — with a small bridge constant (`EQ_SECTION_LEVEL_BRIDGE`) mapping the *current* pre-migration `IFRS17_BS.json` (items 1-7, no 섹션/레벨 columns yet) so the frame works today; once parser lands the real columns (`inbox/parser/20260814T1250Z…ifrs17bs_detail_lines_for_taccount.md`, in progress) the bridge stops mattering with zero HTML changes. 준비금 (해약환급금 등) kept out of the capital total/detail — separate side note, per owner's explicit double-counting warning.
- **Deleted (not hidden this time) the 08-14b/c dead L2/L3 code**: `renderBsL2`/`toggleBsL2`/`toggleBsDrill`/`renderBsReserves`/`renderBsAociWaterfall`/`eqAociSteps` were preserved-but-uncalled twice already and both times turned out unreusable as-is (schema kept moving under them) — a third preservation added confusion with no realistic reuse path, so this time they're gone; history lives in the changelog instead of dead code in the file.
- Verified 4 companies incl. all three owner-named edge cases: has-detail (삼성화재, 자본 `+` shows AOCI), listed-but-scope-not-landed-yet (자산/부채 `+` disabled everywhere right now, expected pre-parser), non-listed/no-XBRL (라이나생명보험 — totals only, `+` disabled, matches owner's D-3 spec exactly), zero-BS-data (카카오페이손해보험 — stub). T-split flexGrow ratio double-checked against raw values. 0 console errors. `pytest tests/test_deploy_assets.py` 10/10 (no new JSON, no keep-list change expected or seen). No screenshot again — same Browser-pane non-compositing limitation as 08-14b/c (this time confirmed via `window.innerWidth===0`), substituted with direct DOM/attribute queries. Detail: `docs/changelog_designer.md` 2026-08-14d.
- **Still open**: real-viewport mobile stack + keyboard check (carried over, now 3 sessions running — worth prioritizing next time this page is touched in an environment where the Browser pane actually composites). Full detail expansion waits on parser's 섹션/레벨 landing — no designer action needed until that notification arrives.

**Recent (2026-08-14c, same-day repoint):**
- **Panel 7 repoint: `equity_composition.json` → `IFRS17_BS.json`** — owner archived the old 49-item
  master (`inbox/designer/20260814T0232Z`), validator flagged the resulting live-404 risk. Swapped
  `PATHS.eqx` (`IFRS17.html:267`) and remapped `renderBsSection`'s item numbers (old 40/41/1/6/10 →
  new 1/2/3/4/5 — schema changed shape, not just filename). Added a warning comment on the hidden
  L2/L3 code from 08-14b: its item numbers (2-7/20-31/5·10·12·14) belong to the archived schema and
  now silently collide with the new one's 1-7 if ever re-enabled (wrong-labeled real values, not
  nulls). Added `IFRS17_BS.json` to `claude-agent-designer.md` §1 (was never there for
  `equity_composition.json` either — the doc gap validation actually flagged). Verified: all 39
  dropdown companies cycled with 0 console errors, `IFRS17_BS.json` 200s and `equity_composition.json`
  is no longer fetched at all, identity check (KR0001), "미공시" fallback (KR0004, no item5 ever), and
  the no-BS-data stub (KR1098) all still correct. `pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch`
  passes on the designer-doc side; the publishing-doc side is still red pending
  `inbox/publishing/20260814T0232Z` (separate stage, not this session's scope). Detail:
  `docs/changelog_designer.md` 2026-08-14c.

**Recent (2026-08-14b, same-day scope correction):**
- **BS-DRILLDOWN cut down to owner's actual ask**: the 8/14 Panel 7 build below turned out to be built off an over-scoped spec — `inbox/parser/20260814T0035Z__owner__MULTI__equity_tier2_stop.md` + `inbox/validation/20260814T0035Z__owner__MULTI__equity_scope_rollback_core_shrink.md` (both same-day owner corrections to the other two stages, quoting owner's real ask: "high level 17BS(자산/부채/자본/AOCI), 가능하면 해약환급금준비금(안되면 pass)") made clear the L2/L3 drill-down was never requested. No designer-addressed correction existed yet, but confirmed the same read with the user and cut Panel 7 to 5 flat tiles (자산/부채/자본/AOCI/해약환급금, `null`→"미공시"). Drill-down code (L2 stack, L3-a AOCI waterfall, L3-b reserves) **hidden, not deleted** — same convention as the 07-30c CSM 보조표 hide. Detail: `docs/changelog_designer.md` 2026-08-14b.

**Recent (2026-08-14):**
- **IFRS17.html Panel 7 "재무상태표 · 자본의 질"** (inbox `20260813T0422Z`/`20260813T0436Z`, mockup, **not live — superseded same day, see 2026-08-14b above**): new 3-level drill-down section (L1 자산/부채/자본 tiles → L2 자본구성 row-bars → L3-a AOCI waterfall / L3-b 법정준비금) consuming the new `equity_composition.json` root master (항목 1-49). AOCI waterfall reuses the existing PL-panel 0-line-crossing custom-renderItem pattern verbatim; colorblind-safe via ECharts `decal` + text tags (not color-only) on the asset/liability-side bars. Verified against real data (identity checks, a genuine sign-flip case) with 0 console errors across repeated company switches; keyboard/375px pixel verification blocked by this session's Browser-pane compositing limitation (confirmed session-wide via a control test on a pre-existing production button, not a defect in the new code) — flagged below for next-session recheck. **Gated behind validation RED=0 (currently 207) — no deploy, no push.** Detail: `docs/changelog_designer.md` 2026-08-14.

**Recent (2026-07-30c):**
- **CSM 보조표 숨김**: owner "너무 추하게 생겼어" 피드백 → 제거/숨김/재디자인 확인 후 **숨기기(코드 보존)** 선택. `#csm-coverage-panel` `display:none` 인라인 추가, 렌더 로직/CSS 그대로 둠(재노출은 style 제거만). 버블맵은 그대로 노출. **재디자인 여부는 미결 — 다음에 논의 필요.**

**Recent (2026-07-30b, 배포 전 blocker fix):**
- **KR0075 하드코딩 해제**: 보조표의 `verifying = r.code === 'KR0075'`가 parser의 100배 override 정정(inbox 답변)을 모른 채 계속 '검증중'으로 가리고 있었음 — 제거. 이제 정상 데이터(추정 (FY÷4), 0.86×) 표시. 검증 중 census가 35→36사(예별손해보험 신규 온보딩)로 늘어난 걸 보고 카드 제목의 "(전 35사)" 하드코딩도 `#csm-coverage-count` 동적 표기로 같이 고침(재발 방지). 카카오페이 CSM 급변은 상류 데이터 변경이라 designer가 손대지 않음. `pytest tests/test_deploy_assets.py` 8/8. 상세: `docs/changelog_designer.md` 2026-07-30b.

**Recent (2026-07-30):**
- **CSM 버블맵 연1회 공시사 fallback + 전 35사 보조표** (inbox `20260730T0035Z`, resolved): owner flagged IM라이프·IBK연금보험 missing from index.html bubble map — root cause is disclosure-cadence (13/35 companies only file IFRS17 annually, no 2026.1Q NB row), not a data bug. `buildBubbleData()` now censuses all 35 `CSM_waterfall` companies (was 34, missed IBK연금보험 which has no NB row at all); Group A (10사, multiplier carry-forward possible) falls back to latest quarter with both fields non-null, `nbCsm`÷4-annualized for chart X, multiplier carried unscaled; Group B (코리안리·IBK연금·BNP파리바카디프— structurally no multiplier) excluded from chart, kept for the table. Bubble chart: gray/dashed always-legended '추정 (연1회 공시)' series + branching tooltip + `#bubble-meta` count split. New card "IFRS17 — CSM 수록 현황 (전 35사)" below the bubble map — full census table (no new fetch, reuses already-loaded masters), muted+left-border for estimated/no-multiplier rows, remark text chips (not color-only), `<table>+<caption class="sr-only">+scope="col"`. BNP파리바카디프(KR0075) shows `검증중` for all numeric cells pending the 100x-unit-error fix routed to parser. Verified 1280px+375px, 0 console errors, no body horizontal scroll at mobile, cross-checked every Group A/B figure against the inbox's own census (±1억 rounding only). `pytest tests/test_deploy_assets.py` 8/8. Detail: `docs/changelog_designer.md` 2026-07-30.

**Recent (2026-07-22):**
- **Treemap red→blue reverted — owner: finviz identity**: the 07-21d commit's `colorForRatio()` blue swap (below) got reverted same-day-plus-one — owner flagged that the treemap's red/green is an intentional finviz.com market-map reference, not an oversight, and that outweighs the colorblind gap here. Back to red/green; documented as an accepted exception (every cell already shows the ratio as on-cell text too, so it was never color-only). Other 4 items from 07-21d (muted gray, bubble-legend green, placeholder gray, NB_LINE_COLORS, active-tab underline) unaffected. Detail: `docs/changelog_designer.md` 2026-07-22, `docs/a11y_baseline.md` §2b row 12.

**Recent (2026-07-21d):**
- **A11y owner-review queue — sign-off received, all fixed**: the 5 color/contrast items left open from the 07-21 audit (`--muted` 4.45:1, bubble-legend green 3.30:1, `#adb5bd` placeholder 2.07:1, `NB_LINE_COLORS` 2 confusable pairs, treemap/bubble red-green diverging scale) + the active-tab color-only gap — all fixed and verified with `scripts/a11y_contrast_check.py` (not eyeballed) before editing. `NB_LINE_COLORS` needed a full-palette redesign, not a 2-color swap — a minimal fix kept re-introducing new clashes elsewhere in the 6-set; final palette's worst pair is ΔRGB 82 (was 39). Treemap's live `colorForRatio()` below-threshold red→blue (not just the CSS swatch) — mobile list bars inherit for free (same function). Full detail: `docs/a11y_baseline.md` §2b.

**Recent (2026-07-21c):**
- **J-ESR MVP reverted — owner hold confirmed**: built `J-ESR/index.html` (card+ranking-bar, see 07-21b below), then owner corrected: J-ESR work (including the display MVP, not just full-coverage/treemap) is **on hold until 2026-09/10** — meaningful individual-company data doesn't exist before the EDINET 有報 window. This decision predates 07-21b but wasn't recorded anywhere retrievable (not in inbox, TODO, or memory) — owner recalled it from a session that never got written down. Page removed. **Do not resume J-ESR designer work before checking with owner, even though the 06-24 inbox thread (superseded now) reads as an active order.**

**Recent (2026-07-21b, reverted — see above):**
- ~~J-ESR MVP shipped~~ (inbox `20260624T0337Z`): new standalone `J-ESR/index.html` — 일본 주요 보험그룹 ESR 현황, card+ranking-bar (not treemap — owner re-order after as-of mixed across companies). Fetches `J-ESR/jesr_master.json`, splits by `as_of_consistent` into 3 sections: 2026.3末 확정(4사, mutually comparable) / 직전분기 참고(5사, dimmed + "don't compare across sections" note) / 공표대기(2사: T&D·かんぽ生命). Per-card: ESR% + mini bar (intra-section only) + basis label + entity badge(그룹/상호) + yoy_change_pp (△/+ samo) + provenance link. Links `../common.css` for brand consistency; Korea pages untouched per owner's hard constraint. Oct-2026 promotion-to-treemap noted as a code comment hook only (not built — data shape is already treemap-ready). Verified: local server preview, 0 console errors, 11/11 companies in correct section, 375px mobile collapses to 1-col grid, no horizontal overflow.

**Recent (2026-07-21):**
- **A11y baseline + audit** (inbox `20260721T0233Z`, resolved): formalized WCAG 2.1 AA baseline + method in `docs/a11y_baseline.md`, local skill `.claude/skills/a11y-audit/` (chose local over external `ui-ux-pro-max`), contrast/colorblind tool `scripts/a11y_contrast_check.py`. Fixed low-risk/purely-additive gaps: index.html treemap cells + mobile list rows were **click-only** (no keyboard path at all — the site's primary nav interaction, WCAG 2.1.1 fail) → added tabindex/role/aria-label/keydown; custom toggle's focus ring was landing on a 0×0 hidden checkbox → retargeted to the visible label; `공시보고서.html` wasn't linking `common.css` at all (no focus-visible ring, no reduced-motion) → added the link; 10 chart canvases/ECharts containers across 3 pages got `role`/`aria-label`; active-tab links (K-ICS/IFRS17/공시보고서) got `aria-current="page"` (mitigates the color-only active-tab gap for screen readers; visual-only gap for sighted users still owner-gated, unchanged). Owner-review queue (rendered-value changes, not auto-fixed): `--muted`-on-`--card` contrast 4.45:1, bubble-legend green text 3.30:1, `#adb5bd` placeholders 2.07:1, IFRS17 `NB_LINE_COLORS` 2 confusable pairs under deuteranopia sim, index.html treemap/bubble red↔green diverging scale loses contrast under sim. `docs/agents/claude-agent-designer.md` §5.3 updated, stale `#ff9f40` note removed.

**Recent (2026-06-20):**
- **도넛 섹션 잠정 숨김**: K-ICS.html 자본성증권 소진율 패널 `display:none` — 분자 오류(tier1 excess누락·tier2 proxy과대). 마크업/JS 보존. 복구: ifrs17 capital_securities_issuance JSON 완성 후 owner 신호.
- **차트 공통 테마**: Chart.js defaults (Pretendard 폰트, 그리드 #e9ecef, tooltip dark) IFRS17+K-ICS 양 페이지 적용. ECharts 'iq' 테마 IFRS17 waterfall/PL 적용.
- **MOB-KICS 카드뷰**: ≤640px 피벗 테이블 → 분기별 카드(`renderMobileCards`). 서브아이템 들여쓰기. 데스크톱 무변경.
- **KPI 카운트업 애니**: `countUp(el,target,fmt,dur)` ease-out cubic 600ms. index.html 히어로 3개 + IFRS17 Panel 7 KPI 4개. `prefers-reduced-motion` 즉시세팅. **DESIGN-V2 P2 완결.**

**Recent (2026-06-17):**
- **FORWARD_DATA 재임베드**: K-ICS.html L205 `window.FORWARD_DATA` → `templates/forward_capital_latest.json` (37→38사, 2026.1Q 재베이스라인). L1104 Baseline 라벨 2025.4Q→2026.1Q. publishing 트리거 신호 발송.
- **모바일 timeframe 수정 (D9 override)**: `selectPeriods` `isMobile→slice(-1)` 제거 + waterfall 테이블 `_mob` 1버킷 제한 제거. 모바일도 연도/분기 동일 windowing. Playwright 29 GREEN.
- **상각스케줄 Y축 auto-scale**: `toLocaleString` → 데이터 최댓값 기준 조/억/백만 자동 선택 + 타이틀 단위 동기화.
- **예별손해보험 드롭다운 4번째 삽입**: K-ICS.html 하드코딩 옵션에 롯데손해보험 바로 다음 추가.
- **VIS-DONUT 완료 확인**: `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택(명시적 flex-direction:column 불필요). 이미 구현돼있었음.
- **KEYCOLOR-V1 K-ICS 취소**: owner 지시. IFRS17 구현도 불만족(구리다) — K-ICS 미적용.

**Recent (2026-06-16):**
- **DS1 (frontend-design skill)**: 디자인 시스템 정식화 — 신규 루트 `common.css`(토큰 + 공통 chrome + A11y baseline), 3 HTML 점진 배선(무회귀, 확정결정 4개 유지), 프롬프트 §5 skeleton→정식. **common.css는 신규 배포 에셋**(publishing handoff 필요).
- **DS1b (DESIGN-V2 P2 슬라이스)**: index 히어로 KPI 스트립(총 CSM·중위값·수록사·기준분기) + 회사 typeahead 점프. 진입 애니(degrade-safe). 토큰/팔레트/△ 유지.
- **DS2 (webapp-testing/Playwright)**: 회귀 하니스 `tests/regression_dashboards.py`(+README) — **29 assert GREEN**. venv playwright+chromium 설치(번들 Chromium 구동 = Edge dump 0바이트 우회). owner QA 글리치 자동화.
- **G1/G2 (inbox 0506Z)**: IFRS17 재보험 +버튼 → K-ICS `.subtoggle` 양식 통일(.subtoggle→common.css 승격) · Panel2 점선 시리즈 legend "신계약 CSM 시계열 (점선)" 명시.
- **W1**: CSM waterfall(P1)+PL table(P4) 기간 윈도잉 통일 / 롯데 PL waterfall 투자손익 zero-crossing → ECharts custom renderItem.
- **상류 의존**: sensitivity_heatmap의 `period`/`as_of` null → parser inbox `20260616T0030Z`.

## 🔴 Open — P1

### BS-TACCOUNT — IFRS17.html Panel 1 (was Panel 7) 재무상태표 (formerly BS-DRILLDOWN, renamed 2026-08-14d)
Now a T-account at the **top** of the dashboard (owner's own explicit ask this round — `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md`, answered), not a mockup panel anymore in intent. Data-contract-driven by `섹션`/`레벨` fields on `IFRS17_BS.json` (parser landing separately, `inbox/parser/20260814T1250Z…`) — no item-number branching in the render code.
- [x] **T-account + reposition (2026-08-14d)**: moved above Panel "2) CSM 이동" (was 7, all panels renumbered 1-7). 좌 자산 / 우상단 부채 / 우하단 자본, right-column height ∝ value ratio. Per-zone `+` (`.subtoggle`, reused from the PL panel) toggles a 레벨2 detail list; disabled+`aria-disabled`+"세부 미공시" when a section has zero 레벨2 rows (covers both "parser hasn't landed detail yet" and "company doesn't disclose" with the same code path — no special-casing needed). 준비금 kept structurally separate from 자본 (own side-note block, excluded from the capital total/detail) per owner's explicit double-counting warning.
- [x] `EQ_SECTION_LEVEL_BRIDGE` bridges the *current* pre-migration schema (items 1-7, no 섹션/레벨 columns yet) so the frame renders today; disappears in effect the moment parser's real columns land (row data wins over the bridge automatically, zero HTML changes needed).
- [x] **This time actually deleted** (not hidden) the 08-14b/c dead L2/L3 functions — preserved-uncalled twice already, proven unreusable both times because the schema kept moving under them. History is in the changelog, not in commented-out code.
- [x] Verified 4 companies incl. all 3 of owner's named edge cases (has-detail / listed-no-detail-yet / non-listed-never-has-detail / zero-BS-data). 0 console errors. `pytest tests/test_deploy_assets.py` 10/10.
- [x] **Real-viewport recheck (2026-08-18, resolved after 3 carried-over sessions)**: this session's Browser pane returned a real `window.innerWidth===375` (not the `0` bug from 08-14b/c/d) — confirmed via `resize_window`+JS query: `.bs-t` switches to `flex-direction:column`, detail/sub rows collapse to 1 grid column, `body.scrollWidth` never exceeds `innerWidth` (no horizontal overflow), 0 console errors. Screenshot pixels still unavailable (pane still doesn't composite for actual frame capture), but this is real DOM/computed-style verification, not a skip.
- [x] **Schema landed same session** (owner shrank scope to 13 detail items, not the original ~60 — `inbox/_resolved/20260815T0100Z__parser__MULTI__ifrs17bs_taccount_schema_ready.md`): confirmed compatible with zero HTML changes (contract design worked as intended). Data shape + render-code field matching verified by direct inspection (`fetch(...,{cache:'no-store'})` vs. `renderBsZone`); a true fresh-browser render wasn't achieved that session — local server's HTTP cache kept serving the pre-migration snapshot. **2026-08-18: confirmed live** — 자산/부채/자본 `+` all enable and render real rows for KR0008 (Tier-1), verified via `.click()` + `box.hidden`/`getComputedStyle(...).display` in a clean preview.
- [x] **Partial-detail confusion fixed (2026-08-15, inbox `20260814T1710Z__validation__IFRS17__bs_detail_is_highlight_label_it.md`)**: validation caught that the 레벨2 detail is an intentional "≤15-line highlight" (owner scope, not full closure — `scripts/build_ifrs17_bs.py`), so a section's shown detail routinely undershoots its total (worst case validation found: 신한라이프 자산 세부 17-21조 vs 59조+ total) with zero on-screen explanation — reads as broken. Fixed by computing a "기타·미표시" residual row client-side (`total − Σshown`, no master change) plus a short caption clause. Re-verified on the exact worst-case company (신한라이프/KR0094): shown-detail + residual now ties out to the total within rounding.
- [x] **🔴 `+` toggle dead-on-arrival bug fixed (2026-08-18, owner live-QA `inbox/designer/20260818T0026Z` D-3)**: `.bs-l2-rows{display:flex}` was beating the UA `[hidden]{display:none}` default in cascade, so `box.hidden` toggling never changed the rendered layout — the button looked completely dead (aria-expanded flipped, screen didn't). Fixed with one CSS rule, `.bs-l2-rows[hidden]{display:none}`. Audited all 4 HTML pages for the same display+hidden collision pattern — none found elsewhere (K-ICS/index/공시보고서 don't use the `hidden` attribute at all; the PL 재보험 subrow toggle uses `style.display`, unaffected).
- [x] **법정준비금 재배치 (2026-08-18, D-4)**: moved from a standalone `#bsReserveNote` block (deleted, along with its render code + CSS) into the 자본 zone's own detail list, as indented sub-rows anchored right after the "이익잉여금" row (name-matched, not item-number — new `renderReserveSubrows()`). Still excluded from the shown/residual sum (rendered via a separate pass, owner's double-counting warning preserved) — verified on KR0008 the residual stayed a small △81억 (not off by the ~6.95조 it would be if reserves had leaked into the sum). Companies without an 이익잉여금 row (non-listed) get the sub-rows inserted before the residual row instead.
- [x] **버그 수정(같은 대화, owner 즉시 재확인): 연도모드 "직전 3년" 위반** — 재사용한 `selectPeriods()`가 무상한(전체 4Q) 반환이라 BS가 2021년까지 있는 회사(메리츠화재·현대해상·KB손보·코리안리 등)에서 6열까지 붙었음. BS 전용 `eqYearPeriods()`(최신+직전3개년말 하드캡, `wfYearBuckets()`와 동일 패턴) 신설로 교체, 공유 함수는 미변경(CSM/PL/NB 마스터는 실측상 전부 2023년 시작이라 이 결함이 잠재적일 뿐 미발현 — 확인만 하고 안 건드림). 6개사 전부 재검증 완료.
- [x] **시계열 원천 테이블 신설 (2026-08-19, owner 채팅 발주)**: T자 밑에 다분기(`#wfPeriod` 연동, `selectPeriods` 재사용) 표 추가 — 분기=직전5분기 / 연도=최신+직전3개년말, 분기 미제공사는 CSM 패널과 동일 문구의 stub. 자산/부채/자본[+] → 세부[+] → 자본 세부의 "이익잉여금"은 자체 중첩 [+]로 법정준비금(이제 4항목 — `보증준비금 기적립액` 신규, 생보 16사만) 한 겹 더. 항목은 선택 기간 전체의 이름 유니온(`eqUnionNames`)이라 항목번호 하드코딩 없음. 상위 토글 접을 때 중첩 하위 토글도 재귀 리셋(`collapseGroup`). `renderBsTable`/`buildBsTableDom`/`eqHasQuarterly`/`eqUnionNames`/`eqValByName` 신설. 브라우저 실측 다수(연도/분기 헤더 owner 예시와 정확 일치, 생보/손보 준비금 항목수 차이 확인, stub 전환, zero-BS-data 회사 무충돌, 375px 표 자체 스크롤). `pytest` 10/10.
- [x] **(종결 2026-08-20)** Deploy 차단 해소 — 게이트 `RED=0 YELLOW=276 exit=0`, main 배포 실제로 진행됨(`a0979b9`, 오늘만 3회). 원문: (unrelated to this rebuild, standing condition). No push attempted.

### DIVIDEND-PAGE — 공시보고서.html 배당현황 (built 2026-08-15)
Owner's C-4 chain, designer leg (`inbox/_resolved/20260814T2230Z__parser__MULTI__dividend_json_ready_for_gongsi_page.md`). Fills the page's long-standing "준비 중" shell — no new tab/page, per owner's explicit constraint.
- [x] Company selector (24-company registry, drawn from `dividend.json` itself, not the 39-company kics universe — the 15 non-listed companies structurally never have this DART disclosure, so they're left out of the picker rather than showing a permanent empty stub) + KPI strip + company-level table (항목 1-7) + per-종류주 mini-tables (항목 8-10, auto-detected classes, no hardcoded company list).
- [x] `0` vs `"정보없음"` kept strictly separate everywhere (owner's own repeatedly-flagged trap) — verified on real data, not just written and assumed.
- [x] `claude-agent-designer.md` §1 doc-table gap fixed (my half of `test_docs_agree_with_what_pages_fetch`).
- [x] **(종결 2026-08-20)** `dividend.json`은 **git 추적 중**이고(`git ls-files` 확인) 2026.2Q 24사까지 배포됐다. 'untracked·deploy far off' 전제 stale. 원문:, `claude-agent-publishing.md` doesn't mention it yet, and `validate_data_contract.py` doesn't wire this master into its gate at all — all three already ticketed in `inbox/publishing/20260814T2230Z` (P-1/P-2/P-4), not this stage's files to touch.
- [x] **Period selector added (2026-08-18, owner live-QA `inbox/_resolved/20260818T0026Z` D-5)**: the "shows all 14 raw quarters" gap above is closed — added a K-ICS.html-style 기간(분기/연도) toggle. Quarter mode = last 5 quarters, year mode = latest + prior 3 fiscal year-ends (partial current year labeled "…누계", e.g. "2026.2Q누계"), both derived from `dividend.json`'s own data (`GLOBAL_QUARTERS`), not hardcoded. Window is **global** (same header columns regardless of which company is selected), not per-company — deliberate, so a company's missing quarter shows as a 정보없음 cell under a stable header rather than shifting the whole column set. Also removed 항목1 주당액면가액 (owner: "필요없으니까 빼고"). KPI strip decision: stays anchored to "latest 4Q" regardless of the new period selector (a multi-quarter window doesn't map to a single KPI snapshot) — documented in `#divKpiCap`'s caption per owner's explicit ask to decide-and-state. Verified live on KR0008: quarter headers 2025.2Q~2026.2Q, year headers 2023/2024/2025/2026.2Q누계, `0`-vs-정보없음 distinction intact (현금배당금총액 real 0 for 3 quarters vs 정보없음 for the undisclosed 2026.2Q cell), 0 console errors, 375px no horizontal overflow.
- [x] Real-viewport mobile recheck done for this page too (2026-08-18, same session as BS-TACCOUNT above) — `resize_window`+JS query confirmed `.controls` wraps, period selector visible, no horizontal overflow at 375px.

### KEYCOLOR-V1 — 회사 키컬러 액센트 시스템 ~~(K-ICS 취소, IFRS17 재검토 대기)~~
IFRS17 적용 완료 2026-06-13. K-ICS 적용은 **owner가 2026-06-17 취소** (IFRS17 구현 불만족). IFRS17 키컬러도 재검토 필요 — owner 피드백 대기.
- [x] IFRS17 적용 완료 (2026-06-13)
- [~] K-ICS 적용: **owner 취소 (2026-06-17)**
- [ ] (보류) 전체 키컬러 방향 재검토 — owner 피드백 후

### DESIGN-V2 — de-AI 디자인 오버홀 (proposal delivered 2026-06-11, awaiting owner sign-off)
Owner complaint: site looks AI-generated. Audit done (4 pages + barabom.me reference — actual findings: Spoqa Han Sans Neo webfont + restrained neutrals + 0.1-0.2s micro transitions, NOT heavy animation). Phases:
- [ ] **P1 quick wins (~half day)**: Pretendard Variable + `font-variant-numeric:tabular-nums` 전역 / 탈부트스트랩 팔레트(#0d6efd·#f8f9fa 교체, 잉크+페이퍼+딥블루 1액센트) / favicon(IQ 모노그램)+OG+meta description / footer(출처·기준분기·면책) / 이모지 placeholder 제거 / radius 12→6px / Chart.js·ECharts 색 CSS 변수화 (기본 teal/pink 퇴출). [부분 착수: P1-QUICKWIN 일부 done 2026-06-12, 팔레트 교체는 보류]
- [x] **P2 structural (1~2d)**: ✅ common.css · ✅ index 히어로 KPI 스트립+typeahead · ✅ scroll-reveal · ✅ 차트 공통 테마 · ✅ KPI 카운트업 애니(index 3개+IFRS17 Panel7 4개, ease-out 600ms, 2026-06-20) — **완료**
- [ ] **P3**: M3 잔여(도넛 stack·범례) 흡수, 다크모드(선택)
- [x] **TREEMAP-SCALE**: 트리맵 색 임계 앵커 130/200% + 범례 임계 표기 — done 2026-06-13 (권고선=130%, 민감도 패널 150%→130% 정합)
- [ ] **COMPANY-ACCENT**: 회사 키컬러는 배경 틴트 대신 "액센트 1곳" 원칙(패널 제목 2px 룰 + 회사명 칩 + 차트 주 시리즈, 저채도 변형 23사 맵) — 시안 owner 승인 후

## 🟠 Open — P2

### MOB-KICS — K-ICS.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render** (not foundation-only). M1 foundation already in place (header/tabs/table scroll, chart heights ↓).
- [x] Donuts stacked vertically — `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap`으로 375px에서 자동 1열 스택. 이미 구현됨 (2026-06-17 확인).
- [x] Forward-chart legend reposition — `position: window.innerWidth < 640 ? "bottom" : "top"` (2026-06-17)
- [x] Dense table → card view (가/나/다 sub-items) — `renderMobileCards` ≤640px (2026-06-20)
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels — decide which panels scroll vs reflow
- [ ] **(owner open rec 2)** breakpoint set — confirm thresholds beyond the single 640px (e.g. <400px sub-query)

### MOB-IFRS17 — IFRS17.html full mobile layout (scope confirmed by owner 2026-06-12)
Owner confirmed scope: **full-panel mobile pass + alternative render**. M1 foundation only so far.
- [ ] Panel 1–6 mobile policy: which to keep, which to collapse, which to swap for alternate viz
- [ ] Panel 7 (BS-DRILLDOWN, added 2026-08-14) has `@media(max-width:640px)` CSS following the same pattern as Panels 1-6 but hasn't had a real-viewport pixel check — fold into this pass' verification
- [ ] **(owner open rec 1)** horizontal-scroll range for dense panels
- [ ] **(owner open rec 2)** breakpoint set confirmation
- (shares the two owner open recs with MOB-KICS — resolve once for both pages.)

### VIS-DONUT — K-ICS donut row stacks on phones ✅ 완료
- [x] `.donut-cell{flex:1 1 280px}` + `flex-wrap:wrap` → 375px 화면에서 자동 1열 스택. 명시적 flex-direction:column 불필요. 이미 구현됨 (2026-06-17 확인).
- [x] Labels legible: 각 도넛이 전체 너비 차지, 레이블 공간 충분.

### VIS-CHARTLEGEND — chart legend/axis density on mobile
- [x] K-ICS forward + IFRS17 hist/NB legend → bottom on mobile (`window.innerWidth < 640`) (2026-06-17)
- [ ] IFRS17 amort + index bubble legend (amort display:false OK, bubble ECharts top=8 review later)

### M3 — chart fine-tuning (roll-up of VIS-DONUT + VIS-CHARTLEGEND + misc)
- [x] K-ICS 도넛 2개 세로배치 (= VIS-DONUT) — 이미 구현됨
- [x] Forward 라인 범례 위치 (= VIS-CHARTLEGEND) — done 2026-06-17
- [ ] 차트 미세조정 across pages

### Panel 7 — 원천지표 카드 ✅ 완료 (2026-06-17)
IFRS17.html 대시보드 최상단에 4-card KPI strip 추가(기말 CSM 잔액·CSM 상각·신계약 CSM·NB CSM 배수). `wfVal(company,latestQ,6/5/2)` + `ix.nbm` 기반. 2열 모바일 그리드.

### INDEX-BUBBLE-V2 HTML side — 4축 bubble rendering
Publishing ships the data (`TODO_publishing.md` INDEX-BUBBLE-V2). Designer ships the ECharts spec:
- [x] **🚫 폐기 — 재착수 금지 (2026-08-20 확인)**. 4축 V2는 owner가 폐기했고 **3축이 이미 라이브 완결**이다: `index.html` L165 *"X: 신계약 CSM 규모 · Y: NB CSM 배수 · 크기: 기말 CSM 잔액"*. 이 줄을 열린 항목으로 두면 다음 세션이 완결된 기능을 다시 만든다. 원문:
- [ ] Mobile rendering: **3축** 버블맵 → simplified (bar 또는 list with sort options) — 위 4축 폐기에 맞춰 축 표기 정정(2026-08-20)
- [ ] Click → cross-nav (existing pattern)

### F17 Panel 3 — Tier2 LOB drill-down rendering (when publishing ships Tier2 JSON)
Publishing currently has Tier1 4-bar in production. Tier2 (LOB 장기/자동차/일반 stacked) waits on parser F17 decision + publishing assembly.
- [ ] Stacked bar / waterfall design (손보만, LOB visible)
- [ ] 생보 alt-rendering (장기 전사 fallback)
- [ ] Caption variant per-company taxonomy (장기/자동차/일반 vs 보장성/물보험/저축성)

## ✅ Done (archive)
완결 항목 25+개(2026-05-28~06-14) — M1 모바일 foundation, KEYCOLOR/TREEMAP-SCALE, △(세모) 전면화, 생명장기·시장위험액 토글, PL/CSM 워터폴 패널, HTML single-source refactor, dead-CDN 제거 등. 상세는 `docs/changelog_designer.md`(당시 `(changelog MM-DD)`로 인덱싱) + git log.


## 🗂️ Conventions reference

**Responsive breakpoints**
- M1 foundation: `@media (max-width:640px)` on all 4 pages. Header/tabs/chart heights/table scroll.
- M2: index.html ≤640px swaps treemap → vertical list (`renderList()` mirrors `render()`).
- M3: donut stack + legend reposition + chart fine-tuning.

**Chart libraries (committed)**
- Chart.js: IFRS17 Panels 2–6
- ECharts: Panel 1 (CSM waterfall), index treemap, bubble

**Page roster (root single-source since 2026-05-28)**
- `index.html` — market map + IFRS17 quadrant + bubble
- `K-ICS.html` — per-insurer detail + sub-items + forward outlook
- `IFRS17.html` — 7-panel dashboard (1=BS T-account, 2-7=CSM/PL/NB/sensitivity)
- `공시보고서.html` — 배당현황 (per-company dividend disclosure, filled in 2026-08-15; was a static "coming soon" shell before)

**Local preview:** `python -m http.server 8000` from repo root. (preview_eval 반복 행 시 Edge headless `--dump-dom` 대체; 좀비 포트 회피로 현재 8889.)

## Reading order for designer subagent
1. This file (`TODO_designer.md`) — current state (changelog is deferred: [`docs/changelog_designer.md`](docs/changelog_designer.md) is history, open only when you need a past decision's background)
2. [`docs/agents/claude-agent-designer.md`](docs/agents/claude-agent-designer.md)
3. Root HTML page(s) in scope
4. Master JSON schema (publishing's output) for the panel you touch — read-only
5. Root [`TODO.md`](TODO.md) for cross-stage roadmap notes

## Hand-off
- **From publishing**: notification that a master JSON changed (`manual_html_edit` warn) or that a new field needs rendering.
- **To human**: designer never pushes. Hand off to publishing for the commit message + push recommendation.
