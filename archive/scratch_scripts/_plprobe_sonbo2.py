# -*- coding: utf-8 -*-
"""Sonbo2 PL Tier-2 handlers + self-checks for DB / NH / 롯데 / 코리안리.

COPY of _diag_pl_notes.py — safe to edit (do NOT touch the original or
build_pl_breakdown.py). Read-only against the DART filings.

Four distinct note structures were found at 2025.4Q:

  Format-DB (KR0011): 연결 발행 보험손익 note, very wide multi-row header
    원수/수재 × 비생명/생명 × 장기/일반/자동차 (≈24 cols). Detail rows for the
    GMM lines (CSM/RA/예상*) populate only 원수·비생명·장기 in the FIRST numeric
    cell. 예상/실제 are SPLIT (보험금+유지비+손해조사비+투자관리비) -> SUM.
    LOB net (13/14) read from the clean 6-col SUMMARY tables (보험수익/보험비용/
    재보험수익/재보험비용), folding 수재 into 일반/자동차.

  Format-NH (KR0032): a single '보험영업이익의 내역' table, NO LOB split, two
    columns [당기,전기]. Row labels: 보험계약마진 상각 / 위험조정 변동 /
    예상 보험금 및 기타서비스비용 / (재보험) 보험계약마진 상각 / 위험조정 변동.
    13/14 N/A (no 자동차/일반 split). item6/11 NOT cleanly isolable (cost side
    mixes GMM+PAA, no 측정치 split) -> reported None.

  Format-롯데 (KR0003): two clean single tables '30. 보험손익' and '31. 재보험손익'
    with columns [장기,일반,자동차,합계]. GMM decomposition only on 장기.
    Labels: 보험계약마진 상각 / 위험조정 변동 / 예상보험금 및 예상기타보험서비스비용 /
    발생보험금 및 기타서비스비용. 13/14 = 총 보험수익 - 총 보험비용 + 총 재보험수익
    - 총 재보험비용 per LOB. item16 (기타사업비용=38,023) lives in a note, not the
    compact income statement.

  Format-코리안리 (KR1000, reinsurer): 발행 보험손익 note, columns
    [장기보험,생명보험,일반보험] (NO 자동차; 생명보험 is a distinct GMM column).
    All 'issued' business is inward reinsurance (수재). GMM decomposition on
    장기보험 & 생명보험; 일반보험 is PAA. self-check on TRUE 별도 IS (보험수익=
    4,878,323), NOT the overseas-folded statement. Same 원수보험사 schema item
    4/5/6 maps to the 장기보험 (수재 GMM) column.

Usage:
  python scripts/_plprobe_sonbo2.py KR0011 2025.4Q --solve
  python scripts/_plprobe_sonbo2.py all 2025.4Q --solve
  python scripts/_plprobe_sonbo2.py KR0011 2025.4Q          # candidate notes
  python scripts/_plprobe_sonbo2.py KR0011 2025.4Q --raw    # raw cells w/ index
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.build_net_income_breakdown import to_num  # noqa: E402
from scripts.build_pl_breakdown import (  # noqa: E402
    extract_tier1, _is_income_statement, _is_consolidated, _pick_line,
    _income_unit_factor,
)


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


def _rownums(r):
    out = []
    for c in r:
        v = to_num(c)
        if v is not None:
            out.append(v)
    return out


def _load(code, q):
    y, qq = re.match(r"(\d{4})\.(\d)Q", q).groups()
    dirs = glob.glob(f"data/dart/FY{y}_Q{qq}/raw/{code}_*")
    tables = []
    for d in dirs:
        xs = (glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml")
              + glob.glob(d + "/extracted*/*.xml"))
        for x in sorted(set(xs), key=os.path.getsize, reverse=True):
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception:
                pass
    return tables


def _fl(t):
    return _norm(t.rows[0][0]) if t.rows else ""


def _firstlab(t, *needles, exclude=()):
    """First numeric cell of the first row whose col0/col1 label contains a needle."""
    for r in t.rows:
        lab = (_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles) \
                and not any(e.replace(" ", "") in lab for e in exclude):
            ns = _rownums(r)
            if ns:
                return ns[0]
    return None


def _sum_split(t, needle_groups):
    tot = 0.0
    found = False
    for nd in needle_groups:
        v = _firstlab(t, nd)
        if v is not None:
            tot += v
            found = True
    return tot if found else None


# --------------------------------------------------------------------------- #
# row-label variant sets (superset across the four companies)
# --------------------------------------------------------------------------- #
CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "보험계약마진 상각",
       "제공된 서비스의 보험계약마진")
RA = ("비금융위험에 대한 위험조정의 변동분", "위험조정 변동",
      "위험해제로 인한 비금융위험에 대한 위험조정의 변동")
# expected-claim measurement components (some companies split into 4 sub-rows)
EXP_SPLIT = ("예상 보험금 (기초 예상 측정치)", "예상 유지비 (기초 예상 측정치)",
             "예상 손해조사비 (기초 예상 측정치)", "예상 투자관리비 (기초 예상 측정치)")
EXP_SINGLE = ("보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
              "예상보험금 및 예상기타보험서비스비용",
              "예상 보험금 및 기타서비스비용")
# actual incurred (some companies split into 4)
ACT_SPLIT = ("발생한 보험금", "발생한 유지비", "발생한 손해조사비", "발생한 투자관리비")
ACT_SINGLE = ("발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생보험금 및 기타서비스비용")
RE_EXP_COST = ("재보험비용, 예상 보험금 (기초 예상 측정치)",
               "재보험비용, 예상 기타 보험서비스비용 (기초 예상 측정치)",
               "보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
               "회수예상 보험금 및 기타보험서비스비용")
RE_REV_ACT = ("재보험수익, 발생한 보험금", "발생보험금 및 기타재보험수익",
              "발생재보험비용")


def _basis_match_is(tables, code, target_rev=None):
    """Return (item1, item16, basis) using the income statement whose 보험수익
    matches `target_rev` (note grand total) when given; else tier1's pick."""
    cands = [t for t in tables if _is_income_statement(t)]
    best = None
    for t in cands:
        ni = _pick_line(t, "당기순이익(손실)", "당기순이익", "계속영업당기순이익")
        if ni is None:
            continue
        f = _income_unit_factor(ni)
        rev = _pick_line(t, "보험수익")
        ins = _pick_line(t, "보험손익", "보험서비스결과")
        oexp = _pick_line(t, "기타사업비용")
        if rev is None or ins is None:
            continue
        revm = rev * f
        score = 0
        if target_rev is not None and abs(revm - target_rev) <= max(2000, 0.002 * abs(target_rev)):
            score = 100  # exact basis match to the note
        rec = (score, abs(ni * f))
        cand = (ins * f, (oexp * f) if oexp is not None else None, revm)
        if best is None or rec > best[0]:
            best = (rec, cand)
    return best[1] if best else (None, None, None)


