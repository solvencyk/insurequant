"""Read-only: what the CSM R-without-pins package changes in data/_gold/gold_overlay_ledger.json and data/_gold/user_csm_cells.json (live vs package)."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
P = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021" / "R_nopins_package"
sys.stdout.reconfigure(encoding="utf-8")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


lv, pk = load(ROOT / "data/_gold/gold_overlay_ledger.json"), load(P / "data/_gold/gold_overlay_ledger.json")
le, pe = lv["entries"], pk["entries"]
print("ledger top-level keys equal:", set(lv) == set(pk), "| entries live/package:", len(le), len(pe))
for k in sorted(set(le) - set(pe)):
    print("  REMOVED pin:", k, "|", {x: le[k].get(x) for x in ("overlay", "verdict", "gold", "src")})
for k in sorted(set(pe) - set(le)):
    print("  ADDED   pin:", k, "|", {x: pe[k].get(x) for x in ("overlay", "verdict", "gold", "src")}, "|", str(pe[k].get("note"))[:140])
chg = [k for k in set(le) & set(pe) if le[k] != pe[k]]
print("  changed pins:", chg)
gl, gp = load(ROOT / "data/_gold/user_csm_cells.json"), load(P / "data/_gold/user_csm_cells.json")
print("\nuser_csm_cells top-level keys equal:", set(gl) == set(gp))
key = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])
a, b = {key(e): e for e in gl["set"]}, {key(e): e for e in gp["set"]}
print("gold entries live/package:", len(a), len(b))
added = sorted(set(b) - set(a), key=lambda x: (x[2], x[1]))
upd = sorted((k for k in set(a) & set(b) if a[k] != b[k]), key=lambda x: (x[2], x[1]))
print("added:", len(added), "updated:", len(upd), "removed:", len(set(a) - set(b)))
for k in upd[:30]:
    print("  UPD", k, a[k].get("값"), "->", b[k].get("값"))
for k in added[:30]:
    print("  ADD", k, "->", b[k].get("값"))
