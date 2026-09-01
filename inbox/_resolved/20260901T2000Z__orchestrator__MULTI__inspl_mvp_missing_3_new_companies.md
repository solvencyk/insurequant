---
from: orchestrator
to: parser
created: 20260901T2000Z
status: resolved
route: reparse
company: KR0050,KR0076,KR1098
period: 2023.4Q-2025.4Q
rule: INSPL_CENSUS_MISSING (live_artifacts)
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

owner 승인(2026-09-01)으로 **PL 마스터에 3사가 새로 들어왔다** — 하나손해보험(KR0050) ·
아이엠라이프생명보험(KR0076) · 카카오페이손해보험(KR1098). 회사수 36 → 39.

그런데 **보험손익 원표 패널(`data/dart/viz/insurance_pl_breakdown.json`)이 이 3사를 모른다.**

```
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  아이엠라이프생명보험
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  카카오페이손해보험
RED  insurance_pl_breakdown.json :: INSPL_CENSUS_MISSING  하나손해보험
```

### 왜 안 따라왔나

패널 빌더 `scripts/viz_build_ifrs17_panels.py` L1631 이 이 패널을 **PL 마스터가 아니라**
`data/dart/extracted/*_insurance_pl_mvp.json` 에서 만든다:

```python
"insurance_pl_breakdown.json": ("*_insurance_pl_mvp.json", extract_pl_breakdown),
```

그 mvp 파일은 `scripts/ifrs17_ingest_audit_annual.py` 가 만드는데, 현재 47개가 있고
**KR0050 · KR0076 · KR1098 것은 없다.** 즉 PL 마스터 경로와 패널 경로가 서로 다른
추출기를 쓰고 있고, 마스터에 회사를 추가해도 패널은 자동으로 안 따라온다.

**값이 틀린 것이 아니라 커버리지가 안 따라온 상태다.** 그래서 화면에서 이 3사는 PL 관련
어떤 자리에는 나오고 보험손익 원표에는 안 나온다.

### 지금 조치 (임시)

`data/_gold/live_artifact_baseline.json` 에 3줄 등재해 push 를 풀었다. 통째 skip 이 아니라
건별 등재이고, mvp 추출이 생기면 게이트가 `BASELINE STALE` 로 알려준다 — **그때 그 줄을
지워야 한다**(안 지우면 등재부가 거짓말을 시작한다).

### 부탁

1. 3사의 `*_insurance_pl_mvp.json` 을 만들어 달라(`ifrs17_ingest_audit_annual.py` 경로).
   회사마다 표 형태가 다르다는 것은 이미 확인됐다 — PL 마스터 쪽에 각각 독립 핸들러를 짰다
   (`_hana_sonbo_*` · `_imelife_*` · 카카오페이, `scripts/pl_breakdown/companies.py`). 그 로직이
   참고가 될 것이다.
2. 만든 뒤 `viz_build_ifrs17_panels.py` 재실행 → `validate_live_artifacts.py` 가
   `BASELINE STALE` 을 인쇄하면 등재부 3줄을 지워라.
