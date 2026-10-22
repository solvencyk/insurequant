"""gate_digest: compact comparison of a scenario gate folder vs g_base: data_contract RED/YELLOW findings added, master_tables SUMMARY field changes, continuity lines, removed/added FAIL lines. (READ-ONLY)"""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
def lines(p): return Path(p).read_text(encoding="utf-8", errors="replace").splitlines()
def summ(p):
    for l in lines(p):
        if l.startswith("SUMMARY"):
            return [x.strip() for x in l.split("|")]
    return []
FIND = re.compile(r"^\s{2}(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(.+)$")
def finds(p):
    out = set()
    for l in lines(p):
        m = FIND.match(l)
        if m:
            out.add((m.group(1), m.group(2), m.group(3), m.group(4).strip()[:60]))
    return out
for s in sys.argv[1:]:
    b, a = H / "g_base", H / f"g_{s}"
    print("=" * 100); print("SCENARIO", s)
    sb, sa = summ(b / "master_tables.txt"), summ(a / "master_tables.txt")
    for x, y in zip(sb, sa):
        if x != y: print("  master_tables SUMMARY:", x[:150], "  ->  ", y[:150])
    fb = {l.strip() for l in lines(b / "master_tables.txt") if "FAIL" in l or "WFY" in l or "CONT " in l or "SPIKE" in l}
    fa = {l.strip() for l in lines(a / "master_tables.txt") if "FAIL" in l or "WFY" in l or "CONT " in l or "SPIKE" in l}
    for l in sorted(fa - fb): print("  + master_tables:", l[:200])
    for l in sorted(fb - fa): print("  - master_tables:", l[:200])
    db, da = finds(b / "data_contract.txt"), finds(a / "data_contract.txt")
    for f in sorted(da - db): print("  + data_contract:", f)
    for f in sorted(db - da): print("  - data_contract:", f)
    sdb, sda = summ(b / "data_contract.txt"), summ(a / "data_contract.txt")
    print("  data_contract SUMMARY:", sdb, "->", sda)
    cb, ca = lines(b / "csm_continuity.txt"), lines(a / "csm_continuity.txt")
    print("  continuity before:", cb[0][:80], "| after:", ca[0][:80])
    for l in ca[1:]:
        if l not in cb and l.startswith("  "): print("  + continuity:", l[:230])
    for l in cb[1:]:
        if l not in ca and l.startswith("  "): print("  - continuity:", l[:230])
    for g in ("csm_waterfall", "nb_csm", "csm_coverage"):
        gb, ga = lines(b / f"{g}.txt"), lines(a / f"{g}.txt")
        if gb != ga: print(f"  {g}: differs ->", [l for l in ga if l not in gb][:3])
    lb, la = lines(b / "live_artifacts.txt"), lines(a / "live_artifacts.txt")
    print("  live_artifacts:", [l for l in la if l.startswith("SUMMARY")], " base:", [l for l in lb if l.startswith("SUMMARY")])
