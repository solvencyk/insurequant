# -*- coding: utf-8 -*-
"""Simulation-only: copies kics_disclosure.json to a scratch file, applies
_patch_2026q2_KR0095.json (UPSERT by 원보험사코드+공시분기+항목번호), and writes
the scratch copy so the gate can be re-run against it via --master. Does NOT
touch the real kics_disclosure.json.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
SRC = REPO / "kics_disclosure.json"
PATCH = REPO / "data" / "_derived" / "_patch_2026q2_KR0095.json"
SCRATCH_DIR = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad")
SCRATCH = SCRATCH_DIR / "kics_disclosure_KR0095_sim.json"

data = json.loads(SRC.read_text(encoding="utf-8"))
patch = json.loads(PATCH.read_text(encoding="utf-8"))
code = patch["company_code"]
quarter = patch["quarter"]

bucket = {r["항목번호"]: r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter}
template = bucket[1]

n_new, n_upd = 0, 0
for cell in patch["cells"]:
    item = cell["항목번호"]
    row = bucket.get(item)
    if row is None:
        new_row = {
            "원보험사코드": template["원보험사코드"],
            "원수사명": template["원수사명"],
            "티커": template.get("티커"),
            "생손보여부": template.get("생손보여부"),
            "항목번호": item,
            "항목명": cell["항목명"],
            "공시분기": quarter,
            "값": cell["값"],
        }
        if cell["값_적용후"] is not None:
            new_row["값_적용후"] = cell["값_적용후"]
        data.append(new_row)
        bucket[item] = new_row
        n_new += 1
    else:
        row["값"] = cell["값"]
        if cell["값_적용후"] is not None:
            row["값_적용후"] = cell["값_적용후"]
        n_upd += 1

SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"scratch written: {SCRATCH} (new={n_new} upd={n_upd}, total rows={len(data)})")
