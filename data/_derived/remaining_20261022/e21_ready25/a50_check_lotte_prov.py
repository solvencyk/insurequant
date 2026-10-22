# -*- coding: utf-8 -*-
"""READ-ONLY: provenance blocks of 롯데손보 KR0003 2023.1Q in the PL sidecar (live vs HEAD) and the CSM sidecar owner flags."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
live = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
head = json.loads(subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown_provenance.json"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
def blocks(d, code, q):
    return {c["item_block"]: c for c in d["cells"] if c["company_code"] == code and c["quarter"] == q}
for tag, d in (("HEAD", head), ("LIVE", live)):
    b = blocks(d, "KR0003", "2023.1Q")
    print(tag, "KR0003 2023.1Q blocks:", sorted(b))
    for k, c in sorted(b.items()):
        print("   ", k, {f: (str(v)[:80]) for f, v in c.items() if f not in ("cells", "items")})
