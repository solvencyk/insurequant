# -*- coding: utf-8 -*-
"""Pull the full '(1) 공통적용 경과조치' table text (raw MD) for a list of
(code, period_label) targets -- for line-by-line manual re-verification."""
import io, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

targets = [
    ("KR0051_신한이지손해보험", "FY2026_Q2"),
    ("KR0068_한화생명", "FY2026_Q2"),
    ("KR0071_흥국생명보험", "FY2026_Q2"),
    ("KR0073_교보생명보험", "FY2026_Q2"),
    ("KR0080_에이아이에이생명보험", "FY2026_Q2"),
    ("KR0099_KB라이프생명", "FY2026_Q2"),
    ("KR0104_농협생명보험", "FY2026_Q2"),
    ("KR1098_카카오페이손해보험", "FY2026_Q2"),
    ("KR0003_롯데손해보험", "FY2026_Q1"),
]
import glob
for stem_prefix, period in targets:
    code = stem_prefix.split("_")[0]
    pattern = str(REPO / "md_inbox" / period / f"{code}_*.md")
    files = sorted(glob.glob(pattern))
    print(f"===== {code} {period}: files={ [Path(f).name for f in files] } =====")
    for fp in files:
        text = Path(fp).read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        # find the line containing 공통적용 경과조치 관련 (heading)
        idx = None
        for i, l in enumerate(lines):
            if "공통적용" in l and "경과조치" in l and ("관련" in l or l.strip().startswith("#")):
                idx = i
                break
        if idx is None:
            print("  (no 공통적용 경과조치 heading found)")
            continue
        for l in lines[idx:idx+20]:
            print("  ", l)
    print()
