# -*- coding: utf-8 -*-
"""Apply data/_derived/_patch_2026q2_KR0005.json to the SCRATCH copy of kics_disclosure.json
ONLY (never the live root file). Matches master's string-number convention (whole numbers as
plain ints, decimals trimmed of trailing zeros) so the diff against sibling cells is minimal."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch_KR0005.json"
)
PATCH = ROOT / "data" / "_derived" / "_patch_2026q2_KR0005.json"


def fmt(x: float) -> str:
    r = round(float(x), 2)
    if r == int(r):
        return str(int(r))
    s = f"{r:.2f}".rstrip("0").rstrip(".")
    return s


with open(PATCH, encoding="utf-8") as f:
    patch = json.load(f)

with open(SCRATCH, encoding="utf-8") as f:
    data = json.load(f)

code, quarter = patch["company_code"], patch["quarter"]
by_item = {r["항목번호"]: r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter}

applied = []
for cell in patch["cells"]:
    item = cell["항목번호"]
    row = by_item.get(item)
    if row is None:
        raise SystemExit(f"ABORT: {code} {quarter} item{item} not found in scratch master")
    if row["항목명"] != cell["항목명"]:
        raise SystemExit(
            f"ABORT: label mismatch item{item}: master={row['항목명']!r} patch={cell['항목명']!r}"
        )
    before = row.get("값_적용후")
    if cell["값"] is not None:
        row["값"] = fmt(cell["값"])
    if cell["값_적용후"] is not None:
        row["값_적용후"] = fmt(cell["값_적용후"])
    applied.append((item, before, row.get("값_적용후")))

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("Applied to SCRATCH copy only:")
for item, before, after in applied:
    print(f"  item{item} 값_적용후: {before!r} -> {after!r}")
