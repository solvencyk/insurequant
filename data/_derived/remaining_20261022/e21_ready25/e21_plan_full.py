# -*- coding: utf-8 -*-
"""e21 full plan: PL buckets (e21_plan) + gold classification + seams + CSM buckets + apply contract.  READ-ONLY on every repo file.  Writes e21_plan.json + e21_plan_report.txt next to this file.
python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe   (script file only, stdin /dev/null)"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm as C  # noqa: E402
import e21_csm2 as C2  # noqa: E402
import e21_plan as PL  # noqa: E402
import e21_plan_lib as P  # noqa: E402
import e21_raw as W  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
EV, EVREL, TIER1 = PL.EV, PL.EVREL, PL.TIER1
ITEM_NAME, CSM_NAME, LIVE_NOTE = PL.ITEM_NAME, PL.CSM_NAME, PL.LIVE_NOTE
TICKET = "20261023T0300Z"
# original-vintage prints of the owner-gold cells.  key -> dict(gold_src=[(printed text, label substring, sign, abs?)]  the print(s) that equal the gold value (any section),
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
UNIT_RE = re.compile(r"단위\s*[:：]?\s*(백만원|천원|원)")


def unit_of_line(lines, ln, span=4000):
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = UNIT_RE.search(re.sub(r"<[^>]+>", "", lines[k]))
        if m:
            return m.group(1), k + 1
    raise RuntimeError(f"unit above L{ln} not found")


def printed_cell(lines, ln, text):
    """exact cell text printed on physical line ln that contains `text` (keeps the parentheses)"""
    m = re.search(r">\s*(\(?-?" + re.escape(text) + r"\)?)\s*<", lines[ln - 1])
    if not m:
        raise RuntimeError(f"L{ln}: {text!r} not found as a cell text")
    return m.group(1)


def print_record(code, q, spec, sep_only):
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


def fmt(v, nd=1):
    return "None" if v is None else f"{v:,.{nd}f}"


def build():
    S = PL.build_pl_buckets()
    plan, master, masterd, csm_m = S["plan"], S["master"], S["masterd"], S["csm_m"]
    GOLD, GOLDC, NULLD, SETD = S["GOLD"], S["GOLDC"], S["NULLD"], S["SETD"]
    cand, cand_csm, cells_all, bucket_by = S["cand"], S["cand_csm"], S["pl_cells_all"], S["bucket_by"]
    gold, gold_csm = S["gold"], S["gold_csm"]
    LOG = list(S["LOG"])
    OUT = []

    # ------------------------------------------------------------------------------------------------ 0. masked-gold guard
    sys.path.insert(0, str(PL.ROOT / "scripts"))
    import validate_data_contract as GV
    src_pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((PL.ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))}
    OUT.append("== 0. new gold cells that would be MASKED (value == builder source within the census tolerance) -> dropped (a masked cell needs a ledger pin; ticket: no new mask cells / no new pins)")
    plan.setdefault("findings", [])
    for b in plan["buckets"]:
        keep = []
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if k not in GOLD and GV.gold_overlay_verdict(c["new"], src_pl.get(k)) in GV._GOLD_MASKED:
                OUT.append(f"   dropped {k}: new {c['new']} vs builder source {src_pl.get(k, {}).get('값')} -> masked")
                b["dropped"].append(dict(item=c["item"], old=c["old"], new=c["new"], cls="masked", reason="would be a masked gold cell (== builder source); a new ledger pin is forbidden by the ticket", in_cand=c["cand_new"] is not None))
                plan["findings"].append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], kind="masked new gold cell not loaded",
                                             text=f"latest comparative {c['new']} equals the builder source value; master stays {c['old']} (the _zero_other_expense heuristic blanks it); loading it needs a new ledger pin"))
                cells_all.pop((c["code"], c["quarter"], c["item"]), None)
                continue
            keep.append(c)
        b["cells"] = keep
    # ------------------------------------------------------------------------------------------------ 1. value differences against the measure-phase candidates
    OUT.append("== A. adopted cells whose value differs from the measure-phase candidate")
    n_adopt = sum(len(b["cells"]) for b in plan["buckets"])
    for b in plan["buckets"]:
        for c in b["cells"]:
            if c["cand_new"] is not None and abs(c["cand_new"] - c["new"]) > 1e-3:
                OUT.append(f"   {c['code']} {c['quarter']} i{c['item']}: mine {c['new']} vs candidate {c['cand_new']} (diff {c['new'] - c['cand_new']:+.6f})")
    OUT.append(f"   adopted PL cells {n_adopt} (measure-phase candidates {len(cand)}); candidate items not adopted by bucket: " +
               str({f"{b['code']} {b['quarter']}": b["only_cand"] for b in plan["buckets"] if b["only_cand"]}))

    # ------------------------------------------------------------------------------------------------ 2. owner-gold classification (re-done per cell from the ORIGINAL filing)
    OUT.append("== B. owner-gold cells in the adopted set: gold vs original print vs latest comparative")
    held, gold_replace, gold_new = [], [], []
    gold_class = {}
    for b in plan["buckets"]:
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if k not in GOLD:
                continue
            g = GOLD[k]
            if (c["code"], c["quarter"], c["item"]) not in ORIG_PRINT:
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
            OUT.append(f"   {k}: gold {g['값']} | gold-source print {gs['value']} ({[(p['line'], p['printed']) for p in gs['lines']]}) | separate original print {op['value']} ({op['unit']}; lines {[(p['line'], p['printed'], p['label']) for p in op['lines']]}) | latest {c['new']} -> class {cls}")
            if cls == "B":
                held.append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], reason="owner gold is neither the original print nor the latest comparative (class B) -> bucket held"))

    # ------------------------------------------------------------------------------------------------ 3. single-quarter seams
    OUT.append("== C. single-quarter (값_당분기) seam analysis")
    adopted = {(c["code"], c["item"], c["quarter"]): c["new"] for b in plan["buckets"] for c in b["cells"]}
    stmts = {}

    def stmt(code, fy):
        if (code, fy) not in stmts:
            stmts[(code, fy)] = R.Stmt(code, fy)
        return stmts[(code, fy)]

    def cum_after(code, i, q):
        return adopted.get((code, i, q), master.get((code, i, q)))

    def prevq(q):
        return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"

    def restated(code, q, i):
        """is cum (code, i, q) on a restated basis, i.e. does the later filing's comparative differ from the ORIGINAL print?  original print = HEAD master unless an earlier gold adoption replaced it (gold `was`)"""
        g = GOLD.get((code, i, q))
        if g is not None and g.get("was") is not None and abs(g["값"] - g["was"]) > 1.0:
            return True, f"gold {g['값']} replaced the original {g['was']}"
        if i not in TIER1:
            if code != "KR0010":
                return False, "LOB item of a non-KB company: not checked directly"
            r3 = T.kb_read(code, q)
            old = master.get((code, i, q))
            if i in r3 and old is not None:
                return abs(r3[i]["val"] - old) > 1.5, f"LOB note comparative {round(r3[i]['val'], 6)} vs master {old}"
            return False, "LOB item not read"
        st = stmt(code, P.later_fy(q))
        v = R.read_vector(st, "prior", "cum")
        if i not in v or (i in (26, 27, 28, 29, 30) and v[i].get("absent")):
            return False, "item not printed"
        comp = sum(p.sign * p.val_mn for p in v[i]["parts"])
        old = master.get((code, i, q))
        if old is None:
            return False, "master empty"
        band = 2e-5 if st.unit == "원" else 1.5
        EVID[(code, q, i)] = dict(file=st.rel, unit=st.unit, parts=[P.pdict(p, st.unit) for p in v[i]["parts"]], comparative=round(comp, 6), master=old)
        return abs(comp - old) > band, f"comparative {round(comp, 6)} vs master {old}"

    EVID = {}
    null_add, null_remove, set_add, set_remove = [], [], [], []
    seams = []
    by_code = defaultdict(set)
    for (code, i, q) in adopted:
        by_code[code].add((i, q))
    for code, lst in sorted(by_code.items()):
        touched = set()
        for (i, q) in lst:
            touched.add((i, q))
            if int(q[5]) < 4:
                touched.add((i, f"{q[:4]}.{int(q[5]) + 1}Q"))
        for (i, qq) in sorted(touched, key=lambda x: (x[1], x[0])):
            n = int(qq[5])
            pq = prevq(qq)
            if n == 1:
                continue
            cur, prev = cum_after(code, i, qq), cum_after(code, i, pq)
            D = None if (cur is None or prev is None) else cur - prev
            live = masterd.get((code, i, qq))
            rec = dict(code=code, quarter=qq, item=i, derived_after=D, live_dangi=live, cur_adopted=(code, i, qq) in adopted, prev_adopted=(code, i, pq) in adopted, existing_null=(code, qq, i) in NULLD,
                       existing_set=(code, qq, i) in SETD)
            if D is None:
                rec.update(cls="derived_none", proposal="none")
                seams.append(rec)
                continue
            if n in (2, 3):
                if i not in TIER1:
                    rec.update(cls="lob_item_not_checked_directly", proposal="none")
                    seams.append(rec)
                    continue
                st = stmt(code, P.later_fy(qq))
                v3 = R.read_vector(st, "prior", "3m")
                p3 = round(sum(p.sign * p.val_mn for p in v3[i]["parts"]), 6)
                tol = 3 * 2e-5 if st.unit == "원" else 3.0
                rec["printed_3m"] = dict(value=p3, file=st.rel, unit=st.unit, parts=[P.pdict(p, st.unit) for p in v3[i]["parts"]])
                rec["diff_vs_printed_3m"] = round(D - p3, 6)
                if abs(D - p3) <= tol:
                    rec.update(cls="consistent", proposal="none")
                    if rec["existing_set"]:
                        pinned = float(SETD[(code, qq, i)][3])
                        rec["existing_set_value"] = pinned
                        if abs(pinned - D) <= 1e-6:
                            set_remove.append([code, qq, i])
                            rec["proposal"] = "remove_redundant_set_dangi"
                else:
                    rec.update(cls="seam", proposal="set_dangi")
                    parts = rec["printed_3m"]["parts"]
                    src = f"{st.rel}: " + " || ".join(f"L{p['line']} [{p['label']}] {p['printed']}" for p in parts) + \
                          f" (prior-year 3-month column printed in the {P.later_fy(qq)} report; the single quarter derived from the two cumulatives differs by {D - p3:+.6f})"
                    set_add.append([code, qq, i, p3, src])
                seams.append(rec)
                continue
            # n == 4: no printed 3-month column.  Rule: the single quarter is consistent iff the 9M cumulative (Q3) is on a restated basis too (restatement event before both prints);
            # if the annual cumulative is adopted while the 9M comparative is NOT restated, the two sit on different bases -> blank (owner rule 2026-10-22).
            if (code, i, qq) in adopted:
                rs, why = restated(code, pq, i)
                rs1, why1 = (rs, why) if i in TIER1 else restated(code, pq, 1)
                rec["q3_restated"] = rs
                rec["q3_evidence"] = why + ("" if i in TIER1 else f" | item-1 check: {why1}")
                ek = (code, pq, i if i in TIER1 else 1)
                if ek in EVID:
                    rec["q3_comparative"] = EVID[ek]
                if rs:
                    rec.update(cls="consistent_both_restated", proposal="none")
                    if rec["existing_null"]:
                        null_remove.append([code, qq, i])
                        rec["proposal"] = "remove_null_dangi"
                else:
                    rec.update(cls="seam_annual_vs_unrestated_9M", proposal="null_dangi")
                    if not rec["existing_null"]:
                        null_add.append([code, qq, i])
            else:
                # Q4 not adopted, Q3 adopted: consistent iff the Q4 print is on the restated basis (the later filing's comparative == master)
                rec.update(cls="q4_unchanged_q3_adopted", proposal="none")
                if i in TIER1:
                    st4 = stmt(code, P.later_fy(qq))
                    v4 = R.read_vector(st4, "prior", "cum")
                    if not (i in (26, 27, 28, 29, 30) and v4[i].get("absent")):
                        comp4 = sum(p.sign * p.val_mn for p in v4[i]["parts"])
                        m4 = master.get((code, i, qq))
                        rec["q4_comp_vs_master"] = [round(comp4, 6), m4]
                        band4 = 2e-5 if st4.unit == "원" else 1.5
                        if m4 is not None and abs(comp4 - m4) > band4:
                            rec.update(cls="q4_changed_but_not_adopted", proposal="none (finding)")
                            plan.setdefault("findings", []).append(dict(code=code, quarter=qq, item=i, kind="stale Q4 cumulative",
                                                                        text=f"master {m4} vs the {P.later_fy(qq)} comparative {round(comp4, 6)}; the cell is outside the READY set (not adopted); the single quarter is not pinned"))
            seams.append(rec)
    plan["seams"] = seams
    for r in seams:
        if r["cls"] in ("seam", "seam_annual_vs_unrestated_9M", "consistent_both_restated") or r["proposal"] != "none":
            OUT.append(f"   {r['code']} {r['quarter']} i{r['item']}: {r['cls']} -> {r['proposal']} (D={fmt(r['derived_after'], 6)}, printed3m={r.get('printed_3m', {}).get('value')}, live={r['live_dangi']}, {r.get('q3_evidence', '')})")
    ncons = sum(1 for r in seams if r["cls"] == "consistent")
    OUT.append(f"   seam table: {len(seams)} touched single-quarter cells; consistent with the printed 3-month column: {ncons}; by class: " +
               str({k: sum(1 for r in seams if r['cls'] == k) for k in sorted({r['cls'] for r in seams})}))

    # ------------------------------------------------------------------------------------------------ 4. CSM vectors
    OUT.append("== D. CSM vectors (latest comparative, separate basis)")
    csm_cells, csm_buckets = [], []
    readers = {("KR0003", "2023.1Q"): C2.lotte_csm, ("KR0003", "2024.1Q"): C2.lotte_csm, ("KR0003", "2024.2Q"): C2.lotte_csm, ("KR0003", "2024.3Q"): C2.lotte_csm,
               ("KR0079", "2024.1Q"): lambda q: C2.mirae_q1(), ("KR0079", "2024.2Q"): C2.mirae_wide, ("KR0079", "2024.3Q"): C2.mirae_wide,
               ("KR0001", "2023.1Q"): C.meritz_csm, ("KR0001", "2023.2Q"): C.meritz_csm, ("KR0068", "2023.1Q"): C.hanwha_csm, ("KR0068", "2023.2Q"): C.hanwha_csm, ("KR0068", "2023.3Q"): C.hanwha_csm}
    for code, q in PL.CSM_SPECS:
        res = readers[(code, q)](q)
        # precision of the stored row: 2 dp when the existing row is an owner-gold row at 2 dp, else the master's 1 dp
        two_dp = any((code, i, q) in GOLDC and abs(round(GOLDC[(code, i, q)]["값"], 1) - GOLDC[(code, i, q)]["값"]) > 1e-9 for i in range(1, 7))
        vec = res["vec"] if two_dp else res["vec1"]
        old = [csm_m.get((code, i, q)) for i in range(1, 7)]
        cb = dict(code=code, quarter=q, file=res["src"], two_dp=two_dp, vec_exact=[round(x, 6) for x in res["vec_exact"]], vec=vec, old=old, cells=[], dropped=[])
        for i in range(1, 7):
            o, nv = old[i - 1], vec[i - 1]
            tol = 0.0051 if (o is not None and abs(round(o, 1) - o) > 1e-9) else 0.0501
            if o is not None and abs(nv - o) <= tol:
                if (code, q, i) in cand_csm:
                    cb["dropped"].append(dict(item=i, old=o, new=nv, reason="equal to the master within the print rounding"))
                continue
            cd = cand_csm.get((code, q, i))
            cell = dict(code=code, quarter=q, item=i, item_name=CSM_NAME[i], old=o, new=nv, delta=None if o is None else round(nv - o, 6), exact=round(res["vec_exact"][i - 1], 6),
                        parts=res["cells"].get(i, []), derived=res["derived"].get(i), src=res["src"], cand_new=None if cd is None else cd["new"],
                        cand_equal=None if cd is None else abs(cd["new"] - nv) <= (0.0501 if not two_dp else 0.0201), gold_cell=((code, i, q) in GOLDC))
            cb["cells"].append(cell)
            csm_cells.append(cell)
        merged = [nv if any(c["item"] == i for c in cb["cells"]) else (old[i - 1] if old[i - 1] is not None else vec[i - 1]) for i, nv in enumerate(vec, 1)]
        cb["closure_resid"] = round(merged[0] + merged[1] + merged[2] + merged[3] + merged[4] - merged[5], 4)
        cb["cand_items"] = sorted(i for (c_, q_, i) in cand_csm if c_ == code and q_ == q)
        cb["only_cand"] = sorted(set(cb["cand_items"]) - {c["item"] for c in cb["cells"]})
        cb["only_mine"] = sorted({c["item"] for c in cb["cells"]} - set(cb["cand_items"]))
        if "check_group_row_5" in res:
            g = res["check_group_row_5"]
            cb["group_row_amort"] = g["contribution_eok"] if isinstance(g, dict) else g[0] / 100.0
        csm_buckets.append(cb)
        OUT.append(f"   {code} {q}: exact={cb['vec_exact']} stored={vec} old={old} cells {[c['item'] for c in cb['cells']]} cand {cb['cand_items']} only_cand={cb['only_cand']} only_mine={cb['only_mine']} closure_resid={cb['closure_resid']}")
    plan["csm_buckets"] = csm_buckets
    # CSM owner-gold cells: 롯데 2023.1Q items 4 / 6 -> evidence of the old gold (class C: gold = the gross-liability line of the same restated table + closing plug)
    csm_gold_overlap = [c for c in csm_cells if c["gold_cell"]]
    csm_gold_class = {}
    for c in csm_gold_overlap:
        g = GOLDC[(c["code"], c["item"], c["quarter"])]
        csm_gold_class[(c["code"], c["item"], c["quarter"])] = analyse_lotte_csm_gold(c, g, GOLDC)
        OUT.append(f"   CSM gold {c['code']} {c['quarter']} i{c['item']}: gold {g['값']} -> {csm_gold_class[(c['code'], c['item'], c['quarter'])]['summary']}")
    plan["csm_gold_class"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in csm_gold_class.items()}

    # ------------------------------------------------------------------------------------------------ 5. contract
    gold_new, gold_replace = [], []
    held_buckets = {(h["code"], h["quarter"]) for h in held}
    for b in plan["buckets"]:
        if (b["code"], b["quarter"]) in held_buckets:
            continue
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            note = make_note(c, b, S)
            if k in GOLD:
                old_e = GOLD[k]
                gold_replace.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=old_e["값"], note=make_note(c, b, S, replaced=old_e), old_entry=dict(old_e)))
            else:
                gold_new.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=c["old"], note=note))
    csm_gold_new, csm_gold_replace = [], []
    for c in csm_cells:
        k = (c["code"], c["item"], c["quarter"])
        why = make_csm_why(c)
        if k in GOLDC:
            old_e = GOLDC[k]
            csm_gold_replace.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=old_e["값"], why=make_csm_why(c, replaced=old_e, cls=csm_gold_class.get(k)), old_entry=dict(old_e)))
        else:
            csm_gold_new.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=c["old"], why=why))
    plan["apply_contract"] = dict(gold_new=gold_new, gold_replace=gold_replace, csm_gold_new=csm_gold_new, csm_gold_replace=csm_gold_replace, null_dangi_add=null_add, null_dangi_remove=null_remove,
                                  set_dangi_add=set_add, set_dangi_remove=set_remove, held=held)
    OUT.append(f"== E. APPLY CONTRACT: PL gold_new {len(gold_new)}, gold_replace {len(gold_replace)}, CSM gold_new {len(csm_gold_new)}, gold_replace {len(csm_gold_replace)}, null_dangi_add {len(null_add)}, "
               f"null_dangi_remove {len(null_remove)}, set_dangi_add {len(set_add)}, set_dangi_remove {len(set_remove)}, held {held}")
    OUT.append(f"   null_dangi_add: {null_add}")
    OUT.append(f"   null_dangi_remove: {null_remove}")
    OUT.append(f"   set_dangi_add: {[(x[0], x[1], x[2], x[3]) for x in set_add]}")
    OUT.append(f"   set_dangi_remove: {set_remove}")
    plan["n_pl_cells"] = len(gold_new) + len(gold_replace)
    plan["n_csm_cells"] = len(csm_gold_new) + len(csm_gold_replace)
    (EV / "e21_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    (EV / "e21_plan_report.txt").write_text("\n".join(LOG + [""] + OUT) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(OUT))
    print("PL cells", plan["n_pl_cells"], "CSM cells", plan["n_csm_cells"])


def per_of(q):
    return {"1": "3월", "2": "6월", "3": "9월", "4": "12월"}[q[5]]


def make_note(c, b, S, replaced=None):
    code, q, it = c["code"], c["quarter"], c["item"]
    multi = len(c["parts"]) > 1 or c["operands"]
    first = c["parts"][0]["line"] if c["parts"] else None
    lines_txt = f"L{first}" + (f" 외 합산 {len(c['parts'])}줄(증거 e21_plan.json parts)" if len(c["parts"]) > 1 else "") if first else "마스터 피연산자만"
    kind_txt = {"kb": "보험손익 상세내역 노트 전기 표(장기·일반·자동차·해외 열) + 4-2 포괄손익계산서", "lotte": "보험손익 및 재보험손익 노트 전기 표 + 4-2 포괄손익계산서",
                "meritz": "보험손익 상세내역 노트 전기 표 + 4-2 포괄손익계산서", "life": "4-2 포괄손익계산서(보험수익·재보험수익·보험서비스비용·재보험비용) + 노트", "kblife_fix": "같은 공시의 4-2 포괄손익계산서 보험영업수익·비용 4줄"}[b["kind"]]
    mo = ""
    if c.get("original_print") and c.get("gold_class") == "A_basis":
        o, gsrc = c["original_print"], c["gold_source_print"]
        mo = (f"현재 마스터값(gold) {c['old']} 는 원 공시 rcept {gsrc['rcept']} 의 연결 기준 인쇄값(원문 " + ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in gsrc["lines"]) +
              f", 단위 {gsrc['unit']})이고, 같은 원 공시의 별도 기준 인쇄값(" + ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) +
              f" = {o['value']})이 최신 비교열 값과 같다 -> 재작성이 아니라 연결 -> 별도 기준 보정. ")
    elif c.get("original_print"):
        o = c["original_print"]
        mo = (f"현재 마스터값(gold) {c['old']} 는 원 공시 rcept {o['rcept']}(단위 {o['unit']}) 별도 기준 인쇄값({o['value']}, 원문 " +
              ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) + ")과 일치. ")
    elif c["old"] is not None:
        mo = f"변경 전 마스터값 {c['old']}. "
    ops = ""
    if c["operands"]:
        ops = " 피연산자: " + ", ".join(f"{o['item']}번={o['value']}({o['source']})" for o in c["operands"]) + "."
    pre = ""
    if replaced is not None:
        pre = (f"owner gold 를 최신 비교열로 갱신(owner 2026-10-12·2026-10-22 규칙, gold == 원 공시 인쇄값인 경우만): 이전 gold 값 {replaced['값']}, 이전 was {replaced.get('was')}, "
               f"이전 note 요약 「{str(replaced.get('note'))[:140]}…」(전문은 git HEAD 의 data/_gold/user_pl_cells.json). ")
    return (pre + f"{LIVE_NOTE}: 별도(OFS) 기준 {kind_txt}, {b['meta']['later_fy']} rcept {c['xml_rcept']} 의 전기 {q[:4]}.{q[5]}Q 누적({per_of(q)}) 열 → {c['new']} 백만원. "
            f"원문 {c['xml_file']} {lines_txt}. 단위 {c['source_unit']}. {mo}변동 {c['delta'] if c['delta'] is not None else '신규'}. 산식: {c['formula']}.{ops} 증거 {EVREL}/e21_plan.json")


