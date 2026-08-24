import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fitz  # noqa: E402

pdf = REPO / "data" / "disclosure" / "FY2026_Q1" / "raw" / "KR0087_동양생명.pdf"
doc = fitz.open(pdf)
print("page_count:", doc.page_count)
# printed page "17" per prior TODO note -- try a small range around it (0-idx)
for i in (15, 16, 17, 18):
    page = doc[i]
    pix = page.get_pixmap(dpi=220)
    out = REPO / "scripts" / "_probes" / f"kr0087_2026q1_p{i}.png"
    pix.save(str(out))
    print(f"page idx {i} -> {out} ({pix.width}x{pix.height}), text_len={len(page.get_text())}")
doc.close()
