# -*- coding: utf-8 -*-
"""Phase 1 (read-only): statement-based items (1, 15..32 and life 3/8/2) of the LATER filing's prior-period cumulative column vs the working-tree master, for every touched company-quarter.
Also calibrates the reader on the same filing's CURRENT column vs the master at quarter+4 (reader fidelity)."""
import json, sys, traceback, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
import e21_life as L
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
t = json.load(open("s01_touched.json", encoding="utf-8"))
cq = set()
for k, v in t.items():
    if k.startswith("PL") or k.startswith("CSM"):
        for key in v:
            c, q = key.split("|"); cq.add((c, q))
cq = sorted(cq)
def later(q): return f"FY{int(q[:4]) + 1}_Q{q[5]}"
def fy_of(q): return f"FY{int(q[:4])}_Q{q[5]}"
res = {}
for c, q in cq:
    key = f"{c}|{q}"
    rec = {"later_fy": later(q), "prior": {}, "cur_calib": {}, "err": None}
    try:
        st = R.Stmt(c, later(q))
    except Exception as e:
        rec["err"] = f"Stmt: {type(e).__name__}: {str(e)[:200]}"; res[key] = rec; continue
    rec["file"] = st.rel; rec["unit"] = st.unit
    for role in ("prior", "cur"):
        try:
            vec = R.read_vector(st, role, "cum")
            out = {}
            for i, v in vec.items():
                if isinstance(i, int):
                    ln = v["parts"][0].line if v["parts"] else None
                    out[str(i)] = dict(val=v["val"], line=ln, absent=bool(v.get("absent")))
            try:
                p15 = L.presence_015(st, role, "cum")
                out["15"] = dict(val=p15["val"], line=(p15["parts"][0]["line"] if p15["parts"] else None), absent=not p15["present"])
            except Exception as e:
                out["15_err"] = str(e)[:100]
            if c in L.SPEC:
                try:
                    lr = L.life_is_items(c, later(q), role, "cum", st=st)
                    for i in (2, 3, 8):
                        out[str(i)] = dict(val=lr[i]["val"], line=lr[i]["parts"][0]["line"] if lr[i]["parts"] else None, absent=False)
                except Exception as e:
                    out["life_err"] = str(e)[:150]
            rec["prior" if role == "prior" else "cur_calib"] = out
        except Exception as e:
            rec["err_" + role] = f"{type(e).__name__}: {str(e)[:250]}"
    res[key] = rec
    print(key, "ok" if not rec["err"] else rec["err"], len(rec["prior"]), len(rec["cur_calib"]), flush=True)
json.dump(res, open("p1_stmt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
