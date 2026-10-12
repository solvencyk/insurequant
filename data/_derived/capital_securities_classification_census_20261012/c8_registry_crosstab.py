"""c8_registry_crosstab.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.

Cross-tab of the 18 companies of data/bonds/capital_tier_registry.json against the census (census_securities.csv): per company, how many registry securities
are judged legacy_tfi / tier1 / tier2 / unconfirmed, and at which census grade (a / b / c) the census stands now.  The registry itself is never modified.
Bonds (the securities of the bond lists) and the extra rows (preferred shares, redeemed hybrids found only in the K-ICS series, unidentified remainders) are
counted separately: the headline "all bonds grade a" concerns the bonds only.
Output: census_registry_crosstab.txt (utf-8, LF).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c8_registry_crosstab.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
reg = json.loads((REPO / "data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))
rows = list(csv.DictReader(open(HERE / "census_securities.csv", encoding="utf-8-sig")))

bonds = defaultdict(list)
extras = defaultdict(list)
for r in rows:
    if r["code"] not in reg["companies"]:
        continue
    if r["tier"] == "hybrid" and r["kind"] == "bond":
        bonds[r["code"]].append(r)
    elif r["tier"] in ("hybrid", "hybrid-like"):
        extras[r["code"]].append(r)


def gr_text(rs):
    g = Counter(r["grade"] for r in rs)
    return f"ⓐ{g.get('a', 0)}/ⓑ{g.get('b', 0)}/ⓒ{g.get('c', 0)}"


out = ["등재부(capital_tier_registry.json) 18사 x census 확정도 (증권 단위; 등재부는 수정하지 않음)", ""]
n_with_bonds = n_all_a = n_diff = 0
for code, comp in reg["companies"].items():
    secs = comp.get("securities", [])
    rt = Counter(s["type"] + ("(미확정)" if s.get("type_unconfirmed") else "") for s in secs)
    bs, xs = bonds.get(code, []), extras.get(code, [])
    mm = [r for r in bs + xs if r["mismatch"] in ("DIFFERENT", "census-unknown")]
    n_diff += bool(mm)
    line = f"{code} {comp.get('company', code)}: 등재부 {len(secs)}건 (" + "·".join(f"{k} {v}" for k, v in sorted(rt.items())) + ")"
    if bs:
        n_with_bonds += 1
        all_a = all(r["grade"] == "a" for r in bs)
        n_all_a += all_a
        line += f" | 채권 {len(bs)}건 {gr_text(bs)}" + (" -> 채권 전부 ⓐ" if all_a else "")
    else:
        line += " | 채권 신종 없음"
    if xs:
        line += " | 채권 밖 " + ", ".join(f"{r['kind'].split(' ')[0]}({r['grade']})" for r in xs)
    if mm:
        line += f" | 등재부와 다름/미확정 {len(mm)}건"
    out.append(line)
out.append("")
out.append(f"신종 채권이 있는 {n_with_bonds}사 중 채권 전부 ⓐ: {n_all_a}사  |  등재부와 다르거나 census 가 확정 못 한 증권이 있는 사: {n_diff} / 18")
text = "\n".join(out) + "\n"
(HERE / "census_registry_crosstab.txt").write_text(text, encoding="utf-8", newline="\n")
print(text)
