# -*- coding: utf-8 -*-
"""Physical spot check: for sampled mismatch rows, re-open the cited filing line(s) and look for the claimed value among the numbers printed on those physical lines (unit-scaled)."""
import csv, re, sys, random, json
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rows = list(csv.DictReader(open("mismatches_part2.csv", encoding="utf-8-sig")))
rows = [r for r in rows if r["filing"].startswith("data/") and r["source"].split(":")[0] in ("stmt", "note", "csm")]
random.seed(11)
by = {}
for r in rows:
    by.setdefault((r["source"], r["company"]), []).append(r)
pick = []
for k, v in sorted(by.items()):
    pick.append(v[0])
    if len(v) > 3: pick.append(v[len(v) // 2])
TAG = re.compile(r"<[^>]+>")
NUM = re.compile(r"\(?-?[\d,]+(?:\.\d+)?\)?")
cache = {}
ok = bad = 0
out = []
for r in pick:
    f = r["filing"]
    lns = [int(x) for x in re.findall(r"L(\d{2,7})|(?<![\d.])(\d{4,7})(?![\d,.])", r["line"]) for x in x if x]
    if not lns: continue
    if f not in cache:
        cache[f] = open(ROOT + f, encoding="utf-8", errors="replace").read().split("\n")
    L = cache[f]
    want = abs(float(r["latest"]))
    found = None
    printed = []
    for ln in lns[:3]:
        txt = TAG.sub(" ", L[ln - 1]).replace("&nbsp;", " ")
        for m in NUM.findall(txt):
            try: v = float(m.replace(",", "").replace("(", "").replace(")", ""))
            except: continue
            printed.append(m)
            for sc in (1.0, 1e6, 1e3, 100.0):
                if abs(v / sc - want) <= 1.0 or (sc == 100.0 and abs(v / sc - want / 100.0) <= 0.06):
                    found = (m, ln, sc)
    status = "PASS" if found else "NOT-CONFIRMED"
    if found: ok += 1
    else: bad += 1
    out.append(f"{status} {r['company']} {r['quarter']} item {r['item']} latest={r['latest']} src={r['source']} {f.split('/')[-1]} lines={lns[:3]} found={found} printed_on_line={printed[:4]}")
print("\n".join(out))
print("PASS", ok, "NOT-CONFIRMED", bad)