# --------------------------------------------------------------------------- #
# Format-DB (KR0011)
# --------------------------------------------------------------------------- #
def solve_db(tables):
    def find(pred):
        for t in tables:
            if "연결회사" in (t.caption or "") and pred(t):
                return t
        return None

    def has(t, kw):
        return kw in " ".join(_norm(r[0]) for r in t.rows)

    rev_t = find(lambda t: _fl(t).startswith("보험수익, 예상 보험금")
                 and has(t, "서비스의 이전으로 당기손익에 인식한 보험계약마진"))
    cost_t = find(lambda t: _fl(t).startswith("보험서비스비용, 발생한 보험금")
                  and has(t, "보험비용"))
    recost_t = find(lambda t: _fl(t).startswith("재보험비용, 예상 보험금")
                    and has(t, "서비스의 이전으로 당기손익에 인식한 보험계약마진"))
    rerev_t = find(lambda t: _fl(t).startswith("재보험수익, 발생한 보험금")
                   and has(t, "재보험자에게서 회수한 금액에서 생기는 수익"))
    # clean LOB summary tables (총/합계 rows; 6-col rev, 원수/수재 cost)
    sum_rev = find(lambda t: _fl(t) == "보험수익" and len(_rownums(t.rows[-1])) >= 6)
    sum_cost = find(lambda t: _fl(t).startswith("보험서비스비용")
                    and _norm(t.rows[-1][0]) == "보험비용")
    sum_rerev = find(lambda t: _norm(t.rows[-1][0]) == "재보험자에게서 회수한 금액에서 생기는 수익")
    sum_recost = find(lambda t: _norm(t.rows[-1][0]) == "재보험자에게 지급된 보험료 배분액에서 생기는 비용")

    out = {}
    out[4] = abs(_firstlab(rev_t, *CSM))
    out[5] = abs(_firstlab(rev_t, *RA))
    out[6] = _sum_split(rev_t, EXP_SPLIT) - _sum_split(cost_t, ACT_SPLIT)
    out[9] = -abs(_firstlab(recost_t, *CSM))
    out[10] = -abs(_firstlab(recost_t, *RA))
    re_rev_act = _firstlab(rerev_t, "재보험수익, 발생한 보험금")
    re_cost_exp = _sum_split(recost_t, RE_EXP_COST)
    out[11] = abs(re_rev_act) - abs(re_cost_exp)

    # LOB nets. The four summary total rows have DISTINCT layouts (the 보험수익 row
    # folds 수재 into the LOB columns; the cost/recost rows split 원수/수재):
    #   rev    : [장기, 일반, 자동차, 비생명합, 생명, 총]                 (생명=idx4)
    #   cost   : [장기, 일반, 자동차, 생명, 원수소계, 수재장기, 수재일반, 수재자동차, …] (생명=idx3)
    #   rerev  : [장기, 일반, 자동차, 생명, 총]                          (생명=idx3)
    #   recost : [장기, 일반, 자동차, 생명, 원수소계, 수재장기, 수재일반, 수재자동차, …] (생명=idx3)
    # In all four, 일반=idx1, 자동차=idx2.  DB books inward-reinsurance (수재) under
    # 일반/자동차; fold it in for income-statement-consistent LOB nets.
    rev = _rownums(sum_rev.rows[-1])
    cost = _rownums(sum_cost.rows[-1])
    rerev = _rownums(sum_rerev.rows[-1])
    recost = _rownums(sum_recost.rows[-1])

    def suje(arr, lob_idx):
        # 수재 일반/자동차 sit at idx 6/7 in the 원수/수재-split cost/recost rows.
        i = 5 + lob_idx  # 일반→6, 자동차→7
        return arr[i] if len(arr) > i else 0.0
    out[14] = (rev[1] - (cost[1] + suje(cost, 1)) + rerev[1] - (recost[1] + suje(recost, 1)))
    out[13] = (rev[2] - (cost[2] + suje(cost, 2)) + rerev[2] - (recost[2] + suje(recost, 2)))
    # 장기 block = 장기 + 생명 (원수 GMM; 수재장기 = 0 for DB). 생명 col index differs:
    # idx4 in the folded rev row, idx3 in the others.
    out["_jang_rev"] = rev[0] + rev[4]
    out["_jang_cost"] = cost[0] + cost[3]
    out["_jang_rerev"] = rerev[0] + rerev[3]
    out["_jang_recost"] = recost[0] + recost[3]
    return out


