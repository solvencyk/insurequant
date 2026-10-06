# -*- coding: utf-8 -*-
"""2026.2Q per-company row-count census for kics_rate_sensitivity.json against the
expected 6-row grid (적용전 x 3 measures + 적용후 x 3 measures)."""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rs = json.loads(open(ROOT + "kics_rate_sensitivity.json", encoding="utf-8").read())
disc = json.loads(open(ROOT + "kics_disclosure.json", encoding="utf-8").read())
diag = json.loads(open(ROOT + "data/_derived/kics_rate_sensitivity_diag.json", encoding="utf-8").read())

MEASURES = {"지급여력비율", "지급여력금액", "지급여력기준금액"}
PHASES = {"적용전", "적용후"}

q = "2026.2Q"
disc_names = {}
for r in disc:
    if r.get("공시분기") == q:
        disc_names[r["원보험사코드"]] = r["원수사명"]

rows_q = [r for r in rs if r.get("공시분기") == q]
print(f"total rows 2026.2Q = {len(rows_q)}, companies = {len(disc_names)} (39 expected -> 234 rows if all full)")
print()

by_code = {}
for r in rows_q:
    by_code.setdefault(r["원보험사코드"], []).append(r)

full, partial, absent = [], [], []
for code, name in sorted(disc_names.items()):
    recs = by_code.get(code, [])
    have = {(r["경과조치여부"], r["measure구분"]) for r in recs}
    expect = {(p, m) for p in PHASES for m in MEASURES}
    missing = sorted(expect - have)
    d = diag.get(f"{code}|{q}", "???")
    if not recs:
        absent.append((code, name, d))
    elif missing:
        partial.append((code, name, len(recs), missing, d))
    else:
        full.append((code, name))

print(f"=== FULL (6/6) : {len(full)} companies ===")
print()
print(f"=== PARTIAL (<6) : {len(partial)} companies ===")
for code, name, n, missing, d in partial:
    miss_str = ", ".join(f"{p}/{m}" for p, m in missing)
    print(f"  {code} {name:16s} rows={n} diag={d:20s} missing=[{miss_str}]")
print()
print(f"=== ABSENT ENTIRELY (0/6) : {len(absent)} companies ===")
for code, name, d in absent:
    print(f"  {code} {name:16s} diag={d}")

print()
print(f"row total check: full={len(full)*6} + partial={sum(n for _,_,n,_,_ in partial)} + absent=0 -> ", end="")
print(len(full)*6 + sum(n for _,_,n,_,_ in partial))
