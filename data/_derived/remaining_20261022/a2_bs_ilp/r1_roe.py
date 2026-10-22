"""compare.html ROE effect: master vs after, recomputed with the panel rule (viz_build_compare_panel.py line 20)."""
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def load_head(p): return json.loads(subprocess.run(["git", "show", "HEAD:" + p], cwd=R, capture_output=True, check=True).stdout.decode("utf-8"))
bs_h = load_head("IFRS17_BS.json"); bs_c = json.load(open(R + "IFRS17_BS.json", encoding="utf-8"))
pl = json.load(open(R + "PL_breakdown.json", encoding="utf-8"))
eq = lambda bs: {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 3}
ni = {r["공시분기"]: r["값"] for r in pl if r["원보험사코드"] == "KR0073" and r["항목번호"] == 24}
mult = {1: 4, 2: 2, 3: 4 / 3, 4: 1}
def roe(E, q):
    y, n = int(q[:4]), int(q[5])
    prev = f"{y-1}.4Q"
    if prev not in E or q not in E or q not in ni: return None
    avg = (E[prev] + E[q]) / 2
    return ni[q] * mult[n] / avg * 100
Eh, Ec = eq(bs_h), eq(bs_c)
print("quarter  ROE_before  ROE_after  screen(1dp) before->after")
for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"):
    a, b = roe(Eh, q), roe(Ec, q)
    print(q, f"{a:.2f}", f"{b:.2f}", f"{a:.1f} -> {b:.1f}")
