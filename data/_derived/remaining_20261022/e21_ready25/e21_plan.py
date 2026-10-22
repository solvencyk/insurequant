# -*- coding: utf-8 -*-
"""e21 plan builder (parser/ifrs17, ticket 20261023T0300Z READY-25 load): READ-ONLY on every master / gold / provenance / test / doc.
Independent re-read of every bucket from the filing XML (e21_plan_lib readers), HEAD masters as `old`, rounding rule (a cell that differs from the master only by print rounding is NOT adopted;
the more precise / existing value stays), residual items 2 / 7 / 12 recomputed from the FINAL legs, gold classification (gold == original print -> replace; neither -> hold), seam analysis
(printed 3-month columns for Q2/Q3, vintage rule for Q4), CSM vectors, apply contract.  Writes e21_plan.json + e21_plan_report.txt."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm as C  # noqa: E402
import e21_csm2 as C2  # noqa: E402
import e21_life as L  # noqa: E402
import e21_plan_lib as P  # noqa: E402
import e21_raw as W  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT, EV, MEAS = P.ROOT, P.EV, P.MEAS
EVREL = "data/_derived/remaining_20261022/e21_ready25"
TIER1 = P.TIER1
ITEM_NAME = {1: "보험손익", 2: "생명장기 손익", 3: "원수손익(장기)", 4: "원수 CSM상각", 5: "원수 위험조정", 6: "원수 예실차", 7: "기타 원수", 8: "재보험손익(장기)", 9: "재보험 CSM상각",
             10: "재보험 위험조정", 11: "재보험 예실차", 12: "기타 재보험", 13: "자동차", 14: "일반(+해외)", 15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익",
             20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품",
             29: "FVOCI 지분증권", 30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CSM_NAME = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}
SPECS = [
    ("KR0104", "2023.1Q", "life", "prior"), ("KR0104", "2023.2Q", "life", "prior"),
    ("KR0083", "2024.4Q", "life", "prior"),
    ("KR0070", "2024.4Q", "life", "prior"),
    ("KR0079", "2023.4Q", "life", "prior"), ("KR0079", "2024.1Q", "life", "prior"), ("KR0079", "2024.2Q", "life", "prior"), ("KR0079", "2024.3Q", "life", "prior"),
    ("KR0010", "2023.1Q", "kb", "prior"), ("KR0010", "2023.2Q", "kb", "prior"), ("KR0010", "2023.4Q", "kb", "prior"),
    ("KR0010", "2024.1Q", "kb", "prior"), ("KR0010", "2024.2Q", "kb", "prior"), ("KR0010", "2024.3Q", "kb", "prior"),
    ("KR0099", "2024.1Q", "kblife_fix", "cur"),
    ("KR0003", "2023.1Q", "lotte", "prior"), ("KR0003", "2023.2Q", "lotte", "prior"), ("KR0003", "2024.1Q", "lotte", "prior"), ("KR0003", "2024.2Q", "lotte", "prior"), ("KR0003", "2024.3Q", "lotte", "prior"),
    ("KR0001", "2023.1Q", "meritz", "prior"), ("KR0001", "2023.2Q", "meritz", "prior"),
    ("KR0068", "2023.1Q", "life", "prior"), ("KR0068", "2023.2Q", "life", "prior"), ("KR0068", "2023.3Q", "life", "prior"),
]
# CSM buckets: code, quarter, reader
CSM_SPECS = [("KR0003", "2023.1Q"), ("KR0003", "2024.1Q"), ("KR0003", "2024.2Q"), ("KR0003", "2024.3Q"), ("KR0079", "2024.1Q"), ("KR0079", "2024.2Q"), ("KR0079", "2024.3Q"),
             ("KR0001", "2023.1Q"), ("KR0001", "2023.2Q"), ("KR0068", "2023.1Q"), ("KR0068", "2023.2Q"), ("KR0068", "2023.3Q")]
# measure-phase cell exclusions decided by the ticket / by this independent re-read
TICKET_EXCLUDE = {("KR0010", "2024.2Q", 16): "ticket: KB손보 2024.2Q 항목 16 (192,135 -> 192,136) is a 1 mn reprint difference of an owner-gold cell (rounding rule)"}
LIVE_NOTE = "2026-10-23 parser/ifrs17 (e21, ticket 20261023T0300Z READY-25: 최신 비교열 채택, owner 결정 2026-10-12·2026-10-22)"


def classify(old, c):
    """fill | equal | rounding | changed (rounding band of the NEW print's precision; 원 prints are exact)"""
    new = c["val"]
    if old is None:
        return "fill"
    d = new - old
    units = {p.get("unit") for p in c["parts"]} or {"백만원"}
    exact_src = units == {"원"}
    if abs(d) <= 2e-5:
        return "equal"
    band = 2e-5 if exact_src else (1.0 + 0.5 * (max(1, len(c["parts"])) - 1) + 1e-3)
    if abs(d) <= band:
        return "rounding"
    return "changed"


def merged_identities(v, exact):
    res = []

    def chk(name, lhs, rhs, n_round):
        if lhs is None or rhs is None:
            res.append(dict(name=name, status="SKIP (operand empty)", ok=True))
            return
        d = lhs - rhs
        tol = 0.002 if exact else 0.5 * n_round + 0.002
        res.append(dict(name=name, lhs=round(lhs, 6), rhs=round(rhs, 6), resid=round(d, 6), tol=round(tol, 4), ok=abs(d) <= tol))

    g = lambda i: v.get(i)  # noqa: E731
    S = lambda *xs: None if any(x is None for x in xs) else sum(xs)  # noqa: E731
    chk("I1 20 = 1 + 17", g(20), S(g(1), g(17)), 3)
    chk("I2 22 = 20 + 21", g(22), S(g(20), g(21)), 3)
    chk("I2b |22-24| = |23|", None if g(22) is None or g(24) is None else abs(g(22) - g(24)), None if g(23) is None else abs(g(23)), 3)
    chk("I3 31 = 24 + 25", g(31), S(g(24), g(25)), 3)
    oci = [i for i in (26, 27, 28, 29, 30, 32) if g(i) is not None]
    chk("I4 25 = sum of the OCI parts the master carries", g(25), S(*[g(i) for i in oci]) if oci else None, 1 + len(oci))
    chk("I5 17 = 18 + 19", g(17), S(g(18), g(19)), 3)
    # insurance-result bridge: 1 = 2 (+13 +14) + 15 - 16 ; the bare / adjusted forms of scripts/_pl_selfcheck.py (either closes)
    if g(1) is not None and g(2) is not None:
        lob = g(2) + (g(13) or 0) + (g(14) or 0)
        bare = g(1) - lob
        adj = g(1) - (lob + (g(15) or 0) - (g(16) or 0))
        pick = adj if abs(adj) <= abs(bare) else bare
        res.append(dict(name="I6 LOB bridge 1 = 2+13+14 (+15-16)", lhs=round(g(1), 6), rhs=round(lob, 6), resid=round(pick, 6), tol=round(0.5 * 6 + 0.002 if not exact else 0.5, 4), ok=abs(pick) <= (3.0 if not exact else 0.5)))
    if g(2) is not None and g(3) is not None and g(8) is not None:
        chk("I7 2 = 3 + 8", g(2), g(3) + g(8), 3)
    if g(3) is not None and None not in (g(4), g(5), g(6), g(7)):
        chk("I8 3 = 4+5+6+7", g(3), g(4) + g(5) + g(6) + g(7), 5)
    if g(8) is not None and None not in (g(9), g(10), g(11), g(12)):
        chk("I9 8 = 9+10+11+12", g(8), g(9) + g(10) + g(11) + g(12), 5)
    return res


def read_orig_vector(code, q):
    st = R.Stmt(code, P.orig_fy(q))
    return st, R.read_vector(st, "cur", "cum")


def find_printed(path, texts, label_sub, sep_only=False):
    """lines of an xml file that print any of `texts` inside a table row whose label contains label_sub (normalised) -> [(line, label, printed)]"""
    lines = M_lines(path)
    hits = []
    for i, ln in enumerate(lines, 1):
        for tx in texts:
            if tx in ln and re.search(r">\s*\(?-?" + re.escape(tx.strip("()-")) + r"\)?\s*<", ln):
                # label of the TR: walk up to the <TR line and read the first cell text
                j = i - 1
                while j > 0 and not lines[j - 1].startswith("<TR"):
                    j -= 1
                k = j
                lab = ""
                while k < len(lines) and not lines[k].startswith("</TR"):
                    if lines[k].startswith(("<TD", "<TE", "<TH")):
                        m = k + 1
                        buf = []
                        if re.search(r"</T[DEH]>\s*$", lines[k]):
                            buf.append(W.clean(lines[k]))
                        else:
                            while m < len(lines) and not lines[m].startswith("</T"):
                                buf.append(W.clean(lines[m]))
                                m += 1
                        lab = " ".join(b for b in buf if b).strip()
                        if re.search(r"[가-힣]", lab):
                            break
                    k += 1
                if label_sub in re.sub(r"\s+", "", lab):
                    if sep_only:
                        t = i - 1
                        while t > 0 and not lines[t - 1].startswith("<TITLE"):
                            t -= 1
                        if "연결" in re.sub(r"\s+", "", W.clean(lines[t - 1] if t > 0 else "")):
                            continue
                    hits.append((i, lab, tx))
    return hits


_L = {}


def M_lines(path):
    if path not in _L:
        _L[path] = Path(path).read_text(encoding="utf-8", errors="replace").split("\n")
    return _L[path]


def build_pl_buckets():
    plh = P.head_json("PL_breakdown.json")
    csmh = P.head_json("CSM_waterfall.json")
    master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in plh}
    masterd = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in plh}
    csm_m = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in csmh}
    name_of = {r["원보험사코드"]: r["원수사명"] for r in plh}
    gold = P.head_json("data/_gold/user_pl_cells.json")
    gold_csm = P.head_json("data/_gold/user_csm_cells.json")
    GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GOLDC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold_csm["set"]}
    NULLD = {tuple(x) for x in gold["null_dangi"]["cells"]}
    SETD = {(x[0], x[1], int(x[2])): x for x in gold["set_dangi"]["cells"]}
    cj = json.loads((MEAS / "cands_READY_all.json").read_text(encoding="utf-8"))
    cand = {(c["code"], c["q"], c["item"]): c for c in cj["pl_cells"]}
    cand_csm = {(c["code"], c["q"], c["item"]): c for c in cj["csm_cells"]}
    plan = dict(generated="2026-10-23", ticket="inbox/parser/20261023T0300Z__orchestrator__MULTI_2023.1Q-2024.4Q__latest_comparative_ready_25_rows.md", buckets=[], csm_buckets=[], seams=[], notes=[])
    LOG = []
    pl_cells_all = {}      # (code, q, item) -> cell dict (adopted)
    bucket_by = {}
    for code, q, kind, role in SPECS:
        rb = P.read_bucket(code, q, kind, master, role) if kind != "kblife_fix" else None
        if kind == "kblife_fix":
            rb = read_kblife_fix(code, q, master)
        meta, items = rb["meta"], rb["items"]
        LOG.append(f"== {code} {q} {kind} later {meta['file']} unit {meta['unit']}")
        adopted, dropped = {}, []
        derived_ids = (2, 7, 12)
        for i in sorted(items):
            if i in derived_ids:
                continue
            c = items[i]
            if i in (26, 27, 28, 29, 30) and c.get("absent"):
                continue
            old = master.get((code, i, q))
            cls = classify(old, c)
            cd = cand.get((code, q, i))
            reason = None
            if (code, q, i) in TICKET_EXCLUDE:
                reason = TICKET_EXCLUDE[(code, q, i)]
            elif cls in ("equal", "rounding"):
                reason = {"equal": "equal to the master", "rounding": "rounding-only difference (more precise / existing value kept)"}[cls] if cd is not None or cls == "rounding" else None
            if cls in ("fill", "changed") and reason is None:
                adopted[i] = c
            elif cd is not None or cls == "rounding":
                dropped.append(dict(item=i, old=old, new=c["val"], cls=cls, reason=reason or cls, in_cand=cd is not None))
        # --- residual items 2 / 7 / 12 recomputed from the FINAL legs
        rd = {k: v for k, v in rb["reader"].items() if isinstance(k, int)}
        legs_adopted = {k: rd[k] for k in (3, 4, 5, 6, 8, 9, 10, 11) if k in rd and (k in adopted or (k == 4 and 4 in items and 4 in adopted))}
        extra_ops = {}
        if 4 in adopted and 4 not in rd:
            extra_ops[4] = adopted[4]["val"]
        legs = {}
        for k in (3, 8):
            if k in adopted:
                legs[k] = dict(val=adopted[k]["val"], parts=adopted[k]["parts"], src=adopted[k]["src"])
        for k in (4, 5, 6, 9, 10, 11):
            if k in adopted and k in rd:
                legs[k] = dict(val=adopted[k]["val"], parts=adopted[k]["parts"], src=adopted[k]["src"])
        # base legs 3 / 8: when a base leg is not adopted its master value is the operand (handled by derive_2_7_12 through `master`)
        out_d = derive_final(code, q, legs, extra_ops, master, adopted, rd)
        for i, c in out_d.items():
            old = master.get((code, i, q))
            if old is None:
                cls = "fill"
            else:
                cls = "changed" if abs(c["val"] - old) > 2e-5 else "equal"
            cd = cand.get((code, q, i))
            if cls in ("fill", "changed"):
                adopted[i] = c
            elif cd is not None:
                dropped.append(dict(item=i, old=old, new=c["val"], cls="equal", reason="recomputed from the final legs: equal to the master", in_cand=True))
        cset = {i for (c_, q_, i) in cand if c_ == code and q_ == q}
        only_c = sorted(cset - set(adopted))
        only_m = sorted(set(adopted) - cset)
        LOG.append(f"   adopted {len(adopted)}: {sorted(adopted)}")
        LOG.append(f"   candidate items not adopted: {only_c}  | adopted but not in candidates: {only_m}")
        for d in dropped:
            LOG.append(f"   dropped i{d['item']}: old={d['old']} new={d['new']} cls={d['cls']} ({d['reason']}) in_cand={d['in_cand']}")
        # closure on the merged vector
        merged = {i: master.get((code, i, q)) for i in range(1, 33)}
        for i, c in adopted.items():
            merged[i] = c["val"]
        exact_all = (meta["unit"] == "원")
        clos = merged_identities(merged, exact_all and kind not in ("kb", "lotte", "meritz", "kblife_fix"))
        bad = [x for x in clos if not x.get("ok", True)]
        LOG.append("   closure: " + "; ".join(f"{x['name'].split(' ')[0]}={'SKIP' if 'resid' not in x else format(x['resid'], '+.4f')}{'' if x.get('ok', True) else ' FAIL'}" for x in clos))
        b = dict(code=code, quarter=q, kind=kind, meta=meta, cells=[], dropped=dropped, closure=clos, closure_ok=not bad, cset=sorted(cset), only_cand=only_c, only_mine=only_m)
        for i in sorted(adopted):
            c = adopted[i]
            old = master.get((code, i, q))
            cd = cand.get((code, q, i))
            cell = dict(code=code, quarter=q, item=i, item_name=ITEM_NAME[i], old=old, new=round(c["val"], 6), delta=None if old is None else round(c["val"] - old, 6), unit="백만원",
                        xml_file=meta["file"], xml_rcept=meta["rcept"], source_unit=meta["unit"], parts=c["parts"], operands=c["operands"], abs_of_sum=c.get("abs_of_sum", False), formula=c["formula"],
                        kind=c["kind"], cand_new=None if cd is None else cd["new"], cand_equal=None if cd is None else abs(cd["new"] - c["val"]) <= 1e-3, cls=("fill" if old is None else "changed"),
                        gold_cell=((code, i, q) in GOLD))
            b["cells"].append(cell)
            pl_cells_all[(code, q, i)] = cell
        plan["buckets"].append(b)
        bucket_by[(code, q)] = b
    plan["_log_pl"] = LOG
    return dict(plan=plan, master=master, masterd=masterd, csm_m=csm_m, name_of=name_of, gold=gold, gold_csm=gold_csm, GOLD=GOLD, GOLDC=GOLDC, NULLD=NULLD, SETD=SETD,
                cand=cand, cand_csm=cand_csm, pl_cells_all=pl_cells_all, bucket_by=bucket_by, LOG=LOG)


