"""Move all PDFs from _to_be/<PERIOD>/pdf/ into their actual destinations
data/disclosure/<PERIOD>/pdf/, then delete the empty _to_be tree.
"""
from __future__ import annotations

import shutil
from pathlib import Path

TO_BE = Path(
    r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure\_to_be"
)
DISCLOSURE = Path(r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure")

if not TO_BE.exists():
    print("_to_be folder does not exist.")
    exit(0)

moved = 0
for pdf in sorted(TO_BE.rglob("*.pdf")):
    # _to_be/FY2023_Q1/pdf/KR0001.pdf -> extract FY2023_Q1
    period = pdf.parent.parent.name
    target_dir = DISCLOSURE / period / "pdf"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / pdf.name
    if target.exists():
        print(f"SKIP (exists): {pdf.name} -> {period}")
        continue
    print(f"Move {pdf.name} -> {period}/pdf/")
    shutil.move(str(pdf), str(target))
    moved += 1

print(f"\nMoved {moved} files.")

# cleanup empty _to_be tree
try:
    shutil.rmtree(TO_BE)
    print("Removed _to_be folder.")
except Exception as e:
    print(f"Could not remove _to_be: {e}")