# --------------------------------------------------------------------------- #
# Format-롯데 (KR0003)
# --------------------------------------------------------------------------- #
def solve_lotte(tables):
    def find(capkw, lobkw):
        for t in tables:
            if capkw in (t.caption or "") and "<제81(당)기>" in (t.caption or ""):
                h = " ".join(" ".join(_norm(c) for c in hr) for hr in t.header)
                if all(k in h for k in lobkw):
                    return t
        return None
    ins_t = find("30. 보험손익", ("장기", "일반", "자동차"))
    rein_t = find("31. 재보험손익", ("장기", "일반", "자동차"))

    def row(t, *needles, exclude=()):
        for r in t.rows:
            lab = (_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles) \
                    and not any(e.replace(" ", "") in lab for e in exclude):
                ns = _rownums(r)
                if ns:
                    return ns
        return None

    def lob(ns):
        # rows in 롯데 tables read [장기, 일반, 자동차, 합계] but PAA-only rows collapse
        # to fewer cells; for the 총 rows the first 3 are 장기/일반/자동차.
        return ns

    out = {}
    out[4] = abs(row(ins_t, "보험계약마진 상각")[0])
    out[5] = abs(row(ins_t, "위험조정 변동")[0])
    exp = row(ins_t, "예상보험금 및 예상기타보험서비스비용")[0]
    act = row(ins_t, "발생보험금 및 기타서비스비용")[0]
    out[6] = exp - act
    out[9] = -abs(row(rein_t, "보험계약마진 상각")[0])
    out[10] = -abs(row(rein_t, "위험조정 변동")[0])
    re_rev_act = row(rein_t, "발생보험금 및 기타재보험수익")[0]
    re_cost_exp = row(rein_t, "회수예상 보험금 및 기타보험서비스비용")[0]
    out[11] = abs(re_rev_act) - abs(re_cost_exp)

    rev_tot = lob(row(ins_t, "총 보험수익"))
    cost_tot = lob(row(ins_t, "총 보험비용"))
    rerev_tot = lob(row(rein_t, "총 재보험수익"))
    recost_tot = lob(row(rein_t, "총 재보험비용"))

    def net(i):
        return (rev_tot[i] - cost_tot[i] + rerev_tot[i] - recost_tot[i])
    out[14] = net(1)   # 일반
    out[13] = net(2)   # 자동차
    out["_jang_rev"] = rev_tot[0]
    out["_jang_cost"] = cost_tot[0]
    out["_jang_rerev"] = rerev_tot[0]
    out["_jang_recost"] = recost_tot[0]
    return out


