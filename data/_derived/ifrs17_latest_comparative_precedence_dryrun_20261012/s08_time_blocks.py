"""Read-only timing probe: how long does blocks_for_dir take for one raw dir (imports the builder module, writes nothing)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

t0 = time.time()
import build_csm_waterfall_master as B  # noqa: E402  (import only; main() is not called)

print("import", round(time.time() - t0, 1), "s")
rd = ROOT / "data/dart/FY2024_Q1/raw/KR0011_DB손해보험"
t0 = time.time()
blocks = B.blocks_for_dir(rd, "DB손해보험")
print("blocks_for_dir", len(blocks), "blocks", round(time.time() - t0, 1), "s")
for i, b in enumerate(blocks):
    st = None
    try:
        st = B.block_stages(b)
    except Exception as e:
        st = f"ERR {e}"
    print(i, (b.get("caption") or "")[:70], "| prior_cap", B._is_prior_caption(b.get("caption") or ""), "prior_hdr", B._is_prior_header(b), "| stages", st)
