# -*- coding: utf-8 -*-
"""Sync ONE sheet (argv[1]) into a copy of the COMMITTED (HEAD) master xlsx so the commit contains only my sheet changes
(the working xlsx also carries parser-kics' uncommitted K-ICS공시 edits, which must not ride in my commit)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_master_xlsx_sheet as S
S.XLSX = Path(__file__).resolve().parent / "xlsx_tmp" / "head.xlsx"
sheet = sys.argv[1]
sys.argv = ["sync", sheet]
rc = S.main()
print(sheet, "rc", rc)