def make_csm_why(c, replaced=None, cls=None):
    lines = []
    for p in c["parts"][:6]:
        lines.append(f"L{p['line']} {p['printed']}")
    cite = ", ".join(lines) + (f" 외 {len(c['parts']) - 6}셀" if len(c["parts"]) > 6 else "")
    pre = ""
    if replaced is not None:
        pre = (f"이전 gold {replaced['값']} (이전 was {replaced.get('was')}) 를 교체: {cls['summary'] if cls else ''} | ")
    deriv = f" 이 항목은 인쇄 셀이 아니라 {c['derived']} 로 계산한 값이다." if c.get("derived") else ""
    return (pre + f"{LIVE_NOTE}: 최신 공시의 전기 열(별도 기준, 발행 보험계약 CSM) {c['src']}. 인쇄 셀: {cite or '없음'} -> {c['exact']} 억원, 저장값 {c['new']}.{deriv} 증거 {EVREL}/e21_plan.json")


def analyse_lotte_csm_gold(c, g, GOLDC):
    """롯데 2023.1Q CSM items 4 / 6: the original 2023.1Q filing prints NO CSM roll-forward (owner-gold note: 'no table'); show where the old gold value comes from."""
    code, q, item = c["code"], c["quarter"], c["item"]
    fy = P.later_fy(q)
    path = T.main_path(code, fy)
    lines, s0 = C.sep_tables(path)
    # the prior table of the pair (same one the reader used)
    cands = []
    for t in T.M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [T.nl(W.label_of(r)) for r in rows]
        if any(x.startswith("기초순보험계약부채") for x in labs) and "보험계약마진상각액" in labs and "최초인식계약" in labs:
            cands.append((t, rows))
    t, rows = cands[1]
    unit = T.find_unit(lines, t, span=2500)
    liab = [r for r in rows if T.nl(W.label_of(r)) == "기말보험계약부채"]
    net = [r for r in rows if T.nl(W.label_of(r)) == "기말순보험계약부채"]
    out = dict(liab_close=None, net_close=None)
    if liab and net:
        lv = W.numeric_cells(liab[0])[5]
        nv = W.numeric_cells(net[0])[5]
        out.update(liab_close=dict(line=lv[1], printed=lv[2], eok=lv[0] / 100.0), net_close=dict(line=nv[1], printed=nv[2], eok=nv[0] / 100.0))
    plug = None
    if out["liab_close"] is not None:
        vals = [GOLDC[(code, i, q)]["값"] for i in (1, 2, 3, 5)]
        plug = round(out["liab_close"]["eok"] - sum(vals), 2)
    gv = g["값"]
    if item == 6:
        match = out["liab_close"] is not None and abs(gv - out["liab_close"]["eok"]) <= 0.0051
        summary = (f"class C (원 공시 2023.1Q 에는 CSM 표가 없어 원 인쇄값이 존재하지 않음): 이전 gold {gv} = 같은 전기 표의 기말보험계약부채(총, 자산 제외) CSM 소계 L{out['liab_close']['line']} {out['liab_close']['printed']} "
                   f"({'일치' if match else '불일치'}), 최신 값은 기말순보험계약부채 L{out['net_close']['line']} {out['net_close']['printed']} (기초·신계약·이자·상각이 모두 순 기준)")
    else:
        match = plug is not None and abs(gv - plug) <= 0.0051
        summary = (f"class C: 이전 gold {gv} 는 총 부채 기준 기말 {out['liab_close']['eok']} 에 맞춘 닫힘 플러그(기말 - (기초+신계약+이자+상각) = {plug}, {'일치' if match else '불일치'}); "
                   f"인쇄된 추정치 변동은 L{c['parts'][0]['line']} {c['parts'][0]['printed']}")
    return dict(summary=summary, evidence=out, plug=plug, matches_gross_liability_basis=bool(match), unit=unit)


if __name__ == "__main__":
    build()
