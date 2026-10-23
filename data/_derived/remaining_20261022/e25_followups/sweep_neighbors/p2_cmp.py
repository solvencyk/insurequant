import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
g = json.load(open("p2_generic.json", encoding="utf-8"))
def lq(q): return f"{int(q[:4])+1}.{q[5:]}"
rows = []; stat = collections.defaultdict(collections.Counter)
for k, rec in sorted(g.items()):
    c, q = k.split("|")
    if "prior" not in rec: stat[c]["no_read"] += 1; continue
    for it in ("4", "5", "9", "10"):
        pr = rec["prior"].get(it) or rec["prior"].get(int(it)) if False else rec["prior"].get(it)
        cu = rec.get("cur", {}).get(it)
        m = pl.get((c, it, q)); mlater = pl.get((c, it, lq(q)))
        if not pr: stat[c]["no_cand_" + it] += 1; continue
        # calibration: candidate index whose |cur| matches |master(Q+4)|
        j = None
        if cu and mlater is not None:
            for idx, x in enumerate(cu):
                if abs(abs(x["val"]) - abs(mlater)) < 0.5: j = idx; break
        sign = 1 if it in ("4", "5") else -1
        if j is not None and j < len(pr):
            val = sign * abs(pr[j]["val"]); calib = "CAL"
        elif len(pr) == 1:
            val = sign * abs(pr[0]["val"]); calib = "UNCAL1"; j = 0
        else:
            stat[c]["ambiguous_uncal_" + it] += 1; continue
        if m is None:
            stat[c]["master_blank"] += 1; rows.append((c, q, it, None, val, None, calib, pr[j]["line"], pr[j]["label"])); continue
        d = val - m
        stat[c][calib + ("_eq" if abs(d) < 1 else "_DIFF")] += 1
        if abs(d) >= 1: rows.append((c, q, it, m, val, d, calib, pr[j]["line"], pr[j]["label"]))
for c, v in sorted(stat.items()): print(c, dict(v))
print()
for r in rows: print(r)