# --------------------------------------------------------------------------- #
# Format-NH (KR0032) — single table, no LOB
# --------------------------------------------------------------------------- #
def solve_nh(tables):
    note = None
    for t in tables:
        labs = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
        if ("보험영업이익" in (t.caption or "")) and "보험계약마진 상각" in labs \
                and "보험료배분접근법 보험수익" in labs:
            note = t
            break
    if note is None:
        return {}
    # section-aware: rows appear in order 보험수익 / 보험서비스비용 / 재보험수익 / 재보험비용
    section = None
    vals = {}
    for r in note.rows:
        lab0 = _norm(r[0])
        lab1 = _norm(r[1]) if len(r) > 1 else ""
        if lab0 in ("보험수익", "보험서비스비용", "재보험수익", "재보험비용"):
            section = lab0
        lab = (lab0 + " " + lab1).replace(" ", "")
        ns = _rownums(r)
        if not ns:
            continue
        v = ns[0]
        if section == "보험수익":
            if "보험계약마진상각" in lab:
                vals["csm"] = v
            elif "위험조정변동" in lab:
                vals["ra"] = v
        elif section == "재보험비용":
            if "보험계약마진상각" in lab:
                vals["recsm"] = v
            elif "위험조정변동" in lab:
                vals["rera"] = v
    out = {}
    if "csm" in vals:
        out[4] = abs(vals["csm"])
    if "ra" in vals:
        out[5] = abs(vals["ra"])
    if "recsm" in vals:
        out[9] = -abs(vals["recsm"])
    if "rera" in vals:
        out[10] = -abs(vals["rera"])
    # item6/11 not cleanly isolable (cost side mixes GMM+PAA, no measurement split)
    # 13/14 N/A (no LOB split). 장기 totals = the note 소계 lines (single column).
    def subtotal(after_section):
        sec = None
        for r in note.rows:
            l0 = _norm(r[0])
            if l0 in ("보험수익", "보험서비스비용", "재보험수익", "재보험비용"):
                sec = l0
            if l0 == "소계" and sec == after_section:
                ns = _rownums(r)
                return ns[0] if ns else None
        return None
    out["_jang_rev"] = subtotal("보험수익")
    out["_jang_cost"] = subtotal("보험서비스비용")
    out["_jang_rerev"] = subtotal("재보험수익")
    # 재보험비용 has no 소계 row; sum its component rows
    return out


