# -*- coding: utf-8 -*-
"""Run the real gate (unmodified live master) and print every finding for KR0005 2026.2Q,
plus the mmult/identity/other-capital/post-transition-census axes (which live in
validate_kics_disclosure.py's main(), not the importable rule engine) filtered to this bucket."""
import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PY = r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"

proc = subprocess.run(
    [PY, str(ROOT / "scripts" / "validate_kics_disclosure.py")],
    cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace",
)
out = proc.stdout
print(f"exit_code={proc.returncode}")
for line in out.splitlines():
    if "KR0005" in line and "2026.2Q" in line:
        print(line)
print("\n--- stderr tail ---")
print(proc.stderr[-2000:] if proc.stderr else "(none)")
