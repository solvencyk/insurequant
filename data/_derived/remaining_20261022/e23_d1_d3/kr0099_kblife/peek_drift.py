# -*- coding: utf-8 -*-
"""KR0099 probe (read-only): the 4 pre-existing live-vs-fresh-build drift cells of KR0099 2023.3Q (items 16 / 22 / 23 / 24): live master, fresh build with the LIVE gold, builder source, provenance."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kyobo_pl_restate_dryrun_20261021")
sys.stdout.reconfigure(encoding="utf-8")
import sim_pl_builder as S  # noqa: E402

TMP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0099_tmp")
TMP.mkdir(parents=True, exist_ok=True)
rows, _n = S.simulate(ROOT / "data/_gold/user_pl_cells.json", TMP / "peek_master.json")
(TMP / "peek_master.json").unlink()
base = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))}
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
for k in [("KR0099", i, "2023.3Q") for i in (16, 22, 23, 24)]:
    print(k, "live", live[k]["값"], live[k].get("값_당분기"), "| fresh build", base[k]["값"], base[k].get("값_당분기"), "| builder source", src.get(k, {}).get("값"), "| gold", G.get(k, {}).get("값"))
dr = json.loads((Path(__file__).resolve().parent / "drift_before.json").read_text(encoding="utf-8"))
print("drift cells of KR0099:", [x for x in dr["drift_all"] if x[0] == "KR0099"])
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
for c in prov["cells"]:
    if c["company_code"] == "KR0099" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q"):
        print(c["quarter"], c["item_block"], json.dumps({k: v for k, v in c.items() if k not in ("company_code", "quarter", "item_block")}, ensure_ascii=False)[:400])
