"""a1: list every 신종자본증권 (hybrid) row in the bond ledger kics_capital_securities.json for the companies with
item6 > 0 in 2026.2Q (read-only) - issue date, amount, name, call/maturity, step_up / conditional flags if present.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a1_bond_ledger_hybrids.py
Output: a1_bond_ledger_hybrids.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = "2026.2Q"


def main() -> int:
    kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    item6 = {r["원보험사코드"]: r.get("값") for r in kics if r.get("공시분기") == Q and r.get("항목번호") == 6}
    cs = json.loads((REPO / "kics_capital_securities.json").read_text(encoding="utf-8"))
    out = [f"top-level keys: {list(cs.keys())}", f"row keys: {list(cs['rows'][0].keys())}" if cs.get("rows") else ""]
    by = {}
    for r in cs.get("rows", []):
        by.setdefault(r["원보험사코드"], []).append(r)
    for code in sorted(by):
        hy = [r for r in by[code] if r.get("종류") == "신종자본증권"]
        if not hy:
            continue
        out.append(f"== {code} {hy[0].get('회사명')}  item6({Q})={item6.get(code)}")
        for r in sorted(hy, key=lambda x: x.get("발행일") or ""):
            keep = {k: v for k, v in r.items() if k not in ("원보험사코드", "회사명")}
            out.append("   " + json.dumps(keep, ensure_ascii=False))
    txt = "\n".join(out) + "\n"
    (HERE / "a1_bond_ledger_hybrids.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
