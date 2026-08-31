import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

COMPANIES = [
    "KR0001_메리츠화재해상보험",
    "KR0003_롯데손해보험",
    "KR0004_MG_예별손해보험",
    "KR0011_DB손해보험",
    "KR0029_AIG손해보험",
    "KR0051_신한이지손해보험",
    "KR0070_에이비엘생명보험",
    "KR0072_케이디비생명보험",
    "KR0080_에이아이에이생명보험",
    "KR0082_DB생명보험",
    "KR0083_푸본현대생명보험",
    "KR0087_동양생명",
    "KR0094_신한라이프생명보험",
    "KR0097_하나생명보험",
    "KR0100_처브라이프생명보험",
    "KR0104_농협생명보험",
    "KR1011_IBK연금보험",
    "KR1098_카카오페이손해보험",
]

ROOT = Path("md_inbox/FY2026_Q2")

# find the "[지급여력비율의 경과조치 적용에 관한 사항]" bracket section, or failing that
# the "(1) 공통적용 경과조치" heading, and print +/- context including the table.
BRACKET_RE = re.compile(r"지급여력비율의\s*경과조치\s*적용에\s*관한\s*사항")
COMMON_RE = re.compile(r"공통적용\s*경과조치")

for name in COMPANIES:
    path = ROOT / f"{name}.md"
    print("#" * 110)
    print(f"### {name}  (exists={path.exists()})")
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    hit_lines = [i for i, l in enumerate(lines) if BRACKET_RE.search(l)]
    if not hit_lines:
        hit_lines = [i for i, l in enumerate(lines) if COMMON_RE.search(l)]
    if not hit_lines:
        print("  !! NO '[지급여력비율의 경과조치 적용에 관한 사항]' OR '공통적용 경과조치' HEADER FOUND")
        # fallback: show any "보완자본 한도" line
        alt = [i for i, l in enumerate(lines) if "보완자본" in l and ("한도" in l or "안도" in l)]
        if alt:
            print(f"  (but found '보완자본 한도/안도' at lines: {[a+1 for a in alt]})")
            for a in alt[:3]:
                lo, hi = max(0, a - 5), min(len(lines), a + 20)
                for j in range(lo, hi):
                    print(f"    L{j+1}: {lines[j]}")
        continue
    for h in hit_lines[:2]:
        lo, hi = h, min(len(lines), h + 45)
        print(f"  --- context from line {h+1} ---")
        for j in range(lo, hi):
            print(f"  L{j+1}: {lines[j]}")
        print()
