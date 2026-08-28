"""Cell-level patch (NOT a full build_pl_breakdown.py rebuild -- see SKILL.md /
inbox/parser/20260828T2300Z): write KR0079 2026.2Q item6/item7 into
data/dart/viz/pl_breakdown_master.json using the EXACT values the real production dispatch
(parse_filing -> assemble) produces, verified in scripts/_probes/mirae_parse_filing_test.py.

Idempotent-safe: asserts the BEFORE values match the known baseline, so re-running this after
it already applied will fail loudly instead of double-patching or overwriting someone else's
change.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
MASTER = ROOT / "data/dart/viz/pl_breakdown_master.json"

NEW_ITEM6 = -18120.139965
NEW_ITEM7 = -77480.939869
OLD_ITEM6 = 0.0
OLD_ITEM7 = -95601.079834

d = json.loads(MASTER.read_text(encoding="utf-8"))
n_patched = 0
for r in d:
    if r.get("원보험사코드") != "KR0079" or r.get("공시분기") != "2026.2Q":
        continue
    if r.get("항목번호") == 6:
        assert r["값"] == OLD_ITEM6, f"item6 baseline mismatch: {r['값']!r}"
        r["값"] = NEW_ITEM6
        n_patched += 1
    elif r.get("항목번호") == 7:
        assert r["값"] == OLD_ITEM7, f"item7 baseline mismatch: {r['값']!r}"
        r["값"] = NEW_ITEM7
        n_patched += 1

assert n_patched == 2, f"expected to patch exactly 2 cells, patched {n_patched}"
MASTER.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"patched {n_patched} cells in {MASTER}")

# verify readback
d2 = json.loads(MASTER.read_text(encoding="utf-8"))
row6 = next(r for r in d2 if r["원보험사코드"] == "KR0079" and r["항목번호"] == 6 and r["공시분기"] == "2026.2Q")
row7 = next(r for r in d2 if r["원보험사코드"] == "KR0079" and r["항목번호"] == 7 and r["공시분기"] == "2026.2Q")
print("readback item6:", row6["값"])
print("readback item7:", row7["값"])
assert row6["값"] == NEW_ITEM6 and row7["값"] == NEW_ITEM7
print("OK")
