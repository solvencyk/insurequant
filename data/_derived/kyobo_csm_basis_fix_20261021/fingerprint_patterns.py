import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_golden_input_fingerprints as V
touched = ["CSM_waterfall.json", "user_csm_cells.json", "csm_amort_identity_ledger.json", "CSM_waterfall_provenance.json", "gold_overlay_ledger.json", "test_rule_coverage_manifest"]
for name, spec in V.SPECS.items():
    hits = [p for p in spec["inputs"] if any(t in p for t in touched) or "_gold" in p or "provenance" in p]
    code_hits = [e for e in spec.get("code", []) if any(t in e for t in touched)]
    print(name, "| input patterns touching my files:", hits, "| code entries:", code_hits)
