---
from: owner
to: designer
created: 20260912T0530Z
status: resolved
route: html
company: JP_MULTI
period: FY2025
track: J-ESR
supersedes: 20260912T0446Z
---

## 미결 (owner) — `jp/index.html` 2차 개선 (정렬·섹션분리·표 단순화, owner 실사용 피드백)

**배경.** owner 가 초안을 직접 보고 5가지 지적. publishing 이 병렬로 `jp/jesr_esr.json` 에서 부모-자식 중복 2건
(Sony Life Insurance, Meiji Yasuda Non-Life)을 빼는 작업 중이다(`inbox/publishing/20260912T0530Z`) — 이 페이지는
그 결과(13 레코드가 될 예정, `_meta.excluded_subsidiaries` 로 확인 가능)를 그대로 읽으면 된다. **레코드를 이 페이지에서
또 필터링하지 마라** — 필터는 publishing 쪽 책임이고 designer 는 받은 records 를 그대로 쓴다.

**할 일 (owner 지시 5개, 전부 반영).**

1. **정렬 = 2단 버킷.** `category` 가 `HD上場`·`相互会社`·`上場` 로 시작하면 버킷 A(주요 시장 플레이어),
   `子会社`·`独立` 등 그 외는 버킷 B. 각 버킷 안에서 `esr_pct` 내림차순. 버킷 A 전체를 먼저, 그 다음 버킷 B.
   차트·표 둘 다 이 순서를 쓴다. (총자산 데이터가 15사 중 2사뿐이라 시가총액/자산 정렬은 불가 — category 로 대체.)
2. **업종별 top5 + 더보기.** 루트 `index.html` 의 기존 패턴(`FOLD = 5`, 버튼 텍스트
   `더보기 (${count}개사)` / `접기`, MOB-INDEX-FOLD 근처 참고)을 그대로 가져온다. `sector` 로 두 섹션(生保/損保) —
   **`reinsurance` sector 는 損保 섹션에 합친다**(한국 사이트가 코리안리를 별도 탭 없이 손보군에 묶는 것과 동일 관례,
   지금은 posted 0건이라 당장 안 보이지만 10월 재census 이후 나올 수 있다). 섹션 안 회사 수가 5 이하면 더보기 버튼
   자체를 렌더링하지 않는다(지금 손보는 4사라 버튼 없음, 생보는 9사라 top5+더보기 4사).
3. **출처 열 제거 + 공시일자에 링크.** 표의 `出所` 열을 없앤다. 대신 `基準日` 옆이나 별도로 두던 문서 게시일
   (현재 `doc_date`, 예: 2026-07-30)을 **그 텍스트 자체에 `source_url` 하이퍼링크**를 건다(`target="_blank" rel="noopener"`,
   `aria-label`에 "…의 근거 자료, 새 탭에서 열림" 류 유지). `基準日`(as_of, 전 행 2026-03-31로 동일)은 그대로 열로 둔다.
4. **연결/단체 시각 축 제거.** 막대차트의 빗금(연결) 패턴과 그 범례 항목을 없앤다. `scope` 값 자체는 버리지 말고
   표의 備考 열이나 툴팁에 짧은 텍스트(예: "連結"/"単体")로만 남긴다 — 차트 색상·패턴 인코딩에서는 뺀다.
5. **잠정(速報) 배지는 유지.** owner 지적 대상이 아니었다.

**검증.** `python -m http.server 8896` (repo root) → `http://localhost:8896/jp/`. 콘솔 에러 0, 데스크톱 1280px +
모바일 375px 스크린샷 재생성(같은 파일명에 덮어쓰기: `artifacts/designer/jesr_jp_draft_desktop_20260912.png`,
`..._mobile_20260912.png`). `jp/jesr_esr.json` 이 아직 15사(publishing 작업 전)면 그 상태로 먼저 만들고, 끝나기 전에
`_meta.excluded_subsidiaries` 존재 여부로 13사 갱신을 확인해 반영한다(순서상 기다려야 하면 답변란에 명시).

**규칙.** 서브에이전트 생성 금지, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 데이터 HTML 인라인 금지(fetch 유지).
끝나면 답변란에 변경 요약 + 스크린샷 경로 + (있으면) 새 판단거리를 적고 `status: answered`.

## 답변 (designer, 2026-09-12)

`jp/jesr_esr.json` 은 착수 시점 이미 publishing 작업 완료 상태(13 레코드, `_meta.excluded_subsidiaries` 2건 확인) —
대기 없이 바로 반영, 재필터링 없이 그대로 fetch.

**수정 파일**: `jp/index.html` 만 (145줄 추가/51줄 삭제).

1. **정렬 2단 버킷** — `isBucketA(category)=/^(HD上場|相互会社|上場)/`, `sortBucketed()` 로 버킷A(esr desc)→버킷B(esr desc).
   실측: 生保 9사 전원 버킷A. 損保 4사는 SOMPO(270)/東京海上(238)/MS&AD(214, 전부 버킷A) 뒤에 au損害保険(791.7%, 버킷B
   `子会社(KDDI)`)이 esr 1위인데도 맨 뒤로 밀림 — 지시대로.
