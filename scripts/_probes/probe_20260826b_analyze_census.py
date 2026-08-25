import json, sys, io
sys.stdout.reconfigure(encoding="utf-8")

census = json.load(open("scripts/_probes/out_20260826_pl_basis_census.json", encoding="utf-8"))

out = io.open("scripts/_probes/out_20260826b_basis_tag_summary.txt", "w", encoding="utf-8")
by_company = {}
for r in census:
    code = r["code"]
    by_company.setdefault(code, {"name": r["name"], "rows": []})
    by_company[code]["rows"].append(r)

for code in sorted(by_company):
    info = by_company[code]
    rows = info["rows"]
    n = len(rows)
    n_has_ofs_tag = sum(1 for r in rows if r["basis_tag_counts"].get("OFS", 0) > 0)
    n_has_cfs_tag = sum(1 for r in rows if r["basis_tag_counts"].get("CFS", 0) > 0)
    n_dedicated = sum(1 for r in rows if r["has_dedicated_handler"])
    n_structfail = sum(1 for r in rows if r.get("ofs_structural_fail"))
    n_flag = sum(1 for r in rows if r["diffs"])
    out.write(f"{code}\t{info['name']}\tfilings={n}\tdedicated={n_dedicated}\t"
              f"has_OFS_tag={n_has_ofs_tag}\thas_CFS_tag={n_has_cfs_tag}\t"
              f"struct_fail={n_structfail}\tflagged={n_flag}\n")
    for r in rows:
        btc = r["basis_tag_counts"]
        none_n = btc.get("null", btc.get("None", btc.get(None, 0)))
        out.write(f"    {r['quarter']}\tOFS={btc.get('OFS',0)}\tCFS={btc.get('CFS',0)}\t"
                   f"None={none_n}\thandler={r['handler_name']}\t"
                   f"structfail={r.get('ofs_structural_fail')}\tflags={sorted(r['diffs'].keys())}\n")
out.close()
print("done")
