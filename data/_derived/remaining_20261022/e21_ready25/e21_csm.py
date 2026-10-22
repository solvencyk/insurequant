# -*- coding: utf-8 -*-
"""e21 independent CSM roll-forward readers (PRIOR-period vector of the LATER filing, separate basis, issued-contract CSM) + the PL4 note readers (한화 / 미래에셋 / 롯데 2023.1Q).
Own code (e21_raw / measure-phase mlib only; nothing from scripts/ or src/).  Vector order = master items 1..6 = [기초, 신계약, 이자 부리, 가정 및 경험 조정, CSM 상각, 기말] (억원).
Every reader returns dict(vec_exact=[6 floats 억원], vec=[6 floats rounded half-away-from-zero to 1 dp], cells={item: [dict(label, line, printed, sign, unit, contribution_eok)]}, derived={4: ...}, src=...).
Item 4 is the PRINTED 'CSM-adjusting estimate change' where the table prints it (한화, 롯데, 메리츠) or the closing plug close-(open+new+int+amort) where it does not (미래에셋); that is recorded in `derived`."""
import re
import sys
from decimal import ROUND_HALF_UP, Decimal

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

M = T.M
nl = T.nl
DIV_EOK = {"백만원": 100.0, "원": 1e8, "천원": 1e5}


