"""one-off patcher #2 for e21_csm2.py: wide rows = the LAST 25 cells of the row (blank / '-' cells count as 0)"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_csm2.py"
s = open(p, encoding="utf-8").read()
old = '''    def csm_cells(r, label, sign=1):
        nums = W.numeric_cells(r, 0)[-25:]
        if len(nums) != 25:
            raise RuntimeError(f"{label}: {len(nums)} value cells (need 25)")
        non_csm = [nums[i] for i in range(25) if i not in CSM_IDX]
        return [eok_cell(f"{label} [col {i}]", nums[i], sign, unit) for i in CSM_IDX], non_csm
'''
new = '''    def last25(r, label):
        """the last 25 cells of the row as (value, line, text); blank and '-' cells are 0"""
        cs = r["cells"][-25:]
        if len(cs) != 25:
            raise RuntimeError(f"{label}: {len(r['cells'])} cells (need >= 25)")
        out = []
        for c in cs:
            if c["val"] is not None:
                out.append((c["val"], c["line"], c["text"]))
            elif c["text"].strip() in ("", "-", "\u2212"):
                out.append((0.0, c["line"], c["text"]))
            else:
                raise RuntimeError(f"{label}: non-numeric value cell {c['text']!r}")
        return out

    def csm_cells(r, label, sign=1):
        nums = last25(r, label)
        non_csm = [nums[i] for i in range(25) if i not in CSM_IDX]
        return [eok_cell(f"{label} [col {i}]", nums[i], sign, unit) for i in CSM_IDX], non_csm
'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = '''    allc = W.numeric_cells(am, 0)[-25:]
'''
new2 = '''    allc = last25(am, "amort")
'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched #2")
