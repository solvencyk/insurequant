"""Loss-ratio panels vs the master: an independent recomputation (offline, read-only, a few seconds).

Why this exists (2026-10-19): the builders' own --check only proves "rebuild == file on disk". A unit-scale bug (million-won
filers divided by 100 twice) sat inside both the builders and their --check, so the check stayed green while risk premiums
were 100x too small. This test recomputes the numbers straight from data/loss_ratio/master_loss_ratio.json WITHOUT importing
any builder and compares them with the two shipped panels:

  (a) panel_loss_ratio.json  leaf-row 5th element (risk premium, eok)  == master value (+-0.005)
  (b) panel_compare.json     loss_curve.up                              == master sums, same cells (unit x company x quarter x year)
  (c) no unit x company risk-premium sum jumps by more than 30x between consecutive disclosed quarters
  (d) loss-ratio cells (loss_curve.u / g, metric loss_pv.vu) == half-up rounding (JS toFixed) of the master-derived ratio
  (e) the rest of the loss-ratio numbers: 합계 curve (loss_curve.v), 합계 현재가치 (loss_pv.v), 구분 현재가치 (vg) and the six sector
      medians (loss_curve.med / med_g / med_u, loss_pv med / medg / medu); a median is half-up on the DECIMAL mean of the two middle
      company cells (89.3 and 89.4 -> 89.4), not on the binary float
  (f) unit list and company composition: which units qualify (>=10 filers and >=1% of the sector, reinsurers >=4), n_companies /
      n_sector / alt_n / alt_gubun and the alt_co company list, all recomputed from the master

Each check is a function returning a list of mismatches. The mutation tests feed the SAME functions an in-memory copy of the
master with the old x0.01 scale (or a 100x quarter, or banker-style rounding) and require a non-empty result, so the test can
not silently become a tautology.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_loss_unit_panels_vs_master.py -q
"""
from __future__ import annotations

import copy
import json
import statistics
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data" / "loss_ratio" / "master_loss_ratio.json"
PANEL_LR = ROOT / "data" / "loss_ratio" / "panel_loss_ratio.json"
PANEL_CMP = ROOT / "data" / "compare" / "panel_compare.json"

TOL = 0.005 + 1e-9                  # 0.005 허용 + 부동소수 여유(0.535 -> 0.54 처럼 반올림이 딱 0.005 인 칸)
JUMP_X = 30.0
GROUPS = ("Non-Par", "Direct-Par", "Indirect-Par")
PV = "현재가치"
# 단위 표기별 억원 환산 배수: 마스터 위험보험료는 이미 억원이다(백만원 원문은 빌더가 ÷100 해서 싣고 `단위` 열에는 원문 표기만 남는다).
GOOD_SCALE = {"억원": 1.0, "백만원": 1.0}
OLD_BUG_SCALE = {"억원": 1.0, "백만원": 0.01}            # 2026-10-19 에 고친 버그: 백만원 공시사를 한 번 더 ÷100
RE_PAIRS = {("생명", "건강"), ("생명", "사망"), ("장기손해", "질병"), ("장기손해", "상해")}
SECTOR_OF_TYPE = {"생보": "생보", "손보": "손보", "재보·보증": "재보"}


def hu(x: float, dec: int = 1) -> float:
    """Half-up on the exact binary value = JS Number.toFixed(dec)."""
    return float(Decimal(x).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP))


def bankerish(x: float, dec: int = 1) -> float:
    return round(x, dec)


