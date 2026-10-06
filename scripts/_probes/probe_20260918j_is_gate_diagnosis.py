# -*- coding: utf-8 -*-
"""For every orphan bucket, find the real 포괄손익계산서 table(s) in the raw XML and report
which of _is_income_statement()'s four conditions fail, plus whether the insurance-service
gross lines (일반/출재 보험서비스수익·비용, 보험수익/보험비용, 재보험수익/재보험비용) are present.

This turns 'the extractor returned None' into 'the source has X, the gate rejects it because Y'.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_pl_breakdown as B  # noqa: E402
from scripts.pl_breakdown.tier1 import (  # noqa: E402
    _is_income_statement, _header_blob, INCOME_PROFIT_LABELS, NI_LABELS)
from scripts.pl_breakdown.common import _label  # noqa: E402

BUCKETS = [
    ("KR0068", "2023.1Q"), ("KR0068", "2023.2Q"),
    ("KR0069", "2023.1Q"), ("KR0069", "2023.2Q"),
    ("KR0071", "2023.1Q"), ("KR0071", "2023.2Q"),
    ("KR0073", "2023.1Q"), ("KR0073", "2023.2Q"),
    ("KR0083", "2023.1Q"), ("KR0083", "2023.2Q"),
    ("KR0094", "2023.1Q"), ("KR0094", "2023.2Q"),
    ("KR0104", "2023.1Q"), ("KR0104", "2023.2Q"),
    ("KR0074", "2023.4Q"), ("KR0075", "2023.4Q"),
    ("KR0095", "2023.4Q"), ("KR0097", "2023.4Q"),
    ("KR0004", "2023.4Q"), ("KR0004", "2024.4Q"), ("KR0004", "2025.4Q"),
    ("KR0029", "2023.4Q"), ("KR0029", "2024.4Q"), ("KR0029", "2025.4Q"),
    ("KR0002", "2023.1Q"), ("KR0002", "2023.2Q"),
    ("KR0003", "2023.2Q"), ("KR0003", "2023.3Q"),
    ("KR0005", "2023.2Q"),
]

CAP_RE = re.compile(r"포괄손익계산서|손익계산서")
LINE_PATTERNS = {
    "일반보험서비스수익": r"일반보험서비스수익",
    "일반보험서비스비용": r"일반보험서비스비용",
    "출재보험서비스수익": r"출재보험서비스수익",
    "출재보험서비스비용": r"출재보험서비스비용",
    "보험수익": r"(?<!재)보험수익",
    "보험비용": r"(?<!재)보험비용",
    "보험서비스수익": r"(?<!일반)(?<!출재)보험서비스수익",
    "보험서비스비용": r"(?<!일반)(?<!출재)보험서비스비용",
    "재보험수익": r"재보험수익",
    "재보험비용": r"재보험비용",
    "재보험서비스비용": r"재보험서비스비용",
    "보험손익": r"보험손익",
    "보험서비스결과": r"보험서비스결과",
}

out = {}
for code, quarter in BUCKETS:
    dirs = B.discover_filings().get(code, {}).get(quarter) if False else None
    print(f"\n######## {code} {quarter} ########")
    filings = getattr(sys.modules[__name__], "_F", None)
    if filings is None:
        filings = B.discover_filings()
        sys.modules[__name__]._F = filings
    dirs = filings.get(code, {}).get(quarter)
    if not dirs:
        print("   no dirs")
        continue
    tables = []
    for d in dirs:
        for x in B._xmls_in(d):
            try:
                tables.extend(B._tag_basis(
                    list(B._iter_tables_by_basis(Path(x), B._iter_tables_with_context)), x))
            except Exception:
                pass
    hits = []
    for i, t in enumerate(tables):
        cap = getattr(t, "caption", "") or ""
        rows = list(getattr(t, "rows", []) or [])
        labs = " ".join(_label(r) for r in rows)
        if not CAP_RE.search(cap):
            continue
        if "영업이익" not in labs and "영업손익" not in labs:
            continue
        hb = _header_blob(t)
        c_restate = any(k in hb for k in ("소급", "재작성", "수정전", "수정후"))
        has_top = any(k in labs for k in INCOME_PROFIT_LABELS)
        has_op = "영업이익" in labs or "영업손익" in labs
        has_tax = "법인세" in labs
        has_ni = any(k in labs for k in NI_LABELS)
        present = [k for k, p in LINE_PATTERNS.items() if re.search(p, labs)]
        hits.append({
            "idx": i, "basis": getattr(t, "_basis", None), "caption": cap[:90],
            "IS": _is_income_statement(t),
            "fail": {"restate_header": c_restate, "no_보험손익/보험서비스결과": not has_top,
                     "no_영업이익": not has_op, "no_법인세": not has_tax, "no_순이익": not has_ni},
            "lines": present,
        })
    for h in hits:
        bad = [k for k, v in h["fail"].items() if v]
        print(f"  [{h['idx']}] basis={h['basis']} IS={h['IS']}  {h['caption']}")
        print(f"        FAIL={bad or 'none'}")
        print(f"        lines={h['lines']}")
    if not hits:
        print("   (no 포괄손익계산서-captioned table with an 영업이익 row)")
    out[f"{code}|{quarter}"] = hits

dest = ROOT / "data" / "_derived" / "_probe_20260918_is_gate_diagnosis.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwritten:", dest)
