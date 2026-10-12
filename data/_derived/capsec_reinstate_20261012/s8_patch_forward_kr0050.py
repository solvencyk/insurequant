# -*- coding: utf-8 -*-
"""Request 2: the 하나손해 ledger got an estimated row -> re-run the forward model for KR0050 ONLY and patch that row in
kics_forward_capital.json cell-wise. Proves the projections are identical (the estimated row has no call date -> no call event);
only the outstanding/classification/confidence bookkeeping fields move. Other 46 rows are not touched."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
import scripts.forward_capital_simulation as F  # noqa: E402

man_dirs = sorted(p for p in (ROOT / "output" / "kics_forward_capital").iterdir() if (p / "manifest.json").exists())
man = json.loads((man_dirs[-1] / "manifest.json").read_text(encoding="utf-8"))
F.BASELINE_QUARTER = man["baseline_quarter"]
F._args.bonds_source = man["bonds_source"]
# the module computed its tier-file paths at import time from the default quarter; use the quarter the deployed forward was built with
F.TIER1_JSON = ROOT / man["tier1_utilization_json"].replace("\\", "/")
F.TIER2_JSON = ROOT / man["tier2_utilization_json"].replace("\\", "/")
baselines = F.load_kics_baselines()
bonds_per, _ = F.load_outstanding_bonds()
t1, t2 = F.load_utilization()
code = "KR0050"
bonds = bonds_per[code]
row = F.simulate_one(code, baselines[code], bonds)
cov = F._bond_coverage(code, bonds, bonds_per)
row["bond_coverage"] = cov
row["confidence"] = F.compute_confidence(code, bonds, t1, t2, bond_coverage=cov)

path = ROOT / "kics_forward_capital.json"
raw = path.read_text(encoding="utf-8")
doc = json.loads(raw)
i = next(k for k, r in enumerate(doc) if r["insurer_code"] == code)
old = doc[i]
assert [p for p in old["projections"]] == [p for p in row["projections"]], "projections must be identical"
changed = sorted(k for k in set(old) | set(row) if old.get(k) != row.get(k))
print("KR0050 changed fields:", changed)
for k in changed:
    print("  ", k, "|", json.dumps(old.get(k), ensure_ascii=False)[:160], "->", json.dumps(row.get(k), ensure_ascii=False)[:160])
# keep key order of the old row, append new keys at the end
new_row = {k: row[k] for k in old if k in row}
new_row.update({k: v for k, v in row.items() if k not in new_row})
doc[i] = new_row
indent = 1 if raw.startswith('[\n {') else 2
text = json.dumps(doc, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else "")
path.write_text(text, encoding="utf-8")
# other rows untouched
orig = json.loads((HERE / "before3" / "kics_forward_capital.json").read_text(encoding="utf-8"))
now = json.loads(path.read_text(encoding="utf-8"))
diff_codes = [a["insurer_code"] for a, b in zip(orig, now) if a != b]
print("rows differing from before3:", diff_codes, "| indent", indent)
