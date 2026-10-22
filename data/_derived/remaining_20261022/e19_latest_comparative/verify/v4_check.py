import json, sys, collections
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vstmt
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
B = {"KR0082": ["2023.3Q"], "KR0032": ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"], "KR0104": ["2023.3Q"],
     "KR0087": ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"], "KR0070": ["2024.1Q", "2024.2Q", "2024.3Q"],
     "KR0083": ["2024.1Q", "2024.2Q"], "KR0005": ["2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]}
def later(q):
    y, r = q.split("."); return "%d.%s" % (int(y) + 1, r)

head = json.load(open(SP + "/head_PL.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
H = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in head}
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
gold = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_head = json.load(open(SP + "/head_gold.json", encoding="utf-8"))
ghk = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold_head["set"]}
gk = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"]}

out = []
def P(*a):
    out.append(" ".join(str(x) for x in a))

TOL = 0.0105   # million won (6 decimals printed in won -> exact; rounding in million-won prints exact too)
summary = collections.Counter()
detail = {}
for code, qs in B.items():
    for q in qs:
        L = later(q)
        st_new = vstmt.read_separate_stmt(code, L)
        st_old = vstmt.read_separate_stmt(code, q)
        new_vals, _, nc_new = vstmt.item_values(st_new, "prior")
        old_vals, _, nc_old = vstmt.item_values(st_old, "cur")
        P("== %s %s | later filing %s line %d unit %s ncol %d | orig %s line %d unit %s ncol %d" % (
            code, q, st_new["file"].split("/")[-1].split("\\")[-1], st_new["line"], st_new["unit"], nc_new,
            st_old["file"].split("/")[-1].split("\\")[-1], st_old["line"], st_old["unit"], nc_old))
        for it in sorted(new_vals, key=int):
            nv = new_vals[it]
            k = (code, it, q)
            if k not in C or nv is None:
                P("   item %2d reader=%s master=%s -> not comparable" % (it, nv, C.get(k, {}).get("값")))
                summary["notcomp"] += 1
                continue
            cv = C[k]["값"]; hv = H[k]["값"]
            changed = (cv != hv)
            ok_new = cv is not None and abs(cv - nv) <= TOL
            ov = old_vals.get(it)
            ok_old = (ov is not None and hv is not None and abs(hv - ov) <= TOL)
            tag = ("CHG" if changed else "same") + (" gold" if k in ghk else "") + (" NEWgold" if (k in gk and k not in ghk) else "")
            summary[("changed_ok" if ok_new else "changed_BAD") if changed else ("unchanged_eq_new" if ok_new else "unchanged_ne_new")] += 1
            summary[("reader_calib_ok" if ok_old else "reader_calib_ne")] += 1
            flag = "" if ok_new else "   <<<<< master!=later-filing"
            if changed and not ok_new:
                flag = "   <<<<< CHANGED BUT MISMATCH"
            P("   item %2d %-5s%s head=%s cur=%s later_prior=%s | orig_cur=%s calib=%s%s" % (
                it, tag, "", hv, cv, round(nv, 6), None if ov is None else round(ov, 6), "ok" if ok_old else "ne", flag))
        # changed items for which the reader produced nothing
        for k in C:
            if k[0] == code and k[2] == q and C[k]["값"] != H[k]["값"] and k[1] not in new_vals:
                P("   !! changed item %s has no reader value (cur=%s head=%s)" % (k[1], C[k]["값"], H[k]["값"]))
                summary["changed_unread"] += 1
P("SUMMARY", dict(summary))
open(V + "v4_check.txt", "w", encoding="utf-8").write("\n".join(out))
