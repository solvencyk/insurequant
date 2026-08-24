# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
led = json.loads((ROOT / "data/_gold/kics_exemption_provenance.json").read_text(encoding="utf-8"))
want = set(sys.argv[1:])
for i, e in enumerate(led.get("entries", [])):
    tag = f"{e.get('company')}|{e.get('quarter')}|{e.get('registry')}"
    if any(w in tag for w in want):
        print(f"### entries[{i}]  {tag}")
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
