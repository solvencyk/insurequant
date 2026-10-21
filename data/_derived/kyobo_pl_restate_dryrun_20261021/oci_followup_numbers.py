"""Read-only: the OCI-only differences between the live PL master and the latest comparative for KR0073 2024.4Q / 2025.1Q / 2025.2Q (numbers for the follow-up ticket)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
alt = json.loads((HERE / "restated_blocks_alt.json").read_text(encoding="utf-8"))
a26 = json.loads((HERE / "restated_blocks_2026.json").read_text(encoding="utf-8"))
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cur, names = {}, {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
        names[r["항목번호"]] = r["항목명"]
src = {"2024.4Q": (alt["2024.4Q"], "FY2025 annual (rcept per FY2025_Q4 dir)"), "2025.1Q": (a26["2025.1Q"], "FY2026_Q1 filing rcept 20260813001077"),
       "2025.2Q": (a26["2025.2Q"], "FY2026_Q2 filing rcept 20260814004024")}
lines = []
for q, (rec, label) in src.items():
    blk = rec["restated_alt"]
    lines.append(f"{q}  later filing: {label}; Tier-1 source {rec.get('t1_src')}")
    tot_old = tot_new = 0.0
    for i in (25, 26, 27, 28, 29, 30, 31, 32, 24):
        old, new = cur[q].get(i), blk.get(str(i))
        mark = "" if (old is not None and new is not None and abs(old - new) <= 5e-4) else "  <-- differs"
        d = "" if old is None or new is None else f"{new - old:+,.2f}"
        lines.append(f"   item{i:2d} {names[i][:16]:16s} master={('None' if old is None else f'{old:,.2f}'):>16s} later={('None' if new is None else f'{new:,.2f}'):>16s} delta={d:>12s}{mark}")
    parts = [blk.get(str(i)) or 0.0 for i in (26, 27, 28, 29, 30, 32)]
    lines.append(f"   later-vector check 25 = 26+27+28+29+30+32: {blk.get('25'):,.2f} vs {sum(parts):,.2f} (residual {blk.get('25') - sum(parts):+.3f})")
    old_parts = [cur[q].get(i) or 0.0 for i in (26, 27, 28, 29, 30, 32)]
    lines.append(f"   master-vector check 25 = parts: {cur[q].get(25):,.2f} vs {sum(old_parts):,.2f} (residual {cur[q].get(25) - sum(old_parts):+.3f})")
text = "\n".join(lines)
(HERE / "oci_followup_numbers.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
print(text)
