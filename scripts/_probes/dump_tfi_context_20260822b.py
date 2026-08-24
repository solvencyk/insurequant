# -*- coding: utf-8 -*-
"""Context dump for the 6-company TFI(공통적용경과조치) singles backlog investigation.
Read-only. Dumps existing master items 1/14/47-51 + PDF path + current
extract_tfi_full() reason for each (code, quarter) target to a JSON file
(NOT stdout -- the fix_2026082{1,2}_*.py modules each reassign sys.stdout at
import time, and importing two of them together in one process leaves the
final sys.stdout wrapping an already-closed buffer; writing to a file instead
sidesteps that entirely).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import fitz  # noqa: E402
import fix_20260822_tfi_tier_full_scan as F  # noqa: E402
T2 = F.T2

OUT = REPO / "scripts" / "_probes" / "_tfi_context_20260822b_out.json"

TARGETS = [
    ("KR0005", "2024.4Q"),
    ("KR0009", "2023.1Q"),
    ("KR0049", "2024.3Q"),
    ("KR0050", "2023.1Q"),
    ("KR0069", "2025.4Q"),
    ("KR0073", "2023.1Q"),
]

data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
by_key: dict[tuple, dict] = {}
for r in data:
    by_key[(r["원보험사코드"], r["공시분기"], int(r["항목번호"]))] = r

results = []
for code, q in TARGETS:
    name_row = next((r for r in data if r["원보험사코드"] == code), None)
    name = name_row.get("원수사명") if name_row else "?"
    entry = {"code": code, "name": name, "quarter": q}
    pdf = T2._pdf(T2.q2p(q), code)
    entry["pdf"] = str(pdf) if pdf else None
    if pdf is None:
        entry["error"] = "raw PDF 없음"
        results.append(entry)
        continue
    entry["pdf_size"] = pdf.stat().st_size
    doc = fitz.open(pdf)
    n = doc.page_count
    dens = [len(doc[i].get_text()) for i in range(n)]
    doc.close()
    total = sum(dens)
    entry["page_count"] = n
    entry["total_chars"] = total
    entry["avg_chars_per_page"] = round(total / n, 1) if n else 0
    lowd = [i for i, d in enumerate(dens) if d < 200]
    entry["low_density_pages"] = lowd
    entry["low_density_page_dens"] = [dens[i] for i in lowd[:15]]
    entry["existing_items"] = {}
    for item in (1, 14, 47, 48, 49, 50, 51):
        r = by_key.get((code, q, item))
        entry["existing_items"][str(item)] = (
            {"값": r.get("값"), "값_적용후": r.get("값_적용후")} if r else None
        )
    found, anchor, reason = F.extract_tfi_full(pdf)
    entry["extract_tfi_full"] = {
        "found": {str(k): list(v) for k, v in found.items()},
        "anchor": list(anchor) if anchor else None,
        "reason": reason,
    }
    results.append(entry)

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
