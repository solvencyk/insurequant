# -*- coding: utf-8 -*-
"""Dump the raw MD 'III. other required capital' block for group2's target buckets.
Read-only probe, no writes to any master."""
import sys, io, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

TARGETS = [
    ("KR0002", "한화손해보험", ["2023.4Q","2024.1Q","2024.2Q","2024.4Q","2025.1Q","2025.2Q","2025.4Q","2026.1Q","2026.2Q"]),
    ("KR0003", "롯데손해보험", ["2026.1Q","2026.2Q"]),
    ("KR0049", "악사손해보험", ["2023.1Q","2023.2Q","2023.3Q","2024.3Q","2024.4Q","2025.1Q"]),
    ("KR0050", "하나손해보험", ["2023.3Q"]),
    ("KR0080", "에이아이에이생명보험", ["2024.1Q"]),
    ("KR0097", "하나생명보험", ["2024.4Q"]),
    ("KR0099", "KB라이프생명", ["2023.3Q","2023.4Q","2024.1Q","2025.1Q","2025.3Q"]),
    ("KR0104", "농협생명보험", ["2026.2Q"]),
    ("KR0150", "서울보증보험", ["2026.1Q"]),
    ("KR1098", "카카오페이손해보험", ["2024.4Q"]),
]

def quarter_to_period(q):
    y, qq = q.split(".")
    qq = qq.replace("Q", "")
    return f"FY{y}_Q{qq}"

def find_md(code, quarter):
    period = quarter_to_period(quarter)
    d = ROOT / "data" / "disclosure" / period / "parsed"
    if not d.is_dir():
        return None
    matches = list(d.glob(f"{code}_*.md"))
    return matches[0] if matches else None

KEYWORDS = ["기타요구자본", "기타 요구자본", "비례성원칙", "종속회사", "관계회사"]

for code, name, quarters in TARGETS:
    print(f"\n{'='*100}")
    print(f"### {code} {name}")
    print('='*100)
    for q in quarters:
        md_path = find_md(code, q)
        print(f"\n--- {q} ---")
        if md_path is None:
            print(f"  [NO MD FILE FOUND for {code} {q}]")
            continue
        print(f"  file: {md_path.relative_to(ROOT)}")
        text = md_path.read_text(encoding="utf-8")
        lines = text.split("\n")
        # find lines containing "기타요구자본" or "기타 요구자본" (item23 header)
        hit_lines = [i for i, l in enumerate(lines) if re.search(r"기타\s*요구자본", l)]
        if not hit_lines:
            print(f"  [NO '기타요구자본' MATCH IN TEXT] -- checking char count for scan-suspicion")
            print(f"  total chars={len(text)}, total lines={len(lines)}")
            continue
        for hi in hit_lines:
            lo = max(0, hi - 1)
            hidx = min(len(lines), hi + 5)
            print(f"  [match at line {hi+1}]")
            for j in range(lo, hidx):
                print(f"    L{j+1}: {lines[j]}")
            print("    ...")
