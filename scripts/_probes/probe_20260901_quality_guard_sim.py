"""Blast-radius simulation for the new page-selection guard in quality_check.

Prints, over the whole md_inbox tree:
  * old review count (pre-guard criteria only)
  * new review count (guard included)
  * how many files flip accept -> review, and which flag caused it
  * per-period / per-flag tallies

Run BEFORE relying on the guard so a threshold change cannot flood the queue.
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import quality_check as QC  # noqa: E402


def main() -> int:
    md_root = REPO / "md_inbox"
    paths = sorted(md_root.rglob("*.md"))
    old_review = 0
    new_review = 0
    flips: list[tuple[str, str, list[str]]] = []
    flag_counter: Counter[str] = Counter()
    period_flips: Counter[str] = Counter()
    period_total: Counter[str] = Counter()

    for p in paths:
        rep = QC.score(p)
        period = p.parent.name
        period_total[period] += 1
        critical = "생명장기손해보험위험액" in rep.missing_rows
        missing_core = [m for m in rep.missing_rows if m.startswith(("가.", "나.", "다."))]
        was_review = bool(missing_core) or critical or rep.score < 0.7
        old_review += int(was_review)
        new_review += int(rep.decision == "review")
        for f in rep.page_flags:
            flag_counter[f.split("=")[0]] += 1
        if rep.decision == "review" and not was_review:
            flips.append((period, p.stem, rep.page_flags))
            period_flips[period] += 1

    print(f"\n=== quality guard simulation over {len(paths)} md_inbox files ===")
    print(f"  review BEFORE guard : {old_review}")
    print(f"  review AFTER  guard : {new_review}")
    print(f"  newly routed to review (accept -> review): {len(flips)}")
    print("\n  flag occurrences (all files, review or not):")
    for flag, n in flag_counter.most_common():
        print(f"    {flag:<26} {n}")
    print("\n  flips by period:")
    for period, n in sorted(period_flips.items()):
        print(f"    {period:<12} {n:>4} / {period_total[period]}")
    print("\n  first 40 flips:")
    for period, stem, flags in flips[:40]:
        print(f"    {period:<12} {stem:<44} {';'.join(flags)}")

    out = REPO / "data" / "_derived" / "_probe_quality_guard_sim.json"
    out.write_text(
        json.dumps(
            {
                "total": len(paths),
                "review_before": old_review,
                "review_after": new_review,
                "flips": [{"period": a, "file": b, "flags": c} for a, b, c in flips],
                "flag_counts": dict(flag_counter),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
