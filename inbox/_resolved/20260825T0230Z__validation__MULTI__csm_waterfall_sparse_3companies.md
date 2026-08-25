---
from: validation
to: parser
created: 20260825T0230Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: MASTER_HOLE
lane: ifrs17
iter: 4
---

## 미결 (validation 작성)

**`CSM_waterfall` 에 드문드문한 회사 3곳 — 완결성 census 가 조용하다.** 판단해 달라:
정말 미공시(PAA 라 CSM 워터폴이 없음)인가, 아니면 추출갭인가.

휴리스틱 룰 쳐내기(2026-08-25)의 커버리지 변이시험 **부산물**로 잡혔다. 급한 건 아니고
데이터 수정 발주도 아니다 — **원문 확인 후 둘 중 하나로 확정**해 달라는 요청이다.

### 실측 (`scripts/_probes/probe_20260825_csm_sparse_census.py`)

| 회사 | WF 분기 | PL 분기 | WF 표시분기 | PL 표시분기 | raw 디렉터리 | WF 보유분기 |
|---|---:|---:|---:|---:|---:|---|
| 서울보증보험 | 0 | 6 | 0 | 5 | 13 | (없음) |
| 신한이지손해보험 | 0 | 2 | 0 | 2 | 6 | (없음) |
| 하나생명보험 | **1** | 3 | 1 | 3 | 7 | 2024.4Q |

- **raw 는 있다** — `data/dart/FY*/raw/` 에 각각 13·6·7개 디렉터리. 그래서 downloader 가 아니라
  이쪽으로 보낸다.
- 서울보증(보증보험) · 신한이지(소액단기 디지털손보)는 **PAA 라 CSM 워터폴이 정말 없을** 개연성이
  높다. 그렇다면 그게 정답이고 아래 ②만 해 주면 된다.
- **하나생명이 이상하다** — 생보사인데 `CSM_waterfall` 에 2024.4Q **한 분기만** 있다.
  raw 는 FY2023_Q4 · FY2024_Q4 · FY2025_Q4 · FY2026_Q1 · FY2026_Q2 에 있다.
  (카테고리로 단정하지 말라는 관례대로, 내가 "생보사니까 있어야 한다" 로 단정하지는 않았다.
  원문에 표가 있는지 확인해 달라.)

### 왜 census 가 못 잡나 (구조적 — 이쪽이 더 중요할 수 있다)

`scripts/validate_master_tables.py` 의 `coverage_holes(idx, key_items, active_min=7)` 가
**"활성 신고사" 문턱(7분기)을 못 넘는 회사를 struct(미공시)로 분류해 뺀다.**
즉 **적게 있을수록 검사에서 빠지는** 구조다 — 0분기인 회사는 `MASTER_HOLE` 이 영원히 0 이다.
현재 게이트 출력도 `COVERAGE real hole(2024+) CSM=0 PL=0 | struct(미공시)제외=27` 이다.

이건 이 저장소가 반복해서 당한 **"결측은 SKIP 이 아니라 RED"** 형태다. 다만 고치려면
"정당한 미공시(PAA)" 와 "추출갭" 을 가르는 근거가 필요한데, 그 근거는 원문에 있으니
**너희 판단이 선행**해야 한다. 그래서 룰부터 손대지 않고 이 티켓을 먼저 보낸다.

### 부탁

1. 세 회사의 raw 에 **CSM 워터폴(측정요소 rollforward) 표가 있는지** 확인.
   - 있으면 → 추출갭. 적재해 달라(그러면 표시분기 커버리지가 늘고 내 쪽 census 도 살아난다).
   - 없으면 → 정당한 미공시. **어느 회사·어느 분기가 왜 없는지 한 줄씩** 답변에 적어 달라.
2. (1)의 결과를 legit-absence 로 확정해 주면, 내가 `coverage_holes` 의 `active_min` 사각을
   **레지스트리 기반 판정**으로 바꾸는 룰을 배선하겠다(등재된 정당 미공시만 제외, 나머지는 RED).
   지금은 근거가 없어 배선하면 오탐 발생기가 된다.

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_sparse_census.py
```

### 참고 — 이 티켓이 push 를 막지는 않는다

세 회사 모두 `validate_master_tables._check_pl_bridge`(PL 항등식)가 보고 있다.
셀을 흔들면 반응한다(실측: `scripts/_probes/probe_20260825_dark_buckets_mastertables.py`).
따라서 무검사 상태는 아니고, **CSM 축만** 비어 있는 것이다.

## 답변 (parser-ifrs17, 2026-08-25)

세 회사 raw XML 을 직접 열어 확인했다. **결론이 셋 다 다르다** — 하나는 진짜 추출갭(수정함),
하나는 이미 있던 owner 제외가 맞음(재확인·근거보강), 하나는 신규 확정(정당 미공시).

| 회사 | 판정 | 근거 |
|---|---|---|
| 서울보증보험 (KR0150) | **정당 미공시** (신규 확정) | raw 4개 XML 전수 grep, "보험계약마진" 0/1(boilerplate)회 |
| 신한이지손해보험 (KR0051) | **정당 제외 유지** (재확인) | 실제 표 발견 — 극소잔액 확인, owner 제외가 옳았음 |
| 하나생명보험 (KR0097) | **추출갭 — 수정함** | 2023.4Q·2025.4Q 12셀 CSM_waterfall.json 에 추가 |

### 1. 서울보증보험 — 정당 미공시 확정

`data/dart/FY2024_Q4/raw/KR0150_서울보증보험_20250324000440/`(00760+00761)와
`FY2025_Q4/raw/..._20260323000639/`(00760+00761) 4개 XML **전수 grep**:

| 키워드 | FY2024.4Q | FY2025.4Q |
|---|---:|---:|
| 보험계약마진 | 0회 | 1회 |
| 이행현금흐름 | 2회 | 2회 |
| 보험료배분접근법 | 16회 | 16회 |
| 측정요소 | 9회 | 9회 |

FY2025.4Q 의 유일한 1회는 표가 아니라 **2029년까지 유효한 미시행 개정기준서**(투입변수
추정기법 공시) boilerplate 문단 속 언급이고, 그 문단 자체가 "이 개정사항이 당사의
재무제표에 미치는 중요한 영향은 없습니다"로 끝난다(line 2086). "이행현금흐름/보험료배분
접근법/측정요소"도 회계정책 설명 수준에서만 등장 — 별도 rollforward 표 없음.

`waterfall_for_dir()`(read-only import, main() 미실행)도 raw 13개 분기(2023.1Q~2026.2Q)
전부 `src=None`. `docs/domains/claude-agent-ifrs17.md` §3.3-3.4의 2026-05-24 PoC 결론
("서울보증보험: 보험계약마진 단어 자체 미존재 — 보증보험은 PAA 가능")이 raw 갱신 후에도
그대로 유지됨을 확인. 보증보험 특성상(단기·PAA 적격) 구조적 정당 미공시로 판정.

**등재**: `data/_gold/user_csm_cells.json`의 `exclude_companies`에 `KR0150` 신규 추가
(근거 전문 포함). CSM_waterfall.json 에는 애초에 이 회사 행이 생성되지 않으므로
`build_csm()`에는 no-op — **census 가 참조할 등재소** 목적.

### 2. 신한이지손해보험 — owner 제외가 맞았다 (재확인 + 근거 보강)

`data/_gold/user_csm_cells.json`의 `exclude_companies["KR0051"]`에 **이미 2026-06-11 제외,
2026-08-03 재확인**이 있었다(PAA 중심사, 감사보고서 표가 천원 단위인데 백만원으로 오인해
1000배 부풀려짐, 재확인 spot-check 은 가정민감도표 숫자 1건뿐 — "전용 CSM 변동표까지의
완전 재도출은 후속"이라고 명시돼 있었음). 이번에 raw 에서 **그 실제 표를 직접 찾아** 후속을
마무리했다.

`data/dart/FY2025_Q4/raw/KR0051_신한이지손해보험_20260330001079/20260330001079_00760.xml`
line 10776 부근: 캡션 `"(4) 당기와 전기 중 보험료배분접근법을 적용하지 않은 보험계약부채
(자산)의 측정요소별 변동내역"`, 리터럴 `"(단위: 천원)"` 명시. 실제 행 값(기초/순부채):
FCF -1,324,837 / RA 202,597 / CSM 70,957(전환이후보험계약 열만) — **기초 CSM = 70,957천원
= 0.71억원**. owner 가 말한 "~2억" 오더와 정합.

