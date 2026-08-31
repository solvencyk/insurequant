# -*- coding: utf-8 -*-
"""Apply data/_derived/_patch_2026q2_KR0008.json onto a SCRATCH COPY of
kics_disclosure.json (never touches the real root file). UPSERT by
(원보험사코드, 항목번호, 공시분기): update 값/값_적용후 on existing rows,
append new rows, carrying 원수사명/티커/생손보여부 from the row template.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"
PATCH = ROOT / "data" / "_derived" / "_patch_2026q2_KR0008.json"
SCRATCH = ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_KR0008.json"

data = json.loads(MASTER.read_text(encoding="utf-8"))
patch = json.loads(PATCH.read_text(encoding="utf-8"))

code = patch["company_code"]
quarter = patch["quarter"]

template = next(r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == quarter)
meta = {k: template[k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")}


def _fmt(x):
    if x is None:
        return None
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in data}

n_updated = 0
n_added = 0
for cell in patch["cells"]:
    key = (code, cell["항목번호"], quarter)
    val_str = _fmt(cell["값"])
    val_post_str = _fmt(cell["값_적용후"])
    if key in by_key:
        row = by_key[key]
        row["값"] = val_str
        if val_post_str is not None:
            row["값_적용후"] = val_post_str
        elif "값_적용후" in row:
            del row["값_적용후"]
        n_updated += 1
    else:
        new_row = {
            **meta,
            "항목번호": cell["항목번호"],
            "항목명": cell["항목명"],
            "공시분기": quarter,
            "값": val_str,
        }
        if val_post_str is not None:
            new_row["값_적용후"] = val_post_str
        data.append(new_row)
        n_added += 1

print(f"updated={n_updated} added={n_added} total_rows={len(data)} (was {len(by_key)})")

SCRATCH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote scratch master: {SCRATCH}")
