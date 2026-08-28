---
from: orchestrator
to: parser
created: 20260829T0100Z
status: resolved
route: backlog
company: MULTI
period: MULTI
lane: kics
iter: 1
---

## 미결 (orchestrator 작성 — owner 지시)

**루트 마스터 3종이 `insurequant_master_tables.xlsx` 목록에서 빠져 있다. 넣어라.**

```
kics_tier1_utilization.json     기본자본 인정한도 소진율 (신종자본증권/후순위채 발행현황 기반)
kics_tier2_utilization.json     보완자본 인정한도 소진율
kics_forward_capital.json       자본비율 5년 전망 (콜옵션 도래 + SCR 선형보간)
```

셋 다 이미 존재하고 `K-ICS.html` 이 fetch 해서 화면에 그리고 있다(도넛 한도소진율,
"자본비율 5년 전망(Forward Outlook)" 차트). `build_master_xlsx.py` 의 `MASTERS`(현재 8개)에
처음부터 안 들어가 있어서 xlsx 에도, 다운로드 팝업 시트 목록에도 빠졌다.

### 방식 — 전체 재생성 금지 (여기가 핵심이다)

선행 조사가 *"스키마 변경이라 마스터 xlsx 재생성이 걸리는 작업"* 이라고 했는데 **결론이 반대다.**

`build_master_xlsx.py` 는 `pd.ExcelWriter(OUT, engine="openpyxl")`(기본 `mode="w"`)로 **파일
전체를 새로 쓴다.** MASTERS 밖 수기 시트와 다른 레인이 손으로 맞춰 둔 설명까지 되돌린다.

**그런데 `sync_master_xlsx_sheet.py` 가 `build_master_xlsx` 의 `MASTERS`/`coerce` 를 import 해서
목표 상태를 만든다.** 따라서:

1. **스키마는 `MASTERS` 에 정의한다**(flatten 로직 포함). 거기가 단일 정의처다.
2. **시트 반영은 `sync_master_xlsx_sheet.py` 로 한다.** `build_master_xlsx.py` 통짜 실행 금지.
3. sync 가 **신규 시트 생성을 지원하는지 먼저 확인**해라. 기존 시트 동기화용으로 만들어져 있어
   신규 시트는 전량 insert 경로가 된다. 지원 안 하면 sync 를 최소한으로 확장해라 — 전체 재생성보다
   그쪽이 안전하다. 확장했으면 사후검증(다른 시트 값 동일성)이 그대로 도는지 확인해라.

### flatten 스키마 — 설계해서 먼저 보고해라

기존 8시트는 전부 `회사 × 분기 × 항목명 × 값` long-format 인데 이 셋은 구조가 다르다.
tier1/2 는 "분기 스냅샷 + 회사별 결과", forward 는 "회사별 5개년 projections 중첩" 이다.
**기존 long-format 과 최대한 같은 모양으로 눕히는 안**을 만들어 owner 승인 전에 보고해라.
`공시분기` 자리에 전망연도(2026~2030)를 넣는 식이 후보다.

### tier2 4개사 이상치 — 이것 때문에 미루지 않는다 (owner 판단)

tier2 소진율이 38개사 중 34개사만 0~100% 안에 들어오고 4개사는 분자 파서 추출이 불안정한
known issue다. forward 는 콜옵션 미공시 시 법정만기 폴백 한계가 있다.

**그렇다고 xlsx 를 미루지 않는다.** 같은 데이터가 이미 화면에 같은 한계를 안고 나가 있어서
xlsx 를 보류해도 아무도 보호되지 않는다. 대신 **한계를 시트 안에 박아라** — hover 설명은 파일에
안 따라가지만 시트 열은 따라간다.

- 각 시트에 **주석/신뢰도 열**을 두고 해당 셀의 한계를 표기해라(예: tier2 분자 불안정 4개사,
  forward 콜옵션 미공시 폴백 적용사).
- 또는 시트 상단에 한계 명시 행. 어느 쪽이든 **숫자만 떼어가도 한계가 같이 간다**는 조건을 만족해라.
- 어느 4개사·어느 폴백사인지 실제로 census 해서 표기해라. 추정으로 쓰지 마라.

