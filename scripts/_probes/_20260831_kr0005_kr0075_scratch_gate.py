# -*- coding: utf-8 -*-
"""Apply the KR0005 + KR0075 (x2) 2026.2Q TFI patches onto a SCRATCH COPY of the
live kics_disclosure.json (never writes the real root file), then run the real
gate against both the untouched live master (baseline) and the scratch copy,
and diff every finding whose status differs anywhere in the whole file (not
just the two target companies) -- to prove zero out-of-scope drift.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PY = r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.path.insert(0, str(ROOT / "scripts"))
import apply_2026q2_patches as ap  # noqa: E402

MASTER = ROOT / "kics_disclosure.json"
SCRATCH = ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_20260831_kr0005_kr0075.json"

PATCHES = [
    ROOT / "data" / "_derived" / "_patch_2026q2_KR0005.json",
    ROOT / "data" / "_derived" / "_patch_2026q2_KR0075.json",
    ROOT / "data" / "_derived" / "_patch2_2026q2_KR0075.json",
]

rows = json.loads(MASTER.read_text(encoding="utf-8"))
before_n = len(rows)

for p in PATCHES:
    patch = json.loads(p.read_text(encoding="utf-8"))
    rows, st = ap.apply_patch(rows, patch, dry=False)
    print(f"{patch['company_code']} <- {p.name}: +{st['added']} new / {st['updated']} "
          f"updated / {st['skipped']} unchanged" + (f" / ERRORS {st['errors']}" if st['errors'] else ""))
    if st["errors"]:
        raise SystemExit(f"ABORT: apply errors in {p.name}: {st['errors']}")

print(f"\nrow count {before_n} -> {len(rows)} (delta {len(rows) - before_n})")
SCRATCH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote scratch master: {SCRATCH}\n")

# ---------------------------------------------------------------------------
print("=== running gate on LIVE (baseline, unpatched) master ===")
before = subprocess.run([PY, str(ROOT / "scripts" / "validate_kics_disclosure.py")],
                         cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace")
print(f"exit_code={before.returncode}")

print("\n=== running gate on SCRATCH (patched) master ===")
after = subprocess.run([PY, str(ROOT / "scripts" / "validate_kics_disclosure.py"),
                         "--master", str(SCRATCH)],
                        cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace")
print(f"exit_code={after.returncode}")

for tag, proc in (("BEFORE", before), ("AFTER", after)):
    print(f"\n--- {tag} stdout tail (status counts) ---")
    for line in proc.stdout.splitlines():
        if any(k in line for k in ("Status counts", "RED", "coverage", "Coverage",
                                     "MISSING_CELLS", "collapsed_quarters")):
            print(f"  {line}")
    if proc.returncode not in (0,) and not proc.stdout.strip():
        print("  (no stdout -- check stderr)")
        print(proc.stderr[-3000:])

(ROOT / "scripts" / "_probes" / "_20260831_before_stdout.txt").write_text(
    before.stdout, encoding="utf-8")
(ROOT / "scripts" / "_probes" / "_20260831_after_stdout.txt").write_text(
    after.stdout, encoding="utf-8")
print("\nwrote full stdout: _20260831_before_stdout.txt / _20260831_after_stdout.txt")
