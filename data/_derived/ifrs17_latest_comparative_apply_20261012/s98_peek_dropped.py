"""Read-only: cells present in plan_diff.json (dry-run candidate vs live) but absent from plan_final.json (the dropped cells), with old/new values."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
pd_ = json.loads((HERE / "plan_diff.json").read_text(encoding="utf-8"))
pf = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
final = {(c["master"], c["code"], c["quarter"], c["item"]) for c in pf["cells"]}
mname = {"CSM": "CSM_waterfall", "PL": "PL_breakdown", "BS": "IFRS17_BS"}
print("plan_diff cells:", {k: len(v) for k, v in pd_.items() if isinstance(v, list)})
for dom, lst in pd_.items():
    if dom == "notes":
        for n in lst:
            print("NOTE", n)
        continue
    for c in lst:
        k = (mname[dom], c["code"], c["quarter"], c["item"])
        if k not in final:
            print("DROPPED", k, "old", c["old"], "new", c["new"])
extra = [c for c in pf["cells"] if c["kind"] == "latest_comparative" and (c["master"], c["code"], c["quarter"], c["item"]) not in {(mname[d], x["code"], x["quarter"], x["item"]) for d in ("CSM", "PL", "BS") for x in pd_[d]}]
print("cells in plan_final (latest_comparative) that are not in plan_diff:", len(extra))
for c in extra[:40]:
    print("  EXTRA", c["master"], c["code"], c["quarter"], c["item"], c["old"], "->", c["new"], "|", c["source_ref"][:90])