### 후속 (이 티켓 범위 밖)

다운로드 팝업의 시트 목록(`public_exports/*.csv`, `download-survey.js`)에 새 3시트를 반영하는 것은
designer 소관이다. 이 티켓이 끝나면 orchestrator 가 발주한다.

### 하지 말 것

- **`build_master_xlsx.py` 통짜 실행 금지.** 위 §방식 참조.
- openpyxl 로 마스터 xlsx 재저장 금지(수식 캐시가 날아간다).
- `PL_breakdown.json`·`data/dart/viz/pl_breakdown_master.json` 금지 — ifrs17 레인 에이전트가
  지금 그 마스터에 쓰고 있다. `손익분해PL` 시트도 건드리지 마라.
- `index.html`·`K-ICS.html`·`IFRS17.html` 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.
- python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스. UTF-8(BOM 없음).

## 답변 (recipient 작성 — 처리 후)

**status: answered** (구현 완료·검증 통과, 다만 §3 "4개사 이상치" 전제가 stale 로 실측돼 owner/orchestrator
재확인 필요 — 아래 참조). 1단계(설계) 도중 코디네이터가 owner 승인 스키마를 채팅으로 전달하며 2단계
구현까지 지시해 같은 세션에서 이어서 처리했다.

### 변경 파일

- `scripts/build_master_xlsx.py` — `MASTERS` 에 3항목 추가 + flatten 함수 3개(`_flatten_tier1/
  _flatten_tier2/_flatten_forward_capital`) + `FLATTEN` dict. **`main()` 은 실행하지 않았다**(정의만
  참조됨, `git log`/실행이력 없음).
- `scripts/sync_master_xlsx_sheet.py` — `FLATTEN` 적용(`target_rows()`), **신규 시트 생성 지원**
  추가(`is_new_sheet` 분기: 헤더행 생성 → 기존 코드가 "빈 시트로 시작하는 기존 시트"로 취급해
  그대로 동작 → insert 루프 종료 후 스타일 보정 1패스 → 요약 시트에 신규 행 삽입). 기존 "시트
  cherry-pick" 경로는 **한 줄도 안 바꿨다**(신규 분기만 추가).
- `insurequant_master_tables.xlsx` — 신규 시트 3개 추가(아래).
- 신규 read-only 진단(전부 `scripts/_probes/`, 상주): `probe_20260829_capital_masters_census.py`
  (census 전체), `probe_20260829_flatten_smoke.py`(flatten 스모크), `probe_20260829_xlsx_final_check.py`
  (xlsx 사후검증).

### 1) 컬럼 스키마 (owner 승인안 그대로 구현)

8열: `원보험사코드·원수사명·티커·생손보여부·공시분기·항목명·값` (기존 8시트와 글자까지 동일) +
**신규 1열 `비고`**. `비고` 를 만든 근거 — 원 티켓 §"tier2 4개사 이상치" 절 자신이 "각 시트에
주석/신뢰도 열을 두고... 숫자만 떼어가도 한계가 같이 간다는 조건을 만족해라" 라고 명시적으로
요구했다. 시트 상단 한계표기 행은 "숫자만 떼어가도" 조건을 못 만족해(필터링하면 빠짐) 셀 단위
`비고` 로 구현. 값이 없는 행은 빈 문자열(공란) — `NUMERIC_COLS`/`TEXT_COLS` 변경 없이 `coerce()`
의 기존 else-분기(문자열)로 자동 처리되어 다른 시트에 영향 없다.

- `기본자본소진율`(← kics_tier1_utilization.json): 390행 = 39개사 × 10항목명, 공시분기="2026.1Q" 고정.
  `tier1_hybrid_excess_eok` 는 39/39 전부 null 이라 드롭(정보량 0), `utilization_pct_raw` 는
  `utilization_pct` 와 39/39 바이트단위 동일이라 드롭(순수 중복) — 둘 다 실측 확인 후 제외.
- `보완자본소진율`(← kics_tier2_utilization.json): 546행 = 39개사 × 14항목명(구 산식
  `proxy_utilization_pct` 포함, 참고용으로 유지 + 비고).
