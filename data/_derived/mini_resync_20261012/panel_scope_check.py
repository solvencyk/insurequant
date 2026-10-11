# -*- coding: utf-8 -*-
"""Why the ifrs17 viz panels stay byte-identical: the master-only branch loads only each reinsurer's LATEST quarter; show new rows vs latest."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "812b007"
for f, key in (("CSM_amortization.json", ("원보험사코드", "공시분기", "경과차년")), ("CSM_sensitivity.json", ("원보험사코드", "공시분기", "순번"))):
    old = json.loads(subprocess.run(["git", "show", f"{BASE}:{f}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
    new = json.loads((ROOT / f).read_text(encoding="utf-8"))
    ko = {tuple(r[k] for k in key) for r in old}
    added = [r for r in new if tuple(r[k] for k in key) not in ko]
    qs = {}
    for r in new:
        if r["원보험사코드"].startswith("KR11"):
            qs.setdefault(r["원보험사코드"], set()).add(r["공시분기"])
    def k(q): return (int(q[:4]), int(q[5]))
    print(f)
    for code in sorted({r["원보험사코드"] for r in added}):
        aq = sorted({r["공시분기"] for r in added if r["원보험사코드"] == code}, key=k)
        latest = max(qs[code], key=k)
        print(f"  {code}: added quarters {aq}; latest quarter in master {latest}; added latest? {latest in aq}")
