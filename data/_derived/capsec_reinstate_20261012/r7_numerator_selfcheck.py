# -*- coding: utf-8 -*-
"""47사 분자 자기검산 (owner 정정 2026-10-12): tier2 분자 = 항목 47(적용후, R규칙 정규화) - 항목 49 - 항목 53/54,
tier1 분자 = 항목 6 기반(기발행 53 + 기본자본형 신규 = 항목 6 - 기발행 - 보완자본형). 그 밖에 더하거나 빼는 것 없음."""
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")
import capital_utilization_rules as R
recs = json.loads(Path("kics_disclosure.json").read_text(encoding="utf-8"))
pre, post, names = R.load_disclosure(recs, "2026.2Q")
comp = R.compute_quarter(recs, "2026.2Q", R.load_ledger(), R.load_registry())
bad = []
for code, c in comp.items():
    p, q = pre[code], post.get(code, {})
    t2 = c["t2"]
    i47 = (q.get(47) if q.get(47) is not None else p.get(47))
    i49 = p.get(49) or 0.0; i53 = p.get(53) or 0.0; i54 = (p.get(54) or 0.0)
    rule, num = t2["rule"], t2["numerator"]
    if rule == "NA":
        exp = None
    elif rule == "R0":
        exp = 0.0
    else:
        gross = t2["gross_printing"]
        base = (i47 - i49) if gross and (R.close(i47, p.get(3)) or R.close(i47, p.get(47))) else i47
        leg_sub = 0.0 if t2["legacy_row_is_new_debt"] else i54
        if rule == "R3":
            base = ((p.get(47) - i49) if gross else p.get(47)) - i53 - leg_sub
        elif rule == "R4":
            base = base - leg_sub
        exp = max(0.0, base)
    if (exp is None) != (num is None) or (exp is not None and abs(exp - num) > 0.011):
        bad.append((code, "t2", rule, exp, num))
    t1 = c["t1"]
    if t1:
        reg = (R.load_registry()["companies"].get(code) or {}).get("securities") or []
        t2amt = sum(s["amount_eok"] for s in reg if s["type"] == "tier2")
        sec = max(p.get(6) or 0.0, 0.0)
        # 항목 6 = 기발행 + 기본자본형 신규 + 보완자본형(제외분) 이 닫힌다
        if abs(t1["securities_eok"] - (t1["legacy_eok"] + t1["basic_new_eok"] + t1["excluded_tier2_type_eok"])) > 0.011:
            bad.append((code, "t1 identity", t1["securities_eok"], t1["legacy_eok"], t1["basic_new_eok"], t1["excluded_tier2_type_eok"]))
        if abs(t1["securities_eok"] - sec) > 0.011:
            bad.append((code, "t1 item6", t1["securities_eok"], sec))
print("companies", len(comp), "mismatches", len(bad))
for b in bad: print(b)
