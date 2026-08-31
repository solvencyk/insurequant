# -*- coding: utf-8 -*-
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_post_transition_to_disclosure import (
    _scan_tables_with_context, _pick_pre_post_columns, _normalise, _md_period_to_quarter,
)
MD_INBOX = REPO / "md_inbox"
files = sorted(MD_INBOX.glob("FY*/*.md"))
for f in files:
    period = f.parent.name
    try:
        _md_period_to_quarter(period)
    except ValueError:
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    if "보완자본한도" not in _normalise(text):
        continue
    tables = _scan_tables_with_context(text)
    kw_tables = [t for t in tables if any("보완자본한도" in _normalise(row[0]) for row in t["table"] if row)]
    selected = None
    for t in kw_tables:
        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is not None and post_idx is not None:
            selected = t
            break
    if selected is None:
        continue
    n = len(selected["table"]) - 1
    if n not in (10,):
        print(f"{f.relative_to(MD_INBOX).as_posix()}  rows={n}")
        for row in selected["table"]:
            print("   ", row)
        print()
