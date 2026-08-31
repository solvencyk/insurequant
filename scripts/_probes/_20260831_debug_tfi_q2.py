# -*- coding: utf-8 -*-
import io, sys, re
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
import importlib.util
spec = importlib.util.spec_from_file_location("pp", ROOT / "scripts/_probes/_20260831_aig_quarter_postprocess.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

md = (ROOT / "md_inbox/FY2023_Q2/KR0029_AIG손해보험.md").read_text(encoding="utf-8")
lines = md.splitlines()
tables = pp._tables_with_pos(lines)
print(f"num tables: {len(tables)}")
for start_idx, tbl in tables:
    header_join = "".join(tbl[0]).replace(" ", "")
    if "경과조치적용전" in header_join and "경과조치적용후" in header_join:
        body_labels = "".join((r[0] if r else "") for r in tbl[1:]).replace(" ", "")
        has_both = "지급여력금액" in body_labels and "지급여력기준금액" in body_labels
        print(f"\n--- table at line {start_idx+1}, rows={len(tbl)}, has_both_labels={has_both} ---")
        for r in tbl[:12]:
            print("  ", r)
