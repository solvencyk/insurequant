# -*- coding: utf-8 -*-
"""Negative controls for kr0003_verify.py: each mutation MUST make the verifier report problems (exit code 1 or 2)."""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
plan = json.loads((HERE / "e23_plan_lotte.json").read_text(encoding="utf-8"))


def write_plan(name, fn):
    p = json.loads(json.dumps(plan))
    fn(p)
    (HERE / name).write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")


def m_line(p):                      # point item 17 to the neighbouring (current-year) cell
    c = next(c for c in p["buckets"][0]["cells"] if c["item"] == 17)
    c["parts"][0]["line"] -= 4


def m_value(p):                     # off-by-one in a planned value
    c = next(c for c in p["buckets"][0]["cells"] if c["item"] == 24)
    c["new"] += 1.0


def m_csm(p):                       # CSM item 5 stored one tick away
    c = next(c for c in p["csm_buckets"][0]["cells"] if c["item"] == 5)
    c["new"] = -1859.1


def m_unit(p):                      # wrong unit label of one part
    c = next(c for c in p["buckets"][0]["cells"] if c["item"] == 20)
    c["parts"][0]["unit"] = "백만원"


write_plan("_mut_plan_line.json", m_line)
write_plan("_mut_plan_value.json", m_value)
write_plan("_mut_plan_csm.json", m_csm)
write_plan("_mut_plan_unit.json", m_unit)
runs = [("col", dict(KR0003_MUTATE="col")), ("tbl", dict(KR0003_MUTATE="tbl")), ("plan_line", dict(KR0003_PLAN="_mut_plan_line.json")),
        ("plan_value", dict(KR0003_PLAN="_mut_plan_value.json")), ("plan_csm", dict(KR0003_PLAN="_mut_plan_csm.json")), ("plan_unit", dict(KR0003_PLAN="_mut_plan_unit.json"))]
out = []
allok = True
for tag, env in runs:
    e = dict(os.environ, KR0003_OUTTAG="mut_" + tag, PYTHONIOENCODING="utf-8", **env)
    p = subprocess.run([PY, str(HERE / "kr0003_verify.py")], cwd=str(HERE), env=e, capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    txt = (p.stdout or "") + (p.stderr or "")
    nprob = txt.count("!! PROBLEM")
    crashed = p.returncode == 2
    detected = p.returncode != 0
    allok &= detected
    out.append(f"mutation {tag:11s}: exit {p.returncode}  PROBLEM lines {nprob}  crashed {crashed}  -> {'DETECTED' if detected else 'MISSED'}")
    print(out[-1])
print("ALL MUTATIONS DETECTED" if allok else "SOME MUTATION MISSED")
(HERE / "kr0003_verify_mutation.txt").write_text("\n".join(out + ["ALL MUTATIONS DETECTED" if allok else "SOME MUTATION MISSED"]) + "\n", encoding="utf-8", newline="\n")
for f in HERE.glob("_mut_plan_*.json"):
    f.unlink()
sys.exit(0 if allok else 1)
