---
from: validation
to: parser
created: 20260825T0230Z
status: answered
route: reparse
company: MULTI
period: ALL
rule: MASTER_HOLE
lane: ifrs17
iter: 1
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
