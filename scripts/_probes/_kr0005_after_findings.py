# -*- coding: utf-8 -*-
"""Run the real gate against the SCRATCH (patched) copy, print KR0005 2026.2Q lines, and
print the full SUMMARY red/yellow counts (to confirm no other bucket's counts moved --
scratch copy only touches KR0005 2026.2Q rows so nothing else should change)."""
import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PY = r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch_KR0005.json"
)

proc = subprocess.run(
    [PY, str(ROOT / "scripts" / "validate_kics_disclosure.py"), "--master", str(SCRATCH)],
    cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace",
)
out = proc.stdout
print(f"exit_code={proc.returncode}")
print("\n--- lines mentioning KR0005 2026.2Q ---")
for line in out.splitlines():
    if "KR0005" in line and "2026.2Q" in line:
        print(line)

print("\n--- RED/SUMMARY lines ---")
for line in out.splitlines():
    if line.strip().startswith("RED") or "red=" in line.lower() or line.strip().startswith("SUMMARY") \
       or "by_status" in line or line.strip().startswith("TOTAL") or "gate exit" in line.lower():
        print(line)

print("\n--- stderr tail ---")
print(proc.stderr[-2000:] if proc.stderr else "(none)")

out_path = ROOT.parent / "scratch_gate_after_output.txt"
