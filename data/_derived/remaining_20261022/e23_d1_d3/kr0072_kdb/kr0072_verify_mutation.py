# -*- coding: utf-8 -*-
"""Mutation test of kr0072_verify.py: each deliberate defect must make the verifier fail (exit code 1).  The verifier is run as a subprocess (stdin /dev/null) with KR0072_MUTATE set.
col  = read the 2024 (current-year) column instead of the 2023 comparative column     line = shift one cited physical line by +1 (PL cell 2023.1Q i1 and CSM 2023.1Q i1)
tbl  = take the 당기 CSM roll-forward table instead of the 전기 one                    val  = alter one planned value (PL 2023.2Q i20 +1, CSM 2023.3Q i6 +0.1)
unit = treat the 2023.1Q CSM table unit as wrong"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
lines = []
allcaught = True
for m in ("", "col", "line", "tbl", "val", "unit"):
    env = dict(os.environ, KR0072_MUTATE=m, KR0072_OUTTAG=("mut_" + m) if m else "", PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(HERE / "kr0072_verify.py")], cwd=str(HERE), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    tag = ("_mut_" + m) if m else "_"
    jf = HERE / (f"kr0072_verify_mut_{m}.json" if m else "kr0072_verify.json")
    n = None
    if jf.exists():
        n = len(json.loads(jf.read_text(encoding="utf-8")).get("problems", []))
    caught = (p.returncode == 1) if m else (p.returncode == 0)
    allcaught = allcaught and caught
    lines.append(f"mutation {m or '(none = baseline)'}: exit {p.returncode}, problems {n} -> {'detected' if (m and caught) else ('baseline clean' if caught else 'NOT DETECTED / baseline failing')}")
    print(lines[-1])
lines.append("ALL MUTATIONS DETECTED, baseline clean" if allcaught else "SOME MUTATION NOT DETECTED")
print(lines[-1])
(HERE / "kr0072_verify_mutation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
sys.exit(0 if allcaught else 1)
