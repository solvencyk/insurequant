"""Owner request 2026-07-16: K-ICS.html shows mostly-blank 경과조치 적용후
sub-items. For companies confirmed as NOT selective-transition appliers
(outside `_TRANSITION_APPLIERS`, the owner-provided 18사 definitive list in
scripts/validate_kics_disclosure.py), where the relevant parent item is
*provably* unchanged 전/후, mirror the still-blank children 값_적용후 = 값.
Where the parent genuinely differs (even a company that never elects a
selective transition can see a small K-ICS-ratio move from the *mandatory*
common TFI provision), leave blank -- per owner's explicit instruction.

Three independently-gated tiers (each gate only licenses its own children;
does NOT touch items 1-13, the capital-tier side -- see
fix_20260716_revert_wrong_item1213_mirror.py for why that side is unsafe to
blanket-mirror even when item1/14/27 look flat: TFI can reallocate the
기본자본/보완자본 tier split, and by extension item12/13, without moving
the totals):

  - items 15-23, 24-26: gated on item14(지급여력기준금액) 전==후 (tol 1.0억
    -- empirically calibrated, scripts/_probes/survey_item14_gap.py: 247/252
    non-applier pairs exact-0, next cluster ≤0.45(rounding noise), then a
    clean gap to the one genuine outlier at 45.0 (하나손해 2023.2Q, excluded)).
  - items 29-35 (생명·장기손해보험 sub-risks, 2Q/4Q only): gated on item17
    전==후 (tol 0.5).
  - items 36-40 (시장위험 sub-risks, 2Q/4Q only): gated on item19 전==후
    (tol 0.5).

UPSERT-only (never overwrites a present 값_적용후). Idempotent -- safe to
re-run every quarter going forward as new data loads, unlike the one-off
dated fix_2026071X_* scripts elsewhere in this directory.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

# Keep in sync with _TRANSITION_APPLIERS in scripts/validate_kics_disclosure.py
_TRANSITION_APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

TOL_ITEM14 = 1.0
TOL_ITEM17 = 0.5
TOL_ITEM19 = 0.5

TIER1_ITEMS = list(range(15, 27))  # 15-23 core breakdown + 24-26 종속/관계회사 세부
TIER2_ITEMS = list(range(29, 36))  # 생명장기 subs
TIER3_ITEMS = list(range(36, 41))  # 시장위험 subs


def _num(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main():
    dry_run = "--dry-run" in sys.argv
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))

    by_cq: dict[tuple[str, str], dict[int, dict]] = {}
    for r in data:
        by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r

    written: list[tuple[str, str, int]] = []
    excluded: list[tuple[str, str, str, float]] = []

    for (code, q), items in by_cq.items():
        if code in _TRANSITION_APPLIERS:
            continue

        def gate(parent_no: int, tol: float) -> bool:
            row = items.get(parent_no)
            if row is None:
                return False
            v, vp = _num(row.get("값")), _num(row.get("값_적용후"))
            if v is None or vp is None:
                return False
            return abs(v - vp) <= tol

        r14 = items.get(14)
        name = r14.get("원수사명", code) if r14 else code

        if gate(14, TOL_ITEM14):
            for n in TIER1_ITEMS:
                row = items.get(n)
                if row is None:
                    continue
                if row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
                    row["값_적용후"] = row["값"]
                    written.append((code, q, n))
        else:
            row14 = items.get(14)
            if row14:
                v14, vp14 = _num(row14.get("값")), _num(row14.get("값_적용후"))
                if v14 is not None and vp14 is not None:
                    excluded.append((code, q, name, abs(v14 - vp14)))

        if q.endswith("2Q") or q.endswith("4Q"):
            if gate(17, TOL_ITEM17):
                for n in TIER2_ITEMS:
                    row = items.get(n)
                    if row is None:
                        continue
                    if row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
                        row["값_적용후"] = row["값"]
                        written.append((code, q, n))
            if gate(19, TOL_ITEM19):
                for n in TIER3_ITEMS:
                    row = items.get(n)
                    if row is None:
                        continue
                    if row.get("값_적용후") in (None, "") and row.get("값") not in (None, ""):
                        row["값_적용후"] = row["값"]
                        written.append((code, q, n))

    print(f"{'DRY-RUN: ' if dry_run else ''}{len(written)} cells filled across "
          f"{len({(c, q) for c, q, _ in written})} (company,quarter) pairs")
    by_pair: dict[tuple[str, str], list[int]] = {}
    for c, q, n in written:
        by_pair.setdefault((c, q), []).append(n)
    for (c, q), ns in sorted(by_pair.items()):
        print(f"  {c} {q}: {sorted(ns)}")

    print(f"\nexcluded (item14 genuinely differs, left blank per owner instruction): {len(excluded)}")
    for c, q, name, d in excluded:
        print(f"  {name}({c}) {q}: |item14 diff|={d:.2f}")

    if dry_run:
        return

    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
