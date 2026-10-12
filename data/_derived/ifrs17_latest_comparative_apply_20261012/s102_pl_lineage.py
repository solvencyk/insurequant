"""Read-only: PL source lineage of every 2023.1Q-2023.4Q bucket (PL_breakdown_provenance.json): source_id, how, per company.
prints a table company x quarter -> source_id/how-set, and lists the DISCLOSURE (PDF) buckets of 2023.2Q."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
names = {r["원보험사코드"]: r["원수사명"] for r in pl}
tab = defaultdict(dict)
for c in prov["cells"]:
    if c["quarter"].startswith("2023."):
        hows = sorted({f.get("how", "?") for f in c.get("source_files", [])})
        tab[c["company_code"]][c["quarter"]] = f"{c.get('source_id')}:{'+'.join(hows)}"
qs = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
print(f"{'code':<7}{'company':<14}" + "".join(f"{q:<34}" for q in qs))
for code in sorted(tab):
    print(f"{code:<7}{names.get(code, '')[:10]:<14}" + "".join(f"{tab[code].get(q, '-')[:32]:<34}" for q in qs))
