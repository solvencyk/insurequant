"""Surgical patch: KR0079 (미래에셋생명) item6 for 2025.2Q/2025.3Q into
data/dart/viz/pl_breakdown_master.json, following the exact same pattern as the 2026.2Q patch
(inbox/_resolved 20260828T2300Z item 7): item6 0.0 -> new value (via the PRODUCTION
_ma_yesilcha_direct, post label-variant edit), item7 (기타 생명장기 원수손익) reduced by the
same amount so item3 = 4+5+6+7 keeps closing (item3/4/5 unchanged).
Backs up the file first. Touches ONLY these 4 cells -- prints before/after for verification.
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
BACKUP = ROOT / "data/dart/viz/pl_breakdown_master.json.bak_20260829_mirae_2025q2q3"

XML_PATHS = {
    "2025.2Q": ROOT / "data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml",
    "2025.3Q": ROOT / "data/dart/FY2025_Q3/raw/KR0079_미래에셋생명/xml/20251114002791.xml",
}

# Recompute item6 fresh from raw XML via the ACTUAL production function (not hand-copied),
# so the patched value is exactly what the committed code would emit.
item6_new = {}
for q, xml_path in XML_PATHS.items():
    tables = list(_tag_basis(
        list(_iter_tables_by_basis(xml_path, _iter_tables_with_context)), xml_path))
    v = _ma_yesilcha_direct(tables)
    assert v is not None, f"{q}: _ma_yesilcha_direct returned None -- ABORT, do not patch"
    item6_new[q] = v
    print(f"{q}: production item6 = {v:.6f}")

shutil.copy2(MASTER, BACKUP)
print(f"\nbackup -> {BACKUP}")

rows = json.loads(MASTER.read_text(encoding="utf-8"))
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}

changed = []
for q, new6 in item6_new.items():
    k6 = ("KR0079", 6, q)
    k7 = ("KR0079", 7, q)
    r6, r7 = idx.get(k6), idx.get(k7)
    assert r6 is not None and r7 is not None, f"{q}: item6/item7 row missing -- ABORT"
    old6, old7 = r6["값"], r7["값"]
    assert old6 == 0.0, f"{q}: item6 not currently 0.0 ({old6}) -- ABORT, unexpected pre-state"
    new7 = round(old7 - new6, 6)
    print(f"\n{q}: item6 {old6} -> {new6:.6f}   item7 {old7} -> {new7}")
    r6["값"] = round(new6, 6)
    r7["값"] = new7
    changed.append((q, "item6", old6, r6["값"]))
    changed.append((q, "item7", old7, r7["값"]))

MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nwrote {MASTER}  ({len(rows)} rows, unchanged count)")
print(f"\nchanged cells: {len(changed)}")
for c in changed:
    print(" ", c)
