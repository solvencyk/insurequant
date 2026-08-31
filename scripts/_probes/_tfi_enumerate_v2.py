# -*- coding: utf-8 -*-
"""Refined enumeration: ONLY tables that (a) contain a 보완자본한도-signature
row AND (b) have valid pre/post columns -- i.e. exactly what the real
extractor will select. Confirms row-label variants + flags any residual
ambiguity before finalizing TFI_ROW_MAP."""
import io, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_post_transition_to_disclosure import (
    _scan_tables_with_context, _pick_pre_post_columns, _normalise, _md_period_to_quarter,
)

MD_INBOX = REPO / "md_inbox"
files = sorted(MD_INBOX.glob("FY*/*.md"))

TARGET_LABEL_PROBES = [
    "보완자본한도적용전", "보완자본한도", "해약환급금", "기발행신종자본증권",
    "기발행후순위채무", "지급여력금액", "기본자본", "보완자본",
]

row_label_variants = defaultdict(Counter)
selected_table_row_counts = Counter()
files_with_selected_table = 0
files_kw_but_no_selected_table = []
n_files_with_kw = 0

for f in files:
    period = f.parent.name
    try:
        _md_period_to_quarter(period)
    except ValueError:
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    if "보완자본한도" not in _normalise(text):
        continue
    n_files_with_kw += 1
    tables = _scan_tables_with_context(text)
    kw_tables = [t for t in tables if any("보완자본한도" in _normalise(row[0]) for row in t["table"] if row)]
    selected = None
    for t in kw_tables:
        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        if pre_idx is not None and post_idx is not None:
            selected = (t, pre_idx, post_idx)
            break
    if selected is None:
        files_kw_but_no_selected_table.append(f.relative_to(MD_INBOX).as_posix())
        continue
    files_with_selected_table += 1
    t, pre_idx, post_idx = selected
    selected_table_row_counts[len(t["table"]) - 1] += 1
    for row in t["table"][1:]:
        if not row:
            continue
        label = row[0]
        nl = _normalise(label)
        matched_any = False
        for probe in TARGET_LABEL_PROBES:
            if probe in nl:
                row_label_variants[probe][label.strip()] += 1
                matched_any = True
                break
        if not matched_any:
            row_label_variants["<UNMATCHED>"][label.strip()] += 1

print(f"files containing 보완자본한도 keyword: {n_files_with_kw}")
print(f"files where a valid (colpick-ok) TFI table was selected: {files_with_selected_table}")
print(f"files with keyword but NO valid table selected: {len(files_kw_but_no_selected_table)}")
for x in files_kw_but_no_selected_table:
    print("   ", x)
print()
print("row-count distribution of selected tables (rows excl. header):", dict(sorted(selected_table_row_counts.items())))
print()
for probe in TARGET_LABEL_PROBES + ["<UNMATCHED>"]:
    c = row_label_variants.get(probe)
    if not c:
        print(f"[{probe}]: 0 matches")
        continue
    print(f"[{probe}]: {sum(c.values())} occurrences, {len(c)} distinct label strings")
    for label, n in c.most_common(12):
        print(f"    {n:4d}  {label!r}")
