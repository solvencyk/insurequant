# -*- coding: utf-8 -*-
"""Independent re-read of KB라이프 KR0099 2023.1Q-3Q from the NEXT-YEAR filing prior (comparative) columns, separate (OFS) statements. stdlib only; own parser (vlib)."""
import sys, json, subprocess
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife")
from vlib import *
sys.stdout.reconfigure(encoding="utf-8")
OUT = R + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0099_kblife/"
SRC = {"2023.1Q": "2024.1Q", "2023.2Q": "2024.2Q", "2023.3Q": "2024.3Q"}


def head(rel):
    return json.loads(subprocess.run(["git", "-C", R, "show", "HEAD:" + rel], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))


def live(rel):
    return json.load(open(R + "/" + rel, encoding="utf-8"))


def cellmap(rows):
    return {(r["항목번호"], r["공시분기"]): (r["값"], r["값_당분기"]) for r in rows if r["원보험사코드"] == "KR0099"}


PLH, PLL = cellmap(head("PL_breakdown.json")), cellmap(live("PL_breakdown.json"))
CSH, CSL = cellmap(head("CSM_waterfall.json")), cellmap(live("CSM_waterfall.json"))
out = []


def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def N(s):
    v = num(s)
    assert v != "NaN", s
    return 0.0 if v is None else v


def find_is(tb):
    c = [(i, t) for i, t in enumerate(tb) if "4-2. 포괄손익계산서" in t["pre"][-260:] and len(t["rows"]) > 30]
    assert len(c) == 1, len(c)
    return c[0]


def parse_is(t):
    d = {}
    for r in t["rows"][2:]:
        cells = [c for c, _ in r]
        assert len(cells) == 5, cells
        lab = cells[0]
        occ = sum(1 for k in d if k[0] == lab)
        d[(lab, occ)] = (num(cells[1]), num(cells[2]), num(cells[3]), num(cells[4]))  # cur3m, curcum, pri3m, pricum
    return d


def after(tb, pos):
    return [(i, t) for i, t in enumerate(tb) if t["pos"] > pos]


def add(a, b):
    return (a[0] + b[0], (a[1] + b[1]) if a[1] is not None and b[1] is not None else None)


def sub(a, b):
    return (a[0] - b[0], (a[1] - b[1]) if a[1] is not None and b[1] is not None else None)