# --------------------------------------------------------------------------- #
# Format-코리안리 (KR1000, reinsurer)
# --------------------------------------------------------------------------- #
def solve_koreanre(tables):
    """코리안리 (reinsurer). The note set appears TWICE in document order:
    a 연결 (overseas-subsidiary-folded) group first, then the 별도 (standalone)
    group. Within each group every detail table is duplicated 당기→전기. We want
    the standalone-당기 of each type. Strategy: collect, per fl-type, the list of
    matching detail tables in document order; the standalone group is the SECOND
    half (later half); take its first element (=당기)."""
    def labs(t):
        return " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)

    def collect(fl_start, must_all):
        hits = [t for t in tables
                if _fl(t).startswith(fl_start) and all(m in labs(t) for m in must_all)]
        return hits

    rev_all = collect("보험수익", ["서비스의 이전으로 당기손익에 인식한 보험계약마진",
                                  "예상 손해조사비 (기초 예상 측정치)"])
    cost_all = collect("보험비용", ["발생한 보험금", "발생한 손해조사비"])
    rerev_all = collect("재보험자에게서 회수한 금액에서 생기는 수익", ["재보험수익, 발생한 보험금"])
    recost_all = collect("재보험자에게 지급된 보험료 배분액에서 생기는 비용",
                         ["서비스의 이전으로 당기손익에 인식한 보험계약마진"])
    if not (rev_all and cost_all and rerev_all and recost_all):
        return {}, None

    def standalone_current(lst):
        # 4 tables: [연결당기, 연결전기, 별도당기, 별도전기]; standalone-당기 = index 2,
        # fallback to second-half first element / last resort first element.
        if len(lst) >= 4:
            return lst[len(lst) // 2]
        return lst[-1] if len(lst) >= 2 else lst[0]

    rev_t = standalone_current(rev_all)
    cost_t = standalone_current(cost_all)
    rerev_t = standalone_current(rerev_all)
    recost_t = standalone_current(recost_all)

    def grand(t):
        # first total row layout: [GMM장기, GMM생명, GMM일반(0), GMM소계, _, _, PAA일반, PAA(dup)]
        # true grand = GMM소계 (idx 3) + PAA (idx 6).  GMM일반 is always 0 for a reinsurer.
        ns = _rownums(t.rows[0])
        if len(ns) >= 7:
            return ns[3] + ns[6]
        return ns[-1] if ns else 0
    note_rev_grand = grand(rev_t)

    out = {}
    out[4] = abs(_firstlab(rev_t, *CSM))
    out[5] = abs(_firstlab(rev_t, *RA))
    out[6] = _sum_split(rev_t, EXP_SPLIT) - _sum_split(cost_t, ACT_SPLIT)
    out[9] = -abs(_firstlab(recost_t, *CSM))
    out[10] = -abs(_firstlab(recost_t, *RA))
    re_rev_act = _firstlab(rerev_t, "재보험수익, 발생한 보험금")
    re_cost_exp = _firstlab(recost_t, "재보험비용, 예상 보험금")
    if re_cost_exp is None:
        re_cost_exp = _firstlab(recost_t, "보고기간에 발생한 보험서비스비용 (기초 예상 측정치)")
    out[11] = abs(re_rev_act) - abs(re_cost_exp or 0)
    # reinsurer: no 자동차/일반 GMM LOB; 13/14 N/A. 장기 block = the whole
    # standalone underwriting (장기보험+생명보험+일반PAA), i.e. the grand totals.
    out["_jang_rev"] = grand(rev_t)
    out["_jang_cost"] = grand(cost_t)
    out["_jang_rerev"] = grand(rerev_t)
    out["_jang_recost"] = grand(recost_t)
    return out, note_rev_grand


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #
def selfcheck_lob(code, tables, t2, note_rev_grand=None, manual_item16=None):
    """Reconstruct item1 from LOB nets and compare to the income statement."""
    item1, item16, _ = _basis_match_is(tables, code, target_rev=note_rev_grand)
    if manual_item16 is not None:
        item16 = manual_item16
    item15 = 0.0
    jang = (t2.get("_jang_rev", 0) - t2.get("_jang_cost", 0)
            + t2.get("_jang_rerev", 0) - t2.get("_jang_recost", 0))
    recon = jang + (t2.get(13) or 0) + (t2.get(14) or 0) + item15 - (item16 or 0)
    gap = recon - item1 if item1 is not None else None
    pct = (100 * gap / abs(item1)) if (item1 and gap is not None) else None
    return item1, item16, recon, gap, pct


def main():
    arg = sys.argv[1]
    q = sys.argv[2]
    codes = ["KR0011", "KR0032", "KR0003", "KR1000"] if arg == "all" else [arg]
    if "--solve" not in sys.argv:
        # fall back to the old candidate-note dump
        for code in codes:
            tables = _load(code, q)
            print(f"=== {code} {q}: {len(tables)} tables (use --solve) ===")
        return
    for code in codes:
        tables = _load(code, q)
        print(f"\n########## {code} {q} ({len(tables)} tables) ##########")
        note_rev_grand = None
        manual16 = None
        try:
            if code == "KR0011":
                t2 = solve_db(tables)
            elif code == "KR0003":
                t2 = solve_lotte(tables)
                manual16 = 38023.0  # 기타사업비용 from the note (compact IS omits it)
            elif code == "KR0032":
                t2 = solve_nh(tables)
            elif code == "KR1000":
                t2, note_rev_grand = solve_koreanre(tables)
            else:
                print("  no handler"); continue
        except Exception as e:
            print(f"  HANDLER ERROR ({type(e).__name__}: {e}) -> note structure "
                  f"differs this quarter (full annual note likely absent)")
            continue

        if not t2:
            print("  NO NOTE MATCHED -> Tier-2 note absent/abbreviated this quarter")
            continue

        for k in (4, 5, 6, 9, 10, 11, 13, 14):
            v = t2.get(k)
            print(f"  item{k:<2} = {round(v, 0) if isinstance(v, float) else v}")
        if code == "KR0032":
            # NH: total-underwriting self-check (no LOB)
            item1, item16, _ = _basis_match_is(tables, code)
            rev = t2.get("_jang_rev"); cost = t2.get("_jang_cost")
            rerev = t2.get("_jang_rerev")
            if None in (item1, rev, cost, rerev):
                print("  [self-check NH] inputs missing -> cannot reconcile this quarter")
                continue
            cands = [t for t in tables if _is_income_statement(t)]
            recost = None
            for t in cands:
                f = _income_unit_factor(_pick_line(t, "당기순이익(손실)", "당기순이익") or 1)
                rc = _pick_line(t, "재보험비용", exclude=("금융",))
                if rc is not None and abs((_pick_line(t, "보험수익") or 0) * f - rev) < 5000:
                    recost = rc * f
                    break
            recon = (rev - cost + rerev - (recost or 0)) - (item16 or 0)
            gap = recon - item1
            print(f"  [self-check NH] uw-기타사업비용={round(recon,0)} item1={round(item1,0)} "
                  f"gap={round(gap,0)} pct={round(100*gap/abs(item1),3)}% "
                  f"-> {'PASS' if abs(gap) <= max(2, 0.01*abs(item1)) else 'FAIL'}")
        else:
            item1, item16, recon, gap, pct = selfcheck_lob(
                code, tables, t2, note_rev_grand, manual16)
            if item1 is None or gap is None:
                print("  [self-check] no matching income statement -> cannot reconcile")
                continue
            verdict = "PASS" if (pct is not None and abs(pct) <= 1.0) else "FAIL"
            print(f"  [self-check] item1={round(item1,0) if item1 else None} "
                  f"item16={round(item16,0) if item16 else None} "
                  f"recon={round(recon,0)} gap={round(gap,0) if gap is not None else None} "
                  f"pct={round(pct,3) if pct is not None else None}% -> {verdict}")


if __name__ == "__main__":
    main()
