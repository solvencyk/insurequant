import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fix_20260821_tier2_limit_lines as T2  # noqa: E402
import fitz  # noqa: E402


def norm(s):
    return s.replace(" ", "")


for q in ("2023.1Q", "2025.1Q"):
    pdf = T2._pdf(T2.q2p(q), "KR1000")
    print(f"\n=========== {q}  {pdf.name} ===========")
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
    print(f"total lines={len(lines)}")
    for i, l in enumerate(lines):
        if norm(l) in ("기본자본", "보완자본", "지급여력금액"):
            print(f"  [{i}] {l!r}")
