# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import run_validation  # noqa: E402

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
result = run_validation(data, tolerance=2.0)
for f in result["findings"]:
    if f.get("rule") == "19_market" and f.get("status") == "RED":
        print(f)
