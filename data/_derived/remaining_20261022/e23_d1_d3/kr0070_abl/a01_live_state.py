# -*- coding: utf-8 -*-
"""ABL KR0070 step 0 (read-only): live master / gold state (values, single-quarter values, gold set / null_dangi / set_dangi / ledger pins) + a hash of the 7 apply-target files."""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CODE = "KR0070"
QS = ["2022.4Q", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
csm = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
pins = json.loads((ROOT / "data/_gold/gold_overlay_ledger.json").read_text(encoding="utf-8"))
PL = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl}
CS = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm}
G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
GC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in cgold["set"]}
ND = {tuple(x) for x in gold["null_dangi"]["cells"]}
SD = {(x[0], x[1], int(x[2])): x for x in gold["set_dangi"]["cells"]}
print("gold keys:", list(gold.keys()), "| set", len(gold["set"]), "null_dangi", len(ND), "set_dangi", len(SD), "| csm gold set", len(cgold["set"]), "| pins", len(pins.get("entries", {})))
name = next((r["원수사명"] for r in pl if r["원보험사코드"] == CODE), "?")
print(CODE, name)
for q in QS:
    print(f"-- {q}")
    row = []
    for i in range(1, 33):
        r = PL.get((CODE, i, q))
        if r is None:
            row.append(f"{i}:ROWABSENT")
            continue
        s = f"{i}:{r['값']}"
        d = r.get("값_당분기")
        if d != r["값"] and q[5] != "1":
            s += f"[q={d}]"
        if (CODE, i, q) in G:
            s += "*G"
        if (CODE, q, i) in ND:
            s += "*N"
        if (CODE, q, i) in SD:
            s += f"*S={SD[(CODE, q, i)][3]}"
        row.append(s)
    print("   PL " + " ".join(row))
    crow = []
    for i in range(1, 7):
        r = CS.get((CODE, i, q))
        if r is None:
            crow.append(f"{i}:ROWABSENT")
            continue
        s = f"{i}:{r['값']}[q={r.get('값_당분기')}]"
        if (CODE, i, q) in GC:
            s += "*G"
        crow.append(s)
    print("   CSM " + " ".join(crow))
print("ledger pins:", [k for k in pins.get("entries", {}) if f"|{CODE}|" in k])
print("gold PL entries for KR0070:")
for k, e in sorted(G.items(), key=lambda kv: (str(kv[0][2]), str(kv[0][1]))):
    if k[0] == CODE:
        print("  ", k, e["값"], "was", e.get("was"), "|", str(e.get("note"))[:100].replace("\n", " "))
print("gold CSM entries for KR0070:")
for k, e in sorted(GC.items(), key=lambda kv: (str(kv[0][2]), str(kv[0][1]))):
    if k[0] == CODE:
        print("  ", k, e["값"], "was", e.get("was"), "|", str(e.get("why") or e.get("note"))[:100].replace("\n", " "))
print("null_dangi KR0070:", sorted(x for x in ND if x[0] == CODE))
print("set_dangi KR0070:", sorted(x for x in SD if x[0] == CODE))
print("--- hashes")
for f in ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
          "data/_gold/gold_overlay_ledger.json", "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
          "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"]:
    print(hashlib.sha256((ROOT / f).read_bytes()).hexdigest(), f)
