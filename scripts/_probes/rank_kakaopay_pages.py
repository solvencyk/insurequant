import io
import sys
from pathlib import Path

from PIL import Image

DIR = Path(sys.argv[1])
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

rows = []
for png in sorted(DIR.glob("*.png")):
    img = Image.open(png).convert("L")
    pixels = list(img.getdata())
    n = len(pixels)
    dark = sum(1 for p in pixels if p < 200)
    rows.append((png.stem, dark / n))

for tag in ("q3", "q2"):
    print(f"=== {tag} ===")
    subset = [r for r in rows if r[0].startswith(tag)]
    for name, ratio in subset:
        bar = "#" * int(ratio * 200)
        print(f"{name}: {ratio:.4f} {bar}")
