"""Read-only: print the user_pl_cells.json / user_csm_cells.json gold entries of one company (optionally one quarter).
usage: s107_gold_peek.py <KRcode> [quarter]"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
code = sys.argv[1]
q = sys.argv[2] if len(sys.argv) > 2 else None
for name in ("user_pl_cells.json", "user_csm_cells.json"):
    d = json.loads((ROOT / "data/_gold" / name).read_text(encoding="utf-8"))
    print("==", name, {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items()})
    for g in d.get("set", []):
        if g["원보험사코드"] == code and (q is None or g["공시분기"] == q):
            print(" ", g["공시분기"], "item", g["항목번호"], "값", g.get("값"), "was", g.get("was"), "|", str(g.get("note", ""))[:260])
