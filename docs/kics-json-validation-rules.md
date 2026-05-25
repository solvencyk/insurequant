# K-ICS JSON Validation Rules (Authoritative)

**Source of truth (code):** `src/solvency/validation/kics_json_rules.py`  
**Runner:** `scripts/validate_kics_disclosure.py`  
**Input:** root `kics_disclosure.json` (list of row objects keyed by `항목번호`)

When this document and the Python module disagree, **the Python module wins**. Update this doc in the same PR as any rule change.

---

## Pipeline gate (mandatory)

Before advancing to the next K-ICS pipeline stage (JSON swap, template sync, HTML deploy, push):

1. Run `python scripts/validate_kics_disclosure.py` on root `kics_disclosure.json`.
2. **RED count must be 0**, unless each remaining RED is a **documented exception** in `TODO.md` (company code, quarter, rule id, reason).
3. Any unexpected RED requires **parsing-error review** (MD source, parser scope, row mapping) before proceeding.
4. YELLOW findings are warnings (|diff| >= 0.5 eok-won, <= tolerance); they do not block the gate but should be triaged.
5. SKIP on rule `8_life` is expected when sub-items 29-35 are not all present (non-life insurers, partial tables). SKIP on rule `3` is expected (bridge formula deferred; Rule 1 is authoritative for item1).

See also: `CLAUDE.md`, `docs/claude-validation-harness.md`, `docs/claude-agent-kics.md`, `docs/claude-json-build.md`.

---

## Record shape and grouping

Each JSON row uses (at minimum):

| Field | Key | Role |
|-------|-----|------|
| Company code | 원보험사코드 | Bucket key |
| Company name | 원수사명 | Reporting only |
| Quarter | 공시분기 | Bucket key (e.g. 2025.4Q) |
| Item number | 항목번호 | Integer 1-35 |
| Item label | 항목명 | Korean label (not used by validator) |
| Value | 값 | Primary numeric field |
| Post-transition value | 값_적용후 | Optional; used by rule 8_post |

Rows are grouped into **buckets** (원보험사코드, 공시분기). One finding per rule per bucket.

Numeric parsing (parse_numeric): strips commas; -, —, N/A, empty -> missing (None).

---

## Status and tolerance

Default tolerance: **2.0** (eok-won units for amount rules; percentage points for ratio rules 7, 8, 8_post).

**Per-rule overrides:**
- **Rule 8_life** uses a dynamic tolerance: `max(eff_tol, 0.05 * abs(expected))`. R7 diversified sqrt accumulates rounding from 7 sub-items, so an absolute 2.0 eok-won tolerance is too tight when expected is large (hundreds to thousands of eok-won). Other rules retain the default 2.0 (or the image-OCR override below).
- **Image-only PDF insurers** (KR0010, KR0079): tolerance overridden to **10.0** across all rules to absorb OCR rounding (see KICS-IMG in TODO.md).

Classification (`classify_diff`, diff = actual - expected):

| Status | Condition |
|--------|-----------|
| **GREEN** | abs(diff) < 0.5 |
| **YELLOW** | 0.5 <= abs(diff) <= tolerance |
| **RED** | abs(diff) > tolerance, or required inputs missing, or actual value missing |
| **SKIP** | Rule `8_life` only: item 17 or any of items 29-35 missing |
| **ERROR** | Reserved in summary counters (not emitted by current rules) |

Diversified risk helper: `sqrt(max(V' M V, 0))` — negative inner product clamped to 0 before sqrt.

---

## Rule catalog

Rule IDs match the `rule` field in validation findings.

### Rule 1 — Solvency amount decomposition

**Formula:** item1 = item2 + item3

| Role | Item | Label (see mapping table) |
|------|------|---------------------------|
| Actual | 1 | 가. 지급여력금액 |
| Term | 2 | 기본자본 |
| Term | 3 | 보완자본 |

**Prerequisites:** items 1, 2, 3 all present.  
**Missing inputs:** RED (missing items 1-3).

---

### Rule 2 — Section I net assets (건전성감독기준 재무상태표 상의 순자산)

**Formula:** item4 = item5 + item6 + item7 + item8 + item9 + item10 + item11

| Role | Item | Label |
|------|------|-------|
| Actual | 4 | Ⅰ. 건전성감독기준 재무상태표 상의 순자산 |
| Terms | 5-11 | 보통주 … 조정준비금 (10-11 optional, default 0) |

**Sum behavior:** `_sum_optional` — missing items 10-11 treated as 0.  
**Prerequisites:** item 4 present.  
**Missing inputs:** RED (missing item4).

---

### Rule 3 — Solvency amount from section I bridge (SKIP)

**Formula (not enforced):** item1 = item4 - item12 + item13

