"""Read-only: Kyobo OCI cells before (git HEAD) -> after (live), in 억원 (1억 = 100백만). 누계 = 값, 단일분기 = 값_당분기."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
h = json.loads(subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown.json"], capture_output=True).stdout.decode("utf-8"))
l = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
hm, lm = {key(r): r for r in h}, {key(r): r for r in l}
def f(v):
    return "blank" if v is None else f"{v/100:,.2f}"
lines = ["KR0073 교보생명 OCI, 억원 (before = git HEAD, after = live). 누계(값) / 단일분기(값_당분기)"]
for q in ("2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q"):
    for it in (25, 26, 29, 31, 32):
        a, b = hm[("KR0073", it, q)], lm[("KR0073", it, q)]
        if a["값"] == b["값"] and a["값_당분기"] == b["값_당분기"]:
            continue
        lines.append(f"{q} item {it} {b['항목명'][:12]:12s} 누계 {f(a['값']):>12s} -> {f(b['값']):>12s} | 단일분기 {f(a['값_당분기']):>12s} -> {f(b['값_당분기']):>12s}")
open("onscreen_oci_eok.txt", "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("\n".join(lines))
