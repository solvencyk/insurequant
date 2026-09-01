# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import derive_irr  # noqa: E402

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
mine = {int(r["항목번호"]): r for r in rows if r["원보험사코드"] == "KR0069" and r["공시분기"] == "2026.2Q"}
vals = [float(str(mine[i]["값"]).replace(",", "")) for i in (41, 42, 43, 44, 45, 46)]
derived = derive_irr(vals)
item36 = float(str(mine[36]["값"]).replace(",", ""))
diff = derived - item36
rel = abs(diff) / item36 * 100
print(f"41-46 vals (억원) = {vals}")
print(f"derive_irr(41-46) = {derived:.2f} 억원")
print(f"item36 (금리위험액, master) = {item36:.2f} 억원")
print(f"diff = {diff:+.2f}  rel = {rel:.3f}%")
