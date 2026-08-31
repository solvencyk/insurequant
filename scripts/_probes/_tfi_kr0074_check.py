# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_post_transition_to_disclosure import (
    _scan_tables_with_context, _is_common_section, _is_market_or_rate_section, _pick_pre_post_columns, _normalise,
)
for rel in ["FY2024_Q1/KR0074_라이나생명보험_amended.md", "FY2026_Q1/KR0049_악사손해보험.md", "FY2026_Q1/KR0003_롯데손해보험.md"]:
    f = REPO / "md_inbox" / rel
    text = f.read_text(encoding="utf-8", errors="replace")
    tables = _scan_tables_with_context(text)
    kw_tables = [t for t in tables if any("보완자본한도" in _normalise(row[0]) for row in t["table"] if row)]
    print(f"=== {rel}: {len(kw_tables)} sig tables ===")
    for i, t in enumerate(kw_tables):
        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        print(f"  table{i}: heading={t['headings']!r}")
        print(f"    is_common={_is_common_section(t['headings'])} is_market_rate={_is_market_or_rate_section(t['headings'])} pre={pre_idx} post={post_idx} unit={t['unit']}")
        for row in t["table"]:
            print("    ", row)
    print()
