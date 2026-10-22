# -*- coding: utf-8 -*-
"""e20 plan builder (parser/ifrs17, ticket 20261022T1800Z STEP 1): latest-comparative adoption plan for the buckets that close -- READ-ONLY on every master / gold / doc.
Per bucket: independent XML read (own reader e20_read.py / e20_oldlayout.py) of the SEPARATE-basis '4-2. 포괄손익계산서' of the ORIGINAL filing (current cumulative column) and of the
LATER filing (prior-period cumulative column + prior 3-month column), comparison with the live PL_breakdown.json master, identity closure on the merged vector, owner-gold classification
(gold == original print -> replace; gold == neither -> hold), single-quarter (값_당분기) analysis with the printed 3-month columns, citations (file / physical line / printed text / sign),
and the apply contract (gold set / replace, null_dangi, set_dangi, redundant pins to drop).
Writes e20_plan.json + e20_plan_report.txt next to this script.   python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_oldlayout as OL  # noqa: E402
import e20_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
X = R.X
ROOT = X.ROOT
EVID = "data/_derived/remaining_20261022/e20_held_and_remaining/apply/e20_plan.json"
CHECK_ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익",
             25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
             30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
# (code, quarter, original FY dir, later FY dir, group)   A = old-layout original + owner gold overlap, B = old master lineage (경영공시 rounded), C = standard, D = standard + owner gold overlap
BUCKETS = [
    ("KR0082", "2023.1Q", "FY2023_Q1", "FY2024_Q1", "A"), ("KR0082", "2023.2Q", "FY2023_Q2", "FY2024_Q2", "A"),
    ("KR0083", "2024.3Q", "FY2024_Q3", "FY2025_Q3", "D"),
    ("KR0087", "2024.4Q", "FY2024_Q4", "FY2025_Q4", "C"), ("KR0087", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0087", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0032", "2023.1Q", "FY2023_Q1", "FY2024_Q1", "B"),
    ("KR0104", "2024.4Q", "FY2024_Q4", "FY2025_Q4", "C"), ("KR0104", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0104", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0069", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0069", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0094", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0070", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0070", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0072", "2024.4Q", "FY2024_Q4", "FY2025_Q4", "C"),
    ("KR0068", "2024.4Q", "FY2024_Q4", "FY2025_Q4", "C"), ("KR0068", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0068", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
    ("KR0071", "2025.1Q", "FY2025_Q1", "FY2026_Q1", "C"), ("KR0071", "2025.2Q", "FY2025_Q2", "FY2026_Q2", "C"),
]
# items of a bucket that are NOT adopted although they differ, with the reason (identity of the master would break: presentation split, not a restatement)
EXCLUDE = {
    ("KR0072", "2024.4Q"): ({17, 18}, "후속 공시(FY2025 사업보고서)의 전기 열이 영업손익 안에 새 줄 「기타영업손익」 (58,543,150원)을 따로 인쇄해 투자손익이 같은 금액만큼 작아졌다. "
                                    "보험손익·영업이익·세전이익은 불변이라 마스터 항등식 영업이익 = 보험손익 + 투자손익 이 58.543 백만원 깨진다(마스터에는 기타영업손익 칸이 없다). "
                                    "재작성이 아니라 표시 분리이므로 17·18 은 적재하지 않는다."),
}
OLD_BAND = {("KR0032", "2023.1Q"): 1.5}     # master lineage = 경영공시 (0.01억 = 1 백만원 granularity, observed noise up to 1.1 백만원 versus the DART print)
FSS = "금융감독원 2025-12 질의회신(생명보험사 계약자지분조정 회계처리·일탈회계) 반영 회계정책 변경의 소급재작성"
# cause of the restated comparative per (code, later FY): (text, [physical lines of the later filing that state it])
CAUSE = {
    ("KR0087", "FY2025_Q4"): (FSS + " (제36기 소급수정)", [5641, 74054]),
    ("KR0087", "FY2026_Q1"): (FSS, [47518]), ("KR0087", "FY2026_Q2"): (FSS, [42325]),
    ("KR0104", "FY2025_Q4"): (FSS + " (제13기 포괄손익계산서 소급 재작성 주)", [4720]),
    ("KR0104", "FY2026_Q1"): (FSS, [3358, 5052]), ("KR0104", "FY2026_Q2"): (FSS, [4645, 6316]),
    ("KR0069", "FY2026_Q1"): (FSS + " (별도포괄손익계산서 소급 재작성 주)", [61947, 14733]), ("KR0069", "FY2026_Q2"): (FSS + " (별도포괄손익계산서 소급 재작성 주)", [55275]),
    ("KR0094", "FY2026_Q2"): (FSS + " (제37기말부터 유배당보험계약 계약자 배당 부채를 1117호로 측정)", [57106]),
    ("KR0070", "FY2026_Q1"): (FSS + " (제72기 재작성 주)", [3208]), ("KR0070", "FY2026_Q2"): (FSS + " (제72기 재작성 주)", [3551]),
    ("KR0072", "FY2025_Q4"): (FSS + " (제37기말 소급재작성 주)", [4743, 8231]),
    ("KR0068", "FY2025_Q4"): (FSS + " (제76기 소급 재작성 주)", [29486, 129999]), ("KR0068", "FY2026_Q1"): (FSS, [28490]), ("KR0068", "FY2026_Q2"): (FSS, [31462]),
    ("KR0083", "FY2025_Q3"): ("보험금융수익(비용)의 체계적 배분 회계정책 변경의 소급재작성(재무제표 주석 50, 소급전·소급후 표 L38277~L38401)", [38139]),
}

live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
MD = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in live}
NAME_OF = {r["원보험사코드"]: r["원수사명"] for r in live}
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
NULLD = {tuple(x) for x in gold.get("null_dangi", {}).get("cells", [])}
SETD = {(x[0], x[1], int(x[2])): x for x in gold.get("set_dangi", {}).get("cells", [])}
CONF = json.loads((ROOT / "data/_gold/user_pl_confirmed_cells.json").read_text(encoding="utf-8"))
d5 = {(b["code"], b["q"]): b for b in json.loads((ROOT / "data/_derived/remaining_20261022/d_census/d5_buckets.json").read_text(encoding="utf-8"))}
NOTE50 = json.loads((ROOT / "data/_derived/remaining_20261022/e19_latest_comparative/KR0083_note50.json").read_text(encoding="utf-8"))
NOTE50_MAP = {17: ("II. 투자손익", 1), 20: ("III. 영업이익(손실)", 1), 22: ("V. 법인세차감전순이익(손실)", 1), 23: ("VI. 법인세비용(수익)", 1), 24: ("VII. 분기순이익(손실)", 1),
              25: ("VIII. 기타포괄손익", 1), 27: ("보험계약자산(부채) 순금융손익", 1), 19: ("보험금융비용", -1)}

_ST = {}
_LINES = {}


def stmt(code, fy):
    if (code, fy) not in _ST:
        _ST[(code, fy)] = R.Stmt(code, fy)
    return _ST[(code, fy)]


def rcept_of(st):
    return st.path.stem


def prev_q(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


def later_fy_of(q):
    return f"FY{int(q[:4]) + 1}_Q{q[5]}"


def have_filing(code, fy):
    try:
        return len(X.candidates(code, fy)) > 0
    except Exception:  # noqa: BLE001
        return False


def parts_d(parts):
    return [p.d() if hasattr(p, "d") else p for p in parts]


def band_for(unit, parts):
    """tolerance between a printed value and the exact value / another print of the same line"""
    return 2e-5 if unit == "원" else 1.0 + 0.5 * (max(1, len(parts)) - 1) + 1e-3     # 백만원 print: +-1 footing plug on a line (observed up to 0.73) + 0.5 per further rounded line


def line_text(path, ln, n=170):
    if path not in _LINES:
        _LINES[path] = X.load_lines(path)
    t = re.sub(r"\s+", " ", X.RE_TAG.sub("", _LINES[path][ln - 1])).strip()
    return t[:n]


def merged_identities(v, exact):
    """residuals of the master identities on a (merged) vector; exact = no rounded cell involved"""
    res = []

    def chk(name, lhs, rhs, n_round):
        if lhs is None or rhs is None:
            res.append(dict(name=name, status="SKIP (operand empty)"))
            return
        d = lhs - rhs
        tol = 0.002 if exact else 0.5 * n_round + 0.002
        res.append(dict(name=name, lhs=round(lhs, 6), rhs=round(rhs, 6), resid=round(d, 6), tol=round(tol, 4), ok=abs(d) <= tol))

    g = lambda i: v.get(i)  # noqa: E731
    S = lambda *xs: None if any(x is None for x in xs) else sum(xs)  # noqa: E731
    chk("I1 20 = 1 + 17", g(20), S(g(1), g(17)), 3)
    chk("I2 |22-24| = |23|", None if g(22) is None or g(24) is None else abs(g(22) - g(24)), None if g(23) is None else abs(g(23)), 3)
    chk("I2b 22 = 20 + 21", g(22), S(g(20), g(21)), 3)
    chk("I3 31 = 24 + 25", g(31), S(g(24), g(25)), 3)
    oci = [i for i in (26, 27, 28, 29, 30, 32) if g(i) is not None]
    chk("I4 25 = sum of the OCI parts the master carries", g(25), S(*[g(i) for i in oci]) if oci else None, 1 + len(oci))
    chk("I5 17 = 18 + 19", g(17), S(g(18), g(19)), 3)
    return res


def read_orig(code, q, ofy, group):
    """original-vintage vector (백만원) with citation parts, or None"""
    if group in ("C", "D"):
        st = stmt(code, ofy)
        v = R.read_vector(st, "cur", "cum")
        return dict(st=st, vec={i: v[i]["val"] for i in CHECK_ITEMS}, parts={i: parts_d(v[i]["parts"]) for i in CHECK_ITEMS}, unit=st.unit, file=st.rel, rcept=rcept_of(st))
    if group == "A":
        p = X.main_xml(code, ofy)
        s4 = X.find_titles(X.load_lines(p), r"^<TITLE[^>]*>4\. 재무제표")
        caption = r"분 기 포 괄 손 익 계 산 서" if ofy.endswith("Q1") else r"반 기 포 괄 손 익 계 산 서"
        cap, rows = OL.read_table(p, caption, start_after=s4[0])
        g = 0 if ofy.endswith("Q1") else 1
        got = {}
        for r in rows:
            nl = OL.norm_label(r["label"])
            for key in ("I.보험서비스손익", "(3)기타사업비", "II.투자손익", "III.보험금융손익"):
                if nl == key:
                    v, ln, txt = OL.group_value(r["cells"], g)
                    got[key] = dict(val=v / 1e6, line=ln, printed=txt, label=r["label"].strip())
        o1, o16, o18, o19 = got["I.보험서비스손익"], got["(3)기타사업비"], got["II.투자손익"], got["III.보험금융손익"]
        vec = {1: o1["val"], 16: o16["val"], 17: o18["val"] + o19["val"], 18: o18["val"], 19: o19["val"]}
        parts = {1: [dict(label=o1["label"], line=o1["line"], printed=o1["printed"], sign=1)], 16: [dict(label=o16["label"], line=o16["line"], printed=o16["printed"], sign=1)],
                 17: [dict(label=o18["label"], line=o18["line"], printed=o18["printed"], sign=1), dict(label=o19["label"], line=o19["line"], printed=o19["printed"], sign=1)],
                 18: [dict(label=o18["label"], line=o18["line"], printed=o18["printed"], sign=1)], 19: [dict(label=o19["label"], line=o19["line"], printed=o19["printed"], sign=1)]}
        return dict(st=None, vec=vec, parts=parts, unit="원", file=X.rel(p), rcept=p.stem, layout="old (2023 plain table, caption L%d)" % cap)
    return None


def cause_for(code, lfy):
    c = CAUSE.get((code, lfy))
    if c is None:
        return None
    path = X.main_xml(code, lfy)
    return dict(text=c[0], lines=[dict(line=ln, text=line_text(path, ln)) for ln in c[1]])


def make_note(c, b, replaced=None):
    code, q, it = c["code"], c["quarter"], c["item"]
    unit_txt = c["source_unit"] + ("(백만원 반올림 인쇄)" if c["source_unit"] == "백만원" else "(정확 인쇄)")
    multi = len(c["xml_lines"]) > 1
    lines_txt = f"L{c['xml_lines'][0]['line']}" + (" 외 합산 줄(증거 파일 xml_lines)" if multi else "")
    per = {"1": "3월", "2": "6월", "3": "9월", "4": "12월"}[q[5]]
    o = c.get("original_print")
    if o:
        ol = o["lines"][0]["line"] if o.get("lines") else None
        mo = f"현재 마스터값 {c['old']} 는 원 공시 {b['orig_fy']} rcept {o['rcept']}(단위 {o['unit']}) 인쇄값({o['value']}, 원문 L{ol})과 일치."
    else:
        mo = f"현재 마스터값 {c['old']} 는 경영공시 계보의 억 단위 반올림 값이다(DART 원 공시 인쇄값과 1 백만원 안팎 차이)."
    cs = b.get("cause")
    cause = (f"사유: {cs['text']} — 필링 " + ", ".join(f"L{x['line']}" for x in cs["lines"]) + ".") if cs else "사유: 후속 공시 비교열이 재작성돼 인쇄됨(해당 필링에서 재작성 사유 주석은 찾지 못함)."
    pre = ""
    if replaced is not None:
        pre = (f"owner gold 를 최신 비교열로 갱신(owner 2026-10-22 「쭉 진행」): 이전 gold 값 {replaced['값']} = 원 공시 인쇄값(원 공시 판), 이전 was {replaced.get('was')}, 이전 note 요약 「{str(replaced.get('note'))[:140]}…」 (전문은 git HEAD 의 data/_gold/user_pl_cells.json). ")
    return (pre + f"2026-10-22 parser/ifrs17 (e20, ticket 20261022T1800Z STEP 1: 최신 비교열 채택, owner 결정 2026-10-22, 교보생명 선례와 동일): 별도(OFS) 기준 4-2 포괄손익계산서, "
            f"{b['later_fy']} rcept {c['xml_rcept']} 의 전기 {q[:4]}.{q[5]}Q 누적({per}) 열 = {c['new']} 백만원. 원문 {c['xml_file']} {lines_txt}. 단위 {unit_txt}. {mo} 변동 {c['delta']:+.6f}. {cause} "
            f"2차 근거 FS-API frmtrm(차이 {c['fsapi_diff']}). 증거 {EVID}")


def build_bucket(code, q, ofy, lfy, group):
    b = dict(code=code, quarter=q, group=group, orig_fy=ofy, later_fy=lfy)
    sl = stmt(code, lfy)
    vl = R.read_vector(sl, "prior", "cum")
    b["later"] = dict(file=sl.rel, rcept=rcept_of(sl), unit=sl.unit, fmt=sl.fmt, title_line=sl.title)
    orig = read_orig(code, q, ofy, group)
    b["orig"] = None if orig is None else dict(file=orig["file"], rcept=orig["rcept"], unit=orig["unit"], layout=orig.get("layout", "std"))
    b["cause"] = cause_for(code, lfy)
    cen = d5.get((code, q), {}).get("its", {})
    old_band = OLD_BAND.get((code, q), 2e-5)
    rows = []
    changed, rounding_only, equal = [], [], []
    for it in CHECK_ITEMS:
        m = M.get((code, it, q))
        l = vl[it]["val"]
        if m is None:
            rows.append(dict(item=it, master=None, later=l, status="master empty"))
            continue
        bd = max(old_band, band_for(sl.unit, vl[it]["parts"]))
        d = l - m
        st_ = "equal" if abs(d) <= 2e-5 else ("rounding_only" if abs(d) <= bd else "changed")
        (changed if st_ == "changed" else (rounding_only if st_ == "rounding_only" else equal)).append(it)
        o = None if orig is None else orig["vec"].get(it)
        rows.append(dict(item=it, master=m, later=round(l, 6), orig=(None if o is None else round(o, 6)), delta=round(d, 6), band=round(bd, 6), status=st_,
                         fsapi_prior=(cen.get(str(it), {}) or {}).get("prior"), master_eq_orig=(None if o is None else abs(m - o) <= (2e-5 if orig["unit"] == "원" else 0.5))))
    b["rows"] = rows
    b["changed_items"] = changed
    b["rounding_only_items"] = rounding_only
    b["census_real"] = d5.get((code, q), {}).get("real", [])
    ex_items, ex_reason = EXCLUDE.get((code, q), (set(), None))
    b["excluded_items"] = sorted(set(changed) & ex_items)
    b["excluded_reason"] = ex_reason if b["excluded_items"] else None
    b["adopt_items"] = [i for i in changed if i not in ex_items]
    live_vec = {i: M.get((code, i, q)) for i in range(1, 33)}
    merged = dict(live_vec)
    for i in b["adopt_items"]:
        merged[i] = vl[i]["val"]
    exact_all = (sl.unit == "원") and old_band <= 2e-5
    b["closure_master_before"] = merged_identities(live_vec, old_band <= 2e-5)
    b["closure_later_vector_printed"] = merged_identities({i: vl[i]["val"] for i in CHECK_ITEMS}, sl.unit == "원")
    b["closure_merged_after"] = merged_identities(merged, exact_all)
    b["closure_full_later_if_excluded_adopted"] = merged_identities({**merged, **{i: vl[i]["val"] for i in b["excluded_items"]}}, exact_all) if b["excluded_items"] else None
    b["closes"] = all(x.get("ok", True) for x in b["closure_merged_after"])
    b["printed_oci_leaf_sum_check"] = dict(item25=round(vl[25]["val"], 6), leaf_sum=round(vl["_leaf_all_sum"], 6), resid=round(vl[25]["val"] - vl["_leaf_all_sum"], 6))
    gl = []
    for i in b["adopt_items"]:
        g = GOLD.get((code, i, q))
        if g is None:
            continue
        o = None if orig is None else orig["vec"].get(i)
        new = vl[i]["val"]
        if o is not None and abs(g["값"] - o) <= (2e-5 if orig["unit"] == "원" else 0.5):
            cls = "gold_equals_original_print"
        elif abs(g["값"] - new) <= band_for(sl.unit, vl[i]["parts"]):
            cls = "gold_equals_latest"
        else:
            cls = "gold_other"
        gl.append(dict(item=i, gold_value=g["값"], gold_was=g.get("was"), original_print=o, latest=round(new, 6), cls=cls))
    b["gold_overlap"] = gl
    b["gold_in_block"] = sorted(k[1] for k in GOLD if k[0] == code and k[2] == q)
    nm = NAME_OF.get(code)
    b["confirmed_registry_hits"] = [dict(c) for c in CONF["cells"] if c.get("master") == "PL_breakdown" and c.get("company") == nm and c.get("quarter") == q]
    b["csm_status"] = (d5.get((code, q), {}).get("csm") or {}).get("status")
    cells = []
    for i in b["adopt_items"]:
        old = M[(code, i, q)]
        new = vl[i]["val"]
        o = None if orig is None else orig["vec"].get(i)
        cn = cen.get(str(i), {}) or {}
        cell = dict(code=code, quarter=q, item=i, item_name=ITEM_NAME[i], old=old, new=round(new, 6), delta=round(new - old, 6), unit="백만원", source_unit=sl.unit,
                    source_print=("rounded to million won" if sl.unit == "백만원" else "won (exact)"), xml_file=sl.rel, xml_rcept=rcept_of(sl), xml_fmt=sl.fmt,
                    xml_lines=parts_d(vl[i]["parts"]), derivation=("direct print" if len(vl[i]["parts"]) == 1 else "derived from printed lines (production definition; sign per line)"),
                    fsapi_prior=cn.get("prior"), fsapi_diff=(None if cn.get("prior") is None else round(cn["prior"] - new, 6)),
                    original_print=(None if o is None else dict(value=round(o, 6), file=orig["file"], rcept=orig["rcept"], lines=orig["parts"][i], unit=orig["unit"])),
                    master_equals_original_print=(None if o is None else abs(old - o) <= (2e-5 if orig["unit"] == "원" else 0.5)),
                    gold_cell=((code, i, q) in GOLD), gold_class=next((x["cls"] for x in gl if x["item"] == i), None))
        if code == "KR0083" and i in NOTE50_MAP and "FY2025_Q3" in NOTE50:
            lab, sg = NOTE50_MAP[i]
            row = next((x for x in NOTE50["FY2025_Q3"] if x["label"] == lab), None)
            if row is not None:
                cell["second_source_note50"] = dict(label=lab, before=sg * row["before"], after=sg * row["after"], line_after=row["line_after"],
                                                    after_vs_new=round(sg * row["after"] - new, 3), before_vs_old=round(sg * row["before"] - old, 3))
        cells.append(cell)
    b["cells"] = cells
    return b


def seam_analysis(code, adopted):
    """single-quarter cells (값_당분기) touched by the adoption.  adopted = {(item, q): new cumulative}."""
    out = []
    items = sorted({i for (i, q) in adopted})
    years = sorted({q[:4] for (i, q) in adopted})
    for it in items:
        for y in years:
            qs = [f"{y}.{n}Q" for n in (1, 2, 3, 4)]
            cum_after = {q: (adopted[(it, q)] if (it, q) in adopted else M.get((code, it, q))) for q in qs}
            for q in qs:
                n = int(q[5])
                pq = prev_q(q)
                cur_ad = (it, q) in adopted
                prev_ad = pq is not None and (it, pq) in adopted
                if not (cur_ad or prev_ad):
                    continue
                live_d = MD.get((code, it, q))
                cur, prev = cum_after[q], (cum_after[pq] if pq else None)
                D = None if cur is None else (cur if n == 1 else (None if prev is None else round(cur - prev, 6)))
                rec = dict(code=code, quarter=q, item=it, item_name=ITEM_NAME[it], live_dangi=live_d, derived_after=D, cur_adopted_now=cur_ad, prev_adopted_now=prev_ad,
                           cur_cum_after=cur, prev_cum_after=prev, existing_null=(code, q, it) in NULLD, existing_set=(code, q, it) in SETD)
                if n == 1:
                    rec.update(cls="q1_equals_cumulative", proposal="none")
                    out.append(rec)
                    continue
                if D is None:
                    rec.update(cls="derived_none_before_and_after", proposal="none", reason="a cumulative operand is empty in the master (the builder derives no single quarter); nothing to pin")
                    out.append(rec)
                    continue
                lfy = later_fy_of(q)
                P = None
                if n in (2, 3) and have_filing(code, lfy):
                    sl = stmt(code, lfy)
                    try:
                        v3 = R.read_vector(sl, "prior", "3m")
                        P = dict(value=round(v3[it]["val"], 6), file=sl.rel, rcept=rcept_of(sl), unit=sl.unit, lines=parts_d(v3[it]["parts"]), nparts=len(v3[it]["parts"]))
                    except Exception as e:  # noqa: BLE001
                        P = dict(error=f"{type(e).__name__}: {e}")
                rec["printed_3m"] = P
                if live_d is None and not (cur_ad and prev_ad):
                    rec.update(cls="live_blank_kept", proposal="null_dangi", reason="the live single quarter is blank (hand-blanked, pre-existing) while the builder would now derive a value from a restated cumulative minus an unrestated one -> keep the blank")
                    out.append(rec)
                    continue
                if n == 4 or P is None or "value" not in P:
                    rec.update(cls="seam", proposal="null_dangi",
                               reason=("annual report: no 3-month column is printed, the FY cumulative comes from the annual filing and the 9M cumulative from another filing -> blank (owner rule 2026-10-22, Kyobo precedent)" if n == 4
                                       else "the later filing of this quarter is not filed yet (no printed 3-month column) while the previous cumulative is restated -> blank"))
                    out.append(rec)
                    continue
                tol = 3 * band_for(P["unit"], [0] * P["nparts"]) if P["unit"] != "원" else 3 * 2e-5
                if abs(D - P["value"]) <= tol:
                    rec.update(cls="consistent_both_latest", proposal="none", diff_vs_printed_3m=round(D - P["value"], 6), tol=round(tol, 6))
                    if rec["existing_set"]:
                        pinned = float(SETD[(code, q, it)][3])
                        rec["existing_set_value"] = pinned
                        rec["existing_set_redundant"] = abs(pinned - D) <= 1e-6
                else:
                    rec.update(cls="seam", proposal="set_dangi", diff_vs_printed_3m=round(D - P["value"], 6), tol=round(tol, 6),
                               reason="derived single quarter differs from the 3-month column printed in the later filing -> use the printed value")
                out.append(rec)
    return out


def main():
    if (HERE / "apply_manifest_e20.json").exists():
        raise SystemExit("e20_plan.py reads the PRE-apply masters; the apply has been done (apply_manifest_e20.json exists), a rerun would overwrite e20_plan.json with an empty plan. "
                         "Use e20_verify_plans.py / e20_apply.py --verify / e20_diff_vs_head.py to re-check, or e20_apply.py --revert --apply first.")
    plan = dict(generated="2026-10-22", ticket="inbox/parser/20261022T1800Z__orchestrator__MULTI_2023.1Q-2025.2Q__latest_comparative_held_and_remaining.md", step="STEP 1", buckets=[], seams=[])
    L = []
    by_code = defaultdict(list)
    for (code, q, ofy, lfy, group) in BUCKETS:
        try:
            b = build_bucket(code, q, ofy, lfy, group)
        except Exception as e:  # noqa: BLE001
            plan["buckets"].append(dict(code=code, quarter=q, group=group, error=f"{type(e).__name__}: {e}"))
            L.append(f"== {code} {q}: BUILD ERROR {type(e).__name__}: {e}")
            continue
        plan["buckets"].append(b)
        by_code[code].append(b)
        L.append(f"== {code} {q} group {group} later {b['later']['file']} unit {b['later']['unit']} fmt {b['later']['fmt']}  orig {None if b['orig'] is None else b['orig']['file']}")
        L.append(f"   changed {b['changed_items']}  rounding_only {b['rounding_only_items']}  census_real {b['census_real']}  excluded {b['excluded_items']}  adopt {b['adopt_items']}  closes {b['closes']}  csm {b['csm_status']}  gold_in_block {b['gold_in_block']}  confirmed_registry {b['confirmed_registry_hits']}")
        if b["cause"]:
            L.append("   cause: " + b["cause"]["text"] + " | " + " || ".join(f"L{x['line']}: {x['text'][:110]}" for x in b["cause"]["lines"]))
        if b["excluded_reason"]:
            L.append(f"   EXCLUDED: {b['excluded_reason']}")
        for k in ("closure_master_before", "closure_later_vector_printed", "closure_merged_after"):
            L.append(f"   {k}: " + "; ".join(f"{x['name'].split(' ')[0]}={'SKIP' if 'resid' not in x else format(x['resid'], '+.4f') + ('' if x['ok'] else ' FAIL')}" for x in b[k]))
        if b["closure_full_later_if_excluded_adopted"]:
            L.append("   closure if the excluded items were adopted too: " + "; ".join(f"{x['name'].split(' ')[0]}={'SKIP' if 'resid' not in x else format(x['resid'], '+.4f') + ('' if x['ok'] else ' FAIL')}" for x in b["closure_full_later_if_excluded_adopted"]))
        L.append(f"   OCI leaf-sum check: {b['printed_oci_leaf_sum_check']}")
        for g in b["gold_overlap"]:
            L.append(f"   GOLD overlap item {g['item']}: gold {g['gold_value']} (was {g['gold_was']}) original print {g['original_print']} latest {g['latest']} -> {g['cls']}")
        for c in b["cells"]:
            L.append(f"   CELL i{c['item']:>2} {c['item_name']}: old={c['old']} new={c['new']} delta={c['delta']} src={c['source_print']} fsapi_diff={c['fsapi_diff']} mastEqOrig={c['master_equals_original_print']} gold={c['gold_cell']}:{c['gold_class']} "
                     f"note50={c.get('second_source_note50')} lines={[(p['label'], p['line'], p['printed'], p['sign']) for p in c['xml_lines']]}")
    # ------------------------------------------------------------------ seams per company + apply contract
    contract = dict(gold_new=[], gold_replace=[], null_dangi_add=[], set_dangi_add=[], set_dangi_remove=[], held=[])
    for code, bl in by_code.items():
        adopted = {}
        for b in bl:
            for c in b["cells"]:
                adopted[(c["item"], c["quarter"])] = c["new"]
        ss = seam_analysis(code, adopted)
        plan["seams"] += ss
        L.append(f"== SEAMS {code}: {len(ss)} touched single-quarter cells")
        for s in ss:
            L.append(f"   {s['quarter']} i{s['item']:>2} live={s['live_dangi']} derived_after={s['derived_after']} cls={s['cls']} proposal={s['proposal']} diff_vs_3m={s.get('diff_vs_printed_3m')} 3m={None if not s.get('printed_3m') else s['printed_3m'].get('value')} "
                     f"existing_null={s['existing_null']} existing_set={s['existing_set']} redundant={s.get('existing_set_redundant')}")
            k = (code, s["quarter"], s["item"])
            if s["proposal"] == "null_dangi":
                if k in NULLD:
                    continue
                contract["null_dangi_add"].append([code, s["quarter"], s["item"]])
            elif s["proposal"] == "set_dangi":
                p3 = s["printed_3m"]
                src = f"{p3['file']}:" + " || ".join(f"L{p['line']} [{p['label']}] {p['printed']}" for p in p3["lines"]) + f" (prior-year 3-month column printed in the {later_fy_of(s['quarter'])} report; derived single quarter from the two cumulatives differs by {s['diff_vs_printed_3m']:+.6f})"
                contract["set_dangi_add"].append([code, s["quarter"], s["item"], p3["value"], src])
            if s["existing_set"] and s.get("existing_set_redundant"):
                contract["set_dangi_remove"].append([code, s["quarter"], s["item"]])
    for b in plan["buckets"]:
        if "error" in b:
            contract["held"].append(dict(code=b["code"], quarter=b["quarter"], reason=b["error"]))
            continue
        if not b["closes"] or any(g["cls"] == "gold_other" for g in b["gold_overlap"]):
            contract["held"].append(dict(code=b["code"], quarter=b["quarter"], reason="closure fails or gold value is neither the original print nor the latest comparative"))
            continue
        gold_here = {g["item"]: g for g in b["gold_overlap"]}
        for c in b["cells"]:
            key = (c["code"], c["item"], c["quarter"])
            if key in GOLD:
                old_e = GOLD[key]
                note = make_note(c, b, replaced=old_e)
                contract["gold_replace"].append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=old_e["값"], note=note, old_entry=dict(old_e)))
            else:
                contract["gold_new"].append(dict(code=c["code"], item=c["item"], quarter=c["quarter"], value=c["new"], was=c["old"], note=make_note(c, b)))
    plan["apply_contract"] = contract
    plan["n_cells"] = sum(len(b.get("cells", [])) for b in plan["buckets"])
    L.append(f"== APPLY CONTRACT: gold_new {len(contract['gold_new'])}, gold_replace {len(contract['gold_replace'])}, null_dangi_add {len(contract['null_dangi_add'])}, set_dangi_add {len(contract['set_dangi_add'])}, "
             f"set_dangi_remove {len(contract['set_dangi_remove'])}, held {contract['held']}")
    (HERE / "e20_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (HERE / "e20_plan_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("buckets", len(plan["buckets"]), "cells", plan["n_cells"], "seams", len(plan["seams"]), "contract", {k: len(v) for k, v in contract.items()})


if __name__ == "__main__":
    main()
