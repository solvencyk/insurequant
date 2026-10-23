# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
nb = json.loads(Path("C:/Users/sangwook.cho/Desktop/insurequant/NB_CSM_multiple.json").read_text(encoding="utf-8"))
rows = nb if isinstance(nb, list) else nb.get("rows") or nb.get("data") or []
print(type(nb).__name__, len(rows))
kb = [r for r in rows if isinstance(r, dict) and ("KR0099" in json.dumps(r, ensure_ascii=False) or "KB라이프" in json.dumps(r, ensure_ascii=False))]
print("KB라이프 rows:", len(kb))
for r in kb[:8]:
    print(json.dumps(r, ensure_ascii=False)[:400])
if rows:
    print("fields:", list(rows[0].keys()) if isinstance(rows[0], dict) else rows[0])
