# -*- coding: utf-8 -*-
"""Independent line-level re-read of plan_KR0083.json (own code, does not use KR0083_xml / KR0083_plan):
for each xml_lines entry (cells: prior CUMULATIVE column; seam cells: prior 3-MONTH column) open the file, take the printed text at xml_line, check the enclosing <TE ACONTEXT>
(column, separate member) and the row label (first cell of the <TR>), recompute the value from the printed won amounts.  Original prints (direct items) are re-read by line as well."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
plan = json.loads((HERE / "plan_KR0083.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
cache = {}
def lines(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return cache[rel]
def won(t):
    t = t.replace(",", "").strip()
    if t == "-":
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    v = float(t.strip("()"))
    return -v if neg else v
def row_label(L, ln, single):
    i = ln - 1
    while i > 0 and not L[i].startswith("<TR"):
        i -= 1
    for j in range(i + 1, i + 14):
        if L[j].startswith("<P>") or L[j].startswith("<P ") or (single and L[j].lstrip().startswith("<TE")):
            return TAG.sub("", L[j]).strip()
    return None
def check_line(L, ln, printed, want_ctx, plan_label):
    single = L[ln - 1].lstrip().startswith("<TE")
    txt = TAG.sub("", L[ln - 1]).strip()
    te = L[ln - 1] if single else L[ln - 2]
    ctx = re.search(r'ACONTEXT="([^"]*)"', te)
    ctx = ctx.group(1) if ctx else ""
    label = row_label(L, ln, single)
    ok_text = (txt == printed)
    ok_ctx = (want_ctx is None) or (ctx.startswith(want_ctx + "_") and "SeparateMember" in ctx)
    ok_label = label is not None and label.replace(" ", "").replace("\u3000", "") == plan_label.replace(" ", "").replace("\u3000", "")
    return txt, ctx, label, ok_text, ok_ctx, ok_label
bucket_ctx = {b["quarter"]: (b["later_filing"]["column"], b["later_filing"]["three_month_column"]) for b in plan["buckets"]}
out, bad, n = [], 0, 0
for c in plan["cells"]:
    L = lines(c["xml_file"])
    want = bucket_ctx[c["quarter"]][0]
    total = 0.0
    for p in c["xml_lines"]:
        n += 1
        txt, ctx, label, okt, okc, okl = check_line(L, p["line"], p["printed"], want, p["label"])
        total += p["sign"] * won(txt) / 1e6
        ok = okt and okc and okl
        bad += 0 if ok else 1
        out.append(f"CELL {c['quarter']} i{c['item']} L{p['line']} text={txt!r} printed={p['printed']!r} ctx={ctx.split('_')[0]}:{'SEP' if 'SeparateMember' in ctx else '---'} row_label={label!r} plan_label={p['label']!r} -> {'OK' if ok else 'MISMATCH'}")
    if abs(total - c["new"]) > 2e-5:
        bad += 1
        out.append(f"   VALUE MISMATCH {c['quarter']} i{c['item']} recomputed {total} vs new {c['new']}")
    # original print (direct items only: the original_print line is the first part)
    op = c["original_print"]
    if c["item"] != 19:
        n += 1
        LO = lines(op["xml_file"])
        txt = TAG.sub("", LO[op["xml_line"] - 1]).strip()
        okv = abs(won(txt) / 1e6 - op["value"]) <= 2e-5 and abs(op["value"] - c["old"]) <= 2e-5
        bad += 0 if okv else 1
        out.append(f"ORIG {c['quarter']} i{c['item']} L{op['xml_line']} text={txt!r} value={op['value']} master_old={c['old']} -> {'OK' if okv else 'MISMATCH'}")
for s in plan["seam_cells"]:
    if s["proposed"] != "set_dangi":
        continue
    tp = s["three_month_print"]
    L = lines(tp["xml_file"])
    want = bucket_ctx[s["quarter"]][1]
    total = 0.0
    for p in tp["xml_lines"]:
        n += 1
        txt, ctx, label, okt, okc, okl = check_line(L, p["line"], p["printed"], want, p["label"])
        total += p["sign"] * won(txt) / 1e6
        ok = okt and okc and okl
        bad += 0 if ok else 1
        out.append(f"SEAM {s['quarter']} i{s['item']} L{p['line']} text={txt!r} ctx={ctx.split('_')[0]}:{'SEP' if 'SeparateMember' in ctx else '---'} row_label={label!r} -> {'OK' if ok else 'MISMATCH'}")
    if abs(total - s["proposed_value"]) > 2e-5:
        bad += 1
        out.append(f"   VALUE MISMATCH seam {s['quarter']} i{s['item']} recomputed {total} vs {s['proposed_value']}")
# set_dangi source strings carry the same lines: check every 'L<digits>' in the string exists in the cited file and the cited text is the printed text
for cell in plan["apply_contract"]["set_dangi_cells"]:
    for m in re.finditer(r"(data/dart/[^:|]+\.xml):L(\d+) \[([^\]]+)\] ([^ ]+)원", cell[4]):
        n += 1
        L = lines(m.group(1))
        txt = TAG.sub("", L[int(m.group(2)) - 1]).strip()
        okx = (txt == m.group(4))
        bad += 0 if okx else 1
        out.append(f"SRC {cell[1]} i{cell[2]} L{m.group(2)} {txt!r} vs source string {m.group(4)!r} -> {'OK' if okx else 'MISMATCH'}")
out.append(f"TOTAL line checks {n}, problems {bad}")
(HERE / "KR0083_line_verify.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
plan["verification"]["xml_line_reread"] = dict(script="KR0083_line_verify.py (own parser)", n_line_checks=n, n_problems=bad, report="KR0083_line_verify.txt")
(HERE / "plan_KR0083.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(n, bad)