2. **業種별 top5+더보기** — `FOLD=5`. ESRランキング(차트)·一覧表(표) 둘 다 生保/損保 서브섹션으로 분리, 섹션당 버튼이지만
   `expanded{life,nonlife}` 상태 공유(차트/표 어느 버튼을 눌러도 같이 펼쳐짐). 실측: 生保 9사→top5+"もっと見る（他4社）",
   損保 4사→버튼 없음(hidden). reinsurance 는 `groupKey()` 로 損保 섹션에 자동 합류(현재 0건, 배선만 미리).
3. **出所 열 → 公表日 열** — 헤더 6번째 열을 `公表日` 로 교체, `doc_date` 텍스트에 `source_url` 링크
   (`target="_blank" rel="noopener noreferrer"`, aria-label 유지). `基準日`(as_of) 열은 그대로.
4. **연결 시각 인코딩 제거** — bar `decal`(빗금)·범례 `グループ連結` 삭제 + 이제 안 쓰는 `.hatch-sw` CSS도 같이 제거.
   `scope` 는 表 範囲 열(기존)과 차트 tooltip 신규 1행(`範囲: 連結/単体`)에 텍스트로만 유지. bar 색은 섹션당 단색으로
   단순화(생보=blue, 손보=orange) — 섹션 헤더가 이미 業種을 명시.
5. **速報 배지** — 무변경.

**함정 재확인**: `.more-btn{display:block}` 이 특이도 동점으로 UA `[hidden]{display:none}` 을 이기는 걸 알고
`.more-btn[hidden]{display:none}` 가드를 처음부터 넣음(claude-agent-designer.md §4 기존 사고 재확인, 재발 없음).

**검증**: `python -m http.server 8896` + Playwright(chromium)로 DOM 텍스트 실측 — 生保 top5 순서·損保 4사 전원 노출·
"もっと見る" 라벨·표 링크 텍스트 전부 지시대로 렌더링 확인. **미확인 1건**: ECharts 막대 자체의 시각 렌더는 이 세션에서
확인 못함 — `cdn.jsdelivr.net`(echarts/pretendard) 이 이 순간 간헐적으로 `net::ERR_NETWORK_ACCESS_DENIED` (같은 순간
무수정 루트 `index.html` 도 동일 CDN 참조로 동일 에러 재현 — jp 페이지 결함이 아니라 지금 세션의 네트워크/보안에이전트
상태로 추정, `project_pc_cannot_push` 메모리와 정합). 데이터 변환·색상·타깃마커 로직은 코드 리뷰로 확인함. 다음 세션
네트워크 정상화 시 차트 시각만 재스크린샷 권장.

**스크린샷** (덮어쓰기): `artifacts/designer/jesr_jp_draft_desktop_20260912.png`(1280px),
`artifacts/designer/jesr_jp_draft_mobile_20260912.png`(375px) — 레이아웃·요약카드·섹션분리·표·더보기 버튼 정상.

`TODO_jp.md`·`docs/changelog_jp.md` 갱신 완료. 커밋은 하지 않음(같은 워킹트리에 publishing/parser 세션의 미커밋 변경이
섞여 있어 owner/publishing 판단에 맡김).

## 종결 재확인 (orchestrator 2026-09-12)

- designer 보고대로 5개 지시사항(2단 정렬·top5+더보기·出所→公表日 링크·연결 빗금 제거·速報 유지) 코드 확인 완료.
  designer 세션의 Playwright 캡처가 jsdelivr `ERR_NETWORK_ACCESS_DENIED`(이 PC 크로미움 계열 공통 현상,
  `TODO_designer.md` 2026-09-11 기존 사례와 동일)로 차트가 빈 화면으로 찍힌 것을 확인 — echarts 로컬 임시
  사본(검증 후 즉시 삭제, `jp/index.html`은 CDN 참조만 유지)으로 재검증해 정상 렌더 확인.
- **추가 버그 1건 발견·직접 수정(발주 범위 밖, 명백+해결 쉬움)**: 재검증 중 모바일(375px) 생명보험 차트의
  x축 눈금 라벨이 "50%00%050%060%090%00%" 식으로 겹쳐 읽을 수 없었다(값 범위가 커 눈금 8개가 좁은 폭에
  욱여넣어짐). `xAxis.axisLabel.hideOverlap:true` + 모바일 `splitNumber:4`(데스크톱 6 유지)로 수정,
  재검증 스크린샷(`artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`, 덮어씀)에서 "0% 100%
  200% 300% 400%" 로 정상 표시 확인.
- 최종 상태: `jp/jesr_esr.json` 13사, `jp/index.html` 379행. HTML 태그 균형 재검사 0오류, BOM 없음,
  ECharts CDN integrity 값 루트와 byte-diff 0(제 임시 로컬치환은 검증 후 원복 완료).

status: **resolved** — owner 5개 지시 + 발견 버그 1건 전부 반영·검증 완료.
