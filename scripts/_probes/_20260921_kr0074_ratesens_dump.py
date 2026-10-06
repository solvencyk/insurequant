# -*- coding: utf-8 -*-
"""Dump KR0074 2026.2Q rows from kics_rate_sensitivity.json verbatim, plus the
FSS transition-kind registry lookup and a quick RS5 cohort census for 2026.2Q."""
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"

rs = json.loads(open(ROOT + "kics_rate_sensitivity.json", encoding="utf-8").read())
disc = json.loads(open(ROOT + "kics_disclosure.json", encoding="utf-8").read())

print("=== kics_rate_sensitivity.json rows for KR0074 2026.2Q ===")
rows = [r for r in rs if r.get("원보험사코드") == "KR0074" and r.get("공시분기") == "2026.2Q"]
print(f"count={len(rows)}")
for r in rows:
    print(json.dumps(r, ensure_ascii=False))

print()
print("=== kics_disclosure.json item1/14/27 for KR0074 2026.2Q (RS2 anchor) ===")
for r in disc:
    if r.get("원보험사코드") == "KR0074" and r.get("공시분기") == "2026.2Q" and r.get("항목번호") in (1, 14, 27):
        print(json.dumps({k: r.get(k) for k in ["항목번호", "항목명", "값", "값_적용후"]}, ensure_ascii=False))

print()
print("=== all KR0074 quarters present in kics_rate_sensitivity.json ===")
kr0074_qs = sorted({r["공시분기"] for r in rs if r.get("원보험사코드") == "KR0074"})
print(kr0074_qs)
for q in kr0074_qs:
    phs = sorted({r["경과조치여부"] for r in rs if r.get("원보험사코드") == "KR0074" and r["공시분기"] == q})
    print(f"  {q}: phases={phs}")

print()
print("=== 2026.2Q full cohort census: kics_disclosure vs kics_rate_sensitivity ===")
disc_2026q2 = sorted({(r["원보험사코드"], r["원수사명"]) for r in disc if r.get("공시분기") == "2026.2Q"})
print(f"kics_disclosure 2026.2Q companies: {len(disc_2026q2)}")
rs_2026q2_codes = {r["원보험사코드"] for r in rs if r.get("공시분기") == "2026.2Q"}
print(f"kics_rate_sensitivity 2026.2Q distinct codes: {len(rs_2026q2_codes)}")
rs_2026q2_rows = [r for r in rs if r.get("공시분기") == "2026.2Q"]
print(f"kics_rate_sensitivity 2026.2Q row count: {len(rs_2026q2_rows)}")

missing_entirely = [(c, n) for c, n in disc_2026q2 if c not in rs_2026q2_codes]
print(f"missing entirely from rate_sensitivity (RS5-style): {len(missing_entirely)}")
for c, n in missing_entirely:
    print(f"  {c} {n}")