**Status:** **SKIP** for all buckets. Deferred 2026-05-25: bridge does not reconcile on most insurers (e.g. KR0069 2024.2Q, KR0001 Meritz); disclosure tables use item2 = item4 - item12 - item13 then item1 = item2 + item3 (**Rule 1**). Item12/item13 parsing also has known errors (item12 = item1 in ~100 buckets).

Rule 1 remains the authoritative check on item1 (지급여력금액).

---

### Rule 4 — Basic required capital (R4 diversification)

**Formula:** item15 = sqrt(V' R4 V) + item21

| Role | Item |
|------|------|
| Actual | 15 |
| Vector V | 17, 18, 19, 20 (order matters) |
| Add-on | 21 |

**Note:** item 21 (운영위험액) is **excluded** from V; added after sqrt.

**Prerequisites:** items 15, 17, 18, 19, 20, 21 all present.  
**Missing inputs:** RED (missing items for R4 (15,17-21)).

#### R4 matrix (4x4)

Rows/columns order: (17, 18, 19, 20) = (life-long-term, general P&C, market, credit).

`
     17    18    19    20
17 [ 1.0   0.0  0.25  0.25 ]
18 [ 0.0   1.0  0.25  0.25 ]
19 [ 0.25 0.25  1.0  0.25 ]
20 [ 0.25 0.25 0.25   1.0 ]
`

Diagonal = 1.0; life-nonlife cross = 0.0; all other off-diagonal pairs = 0.25.

---

### Rule 5 — Required capital (section I - II + III)

**Formula:** item14 = item15 - item22 + item23

| Role | Item |
|------|------|
| Actual | 14 |
| Terms | 15, 22, 23 |

**Default:** if item 23 missing, treat as **0.0** (still requires 14, 15, 22).  
**Missing inputs:** RED (missing items 14,15,22).

---

### Rule 6 — Diversification effect

**Formula:** item16 = item17 + item18 + item19 + item20 + item21 - item15

| Role | Item |
|------|------|
| Actual | 16 |
| Terms | 15, 17, 18, 19, 20, 21 |

**Prerequisites:** all listed items present.  
**Missing inputs:** RED (missing items for rule 6).

---

### Rule 7 — Solvency ratio

**Formula:** item27 = item1 / item14 * 100

| Role | Item |
|------|------|
| Actual | 27 |
| Terms | 1, 14 |

**Prerequisites:** items 1, 14, 27 present and **item14 != 0**.  
**Missing inputs:** RED (missing items 1,14,27 or item14=0).

---

### Rule 8 — Basic capital ratio

**Formula:** item28 = item2 / item14 * 100

| Role | Item |
|------|------|
| Actual | 28 |
| Terms | 2, 14 |

**Prerequisites:** items 2, 14, 28 present and **item14 != 0**.  
**Missing inputs:** RED (missing items 2,14,28 or item14=0).

---

### Rule 8_post — Basic capital ratio (post-transition)

**Formula:** item28 = item2_post / item14 * 100

Uses 값_적용후 for item 2 when present.  
**Actual value:** 값_적용후 on item 28 if present, else 값 on item 28.

**Prerequisites:** item 2 post-transition value present, item 14 present, item14 != 0.  
**Missing inputs:** RED (
o post-transition item2 or missing item14).

---

### Rule 9 — Basic capital transitional consistency (item2 post >= pre)

`item2(기본자본) 값_적용후 >= 값(적용 전) - eff_tol`

Rationale: 경과조치 적용 후 신종자본증권 (pre-2022 발행) 한도 무관 인정 → 기본자본 ↑. Therefore post >= pre.

SKIP when 값_적용후 absent (no transitional difference reported) or equal to 값.

Added 2026-05-25 after user observation that 푸본현대/아이엠라이프/KR0001 2023.1Q showed implausible post < pre patterns suggesting parser column-pickup bugs.

### Rule 10 — Required capital transitional consistency (item14 pre >= post)

`item14(지급여력기준금액) 값(적용 전) >= 값_적용후(적용 후) - eff_tol`

Rationale: 경과조치 적용 후 일부 위험액 점진 인식 → SCR ↓ vs 적용 전. Therefore pre >= post.

SKIP when 값_적용후 absent or equal to 값.

Added 2026-05-25.

### Rule 8_life — Life-long-term sub-risk (R7 diversification)

**Formula:** item17 = sqrt(S' R7 S)

| Role | Item |
|------|------|
| Actual | 17 |
| Vector S | 29, 30, 31, 32, 33, 34, 35 |

**Prerequisites:** item 17 and **all** items 29-35 present.  
**Missing inputs:** **SKIP** (not RED) — missing item17 or any of items 29-35.

**Tolerance:** dynamic, `max(eff_tol, 0.05 * abs(expected))`. The R7 diversification accumulates rounding from 7 sub-items, so a fixed 2.0 eok-won tolerance is too tight for large expected values.

#### R7 matrix (7x7)

From K-ICS standard Table II-5 (sub-risk correlation). Rows/columns order: items 29-35.

Raw matrix before symmetrization:

`
        29     30     31     32     33     34     35
29 [  1.0  -0.25   0.25   0.0    0.0    0.25   0.25 ]
30 [ -0.25   1.0    0.0    0.0    0.25   0.25   0.0  ]
31 [  0.25   0.0    1.0    0.0    0.0    0.5    0.25 ]
32 [  0.0    0.0    0.0    1.0    0.0    0.5    0.25 ]
33 [  0.0    0.25   0.0    0.0    1.0    0.5    0.25 ]
34 [  0.25   0.25   0.5    0.5    0.5    1.0    0.25 ]
35 [  0.25   0.0    0.25   0.25   0.25   0.25   1.0  ]
`

**Implementation:** R7 = max(R7, R7.T) element-wise, then diagonal forced to 1.0.

Sub-item labels:

| Item | Label |
|------|-------|
| 29 | 1-1. 사망위험액 |
| 30 | 1-2. 장수위험액 |
| 31 | 1-3. 장해·질병위험액 |
| 32 | 1-4. 장기재물·기타위험액 |
| 33 | 1-5. 해지위험액 |
| 34 | 1-6. 사업비위험액 |
| 35 | 1-7. 대재해위험액 |

---

## Rules not implemented / deferred

- **Rule 3:** always **SKIP** (item4 - item12 + item13 bridge deferred; use Rule 1 for item1).

Rules 1-2, 4-8, 8_post, 8_life, 9, 10 are enforced in `kics_json_rules.py`.

---

## Item number to Korean label mapping

Canonical labels from `templates/kics_disclosure.json` / K-ICS disclosure tables:

| Item | Korean label |
|------|----------------|
| 1 | 가. 지급여력금액 |
| 2 | 기본자본 |
| 3 | 보완자본 |
| 4 | Ⅰ. 건전성감독기준 재무상태표 상의 순자산 |
| 5 | 1. 보통주 |
| 6 | 2. 자본항목 중 보통주 이외의 자본증권 |
| 7 | 3. 이익잉여금 |
| 8 | 4. 자본조정 |
| 9 | 5. 기타포괄손익누계액 |
| 10 | 6. 비지배지분 |
| 11 | 7. 조정준비금 |
| 12 | Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등) |
| 13 | Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등) |
| 14 | 나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ) |
| 15 | Ⅰ. 기본요구자본 |
| 16 | - 분산효과 : (1+2+3+4+5) - Ⅰ |
| 17 | 1. 생명장기손해보험위험액 |
| 18 | 2. 일반손해보험위험액 |
| 19 | 3. 시장위험액 |
| 20 | 4. 신용위험액 |
| 21 | 5. 운영위험액 |
| 22 | Ⅱ. 법인세조정액 |
| 23 | Ⅲ. 기타 요구자본(1+2+3) |
| 24 | 1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치 |
| 25 | 2. 비례성원칙을 적용한 종속회사의 요구자본 대응치 |
| 26 | 3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치 |
| 27 | 다. 지급여력비율 : 가 ÷ 나 × 100 |
| 28 | 기본자본비율 |
| 29 | 1-1. 사망위험액 |
| 30 | 1-2. 장수위험액 |
| 31 | 1-3. 장해·질병위험액 |
| 32 | 1-4. 장기재물·기타위험액 |
| 33 | 1-5. 해지위험액 |
| 34 | 1-6. 사업비위험액 |
| 35 | 1-7. 대재해위험액 |

Items 12, 13, 24-26 are not cross-checked by rules 1-8_life but appear in disclosure JSON.

---

## Running validation

```bash
python scripts/validate_kics_disclosure.py
```

- Reads `kics_disclosure.json` at repo root.
- Writes `artifacts/kics_validation/report_{timestamp}.json`.
- Exit code **0** if RED=0; **2** if RED>0.
- Spot-check: KR0005 / 2025.4Q (Heungkuk Fire) included in report.

Report fields per finding: `rule`, `원보험사코드`, `원수사명`, `공시분기`, `status`, `expected`, `actual`, `diff`, `detail`.

---

## SKIP policy summary

| Rule | SKIP when | Blocks gate? |
|------|-----------|--------------|
| 8_life | item 17 or any item 29-35 missing | No |
| All others | Never SKIP — missing inputs -> RED | Yes (RED) |

Permanent skip cohorts for sub-items (parsing, not validation): see TODO.md KICS-SUB (KR0029, KR0150, KR1098, etc.).
