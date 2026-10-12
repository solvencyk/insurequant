import csv, os, re
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
held = list(csv.DictReader(open(src + "held_blocks.csv", encoding="utf-8-sig")))
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
out = open(here + "/k3_gold3.txt", "w", encoding="utf-8")
g = [r for r in held if r["dryrun_verdict"] == "gold 충돌"]
out.write(f"gold-conflict held rows: {len(g)}\n")
def items(s):
    return set(int(x) for x in re.findall(r"\d+", s))
inter = []
for r in g:
    its = items(r["items"])
    for a in applied:
        if a["master"] == r["master"] and a["code"] == r["code"] and a["quarter"] == r["quarter"] and (not its or int(a["item"]) in its):
            inter.append((r["master"], r["code"], r["quarter"], a["item"], r["items"]))
out.write(f"applied cells inside a gold-conflict block (same master/company/quarter and listed items): {len(inter)}\n")
for x in inter: out.write(f"   {x}\n")
# same (master, company, quarter) regardless of items
bl = set((r["master"], r["code"], r["quarter"]) for r in g)
sq = sorted(set((a["master"], a["code"], a["quarter"]) for a in applied) & bl)
out.write(f"same master+company+quarter overlap (any item): {sq}\n")
for r in g:
    if (r["master"], r["code"], r["quarter"]) in sq: out.write(f"   held: {r['master']} {r['code']} {r['quarter']} items={r['items']} reason={r['reason'][:150]}\n")
