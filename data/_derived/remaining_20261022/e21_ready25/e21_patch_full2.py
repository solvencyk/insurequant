"""one-off patcher #2 for e21_plan_full.py: Q4 cumulative that differs from its own latest comparative but is NOT adopted -> keep the single quarter blank (null_dangi)"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_plan_full.py"
s = open(p, encoding="utf-8").read()
old = '''                            rec.update(cls="q4_changed_but_not_adopted", proposal="REVIEW")'''
new = '''                            rec.update(cls="q4_changed_but_not_adopted", proposal="null_dangi")
                            if not rec["existing_null"]:
                                null_add.append([code, qq, i])'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched full2")
