"""Which 2026.2Q cells does the master still lack? (read-only)

Tells us what a re-conversion could plausibly ADD, versus what it can only
restore provenance for.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

QUARTER = "2026.2Q"


def main() -> int:
    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "name": keys[5], "quarter": keys[6], "val": keys[7]}
    print("field map:", F)

    companies = sorted({r[F["code"]] for r in master if r.get(F["quarter"]) == QUARTER})
    have: dict[int, set[str]] = {}
    names: dict[int, str] = {}
    for r in master:
        if r.get(F["quarter"]) != QUARTER:
            continue
        try:
            item = int(r[F["item"]])
        except (TypeError, ValueError):
            continue
        val = r.get(F["val"])
        names.setdefault(item, str(r.get(F["name"], ""))[:26])
        if val not in (None, "", "None"):
            have.setdefault(item, set()).add(r[F["code"]])

    print(f"\n=== master {QUARTER}: {len(companies)} companies ===\n")
    print(f"{'item':>5}  {'name':<28}{'have':>6}{'miss':>6}  missing companies")
    print("-" * 110)
    for item in range(1, 47):
        got = have.get(item, set())
        miss = sorted(set(companies) - got)
        if not got and not miss:
            continue
        flag = "" if not miss else " ".join(miss)
        print(f"{item:>5}  {names.get(item,''):<28}{len(got):>6}{len(miss):>6}  {flag[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
