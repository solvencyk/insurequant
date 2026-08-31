import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir

rd = ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명"
name = "KR0079_미래에셋생명"

blocks = blocks_for_dir(rd, name)
b = blocks[0]
rows = b.get("rows") or []
print(f"nrows={len(rows)}")
for i, r in enumerate(rows):
    print(i, r)
