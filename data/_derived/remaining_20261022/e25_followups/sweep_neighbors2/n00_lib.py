# -*- coding: utf-8 -*-
"""Part 2, note items 4/5/6/9/10/11 for every uncovered (company, quarter) with a later filing.  Read-only.
Generic label-driven reader on the SEPARATE-basis notes of the later filing with CURRENT-column calibration against the master at quarter+4:
  1. collect every note table row matching a term (csm/ra in revenue region, exp/act, csm/ra in reinsurance-cost region, recv/rexp) with ALL numeric cells and their physical lines;
  2. calibration: find (block, column j) whose current-period value reproduces the master at quarter+4 (|diff|<=1 mn);
  3. prior value = twin table (same row signature, next in document order) at the same column j, or the positional prior half of the same row;
Only calibrated reads count as 'compared'."""
import json, sys, re, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e23_read as E
import s2lib
import e21_t2 as T
import e21_raw as W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S2 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2/"
UD = {"원": 1e6, "천원": 1e3, "백만원": 1.0}
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
unc = sorted({tuple(x) for x in json.load(open(S2 + "uncovered.json", encoding="utf-8"))})
ITEMS = {"4", "5", "6", "9", "10", "11"}
ONLY = set(sys.argv[1:])  # optional company filter
targets = collections.defaultdict(set)
for c, q, i in unc:
    if i in ITEMS and q != "2025.3Q" and (not ONLY or c in ONLY):
        targets[(c, q)].add(i)

PFX = [("출재보험서비스수익", "rerev"), ("출재보험수익", "rerev"), ("재보험영업수익", "rerev"), ("재보험수익", "rerev"),
       ("출재보험서비스비용", "recost"), ("출재보험비용", "recost"), ("재보험영업비용", "recost"), ("재보험서비스비용", "recost"), ("재보험비용", "recost"),
       ("보험서비스비용", "cost"), ("보험영업비용", "cost"), ("보험비용", "cost"), ("일반보험서비스비용", "cost"),
       ("일반보험서비스수익", "rev"), ("보험영업수익", "rev"), ("보험수익", "rev"), ("보험서비스수익", "rev")]
CSM = re.compile(r"보험계약마진")
CSM_OK = re.compile(r"상각|제공|이전|인식|당기손익")
CSM_BAD = re.compile(r"추정|조정하는|처음|최초|신계약|이자|금융|손실|환율|기초|기말|잔액")
RA = re.compile(r"위험(조정|해제)")
RA_OK = re.compile(r"변동|해제|상각|감소|환입")
RA_BAD = re.compile(r"처음|최초|신계약|손실|추정|기초|기말|잔액|보험금융|재보험금융")
EXP = re.compile(r"예상.*(보험금|발생)|예정.*보험금")
EXP_BAD = re.compile(r"기타|유지비|투자관리비|손해조사비|사업비|재보험|회수|이행|위험|마진")
ACT = re.compile(r"(실제|발생).*(보험금)")
ACT_BAD = re.compile(r"사고|이행현금|재보험|회수|예상|위험|마진|취득")
RECV = re.compile(r"(발생|회수가능|실제).*(재보험금|보험금)")
RECV_BAD = re.compile(r"사고|이행현금|예상|위험|마진|손실|취득")
REXP = re.compile(r"회수예상|회수.*예상")


def isnum(c):
    t = c["text"].strip()
    return c["val"] is not None or t in ("-", "−")


def split_row(r):
    cells = r["cells"]
    k = 0
    labs = []
    while k < len(cells):
        c = cells[k]
        t = c["text"].strip()
        if isnum(c) and not re.match(r"^\(?\d{1,2}\)$", t) and not (k == 0 and re.match(r"^\(\d{1,2}\)$", t)):
            break
        if t:
            labs.append(c["text"])
        k += 1
    nums = []
    rest = cells[k:]
    while rest and not isnum(rest[-1]):
        rest = rest[:-1]
    for c in rest:
        if isnum(c):
            nums.append((0.0 if c["val"] is None else c["val"], c["line"], c["text"]))
        elif c["text"].strip() == "":
            nums.append((0.0, c["line"], ""))      # empty printed cell inside the numeric block keeps the column index aligned
    return E.nl("".join(labs)), nums


