"""Round 2 of the 20260715T0801Z ticket: same 적용후 요구자본(15-23) gap
pattern found on historical quarters flagged as "2차(우선순위 낮음)" in the
round-1 inbox reply -- 한화생명(KR0068) 2024.3Q/2025.2Q/2025.3Q and
농협생명(KR0104) 2023.1Q/2023.2Q. Same root cause as round 1: these
quarters' 적용후 breakdown was never (re)populated by
fill_post_transition_to_disclosure.py / backfill_post_transition_when_
not_applied.py.

Raw basis (data/disclosure/<period>/raw/):
- KR0068 all 3 quarters: raw text confirms all 3 selective transitions
  (TAC/②/③) "적용하지 않아 경과조치 전후 금액 및 비율이 동일함" -- same
  zero-effect pattern as 2026.1Q. items 15-23후 = 전 (mirror). 2025.2Q has
  a TFI-only capital-side blip (items 1/2/3후 already correctly differ from
  전 in JSON) but the *requirement* side (14/15+) is separately confirmed
  unchanged by the same raw table, so 15-23 mirroring is still valid there.
- KR0104 2023.1Q/2023.2Q: same ②(장수 등, disjoint->item17)+③(주식/금리,
  disjoint->item19) structure as KR0073/KR0104-2026.1Q in round 1 -- each
  table independently confirms the other bucket unchanged.
  *** CORRECTS A PRIOR SESSION'S DECISION (2026-07-12 2차,
  docs/changelog_parser_kics.md) ***: that round found item17후=10,899.56
  "치명적 헤드라인 신뢰값" didn't reconcile with sqrt(29-35후)=8,979.7 and
  reverted items 33/34/35(해지·사업비·대재해) to None as "다중 경과조치
  결합공식 불명". Re-verified here: raw p.9 [지급여력비율총괄] directly
  discloses 지급여력기준금액(후)=22,802 (exact match to stored item14) --
  no ambiguity in the parent chain. Reverse-solving the R4 identity for
  item17 given trusted item15=28917 yields ~8980.53, matching the raw
  (2)-table value (8979.70) almost exactly, NOT 10,899.56 (see
  scripts/_probes/verify_r4_kr0104_2023q1.py). The "10,899.56" figure
  cited by that session does not satisfy any raw table or the R4 identity
  and appears to have been a stale/erroneous number, not a genuine
  headline. Correcting item17 8979.70 (was wrong stale 10899.56, treated
  as OVERWRITE) and restoring items 33/34/35 = 0 (matches raw dashes,
  confirmed twice: reverse-solved R4 + direct table read).
  2023.2Q items 29-35 rows don't exist at all (전 side also missing) --
  out of scope here (a bigger gap than 값_적용후 alone); only 15-23 handled.

UPSERT-only except the one documented KR0104 2023.1Q item17 OVERWRITE.
Idempotent.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


# ---- UPSERT: (code, quarter, item_no) -> 값_적용후 (억원) ----
UPSERTS: dict[tuple[str, str, int], float] = {}

# KR0068 한화생명 -- mirror 전 (zero selective-transition effect, raw-confirmed for all 3)
_hanwha_mirrors = {
    "2024.3Q": {15: 144344, 16: 49203, 17: 95301, 18: 4262, 19: 62812,
                20: 23181, 21: 7992, 22: 22627, 23: 3252},
    "2025.2Q": {15: 160874, 16: 53519, 17: 105206, 18: 4640, 19: 68001,
                20: 24988, 21: 11558, 22: 26631, 23: 4371},
    "2025.3Q": {15: 165500, 16: 54218, 17: 106521, 18: 4751, 19: 68506,
                20: 25482, 21: 14457, 22: 27428, 23: 4383},
}
for q, items in _hanwha_mirrors.items():
    for item_no, v in items.items():
        UPSERTS[("KR0068", q, item_no)] = float(v)

# KR0104 농협생명 2023.1Q -- raw (2)/(3)표, disjoint buckets
UPSERTS[("KR0104", "2023.1Q", 18)] = 0.0
UPSERTS[("KR0104", "2023.1Q", 19)] = 1_813_184 / 100
UPSERTS[("KR0104", "2023.1Q", 20)] = 1_016_519 / 100
UPSERTS[("KR0104", "2023.1Q", 21)] = 186_219 / 100
UPSERTS[("KR0104", "2023.1Q", 22)] = 611_496 / 100
UPSERTS[("KR0104", "2023.1Q", 23)] = 0.0
# item17 is an OVERWRITE (see docstring), item15/16 DERIVE below

# KR0104 농협생명 2023.2Q -- same structure
UPSERTS[("KR0104", "2023.2Q", 17)] = 899_705 / 100
UPSERTS[("KR0104", "2023.2Q", 18)] = 0.0
UPSERTS[("KR0104", "2023.2Q", 19)] = 1_619_170 / 100
UPSERTS[("KR0104", "2023.2Q", 20)] = 946_394 / 100
UPSERTS[("KR0104", "2023.2Q", 21)] = 179_684 / 100
UPSERTS[("KR0104", "2023.2Q", 22)] = 556_520 / 100
UPSERTS[("KR0104", "2023.2Q", 23)] = 0.0
# item15/16 DERIVE below


def main():
    dry_run = "--dry-run" in sys.argv
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    index: dict[tuple[str, str, int], dict] = {}
    for r in data:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    def get_row(code, q, item_no):
        return index.get((code, q, item_no))

    def get_post(code, q, item_no) -> float | None:
        row = get_row(code, q, item_no)
        if row is None:
            return None
        v = row.get("값_적용후")
        if v in (None, ""):
            return None
        return float(str(v).replace(",", ""))

    written = []

    for (code, q, item_no), value in UPSERTS.items():
        row = get_row(code, q, item_no)
        if row is None:
            print(f"WARN: no row for {code} {q} item{item_no}, skip")
            continue
        if row.get("값_적용후") not in (None, ""):
            continue
        row["값_적용후"] = _fmt(value)
        written.append((code, q, item_no, _fmt(value), "UPSERT"))

    # KR0104 2023.1Q item17 OVERWRITE (corrects prior session's stale 10899.56)
    row17 = get_row("KR0104", "2023.1Q", 17)
    if row17 is not None:
        old = row17.get("값_적용후")
        new = _fmt(897_970 / 100)
        if old != new:
            row17["값_적용후"] = new
            written.append(("KR0104", "2023.1Q", 17, f"{old} -> {new}", "OVERWRITE (stale value, R4-reverse-solve confirms raw)"))

    # KR0104 2023.1Q items 33/34/35: restore raw-confirmed 0 (were None from a prior revert)
    for item_no in (33, 34, 35):
        row = get_row("KR0104", "2023.1Q", item_no)
        if row is not None and row.get("값_적용후") in (None, ""):
            row["값_적용후"] = "0"
            written.append(("KR0104", "2023.1Q", item_no, "0", "RESTORE (raw dash, was reverted to None)"))

    # item15 DERIVE (item14+22-23) where still missing
    for code, q in (("KR0104", "2023.1Q"), ("KR0104", "2023.2Q")):
        row15 = get_row(code, q, 15)
        if row15 is not None and row15.get("값_적용후") in (None, ""):
            v14 = get_post(code, q, 14)
            v22 = get_post(code, q, 22)
            v23 = get_post(code, q, 23)
            if None not in (v14, v22, v23):
                value = v14 + v22 - v23
                row15["값_적용후"] = _fmt(value)
                written.append((code, q, 15, _fmt(value), "DERIVE item14+22-23"))

    # item16 DERIVE (sum(17-21)-15) for all touched (code,quarter) pairs
    for code, q in {("KR0068", "2024.3Q"), ("KR0068", "2025.2Q"), ("KR0068", "2025.3Q"),
                     ("KR0104", "2023.1Q"), ("KR0104", "2023.2Q")}:
        row16 = get_row(code, q, 16)
        if row16 is None or row16.get("값_적용후") not in (None, ""):
            continue
        vals = {}
        missing = []
        for n in (17, 18, 19, 20, 21, 15):
            v = get_post(code, q, n)
            if v is None:
                missing.append(n)
            else:
                vals[n] = v
        if missing:
            print(f"WARN: {code} {q} item16 DERIVE blocked, missing {missing}")
            continue
        value = (vals[17] + vals[18] + vals[19] + vals[20] + vals[21]) - vals[15]
        row16["값_적용후"] = _fmt(value)
        written.append((code, q, 16, _fmt(value), "DERIVE sum(17-21)-15"))

    print(f"{'DRY-RUN: ' if dry_run else ''}{len(written)} cells touched:")
    for code, q, item_no, value, note in written:
        print(f"  {code} {q} item{item_no}: {value}  [{note}]")

    if dry_run:
        return

    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
