"""p_lotte_run: driver of the 롯데 prior-column Tier-2 prototype (functions in lotte_lib.py).  Writes p_lotte.json/.txt.  READ-ONLY.
usage: p_lotte_run.py [quarters csv]"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import lotte_lib as L  # noqa: E402
import fsapi as F  # noqa: E402
import mlib as M  # noqa: E402
import prod as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0003"
pl, names, inames = M.load_pl()
qs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]
res, txt = {}, []


def legs(d):
    j = None
    if d.get("_jang_rev") is not None and d.get("_jang_cost") is not None:
        j = (d["_jang_rev"] - d["_jang_cost"]) + ((d.get("_jang_rerev") or 0) - (d.get("_jang_recost") or 0))
    return {"2(장기)": j, "13": d.get(13), "14": d.get(14), "4": d.get(4), "5": d.get(5), "6": d.get(6), "9": d.get(9), "10": d.get(10), "11": d.get(11)}


for q in qs:
    m = pl[(CODE, q)]
    t_prior, _ = F.prior(CODE, q)
    tabs_o = P.tables_for(CODE, M.fy_of(q))
    nm_o, o, lo_o = L.run(tabs_o, False)
    del tabs_o
    tabs_l = P.tables_for(CODE, M.later_fy(q))
    nm_p, p, lo_p = L.run(tabs_l, True)
    del tabs_l
    lo, lp = legs(o), legs(p)
    target = None if not t_prior else t_prior.get(1) - (t_prior.get(15) or 0) + abs(t_prior.get(16) or 0)
    sp = sum(v for k, v in lp.items() if k in ("2(장기)", "13", "14") and v is not None)
    res[q] = {"layout_orig": nm_o, "layout_prior": nm_p, "same_run": lo, "master": {str(k): m.get(k) for k in (2, 3, 8, 13, 14, 4, 5, 6, 9, 10, 11)},
              "prior_run": lp, "prior_tier2_raw": {str(k): v for k, v in p.items()}, "tables_prior": lo_p, "target_legs": target, "sum_prior": sp,
              "resid_prior": None if target is None else sp - target}
    txt.append(f"=== {q} later {M.later_fy(q)} layout orig={nm_o} prior={nm_p} tables(line_no)={lo_p}  target legs={target}")
    txt.append(f"   master item2/13/14 = {m.get(2)} / {m.get(13)} / {m.get(14)} ; 4/5/6/9/10/11 = {[m.get(k) for k in (4, 5, 6, 9, 10, 11)]}")
    txt.append(f"   same-filing run (fidelity) {lo}")
    txt.append(f"   prior-col run              {lp}")
    txt.append(f"   sum legs prior = {sp:,.1f}  resid vs target = {None if target is None else round(sp - target, 3)}")
M.MEASURE.joinpath("p_lotte.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("p_lotte.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
