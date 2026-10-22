# -*- coding: utf-8 -*-
"""e20 INDEPENDENT re-read of EVERY planned cell (own regex code; imports nothing from e20_xml / e20_read / e20_plan) against the raw filing line it cites.
For each cell: every cited physical line of the filing is opened, the printed number is re-parsed (value, parentheses = negative), the TR's first cell is taken as the row label,
the cell's position inside its row is recorded, the ACONTEXT (xml layout) is checked, the signed sum / scale (원 -> 백만원) is recomputed and compared with the plan value, the live master
is compared with the plan 'old' and the original-vintage print (original_print.lines) is re-read the same way.  The pin sources (set_dangi) and the cause lines are re-read too.
Writes e20_verify_plans.txt / .json next to this file."""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / "e20_plan.json").read_text(encoding="utf-8"))
_cache = {}
TAG = re.compile(r"<[^>]+>")
CELL_INLINE = re.compile(r"<(TE|TD|TH)\b([^>]*)>(.*?)</\1>", re.S | re.I)
P_RE = re.compile(r"<P[^>]*>(.*?)</P>", re.S | re.I)
CTX_RE = re.compile(r'ACONTEXT="([^"]*)"')
CELL_OPEN = re.compile(r"<(TE|TD|TH)\b", re.I)


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ")).strip()


def parse_num(t):
    t = t.strip().replace(",", "").replace(" ", "")
    if t in ("", "-"):
        return 0.0 if t == "-" else None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def cell_at(rel, ln):
    """(text, ctx) of the cell whose text sits on physical line ln"""
    L = lines_of(rel)
    line = L[ln - 1]
    m = CELL_INLINE.search(line)
    if m:
        cm = CTX_RE.search(m.group(2))
        return clean(m.group(3)), (cm.group(1) if cm else None)
    m = P_RE.search(line)
    if m:
        ctx = None
        for k in range(ln - 2, max(ln - 8, 0), -1):
            if CELL_OPEN.search(L[k]):
                cm = CTX_RE.search(L[k])
                ctx = cm.group(1) if cm else None
                break
        return clean(m.group(1)), ctx
    return None, None


def row_cells(rel, ln):
    """all cells (text, line) of the <TR> that contains physical line ln, in order"""
    L = lines_of(rel)
    i = ln - 1
    while i > 0 and not re.search(r"<TR\b", L[i], re.I):
        i -= 1
    j = ln - 1
    while j < len(L) - 1 and "</TR>" not in L[j].upper():
        j += 1
    cells = []
    k = i
    while k <= j:
        line = L[k]
        if CELL_OPEN.search(line):
            m = CELL_INLINE.search(line)
            if m:
                cells.append((clean(m.group(3)), k + 1))
            else:
                # multi-line cell: the text is in a <P> on a following line
                t, ln2 = None, None
                for q in range(k + 1, min(k + 8, j + 1)):
                    mp = P_RE.search(L[q])
                    if mp:
                        t, ln2 = clean(mp.group(1)), q + 1
                        break
                    if re.search(r"</(TE|TD|TH)>", L[q], re.I):
                        break
                cells.append((t if t is not None else "", ln2 if ln2 else k + 1))
        k += 1
    return cells


UNIT_RE = re.compile(r"\(\s*단위\s*[:：]?\s*([^)<]*)\)")


def unit_above(rel, ln, span=2500):
    """unit printed in the statement header: nearest '(단위 : ...)' above the cited line -> '원' | '백만원' | '억원' | '천원'"""
    L = lines_of(rel)
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = UNIT_RE.search(clean(L[k]))
        if m:
            u = m.group(1)
            for cand in ("백만원", "억원", "천원", "원"):
                if cand in u:
                    return cand, k + 1
    return None, None


def scale_of(unit):
    return 1e6 if unit == "원" else 1.0


def norm_label(s):
    s = (s or "").replace("\u3000", "").replace(" ", "").replace("\xa0", "")
    s = re.sub(r"^([\u2160-\u2169]|[IVX]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    s = re.sub(r"^\d+\)", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    return s.replace("(손실)", "").replace("(수익)", "").replace("(이익)", "")


import subprocess


def head_json(rel):
    """the PRE-apply state (HEAD) -- the plan 'old' values and the gold pins are checked against it so that the script gives the same answer before and after the apply"""
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


