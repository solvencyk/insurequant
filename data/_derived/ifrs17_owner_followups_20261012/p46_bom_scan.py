# -*- coding: utf-8 -*-
"""Read-only: BOM / non-UTF-8 scan over the files this round created or edited."""
import glob, sys
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
files = [R / p for p in ("scripts/annotate_csm_prov_kr1107_20261012.py", "scripts/extract_amort_split_tables_20261012.py", "scripts/load_amort_split_tables_20261012.py",
                         "scripts/extract_chubb_d2_20261012.py", "scripts/apply_chubb_ilp_d2_20261012.py", "scripts/apply_ifrs17_bs_fix_20261012.py",
                         "data/disclosure/_meta/ifrs17_owner_followups_runlog_20261012.md")]
files += [Path(p) for p in glob.glob(str(R / "data/_derived/ifrs17_owner_followups_20261012/*")) if Path(p).is_file() and Path(p).suffix in (".py", ".md", ".json", ".txt", ".log", ".sh")]
bad = 0
for f in files:
    b = f.read_bytes()
    try:
        b.decode("utf-8")
        ok = True
    except UnicodeDecodeError:
        ok = False
    if b[:3] == b"\xef\xbb\xbf" or not ok:
        bad += 1
        print("PROBLEM", f, "BOM" if b[:3] == b"\xef\xbb\xbf" else "not utf-8")
print("scanned", len(files), "problems", bad)
