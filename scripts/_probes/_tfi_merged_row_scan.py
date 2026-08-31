# -*- coding: utf-8 -*-
"""How often does docling merge 2+ TFI row-labels into a single table row?"""
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_post_transition_to_disclosure import (
    _scan_tables_with_context, _pick_pre_post_columns, _normalise, _md_period_to_quarter,
)

PROBES = [
    "보완자본한도적용전", "보완자본한도", "해약환급금",
    "기발행신종자본증권", "기발행후순위채무", "지급여력금액", "기본자본", "보완자본",
]

MD_INBOX = REPO / "md_inbox"
files = sorted(MD_INBOX.glob("FY*/*.md"))
merged_count = 0
merged_examples = []
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
    for t in kw_tables:
        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is None or post_idx is None:
            continue  # not the real table (audit-statement dup)
        for row in t["table"][1:]:
            if not row:
                continue
            nl = _normalise(row[0])
            hits = [p for p in PROBES if p in nl]
            # bare 기본자본/보완자본/지급여력금액 are substrings of the longer
            # probes, so any real single-label row will match >=1; only flag
            # when the row structurally contains >=2 *distinct* row concepts,
            # detected as >=2 whitespace-separated numeric tokens in the
            # value cell (the real merge signature) OR multiple ) or ( in
            # label indicating 2 memo rows glued together.
            if pre_idx < len(row):
                val_tokens = row[pre_idx].split()
            else:
                val_tokens = []
            numeric_tokens = [v for v in val_tokens if v.replace(",", "").replace("-", "").replace(".", "").isdigit()]
            if len(numeric_tokens) >= 2:
                merged_count += 1
                merged_examples.append((f.relative_to(MD_INBOX).as_posix(), row[0][:80], row[pre_idx] if pre_idx < len(row) else "", row[post_idx] if post_idx < len(row) else ""))

print(f"merged-row occurrences: {merged_count}")
for ex in merged_examples:
    print(" ", ex)