@pytest.fixture(scope="module")
def master() -> list[dict]:
    return json.loads(MASTER.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def panel_lr() -> dict:
    return json.loads(PANEL_LR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def panel_cmp() -> dict:
    return json.loads(PANEL_CMP.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------- shared master views
def _is_leaf(r: dict) -> bool:
    return r["구분"] in GROUPS and r["포트폴리오"] not in ("합계", "")


def _seg_group(seg: str, pf: str):
    if seg.startswith("생명"):
        return "생명"
    if seg.startswith("장기손해"):
        return "장기손해"
    if seg == "":
        return "생명" if pf in ("건강", "사망") else ("장기손해" if pf in ("질병", "상해") else None)
    return None


def _unit_key(sector: str, seg: str, g: str, prod: str, pf: str):
    """Unit identity the panel lists: 원수사 (업권, 구분, 상품구분, 포트폴리오), 재보사 (재보, 세그먼트 묶음, 포트폴리오)."""
    if sector != "재보":
        return (sector, g, prod, pf)
    sg = _seg_group(seg, pf)
    if g != "Non-Par" or prod not in ("", "무배당") or sg is None or (sg, pf) not in RE_PAIRS:
        return None
    return ("재보", sg, pf)


def _panel_unit_index(panel_cmp: dict) -> dict:
    idx = {}
    for d in panel_cmp["loss_curve"]["units"]:
        if d["sector"] == "재보":
            idx[("재보", d["seg"], d["portfolio"])] = d["key"]
        else:
            idx[(d["sector"], d["gubun"], d["product"], d["portfolio"])] = d["key"]
    assert len(idx) == len(panel_cmp["loss_curve"]["units"])
    return idx


def _roster(panel_cmp: dict) -> dict:
    return {c["code"]: SECTOR_OF_TYPE[c["type"]] for c in panel_cmp["companies"]}


def _leaf_cells(master, roster, quarters, scale_of, only_slots=None):
    """leaf[(code, q)][(seg, g, prod, pf)][year] = (rp_raw, ec_raw, rp_eok). Master order, duplicates are an error."""
    leaf: dict = defaultdict(dict)
    for r in master:
        if not _is_leaf(r) or r["원보험사코드"] not in roster or r["공시분기"] not in quarters:
            continue
        lk = (r.get("세그먼트") or "", r["구분"], r.get("상품구분") or "", r["포트폴리오"])
        slot = leaf[(r["원보험사코드"], r["공시분기"])].setdefault(lk, {})
        yr = r["경과차년"]
        assert yr not in slot, ("마스터 잎 행 키 중복", r["원보험사코드"], r["공시분기"], lk, yr)
        rp, ec = r["위험보험료"], r["예상보험금"]
        slot[yr] = (rp, ec, None if rp is None else rp * scale_of[r["단위"]])
    return leaf


def _unit_sums(master, panel_cmp, scale_of):
    """acc[tok][code][q][year] = [Σrp_raw, Σec_raw, Σrp_eok] over the unit's leaf rows (both amounts present) -- builder-independent."""
    roster = _roster(panel_cmp)
    quarters = set(panel_cmp["meta"]["quarters"])
    idx = _panel_unit_index(panel_cmp)
    leaf = _leaf_cells(master, roster, quarters, scale_of)
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for (c, q), lks in leaf.items():
        for lk, ym in lks.items():
            uk = _unit_key(roster[c], *lk)
            tok = idx.get(uk) if uk is not None else None
            if tok is None:
                continue
            for y, (rp, ec, rpe) in ym.items():
                if rp is None or ec is None:
                    continue
                a = acc[tok][c][q].setdefault(y, [0.0, 0.0, 0.0])
                a[0] += rp
                a[1] += ec
                a[2] += rpe
    return acc


# ---------------------------------------------------------------------------------------------- (a)
def check_a_panel_loss_ratio_rp(master, panel_lr, scale_of) -> tuple[list, int]:
    """Every shipped leaf row's risk-premium array must equal the master value (eok, +-0.005)."""
    expected: dict = {}
    for r in master:
        if not _is_leaf(r):
            continue
        key = (r["원보험사코드"], r["공시분기"], r.get("세그먼트") or "", (r["구분"], r.get("상품구분") or "", r["포트폴리오"]), r["경과차년"])
        b = r["위험보험료"]
        expected[key] = None if b is None else b * scale_of[r["단위"]]
    years = panel_lr["meta"]["years"]
    bad, n = [], 0
    for code, comp in panel_lr["companies"].items():
        for q, qd in comp["q"].items():
            cols = qd.get("c")
            for seg, body in qd["s"].items():
                cs = cols.get(seg, years) if isinstance(cols, dict) else (cols or years)
                for row in body:
                    if len(row) < 5:
                        continue
                    for yr, got in zip(cs, row[4]):
                        key = (code, q, seg, (row[0], row[1], row[2]), yr)
                        want = expected.get(key)          # 마스터에 그 열 행이 없으면 빌더가 None 으로 채운다(다른 잎 행 때문에 열이 생긴 경우)
                        n += 1
                        if (got is None) != (want is None) or (got is not None and abs(got - want) > TOL):
                            bad.append((key, got, want))
    return bad, n


# ---------------------------------------------------------------------------------------------- (b)
def check_b_up(master, panel_cmp, scale_of) -> tuple[list, int]:
    """loss_curve.up must equal the master sums, cell for cell (a cell is present iff the unit's Σrp > 0)."""
    acc = _unit_sums(master, panel_cmp, scale_of)
    labels = panel_cmp["loss_curve"]["labels"]
    up = panel_cmp["loss_curve"]["up"]
    bad, n = [], 0
    toks = set(up) | set(acc)
    for tok in sorted(toks):
        exp = {}
        for c, qd in acc.get(tok, {}).items():
            for q, yd in qd.items():
                row = {labels.index(y): a[2] for y, a in yd.items() if y in labels and a[0] > 0}
                if row:
                    exp[(c, q)] = row
        got = {(c, q): {k: v for k, v in enumerate(arr) if v is not None} for c, qd in up.get(tok, {}).items() for q, arr in qd.items()}
        for key in sorted(set(exp) | set(got)):
            e, g = exp.get(key, {}), got.get(key, {})
            for k in sorted(set(e) | set(g)):
                n += 1
                if k not in e or k not in g or abs(e[k] - g[k]) > TOL:
                    bad.append((tok, key, labels[k], g.get(k), e.get(k)))
    return bad, n


# ---------------------------------------------------------------------------------------------- (c)
def check_c_jumps(master, scale_of) -> tuple[list, int]:
    """Σ risk premium (eok) per company x (구분, 상품구분, 포트폴리오) and quarter; consecutive disclosed quarters must not move > 30x."""
    tot: dict = defaultdict(float)
    for r in master:
        if not _is_leaf(r) or r["경과차년"] == PV:
            continue
        rp = r["위험보험료"]
        if rp is None or rp <= 0:
            continue
        tot[(r["원보험사코드"], r["구분"], r.get("상품구분") or "", r["포트폴리오"], r["공시분기"])] += rp * scale_of[r["단위"]]
    series: dict = defaultdict(dict)
    for (c, g, p, f, q), v in tot.items():
        series[(c, g, p, f)][q] = v

    def qkey(q):
        return (int(q[:4]), int(q[5]))
    bad, n = [], 0
    for k, d in series.items():
        qs = sorted(d, key=qkey)
        for a, b in zip(qs, qs[1:]):
            n += 1
            lo, hi = sorted((d[a], d[b]))
            if hi / lo > JUMP_X:
                bad.append((k, a, b, round(d[a], 2), round(d[b], 2)))
    return bad, n


# ---------------------------------------------------------------------------------------------- (d)
def check_d_ratio_cells(master, panel_cmp, rnd) -> tuple[list, int]:
    """u / g cells and loss_pv.vu cells == rnd(Σec/Σrp x 100), None iff Σrp <= 0."""
    lc = panel_cmp["loss_curve"]
    labels = lc["labels"]
    bad, n = [], 0
    # u: unit x company x quarter x year
    acc = _unit_sums(master, panel_cmp, GOOD_SCALE)
    for tok in sorted(set(lc["u"]) | set(acc)):
        for c in sorted(set(lc["u"].get(tok, {})) | set(acc.get(tok, {}))):
            qs = set(lc["u"].get(tok, {}).get(c, {})) | set(acc.get(tok, {}).get(c, {}))
            for q in sorted(qs):
                got = lc["u"].get(tok, {}).get(c, {}).get(q, [None] * len(labels))
                for k, y in enumerate(labels):
                    a = acc.get(tok, {}).get(c, {}).get(q, {}).get(y)
                    want = rnd(a[1] / a[0] * 100.0) if a and a[0] > 0 else None
                    n += 1
                    if got[k] != want:
                        bad.append(("u", tok, c, q, y, got[k], want))
    # vu: 현재가치 per unit x company (quarter columns = panel meta quarters)
    quarters = panel_cmp["meta"]["quarters"]
    roster = _roster(panel_cmp)
    idx = _panel_unit_index(panel_cmp)
    pv_acc = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0])))
    leaf = _leaf_cells(master, roster, set(quarters), GOOD_SCALE)
    for (c, q), lks in leaf.items():
        for lk, ym in lks.items():
            uk = _unit_key(roster[c], *lk)
            tok = idx.get(uk) if uk is not None else None
            if tok is None or PV not in ym:
                continue
            rp, ec, _ = ym[PV]
            if rp is None or ec is None:
                continue
            a = pv_acc[tok][c][q]
            a[0] += rp
            a[1] += ec
    vu = next(m for m in panel_cmp["metrics"] if m["id"] == "loss_pv")["vu"]
    for tok in sorted(set(vu) | set(pv_acc)):
        for c in sorted(set(vu.get(tok, {})) | set(pv_acc.get(tok, {}))):
            got = vu.get(tok, {}).get(c, [None] * len(quarters))
            for i, q in enumerate(quarters):
                a = pv_acc.get(tok, {}).get(c, {}).get(q)
                want = rnd(a[1] / a[0] * 100.0) if a and a[0] > 0 else None
                if a is None and got[i] is None:
                    continue
                n += 1
                if got[i] != want:
                    bad.append(("vu", tok, c, q, got[i], want))
    # g: 구분 curve = all leaf rows of the 구분 (every portfolio, every segment), summed per company x quarter x year
    g_acc = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))))
    for (c, q), lks in leaf.items():
        for (seg, g, prod, pf), ym in lks.items():
            for y, (rp, ec, _) in ym.items():
                if y in labels and rp is not None and ec is not None:
                    a = g_acc[g][c][q][y]
                    a[0] += rp
                    a[1] += ec
    for g in GROUPS:
        gp = lc["g"].get(g, {})
        for c in sorted(set(gp) | set(g_acc[g])):
            for q in sorted(set(gp.get(c, {})) | set(g_acc[g][c])):
                got = gp.get(c, {}).get(q, [None] * len(labels))
                for k, y in enumerate(labels):
                    a = g_acc[g][c][q].get(y) if q in g_acc[g][c] else None
                    want = rnd(a[1] / a[0] * 100.0) if a and a[0] > 0 else None
                    n += 1
                    if got[k] != want:
                        bad.append(("g", g, c, q, y, got[k], want))
    return bad, n