EXP = {}
CEXP = {}
for q, sq in SRC.items():
    txt = load(XML[sq])
    tb = tables(txt)
    ii, ist = find_is(tb)
    d = parse_is(ist)
    P("==", q, "from", sq, "IS table", ii, "line", ist["line"], "rows", len(ist["rows"]), "header:", [c for c, _ in ist["rows"][0]], [c for c, _ in ist["rows"][1]])

    def both(lab, occ=0):
        a = d.get((lab, occ))
        if a is None:
            return None
        # for 1Q the 3-month column is blank and the cumulative is the 3-month value
        return (a[3], a[2] if a[2] is not None else (a[3] if q == "2023.1Q" else None))

    st = {}
    st[1] = both("보험영업손익"); st[16] = both("기타사업비용"); st[20] = both("영업이익"); st[21] = both("영업외손익"); st[22] = both("법인세비용차감전순이익")
    st[23] = both("법인세비용"); st[24] = both("당기순이익(손실)"); st[25] = both("기타포괄손익")
    st[26] = both("기타포괄손익-공정가치측정채무상품평가손익"); st[27] = both("보험계약자산부채순금융손익"); st[28] = both("현금흐름위험회피파생상품평가손익")
    st[29] = both("기타포괄손익-공정가치측정지분상품평가손익"); st[30] = both("재보험계약자산부채순금융손익"); st[31] = both("총포괄손익"); st[32] = both("순확정급여부채의 재측정요소")
    ins = both("보험영업수익", 1); inc = both("보험영업비용", 1); rin = both("재보험영업수익"); rinc = both("재보험영업비용")
    st[3] = sub(ins, inc); st[8] = sub(rin, rinc); st[2] = add(st[3], st[8])
    if q == "2023.1Q":
        st[18] = both("투자영업손익"); st[19] = both("보험금융손익"); st[17] = add(st[18], st[19])
    else:
        st[17] = both("투자영업손익")
        fin = add(both("보험금융수익"), both("재보험금융수익")); finc = add(both("보험금융비용"), both("재보험금융비용"))
        st[19] = sub(fin, finc); st[18] = sub(st[17], st[19])
        inv = both("투자영업수익"); invc = both("투자영업비용")
        alt = sub(sub(inv, fin), sub(invc, finc))
        P("   item18 route check: (투자영업수익-금융수익)-(투자영업비용-금융비용) =", alt[0], "vs 17-19 =", st[18][0], "| master LIVE", PLL.get((18, q), (None,))[0], "| item17 printed", st[17][0], "master", PLL.get((17, q), (None,))[0])
    st[15] = (0.0, 0.0)
    lob = [(i, t) for i, t in after(tb, ist["pos"]) if any(r and r[0][0] == "서비스제공에 따른 보험계약마진의 변동" for r in t["rows"])]
    P("   LOB note tables after IS:", [(i, t["line"]) for i, t in lob])
    prior = lob[1][1]
    P("   prior LOB table header:", [c for c, _ in prior["rows"][0]][:3])

    def lobcum(lab, which=0):
        hits = [r for r in prior["rows"] if r and r[0][0].replace(" ", "") == lab.replace(" ", "")]
        r = hits[which]
        v = [N(c) for c, _ in r[1:]]
        return (v[-1], (v[-7] if len(v) >= 12 else v[-1]))

    st[4] = lobcum("서비스제공에 따른 보험계약마진의 변동"); st[5] = lobcum("위험해제에 따른 위험조정의 변동 (보험수익)")
    ec = lobcum("예상보험금 및 예상보험서비스 비용"); ac = lobcum("실제보험금 및 실제보험서비스비용")
    st[6] = add(ec, ac)
    st[7] = sub(sub(sub(st[3], st[4]), st[5]), st[6])
    st[9] = lobcum("제공받은 서비스의 재보험계약마진"); st[10] = lobcum("위험해제로 인한 위험조정의 변동")
    r_exp = lobcum("회수예상 보험금 및 보험서비스비용"); r_act = lobcum("발생 재보험금 및 재보험서비스비용 회수액")
    st[11] = add(r_exp, r_act)
    st[12] = sub(sub(sub(st[8], st[9]), st[10]), st[11])
    st[13] = (0.0, 0.0); st[14] = (0.0, 0.0)
    for it, v in st.items():
        EXP[(it, q)] = v
    cs = [(i, t) for i, t in after(tb, ist["pos"]) if any(r and r[0][0] == "기초 보험계약마진" for r in t["rows"]) and any("전" in c for c, _ in t["rows"][0])]
    P("   CSM prior tables (after IS):", [(i, t["line"], [c for c, _ in t["rows"][0]]) for i, t in cs])
    pt = cs[0][1]

    def rr(lab):
        return [N(c) for c, _ in [x for x in pt["rows"] if x and x[0][0] == lab][0][1:]][-1]

    op = rr("기초 보험계약마진"); nb = rr("신계약 인식효과"); fn = rr("보험금융손익"); est = rr("보험계약마진을 조정하는 추정치 변동"); am = rr("제공된 서비스 관련 당기손익 인식")
    cl = rr("분기말 보험계약마진" if q != "2023.2Q" else "반기말 보험계약마진")
    P("   CSM(백만원): open", op, "new", nb, "int", fn, "est", est, "amort", am, "close", cl, "residual(open+new+int+est+amort-close)=", round(op + nb + fn + est + am - cl, 3))
    P("   CSM prior table 보험수익 row (issued contracts):", [c for c, _ in [x for x in pt["rows"] if x and x[0][0] == "보험수익"][0]])
    CEXP[(1, q)] = op; CEXP[(2, q)] = nb; CEXP[(3, q)] = fn; CEXP[(4, q)] = est; CEXP[(5, q)] = am; CEXP[(6, q)] = cl

