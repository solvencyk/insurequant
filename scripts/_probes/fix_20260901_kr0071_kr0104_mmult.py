"""Fix the TRANSITION_AFTER_MMULT_MISMATCH RED newly exposed for KR0071/KR0104 2026.2Q
after this session filled their missing item18/20/21 children (which finally let the
existing-but-slightly-off item15후 face its R4 cross-check). Follows the EXACT established
methodology in scripts/rebuild_combined_transition_after.py (module docstring), whose own
--only run confirmed the same axis-C failure but could not auto-fix 2026.2Q because its
raw-file lookup only checks data/disclosure/<period>/raw/ (empty for 2026.2Q) and not pdf/
(where the files actually are -- known repo issue). This script applies the same formula
by hand using leaf values already extracted from raw this session (KR0071 pages 19-21) or
already correct in the master (KR0104 item17/19, validated by a prior session's exact
sqrt-reconcile per TODO history).

  leaf_후 = whichever isolated table reduced it (already established)
  기본요구자본후(15) = sqrt(W'R4W) + 운영후,  W=(생명장기,일반손해,시장,신용)후
  기준금액후(14) = UNCHANGED (already in master, anchored to headline, matches raw p22/25)
  기타요구자본후(23): KR0071 = AFFILIATE(KR0005) 환산 (item23_전/KR0005.item14_전 비율 유지),
                      KR0104 = 0 (already established/mirrored, unaffected)
  법인세조정액후(22) = 15후 + 23후 - 14후   (RESIDUAL, per module docstring)
  분산효과후(16) = sum(17:21)후 - 15후      (rule 6, recomputed with the corrected 15후)
"""
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "solvency" / "validation"))
from kics_json_rules import R4  # noqa: E402

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
byq = {}
for r in records:
    c, q = r.get("원보험사코드"), r.get("공시분기")
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    byq.setdefault((c, q), {})[it] = r


def num(c, q, it):
    v = byq[(c, q)][it].get("값")
    return float(str(v).replace(",", ""))


def numpost(c, q, it):
    v = byq[(c, q)][it].get("값_적용후")
    return float(str(v).replace(",", ""))


# ---- KR0071 ----
print("=== KR0071 흥국생명 ===")
# leaves already confirmed from raw p19-21 this session (or already in master, cross-checked)
leaf71 = {17: 11571.05, 18: 0.0, 19: 6795.65, 20: 4282.88, 21: 2673.72}
W = np.array([leaf71[17], leaf71[18], leaf71[19], leaf71[20]], dtype=float)
item15_71 = float(np.sqrt(W @ R4 @ W)) + leaf71[21]
item14_71 = numpost("KR0071", "2026.2Q", 14)  # anchored, unchanged
ratio71 = num("KR0071", "2026.2Q", 23) / num("KR0005", "2026.2Q", 14)  # affiliate ratio, pre-column
item23_71 = ratio71 * numpost("KR0005", "2026.2Q", 14)
item22_71 = item15_71 + item23_71 - item14_71
item16_71 = sum(leaf71.values()) - item15_71
print(f"  item15 recompute: {item15_71:.4f}  (existing wrong value in master: {numpost('KR0071','2026.2Q',15)})")
print(f"  item14 anchor (unchanged): {item14_71}")
print(f"  affiliate ratio (item23_pre/KR0005.item14_pre): {ratio71:.6f}")
print(f"  item23 recompute: {item23_71:.4f}  (existing in master: {numpost('KR0071','2026.2Q',23)})")
print(f"  item22 recompute (residual): {item22_71:.4f}  (existing in master: {numpost('KR0071','2026.2Q',22)})")
print(f"  item16 recompute (rule6, using corrected 15): {item16_71:.4f}  (this session's earlier value: {numpost('KR0071','2026.2Q',16)})")
print(f"  item17/19/20/21 unchanged (already correct): {leaf71[17]},{leaf71[19]},{leaf71[20]},{leaf71[21]}")

print()
print("=== KR0104 농협생명 ===")
leaf104 = {
    17: numpost("KR0104", "2026.2Q", 17),  # already correct (prior session, exact sqrt-reconcile per TODO)
    18: 0.0,
    19: numpost("KR0104", "2026.2Q", 19),  # already correct (prior session, exact sqrt-reconcile per TODO)
    20: numpost("KR0104", "2026.2Q", 20),  # this session's mirror
    21: numpost("KR0104", "2026.2Q", 21),  # this session's mirror
}
W2 = np.array([leaf104[17], leaf104[18], leaf104[19], leaf104[20]], dtype=float)
item15_104 = float(np.sqrt(W2 @ R4 @ W2)) + leaf104[21]
item14_104 = numpost("KR0104", "2026.2Q", 14)
item23_104 = 0.0  # already established/mirrored, unaffected (no affiliate mapping for KR0104)
item22_104 = item15_104 + item23_104 - item14_104
item16_104 = sum(leaf104.values()) - item15_104
print(f"  leaves: {leaf104}")
print(f"  item15 recompute: {item15_104:.4f}  (existing wrong value in master: {numpost('KR0104','2026.2Q',15)})")
print(f"  item14 anchor (unchanged): {item14_104}")
print(f"  item23 (unaffected, 0): {item23_104}")
print(f"  item22 recompute (residual): {item22_104:.4f}  (this session's earlier value: {numpost('KR0104','2026.2Q',22)})")
print(f"  item16 recompute (rule6, using corrected 15): {item16_104:.4f}  (this session's earlier value: {numpost('KR0104','2026.2Q',16)})")

out = {
    "KR0071": {15: round(item15_71, 4), 16: round(item16_71, 4), 22: round(item22_71, 4), 23: round(item23_71, 4)},
    "KR0104": {15: round(item15_104, 4), 16: round(item16_104, 4), 22: round(item22_104, 4)},
}
(ROOT / "scripts" / "_probes" / "_kr0071_kr0104_mmult_fix.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nWrote _kr0071_kr0104_mmult_fix.json")
