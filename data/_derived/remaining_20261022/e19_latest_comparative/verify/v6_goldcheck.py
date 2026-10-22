import json
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
gh = json.load(open(SP + "/head_gold.json", encoding="utf-8"))
gc = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
ghk = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gh["set"]}
gck = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gc["set"]}
out = []
chg_val = [k for k in H if C[k]["값"] != H[k]["값"]]
chg_d = [k for k in H if C[k].get("값_당분기") != H[k].get("값_당분기")]
out.append("값 changed %d ; all in NEW gold entries: %s ; any in existing gold: %s" % (
    len(chg_val), all(k in gck and k not in ghk for k in chg_val), [k for k in chg_val if k in ghk]))
out.append("new gold entries %d ; each 'was' equals HEAD master 값: %s" % (
    len(gck) - len(ghk), all(abs((gck[k]["was"] if gck[k]["was"] is not None else 0) - (H[k]["값"] or 0)) < 1e-9 for k in gck if k not in ghk)))
out.append("new gold entries each 값 equals current master 값: %s" % all(abs(gck[k]["값"] - C[k]["값"]) < 1e-9 for k in gck if k not in ghk))
out.append("existing gold 값 equals master (HEAD vs cur identical): %s" % all(H[k]["값"] == C[k]["값"] for k in ghk))
dg = [k for k in chg_d if k in ghk]
out.append("값_당분기 changed %d; of which keys in EXISTING owner gold: %d" % (len(chg_d), len(dg)))
for k in dg:
    out.append("   existing-gold key with changed dangi: %s head=%s cur=%s gold_note=%s" % (k, H[k].get("값_당분기"), C[k].get("값_당분기"), str(ghk[k].get("note"))[:80]))
# which existing-gold companies/quarters overlap w/ changed 값 in the same company-quarter
out.append("existing gold keys in the 19 buckets (same company+quarter as a changed 값):")
bk = {(k[0], k[2]) for k in chg_val}
for k, e in ghk.items():
    if (k[0], k[2]) in bk:
        out.append("   %s item %s val=%s master_cur=%s head=%s" % (k, k[1], e["값"], C[k]["값"], H[k]["값"]))
# gold dangi lists existing entries unchanged
out.append("existing null_dangi preserved: %s ; existing set_dangi preserved: %s" % (
    all(x in gc["null_dangi"]["cells"] for x in gh["null_dangi"]["cells"]), all(x in gc["set_dangi"]["cells"] for x in gh["set_dangi"]["cells"])))
# mask list? other fields in gold doc
for sec in gc:
    if sec not in ("_doc","set","null_dangi","set_dangi"): out.append("other section "+sec)
out.append("sections: %s" % list(gc.keys()))
# new set_dangi in gold: 3 keys in both null and set?
nk = {tuple(x[:3]) for x in gc["null_dangi"]["cells"]}
sk = {(x[0], x[1], x[2]) for x in gc["set_dangi"]["cells"]}
out.append("keys in both null and set dangi: %s" % (nk & sk))
open(V + "v6_goldcheck.txt", "w", encoding="utf-8").write("\n".join(out))
