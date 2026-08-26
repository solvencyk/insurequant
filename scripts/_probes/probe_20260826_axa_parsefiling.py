#!/usr/bin/env python3
"""악사손해 2023.4Q 를 실제 파이프라인으로 흘려보고 어디서 비는지 본다."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP

filings = BP.discover_filings()
q = "2023.4Q"
dirs = filings["KR0049"][q]
print("dirs:", [str(d) for d in dirs])
t1, t2 = BP.parse_filing(dirs, False, code="KR0049", name="악사손해보험", quarter=q)
show = lambda d: None if not d else {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}
print("t1:", show(t1))
print("t2:", show(t2))
t1a = BP._fs_tier1("악사손해보험", q, "KR0049")
print("t1 api:", show(t1a))
t = t1a if t1a else t1
v = BP.assemble(t, t2, False)
print("assemble:", {k: (round(x, 2) if isinstance(x, float) else x) for k, x in v.items() if not str(k).startswith("_")})
print("_reconciled:", v.get("_reconciled"))
