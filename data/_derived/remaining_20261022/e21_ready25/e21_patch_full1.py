"""one-off patcher for e21_plan_full.py: (1) restated() checks KB LOB items directly; (2) Q4 comparative == master check for 'Q4 not adopted, Q3 adopted' buckets"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_plan_full.py"
s = open(p, encoding="utf-8").read()
old = '''        st = stmt(code, P.later_fy(q))
        v = R.read_vector(st, "prior", "cum")
        if i not in v or (i in (26, 27, 28, 29, 30) and v[i].get("absent")):'''
new = '''        if i not in TIER1:
            if code != "KR0010":
                return False, "LOB item of a non-KB company: not checked directly"
            r3 = T.kb_read(code, q)
            old = master.get((code, i, q))
            if i in r3 and old is not None:
                return abs(r3[i]["val"] - old) > 1.5, f"LOB note comparative {round(r3[i]['val'], 6)} vs master {old}"
            return False, "LOB item not read"
        st = stmt(code, P.later_fy(q))
        v = R.read_vector(st, "prior", "cum")
        if i not in v or (i in (26, 27, 28, 29, 30) and v[i].get("absent")):'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = '''                proxy = i if i in TIER1 else 1
                rs, why = restated(code, pq, proxy)
                rec["q3_restated"] = rs
                rec["q3_evidence"] = why + ("" if proxy == i else " (proxy item 1)")'''
new2 = '''                rs, why = restated(code, pq, i)
                rs1, why1 = (rs, why) if i in TIER1 else restated(code, pq, 1)
                rec["q3_restated"] = rs
                rec["q3_evidence"] = why + ("" if i in TIER1 else f" | item-1 check: {why1}")'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
old3 = '''                # Q4 not adopted, Q3 adopted: consistent iff the Q4 print is on the restated basis (comparative == master)
                rec.update(cls="q4_unchanged_q3_adopted", proposal="none")'''
new3 = '''                # Q4 not adopted, Q3 adopted: consistent iff the Q4 print is on the restated basis (the later filing's comparative == master)
                rec.update(cls="q4_unchanged_q3_adopted", proposal="none")
                if i in TIER1:
                    st4 = stmt(code, P.later_fy(qq))
                    v4 = R.read_vector(st4, "prior", "cum")
                    if not (i in (26, 27, 28, 29, 30) and v4[i].get("absent")):
                        comp4 = sum(p.sign * p.val_mn for p in v4[i]["parts"])
                        m4 = master.get((code, i, qq))
                        rec["q4_comp_vs_master"] = [round(comp4, 6), m4]
                        band4 = 2e-5 if st4.unit == "원" else 1.5
                        if m4 is not None and abs(comp4 - m4) > band4:
                            rec.update(cls="q4_changed_but_not_adopted", proposal="REVIEW")'''
assert s.count(old3) == 1
s = s.replace(old3, new3)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched full1")