# ---------------------------------------------------------------------------------------------- (e) totals, PV, medians
RE_TYPE = "재보·보증"
MED_MIN = 5                                 # 업계 중앙값: 값이 있는 회사 수 하한(곡선·현재가치·단위 모두 5)


def qkey(q: str):
    return (int(q[:4]), int(q[5]))


def dmed(xs, dec: int = 1) -> float:
    """Median of already-rounded company values, half-up on the DECIMAL value (what the screen shows): the mean of 89.3 and 89.4
    is 89.35 and rounds to 89.4. Fraction arithmetic, no binary noise."""
    f = sorted(Fraction(repr(float(x))) for x in xs)
    n = len(f)
    m = f[n // 2] if n % 2 else (f[n // 2 - 1] + f[n // 2]) / 2
    k = (m * 10 ** dec + Fraction(1, 2)).__floor__()
    return k / 10 ** dec


def old_binary_med(xs, dec: int = 1) -> float:
    """The pre-fix rule: half-up on the binary mean (statistics.median of floats)."""
    return hu(statistics.median(xs), dec)


def _ratio(a, rnd=hu, dec: int = 1):
    return rnd(a[1] / a[0] * 100.0, dec) if a and a[0] > 0 else None


def _leaf_valid_years(master, roster, quarters, labels):
    """_leaf_cells restricted to the year columns the panel draws (labels + 현재가치); empty (company, quarter) slots dropped."""
    ok = set(labels) | {PV}
    out = {}
    for key, lks in _leaf_cells(master, roster, quarters, GOOD_SCALE).items():
        kept = {lk: {y: v for y, v in ym.items() if y in ok} for lk, ym in lks.items()}
        kept = {lk: ym for lk, ym in kept.items() if ym}
        if kept:
            out[key] = kept
    return out


def _flat_diff(tag, got: dict, want: dict, width: int):
    """got/want: key -> list of cells. A missing key means all-None. Returns (mismatching cells, cells compared)."""
    bad, n = [], 0
    blank = [None] * width
    for key in sorted(set(got) | set(want), key=repr):
        g, w = got.get(key) or blank, want.get(key) or blank
        n += width
        if len(g) != width or len(w) != width:
            bad.append((tag, key, "length", len(g), len(w)))
            continue
        for k in range(width):
            if g[k] != w[k]:
                bad.append((tag, key, k, g[k], w[k]))
    return bad, n


def check_e_totals_and_medians(master, panel_cmp, med=dmed) -> tuple[list, int]:
    """Everything (d) leaves out: 합계 curve (loss_curve.v), 합계 현재가치 (loss_pv.v), 구분 현재가치 (vg) and the six sector medians
    (curve med, 구분 med_g, 단위 med_u, loss_pv med / medg / medu). Medians are taken over the master-derived company cells."""
    lc = panel_cmp["loss_curve"]
    labels, K = lc["labels"], lc["n_std"]
    quarters = panel_cmp["meta"]["quarters"]
    NQ, QI = len(quarters), {q: i for i, q in enumerate(quarters)}
    comp = {c["code"]: c for c in panel_cmp["companies"]}
    roster = _roster(panel_cmp)
    pv_metric = next(m for m in panel_cmp["metrics"] if m["id"] == "loss_pv")
    pdec = pv_metric["dec"]
    bad, n = [], 0

    def pool_by_type(ty):
        return [c for c, d in comp.items() if d["type"] == ty and ty != RE_TYPE]

    def pool_by_sector(sec):
        if sec == "재보":
            return [c for c, d in comp.items() if d["type"] == RE_TYPE and d["sector"] == "재보험"]
        return pool_by_type(next(t for t, s in SECTOR_OF_TYPE.items() if s == sec))

    # --- 합계 포트폴리오: curve cells and 현재가치 per company
    tot = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0])))
    for r in master:
        if r["구분"] != "합계" or r["포트폴리오"] != "합계" or r["원보험사코드"] not in roster or r["공시분기"] not in QI:
            continue
        y = r["경과차년"]
        if (y not in labels and y != PV) or r["위험보험료"] is None or r["예상보험금"] is None:
            continue
        a = tot[r["원보험사코드"]][r["공시분기"]][y]
        a[0] += r["위험보험료"]
        a[1] += r["예상보험금"]
    tcurve = {(c, q): [_ratio(ym.get(y)) for y in labels] for c, qd in tot.items() for q, ym in qd.items()}
    tpv = {c: [None] * NQ for c in tot}
    for c, qd in tot.items():
        for q, ym in qd.items():
            tpv[c][QI[q]] = _ratio(ym.get(PV), hu, pdec)
    got_v = {(c, q): row for c, qd in lc["v"].items() for q, row in qd.items()}
    b, k = _flat_diff("v", got_v, tcurve, len(labels))
    bad += b
    n += k
    b, k = _flat_diff("pv.v", {c: row for c, row in pv_metric["v"].items()}, tpv, NQ)
    bad += b
    n += k

    # --- 구분 (all leaf rows of the 구분): curve cells and 현재가치
    leaf = _leaf_valid_years(master, roster, set(quarters), labels)
    gacc = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))))
    for (c, q), lks in leaf.items():
        for (seg, g, prod, pf), ym in lks.items():
            for y, (rp, ec, _) in ym.items():
                if rp is not None and ec is not None:
                    a = gacc[g][c][q][y]
                    a[0] += rp
                    a[1] += ec
    gcurve = {g: {(c, q): [_ratio(ym.get(y)) for y in labels] for c, qd in gacc[g].items() for q, ym in qd.items()} for g in GROUPS}
    gpv = {g: {c: [None] * NQ for c in gacc[g]} for g in GROUPS}
    for g in GROUPS:
        for c, qd in gacc[g].items():
            for q, ym in qd.items():
                gpv[g][c][QI[q]] = _ratio(ym.get(PV), hu, pdec)
    for g in GROUPS:
        got_vg = pv_metric["vg"].get(g, {})
        b, k = _flat_diff(("vg", g), got_vg, gpv[g], NQ)
        bad += b
        n += k

    # --- medians
    def curve_med(cells, pool):
        """cells: (company, quarter) -> row. -> quarter -> row of K medians (needs MED_MIN values)."""
        out = {}
        for q in {q for (c, q) in cells if c in pool}:
            out[q] = [(med(xs) if len(xs := [cells[(c, q)][j] for c in pool if (c, q) in cells and cells[(c, q)][j] is not None]) >= MED_MIN else None)
                      for j in range(K)]
        return out

    for ty in {d["type"] for d in comp.values()}:                       # curve med
        want = curve_med(tcurve, pool_by_type(ty))
        got = lc["med"].get(ty, {})
        b, k = _flat_diff(("med", ty), {q: r for q, r in got.items()}, want, K)
        bad += b
        n += k
        for g in GROUPS:                                                # 구분 med_g
            want = curve_med(gcurve[g], pool_by_type(ty))
            got = lc["med_g"].get(ty, {}).get(g, {})
            b, k = _flat_diff(("med_g", ty, g), got, want, K)
            bad += b
            n += k

    def pv_med(series, pool):
        return [(med(xs) if len(xs := [series[c][i] for c in pool if c in series and series[c][i] is not None]) >= MED_MIN else None)
                for i in range(NQ)]

    for ty in {d["type"] for d in comp.values()}:                       # loss_pv med / medg
        b, k = _flat_diff(("pv.med", ty), {0: pv_metric["med"].get(ty)}, {0: pv_med(tpv, pool_by_type(ty))}, NQ)
        bad += b
        n += k
        for g in GROUPS:
            b, k = _flat_diff(("pv.medg", ty, g), {0: pv_metric["medg"].get(g, {}).get(ty)}, {0: pv_med(gpv[g], pool_by_type(ty))}, NQ)
            bad += b
            n += k

    # --- 단위 medians (cell values from the unit sums, pool by 업권)
    acc = _unit_sums(master, panel_cmp, GOOD_SCALE)
    idx = _panel_unit_index(panel_cmp)
    pv_acc = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0.0, 0.0])))
    for (c, q), lks in leaf.items():
        for lk, ym in lks.items():
            uk = _unit_key(roster[c], *lk)
            tok = idx.get(uk) if uk is not None else None
            if tok is None or PV not in ym or ym[PV][0] is None or ym[PV][1] is None:
                continue
            a = pv_acc[tok][c][q]
            a[0] += ym[PV][0]
            a[1] += ym[PV][1]
    for d in lc["units"]:
        tok, sec = d["key"], d["sector"]
        pool = pool_by_sector(sec)
        ucells = {(c, q): [_ratio(yd.get(y)) for y in labels] for c, qd in acc.get(tok, {}).items() for q, yd in qd.items()}
        want = curve_med(ucells, pool)
        want = {q: r for q, r in want.items() if any(x is not None for x in r)}
        b, k = _flat_diff(("med_u", tok), lc["med_u"].get(sec, {}).get(tok, {}), want, K)
        bad += b
        n += k
        upv = {c: [None] * NQ for c in pv_acc.get(tok, {})}
        for c, qd in pv_acc.get(tok, {}).items():
            for q, a in qd.items():
                upv[c][QI[q]] = _ratio(a, hu, pdec)
        b, k = _flat_diff(("medu", tok), {0: pv_metric["medu"].get(tok, {}).get(sec)}, {0: pv_med(upv, pool)}, NQ)
        bad += b
        n += k
    return bad, n


