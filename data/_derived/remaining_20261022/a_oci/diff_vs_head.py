"""Read-only: independent JSON diff of every file changed by the apply vs git HEAD (cell level)."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel):
    return subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True).stdout
def live(rel):
    return open(f"{ROOT}/{rel}", "rb").read()
out = []
# PL master
h = json.loads(head("PL_breakdown.json").decode("utf-8")); l = json.loads(live("PL_breakdown.json").decode("utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
hm, lm = {key(r): r for r in h}, {key(r): r for r in l}
out.append(f"PL_breakdown.json rows HEAD {len(h)} live {len(l)}; keys equal: {set(hm) == set(lm)}")
ch = []
for k in sorted(lm, key=lambda x: (x[2], str(x[1]))):
    a, b = hm.get(k), lm[k]
    if a != b:
        ch.append(k)
        for f in sorted(set(a) | set(b)):
            if a.get(f) != b.get(f):
                out.append(f"  {k[0]} {k[2]} item {k[1]:>2} {b['항목명'][:14]:14s} {f}: {a.get(f)} -> {b.get(f)}")
out.append(f"changed rows: {len(ch)}; non-KR0073 changed rows: {sum(1 for k in ch if k[0] != 'KR0073')}")
# gold
hg = json.loads(head("data/_gold/user_pl_cells.json").decode("utf-8")); lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
hs = {(e['원보험사코드'], e['항목번호'], e['공시분기']): e for e in hg["set"]}
ls = {(e['원보험사코드'], e['항목번호'], e['공시분기']): e for e in lg["set"]}
out.append(f"gold set: HEAD {len(hs)} live {len(ls)}; removed {len(set(hs)-set(ls))}; modified existing {sum(1 for k in hs if k in ls and hs[k]!=ls[k])}; added {sorted(set(ls)-set(hs), key=lambda x:(x[2],x[1]))}")
out.append(f"gold null_dangi cells: HEAD {len(hg['null_dangi']['cells'])} live {len(lg['null_dangi']['cells'])}; set_dangi equal: {hg['set_dangi']==lg['set_dangi']}; other keys equal: {all(hg[k]==lg[k] for k in hg if k not in ('set','null_dangi'))}")
# provenance
hp = json.loads(head("PL_breakdown_provenance.json").decode("utf-8")); lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
out.append(f"provenance cells HEAD {len(hp['cells'])} live {len(lp['cells'])}; changed blocks {len(dif)}: {dif}; top-level keys added: {sorted(set(lp)-set(hp))}")
for k in dif:
    a, b = hpm[k], lpm[k]
    out.append(f"  {k}: " + ", ".join(f"{f}" for f in sorted(set(a)|set(b)) if a.get(f)!=b.get(f)))
open("diff_vs_head.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("\n".join(out))
