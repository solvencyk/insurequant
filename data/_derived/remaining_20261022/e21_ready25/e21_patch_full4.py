"""one-off patcher #4 for e21_plan_full.py: the stale KB 2024.4Q item 16 is a finding, not a pin"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_plan_full.py", encoding="utf-8").read()
old = '''                            rec.update(cls="q4_changed_but_not_adopted", proposal="null_dangi")
                            if not rec["existing_null"]:
                                null_add.append([code, qq, i])'''
new = '''                            rec.update(cls="q4_changed_but_not_adopted", proposal="none (finding)")
                            plan.setdefault("findings", []).append(dict(code=code, quarter=qq, item=i, kind="stale Q4 cumulative",
                                                                        text=f"master {m4} vs the {P.later_fy(qq)} comparative {round(comp4, 6)}; the cell is outside the READY set (not adopted); the single quarter is not pinned"))'''
assert s.count(old) == 1
s = s.replace(old, new)
open(H + "e21_plan_full.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched full4")