- `자본비율전망`(← kics_forward_capital.json): 2090행 = 38개사(`status=="ok"` 만) × 5개년(2026~2030)
  × 11항목명. `baseline`/`baseline_2025_4Q` 딕셔너리는 **행으로 안 냈다** — item1/14/27 로 이미
  "K-ICS공시" 시트에 2026.1Q 로 존재해 중복이고, 이걸 냈으면 같은 회사 공시분기 칸에 "2026.1Q"
  와 "2026" 이 섞였을 것(2번 항목 참조). `scr_interp_progress`(연도의 순수 재진술)와
  `capacity_exhausted`/`basic_capacity_exhausted`(불리언)도 행 대신 해당 연도 비고에 접힘.

`티커`/`생손보여부`는 새 레지스트리를 안 만들고 `kics_disclosure.json` 에서 `원보험사코드` 로
조회해 채웠다 — 실측: tier1/tier2 39개사·forward 38개사 전원이 이미 그 파일의 `원보험사코드`
전체집합의 부분집합(`probe_20260829_capital_masters_census.py` 실행 결과, `t1codes.issubset(codes_all)
== True`). 비상장사는 기존 관례대로 티커="X"(null 아님, 예: 라이나생명보험·에이아이에이생명보험).

### 2) `export_public_sheets.py:41-44` 정렬 우려 — 확인 결과: 내 설계엔 해당 없음

그 스크립트의 `_QUARTER_RE = r"^\d{4}\.\dQ$"` 는 "annual (filings skim)" 류 **비표준(알파벳 포함)**
라벨이 분기범위(min/max) 계산에서 문자열정렬로 오판되던 걸 막으려고 2026-08-28 에 이미 고쳐진
필터(패턴 불일치 값은 그 min/max 계산에서 조용히 제외, 크래시·오판 없음) — 그리고 이 스크립트
자체가 원 티켓이 명시한 "범위 밖"(`public_exports/*.csv` 는 designer 소관 후속)이라 이번 배선과
무관하다.

내 설계에서 실제로 검토가 필요했던 지점은 **같은 회사 안에서 `공시분기` 포맷이 섞이는지**였다 —
`"2026.1Q"`(분기) 와 `"2026"`(연도) 를 같은 열에 같이 넣으면 `"2026" < "2026.1Q"`(문자열 비교)라
연말 전망(2026년치)이 분기 baseline(2026.1Q)보다 알파벳순으로 앞에 오는 왜곡이 생긴다. 위 1)에서
baseline 행을 아예 안 낸 것이 이 문제의 실제 회피책이다 — `자본비율전망` 시트의 `공시분기` 는
`"2026".."2030"` **순수 4자리 연도 문자열만** 담고, 다른 포맷과 섞이지 않는다(실측:
`probe_20260829_flatten_smoke.py` 출력 `distinct 공시분기 values: ['2026','2027','2028','2029','2030']`).
`sync_master_xlsx_sheet.py` 자체의 `norm()`(행 식별 키 정규화)도 순수 숫자 문자열을 int 로 정규화해
Excel 왕복 후에도 동일 키로 인식하므로 이 열은 어느 경로로도 안전하다.

### 3) census 실측 — **"tier2 4개사 이상치" 전제가 stale 로 확인됨** (추정 아님, 재현 가능)

**tier2(`kics_tier2_utilization.json`, 2026.1Q, 39개사) 는 현재 `utilization_pct` 기준 0~100%
밖 이상치가 0건이다.** 재현: `probe_20260829_capital_masters_census.py` 실행 →
`outliers (utilization_pct, primary numerator/SCRx50%): 0`. 라이브 게이트로도 재확인:
`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py` →
`4. DOMAIN IDENTITY (capital recognition-limit 분모=SCR×50% / 소진율≤100%)   RED=0  YELLOW=2`
(그 2건도 CSM_waterfall/ifrs17 레인 건, tier1/tier2 findings 는 0건).

