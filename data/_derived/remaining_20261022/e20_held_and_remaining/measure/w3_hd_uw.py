"""w3_hd_uw: dump the '(3) UW Income' sheet rows (label + first 12 numeric cells) of a 현대해상 IR factsheet xlsx; READ-ONLY"""
import sys
import openpyxl
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/data/ir/"
f, sheet = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(ROOT + f, read_only=True, data_only=True)
ws = wb[sheet]
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    vals = [v for v in row if v is not None]
    if not vals:
        continue
    txt = " | ".join((f"{v:,.1f}" if isinstance(v, float) else str(v))[:16] for v in vals[:13])
    print(f"R{i}: {txt}"[:240])
    if i > 70:
        break
