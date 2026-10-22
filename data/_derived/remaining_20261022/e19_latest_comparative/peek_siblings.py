import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
H = Path(__file__).resolve().parent
for c in ("KR0005","KR0032","KR0070","KR0082","KR0083","KR0087"):
    p = H / f"plan_{c}.json"
    if not p.exists(): continue
    d = json.loads(p.read_text(encoding="utf-8"))
    print("==", c, "top keys", list(d.keys()))
    for b in d.get("buckets", []):
        print("  bucket", {k: b[k] for k in b if k in ("quarter","adopt","n_cells","items","reason") or k.startswith("n_")})
    cs = d.get("cells", [])
    print("  cells", len(cs), "keys", list(cs[0].keys()) if cs else None)
    for k in ("seam_cells","auto_follow_cells","neighbour_effects"):
        print("  ", k, len(d.get(k, [])))
    ac = d.get("apply_contract")
    if ac: print("  apply_contract keys", list(ac.keys()))
