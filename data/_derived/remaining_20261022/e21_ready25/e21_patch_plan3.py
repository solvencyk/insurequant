"""one-off patcher #3: make_note wording for A / A_basis; verifier handles gold_source_print and plan_row_label"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
f = open(H + "e21_plan_full.py", encoding="utf-8").read()
old = '''    if c.get("original_print"):
        o = c["original_print"]
        mo = (f"현재 마스터값 {c['old']} 는 원 공시 rcept {o['rcept']}(단위 {o['unit']}) 인쇄값({o['value']}, 원문 " +
              ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) + ")과 일치. ")'''
new = '''    if c.get("original_print") and c.get("gold_class") == "A_basis":
        o, gsrc = c["original_print"], c["gold_source_print"]
        mo = (f"현재 마스터값(gold) {c['old']} 는 원 공시 rcept {gsrc['rcept']} 의 연결 기준 인쇄값(원문 " + ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in gsrc["lines"]) +
              f", 단위 {gsrc['unit']})이고, 같은 원 공시의 별도 기준 인쇄값(" + ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) +
              f" = {o['value']})이 최신 비교열 값과 같다 -> 재작성이 아니라 연결 -> 별도 기준 보정. ")
    elif c.get("original_print"):
        o = c["original_print"]
        mo = (f"현재 마스터값(gold) {c['old']} 는 원 공시 rcept {o['rcept']}(단위 {o['unit']}) 별도 기준 인쇄값({o['value']}, 원문 " +
              ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) + ")과 일치. ")'''
assert f.count(old) == 1
f = f.replace(old, new)
open(H + "e21_plan_full.py", "w", encoding="utf-8", newline="\n").write(f)

s = open(H + "e21_verify.py", encoding="utf-8").read()
old = '''def plan_row_label(label):
    """descriptive plan label -> the row-label text to look for"""
    m = re.search(r"\[([^\]@]+)", label)
    if m and not re.match(r"^(CSM|col|\S+ CSM)", m.group(1)) and "col " not in m.group(1):
        return m.group(1).strip()
    return re.sub(r"\s*\[.*$", "", label).strip()'''
new = '''def plan_row_label(label):
    """descriptive plan label -> the row-label text to look for.  A bracket suffix is the row label only when it holds a Korean row text (LOB readers); capture / column hints are dropped."""
    m = re.search(r"\[([^\]@]+)", label)
    if m:
        inner = m.group(1).strip()
        if re.search(r"[가-힣]", inner) and not re.search(r"(CSM|col |합계$|value cells)", inner):
            return inner
    return re.sub(r"\s*\[.*$", "", label).strip()'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
# allow_consolidated for the gold source print
s = s.replace('def verify_part(rel, p, role_ctx=None, expect_pos=None, skip_label=False):', 'def verify_part(rel, p, role_ctx=None, expect_pos=None, skip_label=False, allow_consolidated=False):')
old = '''    if re.search(r"연결재무제표", tnorm):
        problems.append(f"section is consolidated: {title!r}")'''
new = '''    if re.search(r"연결재무제표", tnorm) and not allow_consolidated:
        problems.append(f"section is consolidated: {title!r}")'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''            g = G[(c["code"], c["item"], c["quarter"])]["값"]
            if abs(tot - op["value"]) > 1e-5 or abs(tot - g) > (2e-5 if op["unit"] == "원" else 1e-6):
                probs.append(f"original print recomputed {tot} vs plan {op['value']} vs gold {g}")'''
new = '''            g = G[(c["code"], c["item"], c["quarter"])]["값"]
            if abs(tot - op["value"]) > 1e-5:
                probs.append(f"original print recomputed {tot} vs plan {op['value']}")
            gs = c.get("gold_source_print")
            gtot = 0.0
            for p in gs["lines"]:
                ok, info = verify_part(rel, p, allow_consolidated=True)
                if not ok:
                    probs.append(f"gold source L{p['line']}: {info['problem']}")
                gtot += contrib(p)
            if abs(gtot - g) > (2e-5 if gs["unit"] == "원" else 1e-6):
                probs.append(f"gold-source print recomputed {gtot} != gold {g}")
            if c["gold_class"] == "A" and abs(tot - g) > (2e-5 if op["unit"] == "원" else 1e-6):
                probs.append(f"class A but separate original print {tot} != gold {g}")
            if c["gold_class"] == "A_basis" and abs(tot - c["new"]) > (2e-5 if op["unit"] == "원" else 1e-6):
                probs.append(f"class A_basis but separate original print {tot} != latest {c['new']}")'''
assert s.count(old) == 1
s = s.replace(old, new)
open(H + "e21_verify.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched plan3")