# ---------------------------------------------------------------------------------------------- (f) company composition (alt_co)
def check_f_unit_composition(master, panel_cmp) -> tuple[list, int]:
    """Recompute from the master: the unit list (>=10 disclosing companies and >=1% of the sector's risk premium; reinsurers >=4),
    each unit's n_companies / n_sector, and alt_co[unit] = companies without the unit that disclose the same 상품구분 x 포트폴리오
    under another 구분 which is itself not a listed unit. A swapped company code must show up here."""
    lc = panel_cmp["loss_curve"]
    labels = lc["labels"]
    quarters = set(panel_cmp["meta"]["quarters"])
    roster = _roster(panel_cmp)
    leaf = _leaf_valid_years(master, roster, quarters, labels)
    uq = max((q for (_, q) in leaf), key=qkey)
    bad, n = [], 0
    if uq != lc["unit_rule"]["quarter"]:
        bad.append(("unit_rule.quarter", lc["unit_rule"]["quarter"], uq))
    sector_cos = defaultdict(set)
    sector_total = defaultdict(float)
    u_rp = defaultdict(lambda: defaultdict(float))
    co_labels = defaultdict(set)
    for (c, q), lks in leaf.items():
        if q != uq:
            continue
        sec = roster[c]
        sector_cos[sec].add(c)
        for lk, ym in lks.items():
            w = sum(rp for y, (rp, ec, _) in ym.items() if y in labels and rp is not None and rp > 0)
            if w <= 0:
                continue
            sector_total[sec] += w
            uk = _unit_key(sec, *lk)
            if uk is not None:
                u_rp[uk][c] += w
            if sec != "재보":
                co_labels[c].add(lk[1:])
    selected = {}
    for uk, per_co in u_rp.items():
        sec, cnt = uk[0], sum(1 for w in per_co.values() if w > 0)
        share = sum(per_co.values()) / sector_total[sec] * 100.0
        if (sec == "재보" and cnt >= 4) or (sec != "재보" and cnt >= 10 and share >= 1.0):
            selected[uk] = cnt
    idx = _panel_unit_index(panel_cmp)
    n += 1
    if set(idx) != set(selected):
        bad.append(("unit list", sorted(set(idx) ^ set(selected))))
    sel_keys = {(uk[0],) + uk[1:] for uk in selected if uk[0] != "재보"}            # (업권, 구분, 상품구분, 포트폴리오)
    for d in lc["units"]:
        uk = (d["sector"], d["seg"], d["portfolio"]) if d["sector"] == "재보" else (d["sector"], d["gubun"], d["product"], d["portfolio"])
        have = {c for c, w in u_rp.get(uk, {}).items() if w > 0}
        alt = {}
        if d["sector"] != "재보":
            for c in sector_cos[d["sector"]] - have:
                gs = {lab[0] for lab in co_labels[c] if lab[1:] == uk[2:] and lab[0] != uk[1] and (uk[0],) + lab not in sel_keys}
                if gs:
                    alt[c] = gs
        want = (len(have), len(sector_cos[d["sector"]]), len(alt), sorted({g for gs in alt.values() for g in gs}), sorted(alt))
        got = (d["n_companies"], d["n_sector"], d["alt_n"], d["alt_gubun"], lc["alt_co"][d["key"]])
        n += 1
        if got != want:
            bad.append(("unit", d["key"], got, want))
    return bad, n