live = head_json("PL_breakdown.json")
LIVE = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
LIVE_D = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in live}
gold = head_json("data/_gold/user_pl_cells.json")
GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
CONTRACT = PLAN["apply_contract"]
REPL = {(e["code"], e["item"], e["quarter"]) for e in CONTRACT["gold_replace"]}
NEW = {(e["code"], e["item"], e["quarter"]) for e in CONTRACT["gold_new"]}

res = {"cells": [], "problems": [], "per_bucket": {}}
txt = []
pos_stat = defaultdict(Counter)
for b in PLAN["buckets"]:
    if "error" in b:
        res["problems"].append(dict(bucket=(b["code"], b["quarter"]), error=b["error"]))
        continue
    code, q = b["code"], b["quarter"]
    n_ok = 0
    for c in b["cells"]:
        it = c["item"]
        key = (code, it, q)
        rec = dict(code=code, q=q, item=it, new=c["new"], old=c["old"], checks={}, labels=[], ctxs=[], positions=[])
        rel = c["xml_file"]
        sc = scale_of(c["source_unit"])
        tot = 0.0
        okp = True
        okl = True
        for p in c["xml_lines"]:
            t, ctx = cell_at(rel, p["line"])
            v = parse_num(t) if t is not None else None
            pr = parse_num(p["printed"])
            if v is None or pr is None or abs(v - pr) > 1e-9:
                okp = False
            if v is not None:
                tot += p["sign"] * v / sc
            cells = row_cells(rel, p["line"])
            lab = cells[0][0] if cells else None
            if lab is None or norm_label(lab) != norm_label(p["label"]):
                okl = False
            rec["labels"].append((lab, p["label"]))
            rec["ctxs"].append(ctx)
            lines_in_row = [ln for _t, ln in cells]
            if p["line"] in lines_in_row:
                numeric = [(i, ln) for i, (tx, ln) in enumerate(cells) if i > 0 and (parse_num(tx) is not None)]
                idxs = [i for i, ln in numeric]
                pos = [ln for _i, ln in numeric].index(p["line"]) if p["line"] in [ln for _i, ln in numeric] else None
                rec["positions"].append((pos, len(numeric)))
                pos_stat[(code, q)][(pos, len(numeric))] += 1
            else:
                rec["positions"].append((None, None))
        u_read, u_line = unit_above(rel, c["xml_lines"][0]["line"])
        rec["unit_read"] = (u_read, u_line)
        rec["checks"]["unit_in_filing_matches_plan"] = (u_read == c["source_unit"])
        rec["checks"]["printed_matches_xml"] = okp
        rec["checks"]["row_label_matches"] = okl
        rec["computed"] = tot
        tol = 1e-5 if c["source_unit"] == "원" else 1e-6
        rec["checks"]["value_matches_plan"] = abs(tot - c["new"]) <= max(tol, 1e-6)
        lv = LIVE.get(key)
        rec["checks"]["old_equals_live_master"] = (lv is not None and abs(lv - c["old"]) <= 5e-7)
        if key in GOLD:
            rec["checks"]["gold_cell_is_planned_replace"] = key in REPL
        else:
            rec["checks"]["new_cell_not_in_gold"] = key in NEW
        # context: prior-year cumulative separate, when the cell carries an ACONTEXT; positional layouts: last cumulative column
        cxs = [x for x in rec["ctxs"] if x]
        if cxs:
            rec["checks"]["ctx_prior_cumulative_separate"] = all(re.match(rf"PFY{int(q[:4])}d(FQA|HYA|TQA|FY)_", x) and "SeparateMember" in x for x in cxs)
        # original-vintage print
        op = c.get("original_print")
        if op:
            otot = 0.0
            ok_o = True
            osc = scale_of(op["unit"])
            for p in op["lines"]:
                t, _ctx = cell_at(op["file"], p["line"])
                v = parse_num(t) if t is not None else None
                if v is None:
                    ok_o = False
                    continue
                otot += p["sign"] * v / osc
            ou, _ol = unit_above(op["file"], op["lines"][0]["line"])
            rec["checks"]["original_unit_in_filing_matches_plan"] = (ou == op["unit"])
            rec["original_print_recomputed"] = otot
            rec["checks"]["original_print_matches"] = ok_o and abs(otot - op["value"]) <= max(1e-5, 1e-6)
            rec["checks"]["old_equals_original_print"] = abs(otot - c["old"]) <= (2e-5 if op["unit"] == "원" else 0.5)
        ok = all(rec["checks"].values())
        if ok:
            n_ok += 1
        else:
            res["problems"].append(rec)
        res["cells"].append(rec)
    res["per_bucket"][f"{code} {q}"] = dict(cells=len(b["cells"]), all_checks_ok=n_ok)
    txt.append(f"{code} {q}: cells {len(b['cells'])}, all checks ok {n_ok}")