CH = json.load(open(OUT + "v01_changes_PL_breakdown.json", encoding="utf-8"))
changed_val = {(k[1], k[2]) for k, f, o, n in CH if f == "값"}
P("\n=== PL cumulative: master LIVE vs own re-read (백만원). OK / ROUND1 (|diff|<=1) / DIFF ; CHG = value changed vs HEAD")
rows = []
for q in SRC:
    for it in range(1, 33):
        e = EXP.get((it, q)); live_v = PLL.get((it, q), (None, None))[0]; head_v = PLH.get((it, q), (None, None))[0]
        ch = (it, q) in changed_val
        if e is None or live_v is None:
            P(f"{q} item{it:>2} live={live_v} head={head_v} exp={e} -> NO EXPECTATION/NO LIVE")
            continue
        diff = live_v - e[0]
        st_ = "OK" if abs(diff) < 5e-4 else ("ROUND1" if abs(diff) <= 1.0 + 5e-4 else "DIFF")
        rows.append((q, it, live_v, head_v, e[0], diff, st_, ch))
        if ch or st_ != "OK":
            P(f"{q} item{it:>2} live={live_v:>12} head={head_v!s:>10} reread={e[0]:>12} diff={diff:+.1f} {st_} {'CHG' if ch else 'unchg'}")
nchg = [r for r in rows if r[7]]
P("changed cumulative cells reread:", len(nchg), "OK", sum(1 for r in nchg if r[6] == "OK"), "ROUND1", sum(1 for r in nchg if r[6] == "ROUND1"), "DIFF", sum(1 for r in nchg if r[6] == "DIFF"))
P("unchanged cells: OK", sum(1 for r in rows if not r[7] and r[6] == "OK"), "| not-OK:", [(r[0], r[1], r[2], r[4], round(r[5], 1), r[6]) for r in rows if not r[7] and r[6] != "OK"])

P("\n=== PL single-quarter (값_당분기): master LIVE vs printed prior 3-month column and vs consecutive-cumulative difference")
for q in SRC:
    pq = {"2023.1Q": None, "2023.2Q": "2023.1Q", "2023.3Q": "2023.2Q"}[q]
    for it in range(1, 33):
        e = EXP.get((it, q)); lv = PLL.get((it, q))
        if e is None or lv is None:
            continue
        cum = lv[0]; dq = lv[1]
        if cum is None:
            P(f"{q} item{it} cum None dangi {dq}"); continue
        prev = PLL.get((it, pq), (None,))[0] if pq else 0.0
        calc = None if prev is None else cum - prev
        printed = e[1]
        bad = []
        if calc is None or dq is None or abs(dq - calc) > 5e-4:
            bad.append(f"dangi!=cum-diff (dangi={dq}, calc={calc})")
        if printed is not None and dq is not None and abs(dq - printed) > 3.0 + 5e-4:
            bad.append(f"vs printed 3m {printed} diff {dq - printed:+.1f}")
        elif printed is not None and dq is not None and abs(dq - printed) > 5e-4:
            bad.append(f"vs printed 3m {printed} (rounding {dq - printed:+.1f})")
        if bad:
            P(f"{q} item{it:>2} dangi={dq} cum={cum} " + "; ".join(bad))

P("\n=== CSM: master LIVE vs own re-read (억원 = 백만원/100, 1 dec)")
chg_csm = {(k[1], k[2]) for k, f, o, n in json.load(open(OUT + "v01_changes_CSM_waterfall.json", encoding="utf-8")) if f == "값"}
for q in SRC:
    for it in range(1, 7):
        lv = CSL[(it, q)][0]; hv = CSH[(it, q)][0]
        ev = CEXP[(it, q)] / 100.0
        ev_r = round(ev + 1e-9, 1)
        flag = "OK" if abs(lv - ev_r) < 1e-6 else ("ROUND.1" if abs(lv - ev_r) <= 0.1 + 1e-6 else "DIFF")
        P(f"{q} CSM{it} live={lv} head={hv} reread={ev:.4f}->{ev_r} {flag} {'CHG' if (it, q) in chg_csm else 'unchg'}")
open(OUT + "v07_reread.txt", "w", encoding="utf-8").write("\n".join(out))
json.dump({f"{k[0]}|{k[1]}": v for k, v in EXP.items()}, open(OUT + "v07_exp_pl.json", "w", encoding="utf-8"), ensure_ascii=False)