# ================================================================================================ the tests
def test_master_units_are_known(master):
    assert {r["단위"] for r in master} <= set(GOOD_SCALE), "새 단위 표기: 환산 배수를 정하고 이 테스트와 빌더 표를 같이 고쳐라"
    assert any(r["단위"] == "백만원" for r in master), "백만원 공시사가 없으면 아래 변이시험이 의미가 없다"


def test_a_panel_loss_ratio_risk_premium_matches_master(master, panel_lr):
    bad, n = check_a_panel_loss_ratio_rp(master, panel_lr, GOOD_SCALE)
    assert n > 10_000, f"비교한 칸이 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 칸 불일치, 처음 5개: {bad[:5]}"


def test_b_compare_up_matches_master_sums(master, panel_cmp):
    bad, n = check_b_up(master, panel_cmp, GOOD_SCALE)
    assert n > 2_000, f"비교한 칸이 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 칸 불일치, 처음 5개: {bad[:5]}"


def test_c_no_unit_company_risk_premium_jumps(master):
    bad, n = check_c_jumps(master, GOOD_SCALE)
    assert n > 300, f"비교한 분기 쌍이 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 쌍이 {JUMP_X:g}배 넘게 뛴다(단위 환산 의심), 처음 5개: {bad[:5]}"


def test_d_ratio_cells_are_half_up_of_master_ratio(master, panel_cmp):
    bad, n = check_d_ratio_cells(master, panel_cmp, hu)
    assert n > 5_000, f"비교한 칸이 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 칸 불일치, 처음 5개: {bad[:5]}"


