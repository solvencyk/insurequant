# -*- coding: utf-8 -*-
"""Build a SCRATCH copy of kics_disclosure.json with the KR0002 2026.2Q patch cells
upserted, for gate simulation via `validate_kics_disclosure.py --master <scratch>`.
Never writes the real root kics_disclosure.json."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SCRATCH_DIR = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad"
)

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
patch = json.loads((ROOT / "data" / "_derived" / "_patch_2026q2_KR0002.json").read_text(encoding="utf-8"))

code = patch["company_code"]
quarter = patch["quarter"]

by_key = {}
for i, r in enumerate(records):
    if r.get("원보험사코드") == code and r.get("공시분기") == quarter:
        by_key[r.get("항목번호")] = i

n_updated = 0
n_appended = 0
for c in patch["cells"]:
    item_no = c["항목번호"]
    row = {
        "원보험사코드": c["원보험사코드"],
        "원수사명": c["원수사명"],
        "티커": c["티커"],
        "생손보여부": c["생손보여부"],
        "항목번호": c["항목번호"],
        "항목명": c["항목명"],
        "공시분기": c["공시분기"],
        "값": c["값"],
    }
    if "값_적용후" in c:
        row["값_적용후"] = c["값_적용후"]
    if item_no in by_key:
        idx = by_key[item_no]
        records[idx].update(row)
        n_updated += 1
    else:
        records.append(row)
        n_appended += 1

print(f"updated {n_updated}, appended {n_appended} rows")

out_path = SCRATCH_DIR / "kics_disclosure_SCRATCH_kr0002_patched.json"
out_path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out_path} ({len(records)} total rows)")
