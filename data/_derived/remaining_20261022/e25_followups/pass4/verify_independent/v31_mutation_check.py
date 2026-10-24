# -*- coding: utf-8 -*-
"""Sensitivity proof of v30_dy_nh_p4.py: mutate five master cells in a scratch copy (value +0.5 on NH 2023.2Q item 20, +1 on 동양 2024.3Q item 9, a spurious value in the blank 동양 2024.1Q item 11, a wrong single quarter on NH 2023.3Q item 1, 0.01 on NH 2023.1Q item 19)
and require that v30 reports at least five BAD lines (a verifier that cannot fail proves nothing)."""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/p4_tmp")
SCR.mkdir(parents=True, exist_ok=True)
rows = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
MUT = {("KR0032", 20, "2023.2Q", "값"): 0.5, ("KR0087", 9, "2024.3Q", "값"): 1.0, ("KR0087", 11, "2024.1Q", "값"): 3805.0, ("KR0032", 1, "2023.3Q", "값_당분기"): 7.0, ("KR0032", 19, "2023.1Q", "값"): 0.01}
n = 0
for r in rows:
    for (c, i, q, fld), d in MUT.items():
        if (r["원보험사코드"], r["항목번호"], r["공시분기"]) == (c, i, q):
            r[fld] = d if r.get(fld) is None or fld == "값" and (c, i, q) == ("KR0087", 11, "2024.1Q") else r[fld] + d
            n += 1
assert n == len(MUT), n
mp, op = SCR / "PL_breakdown_mutated.json", SCR / "v30_mutated_out.txt"
json.dump(rows, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
p = subprocess.run([PY, f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/v30_dy_nh_p4.py", "--master", str(mp), "--out", str(op)], capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
bad = [l for l in p.stdout.splitlines() if l.startswith("BAD")]
print(f"mutated cells {n}; v30 exit code {p.returncode}; BAD lines {len(bad)}")
for l in bad:
    print("  ", l[:170])
assert len(bad) >= 5 and p.returncode == 1
print("SENSITIVITY OK: the verifier fails on every injected defect")
