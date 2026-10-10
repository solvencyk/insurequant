# -*- coding: utf-8 -*-
"""In-memory simulation of scripts/validate_management_indicators.py with the staged reinsurer rows added (READ ONLY).

Imports the validator as a module, runs its census / identity / cross-master checks on (a) the live master and (b) the live
master + staged reinsurer rows (data/_derived/reinsurer_ifrs17_csm_20261011/mi_rows.json), prints the difference.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_reinsurer_mi_validator_sim.py
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import validate_management_indicators as v  # noqa: E402


def run(mi_rows):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        periods_present = sorted(set(f"FY{r['공시분기'].split('.')[0]}_Q{r['공시분기'].split('.')[1].rstrip('Q')}" for r in mi_rows))
        unexplained, have = v.run_census(mi_rows, periods_present)
        v.run_item_completeness(have)
        red = v.run_identities(mi_rows)
        diffs = v.run_cross_master(mi_rows)
    return unexplained, [x for x in red if "RED" in x], [x for x in red if "RED" not in x], diffs


def main() -> int:
    live = json.loads((ROOT / "management_indicators.json").read_text(encoding="utf-8"))
    staged = json.loads((ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011" / "mi_rows.json").read_text(encoding="utf-8"))
    keys = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in live}
    assert not any((r["원보험사코드"], r["항목번호"], r["공시분기"]) in keys for r in staged), "key collision"
    b = run(live)
    a = run(live + staged)
    names = ("unexplained coverage gaps", "hard identity REDs", "identity NOTEs", "cross-master diffs (informational)")
    for n, x, y in zip(names, b, a):
        print(f"{n}: {len(x)} -> {len(y)}")
    new_red = [x for x in a[1] if x not in b[1]]
    print("new hard REDs:", new_red)
    reins = lambda s: [x for x in s if "KR11" in (x if isinstance(x, str) else str(x))]
    print("cross-master diffs mentioning KR11xx after:", reins(a[3]))
    print("unexplained gaps left (non-reinsurer):", sorted({f"{c} {q}" for c, q in a[0]})[:40])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
