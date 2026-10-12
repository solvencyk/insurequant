# -*- coding: utf-8 -*-
"""Read-only: name the extra YELLOW the portfolio gate raises with the candidate master.  The gate prints only the first 50 YELLOW lines, so this runs the
gate's own source (no repository file is written) with that print limit lifted and the MASTER path pointed at (a) the live file and (b) the dry-run candidate,
then diffs the YELLOW/RED lines.  Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe p09_yellow_diff.py"""
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "scripts" / "validate_insurance_liability_portfolio.py"
SIM = ROOT / "data" / "_derived" / "ilp_kr1102_derived_load_20261012" / "sim" / "insurance_liability_portfolio.json"


def run(master: Path) -> list:
    src = GATE.read_text(encoding="utf-8")
    src = src.replace('findings["YELLOW"][:50]', 'findings["YELLOW"]').replace('len(findings["YELLOW"]) > 50', "False")
    assert '[:50]' not in src, "print limit not lifted"
    src = src.replace('MASTER = REPO_ROOT / "insurance_liability_portfolio.json"', f"MASTER = Path(r'{master}')")
    ns = {"__name__": "__main__", "__file__": str(GATE)}
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            exec(compile(src, str(GATE), "exec"), ns)
        except SystemExit:
            pass
    return [l.strip() for l in buf.getvalue().splitlines() if re.match(r"\s+(R\d|R-)", l)]


before, after = run(ROOT / "insurance_liability_portfolio.json"), run(SIM)
print("lines before", len(before), "after", len(after))
print("only in before:", [l for l in before if l not in after])
print("only in after :", [l for l in after if l not in before])
