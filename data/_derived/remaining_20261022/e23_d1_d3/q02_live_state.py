# -*- coding: utf-8 -*-
"""e23 step 0 (read-only): live master / gold state of the five D1-D3 companies (values, single-quarter values, gold set / null_dangi / set_dangi / ledger pins)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BUCKETS = {
    "KR0099": ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"],
    "KR0003": ["2023.3Q", "2023.4Q", "2024.1Q"],
    "KR0070": ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"],
    "KR0072": ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"],
    "KR0009": ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"],
}
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
for code, qs in BUCKETS.items():
    name = next((r["원수사명"] for r in pl if r["원보험사코드"] == code), "?")
    print("=" * 110)
    print(code, name)
    for q in qs:
        print(f"-- {q}")
        v = {i: PL.get((code, i, q)) for i in range(1, 33)}
        row = []
        for i in range(1, 33):
            r = v[i]
            if r is None:
                row.append(f"{i}:ROWABSENT")
                continue
            s = f"{i}:{r['값']}"
            d = r.get("값_당분기")
            if d != r["값"] and q[5] != "1":
                s += f"[q={d}]"
            if (code, i, q) in G:
                s += "*G"
            if (code, q, i) in ND:
                s += "*N"
            if (code, q, i) in SD:
                s += f"*S={SD[(code, q, i)][3]}"
            row.append(s)
        print("   PL " + " ".join(row))
        crow = []
        for i in range(1, 7):
            r = CS.get((code, i, q))
            if r is None:
                crow.append(f"{i}:ROWABSENT")
                continue
            s = f"{i}:{r['값']}[q={r.get('값_당분기')}]"
            if (code, i, q) in GC:
                s += "*G"
            crow.append(s)
        print("   CSM " + " ".join(crow))
    pk = [k for k in pins.get("entries", {}) if f"|{code}|" in k]
    print("   ledger pins:", pk)
