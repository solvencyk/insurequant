"""Read-only helper: write a SANDBOX COPY of scripts/emit_pl_provenance.py whose three paths come from environment variables.

Why a copy: the original calls main() at import time (no __main__ guard) and writes the live PL_breakdown_provenance.json, so it can neither be imported nor
monkeypatched safely.  The copy differs from the original only in these four assignments (each asserted to occur exactly once):
    ROOT   -> explicit repo path (the copy lives elsewhere)
    PL_SRC -> $EMIT_PL_SRC ; PL_OVR -> $EMIT_PL_OVR ; PL_OUT -> $EMIT_PL_OUT
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
src = (ROOT / "scripts" / "emit_pl_provenance.py").read_text(encoding="utf-8")
subs = [
    ('ROOT = Path(__file__).resolve().parents[1]', 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")'),
    ('PL_SRC = ROOT / "PL_breakdown.json"', 'PL_SRC = Path(os.environ["EMIT_PL_SRC"])'),
    ('PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"', 'PL_OVR = Path(os.environ["EMIT_PL_OVR"])'),
    ('PL_OUT = ROOT / "PL_breakdown_provenance.json"', 'PL_OUT = Path(os.environ["EMIT_PL_OUT"])'),
]
for old, new in subs:
    assert src.count(old) == 1, f"expected exactly one occurrence of: {old}"
    src = src.replace(old, new)
out = HERE / "emit_pl_provenance_sandbox_copy.py"
out.write_text(src, encoding="utf-8", newline="\n")
print("wrote", out.name, len(src), "chars")
