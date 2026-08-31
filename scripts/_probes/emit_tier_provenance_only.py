# -*- coding: utf-8 -*-
"""Write ONLY the tier1_utilization / tier2_utilization provenance sidecars from
scripts/emit_capsec_provenance.py's own build_cells(), deliberately skipping
forward_capital (out of scope for this ticket -- its sidecar has unrelated pre-existing
drift from a 2026-08-31 rerun that predates this session; not touching it here so as not
to collide with whichever other session owns that master)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import emit_capsec_provenance as ecp  # noqa: E402

built = ecp.build_cells()
for master in ("tier1_utilization", "tier2_utilization"):
    doc = built[master]
    path = ROOT / ecp.MASTERS[master][1]
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    same = bool(old) and [{k: v for k, v in c.items() if k != "_note"} for c in old.get("cells", [])] == \
        [{k: v for k, v in c.items() if k != "_note"} for c in doc["cells"]]
    if same:
        print(f"unchanged: {path.name}")
        continue
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[wrote] {path.name}  cell={json.dumps(doc['cells'][0], ensure_ascii=False)}")

print("\n(forward_capital sidecar intentionally NOT touched -- out of this ticket's scope)")
