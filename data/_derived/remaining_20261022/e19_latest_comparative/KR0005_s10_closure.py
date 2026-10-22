"""Read-only. Closure of the MERGED vector per bucket with the production gate code (validate_master_tables._check_pl_bridge, source_ids={} = strict)
plus the identities named in the ticket."""
import sys, os, json, io, copy
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import validate_master_tables as V
EVD = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
CMP = json.loads((EVD / "KR0005_s8_compare.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
names = {}; vals = {}
for r in pl:
    if r["원보험사코드"] == "KR0005":
        names[r["항목번호"]] = V.norm(r["항목명"]); CO = r["원수사명"]
        vals[(r["공시분기"], r["항목번호"])] = r.get("값")
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
gold_cells = {(e["공시분기"], e["항목번호"]): e["값"] for e in gold["set"] if e["원보험사코드"] == "KR0005"}
out, res = [], {}
for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"):
    old = {names[k]: vals.get((q, k)) for k in names}
    new = dict(old); adopt = {}
    for k, c in CMP[q].items():
        k = int(k)
        if "DIFF" in c["flags"] and c["later_xml"] is not None:
            adopt[k] = (c["master"], c["later_xml"])
            new[names[k]] = c["later_xml"]
    gold_hit = [k for k in adopt if (q, k) in gold_cells]
    gold_in_block = sorted(k for (qq, k) in gold_cells if qq == q)
    r_old = V._check_pl_bridge({(CO, q): old}, None, [], None, {}, None)
    r_new = V._check_pl_bridge({(CO, q): new}, None, [], None, {}, None)
    def g(m, k): return m.get(names[k])
    def idt(m):
        d = {}
        d["20-(1+17)"] = g(m, 20) - g(m, 1) - g(m, 17)
        d["22-24-23"] = g(m, 22) - g(m, 24) - g(m, 23)
        d["31-(24+25)"] = g(m, 31) - g(m, 24) - g(m, 25)
        d["25-parts"] = g(m, 25) - sum((g(m, k) or 0) for k in (26, 27, 28, 29, 30, 32))
        d["17-(18+19)"] = g(m, 17) - g(m, 18) - g(m, 19)
        d["22-(20+21)"] = g(m, 22) - g(m, 20) - g(m, 21)
        lob = (g(m, 2) or 0) + (g(m, 13) or 0) + (g(m, 14) or 0)
        d["1-legs(bare)"] = g(m, 1) - lob
        d["1-(legs+15-16)"] = g(m, 1) - (lob + (g(m, 15) or 0) - (g(m, 16) or 0))
        return d
    io_, in_ = idt(old), idt(new)
    out.append(f"== {q}: adopted {len(adopt)} cells {sorted(adopt)}; owner-gold cells in this block: items {gold_in_block}; gold overlap with adopted: {gold_hit}")
    out.append(f"   gate _check_pl_bridge old: pass={r_old[0]} fail={r_old[1]} skip={r_old[2]}")
    out.append(f"   gate _check_pl_bridge merged: pass={r_new[0]} fail={r_new[1]} skip={r_new[2]}")
    for kk in io_:
        out.append(f"   {kk:16s} old {io_[kk]:+12.3f}   merged {in_[kk]:+12.3f}")
    res[q] = {"adopt": {str(k): v for k, v in adopt.items()}, "gold_in_block": gold_in_block, "gold_overlap": gold_hit,
              "gate_old": {"pass": r_old[0], "fail": r_old[1], "skip": r_old[2]}, "gate_merged": {"pass": r_new[0], "fail": r_new[1], "skip": r_new[2]},
              "identities_old": io_, "identities_merged": in_}
(EVD / "KR0005_s10_closure.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
(EVD / "KR0005_s10_closure.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
