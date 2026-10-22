"""one-off patcher #3 for e21_apply.py: allow pre-existing drift only where the new value equals the printed 3-month column; CSM provenance restricted to the touched blocks"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_apply.py", encoding="utf-8").read()
old = '''    if pre_drift_on_delta:
        errs.append(f"PL pre-existing live-vs-fresh-build drift on {len(pre_drift_on_delta)} delta cells (the apply would overwrite them): {pre_drift_on_delta[:6]}")'''
new = '''    allowed_pre = []
    p3m = {(s_["code"], s_["item"], s_["quarter"]): s_["printed_3m"]["value"] for s_ in PLAN["seams"] if s_.get("printed_3m")}
    for x in pre_drift_on_delta:
        k = x[0]
        # live differs from the fresh baseline build (pre-existing hand blank) and the apply would write the NEW derivation: accepted only when it equals the printed 3-month column
        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 1e-6 and x[5] == x[3]:
            allowed_pre.append((k, x[2], x[6], p3m[k]))
        else:
            errs.append(f"PL pre-existing live-vs-fresh-build drift on delta cell {x} (the apply would overwrite it)")'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''    have = {(e["원보험사코드"], e["공시분기"]) for e in new_cgold["set"]}
    for c in new["cells"]:'''
new = '''    have = {(e["code"], e["quarter"]) for e in C["csm_gold_new"] + C["csm_gold_replace"]}
    for c in new["cells"]:'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''pre=pre_drift_on_delta)'''
new = '''pre=pre_drift_on_delta, allowed_pre=allowed_pre)'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''    pr(f"CSM master: 값 changed {len(P['cval'])}, 값_당분기 changed {len(P['cdangi'])}")'''
new = '''    pr(f"CSM master: 값 changed {len(P['cval'])}, 값_당분기 changed {len(P['cdangi'])}")
    pr(f"pre-existing live blanks overwritten by a derivation that equals the printed 3-month column: {P['allowed_pre']}")'''
assert s.count(old) == 1
s = s.replace(old, new)
open(H + "e21_apply.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched apply3")
