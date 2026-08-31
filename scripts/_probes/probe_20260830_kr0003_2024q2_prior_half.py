import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, block_stages

rd = ROOT / "data/dart/FY2024_Q2/raw/KR0003_롯데손해보험"
name = "KR0003_롯데손해보험"

blocks = blocks_for_dir(rd, name)
print(f"blocks found: {len(blocks)}")
for i, b in enumerate(blocks):
    cap = b.get("caption") or ""
    bs = block_stages(b)
    print(f"\n--- block {i}: caption={cap[:90]!r}")
    print(f"    block_stages()={bs}")
    if bs:
        print(f"    in 억원: {{k: round(v/100,2) for k,v in bs if v}}" if False else
              {k: (round(v/100, 2) if v is not None else None) for k, v in bs.items()})
