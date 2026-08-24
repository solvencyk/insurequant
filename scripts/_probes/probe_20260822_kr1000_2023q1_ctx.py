import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fix_20260821_tier2_limit_lines as T2  # noqa: E402
import fitz  # noqa: E402

pdf = T2._pdf(T2.q2p("2023.1Q"), "KR1000")
doc = fitz.open(pdf)
page_texts = [doc[i].get_text() for i in range(doc.page_count)]
doc.close()
matched = {i for i, t in enumerate(page_texts)
           if "공통적용" in t and "보완자본" in t and "한도" in t}
include = set(matched)
for i in matched:
    if i + 1 < len(page_texts):
        include.add(i + 1)
lines = []
for i in sorted(include):
    lines.extend(x.strip() for x in page_texts[i].splitlines())
for i in range(0, 70):
    print(f"  [{i}] {lines[i]!r}")
