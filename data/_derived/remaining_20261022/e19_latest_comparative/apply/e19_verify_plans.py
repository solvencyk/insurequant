# -*- coding: utf-8 -*-
"""Read-only independent re-read of EVERY plan cell (172 cells) against the raw XML line it cites.
For each cell: the cited line(s) are read from the filing XML, the printed number is re-parsed (own code, not the planners'),
converted with the printed unit, signed, and compared with the plan 'new'. The row label (first cell of the <TR> that holds the line) and the
cell's position inside the row (idx / ncells) are recorded; position outliers inside one bucket are flagged.
Also: plan 'old' == live PL_breakdown.json; the cell is not an existing owner gold cell; plan sets of cells vs plan.buckets are consistent.
Writes e19_verify_plans.txt / .json next to this file."""
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
E = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
CODES = ["KR0005", "KR0032", "KR0070", "KR0082", "KR0083", "KR0087", "KR0104"]
P_RE = re.compile(r"<P[^>]*>(.*?)</P>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
_cache = {}


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def ptext(s):
    return TAG_RE.sub("", s).replace("&amp;", "&").replace("\u3000", " ").strip()


def parse_num(t):
    t = t.strip().replace(",", "").replace(" ", "")
    if t in ("", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


TE_INLINE = re.compile(r"<TE\b([^>]*)>(.*?)</TE>", re.S)
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


def row_of(rel, ln):
    L = lines_of(rel)
    i = ln - 1
    while i > 0 and "<TR" not in L[i]:
        i -= 1
    j = ln - 1
    while j < len(L) - 1 and "</TR>" not in L[j]:
        j += 1
    cells, lines = [], []
    k = i
    while k <= j:
        mi = TE_INLINE.search(L[k])
        if mi:
            cells.append(ptext(mi.group(2)))
            lines.append(k + 1)
        else:
            for m in P_RE.finditer(L[k]):
                cells.append(ptext(m.group(1)))
                lines.append(k + 1)
        k += 1
    # a <P>..</P> may span lines; fall back to a whole-row regex when the target line was not captured
    if ln not in lines:
        blob = "\n".join(L[i:j + 1])
        cells = [ptext(x) for x in P_RE.findall(blob)]
        lines = []
    return cells, lines


def main():
    live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    liveby = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in live}
    gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    goldkeys = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"]}
    res = {"cells": [], "problems": [], "per_company": {}}
    txt = []
    pos_stat = defaultdict(Counter)
    for code in CODES:
        plan = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
        n_ok = 0
        for c in plan["cells"]:
            q, it, new, old = c["quarter"], c["item"], c["new"], c["old"]
            key = (code, it, q)
            rec = {"code": code, "q": q, "item": it, "new": new, "old": old, "checks": {}}
            # old == live
            r = liveby.get(key)
            lv = None if r is None else r.get("값")
            rec["checks"]["old_eq_live"] = (lv is not None and old is not None and abs(lv - old) <= 5e-4) or (lv is None and old is None)
            rec["checks"]["not_gold"] = key not in goldkeys
            rel = c["xml_file"]
            su = c.get("source_unit")
            scale = 1e6 if su == "원" else 1.0
            lst = c.get("xml_lines")
            labels, positions, ctxs, blanks = [], [], [], []
            computed = None
            if isinstance(lst, list) and lst:
                tot = 0.0
                okp = True
                for e in lst:
                    raw, cx = cell_ctx(rel, e["line"])
                    ctxs.append(cx)
                    v = parse_num(raw) if raw is not None else None
                    pr = parse_num(e.get("printed", "x"))
                    if v is None or pr is None or abs(v - pr) > 0.5:
                        okp = False
                    cells, lines = row_of(rel, e["line"])
                    labels.append((cells[0] if cells else None, e["label"]))
                    if e["line"] in lines:
                        idx = lines.index(e["line"])
                        positions.append((idx, len(cells)))
                    if v is not None:
                        if "sign" in e:
                            tot += e["sign"] * v / scale
                        else:
                            tot += e["contribution_mn"] * (1 if v is not None else 0)
                rec["checks"]["printed_matches_xml"] = okp
                if all("sign" in e for e in lst):
                    computed = tot
                else:
                    t2 = 0.0
                    for e in lst:
                        v = parse_num(cell_at(rel, e["line"]))
                        pv = parse_num(e["printed"])
                        if v is None or pv is None:
                            t2 = None
                            break
                        sg = 1 if (e["contribution_mn"] * pv) >= 0 else -1
                        t2 += sg * v / scale
                    computed = t2
            else:
                ln = c["xml_line"]
                lns = ln if isinstance(ln, list) else [ln]
                vals = []
                for l in lns:
                    raw, cx = cell_ctx(rel, l)
                    ctxs.append(cx)
                    vals.append(0.0 if (raw is not None and raw.strip() == "") else (parse_num(raw) if raw is not None else None))
                    if raw is not None and raw.strip() == "":
                        blanks.append(l)
                    cells, lines = row_of(rel, l)
                    labels.append((cells[0] if cells else None, ""))
                    if l in lines:
                        positions.append((lines.index(l), len(cells)))
                if len(lns) == 1:
                    computed = vals[0] / scale if vals[0] is not None else None
                else:
                    computed = None
                    if all(v is not None for v in vals):
                        for signs in itertools.product((1, -1), repeat=len(vals)):
                            s = sum(sg * v for sg, v in zip(signs, vals)) / scale
                            if abs(s - new) <= 0.5 + 1e-6:
                                computed = s
                                break
                        if computed is None:
                            computed = float("nan")
            tol = 0.5 if (su == "백만원" or su is None) else 1e-5
            rec["computed"] = computed
            rec["checks"]["value_matches_new"] = computed is not None and computed == computed and abs(computed - new) <= max(tol, 1e-5)
            rec["labels"] = labels
            rec["contexts"] = ctxs
            rec["blank_cells_as_zero"] = blanks
            cx_ok = all((cx is None) or (cx.startswith("PFY") and cx.endswith("SeparateMember") and re.match(r"PFY\d{4}d(TQA|HYA|FQA|FY)_", cx)) for cx in ctxs)
            rec["checks"]["context_prior_cumulative_separate"] = cx_ok
            rec["positions"] = positions
            for p in positions:
                pos_stat[(code, q)][p] += 1
            ok = all(rec["checks"].values())
            if ok:
                n_ok += 1
            else:
                res["problems"].append(rec)
            res["cells"].append(rec)
        res["per_company"][code] = {"cells": len(plan["cells"]), "all_checks_ok": n_ok}
        txt.append(f"{code}: cells {len(plan['cells'])}, all checks ok {n_ok}")
    txt.append("")
    txt.append("cell position inside the <TR> (idx, ncells) per bucket (must be one dominant position; the prior-period cumulative column):")
    for k, cnt in sorted(pos_stat.items()):
        txt.append(f"  {k[0]} {k[1]}: {dict(cnt)}")
    txt.append("")
    nctx = Counter(("none" if cx is None else cx.split("_")[0]) for r in res["cells"] for cx in r["contexts"])
    txt.append("ACONTEXT of the cited cells: " + json.dumps(dict(nctx), ensure_ascii=False))
    txt.append("cells with blank cell(s) counted as 0: " + json.dumps([(r["code"], r["q"], r["item"], r["blank_cells_as_zero"]) for r in res["cells"] if r["blank_cells_as_zero"]], ensure_ascii=False))
    txt.append(f"problems: {len(res['problems'])}")
    for p in res["problems"][:60]:
        txt.append("  " + json.dumps({k: p[k] for k in ("code", "q", "item", "new", "old", "computed", "checks", "labels")}, ensure_ascii=False)[:700])
    (OUT / "e19_verify_plans.txt").write_text("\n".join(txt) + "\n", encoding="utf-8", newline="\n")
    (OUT / "e19_verify_plans.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(txt[:12]))


if __name__ == "__main__":
    main()
