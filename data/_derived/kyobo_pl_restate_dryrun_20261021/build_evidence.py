"""Read-only: raw-file + raw-line citation for every planned PL cell (pl_plan.json) -> pl_cell_changes.csv.

Per later filing: separate income statement rows (multi-line <TE> cells, 원) and the 4 separate-basis note tables (single-line <TD>, 백만원);
the cited cell is the LAST numeric cell of the row (= prior-period cumulative column of 2/4-column layouts).  Every citation is verified against the planned value;
mismatches are reported (never silently accepted).
"""
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"))
import stmt_parse as P  # noqa: E402
import stmt_lines as S  # noqa: E402
from xmltab import parse_tables  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
LATER_FY = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3", "2023.4Q": "FY2024_Q4", "2024.1Q": "FY2025_Q1", "2024.2Q": "FY2025_Q2"}
plan = json.loads((HERE / "pl_plan.json").read_text(encoding="utf-8"))["plan"]
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
vec_new = {}
cur = {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
vec_new = {q: dict(v) for q, v in cur.items()}
for c in plan:
    vec_new[c["quarter"]][c["item"]] = c["new"]

SL = {  # statement label candidates per item (space-stripped, exact)
    1: ["보험손익"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익"], 21: ["영업외손익"],
    22: ["법인세차감전순이익", "법인세비용차감전순이익"], 23: ["법인세비용"],
    24: ["당기순이익(손실)", "당기순이익", "분기순이익(손실)", "분기순이익", "반기순이익(손실)", "반기순이익"],
    25: ["기타포괄손익"],
    26: ["기타포괄손익-공정가치측정금융자산관련손익", "기타포괄손익-공정가치측정채무증권평가손익", "기타포괄손익-공정가치측정금융자산평가손익"],
    27: ["보험계약자산(부채)순금융손익", "보험계약자산부채순금융손익"],
    28: ["현금흐름위험회피파생상품평가손익", "위험회피파생상품평가손익", "현금흐름위험회피"],
    29: ["기타포괄손익-공정가치측정유가증권평가손익", "기타포괄손익-공정가치측정지정지분증권평가손익"],
    30: ["재보험계약자산(부채)순금융손익", "재보험계약자산부채순금융손익"],
    31: ["총포괄손익", "연결반기총포괄손익", "반기총포괄손익", "분기총포괄손익", "연결분기총포괄손익", "연결총포괄손익"],
    "rev": ["보험수익"], "cost": ["보험비용"], "rerev": ["재보험수익"], "recost": ["재보험비용"],
    "fin_re_inc": ["재보험금융수익"], "fin_ins_exp": ["보험금융비용"], "fin_re_exp": ["재보험금융비용"], "fin_ins_inc": ["보험금융수익"],
}


def prior_idx(n):
    """index of the prior-period cumulative cell: 2 cells [당기, 전기] -> 1; 3 cells [당기, 전기, 전전기] -> 1; 4 cells [당기 3M, 당기 누적, 전기 3M, 전기 누적] -> 3"""
    return 3 if n >= 4 else 1


def short(p):
    return str(p.relative_to(ROOT)).replace("\\", "/")


class Filing:
    def __init__(self, fy):
        self.fy = fy
        self.path = S.main_xml(fy)
        self.lines = P.read_lines(self.path)
        sec = P.sections(self.lines)
        self.sep_fs = P.rows_in_range(self.lines, *sec["sep_fs"])
        tabs, _ = parse_tables(str(self.path))
        lo, hi = sec["sep_notes"]
        self.note_tabs = [t for t in tabs if lo < t["start"] < hi]

    def stmt(self, labels, want=None):
        """first statement row whose label matches one of labels and (if given) whose last numeric cell/1e6 == want"""
        best = None
        for r in self.sep_fs:
            if not r["cells"]:
                continue
            lab = r["cells"][0][0].replace(" ", "")
            if lab in labels:
                nums = [(P.num(t), ln, t) for t, ln in r["cells"][1:] if P.num(t) is not None]
                if not nums:
                    continue
                v, ln, txt = nums[prior_idx(len(nums))]
                rec = {"label": r["cells"][0][0], "value": v / 1e6, "line": ln, "text": txt}
                if want is None or abs(rec["value"] - want) <= 1e-3:
                    return rec
                best = best or rec
        return best

    MARK = {("발행한 보험계약", "보험수익"): ["(3)당기손익에인식한보험계약마진"],
            ("발행한 보험계약", "보험서비스비용"): ["(1)실제보험금", "(2)실제계약유지비용"],
            ("재보험계약", "재보험수익"): ["발생재보험금"],
            ("재보험계약", "재보험비용"): ["예상재보험금", "보험계약마진상각"]}

    def note(self, cap_all, row_prefixes):
        marks = self.MARK[tuple(cap_all)]
        for t in self.note_tabs:
            labs = [cells[0].replace(" ", "") for ln, cells, cl in t["rows"] if cells]
            if all(any(l.startswith(m) for l in labs) for m in marks):
                cap = t["caption"] or ""
                for ln, cells, cl in t["rows"]:
                    lab = cells[0].replace(" ", "")
                    if any(lab.startswith(p) for p in row_prefixes):
                        nums = [(P.num(c), cl[k], c) for k, c in enumerate(cells) if k >= 1 and P.num(c) is not None]
                        if nums:
                            v, line, txt = nums[prior_idx(len(nums))]
                            return {"label": cells[0], "value": v, "line": line, "text": txt, "caption": cap[:40]}
        return None


def fmt_cite(f, rec, unit):
    return f"{short(f.path)}:L{rec['line']} [{rec['label'][:30]}] {rec['text']}{unit}"


out_rows, bad = [], []
fil = {}
for c in plan:
    q, i, new = c["quarter"], c["item"], c["new"]
    f = fil.get(q) or fil.setdefault(q, Filing(LATER_FY[q]))
    cites, kind, desc, ok = [], "", "", True

    def need(rec, expect_scale, expect):
        global ok
        return rec is not None and abs(rec["value"] * expect_scale - expect) <= 1e-3

    if i in SL and isinstance(i, int) and i in (1, 16, 17, 20, 22, 24, 25, 26, 27, 28, 29, 30, 31):
        rec = f.stmt(SL[i], want=new)
        kind, desc = "T1 statement", f"별도 포괄손익계산서 '{rec['label'] if rec else SL[i][0]}' 전기(누적) 열"
        if i == 17:
            # production may fold 보험금융손익 into 투자손익 when 영업이익 confirms the gross form (not the case for KR0073: 20 = 1 + 17)
            pass
        if rec and abs(rec["value"] - new) <= 1e-3:
            cites.append(fmt_cite(f, rec, "원"))
        else:
            ok = False
            cites.append(f"MISMATCH stmt={rec}")
    elif i == 21:
        rec = f.stmt(SL[21], want=new)
        kind, desc = "T1 derived (22-20)", "세전이익 − 영업이익 (명세 '영업외손익' 행과 대조)"
        cites.append(fmt_cite(f, rec, "원") if rec else "no 영업외손익 row")
        ok = bool(rec and abs(rec["value"] - new) <= 1e-3)
    elif i == 23:
        rec = f.stmt(SL[23], want=new)
        kind, desc = "T1 derived (22-24)", "세전이익 − 당기순이익 (명세 '법인세비용' 행과 대조)"
        cites.append(fmt_cite(f, rec, "원") if rec else "no 법인세비용 row")
        ok = bool(rec and abs(abs(rec["value"]) - abs(new)) <= 1e-3)
    elif i == 19:
        recs = {k: f.stmt(SL[k]) for k in ("fin_ins_inc", "fin_ins_exp", "fin_re_inc", "fin_re_exp")}
        calc = ((recs["fin_ins_inc"] or {}).get("value", 0) - (recs["fin_ins_exp"] or {}).get("value", 0)
                + (recs["fin_re_inc"] or {}).get("value", 0) - (recs["fin_re_exp"] or {}).get("value", 0))
        kind, desc = "T1 derived (FIN accounts)", "보험금융수익 − 보험금융비용 + 재보험금융수익 − 재보험금융비용"
        cites = [fmt_cite(f, r, "원") for r in recs.values() if r]
        ok = abs(calc - new) <= 1e-3
    elif i == 18:
        kind, desc = "T1 derived (17-19)", "투자손익 − 보험금융손익"
        cites = [f"= item17 {vec_new[q][17]:,.6f} − item19 {vec_new[q][19]:,.6f}"]
        ok = abs((vec_new[q][17] - vec_new[q][19]) - new) <= 1e-3
    elif i in (3, 8):
        a, b = ("rev", "cost") if i == 3 else ("rerev", "recost")
        ra, rb = f.stmt(SL[a]), f.stmt(SL[b])
        kind, desc = "T1 derived", ("보험수익 − 보험비용" if i == 3 else "재보험수익 − 재보험비용")
        cites = [fmt_cite(f, ra, "원"), fmt_cite(f, rb, "원")] if ra and rb else ["rows missing"]
        ok = bool(ra and rb and abs((ra["value"] - abs(rb["value"])) - new) <= 1e-3)
    elif i == 2:
        kind, desc = "DERIVED (3+8)", "생명장기 손익 = 원수손익 + 재보험손익"
        cites = [f"= item3 {vec_new[q][3]:,.6f} + item8 {vec_new[q][8]:,.6f}"]
        ok = abs(vec_new[q][3] + vec_new[q][8] - new) <= 1e-3
    elif i == 15:
        kind, desc = "DEFAULT 0", "기타영업수익: 명세에 별도 행이 없으면 0 (assemble() 관례, 생보)"
        cites = ["(no raw cell: statement has no separate 기타영업수익 row)"]
    elif i == 4:
        rec = f.note(("발행한 보험계약", "보험수익"), ["(3)당기손익에인식한보험계약마진"])
        kind, desc = "T2 note", "보험수익 주석 (3) 당기손익에 인식한 보험계약마진금액, 전기(누적) 열"
        cites = [fmt_cite(f, rec, "백만")] if rec else ["row missing"]
        ok = bool(rec and abs(abs(rec["value"]) - new) <= 1e-3)
    elif i == 5:
        rec = f.note(("발행한 보험계약", "보험수익"), ["(2)비금융위험에대한위험조정변동분"])
        kind, desc = "T2 note", "보험수익 주석 (2) 비금융위험에 대한 위험조정 변동분, 전기(누적) 열"
        cites = [fmt_cite(f, rec, "백만")] if rec else ["row missing"]
        ok = bool(rec and abs(abs(rec["value"]) - new) <= 1e-3)
    elif i == 6:
        e = f.note(("발행한 보험계약", "보험수익"), ["(1)발생한보험서비스비용", "(1)발생한보험서비스수익"])
        a1 = f.note(("발행한 보험계약", "보험서비스비용"), ["(1)실제보험금"])
        a2 = f.note(("발행한 보험계약", "보험서비스비용"), ["(2)실제계약유지비용"])
        a3 = f.note(("발행한 보험계약", "보험서비스비용"), ["(3)실제투자관리비"])
        kind, desc = "T2 note", "예실차 = |(1) 발생한 보험서비스비용(수익)| − (실제보험금 + 실제계약유지비용 + 실제투자관리비), 전기(누적) 열"
        recs = [e, a1, a2, a3]
        cites = [fmt_cite(f, r, "백만") for r in recs if r]
        ok = all(recs) and abs(abs(e["value"]) - abs(a1["value"] + a2["value"] + a3["value"]) - new) <= 1e-3
    elif i == 7:
        kind, desc = "DERIVED (3-4-5-6)", "기타 생명장기 원수손익 = 원수손익 − (CSM상각 + 위험조정 변동 + 예실차)"
        v = vec_new[q]
        cites = [f"= item3 {v[3]:,.6f} − item4 {v[4]:,.0f} − item5 {v[5]:,.0f} − item6 {v[6]:,.0f}"]
        ok = abs(v[3] - (v[4] + v[5] + v[6]) - new) <= 1e-3
    elif i == 9:
        rec = f.note(("재보험계약", "재보험비용"), ["보험계약마진상각"])
        kind, desc = "T2 note", "재보험비용 주석 '보험계약마진상각' 전기(누적) 열 (부호 −|x|)"
        cites = [fmt_cite(f, rec, "백만")] if rec else ["row missing"]
        ok = bool(rec and abs(-abs(rec["value"]) - new) <= 1e-3)
    elif i == 10:
        rec = f.note(("재보험계약", "재보험비용"), ["위험조정변동", "비금융위험에대한위험조정"])
        kind, desc = "T2 note", "재보험비용 주석 '위험조정변동' 전기(누적) 열 (부호 −|x|)"
        cites = [fmt_cite(f, rec, "백만")] if rec else ["row missing"]
        ok = bool(rec and abs(-abs(rec["value"]) - new) <= 1e-3)
    elif i == 11:
        a = f.note(("재보험계약", "재보험수익"), ["발생재보험금"])
        b = f.note(("재보험계약", "재보험비용"), ["예상재보험금"])
        kind, desc = "T2 note", "재보험 예실차 = |발생재보험금| − |예상재보험금| 전기(누적) 열"
        cites = [fmt_cite(f, r, "백만") for r in (a, b) if r]
        ok = bool(a and b and abs(abs(a["value"]) - abs(b["value"]) - new) <= 1e-3)
    elif i == 12:
        kind, desc = "DERIVED (8-9-10-11)", "기타 생명장기 재보험손익 = 재보험손익 − (9 + 10 + 11)"
        v = vec_new[q]
        cites = [f"= item8 {v[8]:,.6f} − item9 {v[9]:,.0f} − item10 {v[10]:,.0f} − item11 {v[11]:,.0f}"]
        ok = abs(v[8] - (v[9] + v[10] + v[11]) - new) <= 1e-3
    elif i == 32:
        kind, desc = "T1 derived (residual of CIS leaf rows)", "기타포괄손익 − (26+27+28+29+30)"
        v = vec_new[q]
        cites = [f"= item25 {v[25]:,.6f} − Σ(26..30) {sum(v[k] for k in (26, 27, 28, 29, 30)):,.6f}"]
        ok = abs(v[25] - sum(v[k] for k in (26, 27, 28, 29, 30)) - new) <= 1e-2
    else:
        kind, desc, cites, ok = "UNMAPPED", "", [], False
    if not ok:
        bad.append((q, i, new, cites))
    out_rows.append({"quarter": q, "item": i, "name": c["name"], "class": c["cls"], "old": c["old"], "new": new,
                     "delta": None if c["old"] is None else round(new - c["old"], 6), "flags": ";".join(c["flags"]),
                     "later_filing": short(f.path), "source_kind": kind, "source": desc, "raw_cite": " || ".join(cites), "verified": ok})

with open(HERE / "pl_cell_changes.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    w.writerows(out_rows)
print(f"cells: {len(out_rows)}; verified against raw: {sum(1 for r in out_rows if r['verified'])}; NOT verified: {len(bad)}")
for b in bad:
    print("  NOT VERIFIED:", b)
