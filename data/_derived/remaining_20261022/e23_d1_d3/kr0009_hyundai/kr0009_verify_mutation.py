# -*- coding: utf-8 -*-
"""mutation test of the independent verifier: each mutation must make kr0009_verify.py report problems (exit code 1)"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
out = []
ok_all = True
for mut in ("col", "line", "tbl", "val", "unit", "ir"):
    env = dict(os.environ, KR0009_MUTATE=mut, KR0009_OUTTAG="mut_" + mut, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(HERE / "kr0009_verify.py")], cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    n = sum(1 for l in p.stdout.splitlines() if "!! PROBLEM" in l)
    detected = p.returncode == 1 and n > 0
    ok_all = ok_all and detected
    line = f"mutation {mut:5s}: exit {p.returncode}, {n} problem lines -> {'DETECTED' if detected else 'NOT DETECTED'}"
    if p.returncode not in (0, 1):
        line += " | stderr: " + (p.stderr or "")[-300:].replace("\n", " ")
    out.append(line)
    print(line)
out.append("ALL MUTATIONS DETECTED" if ok_all else "SOME MUTATION NOT DETECTED")
print(out[-1])
(HERE / "kr0009_verify_mutation.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
