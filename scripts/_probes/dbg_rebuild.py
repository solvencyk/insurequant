import io, sys
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(REPO / "src"))
from rebuild_combined_transition_after import scan_occurrences, resolve_leaf, _pdf, q2p, LIFE7, MARKET5
from solvency.validation.kics_json_rules import R4, R7, MARKET_M
code, q = sys.argv[1], sys.argv[2]
occ, hl = scan_occurrences(_pdf(q2p(q), code))
print("headline:", hl)
for k in ["기본요구자본", "기준금액", "가용자본", "법인세", "기타요구자본", "생명장기", "일반손해", "시장", "신용", "운영"] + LIFE7 + MARKET5:
    print(f"  {k:<12} {occ.get(k)}")
leaves = {}
for k in LIFE7 + MARKET5 + ["신용", "운영", "일반손해"]:
    leaves[k], note = resolve_leaf(occ.get(k, []))
    print(f"   leaf {k:<10} -> {leaves[k]}  ({note})")
