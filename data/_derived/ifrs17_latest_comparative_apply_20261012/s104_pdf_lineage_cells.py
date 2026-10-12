"""Read-only: list every PL bucket whose income_statement block comes from the 경영공시 PDF summary (how=disclosure_summary_pl), with its PDF file, items and master values."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in pl}
N = {r["원보험사코드"]: r["원수사명"] for r in pl}
out = []
for c in prov["cells"]:
    for f in c.get("source_files", []):
        if f.get("how") == "disclosure_summary_pl":
            out.append({"code": c["company_code"], "name": N.get(c["company_code"], ""), "quarter": c["quarter"], "pdf": f["file"], "items": f["items"],
                        "values": {i: M.get((c["company_code"], c["quarter"], i)) for i in f["items"]}})
print("PDF-lineage buckets:", len(out))
byq = Counter(o["quarter"] for o in out)
print(sorted(byq.items()))
byc = defaultdict(list)
for o in out:
    byc[(o["code"], o["name"])].append(o["quarter"])
for k, v in sorted(byc.items()):
    print(k, len(v), v[:3], "...", v[-1])
(HERE / "pdf_lineage_cells.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
