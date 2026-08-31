import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, waterfall, block_stages

rd = ROOT / "data/dart/FY2023_Q2/raw/KR0003_롯데손해보험"
name = "KR0003_롯데손해보험"

blocks = blocks_for_dir(rd, name)
print(f"blocks found: {len(blocks)}")
for i, b in enumerate(blocks):
    cap = b.get("caption") or ""
    src = b.get("_src", "")
    basis = b.get("basis", "")
    rows = b.get("rows") or []
    header = b.get("header") or []
    bs = block_stages(b)
    print(f"\n--- block {i}: src={src} basis={basis} nrows={len(rows)} caption={cap[:80]!r}")
    print(f"    header={header[:3]}")
    print(f"    block_stages()={bs}")

print("\n\n=== waterfall(blocks, anchor=16774.4, code='KR0003') ===")
wf, src = waterfall(blocks, 16774.4, "KR0003")
print("wf:", wf)
print("src:", src)
