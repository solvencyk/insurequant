# -*- coding: utf-8 -*-
"""e21 INDEPENDENT re-read of EVERY planned cell (own regex code; imports NOTHING from e21_* / mlib / scripts) against the raw filing lines the plan cites.
For each cited cell: the physical line is opened, the printed number is re-parsed (parentheses = negative, '-' = 0), the TR is re-assembled from raw lines and its label / numeric position / ACONTEXT are
re-derived, the unit is read from the nearest '(단위 : ...)' above, the table's section (separate vs consolidated) is read from the nearest <TITLE>, the signed sum / scale (원 -> 백만원, 억원) is recomputed and
compared with the plan value; the HEAD master is compared with the plan `old`; operands, seam evidence, gold classification evidence and the apply contract are re-checked; identities of the merged vectors
are re-computed.  Writes e21_verify.txt / e21_verify.json next to this file (exit code 1 when anything fails)."""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / "e21_plan.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
_cache = {}


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ").replace("\xa0", " ")).strip()


def parse_num(t):
    t = (t or "").strip().replace(",", "").replace(" ", "")
    if t in ("", ):
        return None
    if t in ("-", "\u2212"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t2 = t.strip("()")
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


def git_json(rel):
    return json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


# ------------------------------------------------------------------------------------------------ raw TR assembly (independent implementation)
def tr_bounds(L, ln):
    i = ln - 1
    while i > 0 and not L[i].lstrip().upper().startswith("<TR"):
        i -= 1
    j = ln - 1
    while j < len(L) - 1 and not L[j].lstrip().upper().startswith("</TR"):
        j += 1
    return i, j


def cells_of_tr(L, i, j):
    """[(text, text_line, ctx)] of the TR spanning lines i..j (0-based, inclusive)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            ctxm = re.search(r'ACONTEXT="([^"]*)"', m.group(2))
            ctx = ctxm.group(1) if ctxm else None
            rest = m.group(3)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append((clean(rest), k + 1, ctx))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", L[q], re.I):
                    t = clean(L[q])
                    if t:
                        buf.append(t)
                        if tl is None:
                            tl = q + 1
                    q += 1
                out.append((" ".join(buf).strip(), tl or (k + 1), ctx))
                k = q
        k += 1
    return out


def unit_above(L, ln, span=5000):
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


def title_above(L, ln):
    for k in range(ln - 1, 0, -1):
        s = L[k]
        if s.startswith("<TITLE"):
            return clean(s), k + 1
        m = re.match(r"^<!-- ===== \d+: (.*?) ===== -->", s)
        if m:
            return m.group(1), k + 1
    return "", 0


def norm(s):
    s = (s or "").replace("\u3000", "").replace(" ", "").replace("\xa0", "")
    s = re.sub(r"^([\u2160-\u2169]|[IVX]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    s = re.sub(r"^\d+\)", "", s)
    s = re.sub(r"^[ivx]+\)", "", s, flags=re.I)
    s = re.sub(r"\(주[^)]*\)", "", s)
    return s.replace("(손실)", "").replace("(수익)", "").replace("(이익)", "")


def plan_row_label(label):
    """descriptive plan label -> the row-label text to look for.  A bracket suffix is the row label only when it holds a Korean row text (LOB readers); capture / column hints are dropped."""
    m = re.search(r"\[([^\]@]+)", label)
    if m:
        inner = m.group(1).strip()
        if re.search(r"[가-힣]", inner) and not re.search(r"(CSM|col |합계$|value cells)", inner):
            return inner
    return re.sub(r"\s*\[.*$", "", label).strip()


def verify_part(rel, p, role_ctx=None, expect_pos=None, skip_label=False, allow_consolidated=False):
    """-> (ok, info) for one cited cell"""
    L = lines_of(rel)
    ln = p["line"]
    i, j = tr_bounds(L, ln)
    cells = cells_of_tr(L, i, j)
    hit = [c for c in cells if c[1] == ln]
    if not hit:
        return False, dict(problem="no cell text on the cited line", line=ln)
    text, _tl, ctx = hit[0]
    v = parse_num(text)
    pr = parse_num(p["printed"])
    problems = []
    if v is None or pr is None or abs(v - pr) > 1e-9 or text.replace(" ", "") != p["printed"].replace(" ", ""):
        problems.append(f"printed {p['printed']!r} != raw {text!r}")
    # label: the leading non-numeric cells of the row
    lab_cells = []
    for c in cells:
        if c[1] == ln:
            break
        if re.search(r"[가-힣A-Za-z]", c[0]) and parse_num(c[0]) is None:
            lab_cells.append(c[0])
    lab_all = " ".join(lab_cells)
    # numeric position among the numeric / dash cells of the row
    seq = [c for c in cells if c[0].strip() != "" and parse_num(c[0]) is not None]
    pos = [c[1] for c in seq].index(ln) if ln in [c[1] for c in seq] else None
    pl = norm(plan_row_label(p.get("label", "")))
    rl = norm(lab_all)
    if pl and len(pl) >= 2 and not skip_label:
        if not ((pl in rl) or (rl in pl and len(rl) >= 2)):
            problems.append(f"label {p.get('label')!r} !~ row {lab_all[:60]!r}")
    # unit
    u, uln = unit_above(L, ln)
    if u != p.get("unit"):
        problems.append(f"unit {u} (L{uln}) != plan {p.get('unit')}")
    # section
    title, tln = title_above(L, ln)
    tnorm = norm(title)
    if re.search(r"연결재무제표", tnorm) and not allow_consolidated:
        problems.append(f"section is consolidated: {title!r}")
    if role_ctx is not None and ctx and "포괄손익계산서" in tnorm:
        if not re.match(role_ctx, ctx) or "SeparateMember" not in ctx:
            problems.append(f"ACONTEXT {ctx[:60]!r} !~ {role_ctx}")
    if expect_pos is not None and pos is not None and pos != expect_pos:
        problems.append(f"position {pos} != expected {expect_pos}")
    return (not problems), dict(problem="; ".join(problems) if problems else None, value=v, ctx=ctx, pos=pos, n=len(seq), label=lab_all[:60], unit=u, title=title[:40])


SCALE = {"원": 1e6, "천원": 1e3, "백만원": 1.0}
CSM_SCALE = {"원": 1e8, "천원": 1e5, "백만원": 100.0}


def contrib(p):
    v = parse_num(p["printed"])
    sc = SCALE[p["unit"]]
    return p["sign"] * (abs(v) if p.get("abs") else v) / sc


def ctx_pattern(meta, quarter, kind_3m=False):
    y = int(quarter[:4])
    if meta["role"] == "cur":
        who, yy = "C", y
    else:
        who, yy = "P", y
    suf = r"(FQQ|HYQ|TQQ)" if kind_3m else r"(FQA|HYA|TQA|FY)"
    return rf"^{who}FY{yy}d{suf}_"


def main():
    res = dict(problems=[], counts=Counter())
    txt = []
    pl_head = git_json("PL_breakdown.json")
    HM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in pl_head}
    HD = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in pl_head}
    csm_head = git_json("CSM_waterfall.json")
    CM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in csm_head}
    gold = git_json("data/_gold/user_pl_cells.json")
    goldc = git_json("data/_gold/user_csm_cells.json")
    G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in goldc["set"]}
    CON = PLAN["apply_contract"]
    plan_val = {}
    for b in PLAN["buckets"]:
        for c in b["cells"]:
            plan_val[(c["code"], c["item"], c["quarter"])] = c["new"]
    pos_stat = defaultdict(Counter)
    n_cells = n_ok = 0
    for b in PLAN["buckets"]:
        code, q, meta = b["code"], b["quarter"], b["meta"]
        bad_here = 0
        for c in b["cells"]:
            n_cells += 1
            key = (code, c["item"], q)
            rec = dict(code=code, q=q, item=c["item"], new=c["new"], old=c["old"], problems=[])
            ho = HM.get(key)
            if (ho is None) != (c["old"] is None) or (ho is not None and abs(ho - c["old"]) > 5e-7):
                rec["problems"].append(f"old {c['old']} != HEAD master {ho}")
            if (key in G) != bool(c["gold_cell"]):
                rec["problems"].append("gold_cell flag differs from HEAD gold")
            tot = 0.0
            for p in c["parts"]:
                kind_ctx = ctx_pattern(meta, q) if meta["fmt"] == "atoc" else None
                ok, info = verify_part(c["xml_file"], p, role_ctx=kind_ctx, expect_pos=p.get("col"))
                if not ok:
                    rec["problems"].append(f"L{p['line']}: {info['problem']}")
                if info.get("pos") is not None:
                    pos_stat[(code, q)][(info["pos"], info["n"])] += 1
                tot += contrib(p)
            if c.get("abs_of_sum"):
                tot = abs(tot)
            for o in c["operands"]:
                if o["source"] == "master HEAD":
                    mv = HM.get((code, o["item"], q))
                    if mv is None or abs(mv - o["value"]) > 5e-7:
                        rec["problems"].append(f"operand {o['item']} {o['value']} != HEAD master {mv}")
                else:
                    pv = plan_val.get((code, o["item"], q))
                    if pv is None or abs(pv - o["value"]) > 1e-6:
                        rec["problems"].append(f"operand {o['item']} {o['value']} != plan cell {pv}")
                tot += o["sign"] * o["value"]
            tol = 2e-5 if all(p["unit"] == "원" for p in c["parts"]) and c["parts"] else 1e-4
            if abs(tot - c["new"]) > tol:
                rec["problems"].append(f"recomputed {tot} != plan {c['new']}")
            if rec["problems"]:
                res["problems"].append(rec)
                bad_here += 1
            else:
                n_ok += 1
        res["counts"][f"{code} {q}"] = (len(b["cells"]), len(b["cells"]) - bad_here)
        txt.append(f"{code} {q}: cells {len(b['cells'])}, all checks ok {len(b['cells']) - bad_here}")
    txt.append("position of the cited cell among the numeric cells of its row (position, n) per bucket:")
    for k, cnt in sorted(pos_stat.items()):
        txt.append(f"  {k[0]} {k[1]}: {dict(cnt)}")
    txt.append(f"PL cells: {n_cells}, all checks ok {n_ok}")

    # ---------------------------------------------------------------------------------------- original prints of the gold overlaps
    n_op = n_op_ok = 0
    for b in PLAN["buckets"]:
        for c in b["cells"]:
            op = c.get("original_print")
            if not op:
                continue
            n_op += 1
            tot, probs = 0.0, []
            rel = op["file"]
            for p in op["lines"]:
                ok, info = verify_part(rel, p)
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                tot += contrib(p)
            g = G[(c["code"], c["item"], c["quarter"])]["값"]
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
                probs.append(f"class A_basis but separate original print {tot} != latest {c['new']}")
            if probs:
                res["problems"].append(dict(code=c["code"], q=c["quarter"], item=c["item"], problems=["original_print: " + "; ".join(probs)]))
            else:
                n_op_ok += 1
    txt.append(f"original-print checks (gold overlaps): {n_op}, ok {n_op_ok}")

    # ---------------------------------------------------------------------------------------- seams: printed 3-month evidence, Q3 comparatives, pins
    adopted_cum = dict(plan_val)

    def cum_after(code, i, q):
        return adopted_cum.get((code, i, q), HM.get((code, i, q)))

    n_s = n_s_ok = 0
    for s in PLAN["seams"]:
        p3 = s.get("printed_3m")
        if p3:
            n_s += 1
            tot, probs = 0.0, []
            for p in p3["parts"]:
                ok, info = verify_part(p3["file"], p, role_ctx=rf"^PFY{int(s['quarter'][:4])}d(FQQ|HYQ|TQQ)_")
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                tot += contrib(p)
            if abs(tot - p3["value"]) > 1e-5:
                probs.append(f"3m recomputed {tot} vs plan {p3['value']}")
            q = s["quarter"]
            pq = f"{q[:4]}.{int(q[5]) - 1}Q"
            D = cum_after(s["code"], s["item"], q)
            Dp = cum_after(s["code"], s["item"], pq)
            if D is None or Dp is None or abs((D - Dp) - s["derived_after"]) > 1e-5:
                probs.append("derived_after is not cum(q) - cum(q-1)")
            if probs:
                res["problems"].append(dict(code=s["code"], q=s["quarter"], item=s["item"], problems=["seam 3m: " + "; ".join(probs)]))
            else:
                n_s_ok += 1
        qc = s.get("q3_comparative")
        if qc:
            tot, probs = 0.0, []
            for p in qc["parts"]:
                ok, info = verify_part(qc["file"], p)
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                tot += contrib(p)
            if abs(tot - qc["comparative"]) > 1e-5:
                probs.append(f"Q3 comparative recomputed {tot} vs plan {qc['comparative']}")
            if probs:
                res["problems"].append(dict(code=s["code"], q=s["quarter"], item=s["item"], problems=["Q3 comparative: " + "; ".join(probs)]))
    txt.append(f"seam printed-3-month re-reads: {n_s}, ok {n_s_ok}")
    nd = {tuple(x) for x in gold["null_dangi"]["cells"]}
    sd = {(x[0], x[1], int(x[2])): x for x in gold["set_dangi"]["cells"]}
    for c, q, i in CON["null_dangi_remove"]:
        if (c, q, i) not in nd:
            res["problems"].append(dict(code=c, q=q, item=i, problems=["null_dangi_remove: pin not in HEAD gold"]))
        D = None if cum_after(c, i, q) is None or cum_after(c, i, f"{q[:4]}.{int(q[5]) - 1}Q") is None else cum_after(c, i, q) - cum_after(c, i, f"{q[:4]}.{int(q[5]) - 1}Q")
        if D is None:
            res["problems"].append(dict(code=c, q=q, item=i, problems=["null_dangi_remove: single quarter would not be derivable"]))
    for c, q, i in CON["set_dangi_remove"]:
        pin = sd.get((c, q, i))
        D = cum_after(c, i, q) - cum_after(c, i, f"{q[:4]}.{int(q[5]) - 1}Q")
        if pin is None or abs(float(pin[3]) - D) > 1e-6:
            res["problems"].append(dict(code=c, q=q, item=i, problems=[f"set_dangi_remove: pinned {None if pin is None else pin[3]} != derived {D}"]))
    for x in CON["null_dangi_add"]:
        c, q, i = x
        if tuple(x) in nd or (c, q, i) in sd:
            res["problems"].append(dict(code=c, q=q, item=i, problems=["null_dangi_add: already pinned in HEAD gold"]))
        if q[5] != "4":
            res["problems"].append(dict(code=c, q=q, item=i, problems=["null_dangi_add: not a Q4 single quarter"]))
    for x in CON["set_dangi_add"]:
        c, q, i, val, src = x
        if (c, q, i) in sd or (c, q, i) in nd:
            res["problems"].append(dict(code=c, q=q, item=i, problems=["set_dangi_add: already pinned"]))
        m = re.match(r"(data/[^:]+): (.*)", src)
        tot = 0.0
        for mm in re.finditer(r"L(\d+) \[([^\]]*)\] (\S+)", m.group(2)):
            ln = int(mm.group(1))
            L = lines_of(m.group(1))
            ii, jj = tr_bounds(L, ln)
            cs = [cc for cc in cells_of_tr(L, ii, jj) if cc[1] == ln]
            if not cs or parse_num(cs[0][0]) is None or abs(parse_num(cs[0][0]) - parse_num(mm.group(3))) > 1e-9:
                res["problems"].append(dict(code=c, q=q, item=i, problems=[f"set_dangi_add: L{ln} {cs[0][0] if cs else None} != {mm.group(3)}"]))
    txt.append(f"contract dangi: null_remove {len(CON['null_dangi_remove'])}, set_remove {len(CON['set_dangi_remove'])}, null_add {len(CON['null_dangi_add'])}, set_add {len(CON['set_dangi_add'])}")

    # ---------------------------------------------------------------------------------------- CSM cells
    n_c = n_c_ok = 0
    CSM_KEYS = {1: ("기초",), 2: ("신계약", "최초인식", "처음인식"), 3: ("보험금융",), 4: ("추정치의변동", "조정하는변동", "조정하는추정치"), 5: ("상각", "당기인식분", "제공한서비스", "서비스의이전", "현행서비스", "인식한보험계약마진"), 6: ("말",)}
    for cb in PLAN["csm_buckets"]:
        code, q = cb["code"], cb["quarter"]
        for c in cb["cells"]:
            n_c += 1
            probs = []
            ho = CM.get((code, c["item"], q))
            if (ho is None) != (c["old"] is None) or (ho is not None and abs(ho - c["old"]) > 1e-9):
                probs.append(f"old {c['old']} != HEAD CSM master {ho}")
            exact = 0.0
            for p in c["parts"]:
                if p["printed"].strip() == "" and p["unit"] == "원":
                    continue            # blank cell of a wide row (counts as 0)
                rel = c["src"].split(" ")[0]
                ok, info = verify_part(rel, p, skip_label=True)
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                else:
                    lab = norm(info["label"])
                    keys = CSM_KEYS[c["item"]]
                    if not any(norm(k) in lab for k in keys):
                        probs.append(f"L{p['line']}: row label {info['label']!r} has none of {keys}")
                v = parse_num(p["printed"])
                exact += p["sign"] * v / CSM_SCALE[p["unit"]]
            if c["parts"] and not c.get("derived"):
                if abs(exact - c["exact"]) > 1e-4:
                    probs.append(f"exact recomputed {exact} != plan {c['exact']}")
                st = round(exact, 2) if cb["two_dp"] else round(exact, 1)
                if abs(st - c["new"]) > 1e-9 and abs(c["new"] - exact) > (0.0051 if cb["two_dp"] else 0.0501):
                    probs.append(f"stored {c['new']} vs exact {exact}")
            n_c_ok += 0 if probs else 1
            if probs:
                res["problems"].append(dict(code=code, q=q, item=c["item"], problems=["CSM: " + "; ".join(probs)]))
        # closure of the merged vector
        merged = [next((cc["new"] for cc in cb["cells"] if cc["item"] == i), cb["old"][i - 1]) for i in range(1, 7)]
        resid = merged[0] + merged[1] + merged[2] + merged[3] + merged[4] - merged[5]
        if abs(resid) > 0.15 or abs(resid - cb["closure_resid"]) > 1e-3:
            res["problems"].append(dict(code=code, q=q, item=0, problems=[f"CSM closure residual {resid}"]))
    txt.append(f"CSM cells: {n_c}, ok {n_c_ok}")

    # ---------------------------------------------------------------------------------------- CSM gold class evidence (롯데 2023.1Q)
    for k, v in PLAN.get("csm_gold_class", {}).items():
        code, item, q = k.split("|")
        e = v["evidence"]
        if e.get("liab_close") and e.get("net_close"):
            rel = [cb for cb in PLAN["csm_buckets"] if cb["code"] == code and cb["quarter"] == q][0]["file"].split(" ")[0]
            for key in ("liab_close", "net_close"):
                ln = e[key]["line"]
                L = lines_of(rel)
                ii, jj = tr_bounds(L, ln)
                cs = [cc for cc in cells_of_tr(L, ii, jj) if cc[1] == ln]
                if not cs or abs(parse_num(cs[0][0]) / 100.0 - e[key]["eok"]) > 1e-6:
                    res["problems"].append(dict(code=code, q=q, item=int(item), problems=[f"csm_gold_class evidence {key} L{ln} mismatch"]))
        old_g = GC.get((code, int(item), q))
        if old_g is None:
            res["problems"].append(dict(code=code, q=q, item=int(item), problems=["csm_gold_class: gold cell missing in HEAD"]))
    txt.append(f"CSM gold class evidence: {len(PLAN.get('csm_gold_class', {}))} cells")

    # ---------------------------------------------------------------------------------------- contract vs plan vs HEAD
    pl_keys = {k for k in plan_val}
    con_keys = {(e["code"], e["item"], e["quarter"]) for e in CON["gold_new"] + CON["gold_replace"]}
    if pl_keys != con_keys:
        res["problems"].append(dict(code="*", q="*", item=0, problems=[f"contract cells != plan cells: only-plan {sorted(pl_keys - con_keys)[:5]} only-contract {sorted(con_keys - pl_keys)[:5]}"]))
    for e in CON["gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        if G.get(k) != e["old_entry"]:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["gold_replace: old_entry != HEAD gold"]))
        if abs(e["was"] - G[k]["값"]) > 1e-12:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["gold_replace: was != HEAD gold value"]))
    for e in CON["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        if k in G:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["gold_new: key already in HEAD gold"]))
        if k not in HM and False:
            pass
        if (HM.get(k) is None) != (e["was"] is None) or (HM.get(k) is not None and abs(HM[k] - e["was"]) > 5e-7):
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=[f"gold_new: was {e['was']} != HEAD master {HM.get(k)}"]))
        if k not in HM:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["gold_new: master row absent (the builder upsert needs an existing row)"]))
    for e in CON["csm_gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        if k in GC:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["csm_gold_new: key already in HEAD CSM gold"]))
        if k not in CM:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["csm_gold_new: CSM master row absent"]))
    for e in CON["csm_gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        if GC.get(k) != e["old_entry"]:
            res["problems"].append(dict(code=k[0], q=k[2], item=k[1], problems=["csm_gold_replace: old_entry != HEAD CSM gold"]))

    # ---------------------------------------------------------------------------------------- identities of the merged vectors (recomputed here)
    n_id = n_id_bad = 0
    for b in PLAN["buckets"]:
        code, q = b["code"], b["quarter"]
        v = {i: HM.get((code, i, q)) for i in range(1, 33)}
        for c in b["cells"]:
            v[c["item"]] = c["new"]
        exact = b["meta"]["unit"] == "원" and b["kind"] in ("life",)
        checks = []
        S = lambda *xs: None if any(x is None for x in xs) else sum(xs)  # noqa: E731
        checks.append(("20=1+17", v.get(20), S(v.get(1), v.get(17))))
        checks.append(("22=20+21", v.get(22), S(v.get(20), v.get(21))))
        checks.append(("31=24+25", v.get(31), S(v.get(24), v.get(25))))
        oci = [v[i] for i in (26, 27, 28, 29, 30, 32) if v.get(i) is not None]
        checks.append(("25=sum(OCI parts)", v.get(25), sum(oci) if oci else None))
        checks.append(("17=18+19", v.get(17), S(v.get(18), v.get(19))))
        if v.get(3) is not None and None not in (v.get(4), v.get(5), v.get(6), v.get(7)):
            checks.append(("3=4+5+6+7", v[3], v[4] + v[5] + v[6] + v[7]))
        if v.get(8) is not None and None not in (v.get(9), v.get(10), v.get(11), v.get(12)):
            checks.append(("8=9+10+11+12", v[8], v[9] + v[10] + v[11] + v[12]))
        if v.get(2) is not None and v.get(3) is not None and v.get(8) is not None:
            checks.append(("2=3+8", v[2], v[3] + v[8]))
        for name, l, r in checks:
            if l is None or r is None:
                continue
            n_id += 1
            tol = 0.002 if exact else 0.5 * 7 + 0.002
            if abs(l - r) > tol:
                n_id_bad += 1
                res["problems"].append(dict(code=code, q=q, item=0, problems=[f"identity {name}: {l} vs {r} (resid {l - r:+.4f}, tol {tol})"]))
    txt.append(f"identity checks on the merged vectors: {n_id}, outside tolerance {n_id_bad}")
    txt.append(f"problems: {len(res['problems'])}")
    for p in res["problems"][:80]:
        txt.append("  " + json.dumps(p, ensure_ascii=False, default=str)[:600])
    (HERE / "e21_verify.txt").write_text("\n".join(txt) + "\n", encoding="utf-8", newline="\n")
    (HERE / "e21_verify.json").write_text(json.dumps(dict(problems=res["problems"], counts={k: list(v) for k, v in res["counts"].items()}), ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    print("\n".join(txt[:6]))
    print("\n".join(txt[-6:]))
    sys.exit(1 if res["problems"] else 0)


if __name__ == "__main__":
    main()
