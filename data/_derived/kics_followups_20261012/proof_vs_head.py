"""proof_vs_head.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY independent proof of the live kics_disclosure.json vs git HEAD.
 (1) every HEAD row is still present, same relative order
 (2) the cells that differ from HEAD == exactly the planned edit cells of the given plans (value-level, old -> new)
 (3) the keys that are new vs HEAD == exactly the planned insert keys, each listed with its 값 / 값_적용후
 (4) rows of every company outside the touched set equal HEAD (list equality incl. order)
usage: proof_vs_head.py --plans a,b
"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_followups_20261012")
from lib import *  # noqa: F401,F403,E402

utf8_stdout()
names = [x for x in sys.argv[sys.argv.index("--plans") + 1].split(",") if x]
mp = merge_plans(names)
live, head = read_rows(), head_rows()
print(f"live sha {sha_file(MASTER)[:12]} rows {len(live)} | HEAD rows {len(head)}")
lk, hk = {key(r): r for r in live}, {key(r): r for r in head}
assert len(lk) == len(live) and len(hk) == len(head), "duplicate keys"
assert all(k in lk for k in hk), "a HEAD row is missing"
pos = {key(r): i for i, r in enumerate(live)}
hp = [pos[key(r)] for r in head]
assert hp == sorted(hp), "relative order of HEAD rows changed"
print(f"(1) all {len(head)} HEAD rows present in the same relative order: True")
diff = []
for k, hr in hk.items():
    lr = lk[k]
    for f in sorted(set(hr) | set(lr)):
        if hr.get(f, "<nokey>") != lr.get(f, "<nokey>"):
            diff.append((k, f, hr.get(f, "<nokey>"), lr.get(f, "<nokey>")))
planned = {(e["code"], e["q"], e["item"], e["field"]): (e["old"], e["new"]) for e in mp["edits"]}
got = {(*k, f): (o, n) for k, f, o, n in diff}
assert got == planned, f"cell diffs differ from the plan: {set(got) ^ set(planned)}"
print(f"(2) cells changed vs HEAD: {len(diff)} == planned {len(planned)} (exactly):")
for k, f, o, n in diff:
    print(f"      {k[0]} {k[1]} item{k[2]} {f}: {o!r} -> {n!r}")
newk = [key(r) for r in live if key(r) not in hk]
pk = [key(i["row"]) for i in mp["inserts"]]
assert sorted(newk) == sorted(pk), "new keys differ from the planned inserts"
print(f"(3) keys new vs HEAD: {len(newk)} == planned {len(pk)} (exactly):")
for r in live:
    if key(r) not in hk:
        print(f"      {r['원보험사코드']} {r['공시분기']} item{r['항목번호']:>2} 값={r['값']!r} 후={r.get('값_적용후', '<nokey>')!r}  {r['항목명']}")
touched = {k[0] for k in planned} | {k[0] for k in pk}
assert [r for r in live if r["원보험사코드"] not in touched] == [r for r in head if r["원보험사코드"] not in touched]
n_out = sum(1 for r in live if r["원보험사코드"] not in touched)
print(f"(4) rows of all companies outside {sorted(touched)}: {n_out} rows identical to HEAD incl. order: True")
