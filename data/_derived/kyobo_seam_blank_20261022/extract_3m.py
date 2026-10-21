"""Read-only: the restated 2023.3Q THREE-MONTH values printed in the FY2024 Q3 report (prior-year 3-month column), separate basis, for every PL item.

Two independent derivations, cross-checked item by item:
  A  raw XML  : separate income statement rows (multi-line <TE> cells, 원) and the 4 separate-basis note tables (<TD>, 백만원); the cited cell is the prior-year 3-MONTH cell = index 2 of the
                4 numeric cells [당기 3개월, 당기 누적, 전기 3개월, 전기 누적]  (line number of that cell)
  B  harness  : the production Tier-1 parser fetch_dart_fs._parse on the FS-API cache with the prior-year 3-month column swapped in (frmtrm_q_amount), the production Kyobo Tier-2 handler with its
                first-number reader switched to index 2, and the production assemble() -> the same 32-item vector the cumulative refresh used.
Then the single-quarter identities (same set as the cumulative check) decide which items may be SET; the rest stay null.
Outputs: seam_3m_vector.csv, seam_3m_plan.json, seam_3m_extract.txt
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
PLD = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"
CSMD = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
sys.path.insert(0, str(PLD))
sys.path.insert(0, str(CSMD))
import stmt_parse as P  # noqa: E402
import stmt_lines as S  # noqa: E402
import plib  # noqa: E402  (chdir ROOT; production PL modules)
from xmltab import parse_tables  # noqa: E402

BP, C, F = plib.BP, plib.C, plib.F
sys.stdout.reconfigure(encoding="utf-8")
CODE, Q, FY, LATER = "KR0073", "2023.3Q", "FY2024_Q3", "2024.3Q"
TOL_IDENT = 0.01      # 백만원, the tolerance of the cumulative identity check (identities.txt)
TOL_X = 1e-3          # raw vs harness agreement, 백만원

# ------------------------------------------------------------------ B: harness 3-month vector
def t1_prior3m():
    cc = plib.corp_code(LATER)
    f = plib.DART / "_fs_api_cache" / f"{cc}_{LATER[:4]}_{plib.REPRT[LATER[5]]}_OFS.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    rows = []
    for a in d.get("list", []):
        b = dict(a)
        b["thstrm_amount"] = a.get("frmtrm_q_amount")        # prior-year 3 MONTHS (DART field frmtrm_q_amount)
        b["thstrm_add_amount"] = a.get("frmtrm_q_amount")    # _parse reads thstrm_add_amount (cumulative) for quarterly filings
        rows.append(b)
    return F._parse({**d, "list": rows}, False), f


def first_num_3m(t, label_variants):
    """prior-year 3-month cell of the first matching row: 4 numbers [당기 3M, 당기 누적, 전기 3M, 전기 누적] -> index 2; anything else -> None."""
    if t is None:
        return None
    for r in t.rows:
        lf = C._life_label_flat(r)
        nums = C._row_nums(r)
        if not nums:
            continue
        for v in label_variants:
            if v.replace(" ", "") in lf:
                return nums[2] if len(nums) >= 4 else None
    return None


def harness_vector():
    t1, src = t1_prior3m()
    tables = plib.parse_tables(plib.raw_dirs(LATER))
    C._life_first_num = first_num_3m
    try:
        t2 = C.extract_tier2_kyobo(tables)
    finally:
        C._life_first_num = plib._orig_first_num
    v = BP.assemble(t1, t2 or None, True, zero_fill_ok=frozenset())
    return {n: v.get(n) for n in range(1, 33)}, t1, t2, str(src.relative_to(ROOT)).replace("\\", "/")


# ------------------------------------------------------------------ A: raw XML 3-month cells
class Filing:
    SL = {1: ["보험손익"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익"], 21: ["영업외손익"],
          22: ["법인세차감전순이익", "법인세비용차감전순이익"], 23: ["법인세비용"],
          24: ["당기순이익(손실)", "당기순이익", "분기순이익(손실)", "분기순이익", "반기순이익(손실)", "반기순이익"],
          25: ["기타포괄손익"],
          26: ["기타포괄손익-공정가치측정금융자산관련손익", "기타포괄손익-공정가치측정채무증권평가손익", "기타포괄손익-공정가치측정금융자산평가손익"],
          27: ["보험계약자산(부채)순금융손익", "보험계약자산부채순금융손익"],
          28: ["현금흐름위험회피파생상품평가손익", "위험회피파생상품평가손익", "현금흐름위험회피", "위험회피목적파생상품평가손익"],
          29: ["기타포괄손익-공정가치측정유가증권평가손익", "기타포괄손익-공정가치측정지정지분증권평가손익"],
          30: ["재보험계약자산(부채)순금융손익", "재보험계약자산부채순금융손익"],
          31: ["총포괄손익", "연결반기총포괄손익", "반기총포괄손익", "분기총포괄손익", "연결분기총포괄손익", "연결총포괄손익"],
          "rev": ["보험수익"], "cost": ["보험비용"], "rerev": ["재보험수익"], "recost": ["재보험비용"],
          "fin_ins_inc": ["보험금융수익"], "fin_ins_exp": ["보험금융비용"], "fin_re_inc": ["재보험금융수익"], "fin_re_exp": ["재보험금융비용"]}
    MARK = {("발행한 보험계약", "보험수익"): ["(3)당기손익에인식한보험계약마진"],
            ("발행한 보험계약", "보험서비스비용"): ["(1)실제보험금", "(2)실제계약유지비용"],
            ("재보험계약", "재보험수익"): ["발생재보험금"],
            ("재보험계약", "재보험비용"): ["예상재보험금", "보험계약마진상각"]}

    def __init__(self, fy):
        self.path = S.main_xml(fy)
        self.lines = P.read_lines(self.path)
        sec = P.sections(self.lines)
        self.sep_fs = P.rows_in_range(self.lines, *sec["sep_fs"])
        tabs, _ = parse_tables(str(self.path))
        lo, hi = sec["sep_notes"]
        self.note_tabs = [t for t in tabs if lo < t["start"] < hi]
        self.rel = str(self.path.relative_to(ROOT)).replace("\\", "/")

    def stmt_all(self, labels):
        """every statement row whose label is in `labels` -> [(label, value_백만원_prior3M, line, text, n_numeric_cells)]"""
        out = []
        for r in self.sep_fs:
            if not r["cells"]:
                continue
            lab = r["cells"][0][0].replace(" ", "")
            if lab in labels:
                nums = [(P.num(t), ln, t) for t, ln in r["cells"][1:] if P.num(t) is not None]
                if len(nums) >= 4:
                    v, ln, txt = nums[2]
                    out.append({"label": r["cells"][0][0], "value": v / 1e6, "line": ln, "text": txt, "n": len(nums)})
                elif nums:
                    out.append({"label": r["cells"][0][0], "value": None, "line": None, "text": f"only {len(nums)} numeric cells", "n": len(nums)})
        return out

    def note(self, cap_all, row_prefixes):
        marks = self.MARK[tuple(cap_all)]
        for t in self.note_tabs:
            labs = [cells[0].replace(" ", "") for ln, cells, cl in t["rows"] if cells]
            if all(any(l.startswith(m) for l in labs) for m in marks):
                for ln, cells, cl in t["rows"]:
                    lab = cells[0].replace(" ", "")
                    if any(lab.startswith(p) for p in row_prefixes):
                        nums = [(P.num(c), cl[k], c) for k, c in enumerate(cells) if k >= 1 and P.num(c) is not None]
                        if len(nums) >= 4:
                            v, line, txt = nums[2]
                            return {"label": cells[0], "value": v, "line": line, "text": txt}
                        return {"label": cells[0], "value": None, "line": None, "text": f"only {len(nums)} numeric cells"}
        return None


def cite(f, rec, unit):
    return f"{f.rel}:L{rec['line']} [{rec['label'][:30]}] {rec['text']}{unit}"


def main():
    hv, t1, t2, t1src = harness_vector()
    f = Filing(FY)
    raw = {}      # item -> dict(value, kind, cite, ok_inputs)

    def pick(labels, want):
        """candidates of the statement with the 3-month cell; prefer the one equal to the harness value"""
        cands = [c for c in f.stmt_all(labels) if c["value"] is not None]
        if not cands:
            return None
        if want is not None:
            for c in cands:
                if abs(c["value"] - want) <= TOL_X:
                    return c
        return cands[0]

    for i in (1, 16, 17, 20, 22, 24, 25, 26, 27, 28, 29, 30, 31):
        r = pick(Filing.SL[i], hv.get(i))
        raw[i] = {"value": None if r is None else r["value"], "kind": "STATEMENT", "cite": None if r is None else cite(f, r, "원"), "src": f"별도 포괄손익계산서 '{r['label'] if r else Filing.SL[i][0]}' 전기 3개월 열"}
    r = pick(Filing.SL[21], hv.get(21))
    raw[21] = {"value": None if r is None else r["value"], "kind": "STATEMENT", "cite": None if r is None else cite(f, r, "원"), "src": "별도 포괄손익계산서 '영업외손익' 전기 3개월 열"}
    r = pick(Filing.SL[23], abs(hv[23]) if hv.get(23) is not None else None)
    raw[23] = {"value": None if r is None else r["value"], "kind": "STATEMENT", "cite": None if r is None else cite(f, r, "원"), "src": "별도 포괄손익계산서 '법인세비용' 전기 3개월 열 (부호는 마스터 규약: 양수)"}
    fin = {k: pick(Filing.SL[k], None) for k in ("fin_ins_inc", "fin_ins_exp", "fin_re_inc", "fin_re_exp")}
    # production convention (fetch_dart_fs._parse): a missing 보험금융수익 row counts as 0 -- Kyobo's separate statement has no such row; the other three must be printed
    if all(fin[k] is not None for k in ("fin_ins_exp", "fin_re_inc", "fin_re_exp")):
        fi = fin["fin_ins_inc"]["value"] if fin["fin_ins_inc"] is not None else 0.0
        val = fi - fin["fin_ins_exp"]["value"] + fin["fin_re_inc"]["value"] - fin["fin_re_exp"]["value"]
        raw[19] = {"value": val, "kind": "STATEMENT (3 rows; 보험금융수익 row absent = 0)", "cite": " || ".join(cite(f, r, "원") for r in fin.values() if r is not None),
                   "src": "(보험금융수익 없음=0) − 보험금융비용 + 재보험금융수익 − 재보험금융비용 (전기 3개월 열)"}
    else:
        raw[19] = {"value": None, "kind": "STATEMENT (rows)", "cite": None, "src": "보험금융비용 / 재보험금융수익 / 재보험금융비용 rows not all printed"}
    rev, cost, rerev, recost = (pick(Filing.SL[k], None) for k in ("rev", "cost", "rerev", "recost"))
    if rev and cost:
        raw[3] = {"value": rev["value"] - abs(cost["value"]), "kind": "STATEMENT (2 rows)", "cite": cite(f, rev, "원") + " || " + cite(f, cost, "원"), "src": "보험수익 − 보험비용 (전기 3개월 열)"}
    else:
        raw[3] = {"value": None, "kind": "STATEMENT (2 rows)", "cite": None, "src": "rows missing"}
    if rerev and recost:
        raw[8] = {"value": rerev["value"] - abs(recost["value"]), "kind": "STATEMENT (2 rows)", "cite": cite(f, rerev, "원") + " || " + cite(f, recost, "원"), "src": "재보험수익 − 재보험비용 (전기 3개월 열)"}
    else:
        raw[8] = {"value": None, "kind": "STATEMENT (2 rows)", "cite": None, "src": "rows missing"}
    # notes (백만원)
    n4 = f.note(("발행한 보험계약", "보험수익"), ["(3)당기손익에인식한보험계약마진"])
    n5 = f.note(("발행한 보험계약", "보험수익"), ["(2)비금융위험에대한위험조정변동분"])
    ne = f.note(("발행한 보험계약", "보험수익"), ["(1)발생한보험서비스비용", "(1)발생한보험서비스수익"])
    a1 = f.note(("발행한 보험계약", "보험서비스비용"), ["(1)실제보험금"])
    a2 = f.note(("발행한 보험계약", "보험서비스비용"), ["(2)실제계약유지비용"])
    a3 = f.note(("발행한 보험계약", "보험서비스비용"), ["(3)실제투자관리비"])
    n9 = f.note(("재보험계약", "재보험비용"), ["보험계약마진상각"])
    n10 = f.note(("재보험계약", "재보험비용"), ["위험조정변동", "비금융위험에대한위험조정"])
    r11a = f.note(("재보험계약", "재보험수익"), ["발생재보험금"])
    r11b = f.note(("재보험계약", "재보험비용"), ["예상재보험금"])
    ok = lambda *rs: all(r is not None and r["value"] is not None for r in rs)
    raw[4] = {"value": abs(n4["value"]) if ok(n4) else None, "kind": "NOTE", "cite": cite(f, n4, "백만") if ok(n4) else None, "src": "보험수익 주석 (3) 당기손익에 인식한 보험계약마진금액, 전기 3개월 열"}
    raw[5] = {"value": abs(n5["value"]) if ok(n5) else None, "kind": "NOTE", "cite": cite(f, n5, "백만") if ok(n5) else None, "src": "보험수익 주석 (2) 비금융위험에 대한 위험조정 변동분, 전기 3개월 열"}
    raw[6] = {"value": (abs(ne["value"]) - abs(a1["value"] + a2["value"] + a3["value"])) if ok(ne, a1, a2, a3) else None, "kind": "NOTE (4 rows)",
              "cite": " || ".join(cite(f, r, "백만") for r in (ne, a1, a2, a3) if r) if ok(ne, a1, a2, a3) else None, "src": "예실차 = |(1) 발생한 보험서비스비용| − (실제보험금 + 실제계약유지비용 + 실제투자관리비), 전기 3개월 열"}
    raw[9] = {"value": -abs(n9["value"]) if ok(n9) else None, "kind": "NOTE", "cite": cite(f, n9, "백만") if ok(n9) else None, "src": "재보험비용 주석 '보험계약마진상각' 전기 3개월 열 (부호 −|x|)"}
    raw[10] = {"value": -abs(n10["value"]) if ok(n10) else None, "kind": "NOTE", "cite": cite(f, n10, "백만") if ok(n10) else None, "src": "재보험비용 주석 '위험조정변동' 전기 3개월 열 (부호 −|x|)"}
    raw[11] = {"value": (abs(r11a["value"]) - abs(r11b["value"])) if ok(r11a, r11b) else None, "kind": "NOTE (2 rows)",
               "cite": " || ".join(cite(f, r, "백만") for r in (r11a, r11b) if r) if ok(r11a, r11b) else None, "src": "재보험 예실차 = |발생재보험금| − |예상재보험금|, 전기 3개월 열"}
    # derived from printed inputs (same definitions as the cumulative refresh)
    g = lambda k: raw[k]["value"]
    raw[2] = {"value": g(3) + g(8) if None not in (g(3), g(8)) else None, "kind": "DERIVED (3+8)", "cite": "= item3 + item8", "src": "생명장기 손익 = 원수손익 + 재보험손익"}
    raw[7] = {"value": g(3) - (g(4) + g(5) + g(6)) if None not in (g(3), g(4), g(5), g(6)) else None, "kind": "DERIVED (3-4-5-6)", "cite": "= item3 − item4 − item5 − item6", "src": "기타 생명장기 원수손익 = 원수손익 − (CSM상각 + 위험조정 변동 + 예실차)"}
    raw[12] = {"value": g(8) - (g(9) + g(10) + g(11)) if None not in (g(8), g(9), g(10), g(11)) else None, "kind": "DERIVED (8-9-10-11)", "cite": "= item8 − item9 − item10 − item11", "src": "기타 생명장기 재보험손익 = 재보험손익 − (9 + 10 + 11)"}
    raw[18] = {"value": g(17) - g(19) if None not in (g(17), g(19)) else None, "kind": "DERIVED (17-19)", "cite": "= item17 − item19", "src": "투자이익 = 투자손익 − 보험금융손익"}
    raw[32] = {"value": g(25) - sum(g(k) for k in (26, 27, 28, 29, 30)) if None not in tuple(g(k) for k in (25, 26, 27, 28, 29, 30)) else None, "kind": "DERIVED (25-Σ26..30)",
               "cite": "= item25 − Σ(26..30)", "src": "기타 포괄손익(미분류) = 기타포괄손익 − (26+27+28+29+30)"}
    raw[15] = {"value": None, "kind": "NOT PRINTED", "cite": "(no 기타영업수익 row in the statement; the cumulative 0.0 is an assemble() default for 생보)", "src": "기타영업수익: 3개월 열에 인쇄된 행이 없다"}

    # ---- agreement raw vs harness (백만원)
    rows, agree = [], {}
    for i in range(1, 33):
        if i in (13, 14):
            continue
        rv, hvv = raw[i]["value"], hv.get(i)
        if i == 23 and hvv is not None:
            hvv = abs(hvv)
        if i in (4, 5):
            hvv = abs(hvv) if hvv is not None else None
        a = (rv is not None and hvv is not None and abs(rv - hvv) <= TOL_X)
        agree[i] = a
    # ---- identities on the raw vector (15 := 0 only for the closure test; it is NOT published)
    v = {i: raw[i]["value"] for i in raw}
    v15 = 0.0
    ident = {
        "20=1+17": (None if None in (v[20], v[1], v[17]) else v[20] - (v[1] + v[17]), (20, 1, 17)),
        "22=20+21": (None if None in (v[22], v[20], v[21]) else v[22] - (v[20] + v[21]), (22, 20, 21)),
        "24=22-23": (None if None in (v[24], v[22], v[23]) else v[24] - (v[22] - v[23]), (24, 22, 23)),
        "31=24+25": (None if None in (v[31], v[24], v[25]) else v[31] - (v[24] + v[25]), (31, 24, 25)),
        "17=18+19": (None if None in (v[17], v[18], v[19]) else v[17] - (v[18] + v[19]), (17, 18, 19)),
        "25=26+27+28+29+30+32": (None if None in tuple(v[k] for k in (25, 26, 27, 28, 29, 30, 32)) else v[25] - sum(v[k] for k in (26, 27, 28, 29, 30, 32)), (25, 26, 27, 28, 29, 30, 32)),
        "1=2+15-16": (None if None in (v[1], v[2], v[16]) else v[1] - (v[2] + v15 - v[16]), (1, 2, 15, 16)),
        "2=3+8": (None if None in (v[2], v[3], v[8]) else v[2] - (v[3] + v[8]), (2, 3, 8)),
        "3=4+5+6+7": (None if None in tuple(v[k] for k in (3, 4, 5, 6, 7)) else v[3] - sum(v[k] for k in (4, 5, 6, 7)), (3, 4, 5, 6, 7)),
        "8=9+10+11+12": (None if None in tuple(v[k] for k in (8, 9, 10, 11, 12)) else v[8] - sum(v[k] for k in (9, 10, 11, 12)), (8, 9, 10, 11, 12)),
    }
    bad_items = set()
    for name, (res, items) in ident.items():
        if res is None or abs(res) > TOL_IDENT:
            bad_items |= {i for i in items if i != 15}
    # ---- decision per item
    head = {}
    import subprocess
    p = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:PL_breakdown.json"], capture_output=True)
    for r in json.loads(p.stdout.decode("utf-8")):
        if r["원보험사코드"] == CODE and r["공시분기"] == Q:
            head[r["항목번호"]] = r
    plan_set, plan_null, plan_keep, table = [], [], [], []
    for i in range(1, 33):
        hrow = head[i]
        if i in (13, 14):
            plan_keep.append(i)
            table.append({"item": i, "name": hrow["항목명"], "decision": "KEEP", "reason": "builder 0.0 (생보 자동차/일반 LOB), 3e53aef8 전에도 값이 있었다", "value_3m": None, "head_dangi": hrow.get("값_당분기"), "harness": None, "agree": None, "kind": "", "cite": ""})
            continue
        val = raw[i]["value"]
        reasons = []
        if val is None:
            reasons.append("not printed / row missing")
        if not agree.get(i, False) and val is not None:
            reasons.append(f"raw {val} != harness {hv.get(i)}")
        if i in bad_items:
            reasons.append("an identity it takes part in does not close")
        decision = "SET" if not reasons else "NULL"
        table.append({"item": i, "name": hrow["항목명"], "decision": decision, "reason": "; ".join(reasons), "value_3m": val, "head_dangi": hrow.get("값_당분기"),
                      "harness": hv.get(i), "agree": agree.get(i), "kind": raw[i]["kind"], "cite": raw[i]["cite"], "src": raw[i]["src"], "cum": hrow.get("값")})
        if decision == "SET":
            plan_set.append([CODE, Q, i, round(val, 6), raw[i]["cite"] if raw[i]["kind"].startswith(("STATEMENT", "NOTE")) else f"{f.rel} (derived: {raw[i]['cite']})"])
        else:
            plan_null.append([CODE, Q, i])
    # ---- outputs
    with open(HERE / "seam_3m_vector.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "name", "decision", "reason", "value_3m", "cum", "head_dangi", "harness", "agree", "kind", "src", "cite"], extrasaction="ignore")
        w.writeheader()
        w.writerows(table)
    (HERE / "seam_3m_plan.json").write_text(json.dumps({"filing": f.rel, "quarter": Q, "t1_source": t1src, "set": plan_set, "null": plan_null, "keep": plan_keep,
                                                         "identity_residuals": {k: (None if r is None else round(r, 6)) for k, (r, _i) in ident.items()}}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    lines = [f"filing {f.rel}; Tier-1 source {t1src}", "", "identity residuals on the printed 3-month vector (백만원; 15 := 0 only inside 1=2+15-16):"]
    for k, (r, _i) in ident.items():
        lines.append(f"   {k:24s} {('missing' if r is None else f'{r:+.6f}')}")
    lines += ["", "item  decision  3M printed (백만원)   harness (FS-API+handler)   HEAD 값_당분기 (derived)   delta(3M-HEAD)   raw==harness  reason"]
    for t in table:
        v3 = t["value_3m"]
        hd = t["head_dangi"]
        d = "" if v3 is None or hd is None else f"{v3 - hd:+,.1f}"
        hh = t['harness']
        lines.append(f"{t['item']:>4d}  {t['decision']:8s} {('' if v3 is None else f'{v3:,.4f}'):>20s} {('' if hh is None else f'{hh:,.4f}'):>24s} {('' if hd is None else f'{hd:,.4f}'):>26s} {d:>16s}   {str(t['agree']):>12s}  {t['reason']}")
    lines += ["", f"SET {len(plan_set)}: {[c[2] for c in plan_set]}", f"NULL {len(plan_null)}: {[c[2] for c in plan_null]}", f"KEEP {len(plan_keep)}: {plan_keep}"]
    (HERE / "seam_3m_extract.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