원 티켓의 "38개사 중 34개사만 0~100%, 4개사는 분자 파서 추출 불안정" 은
`output/tier2_utilization/outlier_report_20261Q.json`(**mtime 2026-06-16**, 5개사 —
동양생명240.23%·하나손해보험234.91%·KB손해보험218.42%·악사손해보험196.78%·미래에셋생명126.45%)와
정확히 일치한다 — 즉 **2026-06-20 에 이미 고쳐진 상태를 가리키고 있다.**
`inbox/_resolved/20260620T0238Z__owner__MULTI__capital_securities_issuance_from_dart.md`:
분자를 item3-proxy 에서 DART 채권별 발행잔액으로 교체 + "data-contract gate RED 4→0(동양240%/
KB218%/미래126% proxy + 신한이지 denom 전부 해소)". 그 구 산식 값은 지금도 JSON 에
`proxy_utilization_pct` 필드로 남아 있다(정의부 자체가 `"replaces": "broken proxy... 동양240%/
KB218% artifact"` 라고 명시) — 시트엔 `보완자본 소진율(구 산식, 참고용)` 행으로 넣고 비고에
동양/KB 실측치와 폐기 사유를 그대로 적었다.

**내가 한 일: 없는 4개사를 지어내 캡션을 붙이지 않았다.** 대신 census 로 실제로 살아있는 한계만
표기했다:
- tier1 `issued_source=="missing"` **7개사**(실측): 롯데손해보험·삼성화재해상보험·KB손해보험·
  미래에셋생명보험·에이아이에이생명보험·동양생명·농협생명보험(KR0003·KR0008·KR0010·KR0079·
  KR0080·KR0087·KR0104) — 신종자본증권 발행잔액이 DART 채권별 공시에서 못 잡혀 BS 경과조치
  인정액으로 대체됨. `기본자본소진율` 시트의 해당 3항목명(발행잔액/인정액/소진율) 행에 비고.
- forward 콜옵션 미공시 폴백 **20개사**(census, `data/bonds/capital_securities_fy2025.json` 의
  `call_source != "disclosed"` AND `outstanding_mn` 有 조건으로 실측 — 하드코딩 아니고
  `_call_fallback_codes()` 가 매 실행 시 그 파일에서 다시 센다): 메리츠화재해상보험·한화손해보험·
  롯데손해보험·예별손해보험·현대해상·KB손해보험·DB손해보험·NH농협손해보험·악사손해보험·
  하나손해보험·한화생명·흥국생명보험·케이디비생명보험·아이엠라이프생명보험·DB생명보험·
  푸본현대생명·동양생명·하나생명보험·KB라이프생명·농협생명보험(KR0001·KR0002·KR0003·KR0004·
  KR0009·KR0010·KR0011·KR0032·KR0049·KR0050·KR0068·KR0071·KR0072·KR0076·KR0082·KR0083·
  KR0087·KR0097·KR0099·KR0104).
- forward `confidence.level=="low"` **14개사**, `bond_coverage=="no_bonds_in_dart"` **11개사**
  (DART 자본성증권 원자료 없음 — SCR 보간만) — 전부 시트 비고에 실림.
- **커버리지 갭 발견**: 서울보증보험(KR0150) 이 tier1/tier2(39개사) 엔 있는데
  `kics_forward_capital.json`(38개사) 에는 통째로 없다 — `자본비율전망` 시트에 이 회사 행 자체가
  없다(빈 칸으로 냄, 지어내지 않음). forward_capital_simulation.py 재실행 여부는 이 티켓 범위
  밖이라 안 건드림 — orchestrator/owner 판단 필요.

### 4) 동시접근 안전성

