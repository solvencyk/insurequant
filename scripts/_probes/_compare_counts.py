# -*- coding: utf-8 -*-
"""Run the gate on BOTH the live master and the patched scratch copy, and diff every
summary-count line (mmult, post_transition_parent_census TRAILING/SANDWICHED, other_capital
children-sum, coverage census, parent-zero-child, etc.) side by side."""
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


def run(master_arg):
    args = [PY, str(ROOT / "scripts" / "validate_kics_disclosure.py")]
    if master_arg:
        args += ["--master", str(master_arg)]
    proc = subprocess.run(args, cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout


rc_before, out_before = run(None)
rc_after, out_after = run(SCRATCH)

KEY_MARKERS = [
    "Status counts", "적용후 mmult 불일치", "적용후 mmult 미판정",
    "TRAILING", "SANDWICHED", "적용후 부모결측",
    "item23", "item24", "item25", "item26",
    "기타 요구자본", "Coverage census", "Parent-zero",
    "선택경과조치 적용후", "item12=item1",
]


def extract(out):
    lines = []
    for line in out.splitlines():
        if any(k in line for k in KEY_MARKERS):
            lines.append(line.strip())
    return lines


before_lines = extract(out_before)
after_lines = extract(out_after)

print(f"BEFORE exit={rc_before}  AFTER exit={rc_after}\n")
print("=== BEFORE (live master) relevant lines ===")
for line in before_lines:
    print(" ", line)
print("\n=== AFTER (patched scratch) relevant lines ===")
for line in after_lines:
    print(" ", line)
