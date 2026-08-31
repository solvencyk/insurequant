# -*- coding: utf-8 -*-
"""Print (rows, combo-count) census for a kics_disclosure.json path -- used
for before/after comparison around fill_tfi_table_to_disclosure.py writes."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
path = Path(sys.argv[1])
rows = json.loads(path.read_text(encoding="utf-8"))
combos = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows}
print(f"{path.name}: rows={len(rows)} combos={len(combos)}")
