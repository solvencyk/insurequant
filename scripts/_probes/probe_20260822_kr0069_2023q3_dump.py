import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fix_20260821_tier2_limit_lines as T2  # noqa: E402
import fitz  # noqa: E402


def norm(s):
    return s.replace(" ", "")


pdf = T2._pdf("FY2023_Q3", "KR0069")
print(pdf.name)
doc = fitz.open(pdf)
page_texts = [doc[i].get_text() for i in range(doc.page_count)]
doc.close()
matched = {i for i, t in enumerate(page_texts)
           if "공통적용" in t and "보완자본" in t and "한도" in t}
print("matched pages (0-idx):", sorted(matched))
include = set(matched)
for i in matched:
    if i + 1 < len(page_texts):
        include.add(i + 1)
lines = []
for i in sorted(include):
    lines.extend(x.strip() for x in page_texts[i].splitlines())
pos47 = next((k for k, l in enumerate(lines) if norm(l) == norm("보완자본 한도 적용 전")), None)
print("pos47:", pos47, "total lines:", len(lines))
lo = max(0, (pos47 or 0) - 25)
hi = min(len(lines), (pos47 or 0) + 5)
for i in range(lo, hi):
    print(f"  [{i}] {lines[i]!r}")
