"""k6: KR0104 2023.1Q / 2023.2Q candidate PL vector from the LATER filing's prior YTD column (separate basis), with filing line numbers,
independent of the FS-API cache; cross-checked against the d_census FS-API 'prior' values and the live-master snapshot.  READ-ONLY.
Writes k6_kr0104_cells.json (candidate cell list) + k6_kr0104_cells.txt."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
import stmtlib as S

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0104"
pl, names, inames = M.load_pl()
d5 = {(r["code"], r["q"]): r for r in M.jload(M.D_CENSUS / "d5_buckets.json")}

LABELS = {  # item -> label (normalised) in the LATER filing statement
    1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익", 21: "영업외손익", 22: "법인세차감전순이익", 23: "법인세비용",
    25: "기타포괄손익", 26: "기타포괄손익-공정가치측정금융자산관련손익", 27: "보험계약자산(부채)순금융손익",
    28: "현금흐름위험회피파생상품평가손익", 29: "기타포괄손익-공정가치측정금융자산평가손익", 30: "재보험계약자산(부채)순금융손익", 31: "총포괄손익",
}
NET = ("분기순이익", "반기순이익")
LEAVES32 = ("확정급여제도의재측정요소", "기타포괄손익-공정가치측정신용손실", "관계기업기타포괄손익지분")
cells = []
txt = []
for q in ("2023.1Q", "2023.2Q"):
    fy = M.later_fy(q)
    path = M.main_xmls(CODE, fy)[0]
    lines = M.read_lines(path)
    t = S.statement_tables(lines)[0]
    rows = S.read_statement(lines, t)
    by = {}
    for r in rows:
        by.setdefault(r["nlabel"], []).append(r)
    def get(label):
        key = M.norm_label(label)
        rs = by.get(key) or next((v for k, v in by.items() if k.startswith(key)), [])
        if not rs:
            return None
        r = rs[0]
        pv = S.prior_ytd(r)
        return None if pv is None else (pv[0] / 1e6, pv[1], pv[2], r["tr_line"])
    vec, src = {}, {}
    for it, lab in LABELS.items():
        g = get(lab)
        if g:
            vec[it], src[it] = g[0], (g[1], g[2], lab)
    for lab in NET:
        g = get(lab)
        if g:
            vec[24], src[24] = g[0], (g[1], g[2], lab)
    # item 16 is a cost -> positive magnitude (assemble() abs())
    vec[16] = abs(vec[16])
    # 보험금융손익 (19) = -(보험금융비용 + 재보험금융비용)  (KR0104 statement has no 보험금융수익 rows)
    gi, gr = get("보험금융비용"), get("재보험금융비용")
    vec[19] = -(gi[0] + gr[0])
    src[19] = (gi[1], gi[2] + " + " + gr[2] + f"@{gr[1]}", "보험금융비용 + 재보험금융비용")
    vec[18] = vec[17] - vec[19]
    src[18] = ("derived", "17 - 19", "")
    # 32 = leaves not classified in 26..30
    v32, l32 = 0.0, []
    for lab in LEAVES32:
        g = get(lab)
        if g:
            v32 += g[0]
            l32.append(f"{lab}@{g[1]}")
    vec[32], src[32] = v32, ("derived", "+".join(l32), "")
    # life LOB legs from the statement insurance lines
    rev, ssc, rrev, rexp = get("보험수익"), get("발행한 보험계약에서 생기는 보험서비스비용"), get("재보험수익"), get("재보험비용")
    vec[3] = rev[0] - ssc[0]
    src[3] = ("derived", f"보험수익@{rev[1]} - 발행보험서비스비용@{ssc[1]}", "")
    vec[8] = rrev[0] - rexp[0]
    src[8] = ("derived", f"재보험수익@{rrev[1]} - 재보험비용@{rexp[1]}", "")
    vec[2] = vec[3] + vec[8]
    src[2] = ("derived", "3 + 8", "")
    vec[15] = 0.0
    src[15] = ("builder rule", "no 기타영업수익 in the operating block -> 0.0", "")
    m = pl[(CODE, q)]
    # plugs from the master's note-derived 4,5,6,9,10,11
    if all(m.get(k) is not None for k in (4, 5, 6)):
        vec[7] = vec[3] - (m[4] + m[5] + m[6])
        src[7] = ("derived", "3 - (4+5+6)  [4,5,6 = live master note values]", "")
    if all(m.get(k) is not None for k in (9, 10, 11)):
        vec[12] = vec[8] - (m[9] + m[10] + m[11])
        src[12] = ("derived", "8 - (9+10+11)  [9,10,11 = live master note values]", "")
    # cross-checks
    b = d5[(CODE, q)]
    xchk = {}
    for it, d in b["its"].items():
        it = int(it)
        if it in vec and d.get("prior") is not None:
            xchk[it] = round(vec[it] - d["prior"], 6)
    # identities (strict, 원-level)
    idn = {
        "1 = 2 + 15 - 16": vec[2] + vec[15] - vec[16] - vec[1],
        "20 = 1 + 17": vec[1] + vec[17] - vec[20],
        "22 = 20 + 21": vec[20] + vec[21] - vec[22],
        "24 = 22 - 23": vec[22] - vec[23] - vec[24],
        "31 = 24 + 25": vec[24] + vec[25] - vec[31],
        "25 = 26+27+28+29+30+32": vec[26] + vec[27] + vec[28] + vec[29] + vec[30] + vec[32] - vec[25],
        "17 = 18 + 19": vec[18] + vec[19] - vec[17],
    }
    txt.append(f"=== {q}  later filing {M.rel(path)}  statement table L{t['start']}-L{t['end']}")
    txt.append("  xcheck vs FS-API prior (d5): max |diff| = %.6f over %d items; diffs>1e-6: %s" % (
        max((abs(x) for x in xchk.values()), default=0), len(xchk), {k: v for k, v in xchk.items() if abs(v) > 1e-6}))
    for k, v in idn.items():
        txt.append(f"  identity {k}: residual {v:+.6f} mn")
    for it in sorted(vec):
        old = m.get(it)
        new = round(vec[it], 6)
        chg = "" if (old is not None and abs(old - new) < 1e-9) else "CHANGE"
        s = src[it]
        txt.append(f"  item {it:>2} {inames.get(it, ''):<22} old={old!s:>16} new={new:>18,.6f}  {chg:<6} src: {s[2]} {s[1]} @L{s[0]}")
        if chg:
            cells.append({"code": CODE, "q": q, "item": it, "old": old, "new": new, "src_line": s[0], "src_text": s[1], "src_label": s[2]})
M.MEASURE.joinpath("k6_kr0104_cells.json").write_text(json.dumps(cells, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("k6_kr0104_cells.txt").write_text("\n".join(txt), encoding="utf-8")
print("cells", len(cells))