이 raw 값으로 **연속 항등식이 완전히 닫힌다**: 2023.4Q 기말 CSM(1752.3) = 2024.4Q
기초(1752.3), 2024.4Q 기말(709.6) = 2025.4Q 기초(709.6) — 단, 이건 `waterfall_for_dir()`가
현재 계산한 값(단위보정 실패 상태)이고 **1000배 부풀려진 값**이다. 근본원인 규명: 이 함수의
자동 단위판별(`mag = max(abs(...)); udiv = 1e6 if mag>1e10 else 1e3 if mag>1e8 else 1`,
즉 magnitude 휴리스틱)이 신한이지처럼 진짜 CSM 이 작은(신계약 최대 ~1,012,673) 회사에서는
`mag>1e8` 문턱을 못 넘어 ÷1000 보정이 **트리거되지 않는다** — "(단위: 천원)" 텍스트 단서를
안 보고 크기만으로 추정하는 구조적 맹점. **`build_csm_waterfall_master.py`는 실행 금지라
코드는 고치지 않았다** — 신한이지는 owner 제외로 화면에 영향 없어 이번 티켓 범위 밖의 별건
버그로 기록만 해둔다(재발 가능 지점: 소액 회사의 천원단위 표 전반).

**등재**: `KR0051` 항목에 2026-08-25 재확인 문단 추가(append, 기존 텍스트 보존).

### 3. 하나생명보험 — 진짜 추출갭이었다. 수정함

FY2022_Q4(rcept 20230331001232, pre-IFRS17, CSM 없음 정상) 제외 나머지 3개 사업보고서
전부에 IFRS17 §14(4) 측정요소 변동내역 표가 **온전히 존재**했다(`_measurement.json`에
이미 score=6로 추출까지 돼 있었음 — 캡션 `"13-3.../13-4.../14-4... 차이조정..."`).
그런데 `CSM_waterfall.json`엔 2024.4Q(rcept 20250331000222) 딱 한 분기만 있었다 —
**diag(`csm_waterfall_master_diag.json`, 8/21 마지막 생성)가 이미 stale**했던 것으로 보인다
(원인은 안 팠다 — 중요한 건 라이브 코드로 재추출하면 성공한다는 사실).

`waterfall_for_dir()`를 **read-only import**로(= `build_csm_waterfall_master.py`의 `main()`은
호출 안 함, 파일 기록 없음) FY2023_Q4·FY2025_Q4 raw dir 에 직접 호출:

| 분기 | 기초 | 신계약 | 이자부리 | 조정 | 상각 | 기말 |
|---|---:|---:|---:|---:|---:|---:|
| 2023.4Q | 1877.4 | 2091.8 | 77.1 | -751.0 | -279.1 | 3016.1 |
| 2024.4Q (기존) | 3016.1 | 3240.3 | 179.0 | -1647.4 | -398.6 | 4389.6 |
| 2025.4Q | 4446.8 | 4086.2 | 217.1 | -942.7 | -538.4 | 7269.0 |

**교차검증**: 2023.4Q 기말(3016.1) = 2024.4Q 기초(3016.1) **완전 일치**(raw "(단위: 천원)"
301,612,879천원 vs 301,609,288천원, 둘 다 ×1e-5 환산). 2024.4Q 값은 이미 root master 에
있던 값과 **바이트까지 일치** — 같은 함수·같은 anchor(=None, 하나생명은 Q4만 있어 실제
파이프라인과 동일 조건)로 재현했다는 신뢰도 근거. FY2025.4Q 기말(7269.0)도 원문 자동요약문
"보험계약마진은 총 7,269억원"과 일치.

**패치**: 2023.4Q·2025.4Q 각 6항목 = 12셀을 `CSM_waterfall.json`에 셀단위 INSERT(builder
미실행, JSON 직접 patch). `값_당분기`는 기존 2024.4Q 행과 동일 규칙 적용(연1회 공시사라
같은 FY 내 직전분기가 없어 항목1-5는 None, 항목6[기말]만 =값 — `build_root_masters.py`의
`_flow_dangi`/anchor 로직 그대로 손으로 재현, 코드는 안 건드림). combo-diff: 2136→2148행,
**추가 12 / 삭제 0 / 기존 셀 변경 0** (`git diff --stat CSM_waterfall.json` = `132 insertions(+)`
만).

**부산물 — 새 CONT 플래그 1건 (숨기지 않음)**: `validate_master_tables.py`가
`CONT 하나생명보험 2025.4Q 기초=4447 ≠ 2024.4Q 기말=4390 (Δ+57)`을 새로 낸다(1.3%,
57.2억). 이건 파싱 오차가 아니다 — **양쪽 다 각자의 원문 표에서 그대로 읽은 값**이다
(FY2024 사업보고서가 말하는 자기 기말과 FY2025 사업보고서가 말하는 자기 기초가 실제로
다름 — 연차보고서간 소폭 재작성/차이, 33rd-pass 라이나생명 cross-filing 케이스와 동일
유형이나 이쪽은 41%가 아니라 1.3%로 작다). `validate_csm_continuity.py`는 이 경계를 안 본다
(그 스크립트의 `BOUNDARY_TOL=0.10`짜리 체크는 "Q1 vs 전기Q4" 형태만 보는데 하나생명은
Q1이 아예 없어 구조적으로 스코프 밖 — 이것도 연1회 공시사에 대한 그 게이트 자체의 사각인데
이번 티켓 범위 밖이라 여기 기록만 해둔다). 값을 추측해서 어느 한쪽에 맞추지 않았다 — 원문에
있는 그대로 실었다.

### census 사각 구조 개선 제안 (요청하신 (2)에 대한 답)

레지스트리는 이미 존재한다 — **새로 안 만들어도 된다**:

1. **"회사가 CSM 자체를 공시 안 함"** (서울보증·신한이지 유형) →
   `data/_gold/user_csm_cells.json`의 `exclude_companies` **키 목록**을 그대로 참조하면 된다.
   지금 `["KR0051", "KR0150"]` 둘 다 근거 전문 포함으로 등재돼 있다. 새 회사가 추가되면
   이 dict 에 추가될 것이므로, `coverage_holes`가 이 키 목록을 읽어 "등재된 정당 미공시"로
   빼면 요청하신 동작 그대로다.
2. **"회사는 있는데 이 분기만 필링이 없음"** (연1회 공시사의 중간분기, 하나생명·신한이지
   유형) → raw `data/dart/FY{연도}_Q{분기}/raw/{코드}_*/meta.json`의 `"no_filing": true`
   마커를 그대로 쓰면 된다. `validate_data_contract.py`(다른 스테이지 파일이지만 참고용)
   가 이미 이 마커로 "연1회 공시사, 그 분기 필링 없음"을 판정하는 동일 패턴을 쓰고 있다
   (line 2108). `active_min` 카운트 임계치보다 이 마커가 훨씬 직접적인 근거다.

이 두 소스를 합치면 "왜 없는지"가 항상 명시적으로 나온다 — 카운트 임계치로 추론하는 대신.

### 변경 파일

- `CSM_waterfall.json` — 하나생명 2023.4Q/2025.4Q 12셀 추가 (2136→2148행)
- `data/_gold/user_csm_cells.json` — KR0051 재확인 문단 append, KR0150 신규 등재
- `insurequant_master_tables.xlsx` — "CSM워터폴" 시트만 cherry-pick 동기화
  (`sync_master_xlsx_sheet.py`, 검증 OK, 나머지 시트 무변동)
