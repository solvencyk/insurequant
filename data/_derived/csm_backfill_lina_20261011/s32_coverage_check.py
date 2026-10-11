# -*- coding: utf-8 -*-
"""Step 32: scripts/check_csm_coverage.py (read-only) in-process, before (git HEAD CSM_waterfall) vs after (working tree)."""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
(W / "nb_sim").mkdir(exist_ok=True)
head = W / "nb_sim" / "CSM_waterfall.head.json"
head.write_bytes(subprocess.run(["git", "show", "HEAD:CSM_waterfall.json"], cwd=ROOT, check=True, capture_output=True).stdout)


def run(label, path):
    spec = importlib.util.spec_from_file_location(f"cov_{label}", ROOT / "scripts" / "check_csm_coverage.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.CSM = path
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = m.main()
    print(f"--- {label}: exit {rc}")
    print(buf.getvalue().rstrip())
    return buf.getvalue()


b = run("before (HEAD)", head)
a = run("after (working tree)", ROOT / "CSM_waterfall.json")
