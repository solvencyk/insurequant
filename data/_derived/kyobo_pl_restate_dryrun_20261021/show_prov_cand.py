"""Read-only: KR0073 PL provenance records, live vs candidate (sim/prov_pl_cand.json), for the 6 refreshed quarters."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
live = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
cand = json.loads((HERE / "sim" / "prov_pl_cand.json").read_text(encoding="utf-8"))
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]


def pick(d):
    return {(c["company_code"], c["quarter"], c["item_block"]): c for c in d["cells"] if c["company_code"] == "KR0073" and c["quarter"] in QS}


a, b = pick(live), pick(cand)
for k in sorted(a, key=lambda x: (x[1], x[2])):
    for tag, rec in (("LIVE", a[k]), ("CAND", b[k])):
        sf = [(e.get("how"), e.get("file"), e.get("items")) for e in rec.get("source_files", [])]
        print(f"{tag} {k[1]} {k[2]:15s} source_id={rec.get('source_id')} resolution={rec.get('resolution')} owner_override={rec.get('owner_override')} published_items={rec.get('published_items')}")
        print(f"      source_file={rec.get('source_file')}")
        for e in sf:
            print(f"      - {e}")
print("top-level keys diff:", sorted(set(cand) ^ set(live)))
print("cells count live/cand:", len(live["cells"]), len(cand["cells"]))
