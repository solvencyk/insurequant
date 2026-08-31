import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import fitz
from PIL import Image, ImageDraw

PDF = "data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf"
PAGES = list(range(16, 33))  # 1-indexed pages 16..32
OUT = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kr0087_contact.png"

doc = fitz.open(PDF)
thumbs = []
for p in PAGES:
    idx = p - 1
    if idx < 0 or idx >= doc.page_count:
        continue
    page = doc[idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(0.6, 0.6))  # thumbnail scale
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 90, 22], fill="yellow")
    draw.text((3, 3), f"p{p}", fill="red")
    thumbs.append((p, img))
doc.close()

cols = 5
rows = (len(thumbs) + cols - 1) // cols
tw, th = thumbs[0][1].size
sheet = Image.new("RGB", (tw * cols, th * rows), "white")
for i, (p, img) in enumerate(thumbs):
    x = (i % cols) * tw
    y = (i // cols) * th
    sheet.paste(img, (x, y))

sheet.save(OUT)
print("saved", OUT, sheet.size)