매 sync 직전 `git status --porcelain`/`(Get-Item ...).LastWriteTime.Ticks` 로 워크북 상태 확인,
3회 전부 sync 자체 사후검증("나머지 시트는 값 기준 완전 동일") 통과 후 저장. 저장 직후 재차
`--dry-run` 3회 재실행 → 전부 `변경 셀 0 · 추가 행 0 · 삭제 행 0`(idempotent 확인). 최종
`요약` 시트 재확인: 11개 시트 합계 49,570행(기존 8개 46,544 + 신규 3개 390+546+2090=3,026 = 49,570,
`probe_20260829_xlsx_final_check.py` 출력과 일치), 전체 수식 개수 0(불변식 유지),
`손익분해PL`(ifrs17 레인이 동시 작업 중이던 시트)은 3회 sync 전부 "나머지 시트 값 동일" 판정을
통과해 무손상. `git status` 로 이번 세션이 건드린 파일이 딱 3개(위 "변경 파일")뿐임을 재확인 —
동시에 다른 레인(ifrs17/downloader)이 만든 변경분(`PL_breakdown.json`,
`data/dart/viz/pl_breakdown_master.json`, `TODO_downloader.md` 등)은 손대지 않았다.

### owner/orchestrator 재확인 필요

1. **§3 "4개사" 전제가 stale** — 위 근거로 지금은 0건이다. 다른 최신 known-issue 를 염두에 둔
   것이었다면 알려달라(재조사한다). 아니라면 이 판정으로 종결.
2. **서울보증보험(KR0150) forward_capital 커버리지 결측** — 새로 발견한 갭, 이 티켓 범위 밖이라
   손 안 댔음. 별도 발주 필요하면 알려달라.
3. **다운로드 팝업 반영(§후속)** 은 원 티켓 그대로 orchestrator 가 designer 에 별도 발주.

## 답변 추가 (coordinator 검토 후속 — 기본자본소진율 100%초과 13행 비고)

코디네이터 검토: 스키마·행수·타시트 무손상 전부 통과, tier2 구산식 참고용 분리 처리를 긍정 평가.
지적 2건 반영 완료.

**근거 확인부터**: `docs/tier1_hybrid_utilization_definition.md`("왜 캡이 없나"·"소진율 필드 의미"
절, owner 2026-06-14/2026-08-25 결정)를 다시 읽어 추측 없이 그대로 인용했다 — 분자(DART 발행
인정액)·분모(K-ICS 공시 SCR 기반 한도)가 서로 독립 소스라 설계상 100%로 안 묶인다는 것,
`utilization_pct_strict`(SCR×10%, KIRI p12 비조건부 원칙한도)가 `utilization_pct`(SCR×15%,
조건부자본증권 인정 시 상향한도)의 정의상 1.5배라는 것, 화면은 `100%+`로 표기한다는 것,
과거 이 값을 `min(100)`으로 캡했다가 6사가 화면에서 평평해져 owner 가 캡을 없앤 사고 이력까지
전부 그 문서에 sourced.

**census 재확인**(`scripts/_probes/probe_20260829b_tier1_strict_list.py`): `utilization_pct`>100
6개사(NH농협손해보험192.9·하나생명보험187.0·하나손해보험144.1·코리안리재보험139.8·한화생명138.5·
케이디비생명보험113.4) + `utilization_pct_strict`>100 7개사(위 6개사 + **교보생명보험**, 이 회사만
primary=79.4≤100 인데 strict=119.1>100 — "엄격만 초과" 케이스). 6×2행 + 1×1행 = **정확히 13행**,
코디네이터가 말한 숫자와 일치. 비율은 6사 전부 실측 1.5000~1.5005(반올림 오차, 문서의 "1.5배"
주장과 일치).

**구현**(`scripts/build_master_xlsx.py::_flatten_tier1`, `_TIER1_BASIS_NOTE`/`_TIER1_OVER100_NOTE`
신설): 항목명(행 식별키)은 안 건드리고 `비고`만 채웠다 — ①`기본자본 소진율`/`기본자본 소진율(엄격)`
두 항목명 **전체 78행(39개사×2)** 에 "분모가 SCR×15% vs SCR×10%로 다르고 그래서 엄격이 1.5배"
설명을 상시 부착(코디네이터 지적 2번 — "같은 회사에 192.9와 289.4가 나란히" 문제는 초과 여부와
무관하게 구조적이라 전체에 적용), ②가 값>100인 **정확히 13행에만** "파싱오류 아님 + 100%+"
문구를 " / " 로 이어붙임(코디네이터 지적 1번). 두 조건 모두 하드코딩 회사목록이 아니라
`r.get(field) > 100.0` 을 flatten 시점에 직접 판정 — 다음 분기 데이터가 바뀌면 자동으로 따라간다.
기존 issued_source=missing 비고(7개사)와 충돌하는 자리는 " / " 로 3개까지 이어붙임(예: 동양생명
`기본자본 소진율` 행 = 발행잔액대체 note + 기준설명 note).