def test_e_totals_pv_and_sector_medians_match_master(master, panel_cmp):
    bad, n = check_e_totals_and_medians(master, panel_cmp)
    assert n > 4_000, f"비교한 칸이 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 칸 불일치, 처음 5개: {bad[:5]}"


def test_f_unit_list_and_company_composition_match_master(master, panel_cmp):
    bad, n = check_f_unit_composition(master, panel_cmp)
    assert n >= 13, f"비교한 단위가 너무 적다({n})"
    assert not bad, f"{len(bad)}/{n} 건 불일치: {bad[:3]}"


def test_alt_co_lists_match_alt_n(panel_cmp):
    """loss_curve.alt_co[단위키] = 같은 상품을 다른 구분으로 공시한 회사 코드. 개수는 단위의 alt_n 과 같고 코드는 명단 안의 회사여야 한다."""
    lc = panel_cmp["loss_curve"]
    codes = {c["code"] for c in panel_cmp["companies"]}
    assert set(lc["alt_co"]) == {d["key"] for d in lc["units"]}
    for d in lc["units"]:
        a = lc["alt_co"][d["key"]]
        assert len(a) == d["alt_n"] and len(set(a)) == len(a) and set(a) <= codes, d["key"]


# ---------------------------------------------------------------------------------------------- mutation checks
def _with_old_scale_bug(master):
    """In-memory copy where every 백만원 filer's risk premium is divided by 100 once more (the 2026-10-19 bug)."""
    return [dict(r, 위험보험료=(r["위험보험료"] * 0.01 if r["단위"] == "백만원" and r["위험보험료"] is not None else r["위험보험료"]))
            for r in master]


