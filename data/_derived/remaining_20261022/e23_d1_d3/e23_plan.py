# -*- coding: utf-8 -*-
"""e23 plan builder (parser/ifrs17, ticket 20261023T0900Z, owner decisions D1-D3 of 2026-10-23).  READ-ONLY on every master / gold / provenance / test / doc.
usage: e23_plan.py <kblife|lotte|abl|kdb|hd>      -> e23_plan_<key>.json + e23_plan_<key>_report.txt next to this file.
Independent re-read (own readers e23_read + e21 helpers) of every bucket of ONE company from the filing XML / IR factsheet, LIVE masters as `old` (not the e20 snapshot), rounding rule (a cell that
differs from the master only by print rounding is NOT adopted), residual items 2 / 7 / 12 recomputed from the FINAL legs, owner-gold overlap only for the cells the owner approved
(gold_cells_replaced.csv), masked-gold guard (no new ledger pin), single-quarter seam analysis (printed 3-month columns for Q2/Q3, vintage rule for Q4), CSM vectors, apply contract.
The e20 candidate cells (cands_<scenario>.json) are only compared with (CAND_EQ / CAND_DIFF)."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

E21 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25"
E23 = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3"
for _p in (E21, E23):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import e21_csm2 as C2  # noqa: E402
import e21_life as L  # noqa: E402
import e21_plan as PL  # noqa: E402
import e21_plan_full as PF  # noqa: E402
import e21_plan_lib as P  # noqa: E402
import e21_raw as W  # noqa: E402
import e21_read as R  # noqa: E402
import e21_t2 as T  # noqa: E402
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT, MEAS, TIER1 = P.ROOT, P.MEAS, P.TIER1
EV = Path(E23)
EVREL = "data/_derived/remaining_20261022/e23_d1_d3"
TICKET = "20261023T0900Z"
LIVE_NOTE = "2026-10-23 parser/ifrs17 (e23, ticket 20261023T0900Z D1~D3: 최신 비교열 채택, owner 결정 2026-10-23 승인)"
ITEM_NAME, CSM_NAME = PL.ITEM_NAME, PL.CSM_NAME
L.SPEC["KR0072"] = [("rev", "보험수익", 1, 1, False), ("cost", "보험비용", 1, -1, True), ("rerev", "재보험수익", 1, 1, False), ("recost", "재보험비용", 1, -1, True)]

# ------------------------------------------------------------------------------------------------------------ company configuration (owner decisions D1-D3, 2026-10-23)
Q4S = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
CO = {
    "kblife": dict(code="KR0099", name="KB라이프생명", scn="N2_KBlife_B", kind="life_note", quarters=["2023.1Q", "2023.2Q", "2023.3Q"], csm_quarters=["2023.1Q", "2023.2Q", "2023.3Q"],
                   tier1=dict(names_extra={1: ["보험영업손익"], 17: ["투자영업손익"]}), p015_insurance_only=True, pl4=X.pl4_kblife, csm=X.csm_kblife,
                   gold_pl_ok={}, gold_csm_ok={}, exclude={}, decision="D1 = 옵션 B (FY2023 2023.1Q~3Q 만 최신, 2023.4Q·2024 는 그대로)"),
    "lotte": dict(code="KR0003", name="롯데손해보험", scn="N7_Lotte_FY2023Q4", kind="lotte", quarters=["2023.4Q"], csm_quarters=["2023.4Q"], tier1={}, pl4=None, csm=C2.lotte_csm,
                  gold_pl_ok={}, gold_csm_ok={}, exclude={}, decision="D2 = 롯데 2023.4Q 채택 (WFY 면제 등재는 validation 몫)"),
    "abl": dict(code="KR0070", name="에이비엘생명보험", scn="N4_ABL_FY2023", kind="life_note", quarters=Q4S, csm_quarters=Q4S, tier1={}, pl4=X.pl4_abl, csm=X.csm_abl,
                gold_pl_ok={("2023.1Q", 4): "print", ("2023.1Q", 7): "derived"}, gold_csm_ok={("2023.4Q", 1): "chain", ("2023.4Q", 4): "chain"}, exclude={},
                decision="D3 = ABL FY2023 진행 (연쇄용 CSM gold 교체 승인)"),
    "kdb": dict(code="KR0072", name="케이디비생명보험", scn="N5_KDB_FY2023", kind="life_note", quarters=Q4S, csm_quarters=Q4S, tier1={}, pl4=X.pl4_kdb, csm=X.csm_kdb,
                gold_pl_ok={("2023.2Q", 4): "print", ("2023.2Q", 7): "derived", ("2023.3Q", 4): "print", ("2023.3Q", 7): "derived"},
                gold_csm_ok={("2023.1Q", 4): "orig", ("2023.1Q", 5): "orig", ("2023.1Q", 6): "orig", ("2023.2Q", 4): "orig", ("2023.2Q", 5): "orig", ("2023.4Q", 1): "chain", ("2023.4Q", 4): "chain"},
                exclude={}, decision="D3 = KDB생명 FY2023 진행 (연쇄용 CSM gold 교체 승인)"),
    "hd": dict(code="KR0009", name="현대해상", scn="N6c_HD_FY2023_IRlegs", kind="hd", quarters=Q4S, csm_quarters=Q4S, tier1=dict(neg_expense=True), pl4=X.pl4_hd, csm=X.csm_hd,
               ir_quarters=["2023.1Q", "2023.2Q"], gold_pl_ok={}, gold_csm_ok={("2023.3Q", 1): "chain", ("2023.3Q", 4): "chain", ("2023.4Q", 1): "chain", ("2023.4Q", 4): "chain"},
               exclude={("2023.4Q", 16): "rounding-only (38,491.0 gold vs 38,490.968273 printed): ticket rule, no new mask pin"},
               decision="D3 = 현대해상 FY2023 진행 (IR 팩트시트 LOB 레그 허용 + 연쇄용 CSM gold 교체 승인)"),
}
# printed originals of the approved PL gold cells (class A): item 4 = |CSM amortisation| of the ORIGINAL filing
PF.ORIG_PRINT[("KR0070", "2023.1Q", 4)] = dict(gold_src=[("22,664", "서비스의이전으로당기손익에인식한보험계약마진", 1, True)], orig_sep=None)
PF.ORIG_PRINT[("KR0072", "2023.2Q", 4)] = dict(gold_src=[("23,415", "제공된서비스의보험계약마진", 1, True)], orig_sep=None)
PF.ORIG_PRINT[("KR0072", "2023.3Q", 4)] = dict(gold_src=[("35,250", "제공된서비스의보험계약마진", 1, True)], orig_sep=None)


def jl(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def fmt(v, nd=1):
    return "None" if v is None else f"{v:,.{nd}f}"


def per_of(q):
    return {"1": "3월", "2": "6월", "3": "9월", "4": "12월"}[q[5]]


def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


def classify(old, c):
    new = c["val"]
    if old is None:
        return "fill"
    d = new - old
    units = {p.get("unit") for p in c["parts"]} or {"백만원"}
    exact_src = units == {"원"} or units == {"천원"}
    if abs(d) <= 2e-5:
        return "equal"
    band = 2e-5 if exact_src else (1.0 + 0.5 * (max(1, len(c["parts"])) - 1) + 1e-3)
    if abs(d) <= band:
        return "rounding"
    return "changed"


# ------------------------------------------------------------------------------------------------------------ bucket reader
def read_bucket23(co, q, master):
    code = co["code"]
    fy = P.later_fy(q)
    st = R.Stmt(code, fy)
    t1 = X.read_tier1(st, "prior", "cum", co.get("tier1"))
    meta = dict(code=code, quarter=q, kind=co["kind"], later_fy=fy, file=st.rel, unit=st.unit, fmt=st.fmt, role="prior", rcept=Path(st.rel).stem)
    items = {}
    for i in TIER1:
        v = t1[i]
        items[i] = P.cell(v["val"], v["parts"], "statement line" if len(v["parts"]) == 1 else "derived from statement lines (production definition)", f"{st.rel} prior/cum unit {st.unit}", unit=st.unit)
        items[i]["absent"] = bool(v.get("absent"))
    items[25]["leaf_all_sum"] = round(t1["_leaf_all_sum"], 6)
    p15 = X.presence_015(st, "prior", "cum", insurance_only=co.get("p015_insurance_only", False))
    items[15] = P.cell(p15["val"], p15["parts"], p15["formula"], p15["src"], unit=st.unit)
    items[15]["present"] = p15["present"]
    r, extra_ops = {}, {}
    kind = co["kind"]
    if kind == "life_note":
        lr = L.life_is_items(code, fy, "prior", "cum", st=st)
        r = {3: lr[3], 8: lr[8]}
        n4 = co["pl4"](q)
        items[4] = P.cell(n4["part"]["contribution_mn"], [n4["part"]], "|CSM amortisation printed in the 보험수익 note, prior-period cumulative (합계)|", n4["src"])
        extra_ops[4] = items[4]["val"]
        for k in (3, 8):
            items[k] = P.cell(r[k]["val"], r[k]["parts"], r[k]["formula"], r[k]["src"])
        items.update(P.derive_2_7_12(r, master, code, q, extra_ops))
        return dict(meta=meta, items=items, reader=r)
    if kind == "lotte":
        r = T.lotte_combined_read(code, q)
        for k, v in r.items():
            if isinstance(k, int):
                items[k] = P.cell(v["val"], v["parts"], v["formula"], v["src"])
        items.update(P.derive_2_7_12({k: v for k, v in r.items() if isinstance(k, int)}, master, code, q, extra_ops))
        return dict(meta=meta, items=items, reader=r)
    if kind == "hd":
        n4 = co["pl4"](q)
        items[4] = P.cell(n4["part"]["contribution_mn"], [n4["part"]], "|보험계약마진상각 (장기 열) of the 보험수익 note, prior-period cumulative|", n4["src"])
        r = {4: dict(val=items[4]["val"], parts=[n4["part"]], src=n4["src"])}
        if q in co.get("ir_quarters", []):
            ir = X.hd_ir_legs(q)
            for it, key in ((2, "장기"), (13, "자동차"), (14, "일반")):
                c = ir["cells"][key]
                part = dict(label=f"IR (3) UW Income {c['block']} 보 험 손 익 [{ir['header_text'].replace(chr(10), ' ')}]", xlsx=ir["file"], sheet=ir["sheet"], cell=c["cell"], label_cell=c["label_cell"],
                            header_cell=ir["header_cell"], block=c["block"], printed=repr(c["value_mn"]), sign=1, abs=False, unit="백만원", contribution_mn=c["value_mn"], line=None)
                items[it] = P.cell(c["value_mn"], [part], f"IR factsheet LOB insurance result ({key})", f"{ir['file']} sheet {ir['sheet']} cell {c['cell']}")
            items[2]["ir"] = dict(file=ir["file"], sum_check=sum(ir["cells"][k]["value_mn"] for k in ("일반", "장기", "자동차")), total_cell=ir["cells"]["합계"]["cell"], total=ir["cells"]["합계"]["value_mn"])
        return dict(meta=meta, items=items, reader=r)
    raise SystemExit(f"unknown kind {kind}")


# ------------------------------------------------------------------------------------------------------------ main build
def build(key):
    co = CO[key]
    code = co["code"]
    plh = jl("PL_breakdown.json")
    csmh = jl("CSM_waterfall.json")
    master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in plh}
    masterd = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in plh}
    csm_m = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in csmh}
    gold = jl("data/_gold/user_pl_cells.json")
    gold_csm = jl("data/_gold/user_csm_cells.json")
    GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GOLDC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold_csm["set"]}
    NULLD = {tuple(x) for x in gold["null_dangi"]["cells"]}
    SETD = {(x[0], x[1], int(x[2])): x for x in gold["set_dangi"]["cells"]}
    cj = json.loads((MEAS / f"cands_{co['scn']}.json").read_text(encoding="utf-8"))
    cand = {(c["code"], c["q"], c["item"]): c for c in cj["pl_cells"] if c["code"] == code}
    cand_csm = {(c["code"], c["q"], c["item"]): c for c in cj["csm_cells"] if c["code"] == code}
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_data_contract as GV
    src_pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in jl("data/dart/viz/pl_breakdown_master.json")}
    plan = dict(generated="2026-10-23", ticket=f"inbox/parser/20261023T0900Z__orchestrator__MULTI_2023.1Q-2023.4Q__latest_comparative_owner_decided_d1_d3.md", company=key, code=code, name=co["name"],
                decision=co["decision"], scenario=co["scn"], buckets=[], csm_buckets=[], seams=[], findings=[], notes=[])
    LOG, OUT = [], []
    stmts = {}

    def stmt(c_, fy, role="prior"):
        if (c_, fy) not in stmts:
            stmts[(c_, fy)] = R.Stmt(c_, fy)
        return stmts[(c_, fy)]

    def t1(c_, fy, role, kind):
        return X.read_tier1(stmt(c_, fy), role, kind, co.get("tier1"))

    # ===== A. PL buckets
    adopted_all = {}
    held = []
    for q in co["quarters"]:
        rb = read_bucket23(co, q, master)
        meta, items = rb["meta"], rb["items"]
        LOG.append(f"== {code} {q} {co['kind']} later {meta['file']} unit {meta['unit']}")
        adopted, dropped = {}, []
        for i in sorted(items):
            if i in (2, 7, 12):
                continue
            c = items[i]
            if i in (26, 27, 28, 29, 30) and c.get("absent"):
                continue
            old = master.get((code, i, q))
            cls = classify(old, c)
            cd = cand.get((code, q, i))
            reason = co["exclude"].get((q, i))
            if reason is None and cls in ("equal", "rounding"):
                reason = {"equal": "equal to the master", "rounding": "rounding-only difference (more precise / existing value kept)"}[cls]
            if cls in ("fill", "changed") and reason is None:
                adopted[i] = c
            elif cd is not None or cls == "rounding" or (q, i) in co["exclude"]:
                dropped.append(dict(item=i, old=old, new=c["val"], cls=cls, reason=reason or cls, in_cand=cd is not None))
        rd = {k: v for k, v in rb["reader"].items() if isinstance(k, int)}
        extra_ops = {}
        if 4 in adopted and (4 not in rd or co["kind"] in ("life_note", "hd")):
            extra_ops[4] = adopted[4]["val"]
        legs = {}
        for k in (3, 8):
            if k in adopted:
                legs[k] = dict(val=adopted[k]["val"], parts=adopted[k]["parts"], src=adopted[k]["src"])
        if co["kind"] == "lotte":
            for k in (4, 5, 6, 9, 10, 11):
                if k in adopted and k in rd:
                    legs[k] = dict(val=adopted[k]["val"], parts=adopted[k]["parts"], src=adopted[k]["src"])
        out_d = {} if co["kind"] == "hd" else PL.derive_final(code, q, legs, extra_ops, master, adopted, rd)
        for i, c in out_d.items():
            old = master.get((code, i, q))
            cls = "fill" if old is None else ("changed" if abs(c["val"] - old) > 2e-5 else "equal")
            cd = cand.get((code, q, i))
            reason = co["exclude"].get((q, i))
            if cls in ("fill", "changed") and reason is None:
                adopted[i] = c
            elif cd is not None:
                dropped.append(dict(item=i, old=old, new=c["val"], cls="equal", reason="recomputed from the final legs: equal to the master", in_cand=True))
        cset = {i for (c_, q_, i) in cand if q_ == q}
        only_c = sorted(cset - set(adopted))
        only_m = sorted(set(adopted) - cset)
        LOG.append(f"   adopted {len(adopted)}: {sorted(adopted)}")
        LOG.append(f"   candidate items not adopted: {only_c}  | adopted but not in candidates: {only_m}")
        for d in dropped:
            LOG.append(f"   dropped i{d['item']}: old={d['old']} new={d['new']} cls={d['cls']} ({d['reason']}) in_cand={d['in_cand']}")
        merged = {i: master.get((code, i, q)) for i in range(1, 33)}
        for i, c in adopted.items():
            merged[i] = c["val"]
        exact_all = meta["unit"] in ("원", "천원")
        clos = PL.merged_identities(merged, exact_all and co["kind"] not in ("lotte",))
        bad = [x for x in clos if not x.get("ok", True)]
        LOG.append("   closure: " + "; ".join(f"{x['name'].split(' ')[0]}={'SKIP' if 'resid' not in x else format(x['resid'], '+.4f')}{'' if x.get('ok', True) else ' FAIL'}" for x in clos))
        b = dict(code=code, quarter=q, kind=co["kind"], meta=meta, cells=[], dropped=dropped, closure=clos, closure_ok=not bad, cset=sorted(cset), only_cand=only_c, only_mine=only_m)
        for i in sorted(adopted):
            c = adopted[i]
            old = master.get((code, i, q))
            cd = cand.get((code, q, i))
            src_file = c["parts"][0].get("xlsx") if (c["parts"] and c["parts"][0].get("xlsx")) else meta["file"]
            cell = dict(code=code, quarter=q, item=i, item_name=ITEM_NAME[i], old=old, new=round(c["val"], 6), delta=None if old is None else round(c["val"] - old, 6), unit="백만원",
                        xml_file=src_file, xml_rcept=Path(src_file).stem if not c["parts"] or not c["parts"][0].get("xlsx") else "IR factsheet", source_unit=meta["unit"] if src_file == meta["file"] else "백만원",
                        parts=c["parts"], operands=c["operands"], abs_of_sum=c.get("abs_of_sum", False), formula=c["formula"], kind=c["kind"], cand_new=None if cd is None else cd["new"],
                        cand_equal=None if cd is None else abs(cd["new"] - c["val"]) <= 1e-3, cls=("fill" if old is None else "changed"), gold_cell=((code, i, q) in GOLD))
            b["cells"].append(cell)
        plan["buckets"].append(b)
    plan["_log_pl"] = LOG

    # ===== 0. masked-gold guard (a NEW gold cell whose value equals the builder source is a masked cell -> would need a ledger pin -> dropped; replaced gold cells: the new value must not be masked either)
    OUT.append("== 0. new / replaced gold cells that would be MASKED (value == builder source within the census tolerance) -> dropped (ticket: no new mask cells / no new pins)")
    for b in plan["buckets"]:
        keep = []
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if GV.gold_overlay_verdict(c["new"], src_pl.get(k)) in GV._GOLD_MASKED:
                OUT.append(f"   dropped {k}: new {c['new']} vs builder source {src_pl.get(k, {}).get('값')} -> masked (gold cell: {k in GOLD})")
                b["dropped"].append(dict(item=c["item"], old=c["old"], new=c["new"], cls="masked", reason="would be a masked gold cell (== builder source); a new ledger pin is forbidden by the ticket", in_cand=c["cand_new"] is not None))
                plan["findings"].append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], kind="masked gold cell not loaded",
                                             text=f"latest comparative {c['new']} equals the builder source value; master stays {c['old']}; loading it needs a new ledger pin"))
                continue
            keep.append(c)
        b["cells"] = keep
    adopted = {(c["code"], c["item"], c["quarter"]): c["new"] for b in plan["buckets"] for c in b["cells"]}
    cells_by_key = {(c["code"], c["item"], c["quarter"]): c for b in plan["buckets"] for c in b["cells"]}

    # ===== 1. differences against the e20 candidates
    OUT.append("== A. adopted cells whose value differs from the e20 candidate (and candidate cells I did not adopt)")
    for b in plan["buckets"]:
        for c in b["cells"]:
            if c["cand_new"] is not None and abs(c["cand_new"] - c["new"]) > 1e-3:
                OUT.append(f"   {c['code']} {c['quarter']} i{c['item']}: mine {c['new']} vs candidate {c['cand_new']} (diff {c['new'] - c['cand_new']:+.6f})")
        if b["only_cand"] or b["only_mine"]:
            OUT.append(f"   {b['quarter']}: candidate items not adopted {b['only_cand']} | adopted but not in candidates {b['only_mine']}")
    OUT.append(f"   adopted PL cells {len(adopted)} (e20 candidates {len(cand)})")

    # ===== 2. owner-gold overlap (only the approved cells may overlap)
    OUT.append("== B. owner-gold cells in the adopted set")
    gold_replace, gold_new = [], []
    for b in plan["buckets"]:
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if k not in GOLD:
                continue
            ok = co["gold_pl_ok"].get((c["quarter"], c["item"]))
            g = GOLD[k]
            if ok is None:
                held.append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], reason="owner gold overlaps a cell the owner has not approved -> bucket held"))
                OUT.append(f"   {k}: gold {g['값']} NOT APPROVED -> held")
                continue
            if ok == "print":
                gs, op = PF.orig_print_records(c["code"], c["quarter"], c["item"])
                tol = 2e-5 if op["unit"] == "원" else 1e-6
                cls = "A" if abs(g["값"] - op["value"]) <= tol else "B"
                c["gold_class"] = cls
                c["original_print"] = op
                c["gold_source_print"] = gs
                OUT.append(f"   {k}: gold {g['값']} | separate original print {op['value']} ({op['unit']}; lines {[(p['line'], p['printed'], p['label']) for p in op['lines']]}) | latest {c['new']} -> class {cls}")
                if cls != "A":
                    held.append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], reason="approved gold cell is not equal to the original print (class B) -> bucket held"))
            else:   # derived plug (item 7): value of 3-(4+5+6)
                c["gold_class"] = "D"
                legs_old = {i: master.get((code, i, c["quarter"])) for i in (3, 4, 5, 6)}
                form_old = None if legs_old[3] is None or legs_old[4] is None or legs_old[5] is None else legs_old[3] - (legs_old[4] + legs_old[5] + (legs_old[6] or 0.0))
                c["gold_derived"] = dict(formula="3 - (4 + 5 + 6)", master_legs=legs_old, formula_value_from_master_legs=None if form_old is None else round(form_old, 6), gold=g["값"], master=master.get(k))
                OUT.append(f"   {k}: gold {g['값']} is a derived plug (3-(4+5+6) of the master legs = {None if form_old is None else round(form_old, 6)}; live master {master.get(k)}) -> class D")
    held_buckets = {(h["code"], h["quarter"]) for h in held}
    for b in plan["buckets"]:
        if (b["code"], b["quarter"]) in held_buckets:
            continue
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if k in GOLD:
                old_e = GOLD[k]
                gold_replace.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=old_e["값"], note=make_note(c, b, replaced=old_e), old_entry=dict(old_e)))
            else:
                gold_new.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=c["old"], note=make_note(c, b)))

    # ===== 3. single-quarter seams
    OUT.append("== C. single-quarter (값_당분기) seam analysis")

    def cum_after(c_, i, q):
        return adopted.get((c_, i, q), master.get((c_, i, q)))

    EVID = {}

    def restated(c_, q, i):
        """is cum (code, i, q) on a restated basis, i.e. does the later filing's comparative differ from the master?"""
        g = GOLD.get((c_, i, q))
        if g is not None and g.get("was") is not None and abs(g["값"] - g["was"]) > 1.0 and (c_, i, q) not in cells_by_key:
            return True, f"gold {g['값']} replaced the original {g['was']}"
        if i not in TIER1:
            return False, "LOB item: not checked directly"
        v = t1(c_, P.later_fy(q), "prior", "cum")
        if i not in v or (i in (26, 27, 28, 29, 30) and v[i].get("absent")):
            return False, "item not printed"
        comp = sum(p["contribution_mn"] for p in v[i]["parts"])
        old = master.get((c_, i, q))
        if old is None:
            return False, "master empty"
        stq = stmt(c_, P.later_fy(q))
        band = 2e-5 if stq.unit in ("원", "천원") else 1.5
        EVID[(c_, q, i)] = dict(file=stq.rel, unit=stq.unit, parts=[P.pdict(p, stq.unit) for p in v[i]["parts"]], comparative=round(comp, 6), master=old)
        return abs(comp - old) > band, f"comparative {round(comp, 6)} vs master {old}"

    null_add, null_remove, set_add, set_remove = [], [], [], []
    seams = []
    touched_all = defaultdict(set)
    for (c_, i, q) in adopted:
        touched_all[c_].add((i, q))
        if int(q[5]) < 4:
            touched_all[c_].add((i, f"{q[:4]}.{int(q[5]) + 1}Q"))
    for c_, lst in sorted(touched_all.items()):
        for (i, qq) in sorted(lst, key=lambda x: (x[1], x[0])):
            n = int(qq[5])
            pq = prevq(qq)
            if n == 1:
                continue
            cur, prev = cum_after(c_, i, qq), cum_after(c_, i, pq)
            D = None if (cur is None or prev is None) else cur - prev
            live = masterd.get((c_, i, qq))
            rec = dict(code=c_, quarter=qq, item=i, derived_after=D, live_dangi=live, cur_adopted=(c_, i, qq) in adopted, prev_adopted=(c_, i, pq) in adopted, existing_null=(c_, qq, i) in NULLD,
                       existing_set=(c_, qq, i) in SETD)
            if D is None:
                rec.update(cls="derived_none", proposal="none")
                seams.append(rec)
                continue
            if n in (2, 3):
                if i not in TIER1:
                    rec.update(cls="lob_item_not_checked_directly", proposal="none")
                    seams.append(rec)
                    continue
                stq = stmt(c_, P.later_fy(qq))
                v3 = t1(c_, P.later_fy(qq), "prior", "3m")
                p3 = round(sum(p["contribution_mn"] for p in v3[i]["parts"]), 6)
                tol = 3 * 2e-5 if stq.unit in ("원", "천원") else 3.0
                rec["printed_3m"] = dict(value=p3, file=stq.rel, unit=stq.unit, parts=[P.pdict(p, stq.unit) for p in v3[i]["parts"]])
                rec["diff_vs_printed_3m"] = round(D - p3, 6)
                if abs(D - p3) <= tol:
                    rec.update(cls="consistent", proposal="none")
                    if rec["existing_set"]:
                        pinned = float(SETD[(c_, qq, i)][3])
                        rec["existing_set_value"] = pinned
                        if abs(pinned - D) <= 1e-6:
                            set_remove.append([c_, qq, i])
                            rec["proposal"] = "remove_redundant_set_dangi"
                else:
                    rec.update(cls="seam", proposal="set_dangi")
                    parts = rec["printed_3m"]["parts"]
                    src = f"{stq.rel}: " + " || ".join(f"L{p['line']} [{p['label']}] {p['printed']}" for p in parts) + \
                          f" (prior-year 3-month column printed in the {P.later_fy(qq)} report; the single quarter derived from the two cumulatives differs by {D - p3:+.6f})"
                    set_add.append([c_, qq, i, p3, src])
                seams.append(rec)
                continue
            if (c_, i, qq) in adopted:
                # Q4 cumulative adopted from the annual comparative (no printed 3-month column exists): the single quarter is consistent only when the 9M cumulative is on the SAME (new) basis,
                # i.e. adopted in this plan too; if the 9M comparative equals the master (unrestated) the two cumulatives sit on different bases -> blank (owner rule 2026-10-22)
                q3_adopted = (c_, i, pq) in adopted
                if i in TIER1:
                    rs, why = restated(c_, pq, i)
                else:
                    rs, why = None, "LOB item: 9M cumulative " + ("adopted in this plan" if q3_adopted else "unchanged")
                rec["q3_restated"] = rs
                rec["q3_adopted"] = q3_adopted
                rec["q3_evidence"] = why
                if (c_, pq, i) in EVID:
                    rec["q3_comparative"] = EVID[(c_, pq, i)]
                if q3_adopted:
                    rec.update(cls="consistent_both_restated", proposal="none")
                    if rec["existing_null"]:
                        null_remove.append([c_, qq, i])
                        rec["proposal"] = "remove_null_dangi"
                else:
                    rec.update(cls="seam_annual_vs_unrestated_9M", proposal="null_dangi")
                    if not rec["existing_null"]:
                        null_add.append([c_, qq, i])
            else:
                rec.update(cls="q4_unchanged_q3_adopted", proposal="none")
                if i in TIER1:
                    v4 = t1(c_, P.later_fy(qq), "prior", "cum")
                    if not (i in (26, 27, 28, 29, 30) and v4[i].get("absent")):
                        comp4 = sum(p["contribution_mn"] for p in v4[i]["parts"])
                        m4 = master.get((c_, i, qq))
                        rec["q4_comp_vs_master"] = [round(comp4, 6), m4]
                        st4 = stmt(c_, P.later_fy(qq))
                        band4 = 2e-5 if st4.unit in ("원", "천원") else 1.5
                        if m4 is not None and abs(comp4 - m4) > band4:
                            rec.update(cls="q4_changed_but_not_adopted", proposal="none (finding)")
            seams.append(rec)
    plan["seams"] = seams
    for r in seams:
        if r["cls"] in ("seam", "seam_annual_vs_unrestated_9M", "consistent_both_restated", "q4_changed_but_not_adopted") or r["proposal"] != "none":
            OUT.append(f"   {r['code']} {r['quarter']} i{r['item']}: {r['cls']} -> {r['proposal']} (D={fmt(r['derived_after'], 6)}, printed3m={r.get('printed_3m', {}).get('value')}, live={r['live_dangi']}, {r.get('q3_evidence', '')})")
    OUT.append(f"   seam table: {len(seams)} touched single-quarter cells; by class: " + str({k: sum(1 for r in seams if r['cls'] == k) for k in sorted({r['cls'] for r in seams})}))

    # ===== 4. CSM vectors
    OUT.append("== D. CSM vectors (latest comparative, separate basis)")
    csm_cells, csm_buckets = [], []
    for q in co["csm_quarters"]:
        res = co["csm"](q)
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
        cb["cand_items"] = sorted(i for (c_, q_, i) in cand_csm if q_ == q)
        cb["only_cand"] = sorted(set(cb["cand_items"]) - {c["item"] for c in cb["cells"]})
        cb["only_mine"] = sorted({c["item"] for c in cb["cells"]} - set(cb["cand_items"]))
        if "check_group_row_5" in res:
            g = res["check_group_row_5"]
            cb["group_row_amort"] = g["contribution_eok"] if isinstance(g, dict) else g[0] / 100.0
        csm_buckets.append(cb)
        OUT.append(f"   {code} {q}: exact={cb['vec_exact']} stored={vec} (2dp={two_dp}) old={old} cells {[c['item'] for c in cb['cells']]} cand {cb['cand_items']} only_cand={cb['only_cand']} only_mine={cb['only_mine']} closure_resid={cb['closure_resid']}")
    plan["csm_buckets"] = csm_buckets
    csm_gold_class = {}
    for c in csm_cells:
        k = (c["code"], c["item"], c["quarter"])
        if k not in GOLDC:
            continue
        ok = co["gold_csm_ok"].get((c["quarter"], c["item"]))
        g = GOLDC[k]
        if ok is None:
            held.append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], reason="owner CSM gold overlaps a cell the owner has not approved -> bucket held"))
            OUT.append(f"   CSM gold {k}: {g['값']} NOT APPROVED -> held")
            continue
        csm_gold_class[k] = analyse_csm_gold(co, c, g, ok)
        OUT.append(f"   CSM gold {k}: gold {g['값']} -> {csm_gold_class[k]['summary']}")
    plan["csm_gold_class"] = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in csm_gold_class.items()}

    # ===== 5. contract
    csm_gold_new, csm_gold_replace = [], []
    for c in csm_cells:
        k = (c["code"], c["item"], c["quarter"])
        if k in GOLDC:
            old_e = GOLDC[k]
            csm_gold_replace.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=old_e["값"], why=make_csm_why(c, replaced=old_e, cls=csm_gold_class.get(k)), old_entry=dict(old_e)))
        else:
            csm_gold_new.append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=c["old"], why=make_csm_why(c)))
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
    (EV / f"e23_plan_{key}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    (EV / f"e23_plan_{key}_report.txt").write_text("\n".join(LOG + [""] + OUT) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(OUT))
    print("PL cells", plan["n_pl_cells"], "CSM cells", plan["n_csm_cells"], "held", held)


def analyse_csm_gold(co, c, g, ok):
    """classify an approved CSM gold cell: 'orig' = gold equals the original-filing print (class A), 'chain' = chain-forced value (class B: neither the original annual print nor the latest comparative)"""
    code, q, item = c["code"], c["quarter"], c["item"]
    gv, was = g["값"], g.get("was")
    if ok == "chain":
        summary = (f"class B chain-forced: gold {gv} is neither the original annual print nor the latest comparative (the original annual print / builder value `was` = {was}; the latest comparative = {c['new']}); "
                   f"its note says: Q1-Q3 openings kept at the original value, Q4 forced to the same opening with item 4 as plug to keep the closing -> obsolete once Q1-Q3 move to the latest vector")
        return dict(summary=summary, cls="B", gold=gv, was=was, latest=c["new"])
    return dict(summary=f"class A (gold == the original filing print {gv}; `was` {was}); replaced by the latest comparative {c['new']}", cls="A", gold=gv, was=was, latest=c["new"])


def make_note(c, b, replaced=None):
    q, it = c["quarter"], c["item"]
    first = c["parts"][0].get("line") if c["parts"] else None
    cell0 = c["parts"][0].get("cell") if c["parts"] else None
    if cell0:
        lines_txt = f"IR 팩트시트 {c['xml_file']} 시트 '(3) UW Income' 셀 {cell0}"
    else:
        lines_txt = (f"L{first}" + (f" 외 합산 {len(c['parts'])}줄(증거 e23_plan_{b['code']}.json parts)" if len(c["parts"]) > 1 else "")) if first else "마스터 피연산자만"
    mo = ""
    if c.get("original_print"):
        o = c["original_print"]
        mo = (f"현재 마스터값(gold) {c['old']} 는 원 공시 rcept {o['rcept']}(단위 {o['unit']}) 별도 기준 인쇄값({o['value']}, 원문 " +
              ", ".join(f"L{p['line']}「{p['label']}」{p['printed']}" for p in o["lines"]) + ")과 일치. ")
    elif c.get("gold_derived"):
        gd = c["gold_derived"]
        mo = f"현재 gold {gd['gold']} 는 파생 plug(3-(4+5+6)) 이고 마스터 피연산자 기준 식 값은 {gd['formula_value_from_master_legs']} (라이브 마스터 {gd['master']}). "
    elif c["old"] is not None:
        mo = f"변경 전 마스터값 {c['old']}. "
    ops = ""
    if c["operands"]:
        ops = " 피연산자: " + ", ".join(f"{o['item']}번={o['value']}({o['source']})" for o in c["operands"]) + "."
    pre = ""
    if replaced is not None:
        pre = (f"owner 2026-10-23 승인, 연쇄용 gold 교체(D3 결정표 · gold_cells_replaced.csv): 이전 gold 값 {replaced['값']}, 이전 was {replaced.get('was')}, "
               f"이전 note 요약 「{str(replaced.get('note'))[:140]}…」(전문은 git HEAD 의 data/_gold/user_pl_cells.json). ")
    return (pre + f"{LIVE_NOTE}: 별도(OFS) 기준 {b['meta']['kind']} 경로, {b['meta']['later_fy']} 의 전기 {q[:4]}.{q[5]}Q 누적({per_of(q)}) 열 → {c['new']} 백만원. "
            f"원문 {c['xml_file']} {lines_txt}. {mo}변동 {c['delta'] if c['delta'] is not None else '신규'}. 산식: {c['formula']}.{ops} 증거 {EVREL}/e23_plan_{b['code']}.json")


def make_csm_why(c, replaced=None, cls=None):
    lines = [f"L{p['line']} {p['printed']}" for p in c["parts"][:6]]
    cite = ", ".join(lines) + (f" 외 {len(c['parts']) - 6}셀" if len(c["parts"]) > 6 else "")
    pre = ""
    if replaced is not None:
        pre = (f"owner 2026-10-23 승인, 연쇄용 gold 교체: 이전 gold {replaced['값']} (이전 was {replaced.get('was')}) 를 교체: {cls['summary'] if cls else ''} | ")
    deriv = f" 이 항목은 인쇄 셀이 아니라 {c['derived']} 로 계산한 값이다." if c.get("derived") else ""
    return (pre + f"{LIVE_NOTE}: 최신 공시의 전기 열(별도 기준, 발행 보험계약 CSM) {c['src']}. 인쇄 셀: {cite or '없음'} -> {c['exact']} 억원, 저장값 {c['new']}.{deriv} 증거 {EVREL}/e23_plan_{c['code']}.json")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CO:
        raise SystemExit("usage: e23_plan.py <" + "|".join(CO) + ">")
    build(sys.argv[1])
