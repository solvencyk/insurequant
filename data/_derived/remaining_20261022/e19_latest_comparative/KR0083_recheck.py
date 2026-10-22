# Independent recheck of plan_KR0083.json against the raw XML (ACODE/ACONTEXT tags), written 2026-10-22.
import json, re, sys
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
EV = ROOT + "data/_derived/remaining_20261022/e19_latest_comparative/"
plan = json.load(open(EV + "plan_KR0083.json", encoding="utf-8"))
out = open(EV + "KR0083_recheck.txt", "w", encoding="utf-8")
def W(s): out.write(s + "\n")
cache = {}
def lines(f):
    if f not in cache:
        cache[f] = open(ROOT + f, encoding="utf-8").read().split("\n")
    return cache[f]
def num(s):
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    d = re.sub(r"[^0-9.]", "", s)
    if d == "": return None
    v = float(d)
    return -v if neg else v
def cell_at(f, ln):
    L = lines(f)
    # find enclosing <TE ...> opening at ln or ln-1 (1-based line numbers)
    for k in (ln - 1, ln - 2, ln - 3):
        if 0 <= k < len(L) and L[k].lstrip().startswith("<TE "):
            tag = L[k]
            m = re.search(r'ACODE="([^"]*)"', tag); c = re.search(r'ACONTEXT="([^"]*)"', tag)
            end = k
            while "</TE>" not in L[end] and end < len(L) - 1: end += 1
            txt = re.sub(r"<[^>]+>", "", " ".join(L[k:end + 1]))
            return (m.group(1) if m else None, c.group(1) if c else None, num(txt))
    return None
bad = 0
for c in plan["cells"]:
    parts = []
    for xl in c["xml_lines"]:
        r = cell_at(c["xml_file"], xl["line"])
        parts.append((xl["label"], xl["line"], r, xl["sign"]))
    tot = 0.0
    ok_ctx = True
    for lab, ln, r, sg in parts:
        if r is None or r[2] is None: ok_ctx = False; continue
        ctx = r[1] or ""
        want = "PFY2024d" + ("FQA" if c["quarter"] == "2024.1Q" else "HYA")
        if not (ctx.startswith(want) and "SeparateMember" in ctx): ok_ctx = False
        tot += sg * r[2]
    val = tot / 1e6
    # item 19: expense lines printed positive, income lines +; plan has sign per line; compare to new
    ok = ok_ctx and abs(val - c["new"]) < 5e-7
    if not ok: bad += 1
    W("CELL %s i%d new=%.6f recheck=%.6f ctx_ok=%s %s | %s" % (c["quarter"], c["item"], c["new"], val, ok_ctx, "OK" if ok else "BAD", [(p[0], p[1], p[2][0] if p[2] else None, p[2][1][:12] if p[2] and p[2][1] else None) for p in parts]))
for s in plan["seam_cells"]:
    tm = s["three_month_print"]
    tot = 0.0; ok_ctx = True
    for xl in tm["xml_lines"]:
        r = cell_at(tm["xml_file"], xl["line"])
        if r is None or r[2] is None: ok_ctx = False; continue
        if not (r[1].startswith("PFY2024dTQQ") and "SeparateMember" in r[1]): ok_ctx = False
        tot += xl["sign"] * r[2]
    val = tot / 1e6
    ok = ok_ctx and abs(val - s["proposed_value"]) < 5e-7
    if not ok: bad += 1
    W("SEAM %s i%d proposed=%.6f recheck=%.6f ctx_ok=%s %s" % (s["quarter"], s["item"], s["proposed_value"], val, ok_ctx, "OK" if ok else "BAD"))
W("BAD=%d" % bad)
