"""one-off patcher for e21_plan.py (find_printed: sep_only filter) and e21_plan_full.py (gold-source vs separate original print)"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_plan.py", encoding="utf-8").read()
old = 'def find_printed(path, texts, label_sub, span_lines=None):'
new = 'def find_printed(path, texts, label_sub, sep_only=False):'
assert s.count(old) == 1
s = s.replace(old, new)
old = '''                if label_sub in re.sub(r"\s+", "", lab):
                    hits.append((i, lab, tx))
    return hits'''
new = '''                if label_sub in re.sub(r"\s+", "", lab):
                    if sep_only:
                        t = i - 1
                        while t > 0 and not lines[t - 1].startswith("<TITLE"):
                            t -= 1
                        if "연결" in re.sub(r"\s+", "", W.clean(lines[t - 1] if t > 0 else "")):
                            continue
                    hits.append((i, lab, tx))
    return hits'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(H + "e21_plan.py", "w", encoding="utf-8", newline="\n").write(s)

f = open(H + "e21_plan_full.py", encoding="utf-8").read()
a = f.index("# original-vintage prints of the owner-gold cells")
b = f.index("UNIT_RE = ")
newspec = '''# original-vintage prints of the owner-gold cells.  key -> dict(gold_src=[(printed text, label substring, sign, abs?)]  the print(s) that equal the gold value (any section),
#                                                          orig_sep =[...] the SEPARATE-basis (not 연결) original print(s), or None when gold_src is itself the separate print)
# sign / abs: the role of the printed line in the item definition (+1 / False = the printed value is the item value, parentheses = negative; -1 / True = minus the magnitude)
ORIG_PRINT = {
    ("KR0010", "2023.1Q", 16): dict(gold_src=[("92,565", "기타사업비용", 1, False)], orig_sep=[("91,710", "기타사업비용", 1, False)]),
    ("KR0010", "2023.2Q", 16): dict(gold_src=[("190,719", "기타사업비용", 1, False)], orig_sep=[("189,068", "기타사업비용", 1, False)]),
    ("KR0003", "2023.2Q", 19): dict(gold_src=[("71,316,307,049", "보험금융손익", -1, True)], orig_sep=None),
    ("KR0001", "2023.1Q", 16): dict(gold_src=[("12,370,224,177", "기타사업비", 1, False)], orig_sep=[("11,048,069,618", "기타사업비", 1, False)]),
    ("KR0001", "2023.2Q", 16): dict(gold_src=[("71,546,566,619", "기타사업비", 1, False)], orig_sep=[("73,064,945,045", "기타사업비", 1, False)]),
    ("KR0068", "2023.1Q", 20): dict(gold_src=[("375,708,317,423", "영업이익", 1, False)], orig_sep=None),
    ("KR0068", "2023.2Q", 21): dict(gold_src=[("255,859,540,321", "영업외수익", 1, False), ("66,392,230,352", "영업외비용", -1, True)], orig_sep=None),
}
'''
f = f[:a] + newspec + f[b:]
# orig_print_record -> two records
a = f.index("def orig_print_record(code, q, item):")
b = f.index("def fmt(v, nd=1):")
newrec = '''def print_record(code, q, spec, sep_only):
    path = T.main_path(code, P.orig_fy(q))
    lines = PL.M_lines(str(path))
    parts, tot = [], 0.0
    for text, lab, sign, absf in spec:
        hits = PL.find_printed(str(path), [text], lab, sep_only=sep_only)
        if len(hits) != 1:
            raise RuntimeError(f"{code} {q}: original print {text!r} (label~{lab}, sep_only={sep_only}) located {len(hits)} times: {hits}")
        ln, label, _tx = hits[0]
        pr = printed_cell(lines, ln, text)
        unit, uln = unit_of_line(lines, ln)
        v = P.num_of(pr) / P.UNIT_DIV[unit]
        contrib = round(sign * (abs(v) if absf else v), 6)
        parts.append(dict(label=label, line=ln, printed=pr, sign=sign, abs=absf, unit=unit, contribution_mn=contrib, unit_line=uln))
        tot += contrib
    return dict(value=round(tot, 6), file=PL.R.X.rel(path), rcept=path.stem, lines=parts, unit=parts[0]["unit"])


def orig_print_records(code, q, item):
    spec = ORIG_PRINT[(code, q, item)]
    gs = print_record(code, q, spec["gold_src"], sep_only=False)
    osr = print_record(code, q, spec["orig_sep"], sep_only=True) if spec["orig_sep"] else print_record(code, q, spec["gold_src"], sep_only=True)
    return gs, osr


'''
f = f[:a] + newrec + f[b:]
# classification block
old = '''            if (c["code"], c["quarter"], c["item"]) not in ORIG_PRINT:
                raise RuntimeError(f"gold cell {k} has no original-print spec")
            op = orig_print_record(c["code"], c["quarter"], c["item"])
            tol = 2e-5 if op["unit"] == "원" else 1e-6
            if abs(g["값"] - op["value"]) <= tol:
                cls = "A"          # gold == original print -> replace
            elif abs(g["값"] - c["new"]) <= 1.0:
                cls = "latest"
            else:
                cls = "B"
            gold_class[k] = cls
            c["gold_class"] = cls
            c["original_print"] = op
            OUT.append(f"   {k}: gold {g['값']} | original print {op['value']} ({op['unit']}; lines {[(p['line'], p['printed'], p['label']) for p in op['lines']]}) | latest {c['new']} -> class {cls}")'''
new = '''            if (c["code"], c["quarter"], c["item"]) not in ORIG_PRINT:
                raise RuntimeError(f"gold cell {k} has no original-print spec")
            gs, op = orig_print_records(c["code"], c["quarter"], c["item"])
            tol = 2e-5 if op["unit"] == "원" else 1e-6
            if abs(g["값"] - op["value"]) <= tol:
                cls = "A"          # gold == the SEPARATE original print -> replace by the latest comparative
            elif abs(g["값"] - gs["value"]) <= tol and abs(op["value"] - c["new"]) <= (2e-5 if op["unit"] == "원" else 1e-6):
                cls = "A_basis"    # gold == the CONSOLIDATED original print; the separate original print equals the latest comparative -> basis correction, not a restatement
            elif abs(g["값"] - c["new"]) <= 1.0:
                cls = "latest"
            else:
                cls = "B"
            gold_class[k] = cls
            c["gold_class"] = cls
            c["original_print"] = op
            c["gold_source_print"] = gs
            OUT.append(f"   {k}: gold {g['값']} | gold-source print {gs['value']} ({[(p['line'], p['printed']) for p in gs['lines']]}) | separate original print {op['value']} ({op['unit']}; lines {[(p['line'], p['printed'], p['label']) for p in op['lines']]}) | latest {c['new']} -> class {cls}")'''
assert f.count(old) == 1
f = f.replace(old, new)
open(H + "e21_plan_full.py", "w", encoding="utf-8", newline="\n").write(f)
print("patched plan2")
