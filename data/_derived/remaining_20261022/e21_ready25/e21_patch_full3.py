"""one-off patcher #3 for e21_plan_full.py: keep the Q3 comparative evidence (lines) in the seam records"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_plan_full.py"
s = open(p, encoding="utf-8").read()
old = '''        comp = sum(p.sign * p.val_mn for p in v[i]["parts"])
        old = master.get((code, i, q))
        if old is None:
            return False, "master empty"
        band = 2e-5 if st.unit == "원" else 1.5
        return abs(comp - old) > band, f"comparative {round(comp, 6)} vs master {old}"'''
new = '''        comp = sum(p.sign * p.val_mn for p in v[i]["parts"])
        old = master.get((code, i, q))
        if old is None:
            return False, "master empty"
        band = 2e-5 if st.unit == "원" else 1.5
        EVID[(code, q, i)] = dict(file=st.rel, unit=st.unit, parts=[P.pdict(p, st.unit) for p in v[i]["parts"]], comparative=round(comp, 6), master=old)
        return abs(comp - old) > band, f"comparative {round(comp, 6)} vs master {old}"'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = '''    null_add, null_remove, set_add, set_remove = [], [], [], []'''
new2 = '''    EVID = {}
    null_add, null_remove, set_add, set_remove = [], [], [], []'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
old3 = '''                rec["q3_restated"] = rs
                rec["q3_evidence"] = why + ("" if i in TIER1 else f" | item-1 check: {why1}")'''
new3 = '''                rec["q3_restated"] = rs
                rec["q3_evidence"] = why + ("" if i in TIER1 else f" | item-1 check: {why1}")
                ek = (code, pq, i if i in TIER1 else 1)
                if ek in EVID:
                    rec["q3_comparative"] = EVID[ek]'''
assert s.count(old3) == 1
s = s.replace(old3, new3)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched full3")
