"""q13_bom: check every .py / .md / .txt / .sh of this folder for a UTF-8 BOM and for non-UTF-8 bytes (READ-ONLY)"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
bad_bom, bad_enc, n = [], [], 0
for p in sorted(H.rglob("*")):
    if p.is_file() and p.suffix in (".py", ".md", ".txt", ".sh"):
        n += 1
        b = p.read_bytes()
        if b[:3] == b"\xef\xbb\xbf":
            bad_bom.append(str(p.relative_to(H)))
        try:
            b.decode("utf-8")
        except UnicodeDecodeError:
            bad_enc.append(str(p.relative_to(H)))
print("checked", n, "BOM:", bad_bom, "non-UTF8:", bad_enc)
