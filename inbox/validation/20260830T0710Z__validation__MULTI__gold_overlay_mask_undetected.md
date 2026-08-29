---
from: validation
to: validation
created: 20260830T0710Z
status: open
route: blind_spot
company: MULTI
period: MULTI
rule: GOLD_OVERLAY_MASK_UNDETECTED
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

`inbox/validation/20260830T0400Z` §2(gold 19건 존치/제거) 판정의 **조건**이다.
19건을 존치하기로 했는데, 존치가 안전한 것은 **마스크가 보일 때뿐**이다. 지금은 안 보인다.

### 실측한 사각

`scripts/build_root_masters.py::_apply_csm_overrides()` 는 gold `set` 의 `값` 을
**무조건 UPSERT** 하고 빌더 소스와 **한 번도 비교하지 않는다**(L198-207). 전 저장소 검색
결과 `data/_gold/user_csm_cells.json` 을 **빌더 소스와 대조하는 게이트·테스트는 0건**이다
(소비처: `build_root_masters.py`=적용, `emit_ifrs17_provenance.py`=공시, `sync_owner_fills_to_json.py`=기입).

결과: **gold 셀 밑에서 빌더가 회귀해도 화면은 옳고 모든 게이트가 clean 을 찍는다.**
KR0079 는 이미 두 번 회귀했던 회사다(항목5 라벨 변형 #3, "기타" 상품블록 누락) — 그때
2025.2Q~2026.1Q 화면이 우연히 맞았던 이유가 정확히 이 마스크였다.

### census (2026-08-30 실측, 276 gold 엔트리 전수)

| 분류 | 건수 | 뜻 |
|---|---:|---|
| `SAME_EXACT` | 28 | 소스 == gold (소수 2자리까지) |
| `SAME_AT_1DP` | 55 | 소스가 소수 1자리로 반올림한 같은 값(&#124;diff&#124; ≤ 0.05) |
| `LOAD_BEARING` | 179 | 소스 ≠ gold — 화면값이 gold 에서만 나온다 |
| `ROW_ABSENT_IN_SOURCE` | 12 | 빌더가 행 자체를 못 만든다 |
| `NULL_IN_SOURCE` | 2 | 소스가 null |

**마스크 후보 = 83건 / 9개사**(28+55): KR0029·KR0070·KR0072·KR0073·KR0075·KR0076·
KR0079(19)·KR0094·KR1098. 티켓 §2 가 "19건" 이라 부른 것은 이 중 KR0079 몫이다.

> **원 티켓의 "코드가 gold 와 오차 0 재현" 은 부정확하다.** `csm_waterfall_master_diag.json`
> 은 소수 **1자리**, gold 는 **2자리**다. 19건은 전부 `SAME_AT_1DP`(최대 ±0.05억 차)이고
> `SAME_EXACT` 는 0건이다. 제거해도 폐쇄식 게이트는 안 깨진다(허용 `max(0.1%, 2.0억)`).
> 즉 제거 판단은 정밀도 문제가 아니라 **마스크 대 보호** 문제로만 갈린다.

### 요청 — 룰 배선

`scripts/validate_data_contract.py` 에 gold 오버레이 축을 신설한다.

1. `GOLD_OVERLAY_REDUNDANT` (YELLOW, 건별 아닌 **census 한 줄**): 소스가 이미 재현하는
   gold 셀 수를 매 실행 인쇄. "몇 칸이 조용히 덮여 있는가" 를 게이트 출력의 숫자로 만든다.
2. `GOLD_OVERLAY_DRIFT` (RED): 직전에 `SAME_*` 로 박제된 셀이 이제 `LOAD_BEARING` 으로
   바뀌면 = 빌더가 회귀했거나 gold 가 틀렸다. 박제부는 기존
   `data/_gold/csm_amort_identity_ledger.json` 패턴을 그대로 따를 것(저장소가 이미 신뢰하는 형태).
3. `GOLD_OVERLAY_DUPLICATE_KEY` (YELLOW): 아래 위생 항목.
4. `tests/test_rule_coverage_manifest.py` 에 이 축을 등재(안 하면 테스트가 막는다).
   `tests/test_identity_registry.py::test_no_undeclared_threshold_constants` 도 임계값
   (`TOL_EXACT=0.005`, `TOL_ROUND=0.05`) 등재를 강제할 것이다.
5. 배선 후 `scripts/prepush_check.py` 가 실제로 그 룰을 부르는지 **그 자리에서 확인**할 것
   (`CLAUDE.md`: "배선했다" ≠ "강제된다").

**전 버킷 시뮬레이션은 이미 끝나 있다** — 위 census 가 그것이다(276/276, 미분류 0).
룰 배선 전 재실행해서 baseline 이 안 바뀌었는지만 확인하면 된다.

### 같이 발견한 위생 2건

1. **gold `set` 중복 키 6건** — `KR0076 2025.4Q 항목1~6`. 뒤 엔트리(2026-08-25 `why` 있음)가
   앞 엔트리(2026-06-11 `note` 만, `why` 공란)를 의도적으로 supersede 하고 있고
   `_apply_csm_overrides` 의 last-wins 로 결과는 맞다. 다만 **리스트 순서에 정합성이 걸려 있다** —
   누가 정렬하거나 dedup 하면 조용히 뒤집힌다. 또 앞 6건은 `why` 가 비어 있어
   `20260825T2200Z` 의 "why 공란 0" census 와 어긋난다(그 census 는 `why`/`note` 둘 중
   하나만 있으면 통과시킨다).
2. **`public_exports/CSM워터폴.json` 이 루트 마스터보다 뒤처져 있다** — KR0079 2025.2Q 항목1
   `값_당분기` 가 public 20840.7 vs 루트 20847.3(= `28ab7f8` "기타" 블록 수정 반영 전).
   즉 **게이트가 보는 파일 ≠ 사용자가 보는 파일**이 지금 사실이다. publishing 라운드에서
   재생성되면 해소되지만, 그 갭 자체를 게이트가 안 보고 있다면 별도 축이 필요하다
   (`validate_live_artifacts.py` 커버 범위 확인 필요).

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_gold_vs_source_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_kr0079_2025q2_adjudication_sim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py   # baseline RED=0 YELLOW=93 exit 0
```

### 이 티켓이 거부되면

**그때는 19건(및 나머지 64건)을 제거하는 쪽이 옳다.** 탐지 못 하는 마스크보다 0.05억
반올림이 낫다 — 저장소 원칙 "게이트가 0 이라고 말한다 ≠ 그 축이 깨끗하다".

## 답변 (validation 작성 — 처리 후)

<룰 배선 결과 + 시뮬레이션 수치 + 훅 경로 확인 + 커밋 해시.>
