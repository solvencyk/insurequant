"""one-off patcher for e21_apply.py: clean TAX22 body, comment regex, build_prov insertion"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_apply.py", encoding="utf-8").read()
# 1. remove tax_expr + TAX_BLOCK_RE
a = s.index("TAX_BLOCK_RE = ")
b = s.index("def new_test_bytes(")
s = s[:a] + s[b:]
# 2. clean TAX22 body construction
a = s.index("    by = {}\n    for co, q in sorted(tax_off_new - set(kyobo)):")
b = s.index("    s = s[:a] + body + s[b:]")
new_body = '''    by = {}
    for co, q in sorted(tax_off_new - set(kyobo)):
        by.setdefault(co, []).append(q)
    pieces = ["(\\"%s\\", q) for q in (%s)" % (co, ", ".join('"%s"' % q for q in sorted(qs))) for co, qs in sorted(by.items())]
    body = "_TAX22_LATEST_COMPARATIVE_ONLY = set(_TAX22_KYOBO_RESTATED) | {\n    " + "} | {\n    ".join(pieces) + "}"
'''
s = s[:a] + new_body + s[b:]
# 3. (a) comment regex
a = s.index('    pat = re.compile(r"(    # \(a\)')
b = s.index("    out = s.replace(")
new_pat = '''    pat = re.compile(r"(    # \(a\) 분기를 빼면 최신 비교열로만 통과하는 )\d+(칸\(교보 4 \+ 다른 )\d+(사 )\d+(\)이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다)")
    if not pat.search(s):
        raise SystemExit("ABORT: the TAX22 (a) comment was not found")
    n_co = len({co for co, _q in tax_off_new} - {"교보생명보험"})
    s = pat.sub(lambda mm: f"{mm.group(1)}{n_new}{mm.group(2)}{n_co}{mm.group(3)}{n_new - len(kyobo)}{mm.group(4)}", s)
'''
s = s[:a] + new_pat + s[b:]
# 4. build_prov insertion cleanup
old = '''            ins = (lk[pred] + 1) if pred is not None else len(new["cells"])
            # account for earlier insertions
            ins += sum(1 for x in inserted if x[1] <= ins and x[1] >= 0 and False)
            new["cells"].insert(ins, ek[k])'''
new = '''            ins = (lk[pred] + 1) if pred is not None else len(new["cells"])
            new["cells"].insert(ins, ek[k])'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''    n = int(q[5])
    if n < 4 and False:
        return False
    pq = None'''
new = '''    pq = None'''
assert s.count(old) == 1
s = s.replace(old, new)
open(H + "e21_apply.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched apply1")