def test_mutation_old_x001_scale_is_caught_by_a_and_b(master, panel_lr, panel_cmp):
    """Feeding the old x0.01 scale must make (a) and (b) fail -- otherwise the checks cannot see the bug they exist for."""
    bad_a, n_a = check_a_panel_loss_ratio_rp(_with_old_scale_bug(master), panel_lr, GOOD_SCALE)
    bad_b, n_b = check_b_up(_with_old_scale_bug(master), panel_cmp, GOOD_SCALE)
    assert bad_a, "mutation (a): x0.01 백만원 스케일이 안 잡힌다"
    assert bad_b, "mutation (b): x0.01 백만원 스케일이 안 잡힌다"
    # and through the unit table the way the builders had it: expected values computed with OLD_BUG_SCALE
    bad_a2, _ = check_a_panel_loss_ratio_rp(master, panel_lr, OLD_BUG_SCALE)
    bad_b2, _ = check_b_up(master, panel_cmp, OLD_BUG_SCALE)
    assert bad_a2 and bad_b2


def test_mutation_scale_bug_in_a_single_quarter_is_caught_by_c(master):
    """A 100x error in one disclosed quarter of one company's rows must trip the jump check (the all-quarters bug is (a)/(b)'s job)."""
    pick = next((r["원보험사코드"], r["공시분기"]) for r in master if _is_leaf(r) and r["위험보험료"] and r["공시분기"] == "2025.4Q")
    mut = [dict(r, 위험보험료=r["위험보험료"] * 100) if (r["원보험사코드"], r["공시분기"]) == pick and r["위험보험료"] else r for r in master]
    bad, _ = check_c_jumps(mut, GOOD_SCALE)
    assert bad, "mutation (c): 한 분기 100배가 안 잡힌다"
    assert not check_c_jumps(master, GOOD_SCALE)[0]


