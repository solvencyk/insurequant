# -*- coding: utf-8 -*-
"""read-only: does the sandbox emitter reproduce the KR0072 provenance blocks in the PRE-LOAD state (backup masters + backup gold vs backup sidecar)?  Same for the POST-LOAD state.  Lists the blocks that differ."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8")
import e23_apply as A  # noqa: E402

ROOT = A.ROOT
BK = A.BACKUP
SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0072_load2_sim")   # byte-identical to what --apply wrote (c18_sim_vs_applied.txt)
for tag, base in (("PRE-LOAD (backup)", BK), ("POST-LOAD (simulation = applied)", SIM)):
    rows = json.loads((base / "PL_breakdown.json").read_text(encoding="utf-8"))
    gold = json.loads((base / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    prov = json.loads((base / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
    sub = [r for r in rows if r["원보험사코드"] == "KR0072"]
    emit = A.run_emitter(sub, gold, "c13_" + tag.split()[0].lower().replace("-", ""))
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in prov["cells"] if c["company_code"] == "KR0072"}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit["cells"] if c["company_code"] == "KR0072"}
    bad = sorted(k for k in set(lk) | set(ek) if lk.get(k) != ek.get(k))
    print(f"{tag}: sidecar blocks {len(lk)}, emitter blocks {len(ek)}, differing {len(bad)}: {[(k[1], k[2]) for k in bad]}")
    for k in bad:
        a, b = lk.get(k), ek.get(k)
        print("    ", k, "sidecar keys-diff:", {f: (a or {}).get(f) for f in ("source_id", "resolution", "published_items")}, "| emitter:", {f: (b or {}).get(f) for f in ("source_id", "resolution", "published_items")})
