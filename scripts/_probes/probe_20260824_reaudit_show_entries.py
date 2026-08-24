# -*- coding: utf-8 -*-
"""Read-only: dump the exemption-registry entries for the re-audit targets to a UTF-8 file."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_registry_entries.txt"

TARGETS = [
    ("KR0094", "2024.2Q"), ("KR0094", "2024.4Q"),
    ("KR0094", "2025.2Q"), ("KR0094", "2025.4Q"),
    ("KR0032", "2024.3Q"), ("KR0032", "2025.4Q"),
]

data = json.loads(REG.read_text(encoding="utf-8"))
buf = []
for e in data["entries"]:
    key = (e.get("company"), e.get("quarter"))
    if key in TARGETS:
        buf.append("=" * 100)
        buf.append(json.dumps(e, ensure_ascii=False, indent=2))
buf.append("=" * 100)
buf.append("CONTRACT: " + json.dumps(data.get("_residual_pin_contract"), ensure_ascii=False, indent=2))
buf.append("VERIFY CONTRACT: " + json.dumps(data.get("_verify_contract"), ensure_ascii=False, indent=2))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT, len(buf), "blocks")