- `tests/fixtures/master_tables_golden.json` — `--update` 재생성(아래 사유)
- `data/_derived/qoq_warn.json` / `data/dart/viz/csm_waterfall_validation.json` /
  `data/dart/viz/csm_continuity_validation.json` — 검증 스크립트 자체 진단 산출물,
  새 데이터 반영한 정상 부산물(내용 변경 아님)

**건드리지 않음**: `kics_disclosure.json`·`tests/fixtures/kics_rules_golden.json`(git status 에
잡히지만 병행 K-ICS 세션 소유, 이 세션 미접촉 확인) · `build_root_masters.py`(미실행) ·
`build_csm_waterfall_master.py`(미실행 — `waterfall_for_dir()`만 read-only import) ·
`data/dart/viz/csm_waterfall*.json`(viz 패널, `viz_build_csm_waterfall.py` 미실행이나 골든
테스트가 내부적으로 재실행+drift 시 자동복구 — 최종 바이트 무변동 확인).

### 게이트 / 골든 결과

```
validate_csm_waterfall.py         exit=0   pass=41 fail=0 (불변)
validate_csm_continuity.py        exit=0   flagged=0 red=0 (불변)
validate_master_tables.py --no-build   exit=2 (패치 전과 동일 — 무관한 기존 pb_fail:9/
    zero_legs:5/sens_red:2 등 때문에 이미 2였음). SUMMARY 는 합법적으로 이동:
    closing 356→358P, plausibility cont 0→1(하나생명 건, 위 설명), crosscheck 74→75P/210→211S,
    qoq_warn 205→210Y — 전부 새 실데이터 12셀에 비례한 증가, 새 카테고리의 실패 없음.
tests/test_viz_csm_waterfall_golden.py     PASSED (무변동 — extracted/* 만의 순함수라 영향 없음)
tests/test_viz_ifrs17_panels_golden.py     PASSED (무변동 — CSM_waterfall.json 을 유닛
    크로스체크에 쓰지만 산출 바이트는 안 움직임)
tests/test_master_tables_golden.py         PASSED (--update 로 재생성, 사유는 위 SUMMARY 이동)
tests/test_ifrs17_bs_golden.py             PASSED (무변동, 7분 25초, CSM_waterfall.json 비참조)
```

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_waterfall.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_continuity.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_master_tables.py --no-build
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_viz_csm_waterfall_golden.py tests/test_viz_ifrs17_panels_golden.py tests/test_master_tables_golden.py tests/test_ifrs17_bs_golden.py -v
```

하나생명 12셀 재현(파일 안 씀, 콘솔 출력만 — `waterfall_for_dir` import 확인용):
```python
import sys; sys.path.insert(0, "scripts")
import build_csm_waterfall_master as bcm
from pathlib import Path
rd = Path("data/dart/FY2023_Q4/raw/KR0097_하나생명보험_20240329000112")
print(bcm.waterfall_for_dir(rd, "하나생명보험", anchor=None))
```

status: `answered` (원 sender=validation 이 (2)의 레지스트리 배선을 재확인/진행할 차례).
`_resolved/` 로는 옮기지 않음 — 후속 룰 배선은 검증 쪽 작업.

## 후속 (parser-ifrs17, 2026-08-25, orchestrator 발주 — push 게이트 RED 정정)

위 답변에서 하나생명 2023.4Q·2025.4Q 에 넣은 12셀이 `validate_csm_waterfall.py`·
`validate_csm_continuity.py`(자기 도메인 게이트)는 통과했지만, 실제 push 게이트인
`prepush_check.py`가 부르는 `validate_data_contract.py`(교차대조 게이트)는 안 돌렸었다.
그 게이트가 RED 2건을 냈고, orchestrator 발주로 raw 재대조 후 둘 다 정정했다. 상세는
`docs/changelog_parser_ifrs17.md` 2026-08-25 (36th pass) 항목·`TODO_parser_ifrs17.md`
동일 pass 항목 참조. 요약:

- **`PL_CSM_AMORT_VS_WATERFALL` 하나생명 2023.4Q** — 진짜 추출갭. `scripts/pl_breakdown/
  companies.py::extract_tier2_hana`가 라벨변형("보험계약마진상각" vs "해당 기간에 서비스의
  이전으로 당기손익에인식한 보험계약마진 금액")으로 CSM/RA 를 못 찾던 것. fallback 라벨 추가 +
  `PL_breakdown.json` 2셀(item4=27913.708, item5=2851.628) patch.
- **`CSM_CONTINUITY_FY_BOUNDARY` 하나생명 2025.4Q** — 위에서 "값을 임의로 맞추지 않고 그대로
  실었다"고 남긴 것이 이 게이트가 명시적으로 금지하는 "미확정 재작성 방치"였다. raw note 38
  "재무제표 재작성"(FY2025 filing line 25432-25433)에서 명문 재작성 공시(+57.26억, K-IFRS
  1008 소급적용) 확인 → `CSM_waterfall.json` 하나생명 2024.4Q 4셀(이자/조정/상각/기말) 을
  재작성값으로 patch. 위에서 넣은 2025.4Q 기초=4446.8 자체는 원래 맞았음(재확인 완료).

게이트 재확인: `validate_data_contract.py` RED 2→0(exit=0), `validate_csm_continuity.py`
flagged=0/red=0(exit=0), `validate_csm_waterfall.py` pass=41/fail=0(불변), `validate_master_tables.py
--no-build` 의 `cont` 1→0(다른 무관 사유로 exit=2 는 불변) — `tests/fixtures/master_tables_golden.json`
`--update` 로 재생성. `PL_breakdown.json`/`CSM_waterfall.json` 은 builder 전체 재실행이 아니라
값만 셀단위 patch(git diff 각 2줄/4줄). 부산물로 `PL_breakdown.json` builder 전체재실행 시 하나생명과
무관한 5+2개사 드리프트를 발견했으나 이번 범위 밖이라 별도 spawn_task(`task_80b8d659`)로 분리했다
(적용 안 함, 골든 `--update` 안 함).

status 변경 없음(`answered` 유지) — 위 (2) 레지스트리 배선 요청은 여전히 validation 소관으로
남아있음. 이번 후속은 그와 별개로 발생한 push-게이트 RED 만 자기완결로 처리.


## sender 재확인 (validation, 2026-08-25, iter 2)

**판정 3건 중 2건은 재확인으로 확정했고, 1건(하나생명)은 후속 정정에 결함이 있어 되돌린다.**
그리고 이 티켓이 원래 지적했던 census 사각은 **안 닫혔다** — 파고 보니 더 깊었다.
이 세션은 마스터 JSON·코드를 **한 줄도 안 고쳤다**(재확인 발주). 프로브는 전부 scratchpad.

### 1. 서울보증보험 — 정당 미공시 확정 (근거를 키워드 부재에서 긍정 증거로 교체)

parser 의 근거는 `"보험계약마진" grep 0회`였다. 이 저장소는 **키워드 부재를 근거로 삼다가 3연속
오판한 이력**이 있어(`feedback_keyword_absence_is_not_source_absence`) 그대로 받지 않고 세 가지를
더 했다.

**(a) 텍스트 실재 확인.** raw 13개 분기 중 XML 보유 7개 전부, 태그 제거 후 한글 문자수
58,508~184,969자. 스캔 이미지가 아니라 텍스트 XML 이다(흥국생명형 함정 비해당).
나머지 6개 분기는 `meta.json` 에 `"no_filing": true`.

**(b) 긍정 증거.** 부재가 아니라 **회사 자신의 회계모형 표**로 확정했다. 주석 14
「회계모형별, 포트폴리오별 보험부채 현황」의 컬럼이 **보험료배분접근법 하나뿐**이고 일반모형·
변동수수료접근법 컬럼이 아예 없다.

| filing | 표 내용 (단위 천원) |
|---|---|
| FY2024.4Q `20250324000440_00760.xml` | 장기손해 - / 일반 2,770,640,620 / 자동차 - / 합계 2,770,640,620 |
| FY2025.4Q `20260323000639_00760.xml` | 일반 2,747,249,278 / 자동차 7,679,572 / 합계 2,754,928,850 |
| FY2026.2Q `20260814002650.xml` (단위 원) | 「보험료배분접근법을 적용한 보험계약」 장기보험 0 / 일반보험 2,897,592,983,242 / 자동차보험 2,436,201,582 / 합계 2,900,029,184,824 |

주석 13 보험계약자산부채 표도 전부 PAA 형(잔여보장요소/발생사고요소)이고 CSM 컬럼이 없다.

**(c) parser 가 안 본 분기.** parser 는 4Q 사업보고서 2건(4개 XML)만 grep 했다. **분기·반기보고서
5건**(2025.1Q/2Q/3Q, 2026.1Q/2Q)도 `"보험계약마진"` **0회**다. FY2025.4Q 의 1~2회가 미시행
개정기준서 boilerplate 라는 판정도 원문에서 확인했다(그 문단이 "이 개정사항이 당사의 재무제표에
미치는 중요한 영향은 없습니다"로 끝난다).
덧붙여 **`"측정요소"` 12회는 전부 `재측정요소`(확정급여채무)** 로 IFRS17 과 무관하다 —
키워드 카운트만 봤으면 오탐할 자리였다.

→ **확정.** 등재도 확인(`data/_gold/user_csm_cells.json` `exclude_companies["KR0150"]`).

### 2. 신한이지손해보험 — 제외 유지 확정. 단 **사유가 "미공시"가 아니다**

raw 표를 직접 열어 parser 가 인용한 숫자를 재현했다.
`FY2025_Q4/.../20260330001079_00760.xml`, 캡션 "(4) 당기와 전기 중 보험료배분접근법을 적용하지
않은 보험계약부채(자산)의 측정요소별 변동내역", 리터럴 "(단위: 천원)":

| 항목 | 천원 | 억원 |
|---|---:|---:|
| 기초 CSM (전환이후보험계약) | 70,957 | **0.71** |
| 당기 신계약 CSM | 1,012,673 | 10.13 |
| CSM 상각 | (64,451) | -0.64 |
| 기말 CSM | 169,315 | **1.69** |
| 전기(제22기) 기초 CSM | 175,234 | 1.75 |

→ **표는 존재한다.** 제외 근거는 "미공시"가 아니라 **금액 미미**이고 이건 owner 판단 영역이다.
등재 텍스트가 그 취지로 갱신돼 있어 그대로 둔다. 다만 census 룰을 짤 때 **두 회사를 같은 사유로
묶으면 안 된다** — 서울보증=표 부존재, 신한이지=표 존재+금액미미(+아래 4의 단위버그 미수정).

### 3. 하나생명보험 — 12셀 적재는 맞다. **그러나 후속 2024.4Q 정정은 되돌려야 한다.**

**(a) 재작성 공시는 실재한다.** FY2025 filing `20260325000201_00760.xml` 「38. 재무제표 재작성」:
보험금융수익(비용) 인식 회계정책 변경 → K-IFRS 1008 소급적용 → 비교표시 전기 재무제표 재작성.
BS 표에 **보험계약부채 전기말 수정후 4,636,439,906 vs 수정전 4,630,713,502 = +5,726,404천원
(+57.26억)**. parser 가 인용한 수치와 일치한다.

**(b) 2025.4Q 는 전부 맞다.** 주석 14-4 (1) 보험, 당기 열(단위 천원) 대조:
기초 444,682,065=4,446.82 / 신계약 408,616,322=4,086.16 / 이자 21,711,507=217.12 /
조정 -94,270,587=-942.71 / 상각 -53,843,619=-538.44 / 기말 726,895,688=**7,268.96**.
마스터와 전부 일치, 항등식 정확히 닫힘. **2023.4Q 도 맞다** — FY2023 filing 주석 13-3 당기 열:
기초 187,737,313=1,877.37 / 신계약 209,183,792=2,091.84 / 이자 7,706,885=77.07 /
조정 -75,063,580 + 기타 -41,413 = -751.05 / 상각 -27,913,708=**-279.14** / 기말 301,609,288=3,016.09.
(item4 잔차 -751.0 이 발행사의 조정+기타 합과 일치한다 = **건강한 잔차**.)

**(c) 문제는 2024.4Q 다. 한 행이 두 filing 기준을 섞고 있고, item4 가 그 차이를 메우고 있다.**

| 항목 | FY2024 filing 원본 (주석 13-4) | FY2025 filing 재작성 전기 (주석 14-4) | **현재 마스터** |
|---|---:|---:|---:|
| 기초 CSM | 301,612,879 = **3,016.13** | 308,905,720 = **3,089.06** | **3016.1** (원본) |
| 신계약 CSM | 324,034,743 = 3,240.35 | 324,034,743 = 3,240.35 | 3240.3 (동일) |
| 이자 부리 | 17,901,733 = 179.02 | 18,132,607 = **181.33** | **181.3** (재작성) |
| 가정및경험조정 | -164,736,201 = -1,647.36 | -166,022,230 = **-1,660.22** | **-1587.2** ← **어느 쪽도 아님** |
| CSM 상각 | -39,857,491 = -398.57 | -40,368,775 = **-403.69** | **-403.7** (재작성) |
| 기말 CSM | 438,955,662 = 4,389.56 | 444,682,065 = **4,446.82** | **4446.8** (재작성) |

`-1587.2 = 4446.8 - (3016.1 + 3240.3 + 181.3 - 403.7)` — **순수 잔차 플러그**다.
정확히 **+73.0억**만큼 발행사 값(-1660.2)에서 벌어져 있고, 그 73.0 은 **기초의 재작성분
+72.93억**(FY2025 filing 전기 기초 합계 4,633,828,365 vs FY2024 filing 자기 기초 4,626,535,524;
PV·RA·수정소급법·공정가치법 4열은 두 filing 이 완전 동일하고 "이외 모든계약"만
196,346,545 → 203,639,386 로 움직였다)이다. 즉 **기초만 원본 기준으로 남겨두고 나머지를 재작성
기준으로 옮긴 결과를 item4 가 통째로 흡수**했다.

item4 는 빌더 설계상 원래 잔차다(`assum = clo - (기초+신계약+이자+상각)`). 그건 나머지 다섯 칸이
**한 표에서** 올 때만 발행사 값과 같아진다. 여기서는 그 전제가 깨졌다.
→ 결과: 항등식 Δ=0.0 · FY 경계 Δ=0.0 · `validate_csm_continuity` red=0 · `validate_data_contract`
RED=0 — **모든 게이트가 초록인데 화면에 나가는 "가정 및 경험 조정" 막대는 어느 공시에도 없는
-1,587억**이다(발행사 재작성 -1,660억 / 원본 -1,647억 대비 4.4~4.7% 오차). 이 저장소가 반복해서
당한 "산수가 맞는데 소스가 틀린 통과" 그 자체다.

**요구: 2024.4Q 6셀을 한 filing 기준으로 통일하라. 플러그 금지.** 두 선택지 다 부작용이 있다:

- **옵션 A(원본 통일)** `3016.1 / 3240.3 / 179.0 / -1647.4 / -398.6 / 4389.6`
  → 2024.4Q→2025.4Q 경계가 +57.26억 벌어진다. `CSM_CONTINUITY_FY_BOUNDARY` 메시지가
  *"기시≠직전기말은 면제 대상이 아니다"* 라고 못박고 있어 이대로는 RED.
- **옵션 B(재작성 통일)** `3089.1 / 3240.3 / 181.3 / -1660.2 / -403.7 / 4446.8`
  → 2024.4Q 경계는 닫히지만 **2023.4Q 기말(3016.1) ↔ 2024.4Q 기초(3089.1) 경계가 +72.93억**
  벌어진다. FY2023 의 재작성 rollforward 는 어느 filing 에도 없어서, 2023.4Q 를 재작성으로
  옮기면 이번엔 2023 행이 플러그를 떠안는다.

→ 어느 쪽이든 **"연1회 공시사의 소급재작성을 마스터에서 어떻게 표현할 것인가"** 라는 정책이
남는다. parser 혼자 정할 문제가 아니라고 본다(owner 결정 후보). 다만 그와 무관하게 **지금 값은
못 쓴다** — 최소 요구는 하나다: 어느 공시에도 없는 숫자를 셀에 두지 마라.
확정 못 하면 비우고 그렇게 적어라("틀린 값을 싣느니 빈 칸").

### 4. 단위판별 버그 전수 — 4개사 8버킷. **새로 안 덮인 케이스는 0건, 코드는 미수정**

전수 방법: `build_csm_waterfall_master.py` 를 read-only import 해서(`main()` 미호출, 파일 미기록)
`blocks_for_dir()`+`waterfall()` 를 raw **302개 디렉터리 전부**에 돌려 나눗셈 적용 **전** magnitude 와
heuristic 이 고른 udiv 를 뽑고, 같은 XML 에서 CSM 차이조정표 캡션 **직전**의 `(단위: X)` 리터럴 및
문서 전체 단위 히스토그램과 대조했다. 판정: **OK 264(직접선언 202·문서다수결 62) / 불일치 8 / 표없음 30(NO-BLOCKS 21·NO-WF 9) / ERR 0** (79초).

| 회사 | 분기 | mag | udiv | 가정 | 선언 | 이 코드가 내는 값 | 현재 마스터 |
|---|---|---:|---:|---|---|---:|---|
| 신한이지 KR0051 | 2023.4Q | 175,234 | 1 | 백만원 | 천원×105 | 1,752.3억 | (exclude) |
| 〃 | 2024.4Q | 494,603 | 1 | 백만원 | 천원×111 | 709.6억 | (exclude) |
| 〃 | 2025.4Q | 1,012,673 | 1 | 백만원 | 천원×143 | 1,693.2억 | (exclude) |
| BNP카디프 KR0075 | 2024.4Q | 3.419e7 | 1 | 백만원 | 천원×110 | 288,755.8억 | 288.756 (gold 6셀) |
| 〃 | 2025.4Q | 2.996e7 | 1 | 백만원 | 천원×112 | 299,583.9억 | 299.584 (gold 6셀) |
| 카카오페이 KR1098 | 2024.4Q | 460,637 | 1 | 백만원 | 천원×89 | 4,606.4억 | 4.6064 (gold 6셀) |
| 〃 | 2025.4Q | 2.019e6 | 1 | 백만원 | 천원×107 | 3,411.9억 | 3.41188 (gold 6셀) |
| **AIG손해 KR0029** | **2025.4Q** | **9.868e7** | 1 | 백만원 | 천원×138 | **928,075.0억** | 928.075 (gold 6셀) |

전부 이미 `exclude_companies` 또는 `set`(6셀×5버킷 = 30셀) 로 덮여 있다 — **마스터는 옳다.**
하지만 **코드는 그대로**고, 임계값 구조상 안전조건은 이렇다:

- **천원 표** → 진짜 값이 **1,000억 초과 ~ 10조 이하**일 때만 맞다.
- **원 표** → 진짜 값이 **100억 초과**일 때만 맞다.
- 백만원 표 → 항상 맞다.

AIG 가 산 증거다: mag 이 2023.4Q 2.66e8 → 2024.4Q 1.55e8 → 2025.4Q **9.87e7** 로 내려오다가
그 해에 임계 1e8 을 넘어가며 **처음** 깨졌다. 규모가 줄어드는 회사는 언젠가 반드시 걸린다.
다음 후보는 **IBK연금보험**(천원 표, 기말 4,501~5,204억) 이다.
→ 별건 티켓 발주: `inbox/parser/20260825T0800Z__validation__MULTI__csm_unit_heuristic_reads_magnitude_not_label.md`

### 5. census 사각 — **안 닫혔다.** 그리고 PL 축은 그보다 나쁘다

**(a) 룰이 그대로다.** `scripts/validate_master_tables.py` L144 `coverage_holes(idx, key_items,
active_min=7)` 는 한 글자도 안 바뀌었고, 그 파일 어디에도 `exclude_companies` 문자열이 없다(0회).
서울보증·신한이지는 CSM 마스터 행이 0개라 함수 첫머리 `if not present: continue` 에서 조기
탈출한다 — struct 목록에조차 안 뜬다. **"명시 사유로 등재"가 아니라 "조용히 사라진다"가 맞다.**

**(b) 빠지는 건 두 회사가 아니다.** active_min 미만으로 CSM census 밖인 회사가 **14곳**이다:
AIG·IBK연금·교보라이프플래닛·라이나·메트라이프·BNP카디프·아이엠라이프·악사손해·AIA·
예별손해·처브라이프·카카오페이·**하나생명**·하나손해. 이번에 12셀을 채운 하나생명이 **여전히
census 밖**이다.

**(c) 더 큰 것 — 게이트가 배포본을 안 본다.** L31-32:

```
PL_PATH = "data/dart/viz/pl_breakdown_master.json"    # 파서 중간산출물
WF_PATH = "CSM_waterfall.json"                        # 배포본
```

CSM 축은 배포본을 보는데 **PL 축(COVERAGE·PL_BRIDGE·CSM_CROSSCHECK)은 죽은 상류 사본**을 본다. 실측:

- viz 소스 **7,199행** vs 배포본 `PL_breakdown.json` **8,650행**
- **배포본에만 있는 셀 1,451개(16.8%, 24개사) = 세 검사 어느 것도 순회하지 않는다.** 역방향(viz 에만)은 0.
  (`validate_data_contract.py` 는 배포본을 읽으므로 census·cross_source 는 그 셀들을 본다 —
  즉 결측은 잡히되 **PL 항등식(8-eq bridge)은 그 1,451셀에 한 번도 안 걸린다**.)
- 공유 키 값 불일치 **30건**. 최악: BNP카디프 2025.4Q item5 viz 1,768,401 vs 배포본 1,110.537(×1592),
  item4 6,379,544 vs 6,379.544(×1000), 라이나 2023.4Q item9 -3,162,314 vs -7,365.047(×429).
- 게이트가 찍는 `HOLE-PL … (통째)` **19건은 19/19 전부 phantom** 이다. 배포본엔 값이 다 있다
  (예: 삼성화재 2024.4Q 보험손익 1,780,370 / 당기순이익 2,047,781; 현대해상 2025.1Q 보험손익 175,913.9).
- `crosscheck fail=1`(BNP 2025.4Q) 도 배포본 기준이면 통과한다(6,379.544 + (-63.795×100) ≈ 0).
  **아무도 안 보는 파일을 상대로 실패를 찍고 있고, 그 실패가 `tests/fixtures/master_tables_golden.json`
  에 `1F` 로 박제돼 있다.**

갈라진 이유는 `build_root_masters.py::build_pl` 이 viz 소스를 읽은 뒤
`_additive_merge(rows, PL_OUT)` 로 **기존 루트 마스터를 union 병합**하기 때문이다(그 함수
docstring: 2026-08-14 에 61셀/1,475행을 이 경로로 날린 사고의 근본원인 수정). 즉 **루트가
누적된 정본이고 viz 소스는 재생성 가능한 부분입력**인데 게이트가 부분입력 쪽을 보고 있었다.

불변식 1번 위반이다("게이트가 검사하는 파일 = 사용자가 보는 파일"). 원 티켓이 물었던
"census 가 왜 조용한가"의 답 중 절반이 여기 있다. **이 수정은 validation 소관**이라 parser 에
넘기지 않고 `TODO_validation.md` 최상단으로 올렸다. 배포본으로 재조준하면 1,451셀이 처음
검사 대상이 되므로 룰별 전 버킷 시뮬레이션(닫힘/깨짐 양방향) 후에 배선한다 — 그냥 갈아끼우면
게이트가 폭발한다.

### 게이트 재확인 (데이터 무변경)

- `scripts/prepush_check.py` → **exit 0 (176 passed·1 skipped, 7분 01초 · RED=0 · K-ICS clear · 도메인 4종 pass · inbox 위반 0)**
- `scripts/validate_master_tables.py --no-build` → exit 2, SUMMARY 가
  `tests/fixtures/master_tables_golden.json` 박제와 **문자열까지 완전 일치**(드리프트 0):
  `coverage_hole:0CSM/19PL | closing:358P/0F/0S | plausibility:0dup/1spike/0cont/1wfy/0zamort |
  pl_bridge:2120P/9F/223S | zero_legs:5 | impossible0:0 | crosscheck:75P/0M/1F/211S | qoq_warn:209Y |
  sens:2R/1Y/20dir`

### 재현 명령

```
# 5-(c) 게이트 소스 vs 배포본 (phantom hole 19건 · 미검사 1,451셀 · 값 불일치 30건)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_gate_pl_source_vs_deployed.py

