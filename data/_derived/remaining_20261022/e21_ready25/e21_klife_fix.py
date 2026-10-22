# -*- coding: utf-8 -*-
"""e21 experiment for the extract_tier2_kblife `_jang_rerev = abs(jrr)` fix.  Runs scripts/build_pl_breakdown.py (the builder the PL golden test reruns) with the CURRENT code,
diffs the rewritten data/dart/viz/pl_breakdown_master.json + data/_derived/pl_breakdown_coverage.json against their pre-run bytes cell by cell and ALWAYS restores the pre-run bytes
(the same discipline as tests/test_pl_breakdown_golden.py).  usage: e21_klife_fix.py <out_prefix> [--keep]   (--keep leaves the rebuilt files in place; default restores)"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MASTER = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
COVERAGE = ROOT / "data" / "_derived" / "pl_breakdown_coverage.json"
BUILDER = ROOT / "scripts" / "build_pl_breakdown.py"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
EV = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
prefix = sys.argv[1]
keep = "--keep" in sys.argv
backups = {p: p.read_bytes() for p in (MASTER, COVERAGE)}
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
old_rows = json.loads(backups[MASTER].decode("utf-8"))
old_cov = json.loads(backups[COVERAGE].decode("utf-8"))
t0 = time.time()
out = []
try:
    proc = subprocess.run([PY, str(BUILDER)], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=1500)
    out.append(f"builder rc={proc.returncode} in {time.time() - t0:.0f}s")
    (EV / f"{prefix}_builder_stdout.txt").write_text((proc.stdout or "")[-20000:] + "\n--- stderr ---\n" + (proc.stderr or "")[-5000:], encoding="utf-8", newline="\n")
    new_rows = json.loads(MASTER.read_text(encoding="utf-8"))
    new_cov = json.loads(COVERAGE.read_text(encoding="utf-8"))
    key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
    ob, nb = {key(r): r for r in old_rows}, {key(r): r for r in new_rows}
    out.append(f"rows {len(old_rows)} -> {len(new_rows)}; sha256 master {sha(backups[MASTER])[:12]} -> {sha(MASTER.read_bytes())[:12]}; coverage {sha(backups[COVERAGE])[:12]} -> {sha(COVERAGE.read_bytes())[:12]}")
    chg = [k for k in nb if k not in ob or ob[k] != nb[k]]
    gone = [k for k in ob if k not in nb]
    out.append(f"changed/new cells in the viz master: {len(chg)}; vanished: {len(gone)}")
    for k in sorted(chg):
        a, b = ob.get(k), nb[k]
        fields = sorted(f for f in set(a or {}) | set(b) if (a or {}).get(f) != b.get(f))
        out.append(f"   {k}: " + "; ".join(f"{f}: {(a or {}).get(f)} -> {b.get(f)}" for f in fields))
    out.append(f"coverage rows {len(old_cov)} -> {len(new_cov)}; coverage identical: {old_cov == new_cov}")
finally:
    if not keep:
        for p, b in backups.items():
            p.write_bytes(b)
        out.append("restored the pre-run bytes of the viz master and the coverage file")
    else:
        out.append("--keep: the rebuilt files stay in place")
txt = "\n".join(out)
(EV / f"{prefix}_diff.txt").write_text(txt + "\n", encoding="utf-8", newline="\n")
print(txt)
