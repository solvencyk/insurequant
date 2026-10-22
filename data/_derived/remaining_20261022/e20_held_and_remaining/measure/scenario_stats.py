"""scenario_stats: cell-level diff of each candidate master (scratchpad cand/) against the start snapshot: value cells, single-quarter (값_당분기) cells, auto-follow cells (single-quarter changed while the value is unchanged),
rows still carrying a gold overlay, per-company counts.  READ-ONLY -> scenario_stats.json/.txt"""
import json, sys
from collections import Counter
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
SP = M.SNAP.parent / "cand"
base_pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): (r["값"], r.get("값_당분기")) for r in M.jload(M.SNAP / "PL_breakdown.json")}
base_cs = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): (r["값"], r.get("값_당분기")) for r in M.jload(M.SNAP / "CSM_waterfall.json")}
out, txt = {}, []
for scn in sys.argv[1:]:
    st = {}
    for kind, base in (("PL", base_pl), ("CSM", base_cs)):
        p = SP / (f"{scn}_PL_breakdown.json" if kind == "PL" else f"{scn}_CSM_waterfall.json")
        if not p.exists():
            st[kind] = {"value": 0, "dangi": 0, "autofollow": 0}
            continue
        v = d = a = 0
        per = Counter()
        for r in M.jload(p):
            k = (r["원보험사코드"], str(r["항목번호"]), r["공시분기"])
            b = base.get(k)
            if b is None:
                continue
            vc = (r["값"] != b[0]) and not (r["값"] is not None and b[0] is not None and abs(r["값"] - b[0]) < 1e-9)
            dc = (r.get("값_당분기") != b[1]) and not (r.get("값_당분기") is not None and b[1] is not None and abs(r.get("값_당분기") - b[1]) < 1e-9)
            v += vc; d += dc; a += (dc and not vc)
            if vc: per[r["원보험사코드"]] += 1
        st[kind] = {"value": v, "dangi": d, "autofollow": a, "per_company_value": dict(per)}
    out[scn] = st
    txt.append(f"{scn}: PL value={st['PL']['value']} dangi={st['PL']['dangi']} (auto-follow {st['PL']['autofollow']}) | CSM value={st['CSM']['value']} dangi={st['CSM']['dangi']} (auto-follow {st['CSM']['autofollow']})")
M.MEASURE.joinpath("scenario_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("scenario_stats.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
