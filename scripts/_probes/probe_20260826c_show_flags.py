import json, sys, io
sys.stdout.reconfigure(encoding="utf-8")
census = json.load(open("scripts/_probes/out_20260826_pl_basis_census.json", encoding="utf-8"))
out = io.open("scripts/_probes/out_20260826c_flag_detail.txt", "w", encoding="utf-8")
for r in census:
    if r["diffs"]:
        out.write(f"{r['code']} {r['name']} {r['quarter']} handler={r['handler_name']}\n")
        out.write(f"  diffs: {r['diffs']}\n")
        out.write(f"  t2_current: {r['t2_current']}\n")
        out.write(f"  t2_ofs_preferred: {r['t2_ofs_preferred']}\n")
        out.write(f"  basis_tag_counts: {r['basis_tag_counts']}\n\n")
out.close()
print("done")
