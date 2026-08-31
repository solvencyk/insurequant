# -*- coding: utf-8 -*-
"""Apply data/_derived/_patch_2026q2_KR0079.json onto a SCRATCH COPY of kics_disclosure.json
(never touches the real root file) so the gate can be run against it for verification."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch_KR0079.json"
)

data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
patch = json.load(open(ROOT / "data" / "_derived" / "_patch_2026q2_KR0079.json", encoding="utf-8"))

code = patch["company_code"]
quarter = patch["quarter"]

# find one existing KR0079/2026.2Q row to copy 원수사명/티커/생손보여부 from
template = next(r for r in data if r["원보험사코드"] == code and r["공시분기"] == quarter)
tmpl_extra = {k: template[k] for k in ("원수사명", "티커", "생손보여부")}

existing_idx = {
    r["항목번호"]: i
    for i, r in enumerate(data)
    if r["원보험사코드"] == code and r["공시분기"] == quarter
}

n_updated, n_added = 0, 0
for cell in patch["cells"]:
    item = cell["항목번호"]
    row = {
        "원보험사코드": code,
        "원수사명": tmpl_extra["원수사명"],
        "티커": tmpl_extra["티커"],
        "생손보여부": tmpl_extra["생손보여부"],
        "항목번호": item,
        "항목명": cell["항목명"],
        "공시분기": quarter,
        "값": cell["값"],
    }
    if "값_적용후" in cell:
        row["값_적용후"] = cell["값_적용후"]
    if item in existing_idx:
        data[existing_idx[item]] = row
        n_updated += 1
    else:
        data.append(row)
        n_added += 1

print(f"updated={n_updated} added={n_added} total_cells_in_patch={len(patch['cells'])}")

SCRATCH.parent.mkdir(parents=True, exist_ok=True)
SCRATCH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote scratch master:", SCRATCH, "rows=", len(data))

# quick before/after cell-loss guard: total row count should only grow by n_added
before_rows = len(json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8")))
print("root kics_disclosure.json rows (unchanged, read-only) =", before_rows)
print("scratch rows =", len(data), "expected =", before_rows + n_added)
assert len(data) == before_rows + n_added, "ROW COUNT MISMATCH -- investigate before validating"
