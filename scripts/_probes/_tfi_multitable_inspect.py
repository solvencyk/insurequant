# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_post_transition_to_disclosure import (
    _scan_tables_with_context, _is_common_section, _pick_pre_post_columns, _normalise,
)

targets = [
    "FY2023_Q4/KR0068_한화생명.md",
    "FY2023_Q4/KR0072_케이디비생명보험.md",
    "FY2025_Q4/KR0070_에이비엘생명보험.md",
    "FY2024_Q4/KR0069_삼성생명.md",
]
for rel in targets:
    f = REPO / "md_inbox" / rel
    text = f.read_text(encoding="utf-8", errors="replace")
    tables = _scan_tables_with_context(text)
    kw_tables = [t for t in tables if any("보완자본한도" in _normalise(row[0]) for row in t["table"] if row)]
    print(f"=== {rel}: {len(kw_tables)} signature tables ===")
    for i, t in enumerate(kw_tables):
        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        print(f"  --- table {i}: heading={t['headings'][-2:]!r} unit={t['unit']!r} pre_idx={pre_idx} post_idx={post_idx} is_common={_is_common_section(t['headings'])}")
        print(f"      header row: {header}")
        for row in t["table"][1:6]:
            print(f"      {row}")
    print()
