import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir, waterfall, block_stages
from viz_build_csm_waterfall import extract_stages

rd = ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명"
name = "KR0079_미래에셋생명"

blocks = blocks_for_dir(rd, name)
print(f"blocks found: {len(blocks)}")
for i, b in enumerate(blocks):
    cap = b.get("caption") or ""
    src = b.get("_src", "")
    basis = b.get("basis", "")
    rows = b.get("rows") or []
    header = b.get("header") or []
    bs_stages = block_stages(b)
    es_stages = extract_stages(b)
    print(f"\n--- block {i}: src={src} basis={basis} nrows={len(rows)}")
    print(f"    caption={cap[:100]!r}")
    print(f"    header={header}")
    print(f"    block_stages()={bs_stages}")
    print(f"    extract_stages()={es_stages}")

print("\n\n=== waterfall(blocks, anchor=20775.6, code='KR0079') ===")
wf, src = waterfall(blocks, 20775.6, "KR0079")
print("wf:", wf)
print("src:", src)