def read_kblife_fix(code, q, master):
    """KR0099 2024.1Q (R0): the master mis-signs 총 재보험수익 (abs() in extract_tier2_kblife); the SAME filing's separate income statement prints the four insurance lines.  Items 2 / 8 / 12 only."""
    fy = P.orig_fy(q)
    st = R.Stmt(code, fy)
    lr = L.life_is_items(code, fy, "cur", "cum", st=st)
    meta = dict(code=code, quarter=q, kind="kblife_fix", later_fy=fy, file=st.rel, unit=st.unit, fmt=st.fmt, role="cur", rcept=Path(st.rel).stem)
    r = {3: lr[3], 8: lr[8]}
    items = {}
    for k in (3, 8):
        items[k] = P.cell(r[k]["val"], r[k]["parts"], r[k]["formula"], r[k]["src"])
    items.update(P.derive_2_7_12(r, master, code, q, {}))
    return dict(meta=meta, items=items, reader=r)


def derive_final(code, q, legs, extra_ops, master, adopted, rd):
    """items 2 / 7 / 12 from the FINAL legs: adopted legs contribute their printed cells, the others the HEAD master value (operands)"""
    out = {}

    def leg(i):
        """-> (val, parts, operand) for leg i"""
        if i in legs:
            return legs[i]["val"], legs[i]["parts"], None
        mv = extra_ops.get(i, master.get((code, i, q)))
        if mv is None:
            return None, None, None
        return mv, [], dict(item=i, value=mv, source=("plan" if i in extra_ops else "master HEAD"))

    # item 2 = 3 + 8
    v3, p3, o3 = leg(3)
    v8, p8, o8 = leg(8)
    def mkcell(val, parts, ops, formula):
        return P.cell(val, parts, formula, "final legs", operands=ops, kind="derived")
    if v3 is not None and v8 is not None and (3 in legs or 8 in legs):
        ops = [dict(item=o["item"], sign=1, value=o["value"], source=o["source"]) for o in (o3, o8) if o]
        out[2] = mkcell(v3 + v8, (p3 or []) + (p8 or []), ops, "3 + 8")
    for tgt, base, opsl in ((7, 3, (4, 5, 6)), (12, 8, (9, 10, 11))):
        vb, pb, ob = leg(base)
        if vb is None:
            continue
        parts = list(pb or [])
        operands = [dict(item=ob["item"], sign=1, value=ob["value"], source=ob["source"])] if ob else []
        val = vb
        ok = True
        any_leg = base in legs
        for o in opsl:
            vo, po, oo = leg(o)
            if vo is None:
                ok = False
                break
            if o in legs:
                any_leg = True
                parts += [P.flip(p) for p in po]
            else:
                operands.append(dict(item=o, sign=-1, value=oo["value"], source=oo["source"]))
            val -= vo
        if ok and any_leg:
            out[tgt] = mkcell(val, parts, operands, f"{base} - ({'+'.join(str(o) for o in opsl)})")
    return out


