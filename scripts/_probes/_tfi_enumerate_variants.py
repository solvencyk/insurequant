# -*- coding: utf-8 -*-
"""Deliverable #1: enumerate TFI table title / row-label / column variants
across ALL md_inbox periods, for items 47-54 ('(1) 공통적용 경과조치 관련' table).

Read-only. Reuses fill_post_transition_to_disclosure's proven table scanner
(_scan_tables_with_context / _is_common_section / _pick_pre_post_columns)
rather than re-implementing heading/table detection.
"""
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fill_post_transition_to_disclosure import (  # noqa: E402
    _scan_tables_with_context,
    _is_common_section,
    _is_market_or_rate_section,
    _pick_pre_post_columns,
    _normalise,
    _md_period_to_quarter,
)

MD_INBOX = REPO / "md_inbox"

# Content signature: this exact keyword appears ONLY in the TFI detail
# rows (47/48), nowhere else in a K-ICS disclosure filing (established by
# direct inspection of KR0005 2026.2Q).
SIGNATURE_KEYWORD = "보완자본한도"

title_variants = Counter()
subheading_variants = Counter()
unit_variants = Counter()
row_label_variants = defaultdict(Counter)  # target_kw -> Counter(actual label seen)
no_keyword_files = []
keyword_but_no_common_section_table = []
common_section_but_no_keyword_row = []
multi_table_with_keyword = []
per_file_table_count = Counter()

TARGET_LABEL_PROBES = [
    "보완자본한도적용전", "보완자본한도", "해약환급금", "기발행신종자본증권",
    "기발행후순위채무", "지급여력금액", "기본자본", "보완자본",
]

files = sorted(MD_INBOX.glob("FY*/*.md"))
print(f"scanning {len(files)} files")
print()

for f in files:
    period = f.parent.name
    try:
        quarter = _md_period_to_quarter(period)
    except ValueError:
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    has_kw = SIGNATURE_KEYWORD in _normalise(text)
    if not has_kw:
        no_keyword_files.append((f.name, period))
        continue

    tables = _scan_tables_with_context(text)
    kw_tables = [
        t for t in tables
        if any(SIGNATURE_KEYWORD in _normalise(row[0]) for row in t["table"] if row)
    ]
    per_file_table_count[len(kw_tables)] += 1
    if len(kw_tables) > 1:
        multi_table_with_keyword.append((f.name, period, len(kw_tables)))
    if not kw_tables:
        # keyword present in raw text but not captured inside any parsed table
        # (e.g. prose sentence, not a markdown table) -- flag for manual look
        common_section_but_no_keyword_row.append((f.name, period, "KEYWORD_NOT_IN_ANY_TABLE_ROW"))
        continue

    for t in kw_tables:
        # title/heading variants: last 1-2 headings leading into this table
        heading_ctx = " | ".join(t["headings"][-2:]) if t["headings"] else "<NO HEADING>"
        subheading_variants[heading_ctx] += 1
        unit_variants[t["unit"]] += 1

        is_common = _is_common_section(t["headings"])
        if not is_common:
            keyword_but_no_common_section_table.append((f.name, period, heading_ctx))

        header = t["table"][0] if t["table"] else []
        pre_idx, post_idx = _pick_pre_post_columns(header)
        col_status = "OK" if (pre_idx is not None and post_idx is not None) else f"COLPICK_FAIL(pre={pre_idx},post={post_idx})"
        if col_status != "OK":
            row_label_variants["<COLUMN_PICK>"][f"{f.name}:{col_status}"] += 1

        for row in t["table"][1:]:
            if not row:
                continue
            label = row[0]
            nl = _normalise(label)
            for probe in TARGET_LABEL_PROBES:
                if probe in nl:
                    row_label_variants[probe][label.strip()] += 1
                    break  # first (most specific, since probes ordered) match only -- mirrors real matcher

# also grep the [...] bracket title line variants across all files (not just kw files)
BRACKET_TITLE_RE = re.compile(r"^\s*#+\s*\[([^\]]*경과조치[^\]]*)\]\s*$", re.MULTILINE)
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in BRACKET_TITLE_RE.finditer(text):
        title_variants[m.group(1).strip()] += 1

print("=== [브라켓 제목] 변형 (### [...] 형태, 경과조치 포함) ===")
for k, v in title_variants.most_common(30):
    print(f"  {v:4d}  {k}")
print()

print("=== 표 헤딩 컨텍스트 변형 (마지막 1-2개 heading, 시그니처 키워드 보완자본한도 포함 표) ===")
for k, v in subheading_variants.most_common(30):
    print(f"  {v:4d}  {k}")
print()

print("=== 단위 변형 ===")
for k, v in unit_variants.most_common(20):
    print(f"  {v:4d}  {k!r}")
print()

print(f"=== 파일당 시그니처-키워드-표 개수 분포 === {dict(per_file_table_count)}")
print()

print(f"=== 키워드 자체가 아예 없는 파일: {len(no_keyword_files)} ===")
for name, period in no_keyword_files:
    print(f"  {period}/{name}")
print()

print(f"=== 키워드는 있는데 표 행으로 안 잡힘: {len(common_section_but_no_keyword_row)} ===")
for name, period, why in common_section_but_no_keyword_row:
    print(f"  {period}/{name}  {why}")
print()

print(f"=== 키워드 표는 있는데 _is_common_section()이 못 잡음 (heading 탐지 갭): {len(keyword_but_no_common_section_table)} ===")
for name, period, ctx in keyword_but_no_common_section_table:
    print(f"  {period}/{name}  heading={ctx!r}")
print()

print(f"=== 한 파일에 시그니처 표가 2개 이상: {len(multi_table_with_keyword)} ===")
for name, period, n in multi_table_with_keyword:
    print(f"  {period}/{name}  n={n}")
print()

print("=== 항목 라벨 실측 변형 (probe keyword -> 실제 라벨 문자열들) ===")
for probe in TARGET_LABEL_PROBES + ["<COLUMN_PICK>"]:
    c = row_label_variants.get(probe)
    if not c:
        print(f"  [{probe}] : (매치 0건)")
        continue
    print(f"  [{probe}] : {sum(c.values())}건, {len(c)}종 라벨")
    for label, n in c.most_common(15):
        print(f"      {n:4d}  {label!r}")
