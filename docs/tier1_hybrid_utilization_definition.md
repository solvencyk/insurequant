# Tier-1 Hybrid Recognition-Limit Utilization (신종자본증권 기본자본 인정한도 소진율)

This note defines the Tier-1 hybrid utilization metric produced by
`scripts/compute_tier1_utilization.py` and explains the data extraction from
K-ICS disclosure MDs and `kics_disclosure.json`.

## Definition (source: KIRI 연구보고서 2024-14)

PDF: `artifacts/kiri_study/nre2024-14_2.pdf`
(downloaded from https://www.kiri.or.kr/pdf/연구자료/연구보고서/nre2024-14_2.pdf)

### Page 12 — 기본자본 자본증권 인정한도 (KIRI text lines 154-157)

> "기본자본 자본증권의 인정한도는 **총요구자본의 10%**로 한다. 다만, 총요구자본의 10%를
> 초과한 자본증권 발행금액이 조건부자본증권인 경우 인정한도를 **총요구자본의 15%**로
> 상향조정한다."

### Page 13 — 자본증권 분류 (Table II-3)

| 구분 | 조건 | 자본 구분 | 인정 한도 |
|---|---|---|---|
| 신종자본증권 | 비조건부, Step-up 부재 | 기본자본 | **요구자본 10%** |
| 신종자본증권 | 조건부, Step-up 부재 | 기본자본 | **요구자본 15%** |
| 신종자본증권 | Step-up 존재 | 보완자본 | 요구자본 50% |
| 후순위채 | (관계없음) | 보완자본 | 요구자본 50% |

### Page 22 — 공통적용 경과조치 (legacy 기발행 자본증권)

> "기본자본으로 인정된 자본증권은 **총요구자본의 15%까지는 기본자본**으로 분류되며
> 총요구자본의 15%를 초과한 금액은 보완자본으로 분류한다."

### Excess reclassification path

Tier-1 hybrid issuance above the recognition limit is **reclassified to
Tier-2 (보완자본)** via 공시 detail row "Ⅴ.1 기본자본 자본증권의 인정한도를
초과한 금액". This same excess feeds the aggregate `kics_disclosure.json`
item 13 "Ⅲ. 보완자본으로 재분류하는 항목 (... 등)" together with other
reclassified components (해약환급금 부족분 상당액 등).

## Computed metric

```
SCR             = kics_disclosure.json item14 (지급여력기준금액, 억원)
tier1_limit_15  = SCR × 15%       (default — KIRI common-transition / conditional-bump)
tier1_limit_10  = SCR × 10%       (KIRI strict base, non-conditional new issuance)

hybrid_issued       = K-ICS MD section 5-1) B/S상의 자기자본 row "신종자본증권" (latest Q)
hybrid_excess_v1    = K-ICS MD detail-table row "1. 기본자본 자본증권의 인정한도를 초과한 금액"
                      (unit auto-detected: 억원 / 백만원 / 천원)

tier1_hybrid_recognized = max(hybrid_issued - hybrid_excess_v1, 0)

utilization_pct        = recognized / tier1_limit_15 × 100   (primary)
utilization_pct_strict = recognized / tier1_limit_10 × 100   (alternative)
```

## Confidence level

**Medium.** The KIRI definition is authoritative for the recognition-limit
formula, but disclosed data reveals two real-world wrinkles:

1. **`issued > SCR × 15%` with disclosed-excess = 0** (KR0068 Hanwha Life,
   KR0073 Kyobo Life). These insurers carry hybrid book-equity well above
   the KIRI-implied 15% cap yet report zero Ⅴ.1 reclassification. Likely
   explanations include (a) the legacy hybrid was structured as 조건부, (b)
   some grandfather provision allows full Tier-1 recognition for these
   issuances, or (c) the regulatory limit applied is broader than KIRI's
   straight 15% × SCR (e.g., uses 기본자본 base × ratio, or a separate cap
   defined in 별표 22). Flagged as `issued_above_15pct_but_no_disclosed_excess`.

2. **`excess_unknown_assumed_zero`** for insurers where the detailed Ⅴ.1
   row is not present in the MD (parser scope / image-only PDF). For these
   the script assumes 0 excess; the `utilization_pct` is therefore an upper
   bound on actual Tier-1 hybrid usage.

User can use `utilization_pct_strict` (10% denominator) as a stricter view.

## Per-company sources used (FY2025 Q4)

| Source | Layout |  Companies |
|---|---|---|
| BS 신종자본증권 issued | standard `\| 신종자본증권 \| value \| ...` | 21 |
| BS 신종자본증권 issued | transposed (label embedded in last cell) | 3 (KR0068 Hanwha Life, KR0069 Samsung Life, KR0094 Shinhan Life via split-char) |
| BS 신종자본증권 issued | missing | 3 (KR0010 KB Sonhae, KR0079 Mirae Asset Life — image-only; KR0080 AIA — no MD) |
| Ⅴ.1 excess row | 백만원 detail block | 4-5 cos (KR0073, KR0068, KR0083, KR0097, KR0082) |
| Ⅴ.1 excess row | 천원 detail block | KR0097 Hana Life (unit auto-detected) |
| Ⅴ.1 excess row | not extracted in MD | 13 cos with non-zero issued — flagged `excess_unknown_assumed_zero` |

## Open questions for user

1. Should `utilization_pct` use 15% (lenient/legacy default) or 10% (strict
   base rate per KIRI) as the headline denominator?
2. For `issued_above_15pct_but_no_disclosed_excess` cases (Hanwha Life,
   Kyobo Life): is there a different limit basis the disclosure uses (e.g.,
   기본자본 × n%, or a 별표 22 grandfather formula)? If you provide the rule
   we can refine.
3. Whether to extend coverage to historical quarters (FY2023 Q1 ... FY2025
   Q3) in a follow-up batch.

## Run

```powershell
python scripts/compute_tier1_utilization.py --quarter 2025.4Q
# outputs:
#   output/tier1_utilization/tier1_utilization_20254Q.json
#   output/tier1_utilization/tier1_utilization_20254Q.csv
```

## 소진율 필드 의미 — 배포 파이프라인 기준 (2026-08-25 갱신)

배포본 `kics_tier1_utilization.json` 의 값은 `compute_tier1_utilization.py` 가 만든 뒤
`wire_capital_securities_to_utilization.py` 가 **DART per-bond 실물**
(`data/bonds/capital_securities_fy2025.json`)로 덮어쓴 것이고, 그것을
`sync_tier_utilization_to_deploy.py --apply` 가 루트로 옮긴다. 화면(K-ICS.html 자본증권 도넛)이
읽는 것은 이 배포본이다. 소진율 계열 4필드의 의미는 아래와 같다 — 서로 겹치지 않는다.

| 필드 | 뜻 | 캡 | 화면 |
|---|---|---|---|
| `utilization_pct` | **표시 정본.** 신종 신규(2023~) 발행 인정액 ÷ 한도(SCR×15%) × 100 | **없음** — 100 을 넘을 수 있다 | 도넛 가운데 숫자(>100 이면 `100%+`) · 툴팁 실제값 |
| `utilization_pct_raw` | 하위호환 별칭. 캡이 있던 시절 "자르기 전" 값을 담던 자리 | 없음 | 안 쓴다. 캡 제거 후 `utilization_pct` 와 **항상 동일** |
| `utilization_pct_strict` | 같은 분자를 **SCR×10%**(비조건부 기본한도, KIRI p12)로 나눈 참고치 | 없음 | 안 쓴다. 정의상 `utilization_pct` 의 1.5배 |
| `tier1_hybrid_overflow_eok` | 발행액 − 한도 (음수면 0). 규정 [별표22] Ⅲ.2.다.(1)에 따라 **보완자본으로 자동 재분류**되는 금액이며 tier2 분자에 더해진다 | 해당 없음 | tier2 도넛 분자에 반영 |

### 왜 캡이 없나 (owner 2026-06-14 결정)

분자는 발행액(KOFIA/DART per-bond), 분모는 인정한도(공시 SCR 기반)로 **소스가 서로 독립**이라
사전에 100% 로 묶는 것이 애초에 불가능하다. 계산값이 100 을 넘으면 그대로 두고 **화면에서만**
`100%+` 로 표기한다(원호는 도넛 360° 한계 때문에 `Math.min(...,100)` 유지 — K-ICS.html L833).
근거: `docs/changelog_designer.md` 2026-06-14 (후속3) · `docs/agents/claude-agent-designer.md` L177
LOCKED 항목.

규정상 한도초과분이 보완자본으로 재분류되는 것은 사실이지만, 그것은 `tier1_hybrid_overflow_eok`
로 드러낼 사실이지 **"한도를 얼마나 채웠나"라는 소진율 표시값을 100 에서 자를 근거가 아니다.**
2026-08-25 이전에는 `wire_capital_securities_to_utilization.py` 가 `min(t1_util, 100.0)` 으로
데이터를 잘라, 6사(NH농협 192.9 · 하나생명 187.0 · 하나손해 144.1 · 코리안리 139.8 ·
한화생명 138.5 · KDB생명 113.4)가 화면에서 **평평한 `100%`** 로 그려졌다 — 한도에 정확히 걸친
회사와 구분이 안 됐다. tier2 는 같은 빌더에서 처음부터 자르지 않았으므로, 그 비대칭 자체가
버그의 지문이었다.

게이트: `scripts/validate_live_artifacts.py` 의 `TIER_UTILIZATION_IDENTITY` 가
`utilization_pct == 분자/한도×100` (캡 없이)을 강제한다. 캡을 다시 넣으면 6사가 RED 로 뜬다.
