# -*- coding: utf-8 -*-
"""Self-contained verification for the three 생보 component-decomposition PL notes:
KR0073 교보생명, KR0082 DB생명, KR0087 동양생명.

These three companies do NOT use the 삼성/한화 '계약유형별' LOB note.  They use a
component-decomposition note (보험수익/보험서비스비용/재보험수익/재보험비용 each broken into
예상발생 + RA변동 + CSM상각 + 보험취득현금흐름 + 손실요소 ...).  All single-column (도메스틱
합계, no 해외).

Items 3/8 (and thus the item1 reconciliation) come from the income-statement insurance
lines (보험수익/재보험수익/보험비용/재보험비용/기타사업비용), NOT from the note totals — because
for these companies 기타사업비용 sits *inside* 보험서비스비용 and must be split out as item16.

Basis: 별도 (separate).  The note totals match the 별도 income-statement insurance lines
exactly.

Read-only.  Usage: python scripts/_plprobe_life1_verify.py [2025.4Q]
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
import scripts.build_pl_breakdown as B  # noqa: E402


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


def _rownums(r):
    return [v for v in (to_num(c) for c in r) if v is not None]


def _flat(t):
    return "".join(_norm(c) for r in t.rows for c in r[:2]).replace(" ", "")


def _label_flat(r):
    return (_norm(r[0]) + _norm(r[1] if len(r) > 1 else "")).replace(" ", "")


def _is_rollforward(t):
    f = _flat(t)
    return any(k in f for k in ("기초순장부금액", "기말순장부금액", "기초보험계약", "기말보험계약",
                                "기초보유", "기말보유", "총현금흐름", "수취한보험료", "순장부금액"))


def _first_num_in_row(t, label_variants, section_first=None):
    """First numeric cell of the FIRST row whose flattened col0/col1 label contains any
    variant.  If section_first is given, only consider rows that appear after a section
    header row whose label == section_first."""
    cur_sec = None
    for r in t.rows:
        lf = _label_flat(r)
        nums = _rownums(r)
        # section header = label present, no numbers
        if not nums:
            cur_sec = lf
            continue
        if section_first is not None and cur_sec != section_first:
            # allow header+value on same row to set section
            pass
        for v in label_variants:
            if v.replace(" ", "") in lf:
                return nums[0]
    return None


# --------------------------------------------------------------------------- #
# Income-statement insurance lines (별도) — common to all three companies.
# --------------------------------------------------------------------------- #
def _is_lines(tables, code):
    """Return (rev, rerev, cost, recost, other_biz, ins_pl) in 백만원 from the 별도
    income statement, or None.  Handles 원 / 백만 unit via 보험손익 anchor."""
    B.BASIS_OVERRIDE[code] = "별도"
    isets = [t for t in tables if B._is_income_statement(t) and not B._is_consolidated(t)]
    if not isets:
        isets = [t for t in tables if B._is_income_statement(t)]
    for t in isets:
        def line(*needles, exclude=()):
            for r in t.rows:
                lab = _norm(r[0])
                if any(n in lab for n in needles) and not any(x in lab for x in exclude):
                    nums = _rownums(r)
                    if nums:
                        return nums[0]
            return None
        pl = line("보험손익")
        rev = line("보험수익", exclude=("재보험",))
        rerev = line("재보험수익")
        cost = line("보험비용", exclude=("재보험",))
        recost = line("재보험비용")
        other = line("기타사업비용")
        if None in (pl, rev, cost):
            continue
        # unit factor: 보험손익 plausible band 50 .. 5,000,000 백만
        f = 1.0
        a = abs(pl)
        if a >= 50e6:
            f = 1e-6
        elif a >= 50e3 and a < 5e6:
            f = 1.0
        elif a >= 5e6:
            f = 1e-6
        vals = [x * f if x is not None else None for x in (rev, rerev, cost, recost, other, pl)]
        return tuple(vals)
    return None


# --------------------------------------------------------------------------- #
# Per-company Tier-2 handlers (items 4,5,6,9,10,11) — see deliverable.
# --------------------------------------------------------------------------- #
def extract_tier2_kyobo(tables):
    """KR0073 교보생명. Note family '17-12) ...발행한 보험계약...보험수익',
    '17-13) ...재보험수익', '17-14) ...보험서비스비용', '17-15) ...재보험비용'.
    Use 별도 ('당사') variants. Single column (당기)."""
    def pick(cap_contains_all, must_row):
        cands = []
        for t in tables:
            cap = t.caption or ""
            if all(s in cap for s in cap_contains_all) and "당사" in cap and not _is_rollforward(t):
                if must_row.replace(" ", "") in _flat(t):
                    cands.append(t)
        return cands[0] if cands else None

    rev = pick(("발행한 보험계약", "보험수익"), "당기손익에인식한보험계약마진")
    cost = pick(("발행한 보험계약", "보험서비스비용"), "보험계약에대한보험비용")
    rerev = pick(("재보험계약", "재보험수익"), "발생재보험금")
    recost = pick(("재보험계약", "재보험비용"), "보험계약마진상각")
    out = {}
    if rev:
        out[4] = abs(_first_num_in_row(rev, ["당기손익에인식한보험계약마진"]) or 0) or None
        out[5] = abs(_first_num_in_row(rev, ["비금융위험에대한위험조정변동"]) or 0) or None
        # 예상 = (1) 발생한 보험서비스수익
        exp = _first_num_in_row(rev, ["발생한보험서비스수익"])
    if cost:
        # 실제 = 실제보험금 + 실제계약유지비용 + 실제투자관리비
        ac = _first_num_in_row(cost, ["실제보험금"])
        am = _first_num_in_row(cost, ["실제계약유지비용"])
        ai = _first_num_in_row(cost, ["실제투자관리비"])
        act = sum(x for x in (ac, am, ai) if x is not None) if ac is not None else None
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_first_num_in_row(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_first_num_in_row(recost, ["위험조정변동", "비금융위험에대한위험조정"]) or 0) or None
        re_exp = _first_num_in_row(recost, ["예상재보험금"])
    if rerev:
        re_act = _first_num_in_row(rerev, ["발생재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out


def extract_tier2_db(tables):
    """KR0082 DB생명. Notes 20.1..20.4 (별도) — caption '발행한 보험계약의 보험수익' etc.
    Single column (당기)."""
    def pick(cap_frag, must_row=None):
        for t in tables:
            cap = t.caption or ""
            if cap_frag in cap and not _is_rollforward(t):
                if must_row is None or must_row.replace(" ", "") in _flat(t):
                    return t
        return None
    # 20.x = 별도 (first occurrence in doc order = 별도, before the 21.x 연결 block)
    rev = pick("발행한 보험계약의 보험수익", "보험계약마진상각")
    cost = pick("발행한 보험계약의 보험비용", "발생보험금")
    rerev = pick("재보험계약의 재보험수익", "발생출재보험금")
    recost = pick("재보험계약의 재보험비용", "예상출재보험금")
    out = {}
    if rev:
        out[4] = abs(_first_num_in_row(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_first_num_in_row(rev, ["비금융위험에대한위험조정상각"]) or 0) or None
        exp = sum(x for x in (
            _first_num_in_row(rev, ["예상보험금"]),
            _first_num_in_row(rev, ["예상유지비"]),
            _first_num_in_row(rev, ["예상손해조사비"]),
            _first_num_in_row(rev, ["예상투자관리비"]),
        ) if x is not None)
    if cost:
        act = sum(x for x in (
            _first_num_in_row(cost, ["발생보험금"]),
            _first_num_in_row(cost, ["발생직접유지비"]),
            _first_num_in_row(cost, ["손해조사비"]),
            _first_num_in_row(cost, ["투자관리비"]),
        ) if x is not None)
        if rev:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_first_num_in_row(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_first_num_in_row(recost, ["비금융위험에대한위험조정상각"]) or 0) or None
        re_exp = _first_num_in_row(recost, ["예상출재보험금"])
    if rerev:
        re_act = _first_num_in_row(rerev, ["발생출재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out


def extract_tier2_dongyang(tables):
    """KR0087 동양생명. note 19 (발행 보험수익/비용) + note 20 (재보험).
    Compact tables: first row = section total, then components. Single column.
    Hallmark rows: '예상 발생보험금 및 기타보험서비스비용', '보험계약마진 상각',
    '비금융위험 위험조정 변동', '실제 발생보험금 및 기타보험서비스비용'."""
    def pick(first_label, must_row):
        for t in tables:
            if not t.rows or _is_rollforward(t):
                continue
            if _norm(t.rows[0][0]) != first_label:
                continue
            if must_row.replace(" ", "") in _flat(t):
                return t
        return None
    rev = pick("보험수익", "예상발생보험금및기타보험서비스비용")
    cost = pick("보험서비스비용", "실제발생보험금및기타보험서비스비용")
    rerev = pick("재보험수익", "실제재보험금및기타재보험서비스비용")
    recost = pick("재보험비용", "예상재보험금및기타재보험서비스비용")
    out = {}
    if rev:
        out[4] = abs(_first_num_in_row(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_first_num_in_row(rev, ["비금융위험위험조정변동"]) or 0) or None
        exp = _first_num_in_row(rev, ["예상발생보험금및기타보험서비스비용"])
    if cost:
        act = _first_num_in_row(cost, ["실제발생보험금및기타보험서비스비용"])
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_first_num_in_row(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_first_num_in_row(recost, ["비금융위험위험조정변동"]) or 0) or None
        re_exp = _first_num_in_row(recost, ["예상재보험금및기타재보험서비스비용"])
    if rerev:
        re_act = _first_num_in_row(rerev, ["실제재보험금및기타재보험서비스비용"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out


HANDLERS = {
    "KR0073": ("교보생명", extract_tier2_kyobo),
    "KR0082": ("DB생명", extract_tier2_db),
    "KR0087": ("동양생명", extract_tier2_dongyang),
}


def load_tables(code, q):
    y, qq = re.match(r"(\d{4})\.(\d)Q", q).groups()
    dirs = glob.glob(f"data/dart/FY{y}_Q{qq}/raw/{code}_*")
    tables = []
    for d in dirs:
        for x in sorted(set(glob.glob(d + "/xml/*.xml") + glob.glob(d + "/*.xml")),
                        key=os.path.getsize, reverse=True):
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception:
                pass
    return tables


def run(code, q):
    name, handler = HANDLERS[code]
    tables = load_tables(code, q)
    if not tables:
        print(f"{code} {name} {q}: NO TABLES")
        return
    isl = _is_lines(tables, code)
    t2 = handler(tables)
    t1 = B.extract_tier1(tables, code=code)
    print(f"\n=== {code} {name} {q} ===")
    print("  Tier-2 items:", {k: round(t2[k], 1) for k in sorted(t2)})
    if isl is None:
        print("  NO income-statement insurance lines -> cannot reconcile")
        return
    rev, rerev, cost, recost, other, ins_pl = isl
    item3 = rev - cost
    item8 = (rerev or 0) - (recost or 0)
    item2 = item3 + item8
    item16 = other if other is not None else 0.0
    item15 = 0.0
    recon = item2 + item15 - item16
    item1 = t1[1] if t1 and t1.get(1) is not None else ins_pl
    gap = abs(recon - item1) / abs(item1) * 100 if item1 else 999
    print(f"  IS(별도 백만): rev={rev:.0f} rerev={(rerev or 0):.0f} cost={cost:.0f} "
          f"recost={(recost or 0):.0f} 기타사업비용={item16:.0f}")
    print(f"  item3={item3:.0f} item8={item8:.0f} item2={item2:.0f}")
    print(f"  SELF-CHECK: recon(item2+15-16)={recon:.1f}  item1(IS 보험손익)={item1:.1f}  "
          f"gap={gap:.4f}%  {'PASS' if gap < 1 else 'FAIL'}")
    if all(t2.get(i) is not None for i in (4, 5, 6)):
        i7 = item3 - (t2[4] + t2[5] + t2[6])
        print(f"  item7(residual 기타 원수손익)={i7:.0f}")
    if all(t2.get(i) is not None for i in (9, 10, 11)):
        i12 = item8 - (t2[9] + t2[10] + t2[11])
        print(f"  item12(residual 기타 재보험손익)={i12:.0f}")


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "2025.4Q"
    for code in ("KR0073", "KR0082", "KR0087"):
        run(code, q)


if __name__ == "__main__":
    main()
