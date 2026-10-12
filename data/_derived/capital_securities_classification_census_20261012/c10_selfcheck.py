"""c10_selfcheck.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.  Internal consistency checks of the census outputs (run after c7 / c9 / c8).

  1. census_securities.csv: 149 rows (133 bond-list securities + 16 extra), grade in {a,b,c}, census_type in the known set, no empty basis
  2. every evidence id used in `ev` exists in census_evidence.csv
  3. every bond-list hybrid of the inventory appears exactly once (key = code, issue_date, face) and every subordinated bond too
  4. counts in census_summary.txt equal the recomputed counts
  5. tier2 / tier1 census assignment of every post-2022 hybrid is the one c9 tested (census_x_band_test.csv `census_assignment` has no '?')
  6. grade a rows carry a basis kind; grade b rows of post-2022 hybrids carry b_strength; mismatch rows (DIFFERENT / census-unknown) are all in census_mismatch.csv
Exit code 0 = all pass, 1 = at least one FAIL.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c10_selfcheck.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent


def rd(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8-sig")))


sec = rd("census_securities.csv")
evid = {r["id"] for r in rd("census_evidence.csv")}
mm = rd("census_mismatch.csv")
band = rd("census_x_band_test.csv")
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]
summary = (HERE / "census_summary.txt").read_text(encoding="utf-8")
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


bonds = [r for r in sec if r["kind"] == "bond"]
extras = [r for r in sec if r["kind"] != "bond"]
check(len(sec) == 149 and len(bonds) == 133 and len(extras) == 16, f"rows {len(sec)} = bonds {len(bonds)} + extras {len(extras)} (expected 149 = 133 + 16)")
check(all(r["grade"] in ("a", "b", "c") for r in sec), "every grade in {a,b,c}")
types = {"legacy_tfi", "tier1", "tier2", "tier2_legacy(TFI (2))", "tier2", "unknown"}
check(all(r["census_type"] in types for r in sec), "every census_type in the known set: " + ", ".join(sorted({r["census_type"] for r in sec})))
check(all(r["basis"].strip() for r in sec), "no empty basis")
missing = sorted({e for r in sec for e in r["ev"].split(";") if e and e not in evid})
check(not missing, f"every evidence id exists in census_evidence.csv (missing: {missing})")

key = lambda r: (r["code"], r["tier"], r["issue_date"], round(float(r["face_eok"] or 0), 2))  # noqa: E731
inv_keys = Counter((r["code"], r["tier"], r["issue_date"] or "", round(float(r["face_eok"] or 0), 2)) for r in inv)
sec_keys = Counter(key(r) for r in bonds)
check(inv_keys == sec_keys, f"bond rows == inventory rows (inventory {sum(inv_keys.values())}, census {sum(sec_keys.values())})")

cnt = Counter((("H" if r["tier"] == "hybrid" and r["kind"] == "bond" else "S" if r["tier"] == "subordinated" else "X"), r["grade"]) for r in sec)
h = {g: cnt[("H", g)] for g in "abc"}
s = {g: cnt[("S", g)] for g in "abc"}
x = {g: cnt[("X", g)] for g in "abc"}
tot = {g: h[g] + s[g] + x[g] for g in "abc"}
line = f"신종 채권 ⓐ {h['a']} / ⓑ {h['b']} / ⓒ {h['c']} | 후순위 ⓐ {s['a']} / ⓑ {s['b']} / ⓒ {s['c']} | 추가 발견 ⓐ {x['a']} / ⓑ {x['b']} / ⓒ {x['c']} | 합계 ⓐ {tot['a']} / ⓑ {tot['b']} / ⓒ {tot['c']}"
check(line in summary, "grade counts in census_summary.txt == recomputed: " + line)
check(sum(h.values()) == 46 and sum(s.values()) == 87, f"hybrid bonds {sum(h.values())} (46 expected), subordinated {sum(s.values())} (87 expected)")

post = [r for r in bonds if r["tier"] == "hybrid" and r["issue_date"] >= "2023-01-01"]
check(all("?" not in b["census_assignment"] for b in band), "c9 tested a definite assignment for every company (no '?' in census_assignment)")
check(all(r["census_type"] in ("tier1", "tier2") for r in post), f"every post-2022 hybrid is tier1 or tier2 ({len(post)} rows)")
check(all(r["a_basis"] for r in sec if r["grade"] == "a" and r["tier"] == "hybrid"), "every grade-a hybrid names its a_basis")
check(all(r["b_strength"] for r in post if r["grade"] == "b"), "every grade-b post-2022 hybrid carries b_strength")
want = {(r["code"], r["issue_date"], r["name"]) for r in sec if r["mismatch"] in ("DIFFERENT", "census-unknown")}
have = {(r["code"], r["issue_date"], r["name"]) for r in mm}
check(want == have, f"census_mismatch.csv lists exactly the DIFFERENT / census-unknown rows ({len(have)})")
check("등재부(capital_tier_registry.json) 대비: 같음 41건 · 다름 8건 · census 가 확정 못 함 0건 · 등재부 없음 13건" in summary, "registry comparison line of the summary (same 41 / different 8 / unknown 0 / absent 13)")
print()
print("ALL PASS" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