txt.append("")
txt.append("position of the cited cell among the numeric cells of its row (position, n numeric cells) per bucket (must be ONE dominant position = prior-period cumulative column):")
for k, cnt in sorted(pos_stat.items()):
    txt.append(f"  {k[0]} {k[1]}: {dict(cnt)}")
# ---------------------------------------------------------------- pin sources and cause lines
txt.append("")
bad_pins = []
for x in CONTRACT["set_dangi_add"]:
    code, q, it, val, src = x
    m = re.match(r"(data/[^:]+):(.*)", src)
    rel = m.group(1)
    got = []
    for mm in re.finditer(r"L(\d+) \[([^\]]*)\] (\S+)", m.group(2)):
        ln = int(mm.group(1))
        t, _ = cell_at(rel, ln)
        got.append((ln, t, mm.group(3)))
    ok = all(parse_num(t) is not None and abs(parse_num(t) - parse_num(pr)) < 1e-9 for _l, t, pr in got) and len(got) > 0
    scale = 1.0 if "백만원" in src else None
    vals = [parse_num(t) for _l, t, _p in got]
    txt.append(f"set_dangi_add {code} {q} i{it}: value {val}; re-read {[(l, t) for l, t, _p in got]} ok={ok} sum={sum(v for v in vals if v is not None)}")
    if not ok or abs(sum(v for v in vals if v is not None) - val) > 1e-6:
        bad_pins.append(x)
txt.append(f"set_dangi_add bad: {len(bad_pins)}")
rm = []
for code, q, it in CONTRACT["set_dangi_remove"]:
    pin = next(x for x in gold["set_dangi"]["cells"] if x[0] == code and x[1] == q and int(x[2]) == it)
    rm.append((code, q, it, pin[3]))
txt.append(f"set_dangi_remove: {len(rm)} pins removed; pinned value == live single quarter (so removal is value-neutral if the builder derives it): " +
           str([(c, q, i, v, LIVE_D.get((c, i, q)), abs(v - LIVE_D[(c, i, q)]) < 1e-6) for c, q, i, v in rm]))
# cause lines cited in the gold notes: the physical line exists and states a restatement / accounting-policy change
bad_cause = []
n_cause = 0
for b in PLAN["buckets"]:
    if "error" in b or not b.get("cause"):
        continue
    for x in b["cause"]["lines"]:
        t = clean(lines_of(b["later"]["file"])[x["line"] - 1])
        n_cause += 1
        if not re.search(r"재작성|소급|일탈회계|회계정책의 변경", t):
            bad_cause.append((b["code"], b["quarter"], x["line"], t[:80]))
txt.append(f"cause lines re-read: {n_cause}, not stating a restatement / policy change: {len(bad_cause)} {bad_cause}")
nctx = Counter(("none" if cx is None else cx.split("_")[0]) for r in res["cells"] for cx in r["ctxs"])
txt.append("ACONTEXT of the cited cells: " + json.dumps(dict(nctx), ensure_ascii=False))
txt.append(f"problems: {len(res['problems'])}")
for p in res["problems"][:60]:
    txt.append("  " + json.dumps({k: v for k, v in p.items() if k in ("code", "q", "item", "new", "old", "computed", "checks", "labels", "positions", "error")}, ensure_ascii=False)[:900])
n_cells = len(res["cells"])
n_ok_all = sum(1 for r in res["cells"] if all(r["checks"].values()))
txt.append(f"TOTAL cells {n_cells}, all checks ok {n_ok_all}")
(HERE / "e20_verify_plans.txt").write_text("\n".join(txt) + "\n", encoding="utf-8", newline="\n")
(HERE / "e20_verify_plans.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
print("\n".join(txt[:6]))
print(txt[-3:])