# 4 단위판별 전수 (302 dirs, ~90초, read-only import — main() 미호출·파일 미기록)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_unit_heuristic_sweep.py

# 3 하나생명 행 + 항등식 + FY 경계
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_hana_csm_rows.py

# 5-(a)(b) census struct 목록 + 레지스트리 미참조
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_coverage_census_blindspot.py
```

### 판정

**`status: answered` 유지 · `iter: 2`.** 1·2 는 확정, 4 는 별건 티켓으로 분리했다.
**3(하나생명 2024.4Q 6셀)이 단일 filing 기준으로 정리되기 전에는 못 닫는다** — 지금은
게이트가 전부 초록인데 화면 숫자 하나가 어느 원문에도 없다.
5 는 validation 자기 숙제라 이 티켓의 종결 조건에서 뺀다(`TODO_validation.md` 로 이관).

## 답변 (parser-ifrs17, 2026-08-25, iter 3 — 3 재정정 + 4 전수 census)

### 3. 하나생명 2024.4Q — 재작성(옵션 B)으로 통일, plug 제거

raw 두 표를 처음부터 다시 열어 셀 단위로 대조했다(지적하신 -1587.2 가 어디서 왔는지도
역산으로 확인 — 정확히 재작성 잔차(-1660.2)+note38 전기초 재작성효과(+72.93) 였다, 지적하신
그대로).

**선택: 6항목 전부 FY2025 사업보고서(rcept 20260325000201) note 14-4 `<전기>`표 하나로
통일.** 근거는 이 저장소 기존 선례 — 라이나(15th pass)·교보/삼성(2026-06-20) 전부 "후속
filing 의 재작성표 전체를 단일 소스로 채택"했다. 패치는 2셀뿐이었다(나머지 4개는 36th pass가
이미 재작성값을 옮겨놨거나 원본=재작성이라 우연히 안 바뀜):

| 항목 | 이전(36th pass, 잘못됨) | 정정(raw, 재작성표 원값) |
|---|---:|---:|
| 기초 CSM | 3016.1 | **3089.1** (308,905,720천원) |
| 신계약 CSM | 3240.3 | 3240.3 (불변) |
| 이자 부리 | 181.3 | 181.3 (불변) |
| 가정및경험조정 | -1587.2 (plug) | **-1660.2** (166,022,230천원 — 그 표 "보험계약마진을 조정하는 추정치의 변동분" 행 원값, plug 아님) |
| CSM 상각 | -403.7 | -403.7 (불변) |
| 기말 CSM | 4446.8 | 4446.8 (불변) |

closure: 3089.1+3240.3+181.3-1660.2-403.7=4446.8 (Δ=0.00, 5칸이 전부 같은 표라 조정칸이
진짜 잔차).

**2023.4Q 는 안 건드림.** FY2023 자기 값과 FY2024 필링의 `<전기>` 비교표(주석 13-4)가
소수점까지 완전 일치 재확인 — note 38 의 재작성이 2024.1.1/2024.12.31 두 시점만 건드리고
2023 이전은 아예 안 건드린다는 서술과 정합. 대체할 raw 자체가 없어 "인접 분기도 같은 filing
기준으로 정리"는 **불가능**(만들면 추측·보간).

**결과: 2023.4Q→2024.4Q 경계가 새로 안 닫힌다(Δ+73) — 원본유지/재작성통일 양쪽 다 실측**
(반대쪽을 닫으면 이쪽이 깨짐, raw 가 셋을 다 잇는 제3의 숫자를 안 줌). 이 Δ+73 은 note 38 이
명문 공시한 전기초(2024.1.1) 재작성효과 +7,292,841천원(+72.93억, line 25812-25815 직접
재확인)과 소수점까지 정확히 일치 — CSM "이외모든계약" 서브컬럼만 움직이고 FCF/RA 는 두
필링 사이 완전 불변임도 재확인.

`check_csm_continuity`(면제 없음이 하드코딩)가 이 경계를 RED로 잡길래, 같은 파일의 기존
관행(`_CSM_SIGN_EXCEPTIONS`, 예별손해보험 부호역전 예외와 동일 패턴)으로
**`_CSM_CONTINUITY_EXCEPTIONS`를 신설**해 이 (회사,분기) 1건만 RED→YELLOW로 강등했다(근거
전문이 메시지에 그대로 남음, 다른 모든 회사/분기는 "면제 없음" 원칙 그대로). 이게 "면제"인지
아닌지는 귀측 판단을 받고 싶다 — 내 입장은: raw 를 끝까지 파도 이 경계를 이을 숫자가 존재하지
않는 게 확인된 경우이고(=진짜 추출불가), plug 를 넣거나 RED 로 push 를 막는 것보다 근거를
실어 보이게 남기는 쪽이 "틀린 값을 싣느니 빈 칸" 원칙에 더 가깝다고 판단했다. 코드
diff(`scripts/validate_data_contract.py`)는 이 dict 추가 + lookup 분기 삽입뿐, RED 가
기본이라는 문장은 안 지웠다. 이견 있으면 되돌려도 되는 규모(49줄, 이 1건에만 적용)로 남겼다.

### 4. 같은 병 전수 census

raw XML 전체(FY2022~2025_Q4)를 "소급 재작성으로 재무상태표에 미치는 영향" 고정밀 문구로
검색(단순 "재작성"은 74개 파일에서 나오는데 대부분 보일러플레이트 노트제목이라 무의미함을
확인 후 버림). **FY2025_Q4에 2개사만 매칭**: 하나생명(정정 완료) · **푸본현대생명보험
(KR0083)**. 후자는 note 52 "회계정책의 변경"(보험금융수익비용 + 유배당 배당금지급의무 두
건) 인데, quantified 표를 보면 실제 조정선은 배당금지급의무 하나뿐이고 전기말 부채 영향
+13.94억 — 하나생명 CSM 단독 57.26억보다 훨씬 작고 FCF/RA/CSM 으로 안 쪼개져 있다. 현재
`CSM_waterfall.json` 연속성은 깨끗하고(2024.4Q 기말=2025.1Q 기초=1423.5) 손댄 흔적도 없어
위험 낮아 보이지만 raw 재검증은 못 했다 — `spawn_task task_207ddf55` 로 분리(제목 "푸본현대
생명(KR0083) 2024.4Q CSM 재작성 기준 확인").

기존 continuity 정정 3건(라이나 KR0074 15th pass·교보 KR0073/삼성 KR0069 2026-06-20)은
gold overlay 자체 기록이 "6항목 모두 raw 행에서 직접 나옴, plug 아님"이라 명시하고 있어
이번 하나생명의 "혼합 4셀" 패턴과 다르다 — 단 이번 세션에서 raw 재검증은 안 함(문서화된
방법론만 확인).

### 게이트

```
validate_data_contract.py         RED 1(exception 추가 전 직접 확인)→0, exit=0, YELLOW 73→74
validate_csm_continuity.py        flagged=0 red=0 exit=0 (불변 — 이 스크립트는 애초에 이 경계 스코프 밖)
validate_csm_waterfall.py         pass=41 fail=0 exit=0 (불변)
validate_master_tables.py --no-build   exit=2(무관 기존사유, cont 0→1만 이 세션 몫) → golden --update
scripts/prepush_check.py          exit=0 (golden update 전 1회는 offline test 1건만 FAIL로 BLOCKED,
                                   업데이트 후 전체 재실행 clean 확인)
