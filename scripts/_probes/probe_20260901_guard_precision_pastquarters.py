"""Guard precision check on past even quarters: is a flag a real data gap?

For every md_inbox file the guard flags with SECTION_LOST_*, report whether the
master actually has the cells that section feeds (36-40 for 시장위험, the
kics_rate_sensitivity rows for 위험민감도). A flag on a company whose cells are
already filled is a *provenance* flag (the value came from a raw-PDF recovery
path, not from the MD) — still worth a review, but not a missing number.
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


def _quarter(period: str) -> str:
    y, _, q = period.partition("_Q")
    return f"{y[2:]}.{q}Q" if y.startswith("FY") is False else f"{y[2:]}.{q}Q"


def main() -> int:
    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "quarter": keys[6], "val": keys[7]}
    have: set[tuple[str, str, int]] = set()
    for r in master:
        try:
            item = int(r[F["item"]])
        except (TypeError, ValueError):
            continue
        if r.get(F["val"]) not in (None, "", "None"):
            have.add((r[F["code"]], r[F["quarter"]], item))

    tally: Counter[str] = Counter()
    rows = []
    for md in sorted((REPO / "md_inbox").rglob("*.md")):
        meta, body = QC._read_md(md)
        flags = [f for f in QC.page_selection_flags(meta, body) if f.startswith("SECTION_LOST_")]
        if not flags:
            continue
        code = meta.get("company_code", "")
        period = meta.get("period", md.parent.name)
        y = period[2:6]
        q = period[-1]
        quarter = f"{y}.{q}Q"
        market_flags = [f for f in flags if "위험액현황" in f or "시장위험" in f]
        if not market_flags:
            continue
        missing = [i for i in range(36, 41) if (code, quarter, i) not in have]
        kind = "DATA_GAP" if missing else "PROVENANCE_ONLY"
        tally[kind] += 1
        rows.append((period, code, kind, missing, market_flags[:2]))

    print(f"\n=== guard SECTION_LOST (market) precision: {sum(tally.values())} flagged files ===\n")
    for period, code, kind, missing, fl in rows:
        if kind == "DATA_GAP":
            print(f"  {period:<12}{code:<9}{kind:<16} master missing items {missing}")
    print("\n", dict(tally))
    print(
        "PROVENANCE_ONLY = the master already carries 36-40 (filled from a raw-PDF\n"
        "recovery path); the flag says the MD no longer shows where they came from."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
