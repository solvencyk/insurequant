# -*- coding: utf-8 -*-
"""Independent line-level re-read of every cell in plan_KR0032.json: open the raw XML, go to the cited line, check the printed number text and (for
context-tagged filings) the ACONTEXT of the enclosing <TE> tag, then recompute the cell value from the cited lines alone."""
import json, re, sys
from pathlib import Path
H = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
plan = json.loads((H / "plan_KR0032.json").read_text(encoding="utf-8"))
cache = {}
def lines(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return cache[rel]
def num(t):
    t = t.replace(",", "").strip()
    neg = t.startswith("(") and t.endswith(")")
    return -float(t.strip("()")) if neg else float(t)
RE_P = re.compile(r"<P[^>]*>(.*?)</P>")
out, bad = [], 0
for c in plan["cells"]:
    rel = c["xml_file"]
    L = lines(rel)
    ctx = c["xml_period_column"].split(" ")[0]
    tot = 0.0
    for p in c["xml_lines"]:
        ln = p["line"]
        if L[ln - 1].startswith("<TE"):          # single-line cell <TE ...>text</TE>
            mi = re.search(r">([^<]*)</TE>\s*$", L[ln - 1])
            txt = mi.group(1).strip() if mi else None
            te = L[ln - 1]
        else:
            m = RE_P.search(L[ln - 1])
            txt = m.group(1).strip() if m else None
            # enclosing TE tag: walk up to the nearest line starting with <TE
            k = ln - 1
            while k > 0 and not L[k - 1].startswith("<TE"):
                k -= 1
            te = L[k - 1] if k > 0 else ""
        ctx_ok = (ctx in te) and ("SeparateMember" in te)
        val = num(txt) / 1e6 if txt else None
        ok = (txt == p["printed"]) and ctx_ok
        tot += p["sign"] * (val if val is not None else 0.0)
        if not ok:
            bad += 1
        out.append(f"{c['quarter']} i{c['item']:>2} L{ln} printed='{txt}' plan='{p['printed']}' ctx_in_TE={ctx_ok} label={p['label']} ok={ok}")
    okv = abs(tot - c["new"]) <= 2e-6
    if not okv:
        bad += 1
    out.append(f"   -> recomputed {round(tot, 6)} plan.new {c['new']} ok={okv}")
out.append(f"BAD={bad} cells={len(plan['cells'])}")
(H / "KR0032_s3_lines.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("bad", bad)