def classify(region, lab):
    if region == "rev":
        if CSM.search(lab) and CSM_OK.search(lab) and not CSM_BAD.search(lab): return "csm_rev"
        if RA.search(lab) and RA_OK.search(lab) and not RA_BAD.search(lab): return "ra_rev"
        if EXP.search(lab) and not EXP_BAD.search(lab): return "exp_rev"
    if region == "cost":
        if ACT.search(lab) and not ACT_BAD.search(lab): return "act_cost"
    if region == "recost":
        if CSM.search(lab) and CSM_OK.search(lab) and not CSM_BAD.search(lab): return "csm_re"
        if RA.search(lab) and RA_OK.search(lab) and not RA_BAD.search(lab): return "ra_re"
        if REXP.search(lab): return "rexp_recost"
    if region == "rerev":
        if RECV.search(lab) and not RECV_BAD.search(lab): return "recv_rerev"
    return None


def blocks_of(path):
    lines, s0, tabs = s2lib.tables_sep2(path)
    out = []
    for t, rows in tabs:
        hdr = E.nl(" ".join(c["text"] for r in rows[:6] for c in r["cells"]))
        capt = E.nl(t["caption"] or "")
        region = None
        terms = {}
        for r in rows:
            lab, nums = split_row(r)
            if not lab:
                continue
            if not nums:
                labp0 = re.sub(r"^((\(\d+\))|(\d+[\.\)])|([가-하]\.))+", "", lab)
                for p, reg in PFX:
                    if labp0 == p:
                        region = reg
                continue
            reg = None
            labp = re.sub(r"^((\(\d+\))|(\d+[\.\)])|([가-하]\.))+", "", lab)
            for p, rg in PFX:
                if labp.startswith(p):
                    reg = rg
                    region = rg          # a labelled section row (even with totals) opens its section
                    break
            reg = reg or region
            term = classify(reg, lab) if reg else None
            if term and term not in terms:
                terms[term] = dict(label=lab, nums=nums, tr=r["tr_line"], n=len(nums))
        if terms:
            try:
                unit = T.find_unit(lines, t, span=2500)
            except Exception:
                unit = "?"
            out.append(dict(start=t["start"], end=t["end"], hdr=hdr[:200], cap=capt[:80], terms=terms, unit=unit))
    return lines, out


def termset(i):
    return {"4": ["csm_rev"], "5": ["ra_rev"], "9": ["csm_re"], "10": ["ra_re"], "6": ["exp_rev", "act_cost"], "11": ["recv_rerev", "rexp_recost"]}[i]


def item_value(b, i, j):
    T_ = b["terms"]
    u = UD.get(b["unit"], float("nan"))

    def g(term):
        t = T_.get(term)
        if not t or j >= t["n"]:
            return None
        return t["nums"][j][0] / u, t["nums"][j][1:], t["tr"]
    ts = termset(i)
    xs = [g(t) for t in ts]
    if any(x is None for x in xs):
        return None
    if len(ts) == 1:
        sg = 1 if i in ("4", "5") else -1
        return dict(val=sg * abs(xs[0][0]), raw=[xs[0][0]], cells=[xs[0][1]], tr=[xs[0][2]])
    return dict(val=abs(xs[0][0]) - abs(xs[1][0]), raw=[xs[0][0], xs[1][0]], cells=[xs[0][1], xs[1][1]], tr=[xs[0][2], xs[1][2]])


def sig(b):
    return tuple(sorted((k, v["label"][:25]) for k, v in b["terms"].items()))


