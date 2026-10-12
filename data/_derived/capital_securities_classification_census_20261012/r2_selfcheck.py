"""r2_selfcheck.py (parser-kics, ticket 20261012T2000Z, round 2) -- internal consistency of the round-2 outputs.  READ ONLY.

Most checks re-derive a number from a source that r2_apply.py did not use for the same number (round-1 json, the registry json, the raw rules of the ticket),
so they are not identities of r2_apply.py with itself.
Run (after r2_apply.py): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/r2_selfcheck.py
Exit code 0 = all FAIL-level checks passed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from c6_evidence import EV as EV1  # noqa: E402
from r2_evidence import EV2, SEARCH_LOG  # noqa: E402


def rcsv(name):
    with open(HERE / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


r1 = json.loads((HERE / "census_securities.json").read_text(encoding="utf-8"))
r2 = json.loads((HERE / "census_securities_r2.json").read_text(encoding="utf-8"))
final = rcsv("census_securities_final.csv")
mm = rcsv("census_mismatch_r2.csv")
newc = rcsv("census_newly_confirmed_r2.csv")
reg = json.loads((REPO / "data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))
ev1csv = {r["id"] for r in rcsv("census_evidence.csv")}

results = []


def check(name, ok, detail="", level="FAIL"):
    results.append((name, ok, detail, level))
    print(f"[{'PASS' if ok else level}] {name}" + (f" - {detail}" if detail else ""))


# 1. partition by an independent re-derivation of the owner rules
def indep_scope(r):
    if r["kind"] == "historical (redeemed)":
        return "excluded_owner"
    if r["kind"] == "bond" and r["outstanding_eok"] is not None and r["outstanding_eok"] <= 0:
        return "excluded_owner"
    if "2026 상반기 중 상환" in r["status"]:
        return "excluded_owner"
    if r["kind"].startswith("non-bond") or r["kind"] == "subsidiary instrument":
        return "item6_other"
    return "in_scope"


ok = len(r1) == len(r2) == 149
bad = [i for i, (a, b) in enumerate(zip(r1, r2)) if indep_scope(a) != b["scope"]]
cnt = Counter(b["scope"] for b in r2)
check("1 scope partition = independent re-derivation (149 rows; in_scope / excluded_owner / item6_other)", ok and not bad and cnt == Counter({"in_scope": 124, "excluded_owner": 17, "item6_other": 8}),
      f"counts {dict(cnt)}; rows that differ {bad}")

INS = [r for r in r2 if r["scope"] == "in_scope"]
HYB = [r for r in INS if r["tier"] == "hybrid"]
SUB = [r for r in INS if r["tier"] == "subordinated"]
EXC = [r for r in r2 if r["scope"] == "excluded_owner"]
OTH = [r for r in r2 if r["scope"] == "item6_other"]

# 2. round-1 hybrid arithmetic: 46 -> 43
h1 = [r for r in r1 if r["kind"] == "bond" and r["tier"] == "hybrid"]
red = [r for r in h1 if r["outstanding_eok"] == 0]
check("2 hybrid count: round 1 bond hybrids 46 - 4 zero-balance + 1 promoted (registry-only) = 43; round-1 grades 40/6/0",
      len(h1) == 46 and len(red) == 4 and len(HYB) == 43 and Counter(r["grade"] for r in h1) == Counter({"a": 40, "b": 6}),
      f"r1 {len(h1)} zero-balance {len(red)} r2 {len(HYB)}")

# 3. classification invariants (regulation: issue date vs 2023-01-01)
bad = [r["name"] for r in HYB if ((r["issue_date"] or "9999") < "2023-01-01") != (r["census_type"] == "legacy_tfi")]
check("3 every in-scope hybrid issued before 2023-01-01 is legacy_tfi and none after is", not bad, str(bad))
bad = [r["name"] for r in SUB if not str(r["census_type"]).startswith("tier2")]
bad += [r["name"] for r in SUB if r["issue_date"] and ((r["issue_date"] < "2023-01-01") != (r["census_type"] == "tier2_legacy(TFI (2))"))]
check("4 every in-scope subordinated bond is tier2 (tier2_legacy iff issued before 2023-01-01)", not bad, str(bad))

# 4. nothing unclassified
unc = [r["name"] for r in INS if r["census_type"] not in ("legacy_tfi", "tier1", "tier2", "tier2_legacy(TFI (2))") or r["grade"] != "a"]
check("5 no in-scope hybrid / subordinated bond is unclassified or below grade a", not unc, str(unc))

# 5. owner decisions as an oracle typed from the ticket text (not from r2_apply's overlay)
exp = {("KR0011", "2025-09-01"): "tier1", ("KR0011", "2025-09-25"): "tier1", ("KR0011", "2026-02-11"): "tier1", ("KR0011", "2026-06-09"): "tier1", ("KR0011", "2026-06-29"): "tier1",
       ("KR0050", "2024-05-14"): "tier2", ("KR0050", "2026-06-29"): "tier2", ("KR0097", "2023-03-31"): "tier2"}
got = {(r["code"], r["issue_date"]): r["census_type"] for r in HYB if (r["code"], r["issue_date"]) in exp}
check("6 owner decisions: DB Non-life 5 = tier1, Hana Non-life 2 = tier2, Hana Life = tier2", got == exp, f"got {got}")
# every other post-2022 hybrid keeps its round-1 type
r1t = {(r["code"], r["issue_date"], r["face_eok"]): r["census_type"] for r in r1}
chg = [(r["code"], r["issue_date"]) for r in HYB if (r["code"], r["issue_date"]) not in exp and r1t.get((r["code"], r["issue_date"], r["face_eok"])) not in (None, r["census_type"])]
check("7 no hybrid outside the owner-decided 8 changed type from round 1", not chg, str(chg))
sub_changed = [r["name"] for r in SUB if r["r1_census_type"] != r["census_type"] and r["r1_grade"] != "c"]
check("8 subordinated bonds changed only where round 1 had an exception candidate (grade c): 4 rows", not sub_changed and sum(1 for r in SUB if r["r1_grade"] == "c") == 4,
      f"{sub_changed}")

# 6. registry comparison re-derived from the registry json by issue date.
# The registry moved while round 2 ran (publishing commit ef62969, 2026-10-12 19:46): the AT-TICKET list is checked against the registry file of the commit before it,
# the NOW list against the working-tree file.
def reg_type(regdoc, code, d):
    for s in regdoc["companies"].get(code, {}).get("securities", []):
        sd = s.get("issue_date")
        if sd == d:
            return s
        if sd and re.fullmatch(r"\d{4}\.\dQ", sd) and d[:4] == sd[:4] and (int(d[5:7]) - 1) // 3 + 1 == int(sd[5]):
            return s
    return None


REG_PATH = "data/bonds/capital_tier_registry.json"
try:
    old_txt = subprocess.run(["git", "show", f"ef62969~1:{REG_PATH}"], cwd=REPO, capture_output=True, timeout=120).stdout.decode("utf-8")
    reg_old = json.loads(old_txt)
except Exception as e:  # noqa: BLE001
    reg_old = None
    print("   (git show of the registry before ef62969 failed:", repr(e), ")")
got_mm = {(r["code"], r["issue_date"]) for r in mm}
if reg_old is not None:
    exp_mm = {(r["code"], r["issue_date"]) for r in HYB if (reg_type(reg_old, r["code"], r["issue_date"]) or {}).get("type") not in (None, r["census_type"])}
    check("9 at-ticket mismatch list = independent comparison against the registry file before ef62969 (git show ef62969~1)", exp_mm == got_mm and len(got_mm) == 6,
          f"expected {sorted(exp_mm)} got {sorted(got_mm)}")
else:
    check("9 at-ticket mismatch list", False, "registry before ef62969 not readable", level="WARN")
now_typ = {(r["code"], r["issue_date"]) for r in HYB if (reg_type(reg, r["code"], r["issue_date"]) or {}).get("type") not in (None, r["census_type"])}
now_iss = {(r["code"], r["issue_date"]) for r in HYB if (reg_type(reg, r["code"], r["issue_date"]) or {}).get("issuer_type") not in (None, r["census_type"])}
check("10 now: registry file in the working tree agrees on type for every in-scope hybrid; issuer_type differs only for Kyobo 2024-11-12 and Hana Life 제1회",
      not now_typ and now_iss == {("KR0073", "2024-11-12"), ("KR0097", "2023-03-31")}, f"type diffs {sorted(now_typ)} issuer_type diffs {sorted(now_iss)}", level="WARN")
check("10b final.csv vs_registry (at ticket) DIFFERENT rows = mismatch csv; vs_registry_now agrees with the check above",
      {(r["code"], r["issue_date"]) for r in final if r["vs_registry"] == "DIFFERENT"} == got_mm and {(r["code"], r["issue_date"]) for r in final if r["vs_registry_now"] == "DIFFERENT"} == now_typ)

# 7. final csv
keys = [(r["code"], r["issue_date"], r["face_eok"]) for r in final]
check("11 final.csv = one line per in-scope hybrid (43), unique, grade a, evidence present (<= 420 chars)",
      len(final) == 43 == len(set(keys)) and all(r["grade"] == "a" and r["evidence"].strip() and len(r["evidence"]) <= 420 for r in final),
      f"rows {len(final)} unique {len(set(keys))} longest {max(len(r['evidence']) for r in final)}")
tcount = Counter(r["type"] for r in final)
check("12 final.csv type counts = legacy_tfi 21 / tier1 5 / tier2 17", tcount == Counter({"legacy_tfi": 21, "tier1": 5, "tier2": 17}), str(dict(tcount)))
check("13 no excluded / item6 row appears in final.csv", not ({(r["code"], r["issue_date"]) for r in final} & {(r["code"], r["issue_date"]) for r in EXC + OTH if r["tier"] == "hybrid" and r["kind"] == "bond"}))

# 8. evidence ids
known = set(EV1) | set(EV2) | ev1csv
miss = sorted({i for r in r2 for i in (r.get("ev") or "").split(";") if i and i not in known})
check("14 every evidence id cited in the r2 table exists in the round-1 or round-2 evidence tables", not miss, str(miss))

# 9. search log
nums = [n for n, *_ in SEARCH_LOG]
refs = {int(x) for r in newc for x in re.findall(r"#(\d+)", r["search_numbers"])}
check("15 search log numbers are 1..N without gaps and every number cited in newly_confirmed exists", nums == list(range(1, len(nums) + 1)) and max(refs) <= len(nums), f"N={len(nums)} cited max {max(refs)}")

# 10. item 6 completeness
txt = (HERE / "census_item6_check_r2.txt").read_text(encoding="utf-8")
check("16 K-ICS item 6 (2026.2Q) is explained by the in-scope hybrid list + item-6 sheet for every company (tolerance max(25, 3%))", "설명 안 되는 잔차(허용 = max(25, 3%)): 없음" in txt)

# 11. round-1 files and registry untouched
paths = ["census_securities.csv", "census_securities.json", "census_mismatch.csv", "census_summary.txt", "census_evidence.csv"]
try:
    out = subprocess.run(["git", "status", "--porcelain", "--"] + [f"data/_derived/capital_securities_classification_census_20261012/{p}" for p in paths] + ["data/bonds/capital_tier_registry.json"],
                         cwd=REPO, capture_output=True, text=True, timeout=120).stdout.strip()
    check("17 round-1 census files and the registry have no uncommitted change (git status --porcelain empty; the registry itself was changed by publishing commit ef62969, not by round 2)", out == "", out)
except Exception as e:  # noqa: BLE001
    check("17 git status", False, repr(e), level="WARN")

# 12. input fingerprints
inp = json.loads((HERE / "r2_inputs.json").read_text(encoding="utf-8"))
cur = {"census_securities.json (round 1)": HERE / "census_securities.json", "kics_disclosure.json": REPO / "kics_disclosure.json",
       "data/bonds/capital_tier_registry.json": REPO / "data/bonds/capital_tier_registry.json",
       "data/bonds/capital_securities_fy2026h1.json (cited in the exclusion reason)": REPO / "data/bonds/capital_securities_fy2026h1.json"}
chg = [k for k, p in cur.items() if hashlib.sha256(p.read_bytes()).hexdigest() != inp.get(k)]
check("18 input files unchanged since r2_apply.py ran (sha256)", not chg, str(chg), level="WARN")

# 13. encoding invariant: no BOM in the python files / text outputs written in round 2
boms = [p.name for p in list(HERE.glob("r2_*.py")) + [HERE / "census_summary_r2.txt", HERE / "census_item6_check_r2.txt", HERE / "r2_search_log.txt", HERE / "r2_inputs.json"] if p.read_bytes()[:3] == b"\xef\xbb\xbf"]
check("19 no UTF-8 BOM in the round-2 .py / .txt / .json files", not boms, str(boms))

fails = [r for r in results if not r[1] and r[3] == "FAIL"]
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed" + ("" if not fails else "  FAILED: " + ", ".join(r[0].split(' ')[0] for r in fails)))
sys.exit(1 if fails else 0)