**검증**(`scripts/_probes/probe_20260829c_tier1_note_check.py`): 소진율 관련 78행 전수 스캔 —
빈 비고 0건, 값>100인 행 정확히 13건 전부 100%+ 문구 포함, 값≤100인 행 중 그 문구가 잘못 붙은
사례 0건, 전체 행수 390(불변, 순수 값 편집이라 스키마 변경 없음). NH농협(둘 다 초과)·교보생명
(엄격만 초과)·흥국화재(둘 다 이하)·동양생명(3중 concat) 4가지 케이스 전부 눈으로 재확인.

**xlsx sync**: `기본자본소진율` 만 재실행(tier2·forward 는 안 건드림) — dry-run 에서 정확히
`변경 셀 78 · 추가 행 0 · 삭제 행 0`(항목명 불변이라 delete+insert 없이 순수 EDIT), 실행 후
"검증 OK — 나머지 시트 값 동일". 3개 시트 전부 재-dry-run 해 idempotent(변경 0) 재확인, 요약
시트 행수·수식개수(0)·시트순서 전부 불변.

**커밋**: 요청대로 `git add` 로 이 세션이 만들거나 고친 파일만 스테이징(아래) 후 커밋, `git add -A`
안 씀, push 안 함. `insurequant_master_tables.xlsx` 는 바이너리 특성상 부분 스테이징이 불가능해
파일 전체를 올렸다 — 현재 바이트는 이 세션의 3개 sync 호출(신규시트 3개+비고패치) 전부와, 그
이전에 이미 반영돼 있던 다른 레인의 자체 sync 결과물(예: 손익분해PL)이 섞여 있지만, 매 sync 가
자기 실행마다 "나머지 시트 값 동일"을 저장 직전에 검증하므로 파일 상태 자체는 일관됨(요청
문구 그대로 "sync 사후검증이 통과한 상태 그대로").

## 답변 마무리 (이어받은 세션 — 커밋 실행, 2026-08-29)

세션 중단으로 커밋 직전에 멈춘 상태를 이어받았다. **처음부터 다시 하지 않았다** — 위 두
`## 답변` 절의 작업(신규 시트 3개 + 100%초과 13행 비고)은 이미 워킹트리에 반영돼 있었고,
아래는 그 상태를 그대로 신뢰하지 않고 새 세션에서 직접 재확인한 결과다.

### 독립 재검증 (신규 세션, 재실행 기준 — 두 개의 서로 다른 경로로 확인)

1. `probe_20260829c_tier1_note_check.py` 재실행(FLATTEN 함수 출력 기준): 소진율 78행 전부
   비고 non-empty, 값>100 정확히 13행 전부 "100%초과는 파싱오류 아님" 문구 포함, ≤100행 중
   오탐 0건 — 이전 세션 보고와 동일하게 재현됨.
2. **xlsx 실물 파일에서 직접 재확인**(FLATTEN 함수가 아니라 저장된 바이트 기준, 신규
   `probe_20260829d_xlsx_disk_note_verify.py` — openpyxl로 `insurequant_master_tables.xlsx`의
   `기본자본소진율` 시트를 열어 셀을 직접 읽음): 결과 동일 — 78/78 non-empty, 13/13 over-100
   문구, 오탐 0. 13행 전부 원 티켓 예시와 일치: NH농협손해보험(192.9/289.4)·
   하나생명보험(187.0/280.6)·하나손해보험(144.1/216.2)·코리안리재보험(139.8/209.7)·
   한화생명(138.5/207.8)·케이디비생명보험(113.4/170.1)·교보생명보험(엄격만 119.1).
