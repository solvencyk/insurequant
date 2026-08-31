import sys, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, waterfall, block_stages

rd = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명"
name = "KR0079_미래에셋생명"

blocks = blocks_for_dir(rd, name)
print(f"blocks found: {len(blocks)}")
for i, b in enumerate(blocks):
    cap = b.get("caption") or b.get("_caption") or ""
    src = b.get("_src", "")
    basis = b.get("basis", "")
    rows = b.get("rows") or b.get("data") or []
    print(f"\n--- block {i}: src={src} basis={basis} caption={cap!r} nrows={len(rows)}")
    stages = block_stages(b)
    print(f"    block_stages() = {stages}")
    # print first few rows for inspection
    for r in rows[:6]:
        print("    row:", r)

print("\n\n=== waterfall(blocks, anchor=19792.7, code='KR0079') ===")
wf, src = waterfall(blocks, 19792.7, "KR0079")
print("wf:", wf)
print("src:", src)
