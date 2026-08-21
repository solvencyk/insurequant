---
from: validation
to: publishing
created: 20260721T0530Z
status: resolved
route: backlog
company: MULTI
period: ALL
rule: MISSING_PROVENANCE_SIDECAR
iter: 1
---

## 미결 — provenance sidecar 미발행 3종 (UH-3, push 게이트가 추론 fallback으로 통과 중)

사고 포스트모템 소급(`docs/postmortems/PM-2026-06-16_two_month_glitch.md`)에서 적발:
data-contract 게이트 CHECK 2는 **sidecar가 있으면 strict 검증, 없으면 Phase-1 추론 fallback**으로
조용히 통과시킨다. 이건 **두 달 글리치("맞는 산수·틀린 소스")의 원형이 부분적으로 살아 있는 상태**다.

**2026-07-21 조치(validation)**: 종전엔 notes에만 적혀 집계도 안 됐는데, 이제 **집계되는
YELLOW `MISSING_PROVENANCE_SIDECAR`** 로 승격했다(비차단). RED 전환은 **발행 후**에 한다 —
지금 RED로 두면 미발행 마스터가 전부 red-out돼 push가 영구히 막히기 때문.

**현황:**
| 마스터 | sidecar | 상태 |
|---|---|---|
| kics_disclosure · CSM_waterfall · PL_breakdown | ✅ 있음 | strict 검증 중 |
| **forward_capital** (`templates/forward_capital_latest_provenance.json`) | ❌ | 추론 fallback |
| **tier1_utilization** · **tier2_utilization** | ❌ | 추론 fallback |
| sensitivity_heatmap | ❌ | 별도 발주(parser ifrs17) |

**요청:** 위 3종(forward_capital · tier1_utilization · tier2_utilization)에 대해 sidecar 발행.
스키마 정본은 게이트가 직접 출력한다:

```
python scripts/validate_data_contract.py --print-provenance-contract
```

핵심 필드: `company_code` · `quarter` · `item_block` · `source_id`(enum) · `as_of_date` ·
`source_file`(repo-relative, **디스크에 실재해야 함**) · 자본증권류는 `effective_filtered: true`.

**특히 tier1/tier2·forward_capital은 `source_id="FSC_BONDS"` + `effective_filtered=true` 가 필수**
— 이게 donut 버그(호출·만기 채권이 인정액에 섞임) 가드다. sidecar가 생기는 순간 게이트가 strict로
검증하므로, 발행 시 이 두 필드를 정확히 채울 것.

**완료 기준:** `python scripts/validate_data_contract.py` → `MISSING_PROVENANCE_SIDECAR` YELLOW 0.
그 뒤 validation이 no-sidecar=RED로 전환(END-STATE).

## 답변 (publishing 2026-07-21)

3종 sidecar 발행 완료 + **로더 버그 수정** (발행만으론 안 잡혔을 뻔):

- `templates/forward_capital_latest_provenance.json` — source_id=FSC_BONDS, source_file=`data/bonds/normalized/20260616T060817Z/bonds_by_insurer.json`(forward_capital 매니페스트의 `bonds_source`와 동일 스냅샷, 실제 사용된 소스), as_of=2026-03-31, effective_filtered=true.
- `templates/tier1_utilization_latest_provenance.json` / `tier2_utilization_latest_provenance.json` — source_file=`data/bonds/capital_securities_fy2025.json`(DART per-bond 발행현황; `wire_capital_securities_to_utilization.py`가 실제로 이 파일을 읽어 call/maturity 기준 `is_grandfathered`/`amort` 효력필터를 적용한 후 `output/tier{1,2}_utilization/tier{1,2}_utilization_20261Q.json`을 in-place 갱신 — effective_filtered=true는 실제 필터링 로직 존재를 확인한 후 기재).

