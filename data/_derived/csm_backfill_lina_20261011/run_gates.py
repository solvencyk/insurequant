# -*- coding: utf-8 -*-
"""Run the read-only gates for the Lina CSM backfill and capture their output.

usage: run_gates.py <label>      (label = before | after)

  1. scripts/validate_data_contract.py            (no args = the gate itself; pure read, verified: no writes, no build)
  2. scripts/validate_master_tables.py --no-build (ALWAYS --no-build; it writes data/_derived/qoq_warn.json and
                                                   data/_derived/pl_oci_vs_bs_aoci_warn.json as a side effect -> the copy
                                                   it wrote is kept under gate_<label>/ and the live files are put back
                                                   to the bytes they had before this script ran)
  3. validate_csm_continuity.main() in-process with OUT redirected to the work dir (the stock script overwrites
     data/dart/viz/csm_continuity_validation.json)
  4. validate_nb_csm_multiple / validate_csm_waterfall are NOT affected by a root-master change (they read the viz panel /
     IR benchmark files) -- run in-process with their OUT_PATH redirected, outputs kept for the record.

Nothing under the repo root is written by this script except (temporarily) the two side-effect files above.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")

label = sys.argv[1]
OUTD = WORK / f"gate_{label}"
OUTD.mkdir(exist_ok=True)
SIDE = [ROOT / "data/_derived/qoq_warn.json", ROOT / "data/_derived/pl_oci_vs_bs_aoci_warn.json"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


pre = {p: p.read_bytes() for p in SIDE}


def run(cmd, outname):
    r = subprocess.run(cmd, capture_output=True, cwd=str(ROOT))
    out = r.stdout.decode("utf-8", errors="replace")
    err = r.stderr.decode("utf-8", errors="replace")
    (OUTD / outname).write_text(out + ("\n[stderr]\n" + err if err.strip() else ""), encoding="utf-8", newline="\n")
    print(f"{outname}: exit {r.returncode}, {len(out.splitlines())} lines")
    return r.returncode, out


rc1, out1 = run([PY, "scripts/validate_data_contract.py"], "data_contract.txt")
rc2, out2 = run([PY, "scripts/validate_master_tables.py", "--no-build"], "master_tables.txt")

# keep what the gate wrote, then put the live files back
for p in SIDE:
    if p.read_bytes() != pre[p]:
        shutil.copyfile(p, OUTD / (p.name + ".written_by_gate"))
        p.write_bytes(pre[p])
        print("restored", p.name)
    else:
        print("unchanged", p.name)

# in-process domain gates with redirected outputs
sys.path.insert(0, str(ROOT / "scripts"))
import validate_csm_continuity as vcc  # noqa: E402

vcc.OUT = OUTD / "csm_continuity_validation.json"
buf = io.StringIO()
with redirect_stdout(buf):
    rc3 = vcc.main()
(OUTD / "csm_continuity.txt").write_text(buf.getvalue(), encoding="utf-8", newline="\n")
print("csm_continuity: exit", rc3, "|", buf.getvalue().splitlines()[0])

import validate_csm_waterfall as vcw  # noqa: E402

vcw.OUT_PATH = OUTD / "csm_waterfall_validation.json"
buf = io.StringIO()
with redirect_stdout(buf):
    rc4 = vcw.main()
(OUTD / "csm_waterfall.txt").write_text(buf.getvalue(), encoding="utf-8", newline="\n")
print("csm_waterfall (viz panel): exit", rc4, "|", buf.getvalue().splitlines()[1] if len(buf.getvalue().splitlines()) > 1 else "")

try:
    import validate_nb_csm_multiple as vnb  # noqa: E402

    vnb.OUT_PATH = OUTD / "nb_csm_validation.json"
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc5 = vnb.main()
    (OUTD / "nb_csm_validation.txt").write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    print("nb_csm_validation: exit", rc5, "|", buf.getvalue().splitlines()[-1] if buf.getvalue().splitlines() else "")
except Exception as e:  # noqa: BLE001
    print("nb_csm_validation: could not run in-process:", repr(e))

# summary lines of the two big gates
for name, txt in (("data_contract", out1), ("master_tables", out2)):
    lines = [l for l in txt.splitlines() if "SUMMARY" in l or "RED" in l[:12] or l.startswith("RESULT") or "GATE" in l[:20]]
    print(f"--- {name}: {len(txt.splitlines())} lines; key lines ---")
    for l in lines[:25]:
        print("  ", l)