3. `sync_master_xlsx_sheet.py --dry-run` 을 3개 신규 시트 전부 재실행 → 셋 다
   `변경 셀 0 · 추가 행 0 · 삭제 행 0`(기본자본소진율 390→390, 보완자본소진율 546→546,
   자본비율전망 2090→2090) — **xlsx가 이미 목표 상태와 완전히 일치해 이번 세션에서 추가
   쓰기가 필요 없었다** (파일 저장 없이 읽기전용 재확인만 함). `probe_20260829_xlsx_final_check.py`
   재실행으로 시트 순서(12개, 신규 3개 포함)·전체 수식 0개·요약 시트 합계(49,570 = 기존
   8시트 46,544 + 신규 3시트 390+546+2090)도 재확인.

### 커밋 범위 판정 — 워킹트리에 섞인 다른 레인 변경분 제외

이 시점 워킹트리에는 ifrs17 레인(예실차/OCI 작업, PL_breakdown 관련 .bak 3종),
validation 레인(`scripts/prepush_check.py`·`tests/test_push_gate_wiring.py`·
`inbox/validation/20260829T0300Z` golden-input-fingerprint 게이트 및 그 증거수집 스크립트
`scripts/_probes/probe_20260829_trace_builder_reads.py`+`data/_derived/_probe_builder_reads/`+
`tests/fixtures/builder_read_traces/`+`tests/test_golden_input_fingerprint.py`+
`scripts/validate_golden_input_fingerprints.py`), designer 레인(`inbox/designer/20260829T0700Z`,
`IFRS17.html`), downloader 레인(`TODO_downloader.md`, `scripts/download_disclosure_2026q2_nonlife.py`)
의 미커밋 변경이 섞여 있었다. `probe_20260829_trace_builder_reads.py`는 파일명 프리픽스가
같은 날짜(`20260829`)라 내 것으로 오인하기 쉬웠지만 실제로 열어 확인한 결과
golden-input-fingerprint 게이트(validation 레인)의 증거수집 스크립트였다 — 이 티켓과 무관해
커밋에서 제외했다. `CLAUDE.md`도 diff가 validation 레인의 골든 실측시간 정정(8분) 내용이라
제외.

### 커밋

`git add`로 아래 4개 기존파일 + 6개 신규파일만 스테이징(`git add -A` 안 씀):
`scripts/build_master_xlsx.py`·`scripts/sync_master_xlsx_sheet.py`·
`insurequant_master_tables.xlsx`·`TODO_parser_kics.md`·
`scripts/_probes/probe_20260829_capital_masters_census.py`·
`scripts/_probes/probe_20260829_flatten_smoke.py`·
`scripts/_probes/probe_20260829_xlsx_final_check.py`·
`scripts/_probes/probe_20260829b_tier1_strict_list.py`·
`scripts/_probes/probe_20260829c_tier1_note_check.py`·
`scripts/_probes/probe_20260829d_xlsx_disk_note_verify.py`(신규, 이번 세션 재검증용).

**커밋 해시: `4092a0a`** (브랜치 `fix/csm-product-segmented-columns`, push 안 함).
`git diff --cached --stat` 확인: 10 files changed, 771 insertions(+), 5 deletions(-).

### owner/orchestrator 재확인 요청 3건 — 이번 발주로 전부 처리/이관됨

원 `## 답변` 절이 올렸던 3건은 이번 오케스트레이터 발주 자체가 답을 줬다 — 이 세션에서
새로 판단한 것은 없음:
1. "tier2 4개사" stale 전제 — 이번 발주문이 "tier2 구 산식을 참고용으로 남기며 비고에
   폐기 사유를 박은 처리도 확인했다"고 명시해 재확인 완료로 처리.
2. 서울보증보험(KR0150) forward 커버리지 결측 — 이번 발주문이 명시적으로 "이번에 손대지
   마라, owner가 보증보험 전문사라 정당한 미해당일 가능성으로 보고 보류했다"고 지시.
3. 다운로드 팝업 반영 — `inbox/designer/20260829T0700Z__orchestrator__MULTI__item32_waterfall_plus_new_sheets.md`
   로 이미 별도 발주됨(파일 존재만 확인, designer 소관이라 내용은 안 열어봄).

**status: resolved** → `inbox/_resolved/`로 이동.
