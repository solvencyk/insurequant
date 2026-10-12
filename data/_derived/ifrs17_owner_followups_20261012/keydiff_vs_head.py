# -*- coding: utf-8 -*-
"""Read-only: key-level comparison of every master/sidecar I changed against git HEAD (removed / added / changed keys, changed fields).  Output -> keydiff_vs_head.txt"""
import json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = R / "data/_derived/ifrs17_owner_followups_20261012/keydiff_vs_head.txt"

def head(path):
    return json.loads(subprocess.run(["git", "-C", str(R), "show", f"HEAD:{path}"], capture_output=True).stdout.decode("utf-8"))

def now(path):
    return json.loads((R / path).read_bytes().decode("utf-8"))

def cmp(rows_a, rows_b, keyf, label, out):
    a, b = {}, {}
    dup = 0
    for r in rows_a:
        k = keyf(r)
        dup += k in a
        a[k] = r
    for r in rows_b:
        k = keyf(r)
        dup += k in b
        b[k] = r
    removed = sorted(set(a) - set(b), key=str)
    added = sorted(set(b) - set(a), key=str)
    changed = [k for k in a if k in b and a[k] != b[k]]
    out.append(f"== {label}: HEAD {len(a)} keys -> now {len(b)} keys | removed {len(removed)} | added {len(added)} | changed {len(changed)} | duplicate keys {dup}")
    for k in removed[:50]:
        out.append(f"   REMOVED {k}")
    for k in added[:60]:
        out.append(f"   added   {k}")
    for k in changed[:80]:
        fields = {f: (a[k].get(f), b[k].get(f)) for f in sorted(set(a[k]) | set(b[k])) if a[k].get(f) != b[k].get(f)}
        out.append(f"   changed {k} {json.dumps(fields, ensure_ascii=False)[:260]}")
    return len(removed), len(added), len(changed)

out = []
tot = {}
tot["CSM_amortization"] = cmp(head("CSM_amortization.json"), now("CSM_amortization.json"), lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"]), "CSM_amortization.json", out)
tot["IFRS17_BS"] = cmp(head("IFRS17_BS.json"), now("IFRS17_BS.json"), lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]), "IFRS17_BS.json", out)
tot["ILP"] = cmp(head("insurance_liability_portfolio.json"), now("insurance_liability_portfolio.json"), lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]), "insurance_liability_portfolio.json", out)
tot["PL"] = cmp(head("PL_breakdown.json"), now("PL_breakdown.json"), lambda r: (r["원보험사코드"], str(r["항목번호"]), r["공시분기"]), "PL_breakdown.json", out)
tot["CSM_wf"] = cmp(head("CSM_waterfall.json"), now("CSM_waterfall.json"), lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]), "CSM_waterfall.json (not changed)", out)
ha, na = head("CSM_waterfall_provenance.json"), now("CSM_waterfall_provenance.json")
tot["CSM_wf_prov"] = cmp(ha["cells"], na["cells"], lambda c: (c["company_code"], c["quarter"], c["item_block"]), "CSM_waterfall_provenance.json cells", out)
ha, na = head("insurance_liability_portfolio_provenance.json"), now("insurance_liability_portfolio_provenance.json")
tot["ILP_prov_cells"] = cmp(ha["cells"], na["cells"], lambda c: (c["company_code"], c["quarter"], c["item_block"]), "insurance_liability_portfolio_provenance.json cells", out)
out.append(f"   value_corrections {len(ha['value_corrections'])} -> {len(na['value_corrections'])} | backfills {len(ha['backfills'])} -> {len(na['backfills'])} | other top-level keys equal: "
           f"{all(ha[k] == na[k] for k in ha if k not in ('cells', 'value_corrections', 'backfills'))}")
ha, na = head("PL_breakdown_provenance.json"), now("PL_breakdown_provenance.json")
tot["PL_prov"] = cmp(ha["cells"], na["cells"], lambda c: (c["company_code"], c["quarter"], c["item_block"]), "PL_breakdown_provenance.json cells", out)
OUT.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out[:40]))
print("... written", OUT)
