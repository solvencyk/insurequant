# -*- coding: utf-8 -*-
"""Step 95 (temp folder only): what the NB quarterly (당분기) multiples of Lina would be if the 20 existing cells that became derivable
(proposed_derived_dangi_existing.json) were filled.  The real masters are never written; a modified COPY of CSM_waterfall.json goes to nb_sim/."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
SIM = W / "nb_sim"
SIM.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

real_nb = ROOT / "NB_CSM_multiple.json"
sha_nb = hashlib.sha256(real_nb.read_bytes()).hexdigest()
sha_wf = hashlib.sha256((ROOT / "CSM_waterfall.json").read_bytes()).hexdigest()

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
cells = json.loads((W / "proposed_derived_dangi_existing.json").read_text(encoding="utf-8"))["cells"]
want = {(c["공시분기"], c["항목번호"]): c["build_csm_규칙_도출값"] for c in cells}
n = 0
for r in wf:
    k = (r["공시분기"], r["항목번호"])
    if r["원보험사코드"] == "KR0074" and k in want and r["값_당분기"] is None:
        r["값_당분기"] = want[k]
        n += 1
tmp = SIM / "CSM_waterfall.with_derived_copy.json"
tmp.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("filled", n, "cells in the COPY")

spec = importlib.util.spec_from_file_location("nbsim_derived", ROOT / "scripts" / "build_nb_csm_multiple.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.CSM = tmp
m.OUT = SIM / "NB_CSM_multiple.with_derived.json"
buf = io.StringIO()
with redirect_stdout(buf):
    m.main()
rows = json.loads(m.OUT.read_text(encoding="utf-8"))
for r in sorted([r for r in rows if r["원보험사코드"] == "KR0074"], key=lambda r: r["공시분기"]):
    print(r["공시분기"], "당분기 신계약CSM", r["신계약CSM_당분기"], "월납 당분기", r["월납월초보험료_당분기"], "배수_당분기", r["신계약CSM배수_당분기"])
assert hashlib.sha256(real_nb.read_bytes()).hexdigest() == sha_nb and hashlib.sha256((ROOT / "CSM_waterfall.json").read_bytes()).hexdigest() == sha_wf
print("real NB master and real CSM_waterfall.json unchanged")
