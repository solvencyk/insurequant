# -*- coding: utf-8 -*-
import json, io, sys, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LIVE = "kics_disclosure.json"
PATCH = "data/_derived/_patch_2026q2_KR0076.json"
SCRATCH = "scripts/_probes/_scratch_kics_disclosure_KR0076.json"

data = json.load(open(LIVE, encoding="utf-8"))
patch = json.load(open(PATCH, encoding="utf-8"))

code = patch["company_code"]
quarter = patch["quarter"]

# find a template row for this (code, quarter) to copy common fields from
template = None
for r in data:
    if r.get("원보험사코드") == code and r.get("공시분기") == quarter:
        template = r
        break
assert template is not None, "no existing rows for company/quarter"

by_item = {}
for i, r in enumerate(data):
    if r.get("원보험사코드") == code and r.get("공시분기") == quarter:
        try:
            by_item[int(r.get("항목번호"))] = i
        except (TypeError, ValueError):
            pass

n_updated, n_added = 0, 0
for cell in patch["cells"]:
    it = cell["항목번호"]
    if it in by_item:
        idx = by_item[it]
        data[idx]["값"] = cell["값"]
        data[idx]["값_적용후"] = cell["값_적용후"]
        n_updated += 1
    else:
        new_row = {
            "원보험사코드": template["원보험사코드"],
            "원수사명": template["원수사명"],
            "티커": template["티커"],
            "생손보여부": template["생손보여부"],
            "항목번호": it,
            "항목명": cell["항목명"],
            "공시분기": template["공시분기"],
            "값": cell["값"],
            "값_적용후": cell["값_적용후"],
        }
        data.append(new_row)
        n_added += 1

print(f"updated {n_updated} existing rows, added {n_added} new rows")

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"wrote scratch master to {SCRATCH}")
