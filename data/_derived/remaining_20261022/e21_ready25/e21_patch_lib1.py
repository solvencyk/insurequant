"""one-off patcher for e21_plan_lib.py: mark absent OCI leaf items"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_plan_lib.py"
s = open(p, encoding="utf-8").read()
old = '''        out[i] = cell(val, v["parts"], "statement line" if len(v["parts"]) == 1 else "derived from statement lines (production definition)", f"{st.rel} {role}/cum unit {st.unit}", unit=st.unit)
'''
new = '''        out[i] = cell(val, v["parts"], "statement line" if len(v["parts"]) == 1 else "derived from statement lines (production definition)", f"{st.rel} {role}/cum unit {st.unit}", unit=st.unit)
        out[i]["absent"] = bool(v.get("absent"))
'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched lib1")
