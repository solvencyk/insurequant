import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fix_20260821_tier2_limit_lines as T2  # noqa: E402
import fitz  # noqa: E402


def norm(s):
    return s.replace(" ", "")


for q in ("2023.1Q", "2024.4Q", "2025.1Q"):
    pdf = T2._pdf(T2.q2p(q), "KR1000")
    print(f"\n=========== {q}  {pdf.name} ===========")
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
    # find pos47
    targets47 = norm("보완자본 한도 적용 전")
    pos47 = next((k for k, l in enumerate(lines) if norm(l) == targets47), None)
    print("pos47:", pos47)
    if pos47 is not None:
        lo = max(0, pos47 - 20)
        for i in range(lo, pos47 + 3):
            print(f"  [{i}] {lines[i]!r}")
    else:
        print("  (item47 라벨 자체 못 찾음 -- 전체 lines 개수:", len(lines), ")")
        for i, l in enumerate(lines):
            if "기본자본" in l or "보완자본" in l:
                print(f"  [{i}] {l!r}")
