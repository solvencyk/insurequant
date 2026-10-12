# -*- coding: utf-8 -*-
"""a6: peek at the published utilization JSONs (the audit TARGET; read-only)."""
import json

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
t1 = json.load(open(ROOT + "/kics_tier1_utilization.json", encoding="utf-8"))
t2 = json.load(open(ROOT + "/kics_tier2_utilization.json", encoding="utf-8"))
print("t1 keys", list(t1.keys()), "n", len(t1["results"]))
print("t2 keys", list(t2.keys()), "n", len(t2["results"]))
print("t1 row keys", list(t1["results"][0].keys()))
print("t2 row keys", list(t2["results"][0].keys()))
print()
print("--- tier1 rows: code name pct strict_pct scr limit15 limit10 legacy new_basic excl_t2 binding unconfirmed no_sec ---")
for r in t1["results"]:
    print(r["code"], r["company"][:8], "pct=", r.get("utilization_pct"), "strict=", r.get("utilization_pct_strict"),
          "scr=", r.get("scr_eok"), "legacy=", r.get("tier1_legacy_eok"), "new=", r.get("tier1_basic_new_eok"),
          "exclT2=", r.get("tier1_excluded_tier2_type_eok"), "bind=", r.get("binding_leg"),
          "unconf=", r.get("type_unconfirmed"), "nosec=", r.get("no_capital_securities"), "q=", r.get("quality_flag"))
print()
print("--- tier2 rows: code name pct num limit rule scope reason nosec q ---")
for r in t2["results"]:
    print(r["code"], r["company"][:8], "pct=", r.get("utilization_pct"), "num=", r.get("numerator_eok"),
          "lim=", r.get("tier2_limit_eok"), "rule=", r.get("rule"), "scope=", r.get("item47_scope"),
          "flags=", r.get("rule_flags"), "reason=", r.get("reason"), "q=", r.get("quality_flag"), "src=", r.get("numerator_source"))