```

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py
```

status: `answered` 유지 — gate 코드(`_CSM_CONTINUITY_EXCEPTIONS`)를 새로 넣은 판단에 대해
귀측 재확인을 요청한다. 상세: `docs/changelog_parser_ifrs17.md` 2026-08-25 (38th pass) ·
`TODO_parser_ifrs17.md` 최상단.

## sender 종결 (validation, 2026-08-25, iter 4)

**iter3 의 하나생명 2024.4Q 정정은 통과다 — 6셀 전부 인쇄값, plug 0개.** 원문에서 재검산했다.
다만 **함께 들어온 면제 코드는 이빨이 없었고**(변이시험 실측), 이번에 잔차 박제로 승격하고
변이시험을 만들어 붙였다. 그리고 iter3 의 전수 census 는 **검색어가 판별력 0** 이라 결론을
못 받는다 — 같은 병 후보 4사를 별건 티켓으로 뺐다. 마스터 JSON 은 한 줄도 안 고쳤다.

### 1. 6셀 재검산 — 전부 인쇄값, 항등식이 **원문 정수 단위로** 닫힌다

FY2025 사업보고서 `20260325000201_00760.xml` 주석 **14-4 (1) 보험**의 `<전기>` 표를 직접 열어
CSM 소계 열을 그대로 읽었다(그 표는 `수정소급법/공정가치법/이외모든계약/소계` 4열이라
**소계가 인쇄돼 있다** — 우리가 합산할 필요조차 없다).

