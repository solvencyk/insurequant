import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_golden_input_fingerprints as V
keys = ["PL_breakdown", "user_pl_cells", "pl_breakdown", "IFRS17_BS", "CSM_waterfall", "user_csm_cells", "provenance"]
for name, spec in V.SPECS.items():
    hits = [p for p in spec["inputs"] if any(k in p for k in keys)]
    print(name, "| inputs touching PL/CSM masters:", hits)
