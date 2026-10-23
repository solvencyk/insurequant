# -*- coding: utf-8 -*-
"""pass3 s01 (read-only): ledger entries + gold entries for the three companies of ticket 20261024T0600Z"""
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
led = json.load(open(f"{ROOT}/data/_gold/gold_overlay_ledger.json", encoding="utf-8"))
ent = led.get("entries", {})
print("ledger keys:", [k for k in led if k != "entries"], "entries:", len(ent))
for k, v in sorted(ent.items()):
    if any(c in k for c in ("KR0070", "KR0087", "KR0032")):
        print(k, "->", json.dumps(v, ensure_ascii=False)[:300])
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
print("gold keys:", list(gold.keys()))
for c in ("KR0070", "KR0087", "KR0032"):
    n = [e for e in gold["set"] if e["원보험사코드"] == c]
    print(c, "set entries", len(n))
    for e in sorted(n, key=lambda e: (e["공시분기"], e["항목번호"])):
        if (c == "KR0070" and e["공시분기"] >= "2024.4Q") or (c == "KR0087" and "2024.1Q" <= e["공시분기"] <= "2025.2Q") or (c == "KR0032" and e["공시분기"] <= "2023.4Q"):
            print("   ", e["공시분기"], e["항목번호"], e["값"], "was", e.get("was"), "|", (e.get("note") or "")[:90].replace("\n", " "))
print("null_dangi:", [c for c in gold["null_dangi"]["cells"] if c[0] in ("KR0070", "KR0087", "KR0032")])
print("set_dangi:", [c[:4] for c in gold["set_dangi"]["cells"] if c[0] in ("KR0070", "KR0087", "KR0032")])
