# -*- coding: utf-8 -*-
"""Line-by-line trace of extract_mkt_subs for KR0005, focused on item37."""
from __future__ import annotations
import io, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F

text = (REPO / "md_inbox" / "FY2026_Q2" / "KR0005_흥국화재.md").read_text(encoding="utf-8")

out = {}
unit = "백만원"
heading_ctx = ""
prev_was_table = False
table_risk_item = None

for lineno, ln in enumerate(text.splitlines(), start=1):
    s = ln.strip()
    if not s.startswith("|"):
        m = F._UNIT_HINT_RE.search(s)
        if m:
            unit = m.group(1)
        if s.startswith("#") or re.match(r"^\d+\)", s):
            heading_ctx = s
        prev_was_table = False
        continue
    cells = [c.strip() for c in s.strip("|").split("|")]
    if len(cells) < 2:
        prev_was_table = False
        continue
    if not prev_was_table:
        table_risk_item = F._table_risk_item_from_header(cells, heading_ctx)
    prev_was_table = True
    item_no = F._bare_subrisk_item(cells[0])
    if item_no is not None and item_no not in out:
        for c in cells[1:]:
            v = F._parse_value(c)
            if v is not None:
                out[item_no] = (v, unit)
                if item_no == 37:
                    print(f"L{lineno}: PRIMARY branch set item37={v} from cells={cells}")
                break
        else:
            value_cells = cells[1:]
            if value_cells and all(c.strip().replace(",", "") in ("-", "\u2500", "\u2013", "\u2014") for c in value_cells):
                out[item_no] = ("0", unit)
        continue
    if table_risk_item is not None and table_risk_item not in out:
        if any(F._is_total_row_label(c) for c in cells):
            for c in reversed(cells):
                v = F._parse_value(c)
                if v is not None:
                    if table_risk_item == 37:
                        print(f"L{lineno}: FALLBACK branch set item37={v} from cells={cells} (matched _is_total_row_label)")
                    out[table_risk_item] = (v, unit)
                    table_risk_item = None
                    break
    if 935 <= lineno <= 966:
        print(f"L{lineno}: cells={cells} table_risk_item={table_risk_item} out.get(37)={out.get(37)}")

print()
print("FINAL out[37] =", out.get(37))