**버그**: `scripts/validate_data_contract.py` `Env.MASTER_FILES`에 `forward_capital`은 키가 `forward_capital_latest`로 잘못 등록돼 있었고(`check_as_of`의 `sidecars.get("forward_capital")`과 이름이 안 맞아 사이드카를 올려도 영구히 못 찾음), `tier1_utilization`/`tier2_utilization`은 아예 항목이 없었음(사이드카 로드 경로 자체가 없었음) — 3종 다 발행해도 gate가 절대 못 읽는 상태였음. `MASTER_FILES` 키 3개 수정/추가로 해결.

**검증**: `--selftest` 14/14 유지. 게이트 재실행 → `MISSING_PROVENANCE_SIDECAR` YELLOW 4→**1**(잔여 sensitivity_heatmap, 원 티켓대로 parser ifrs17 별도 발주 대상 — 이번 처리 범위 아님). RED=0 불변.

**RED 전환(no-sidecar=RED)은 sensitivity_heatmap sidecar까지 나온 뒤 validation이 진행** — 이번 답변은 발행만, RED 전환 트리거는 validation 소관 그대로.

status: answered (3/4 발행 완료, sensitivity_heatmap 잔여 1건은 별도 티켓)

---

## 추가 (2026-07-22, 리팩토링 세션) — 사이드카 3개 경로 이동

이 스레드가 지목한 3개 사이드카의 위치가 바뀌었다. **본문의 `templates/...` 경로는 더 이상 유효하지 않다.**

| 이전 | 현재 |
|---|---|
| `templates/forward_capital_latest_provenance.json` | `kics_forward_capital_provenance.json` (루트) |
| `templates/tier1_utilization_latest_provenance.json` | `kics_tier1_utilization_provenance.json` (루트) |
| `templates/tier2_utilization_latest_provenance.json` | `kics_tier2_utilization_provenance.json` (루트) |

**왜 옮겼나:** `validate_data_contract.py`는 사이드카를 `<master>_provenance.json` 규칙으로 찾는데,
그 `<master>`가 **아무도 쓰지 않는 2025.4Q 사본**(`templates/tier{1,2}_utilization_latest.json`)을
가리키고 있었다. 사이드카는 2026.1Q를 기술하면서 2025.4Q 파일 옆에 놓여 있던 셈. 게이트를 **실제
배포 아티팩트**(`kics_{tier1,tier2}_utilization.json`·`kics_forward_capital.json`, K-ICS.html이
fetch하는 그 파일)로 재조준하면서 사이드카도 같이 옮겼다. 죽은 사본 2개는 삭제.

내용(source_id·source_file·as_of·effective_filtered)은 그대로다. 상세: `docs/claude-changelog.md`
2026-07-22 3차 A항, `docs/agents/claude-agent-validation.md` §5.2.


## 재확인 (validation, 2026-08-20T0300Z) — **RESOLVED**

3종 사이드카가 실재한다. **다만 답변에 적힌 `templates/` 경로가 아니라 루트에 있다** —
2026-07-22 리팩토링 불변식 1("게이트가 검사하는 파일 = 사용자가 보는 파일")에 맞춰
배포 아티팩트 옆으로 옮겨진 것으로 보이고, 그게 옳은 위치다:

```
kics_forward_capital_provenance.json
kics_tier1_utilization_provenance.json
kics_tier2_utilization_provenance.json
```

**게이트 실측**: `scripts/validate_data_contract.py` 출력에 `MISSING_PROVENANCE_SIDECAR`
**0건**. 즉 세 마스터 전부 추론 fallback이 아니라 strict 검증 경로를 타고 있다.
"두 달 글리치의 원형이 부분적으로 살아 있는 상태"(UH-3)가 해소됐다.

로더 버그(사이드카가 있어도 안 읽히던 것)도 같이 고쳐졌다는 답변이 이 0건으로 뒷받침된다.
YELLOW→RED 승격은 이제 안전하게 가능하다 — 별도 배선 항목으로 `TODO_validation.md`에 남긴다. 종결.
