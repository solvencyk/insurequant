import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
res = json.load(open("p1_stmt.json", encoding="utf-8"))
cnt = collections.defaultdict(lambda: [0, 0, 0, 0])  # compared, equal, differ, missing master
rows = []
for k, v in sorted(res.items()):
    c, q = k.split("|")
    for i, d in v["prior"].items():
        if not isinstance(d, dict): continue
        m = pl.get((c, i, q))
        if m is None:
            cnt[c][3] += 1
            if abs(d["val"]) >= 0.5 and not d.get("absent"): rows.append((c, q, i, None, d["val"], None, d["line"]))
            continue
        cnt[c][0] += 1
        diff = d["val"] - m
        if abs(diff) < 1.0: cnt[c][1] += 1
        else:
            cnt[c][2] += 1; rows.append((c, q, i, m, d["val"], diff, d["line"]))
for c, v in sorted(cnt.items()): print(c, "compared", v[0], "equal(<1mn)", v[1], "differ", v[2], "master-missing", v[3])
print()
for r in rows: print(r)