3. 근본적으로 **PL 마스터 경로와 패널 mvp 경로가 갈라져 있는 것 자체**가 이 사고의 원인이다.
   회사를 추가할 때 둘이 같이 움직이도록 묶을 수 있는지 검토해 달라 — 지금은 한쪽만 늘려도
   게이트가 잡아 주긴 하지만, 잡히기 전까지는 화면이 불일치한다.

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
```

## 답변 (recipient 작성 — 처리 후)

### 1. mvp 파일 생성

`scripts/_probes/probe_20260901_insurance_pl_mvp_3new.py` 를 새로 짜서 3사의
`*_insurance_pl_mvp.json`(+ 짝인 `*_insurance_pl.json`)을 만들었다. `ifrs17_ingest_
audit_annual.py` 를 그대로 실행하진 않았다 — 그 스크립트는 `src.ifrs17.universe.
AUDIT_REPORT_ANNUAL` 5개사(감사보고서만 내는 외국계 생보) 전용이고 이 3사는 거기 없다.
대신 그 스크립트가 쓰는 것과 같은 패턴(raw XML에 `extract_insurance_pl_tables` 직접 호출,
universe 게이트 우회)을 3사 스코프로 복제했다. 대상은 각사 FY2025 사업보고서(DOCUMENT-NAME
`00760`, rcept 1건씩 — 다른 해는 중복 rcept 가 있어 스코프 밖으로 둠, 어차피 패널 로직이
회사당 최신 1건만 채택):

```
하나손해보험(KR0050)        rcept=20260325000538
아이엠라이프생명보험(KR0076) rcept=20260406004393
카카오페이손해보험(KR1098)   rcept=20260323001537
```

**하나손해보험만 별도 조치 필요했다.** 실제 "보험손익 상세내역" 표(주석29 — PL 마스터의
`_hana_sonbo_csm_amort`가 이미 CSM상각 21,885,413천원=218.9억으로 검증한 바로 그 표)가
`extract_insurance_pl_tables` 기본 `min_score=5` 바로 아래인 **4점**이라 mvp 0건이었다.
`min_score=0`으로 재스캔해 기존 `is_mvp_table()` 구조 게이트(slice_label/block_type/
재보험제외)만으로 골랐더니 — 3사 전체를 이 방식으로 재확인한 결과 노이즈 없이 하나손해만
실제로 2건(당기/전기) 추가되고 아이엠라이프(8건)·카카오페이(5건)는 기존 결과와 동일했다
(대조 스크립트로 직접 diff 확인).

### 2. 재실행 + 부수 발견한 버그 (당기/전기 오선택)

`viz_build_ifrs17_panels.py` 재실행 전에 `extract_pl_breakdown` 단위테스트를 먼저 돌려보니
**하나손해·아이엠라이프 둘 다 전기(과거분기) 데이터를 골랐다** — 값이 아니라 "어느 표를
고르나"의 문제였다. 원인: `pick_best_block`의 line_no 동점처리가 항상 뒤(=전기)를
고르는, 2026-08-25에 한화손해보험에서 이미 한 번 잡힌 버그(`_dedupe_prefer_current_
period`/`_PL_PREFER_CURRENT_PERIOD`)의 재발이었다 — 단 이번 2사는 그 함수의 동일-키
가정("캡션·헤더가 정확히 같다")을 깨는 새 표현형이었다:
- 하나손해: 캡션 자체가 "- 당기"/"- 전기"라 group-key 1번 요소(caption)부터 다름.
- 아이엠라이프: 캡션은 같은데 헤더 셀에 "제39(당)기"/"제38(전)기"가 박혀 있어 group-key
  2번 요소(header)가 다름. 게다가 하나손해는 후보가 score=4라 애초에 `candidates` 필터를
  못 통과해 dedup 호출 지점(필터 이후)에 도달하지도 못했다.

`scripts/viz_build_ifrs17_panels.py`를 수정: dedup을 candidates 필터 **이전**(blocks
전체)에 적용하도록 순서를 바꾸고, 캡션이 "- 당기"/"- 전기" 단독인 경우와 헤더의
"제NN(당/전)기" 태그를 정규화하는 헬퍼 2개(`_normalize_caption_for_dedup`,
`_normalize_header_for_dedup`)를 추가, 행 라벨의 공백 노이즈("소 계" vs "소계")도
비교 시 제거하도록 했다. `_PL_PREFER_CURRENT_PERIOD`에 하나손해·아이엠라이프를
추가(한화손해와 같은 명시적 allowlist 게이트 유지 — 2026-08-25에 이 dedup을 무조건
적용했다가 15개사가 다른 표로 오선택돼 되돌린 전례가 있어 그 설계를 그대로 따름).

**회귀검증**: 원본 코드(git HEAD)와 수정 코드로 기존 47사 전원의 `extract_pl_breakdown`
출력을 각각 계산해 diff — **0건 차이**. 게이트 대상인 한화손해보험도 단독으로 바이트 동일
확인. 카카오페이는 애초에 캡션에 서술형 텍스트가 남아 있어(전기 캡션이 짧은 스텁이라
score가 낮게 나옴) 기존 score 기반 tie-break로 이미 당기가 정상 선택되고 있었다 — 손대지
않음.

### 3. 결과 + 등재부 정리

`insurance_pl_breakdown.json`: 29사 → **32사**, 3사 전부 `status=ok`. 골든
(`tests/fixtures/viz_ifrs17_panels_golden.json`) `--update`로 재생성(companies
29→32, sha 변경 — 나머지 3패널은 diff 0이라 매니페스트 불변). `pytest
tests/test_viz_ifrs17_panels_golden.py tests/test_push_gate_wiring.py` = 55 passed,
1 skipped.

`validate_live_artifacts.py` 재실행 → `BASELINE STALE — 등재돼 있는데 더는 실패하지
않는다 3건`으로 정확히 이 3줄을 지목. `data/_gold/live_artifact_baseline.json`에서 그
3줄을 삭제하고, 같은 룰의 남은 7사(AIG손해보험 등 — 이들은 실제로 PL 마스터에 없어서
정당하게 빠진 것, 별개 사유) reason 문구의 "PL 마스터 36사 중 29사만" stale 수치를
"39사 중 32사만"으로 고쳤다. 재실행 결과:

```
RED=0  YELLOW(baselined)=48  STALE_BASELINE=0  총 발견=48
```

(YELLOW 는 51→48, 즉 정확히 지운 3줄만큼만 감소 — 다른 축은 안 건드림.) bs_snapshot.json·
csm_amort_schedule.json·sensitivity_heatmap.json 도 재확인했는데 이번 빌더 재실행으로
diff 0이었다 — csm_amort/sensitivity는 `ifrs17_batch_all.py` 계열(universe 게이트 없음)이
이미 이 3사를 커버하고 있었고(하나손해의 csm_amort는 `status=empty`로 이미 등재된 별개
문제, 이번 티켓과 무관 — 손대지 않음), bs_snapshot은 이 3사의 `_bs_snapshot_mvp.json`
자체가 없어 재실행해도 변화가 없었다(17BS 에이전트 소관이라 만들지 않음).

### 4. 근본원인 (3번 요청 — 판단만, 고치지 않음)

PL 마스터(`build_pl_breakdown.py::discover_filings`)는 `data/dart/FY*/raw/`를 직접
스캔하는 **self-census**라 게이트가 없다. 반면 mvp 를 만드는 4개 배치 스크립트 중
`ifrs17_batch_all.py`(CSM)만 `kics_disclosure.json` 전체를 무필터로 돌고, 나머지 3개
— **오늘 고친 P&L(archive됨) + 아직 살아있는 measurement/sensitivity/historical** —
는 전부 `src/ifrs17/universe.py::is_excluded()`를 거친다. 그 안의 `NON_LISTED_SKIP`
(2026-05-24, "정기공시 없음" 가정)에 이 3사 이름이 **이미 박혀 있었다** — 하나손해·
아이엠라이프·카카오페이손해 전부. raw 를 확인하니 FY2022 사업보고서(DOCUMENT-NAME
`00760`)부터 실재해서 그 가정은 지금 틀렸다(언제부터 틀렸는지는 미확인 — 처음부터
틀렸을 수도, 그 사이 공시 의무가 생겼을 수도 있다).

즉 사고의 표면은 "패널 하나가 새 회사를 모른다"였지만, 실제로는 **"이 레인에 회사
유니버스를 정의하는 곳이 하나가 아니라 최소 3곳(마스터 self-census / CSM 무필터 /
P&L·measurement·sensitivity·historical 용 stale allowlist)"**이다. 오늘은 P&L 패널만
겉으로 드러났지만 — 근거: NON_LISTED_SKIP 은 measurement/sensitivity/historical 도
똑같이 걸러서, 이 3사에 대해 그 세 파이프라인도 막혀 있을 가능성이 높다(미검증·미수정,
이 티켓 범위 밖 — universe.py 수정은 아직 살아있는 3개 스크립트 전체의 회귀검증이
필요해서 별도 작업으로 남긴다). 게이트 쪽도 균일하지 않다는 것도 확인했다 —
`validate_live_artifacts.py` 에 `*_CENSUS_MISSING` 류 체크가 NB_CSM_multiple·
csm_amort_schedule·insurance_pl_breakdown 엔 있는데 **bs_snapshot.json·
sensitivity_heatmap.json 엔 전혀 없다**(grep 0건) — 저 두 패널에서 같은 사고가 나면
지금은 RED 도 YELLOW 도 없이 조용히 통과한다.

**권고**:
1. (싸고 빠름) `sensitivity_heatmap.json` 용 `SENS_CENSUS_MISSING` 류 체크를
   `validate_live_artifacts.py` 에 신설(ifrs17 소관 — 다음 라운드에 착수 가능). `bs_snapshot.json`
   은 17BS 에이전트에 같은 패턴을 전달해야 한다(그 파일은 이번에도 안 건드림).
2. (근본) `universe.py::NON_LISTED_SKIP` 에서 이 3사를 빼고 measurement/sensitivity/
   historical 3개 live 스크립트를 재실행 + 전체 회귀검증하거나, 더 근본적으로는 4개
   mvp 배치의 회사선정 로직을 `discover_filings` 식 raw self-census 하나로 통일해
   "마스터에 있는데 어느 패널엔 없다"는 상태 자체가 구조적으로 안 생기게 하는 것.
   둘 다 이번 티켓보다 큰 작업이라 여기서 실행하지 않았다.

재현(수정 후):
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_viz_ifrs17_panels_golden.py
```

status: resolved (자기완결 — mvp 생성·버그 수정·골든·등재부 정리·회귀검증까지 전부 완료
및 재현 확인). `_resolved/` 로 이동.
