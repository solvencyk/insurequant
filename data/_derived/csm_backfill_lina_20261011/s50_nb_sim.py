# -*- coding: utf-8 -*-
"""Step 50: simulate scripts/build_nb_csm_multiple.py in a temp folder (never writes NB_CSM_multiple.json).

  before = CSM_waterfall.json as in git HEAD     -> nb_sim/NB_CSM_multiple.before.json
  after  = CSM_waterfall.json in the working tree -> nb_sim/NB_CSM_multiple.after.json
The module's globals CSM / OUT are redirected before main() runs; the real NB master's sha256 is asserted unchanged.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
SIM = W / "nb_sim"
SIM.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

real_nb = ROOT / "NB_CSM_multiple.json"
sha_before = hashlib.sha256(real_nb.read_bytes()).hexdigest()

head_csm = SIM / "CSM_waterfall.head.json"
head_csm.write_bytes(subprocess.run(["git", "show", "HEAD:CSM_waterfall.json"], cwd=ROOT, check=True, capture_output=True).stdout)


def run(label: str, csm_path: Path):
    spec = importlib.util.spec_from_file_location(f"nbsim_{label}", ROOT / "scripts" / "build_nb_csm_multiple.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.CSM = csm_path
    m.OUT = SIM / f"NB_CSM_multiple.{label}.json"
    buf = io.StringIO()
    with redirect_stdout(buf):
        m.main()
    (SIM / f"stdout.{label}.txt").write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    return json.loads(m.OUT.read_text(encoding="utf-8")), buf.getvalue()


before, out_b = run("before", head_csm)
after, out_a = run("after", ROOT / "CSM_waterfall.json")
assert hashlib.sha256(real_nb.read_bytes()).hexdigest() == sha_before, "the real NB master changed!"
print("real NB_CSM_multiple.json sha256 unchanged:", sha_before[:16])

committed = json.loads(real_nb.read_text(encoding="utf-8"))
print("rows: committed NB master", len(committed), "| sim before", len(before), "| sim after", len(after))
kb = lambda r: (r["원보험사코드"], r["공시분기"])  # noqa: E731
cm = {kb(r): r for r in committed}
bm = {kb(r): r for r in before}
am = {kb(r): r for r in after}
print("sim-before vs committed master: keys only in sim", len(set(bm) - set(cm)), "only in master", len(set(cm) - set(bm)),
      "| differing rows", sum(1 for k in set(bm) & set(cm) if bm[k] != cm[k]))
print("sim-after vs sim-before: keys added", sorted(set(am) - set(bm)), "| changed existing rows", [k for k in set(bm) & set(am) if am[k] != bm[k]])

print("\nKR0074 rows (after):")
for r in sorted([r for r in after if r["원보험사코드"] == "KR0074"], key=lambda r: r["공시분기"]):
    print(" ", r["공시분기"], {k: r[k] for k in ("신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계", "신계약CSM_당분기", "월납월초보험료_당분기", "신계약CSM배수_당분기")})
print("\nKR0074 rows (before):")
for r in sorted([r for r in before if r["원보험사코드"] == "KR0074"], key=lambda r: r["공시분기"]):
    print(" ", r["공시분기"], {k: r[k] for k in ("신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계", "신계약CSM_당분기", "월납월초보험료_당분기", "신계약CSM배수_당분기")})

# flags of the after run that mention Lina; and the range of all multiples
print("\nflags mentioning 라이나 (after):", [l for l in out_a.splitlines() if "라이나" in l])
vals = [r["신계약CSM배수_연누계"] for r in after if r["신계약CSM배수_연누계"] is not None]
print("after: YTD multiples computed", len(vals), "range", min(vals), "..", max(vals))
lina = [r["신계약CSM배수_연누계"] for r in after if r["원보험사코드"] == "KR0074" and r["신계약CSM배수_연누계"] is not None]
print("Lina YTD multiples:", lina)
