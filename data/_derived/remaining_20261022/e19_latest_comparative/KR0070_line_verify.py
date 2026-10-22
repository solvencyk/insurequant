# -*- coding: utf-8 -*-
"""Independent line-level re-read of every cell of plan_KR0070.json (own code, does not use KR0070_xml / KR0070_plan):
for each xml_lines entry open the file, take the <P> at xml_line, compare with the printed text, check the enclosing <TE ACONTEXT> (column) and the row label (first <TE><P> of the <TR>)."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
plan = json.loads((HERE / "plan_KR0070.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
cache = {}
def lines(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return cache[rel]
def won(t):
    t = t.replace(",", "").strip()
    neg = t.startswith("(") and t.endswith(")")
    v = float(t.strip("()"))
    return -v if neg else v
bucket_ctx = {b["quarter"]: b["later_filing"]["column"] for b in plan["buckets"]}
out, bad = [], 0
n = 0
for c in plan["cells"]:
    L = lines(c["xml_file"])
    want_ctx = bucket_ctx[c["quarter"]]
    total = 0.0
    for p in c["xml_lines"]:
        n += 1
        ln = p["line"]
        single = L[ln - 1].lstrip().startswith("<TE")          # single-line cell <TE ...>text</TE>
        txt = TAG.sub("", L[ln - 1]).strip()
        te = L[ln - 1] if single else L[ln - 2]
        ctx = re.search(r'ACONTEXT="([^"]*)"', te)
        ctx = ctx.group(1) if ctx else ""
        # enclosing TR: walk up
        i = ln - 1
        while i > 0 and not L[i].startswith("<TR"):
            i -= 1
        label = None
        for j in range(i + 1, i + 12):
            if L[j].startswith("<P>") or (single and L[j].lstrip().startswith("<TE")):
                label = TAG.sub("", L[j]).strip()
                break
        ok_text = (txt == p["printed"])
        ok_ctx = ctx.startswith(want_ctx + "_") and "SeparateMember" in ctx
        ok_label = (label == p["label"].replace(" ", "")) or (label is not None and label.replace(" ", "") == p["label"].replace(" ", ""))
        total += p["sign"] * won(txt) / 1e6
        ok = ok_text and ok_ctx and ok_label
        bad += 0 if ok else 1
        out.append(f"{c['quarter']} i{c['item']} L{ln} text={txt!r} printed={p['printed']!r} ctx={ctx.split('_')[0]}:{'SEP' if 'SeparateMember' in ctx else '---'} row_label={label!r} plan_label={p['label']!r} -> {'OK' if ok else 'MISMATCH'}")
    if c["derivation"] != "direct print" or len(c["xml_lines"]) == 1:
        if abs(total - c["new"]) > 2e-5:
            bad += 1
            out.append(f"   VALUE MISMATCH {c['quarter']} i{c['item']} recomputed {total} vs new {c['new']}")
out.append(f"TOTAL line checks {n}, problems {bad}")
(HERE / "KR0070_line_verify.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
plan["verification"]["xml_line_reread"] = dict(script="KR0070_line_verify.py (own parser)", n_line_checks=n, n_problems=bad, report="KR0070_line_verify.txt")
(HERE / "plan_KR0070.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(n, bad)