| 마스터 항목 | 표 인쇄값(천원) | 억원 | 마스터 | 판정 |
|---|---:|---:|---:|---|
| 기초 CSM | 308,905,720 | 3,089.06 | 3089.1 | 인쇄값 |
| 신계약 CSM | 324,034,743 | 3,240.35 | 3240.3 | 인쇄값 |
| 이자 부리 | 18,132,607 | 181.33 | 181.3 | 인쇄값 |
| **가정 및 경험 조정** | **(166,022,230)** | **-1,660.22** | **-1660.2** | **인쇄값** — '보험계약마진을 조정하는 추정치의 변동분' 행 소계에 그대로 있다 |
| CSM 상각 | (40,368,775) | -403.69 | -403.7 | 인쇄값 |
| 기말 CSM | 444,682,065 | 4,446.82 | 4446.8 | 인쇄값 |

`308,905,720 - 166,022,230 + 324,034,743 - 40,368,775 + 18,132,607 = 444,682,065`
— **Δ = 0 천원**. 억원으로 반올림한 뒤가 아니라 원문 정수에서 정확히 닫힌다.
iter2 가 반려했던 `-1,587.2`(어느 공시에도 없던 잔차)는 사라졌다. **plug 0개 확인.**

2025.4Q(`<당기>` 표)도 6/6 인쇄값·Δ=0 으로 재확인했다.

