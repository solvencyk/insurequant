# -*- coding: utf-8 -*-
"""서울보증/하나손해 단일컬럼 미러링 결과 + KR1010 교보라이프 대량미검출 원인 확인."""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fix_20260821_tier2_limit_lines import _pdf, extract_tier2, q2p  # noqa: E402

for c, q in [("KR0150", "2023.4Q"), ("KR0050", "2023.2Q"), ("KR1010", "2023.1Q"), ("KR1010", "2024.1Q")]:
    pdf = _pdf(q2p(q), c)
    found, reason = extract_tier2(pdf)
    print(f"{c} {q}: found={found}  reason={reason}")

print()
raw = REPO / "data" / "disclosure" / "FY2024_Q1" / "raw"
pdf = max(sorted(raw.glob("KR1010_*.pdf")), key=lambda p: p.stat().st_size)
import fitz
doc = fitz.open(pdf)
hits = [i for i in range(doc.page_count) if "보완자본" in doc[i].get_text()]
print(f"KR1010 2024.1Q '보완자본' 언급 페이지: {hits}")
for i in hits[:2]:
    print(f"--- p{i} ---")
    print(doc[i].get_text()[:1500])
doc.close()