def test_mutation_banker_rounding_is_caught_by_d(master, panel_cmp):
    """Python round() on exact x.x5 ratios differs from half-up; (d) must see it, so the half-up rule is really enforced."""
    bad, _ = check_d_ratio_cells(master, panel_cmp, bankerish)
    assert bad, "mutation (d): 은행식 반올림이 안 잡힌다(x.x5 경계 칸이 없거나 비교가 무뎌졌다)"


def test_mutation_binary_median_rounding_is_caught_by_e(master, panel_cmp):
    """The pre-fix median rule (half-up on the binary mean) put 89.35 at 89.3. (e) must see those tie cells."""
    bad, _ = check_e_totals_and_medians(master, panel_cmp, med=old_binary_med)
    assert bad, "mutation (e): 이진 평균 half-up 중앙값이 안 잡힌다(동점 칸이 없거나 중앙값 비교가 무뎌졌다)"
    tags = {b[0][0] if isinstance(b[0], tuple) else b[0] for b in bad}
    assert tags <= {"med", "med_g", "med_u", "pv.med", "pv.medg", "medu"}, f"중앙값 밖의 칸이 어긋났다: {tags}"


def test_mutation_total_pv_and_median_tamper_is_caught_by_e(master, panel_cmp):
    assert not check_e_totals_and_medians(master, panel_cmp)[0]
    pv_metric = lambda p: next(m for m in p["metrics"] if m["id"] == "loss_pv")
    for where in ("v", "pv.v", "vg", "med", "med_g", "med_u", "pv.med", "pv.medg", "pv.medu"):
        mut = copy.deepcopy(panel_cmp)
        lc = mut["loss_curve"]
        if where == "v":
            row = next(r for qd in lc["v"].values() for r in qd.values())
        elif where == "pv.v":
            row = next(r for r in pv_metric(mut)["v"].values() if any(x is not None for x in r))
        elif where == "vg":
            row = next(r for gd in pv_metric(mut)["vg"].values() for r in gd.values())
        elif where == "med":
            row = next(r for qd in lc["med"].values() for r in qd.values() if any(x is not None for x in r))
        elif where == "med_g":
            row = next(r for td in lc["med_g"].values() for qd in td.values() for r in qd.values() if any(x is not None for x in r))
        elif where == "med_u":
            row = next(r for sd in lc["med_u"].values() for qd in sd.values() for r in qd.values() if any(x is not None for x in r))
        elif where == "pv.med":
            row = next(r for r in pv_metric(mut)["med"].values() if any(x is not None for x in r))
        elif where == "pv.medg":
            row = next(r for gd in pv_metric(mut)["medg"].values() for r in gd.values() if any(x is not None for x in r))
        else:
            row = next(r for td in pv_metric(mut)["medu"].values() for r in td.values() if any(x is not None for x in r))
        k = next(i for i, x in enumerate(row) if x is not None)
        row[k] = round(row[k] + 0.1, 1)
        assert check_e_totals_and_medians(master, mut)[0], f"mutation (e): {where} 한 칸 +0.1 이 안 잡힌다"


def test_mutation_alt_co_company_swap_is_caught_by_f(master, panel_cmp):
    """Replacing one company in an alt_co list by another roster company keeps the length and the 'is a roster code' test green; (f) must not."""
    assert not check_f_unit_composition(master, panel_cmp)[0]
    mut = copy.deepcopy(panel_cmp)
    lc = mut["loss_curve"]
    tok = next(t for t, a in lc["alt_co"].items() if a)
    other = next(c["code"] for c in mut["companies"] if c["code"] not in lc["alt_co"][tok])
    lc["alt_co"][tok][0] = other
    lc["alt_co"][tok].sort()
    assert check_f_unit_composition(master, mut)[0], "mutation (f): alt_co 회사 하나를 다른 회사로 바꿔도 안 잡힌다"
    mut2 = copy.deepcopy(panel_cmp)
    mut2["loss_curve"]["units"][0]["n_companies"] += 1
    assert check_f_unit_composition(master, mut2)[0], "mutation (f): n_companies 변조가 안 잡힌다"


def test_mutation_panel_value_tamper_is_caught(master, panel_cmp):
    bad0, _ = check_b_up(master, panel_cmp, GOOD_SCALE)
    assert not bad0
    mut = copy.deepcopy(panel_cmp)
    tok = next(iter(mut["loss_curve"]["up"]))
    c = next(iter(mut["loss_curve"]["up"][tok]))
    q = next(iter(mut["loss_curve"]["up"][tok][c]))
    arr = mut["loss_curve"]["up"][tok][c][q]
    k = next(i for i, v in enumerate(arr) if v is not None)
    arr[k] = arr[k] * 100 + 1
    assert check_b_up(master, mut, GOOD_SCALE)[0]
