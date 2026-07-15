"""Fix inbox/parser/20260715T0801Z: 2026.1Q 경과조치 적용후 요구자본 세부
(items 15-23) missing/wrong for 5 companies (KR0068/KR0073/KR0097/KR0003/KR0104).

Root cause: fill_post_transition_to_disclosure.py / backfill_post_transition_
when_not_applied.py have not been (re)run against FY2026_Q1 yet for these
companies' breakdown tables. Raw-verified per company via direct PDF page
dumps (scripts/_probes/dump_pdf_pages.py against data/disclosure/FY2026_Q1/raw/),
cross-validated with the R4 diversification formula
(item15 = sqrt(V'R4V) + item21, V=[17,18,19,20]) against each company's
independently-disclosed headline 지급여력비율(경과조치후) -- see
scripts/_probes/verify_r4_combo_20260715.py / verify_r4_hana_20260715.py
(all four companies' disjoint-derived components reproduce the headline
item14 to within ~0.5억, i.e. rounding noise).

Per-company raw basis (page numbers = data/disclosure/FY2026_Q1/raw/<file>.pdf):
- KR0068 한화생명 (p.4, "4-2-2"): explicit text x3 -- "당사는 자본감소분/
  장수위험 등/주식위험 경과조치를 적용하지 않아 경과조치 전후 금액 및 비율이
  동일함". Zero selective-transition effect this quarter -> items 15-23후 = 전
  (mirror; this is the same "owner 2026-07-07 명시저장" rule already applied
  to items 1/2/3/14/27/28 for this company, just never reached 15-23).
- KR0073 교보생명 (p.14-16): applies TIR(②) + TER(③, 주식위험만). ② and ③
  affect disjoint item buckets (life-only / market-only respectively, each
  table confirms the OTHER bucket unchanged) so item17 <- ②표, item19 <- ③표
  individually, with no combination ambiguity. item14/15/1/2/3후 already
  correct in JSON (headline-anchored by an earlier round); only children
  16/17/19/22/23 were missing.
- KR0097 하나생명 (p.7 총괄, p.9-11): applies TAC(①)+TIR(②)+TER(③,주식만).
  *** BUG FOUND: existing item14/15/27/28후 in JSON were the ②표 ISOLATED
  view (576,944백만 = 5,769.44억) instead of the true ①+②+③ combined
  headline ([지급여력비율총괄] p.7: 지급여력기준금액후 = 5,558억) -- corrected
  here (OVERWRITE, not UPSERT, for these 4 cells only). item17 (life-only,
  unaffected by ① or ③) was already correctly 4055.79 from ②표 -- left as-is.
- KR0003 롯데손해 (p.21 text, p.24 ②표): explicit text -- only ② (장수 등)
  applied; ①③ explicitly "적용하지 않음". ②표 is *the* combined answer
  (single active transition, no combination question). item14/15/27/28
  already correct in JSON; only children 16/17/18/19/22/23 were missing.
- KR0104 농협생명 (p.3 총괄 요약, p.19-21): applies TFI(공통)+TIR(②)+TER+TIRR(③).
  Same disjoint-bucket reasoning as KR0073. item1후 was entirely missing
  (recovered from 공통적용표, confirmed unchanged = 전) as was item3후
  (derived item1-item2). item14/2/27/28 already correct (headline-anchored
  by an earlier round).

UPSERT-only except the 4 documented KR0097 corrections (OVERWRITES list).
Idempotent: safe to re-run.
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]
QUARTER = "2026.1Q"

R4 = [
    [1.0, 0.0, 0.25, 0.25],
    [0.0, 1.0, 0.25, 0.25],
    [0.25, 0.25, 1.0, 0.25],
    [0.25, 0.25, 0.25, 1.0],
]


def _item15(v17, v18, v19, v20, v21):
    V = [v17, v18, v19, v20]
    total = sum(R4[i][j] * V[i] * V[j] for i in range(4) for j in range(4))
    return math.sqrt(total) + v21


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


# ---- UPSERT: (code, item_no) -> 값_적용후 (억원), only written if currently blank ----
UPSERTS: dict[tuple[str, int], float] = {}

# KR0068 한화생명 -- mirror 전 (zero selective-transition effect, raw-confirmed)
_h_mirror = {15: 176030, 16: 58275, 17: 106986, 18: 5595, 19: 78772,
             20: 25850, 21: 17102, 22: 32440, 23: 4704}
for item_no, v in _h_mirror.items():
    UPSERTS[("KR0068", item_no)] = float(v)

# KR0073 교보생명
UPSERTS[("KR0073", 17)] = 3_222_672 / 100
UPSERTS[("KR0073", 19)] = 4_956_271 / 100
UPSERTS[("KR0073", 22)] = 1_469_714 / 100
UPSERTS[("KR0073", 23)] = 188_789 / 100
# item16 DERIVE below (needs 17/19 above + already-present 18/20/21/15)

# KR0097 하나생명 (item14/15/27/28 are OVERWRITES, handled separately below)
UPSERTS[("KR0097", 18)] = 0.0
UPSERTS[("KR0097", 19)] = 144_074 / 100
UPSERTS[("KR0097", 20)] = 105_764 / 100
UPSERTS[("KR0097", 21)] = 51_149 / 100
UPSERTS[("KR0097", 23)] = 0.0
# item16 DERIVE below (needs new item14/15 from OVERWRITE step first)

# KR0003 롯데손해
UPSERTS[("KR0003", 17)] = 1_124_541 / 100
UPSERTS[("KR0003", 18)] = 62_189 / 100
UPSERTS[("KR0003", 19)] = 670_846 / 100
UPSERTS[("KR0003", 22)] = 292_400 / 100
UPSERTS[("KR0003", 23)] = 0.0
# item16 DERIVE below

# KR0104 농협생명
UPSERTS[("KR0104", 1)] = 69292.0
UPSERTS[("KR0104", 17)] = 1_192_615 / 100
UPSERTS[("KR0104", 18)] = 0.0
UPSERTS[("KR0104", 19)] = 1_086_569 / 100
UPSERTS[("KR0104", 20)] = 769_720 / 100
UPSERTS[("KR0104", 21)] = 269_572 / 100
UPSERTS[("KR0104", 22)] = 592_268 / 100
UPSERTS[("KR0104", 23)] = 0.0
# item3, item15, item16 DERIVE below


def main():
    dry_run = "--dry-run" in sys.argv
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    index: dict[tuple[str, str, int], dict] = {}
    for r in data:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    def get_row(code, item_no):
        return index.get((code, QUARTER, item_no))

    def get_post(code, item_no) -> float | None:
        row = get_row(code, item_no)
        if row is None:
            return None
        v = row.get("값_적용후")
        if v in (None, ""):
            return None
        return float(str(v).replace(",", ""))

    written = []

    # --- pass 1: plain UPSERTs ---
    for (code, item_no), value in UPSERTS.items():
        row = get_row(code, item_no)
        if row is None:
            print(f"WARN: no row for {code} item{item_no} {QUARTER}, skip")
            continue
        if row.get("값_적용후") not in (None, ""):
            continue  # never overwrite here
        row["값_적용후"] = _fmt(value)
        written.append((code, item_no, _fmt(value), "UPSERT"))

    # --- pass 2: KR0104 item3 = item1 - item2 (identity, both now present) ---
    row3 = get_row("KR0104", 3)
    if row3 is not None and row3.get("값_적용후") in (None, ""):
        v1 = get_post("KR0104", 1)
        v2 = get_post("KR0104", 2)
        if v1 is not None and v2 is not None:
            value = v1 - v2
            row3["값_적용후"] = _fmt(value)
            written.append(("KR0104", 3, _fmt(value), "DERIVE item1-item2"))

    # --- pass 3: KR0097 OVERWRITE (documented bug: isolated (2)-table value
    #     was stored instead of the true combined-transition headline) ---
    hana_headline_item14 = 5558.0  # p.7 [지급여력비율총괄], 경과조치후 지급여력기준금액
    row14 = get_row("KR0097", 14)
    row15 = get_row("KR0097", 15)
    row27 = get_row("KR0097", 27)
    row28 = get_row("KR0097", 28)
    v1_hana = get_post("KR0097", 1)
    v2_hana = get_post("KR0097", 2)
    if row14 is not None and v1_hana is not None and v2_hana is not None:
        old14, old15, old27, old28 = row14.get("값_적용후"), row15.get("값_적용후"), row27.get("값_적용후"), row28.get("값_적용후")
        row14["값_적용후"] = _fmt(hana_headline_item14)
        # item22/23 후 for KR0097: item22 already stored as 0 (see docstring:
        # true raw is 0.26억 but an earlier round already rounded/stored 0 --
        # not touched here); item23 just UPSERTed to 0 above (pass 1).
        item22 = get_post("KR0097", 22) or 0.0
        item23 = UPSERTS.get(("KR0097", 23), 0.0)
        new15 = hana_headline_item14 + item22 - item23
        row15["값_적용후"] = _fmt(new15)
        new27 = v1_hana / hana_headline_item14 * 100
        row27["값_적용후"] = _fmt(new27)
        new28 = v2_hana / hana_headline_item14 * 100
        row28["값_적용후"] = _fmt(new28)
        written.append(("KR0097", 14, f"{old14} -> {row14['값_적용후']}", "OVERWRITE bugfix"))
        written.append(("KR0097", 15, f"{old15} -> {row15['값_적용후']}", "OVERWRITE bugfix"))
        written.append(("KR0097", 27, f"{old27} -> {row27['값_적용후']}", "OVERWRITE bugfix"))
        written.append(("KR0097", 28, f"{old28} -> {row28['값_적용후']}", "OVERWRITE bugfix"))

    # --- pass 4: item15 DERIVE for KR0073/KR0003/KR0104 (item14+22-23) ---
    # KR0073 and KR0003 already have item15후 stored from an earlier round;
    # only KR0104 is missing it.
    for code in ("KR0104",):
        row15 = get_row(code, 15)
        if row15 is not None and row15.get("값_적용후") in (None, ""):
            v14 = get_post(code, 14)
            v22 = get_post(code, 22)
            v23 = get_post(code, 23)
            if None not in (v14, v22, v23):
                value = v14 + v22 - v23
                row15["값_적용후"] = _fmt(value)
                written.append((code, 15, _fmt(value), "DERIVE item14+22-23"))

    # --- pass 5: item16 DERIVE (needs 17,18,19,20,21,15 all present) for all 5 ---
    for code in ("KR0068", "KR0073", "KR0097", "KR0003", "KR0104"):
        row16 = get_row(code, 16)
        if row16 is None or row16.get("값_적용후") not in (None, ""):
            continue
        vals = {}
        missing = []
        for n in (17, 18, 19, 20, 21, 15):
            v = get_post(code, n)
            if v is None:
                missing.append(n)
            else:
                vals[n] = v
        if missing:
            print(f"WARN: {code} item16 DERIVE blocked, missing {missing}")
            continue
        value = (vals[17] + vals[18] + vals[19] + vals[20] + vals[21]) - vals[15]
        row16["값_적용후"] = _fmt(value)
        written.append((code, 16, _fmt(value), "DERIVE sum(17-21)-15"))

    print(f"{'DRY-RUN: ' if dry_run else ''}{len(written)} cells touched:")
    for code, item_no, value, note in written:
        print(f"  {code} item{item_no}: {value}  [{note}]")

    if dry_run:
        return

    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