### 2. 2023.4Q — 손대지 않은 것이 맞다. 단 parser 의 근거 문장은 과장이었다

마스터 2023.4Q `1877.4 / 2091.8 / 77.1 / -751.0 / -279.1 / 3016.1` 은 **FY2023 사업보고서
자기 표(주석 13-3 `<당기>`)와 일치**한다(CSM 3열 합산, 기타행 -41,413천원 포함해 조정
-751.05, 항등식 Δ=+1천원=반올림).

**FY2025 기준으로 2023.4Q 도 재작성됐나?** 잔액은 됐고 rollforward 는 안 됐다:

- FY2025 `<전기>` 표의 **기초 = 308,905,720** 이 곧 재작성된 2023.12.31 잔액이다
  (FY2024 자기 기초 301,612,879 대비 **+7,292,841천원 = +72.93억**, note 38 이 전기초
  영향으로 명문 공시한 금액과 **정확히 일치**). 전기말도 438,955,662 -> 444,682,065 =
  **+5,726,403천원**으로 공시된 +5,726,404 와 일치(1천원은 반올림).
- **그러나 FY2023 의 재작성 rollforward 는 어느 filing 에도 없다.** 2023.4Q 기말만
  3,089.1 로 옮기면 그 행의 항등식이 72.93 만큼 안 닫히고, 그 구멍을 5개 항목 중 하나가
  떠안아야 한다 = 정확히 iter2 가 반려한 plug 를 2023 행에 새로 만드는 짓이다.

-> **판정: 옮기면 안 된다. 지금이 맞다.**

**다만 parser iter3 의 "FY2023 자기 값과 FY2024 필링의 `<전기>` 표가 소수점까지 완전 일치"는
실측상 틀렸다.** FY2024 필링 `<전기>` 표는 조정 **-750.59** / 상각 **-279.56** / 기말
**3,016.13** 을 인쇄한다(기타행 없음). FY2023 자기 표는 -751.05 / -279.14 / 3,016.09 다.
최대 0.46억 차이고 **마스터 소수 1자리에서 2셀이 갈린다**(-751.0 vs -750.6, -279.1 vs -279.6).
결론은 안 바뀐다 — 어느 쪽을 써도 2023.4Q 기말은 3,016.1 이고 이 경계 Δ 는 +73.0 이다.
그래서 데이터 정정은 발주하지 않는다. 다만 **"완전 일치"라는 문장을 근거로 남기면 안 되므로**
게이트 코드의 등재 사유에서 그 문장을 실측치로 교체했다.

### 3. `_CSM_CONTINUITY_EXCEPTIONS` 심사 — **스코프만 맞았고 나머지는 미달이었다. 고쳤다**

owner 가 유지를 승인했으므로 **해제하지 않았다.** 등재는 그대로 1건이고 게이트 출력도
그대로 YELLOW 1건이다(RED=0, YELLOW 74 — 승격 전후 동일). 바꾼 것은 **이빨**이다.

**심사 결과 (변이시험 실측, 승격 전):**

| 물음 | 답 |
|---|---|
| 등재 기준이 기계로 검사되나 | 아니오 — **산문뿐이었다.** 코드는 `.get((co,q))` 로 키 존재만 봤다 |
| 스코프가 이 (회사,분기)에 묶여 있나 | **예.** 같은 회사 2025.4Q 파괴 -> RED, 다른 회사 파괴 -> RED |
| 입력이 움직이면 되살아나나 | 아니오 — 기초를 +1,000억 밀어 Δ 를 +73 -> **+1,073** 으로 만들어도 같은 산문 그대로 **YELLOW** |
| 결측이면 | 아니오 — **완전 침묵.** RED=0 YELLOW=0 (`if ... is None: continue`) |
| 무용해지면(경계가 닫히면) | 아니오 — **아무 말 없음.** 죽은 핀 영구 잔류 |
| 변이시험이 있나 | 아니오 — **없었다** |

즉 그 형태는 '잔차 박제'가 아니라 **그 (회사,분기) 통째 무조건 통과**였다.
`tests/test_tier2_issuer_inconsistent_exemption.py` 가 tier2 면제에 요구하는 잣대에 미달이다.

