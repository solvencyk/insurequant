# -*- coding: utf-8 -*-
"""KR0104 read-only: run the real validate_master_tables._check_pl_bridge on the KR0104 blocks, live vs merged (plan cells adopted).  Nothing is written except this folder's txt."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
import validate_master_tables as V   # import only (main() guarded?)

plan = json.loads((HERE / "plan_KR0104.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
pl_old, pl_new = {}, {}
adopt = {(c["quarter"], c["item"]): c["new"] for c in plan["cells"]}
for r in live:
    if r["원보험사코드"] != "KR0104" or r.get("값") is None:
        continue
    key = ("KR0104", r["공시분기"])
    pl_old.setdefault(key, {})[r["항목명"].replace(" ", "")] = r["값"]
    pl_new.setdefault(key, {})[r["항목명"].replace(" ", "")] = adopt.get((r["공시분기"], r["항목번호"]), r["값"])
out = []
for tag, pl in (("live", pl_old), ("merged", pl_new)):
    res = V._check_pl_bridge(pl, source_ids={})
    out.append("%s: pb_pass=%s pb_fail=%s pb_skip=%s" % (tag, res[0], res[1], res[2]))
(HERE / "KR0104_gate_bridge.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("ok")
