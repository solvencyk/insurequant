import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
res = json.load(open("p1_stmt.json", encoding="utf-8"))
print(len(res), sum(1 for v in res.values() if v["err"]))
errs = [(k, v["err"] or v.get("err_prior") or v.get("err_cur")) for k, v in res.items() if v["err"] or v.get("err_prior") or v.get("err_cur")]
for e in errs: print("ERR", e)
def later_q(q): return f"{int(q[:4])+1}.{q[5:]}"
cal = collections.Counter(); calbad = []
mm = collections.Counter(); tot = collections.Counter()
for k, v in res.items():
    c, q = k.split("|")
    for i, d in v["cur_calib"].items():
        if not isinstance(d, dict): continue
        m = pl.get((c, i, later_q(q)))
        if m is None: cal["no_master"] += 1; continue
        if abs(m - d["val"]) < 0.0015 or abs(m-d["val"])<1.0: cal["match"] += 1
        else: cal["diff"] += 1; calbad.append((k, i, m, d["val"]))
print(cal); print(calbad[:30])