def r1(x):
    """round half away from zero to 1 dp (exact decimal arithmetic on the repr of x)"""
    d = Decimal(repr(round(x, 8)))
    return float(d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def r2(x):
    """round half away from zero to 2 dp (= the printed 백만원 precision of a 억원 value); exact decimal arithmetic on the repr of x"""
    d = Decimal(repr(round(x, 8)))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def eok_cell(label, cell, sign, unit):
    v, ln, tx = cell
    return dict(label=label, line=ln, printed=tx, sign=sign, unit=unit, contribution_eok=sign * v / DIV_EOK[unit])


def finish(cells, derived_item4=False, src="", extra=None):
    ex = [sum(c["contribution_eok"] for c in cells.get(i, [])) for i in range(1, 7)]
    plug = None
    if derived_item4:
        ex[3] = ex[5] - (ex[0] + ex[1] + ex[2] + ex[4])
        plug = "close - (open + new + int + amort)"
    v2 = [r2(x) for x in ex]
    if derived_item4:
        # the plug is taken from the 2-dp rounded operands so that the stored vector closes EXACTLY at 2 dp
        v2[3] = r2(v2[5] - (v2[0] + v2[1] + v2[2] + v2[4]))
    out = dict(vec_exact=ex, vec=v2, vec1=[round(x, 1) for x in ex], cells=cells, derived=({4: plug} if derived_item4 else {}), src=src)
    if extra:
        out.update(extra)
    return out


def sep_tables(path):
    lines = M.read_lines(path)
    s0 = T.sep_notes_from(lines)
    return lines, s0


# ====================================================================================================== 한화생명 (KR0068)
def hanwha_csm(q):
    """FY+1 filing, separate notes, caption '2) 전반기|전분기' roll-forward table [BEL, RA, CSM, 합계]; CSM = 3rd numeric cell"""
    fy = M.later_fy(q)
    path = T.main_path("KR0068", fy)
    lines, s0 = sep_tables(path)
    hits = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        if not re.match(r"^2\)\s*(전분기|전반기|전기)", t["caption"] or ""):
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        if any("최초인식한계약의효과" in x for x in labs) and any(x.startswith("1.기초") and "재보험" not in x for x in labs):
            hits.append((t, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{path.name}: {len(hits)} prior CSM roll-forward tables found (need exactly 1)")
    t, rows = hits[0]
    unit = T.find_unit(lines, t, span=700)

    def row(pred):
        h = [r for r in rows if pred(nl(W.label_of(r)))]
        if len(h) != 1:
            raise RuntimeError(f"{path.name}: {len(h)} rows for predicate")
        return h[0]

    def csm_cell(r):
        n = W.numeric_cells(r)
        if len(n) != 4:
            raise RuntimeError(f"row {W.label_of(r)!r}: {len(n)} numeric cells (need 4)")
        return n[2]

    r_open = [r for r in rows if re.match(r"^1\.기초", nl(W.label_of(r)))]
    r_close = [r for r in rows if re.match(r"^8\.(분기말|반기말|기말)", nl(W.label_of(r)))]
    if len(r_open) != 1 or len(r_close) != 1:
        raise RuntimeError("open/close rows not unique")
    cells = {
        1: [eok_cell(W.label_of(r_open[0]), csm_cell(r_open[0]), 1, unit)],
        2: [eok_cell("(3) 최초 인식한 계약의 효과", csm_cell(row(lambda x: x.startswith("(3)최초인식한계약의효과"))), 1, unit)],
        3: [eok_cell("6. 보험금융손익", csm_cell(row(lambda x: x.startswith("6.보험금융손익"))), 1, unit)],
        4: [eok_cell("(1) 보험계약마진을 조정하는 추정치의 변동분", csm_cell(row(lambda x: x.startswith("(1)보험계약마진을조정하는추정치의변동분"))), 1, unit)],
        5: [eok_cell("(1) 제공한 서비스에 대해 인식한 보험계약마진", csm_cell(row(lambda x: x.startswith("(1)제공한서비스에대해인식한보험계약마진"))), 1, unit)],
        6: [eok_cell(W.label_of(r_close[0]), csm_cell(r_close[0]), 1, unit)],
    }
    grp = csm_cell(row(lambda x: x.startswith("3.현행서비스관련변동")))
    out = finish(cells, False, f"{M.rel(path)} table@L{t['start']} unit {unit}")
    out["check_group_row_5"] = grp      # 3. 현행서비스 관련 변동 CSM cell must equal the amortisation sub-row
    return out


def hanwha_note_pl4(q):
    """한화 PL4 prior: '1. 보험수익' note table of the later filing (caption '2) 전반기|전분기'), row '3) 서비스제공에 따른 보험계약마진의 변동', 합계 (누적) = LAST numeric cell.
    Also returns the same cell of the current-period table (sanity vs the master's current-year PL4)."""
    fy = M.later_fy(q)
    path = T.main_path("KR0068", fy)
    lines, s0 = sep_tables(path)
    found = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        if not any(x.startswith("1.보험수익") for x in labs):
            continue
        hit = [r for r in rows if "서비스제공에따른보험계약마진의변동" in nl(W.label_of(r))]
        if len(hit) != 1:
            continue
        found.append((t, rows, hit[0]))
    prior = [f for f in found if re.match(r"^2\)\s*(전분기|전반기|전기)", f[0]["caption"] or "")]
    cur = [f for f in found if f not in prior]
    if len(prior) != 1 or not cur:
        raise RuntimeError(f"{path.name}: prior {len(prior)} / current {len(cur)} 보험수익 note tables")
    t, rows, r = prior[0]
    unit = T.find_unit(lines, t, span=2500)
    n = W.numeric_cells(r)
    cell = n[-1]
    c_t, _c_rows, c_r = cur[0]
    cn = W.numeric_cells(c_r)
    return dict(val_mn=abs(cell[0]) * (1.0 if unit == "백만원" else (1e-6 if unit == "원" else 1e-3)), part=dict(label=W.label_of(r), line=cell[1], printed=cell[2], sign=1, abs=True, unit=unit, n_numeric=len(n)),
                current_cell=dict(line=cn[-1][1], printed=cn[-1][2]), src=f"{M.rel(path)} table@L{t['start']} (caption {t['caption'][:12]!r}) unit {unit}")


# ====================================================================================================== 메리츠화재 (KR0001)
def meritz_csm(q):
    """FY+1 filing: '(3) 원수 및 출재 측정요소별 변동내역 ... 원수 일반모형' roll-forward, PRIOR (second of the pair) table; CSM = sum of the 3 CSM columns (수정소급법 / 공정가치법 / 그 외)"""
    fy = M.later_fy(q)
    path = T.main_path("KR0001", fy)
    lines, s0 = sep_tables(path)
    pair = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        cap = t["caption"] or ""
        if "원수" not in cap or "일반모형" not in cap or "상세변동내역" not in cap:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        if any("순보험금융손익" in x for x in labs) and any(x.startswith("기초순장부금액") for x in labs):
            pair.append((t, rows))
    if len(pair) < 2:
        raise RuntimeError(f"{path.name}: {len(pair)} Format-B 원수 일반모형 roll-forward tables (need the current/prior pair)")
    t, rows = pair[1]
    unit = T.find_unit(lines, t, span=700)

    def row(pred, nth=1):
        h = [r for r in rows if pred(nl(W.label_of(r)))]
        if len(h) < nth:
            raise RuntimeError(f"{path.name}: row predicate matched {len(h)} times")
        return h[nth - 1]

    def three(r, label, sign=1):
        n = W.numeric_cells(r)
        if len(n) != 6:
            raise RuntimeError(f"{label}: {len(n)} numeric cells (need 6)")
        return [eok_cell(f"{label} [CSM col {k + 1}/3]", n[2 + k], sign, unit) for k in range(3)]

    cells = {
        1: three(row(lambda x: x.startswith("기초순장부금액")), "기초 순장부금액"),
        2: three(row(lambda x: x == "신계약효과"), "신계약효과"),
        3: three(row(lambda x: x == "순보험금융손익"), "순보험금융손익"),
        4: three(row(lambda x: x == "보험계약마진을조정하는추정치변동"), "보험계약마진을 조정하는 추정치 변동"),
        5: three(row(lambda x: x == "당기손익으로인식한보험계약마진금액"), "당기손익으로 인식한 보험계약마진 금액"),
        6: three(row(lambda x: x.endswith("말순장부금액") and not x.startswith("기초")), "기말 순장부금액"),
    }
    return finish(cells, False, f"{M.rel(path)} table@L{t['start']} unit {unit}")


# ====================================================================================================== 롯데손해보험 (KR0003)
