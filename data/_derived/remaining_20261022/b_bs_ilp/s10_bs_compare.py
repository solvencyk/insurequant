"""Read-only: IFRS17_BS.json KR0073 (19 items x 14 quarters) vs every printed column of the separate 재무상태표 of every filing.
Output: s10_bs_compare.txt (human), s10_bs_compare.json (machine).  Units: master 백만원, filing 원."""
import sys, re, json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/b_bs_ilp"
sys.path.insert(0, str(D))
from s4_bs_rows import filings, bs_rows
sys.stdout.reconfigure(encoding="utf-8")

def norm(s):
    s = re.sub(r"\(주[^)]*\)", "", s)
    s = re.sub(r"^\s*(\d+\s*\.\s*|\(\d+\)\s*)", "", s)
    return s.replace(" ", "")
def num(t):
    t = t.replace(",", "").strip()
    if t == "-": return 0.0
    if t == "": return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v

LAB = {1: ["자산총계"], 2: ["부채총계"], 3: ["자본총계"], 4: ["기타포괄손익누계액", "기타포괄손익누적액"],
       10: ["현금및예치금"], 11: ["당기손익-공정가치측정금융자산", "당기손익공정가치측정금융자산"],
       12: ["기타포괄손익-공정가치측정금융자산", "기타포괄손익공정가치측정금융자산"],
       14: ["재보험계약자산"], 15: ["유형자산"], 20: ["보험계약부채"], 21: ["재보험계약부채"], 22: ["투자계약부채"], 23: ["차입부채"], 24: ["기타부채"],
       30: ["자본금"], 31: ["이익잉여금", "이익잉여금(결손금)"]}
AC = ["상각후원가측정유가증권", "상각후원가측정대출채권", "상각후원가측정기타금융자산", "기타수취채권"]
AC_TOTAL = ["상각후원가측정금융자산"]

NOTE_COL = False
def parse_bs(path):
    rows = bs_rows(path)
    first_total = None
    vals = {}   # item -> [col values won]
    for tr, cells, lns in rows:
        lab = norm(cells[0])
        nums = [num(c) for c in (cells[2:] if NOTE_COL else cells[1:])]
        # note column in 2023 Q1/Q2 filings ("5,16,17..." parses None) -> drop leading non-numeric
        nn = [n for n in nums if n is not None]
        if len(nn) < 1: continue
        # BS stops at first 부채와자본총계
        for it, labs in LAB.items():
            if lab in labs and it not in vals:
                vals[it] = (nn, lns[0])
        for a in AC:
            if lab == a: vals.setdefault("AC:" + a, (nn, lns[0]))
        if lab in AC_TOTAL: vals.setdefault("ACT", (nn, lns[0]))
        if lab.replace(" ", "") in ("부채와자본총계", "자본과부채총계"): break
    # item 13
    ac = [vals[k] for k in vals if isinstance(k, str) and k.startswith("AC:")]
    if "ACT" in vals: vals[13] = vals.pop("ACT")
    elif len(ac) >= 3:
        n = min(len(x[0]) for x in ac)
        vals[13] = ([sum(x[0][i] for x in ac) for i in range(n)], ";".join(f"L{x[1]}" for x in ac))
    for k in [k for k in vals if isinstance(k, str)]: vals.pop(k)
    return vals

FY_Q = lambda name: (int(name[2:6]), int(name[-1]))
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
M = {}
for r in bs:
    if r["원보험사코드"] == "KR0073":
        M[(r["공시분기"], r["항목번호"])] = r["값"]
QS = sorted({q for q, _ in M}, key=lambda q: (int(q[:4]), int(q[5])))
ITEMS = [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31]
files = filings()
V = {}  # (filing, col) -> (quarter label, {item: (value_mn, line)})
for fy, path in files.items():
    y, n = FY_Q(fy)
    NOTE_COL = fy in ("FY2023_Q1", "FY2023_Q2")
    try: vals = parse_bs(path)
    except KeyError:
        print("no sep_fs section:", fy); continue
    cols = [f"{y}.{n}Q", f"{y-1}.4Q", f"{y-2}.4Q"] if n == 4 else [f"{y}.{n}Q", f"{y-1}.4Q"]
    for ci, ql in enumerate(cols):
        d = {}
        for it in ITEMS:
            if it in vals and len(vals[it][0]) > ci:
                d[it] = (vals[it][0][ci] / 1e6, vals[it][1])
        if d: V[(fy, ci)] = (ql, d)
# FS-API fallback for FY2026_Q2 (no section titles in the xml)
import glob
for fs, fy, cols in [("2026_11012", "FY2026_Q2", ["2026.2Q", "2025.4Q"])]:
    d = json.load(open(ROOT / f"data/dart/_fs_api_cache/00112882_{fs}_OFS.json", encoding="utf-8"))
    ids = {"자산총계": 1, "부채총계": 2, "자본총계": 3, "기타포괄손익누계액": 4, "보험계약부채": 20, "재보험계약부채": 21, "투자계약부채": 22, "차입부채": 23, "이익잉여금": 31}
    for ci, ql in enumerate(cols):
        dd = {}
        for r in d.get("list", []):
            if r.get("sj_div") == "BS":
                nm = r["account_nm"].replace(" ", "")
                if nm in ids and ids[nm] not in dd:
                    v = r.get("thstrm_amount" if ci == 0 else "frmtrm_amount")
                    if v not in (None, ""): dd[ids[nm]] = (float(v) / 1e6, "FS-API " + fs)
        V[(fy, ci)] = (ql, dd)

out = {"master": {f"{q}|{i}": M.get((q, i)) for q in QS for i in ITEMS if (q, i) in M}, "cols": {}}
lines = []
for q in QS:
    lines.append(f"=== {q}")
    cand = sorted([(k, v) for k, v in V.items() if v[0] == q], key=lambda kv: (FY_Q(kv[0][0]), kv[0][1]))
    for (fy, ci), (ql, d) in cand:
        out["cols"][f"{q}|{fy}|col{ci}"] = {str(i): d[i][0] for i in d}
    hdr = "item   master          " + "  ".join(f"{fy}/c{ci}".ljust(18) for (fy, ci), _ in cand)
    lines.append(hdr)
    for it in ITEMS:
        m = M.get((q, it))
        cells = []
        for (fy, ci), (ql, d) in cand:
            v = d.get(it, (None,))[0]
            if v is None: cells.append("-".ljust(18)); continue
            flag = "" if m is None else ("=" if abs(v - m) <= 0.51 else f"{v - m:+,.1f}")
            cells.append((f"{v:,.1f}" + (" " + flag if flag and flag != "=" else "" if not flag else " =")).ljust(18))
        lines.append(f"{it:<4}  " + (f"{m:,.1f}" if m is not None else "None").ljust(16) + "  ".join(cells))
(D / "s10_bs_compare.txt").write_text("\n".join(lines), encoding="utf-8")
(D / "s10_bs_compare.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n".join(lines))
