from pathlib import Path
p = Path("e19_verify_plans.py")
s = p.read_text(encoding="utf-8")
# 1) cell_at: support inline <TE ...>text</TE> and return context; blank -> "" ; also expose ctx
a = s.index("def cell_at(rel, ln):")
b = s.index("def row_of(rel, ln):")
new_cell = '''TE_INLINE = re.compile(r"<TE\b([^>]*)>(.*?)</TE>", re.S)
CTX_RE = re.compile(r'ACONTEXT="([^"]*)"')


def cell_ctx(rel, ln):
    """(text, context) of the value cell that sits on line ln. Two filing layouts: <TE ...>text</TE> on one line, or <TE ...> on a line above and <P>text</P> on ln."""
    L = lines_of(rel)
    line = L[ln - 1]
    m = TE_INLINE.search(line)
    if m:
        cm = CTX_RE.search(m.group(1))
        return ptext(m.group(2)), (cm.group(1) if cm else None)
    m = P_RE.search(line)
    if m:
        ctx = None
        for k in range(ln - 2, max(ln - 6, 0), -1):
            if "<TE" in L[k]:
                cm = CTX_RE.search(L[k])
                ctx = cm.group(1) if cm else None
                break
        return ptext(m.group(1)), ctx
    return None, None


def cell_at(rel, ln):
    return cell_ctx(rel, ln)[0]


'''
s = s[:a] + new_cell + s[b:]
# 2) row_of: also take inline TE text
s = s.replace('''        for m in P_RE.finditer(L[k]):
            cells.append(ptext(m.group(1)))
            lines.append(k + 1)
        k += 1''', '''        mi = TE_INLINE.search(L[k])
        if mi:
            cells.append(ptext(mi.group(2)))
            lines.append(k + 1)
        else:
            for m in P_RE.finditer(L[k]):
                cells.append(ptext(m.group(1)))
                lines.append(k + 1)
        k += 1''')
# 3) blank cell counts as 0 for the sum (recorded), record contexts
s = s.replace('''                    raw = cell_at(rel, l)
                    vals.append(parse_num(raw) if raw is not None else None)''', '''                    raw, cx = cell_ctx(rel, l)
                    ctxs.append(cx)
                    vals.append(parse_num(raw) if raw is not None else (0.0 if raw is not None and raw.strip() == "" else None))
                    if raw is not None and raw.strip() == "":
                        blanks.append(l)''')
s = s.replace('''                lns = ln if isinstance(ln, list) else [ln]
                vals = []''', '''                lns = ln if isinstance(ln, list) else [ln]
                vals = []''')
s = s.replace("            labels, positions = [], []\n", "            labels, positions, ctxs, blanks = [], [], [], []\n")
s = s.replace('''                for e in lst:
                    raw = cell_at(rel, e["line"])
                    v = parse_num(raw) if raw is not None else None''', '''                for e in lst:
                    raw, cx = cell_ctx(rel, e["line"])
                    ctxs.append(cx)
                    v = parse_num(raw) if raw is not None else None''')
s = s.replace('''            rec["labels"] = labels
''', '''            rec["labels"] = labels
            rec["contexts"] = ctxs
            rec["blank_cells_as_zero"] = blanks
            cx_ok = all((cx is None) or (cx.startswith("PFY") and cx.endswith("SeparateMember") and re.match(r"PFY\d{4}d(TQA|HYA|FQA|FY)_", cx)) for cx in ctxs)
            rec["checks"]["context_prior_cumulative_separate"] = cx_ok
''')
s = s.replace('''    txt.append(f"problems: {len(res['problems'])}")''', '''    nctx = Counter(("none" if cx is None else cx.split("_")[0]) for r in res["cells"] for cx in r["contexts"])
    txt.append("ACONTEXT of the cited cells: " + json.dumps(dict(nctx), ensure_ascii=False))
    txt.append("cells with blank cell(s) counted as 0: " + json.dumps([(r["code"], r["q"], r["item"], r["blank_cells_as_zero"]) for r in res["cells"] if r["blank_cells_as_zero"]], ensure_ascii=False))
    txt.append(f"problems: {len(res['problems'])}")''')
p.write_text(s, encoding="utf-8", newline="\n")
