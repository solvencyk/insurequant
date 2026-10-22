#!/usr/bin/env python3
"""Golden gate for scripts/validate_master_tables.py main().

main() is 374 lines running 15 independent checks (closing identity, coverage
holes, plausibility, PL bridge, zero legs, cross-check, QoQ, sensitivity) and
emitting one SUMMARY line + an exit code. Before splitting it, pin that
summary and exit code.

Runs with --no-build so no master is rebuilt or written. The SUMMARY line is
a compact count matrix; company lists in the body shift as data is backfilled,
so only the counts are asserted. Fast, deterministic, unconditional.

Regenerate when the counts legitimately change:

    python tests/test_master_tables_golden.py --update
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "fixtures" / "master_tables_golden.json"
SCRIPT = REPO / "scripts" / "validate_master_tables.py"


def _run() -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--no-build"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    line = next((l for l in proc.stdout.splitlines() if l.startswith("SUMMARY")), None)
    assert line, f"no SUMMARY line in output:\n{proc.stdout[-2000:]}\n{proc.stderr[-1000:]}"
    # The SUMMARY packs multi-count fields (closing:324P/0F/0S, sens:1R/1Y/20dir),
    # so key:int alone drops the P/F/S detail. Pin the whole normalised line.
    summary = re.sub(r"\s+", " ", line.strip())
    return {"exit_code": proc.returncode, "summary": summary}


def test_master_tables_summary_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = _run()
    assert expected["exit_code"] == actual["exit_code"], (
        f"exit code moved: {expected['exit_code']} -> {actual['exit_code']}"
    )
    assert expected["summary"] == actual["summary"], (
        "validate_master_tables SUMMARY moved:\n"
        f"  expected: {expected['summary']}\n  actual:   {actual['summary']}\n"
        f"If intended, regenerate: python {GOLDEN.name} --update"
    )


def test_oci_vs_bs_aoci_counts_blank_cells_as_not_compared(tmp_path, monkeypatch, capsys):
    """2026-10-23 (ticket 20261023T0030Z): a PL item-25 cell whose 값_당분기 is None is NOT compared, so it must
    not be counted as 'tol 이내'.  Synthetic masters: one cell of each kind.  The flagged set must be exactly the
    real mismatch -- the counting fix may not change which cells are flagged."""
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_master_tables as V

    def pl(co, q, dangi):
        return {"원수사명": co, "공시분기": q, "항목번호": 25, "항목명": "기타포괄손익", "값": 0, "값_당분기": dangi}

    def bs(co, q, v):
        return {"원수사명": co, "공시분기": q, "항목번호": 4, "항목명": "기타포괄손익누계액", "값": v}

    pl_rows = [pl("A", "2024.2Q", 100000.0),    # compared, closes (dBS 100000)
               pl("A", "2024.3Q", None),        # blank: must be neither compared nor 'within tol'
               pl("A", "2024.4Q", 50000.0),     # compared, dBS 0 -> real mismatch (flagged)
               pl("B", "2024.2Q", 5.0)]         # BS missing for B -> bs_skip
    bs_rows = [bs("A", "2024.1Q", 0.0), bs("A", "2024.2Q", 100000.0),
               bs("A", "2024.3Q", 100000.0), bs("A", "2024.4Q", 100000.0)]
    (tmp_path / V.PL_PATH).write_text(json.dumps(pl_rows, ensure_ascii=False), encoding="utf-8")
    (tmp_path / V.BS_PATH).write_text(json.dumps(bs_rows, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(V, "ROOT", tmp_path)

    counts: dict = {}
    rows = V._check_pl_oci_vs_bs_aoci(counts_out=counts)
    assert [(r[0], r[1]) for r in rows] == [("A", "2024.4Q")], rows
    assert counts == {"compared": 2, "blank": 1, "bs_skip": 1, "flagged": 1}, counts
    out = capsys.readouterr().out
    assert "비교한 2건 중 tol 이내 1건" in out and "단일분기 공란 1건" in out and "BS 결측 1건" in out, out


def _update() -> int:
    r = _run()
    r["_what"] = ("Refactor safety net for validate_master_tables.main(). Captured "
                  "before the 374-line function was split into per-check functions. "
                  "Asserts the SUMMARY count matrix + exit code (--no-build).")
    GOLDEN.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: exit={r['exit_code']}\n  {r['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
