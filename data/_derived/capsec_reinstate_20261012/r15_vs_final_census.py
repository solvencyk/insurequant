# -*- coding: utf-8 -*-
"""census 최종본 대 등재부(현재 HEAD) 대조. 읽기 전용."""
import csv, json, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open("data/_derived/capital_securities_classification_census_20261012/census_securities_final.csv", encoding="utf-8-sig")))
reg = json.load(open("data/bonds/capital_tier_registry.json", encoding="utf-8"))["companies"]
print("rows", len(rows), "vs_registry:", {k: sum(1 for r in rows if r["vs_registry"] == k) for k in sorted({r["vs_registry"] for r in rows})})
for r in rows:
    secs = (reg.get(r["code"]) or {}).get("securities") or []
    hit = [s for s in secs if s.get("issue_date") == r["issue_date"]]
    mine = (hit[0]["type"] if hit else None)
    issuer = (hit[0].get("issuer_type") if hit else None)
    if r["vs_registry"] != "same" or (mine and mine != r["type"]):
        print(r["code"], r["company"][:6], r["issue_date"], "face", r["face_eok"], "| final", r["type"], r["grade"], "| 등재부 지금", mine, issuer, "| vs_registry", r["vs_registry"])
        print("    ", r["evidence"][:240])
