# -*- coding: utf-8 -*-
import json
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/")
import audit_io
rev = audit_io.resolved_rev()
rows = json.load(open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/h1_tier2_recompute_47_%s.json" % rev, encoding="utf-8"))
print("scope differs:")
for x in rows:
    if x["scope_mine"] != x["scope_pub"] and x["scope_mine"] != "-":
        print("  ", x["code"], x["name"], "mine", x["scope_mine"], "pub", x["scope_pub"], "rule_pub", x["rule_pub"], "N2", x["N2_mine"], x["N2_pub"])
print()
print("code name | rule_pub scope | N2 pub | pct pub | ledger h/s | printed 53/54 | variants (date,min,haircut)")
for x in rows:
    print(x["code"], x["name"][:8], "|", x["rule_pub"], x["scope_pub"], "|", x["N2_pub"], "|", x["pct_pub"], "|", x["ledger_hybrid_pub"], "/", x["ledger_sub_pub"], "|", x["printed53_pub"], "/", x["printed54_pub"], "|", x["pct_variant_date"], x["pct_variant_min"], x["pct_variant_haircut"], "|", x["pastcall_excluded"][:80])
