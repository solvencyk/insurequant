# -*- coding: utf-8 -*-
"""Apply data/_derived/_patch_2026q2_KR0004.json to the SCRATCH copy of
kics_disclosure.json ONLY (never the live root file). Unlike the KR0005 probe
this session found (_apply_patch_scratch.py), this supports INSERTING brand-new
rows (most of KR0004's gap items had ZERO existing row), not just updating
existing ones. For existing rows it verifies the label matches before touching
anything (byte-copy discipline) and only overwrites fields the patch cell
actually specifies (leaving 값 alone when the patch cell's 값 is null, e.g.
item17/19 적용후-only fills).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\snap_after_KR0004.json"
)
PATCH = ROOT / "data" / "_derived" / "_patch_2026q2_KR0004.json"

with open(PATCH, encoding="utf-8") as f:
    patch = json.load(f)

with open(SCRATCH, encoding="utf-8") as f:
    data = json.load(f)

code, quarter = patch["company_code"], patch["quarter"]

# template row (for field order / 원보험사코드 etc.) from an existing row of the
# SAME company+quarter if one exists, else from the same company's most recent
# other quarter.
existing_same_q = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter]
if existing_same_q:
    template = existing_same_q[0]
else:
    template = next(r for r in data if r.get("원보험사코드") == code)

by_item = {r["항목번호"]: r for r in existing_same_q}

inserted, updated = [], []
for cell in patch["cells"]:
    item = cell["항목번호"]
    row = by_item.get(item)
    if row is None:
        new_row = {
            "원보험사코드": template["원보험사코드"],
            "원수사명": template["원수사명"],
            "티커": template["티커"],
            "생손보여부": template["생손보여부"],
            "항목번호": item,
            "항목명": cell["항목명"],
            "공시분기": quarter,
            "값": None,
            "값_적용후": None,
        }
        data.append(new_row)
        row = new_row
        by_item[item] = row
        action = "INSERT"
    else:
        if row["항목명"] != cell["항목명"]:
            raise SystemExit(
                f"ABORT: label mismatch item{item}: master={row['항목명']!r} patch={cell['항목명']!r}"
            )
        action = "UPDATE"

    before_v, before_p = row.get("값"), row.get("값_적용후")
    if cell.get("값") is not None:
        row["값"] = str(cell["값"])
    if cell.get("값_적용후") is not None:
        row["값_적용후"] = str(cell["값_적용후"])
    inserted.append((action, item, row["항목명"], before_v, row.get("값"), before_p, row.get("값_적용후")))

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Applied {len(patch['cells'])} cells to SCRATCH copy only ({SCRATCH.name}):")
n_ins = sum(1 for a, *_ in inserted if a == "INSERT")
n_upd = sum(1 for a, *_ in inserted if a == "UPDATE")
print(f"  INSERT (new rows): {n_ins}   UPDATE (existing rows): {n_upd}")
for action, item, label, bv, av, bp, ap in inserted:
    print(f"  [{action}] item{item:>2} {label!r}: 값 {bv!r}->{av!r}  값_적용후 {bp!r}->{ap!r}")

# sanity: row count for this company/quarter now
final_rows = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter]
print(f"\n{code} {quarter} row count now: {len(final_rows)} (items: "
      f"{sorted(r['항목번호'] for r in final_rows)})")
