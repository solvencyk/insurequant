# -*- coding: utf-8 -*-
"""KR0069 삼성생명 2026.2Q raw PDF p48(7-3.해약환급금준비금등의적립) 육안확인용 렌더. 일회성."""
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "raw"
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\bf3f149f-63da-4c1f-b00e-c41148decd48\scratchpad"
)

matches = [p for p in RAW_DIR.glob("*.pdf") if p.name.startswith("KR0069_")]
path = matches[0]
doc = fitz.open(str(path))
mat = fitz.Matrix(240 / 72, 240 / 72)
pix = doc[47].get_pixmap(matrix=mat)  # page 48 (0-indexed 47)
out = SCRATCH / "KR0069_p48.png"
pix.save(str(out))
print(f"saved -> {out} ({pix.width}x{pix.height})")
doc.close()
