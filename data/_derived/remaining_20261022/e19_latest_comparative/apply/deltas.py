import json, sys
sys.stdout.reconfigure(encoding="utf-8")
man = json.load(open("e19_manifest.json", encoding="utf-8"))
l = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8"))}
by = {}
for g in man["gold_set"]:
    k = (g["원보험사코드"], g["항목번호"], g["공시분기"])
    by.setdefault((k[0], k[2]), {})[k[1]] = (g["값"] - g["was"]) / 100
out = []
rng = {}
for (c, q), d in sorted(by.items()):
    out.append(f"{c} {q}: " + ", ".join(f"{i}:{v:+.1f}" for i, v in sorted(d.items()) if i in (1, 17, 24, 25, 31)))
    for i in (1, 17, 24, 25, 31):
        if i in d:
            rng.setdefault(i, []).append(d[i])
for i, v in rng.items():
    out.append(f"item {i}: min {min(v):+.1f} max {max(v):+.1f} eok over {len(v)} buckets")
open("deltas.txt", "w", encoding="utf-8").write("\n".join(out))
