"""Raw-XML dump (WITH colspan/rowspan attrs, not the lossy ExtractedTable.rows list) of the
2025.4Q ACT candidate table that contains the label-value shift anomaly, to determine whether
colspan/rowspan is causing our cell-based parser (which does NOT expand col/rowspan) to
misalign columns. Locates the target TABLE by searching for a unique anchor value
(6,239,505,634,766, the '자산인 보험계약의 기초 장부금액' value flagged as suspicious) inside
the 별도 (OFS) main xml. Read-only -- does not touch any master.
"""
import sys
from pathlib import Path
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
XML = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664/20260318001664.xml"

parser = etree.HTMLParser(encoding="utf-8", huge_tree=True, recover=True)
tree = etree.parse(str(XML), parser)
root = tree.getroot()


def text(el):
    import re
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


# find every TABLE element; for each, check if it contains our two anchor row-label cells
# ("자산인 보험계약의 기초 장부금액" AND "발생한 보험금 및 기타 보험서비스비용") as TE/TD/TH text.
target_tables = []
for tbl in root.iter():
    if not isinstance(tbl.tag, str) or tbl.tag.lower() != "table":
        continue
    all_text = text(tbl)
    if "자산인 보험계약의 기초 장부금액" in all_text and "발생한 보험금 및 기타 보험서비스비용" in all_text \
            and "6,239,505,634,766" in all_text.replace(" ", ""):
        target_tables.append(tbl)

print(f"tables matching anchor value 6,239,505,634,766 + both row labels: {len(target_tables)}")

for ti, tbl in enumerate(target_tables):
    print(f"\n{'='*110}\nTABLE #{ti}  sourceline={tbl.sourceline}")
    for tr in tbl.iter():
        if not isinstance(tr.tag, str) or tr.tag.lower() != "tr":
            continue
        cells_info = []
        for c in tr:
            ctag = (c.tag or "").lower()
            if ctag in ("th", "td", "te"):
                cs = c.get("COLSPAN") or c.get("colspan") or "1"
                rs = c.get("ROWSPAN") or c.get("rowspan") or "1"
                t = text(c)
                cells_info.append(f"[{t!r} cs={cs} rs={rs}]")
        if not cells_info:
            continue
        print(f"  TR(line={tr.sourceline}): " + " ".join(cells_info))