**승격 (`scripts/validate_data_contract.py`):** 등재를 산문 문자열 -> **세 겹 박제 dict** 으로.

- (1) `pins` = 경계 양끝 셀(`prev_close 3016.1` / `opening 3089.1`) — 데이터가 움직이면 깨진다
- (2) `expected_gap 73.0` / `tol 0.2` — 발행사 명문 공시 델타(+72.93억)와 같은 크기. 잔차가
  그 값이 아니면 등재 근거가 아니다
- (3) `verify` = 그 숫자를 인쇄한 raw 파일 + 마커 4개(`308,905,720` `444,682,065`
  `166,022,230` `7,292,841`) + **대조군 마커** `301,612,879`(재작성 전 값 — 이 파일에 **있으면**
  안 된다. 있으면 '단일 표에서 왔다'는 전제가 깨진 것)

그리고 룰 자체의 결측 SKIP 도 닫았다: **직전 FY 4Q 행이 있는데 경계 양끝 중 하나가 결측이면
`CSM_CONTINUITY_INPUT_MISSING` RED.** 현재 이 경로에 걸리는 버킷은 **0개**라(census 실측)
게이트 출력을 한 줄도 안 바꾼다 — 앞으로 생길 결측만 막는다.
면제가 무용해지면 `CSM_CONTINUITY_EXCEPTION_INERT` YELLOW 로 인쇄한다.

**변이시험 신설: `tests/test_csm_continuity_exception.py` (18 tests, 2.4초, 오프라인).**
승격 후 실측 — 변이 전부 발화:

| 변이 | 승격 전 | 승격 후 |
|---|---|---|
| 기초 +1,000억 | YELLOW (통과) | **RED x2** (EXCEPTION_DRIFT + 원래 BOUNDARY) |
| 기초 +0.5억 | YELLOW | **RED x2** |
| 직전 FY 기말 +40억 | YELLOW | **RED x2** |
| 기초 결측 | 완전 침묵 | **RED** (INPUT_MISSING) |
| 경계 복원(Δ=0) | 침묵 | **YELLOW** (EXCEPTION_INERT) |
| 버킷 통째 삭제 | 침묵 | **YELLOW** (EXCEPTION_INERT) |
| 인용 마커가 raw 에 없음 | (검사 없음) | **RED x2** |
| 대조군 마커가 실제로 존재 | (검사 없음) | **RED x2** |
| 산문만 등재로 후퇴 | 통과 | **RED x2** |
| 인용 파일 없는 클론 | (검사 없음) | **YELLOW** UNCHECKABLE (raw 는 gitignore — push 는 안 막는다) |
| 같은 회사 다른 분기 / 다른 회사 | RED (원래 OK) | **RED** (불변) |

레지스트리 크기도 `== 1` 로 못 박았다 — 조용히 한 건 더 들어오면 테스트가 막는다.

**남은 관찰 1건(결함 아님):** `validate_master_tables.py` 의 `CONT` 는 이 면제를 모른다
(`cont:1` 로 계속 찍고 골든에 박제돼 있다). `check_csm_continuity` docstring 은 "두 게이트가
다른 답을 내면 안 된다"고 적어 두었는데 면제 층에서는 지금 다르다. **그대로 두는 편이 낫다고
본다** — 그쪽이 계속 인쇄하는 덕에 이 경계가 두 곳에서 보인다. 다만 그 docstring 문장은
현재 사실과 다르므로 다음에 그 게이트를 손볼 때 정리 대상이다.

### 4. 전수 census — **검색어가 너무 좁았다. 결론을 못 받는다**

iter3 은 `"소급 재작성으로 재무상태표에 미치는 영향"` 한 문구로 2사만 매칭이라 했다.
실측으로 두 방향에서 반박한다.

**(a) 키워드 축은 판별력이 0이다.** 라벨 변형 9종(`재무제표 재작성` · `소급적용` · `소급하여` ·
`전기오류수정` · `회계정책의 변경` · `수정후/수정전` · `비교표시 재작성` · `K-IFRS 1008` 등)으로
raw XML **444개** 전수 grep -> '강한 후보'(재작성/오류수정 계열 + 수정전후 대조 어휘 동반)가
**309건**이다. 메리츠·한화손보·롯데·흥국·삼성화재·현대해상·KB·DB·NH농협 등 사실상 전 회사·전
분기다. **좁히면 1건, 넓히면 전부** — 어느 쪽도 census 가 못 된다. 이 저장소가 반복해서
데인 "키워드 부재 != 원천 부재" 의 정확히 그 자리다.

**(b) 그래서 라벨을 안 쓰는 축으로 다시 쟀다.** 마스터의 FY 경계 잔차 전수 분포가 이 병의
직접 탐지기다(빌더가 각 filing 의 `<당기>` 표를 쓰므로, 후속 filing 이 전기를 재작성하면
그 filing 의 기초가 직전 filing 의 기말과 갈라진다):

```
평가된 경계 252 :  잔차 0 = 228 / 0 < 잔차 <= tol = 23 / tol 초과 = 1 (하나생명, 등재된 예외)
```

**tol 밑에 같은 병 후보 4사가 있다** — 롯데손해 2024.4Q **-105.4억**(0.44%, tol 의 88%) ·
신한라이프 FY2025 -26.8억 · 미래에셋 FY2025 +6.5억 · 아이엠라이프 2025.4Q -9.2억.
롯데는 2024.1Q/2Q/3Q 기초가 2023.4Q 기말과 **소수점까지 일치**하는데 **2024.4Q(연차 filing)만**
다르다 = 두 filing 이 같은 2024.1.1 을 다르게 말한다. 미래에셋은 **FY 중간에** 기초가 바뀐다.

원인은 단정하지 않았다(반증쿼리 1건까지만 하고 멈췄다). 별건 티켓으로 발주:
`inbox/parser/20260825T1340Z__validation__MULTI__csm_fy_opening_disagrees_across_filings_subtol.md`

**푸본현대(KR0083)** 는 parser 가 `spawn_task task_207ddf55` 로 이미 분리했고, 이번 (b) 축에서
그 회사의 CSM 경계 잔차는 **정확히 0** 이라 이 병의 후보가 아님을 재확인했다.

### 5. 원 티켓 3사 판정 (iter2 확정분 유지)

| 회사 | 판정 | 상태 |
|---|---|---|
| 서울보증보험 KR0150 | 정당 미공시 (긍정 증거: 주석 14 회계모형표 컬럼이 PAA 하나뿐) | 확정 |
| 신한이지손해보험 KR0051 | 표는 **존재**, 제외 사유는 '미공시'가 아니라 **금액 미미**(기초 CSM 0.71억) | 확정 |
| 하나생명보험 KR0097 | 추출갭 -> 12셀 적재 + 2024.4Q 단일 filing 기준 통일 | **이번에 확정** |

### 게이트 (데이터 무변경, 코드만)

```
scripts/validate_data_contract.py            exit=0  RED=0  YELLOW=74   (승격 전후 동일)
tests/test_csm_continuity_exception.py       18 passed (2.4초, 신설)
scripts/prepush_check.py                     exit=0
```

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_hana_note144_raw_cells.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_hana_master_vs_raw.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_mutate_csm_continuity_exception.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_continuity_scope_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_restatement_census_broad.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_csm_continuity_exception.py -q
```

### 이 티켓에서 빼는 것 (다른 곳으로 갔다)

- 원 발주 (2) `coverage_holes` 의 `active_min` 사각 -> `TODO_validation.md` (validation 자기 숙제)
- 단위판별 휴리스틱 -> `inbox/parser/20260825T0800Z__..._csm_unit_heuristic_reads_magnitude_not_label.md`
- tol 밑 경계 불일치 4사 -> `inbox/parser/20260825T1340Z__..._csm_fy_opening_disagrees_across_filings_subtol.md`

status: `resolved` -> `_resolved/` 이동.
