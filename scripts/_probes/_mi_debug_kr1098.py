import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
import fitz

p = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf" / "KR1098_카카오페이손해보험.pdf"
doc = fitz.open(str(p))
print(doc[2].get_text()[:1000])
doc.close()
