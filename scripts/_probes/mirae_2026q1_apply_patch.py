"""Surgical patch: KR0079 (미래에셋생명) item6 for 2026.1Q into
data/dart/viz/pl_breakdown_master.json -- coordinator follow-up to inbox/parser/
20260829T1600Z, scope widened to this quarter after fresh triple reconciliation closed
exactly (mirae_2026q1_full_recon.py: boundary rule + internal population check + Tier-1
anchor all exact-won match, candidate A = candidate B). Same pattern as the 2025.2Q/2025.3Q
patch: item6 0.0 -> production value, item7 (기타 생명장기 원수손익) reduced by the same
amount so item3=4+5+6+7 keeps closing (item3/4/5 unchanged).
Backs up the file first. Touches ONLY these 2 cells.
"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import _ma_yesilcha_direct  # noqa: E402

MASTER = ROOT / "data/dart/viz/pl_breakdown_master.json"
BACKUP = ROOT / "data/dart/viz/pl_breakdown_master.json.bak_20260829_mirae_2026q1"

XML_PATH = ROOT / "data/dart/FY2026_Q1/raw/KR0079_미래에셋생명/20260529001897.xml"

tables = list(_tag_basis(
    list(_iter_tables_by_basis(XML_PATH, _iter_tables_with_context)), XML_PATH))
v = _ma_yesilcha_direct(tables)
assert v is not None, "2026.1Q: _ma_yesilcha_direct returned None -- ABORT, do not patch"
print(f"2026.1Q: production item6 = {v:.6f}")

shutil.copy2(MASTER, BACKUP)
print(f"backup -> {BACKUP}")

rows = json.loads(MASTER.read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}

k6 = ("KR0079", 6, "2026.1Q")
k7 = ("KR0079", 7, "2026.1Q")
r6, r7 = idx.get(k6), idx.get(k7)
assert r6 is not None and r7 is not None, "2026.1Q: item6/item7 row missing -- ABORT"
old6, old7 = r6["값"], r7["값"]
assert old6 == 0.0, f"2026.1Q: item6 not currently 0.0 ({old6}) -- ABORT, unexpected pre-state"
new7 = round(old7 - v, 6)
print(f"item6 {old6} -> {v:.6f}   item7 {old7} -> {new7}")
r6["값"] = round(v, 6)
r7["값"] = new7

MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {MASTER}  ({len(rows)} rows)")
