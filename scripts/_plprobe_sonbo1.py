# -*- coding: utf-8 -*-
"""SELF-CHECK harness for KB/현대/한화 손보 Tier-2. Read-only on data.
Implements candidate handlers extract_tier2_kb / _hyundai / _hanwha and runs the
reconstruction self-check against the own-company 보험손익.
Usage: python scripts/_plprobe_sonbo1.py
"""
import glob
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
import scripts.build_pl_breakdown as B  # noqa: E402

N = B._norm


def load(code):
    dirs = glob.glob(f"data/dart/FY2025_Q4/raw/{code}_*")
    tables = []
    for d in dirs:
        xs = (glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml")
              + glob.glob(d + "/extracted*/*.xml"))
        for x in sorted(set(xs), key=os.path.getsize, reverse=True):
            try:
                tables.extend(B._iter_tables_with_context(Path(x)))
            except Exception:
                pass
    return tables


def _lab0(r):
    return N(r[0]).replace(" ", "")


def _row_by_label(t, *subs, exact=False):
    """First row whose col0 label (spaces stripped) matches any sub."""
    for r in t.rows:
        lab = _lab0(r)
        for s in subs:
            s2 = s.replace(" ", "")
            if (lab == s2) if exact else (s2 in lab):
                return r
    return None


# ============================ KB (KR0010) ============================
def _kb_note(tables):
    """KB combined note. caption has 보험손익+상세내역, header 장기/일반/자동차.
    CURRENT-연결: the table whose '총 보험서비스결과' 합계 == income-statement 보험손익.
    Robust pick: among 당기 (<당기> in caption) tables, take the one whose 총 보험수익
    장기 value is the larger (current period block). We confirm via the 총 보험서비스결과
    합계 reconciliation downstream."""
    cands = []
    for t in tables:
        cap = t.caption or ""
        if "보험손익" not in cap or "상세내역" not in cap:
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not all(k in hb for k in ("장기", "일반", "자동차")):
            continue
        if "<당기>" not in cap:
            continue
        result = _row_by_label(t, "총 보험서비스결과")
        if result is None:
            continue
        cands.append(t)
    if not cands:
        return None
    # current period = the block with the larger 장기 총보험수익
    def jang_rev(t):
        r = _row_by_label(t, "총 보험수익")
        n = B._row_nums(r) if r else []
        return n[0] if n else 0
    cands.sort(key=jang_rev, reverse=True)
    return cands[0]


def extract_tier2_kb(tables):
    t = _kb_note(tables)
    if t is None:
        return {}
    out = {}
    # 장기 column = numeric index 0 in every row (GMM sub-rows: [장기, 합계_dup];
    # 총 rows: [장기, 일반, 자동차, 해외, 합계]).
    def jang(r):
        if r is None:
            return None
        n = B._row_nums(r)
        return n[0] if n else None
    # --- 보험수익 section ---
    csm = jang(_row_by_label(t, "제공된 서비스의 보험계약마진", "보험계약마진 상각"))
    ra = jang(_row_by_label(t, "위험해제로 인한 위험조정의 변동"))  # first occ = 보험수익 section
    rev_exp = jang(_row_by_label(t, "예상 보험금 및 보험서비스비용"))
    # --- 보험서비스비용 section: 실제발생 = 보험금 및 보험서비스비용 (NOT '예상...') ---
    cost_act = None
    for r in t.rows:
        lab = _lab0(r)
        if lab == "보험금및보험서비스비용":   # exact: excludes '예상 보험금 및...' and '회수가능...'
            n = B._row_nums(r)
            cost_act = n[0] if n else None
            break
    # --- 재보험비용 section ---
    re_csm = jang(_row_by_label(t, "제공받은 서비스의 재보험계약마진"))
    re_cost_exp = jang(_row_by_label(t, "회수예상 보험금 및 보험서비스비용"))
    # 재보험비용 section RA: second 위험해제로... row
    re_ra = None
    seen_ra = 0
    for r in t.rows:
        if "위험해제로인한위험조정의변동" in _lab0(r):
            seen_ra += 1
            if seen_ra == 2:
                n = B._row_nums(r)
                re_ra = n[0] if n else None
    # --- 재보험수익 section: 실제발생 = 회수가능 보험금 및 보험서비스비용 ---
    re_rev = jang(_row_by_label(t, "회수가능 보험금 및 보험서비스비용"))

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    # 장기-column totals
    tr = B._row_nums(_row_by_label(t, "총 보험수익"))
    tc = B._row_nums(_row_by_label(t, "총 보험서비스비용"))
    trr = B._row_nums(_row_by_label(t, "총 재보험수익"))
    trc = B._row_nums(_row_by_label(t, "총 재보험비용"))
    out["_jang_rev"] = tr[0] if tr else None
    out["_jang_cost"] = abs(tc[0]) if tc else None
    out["_jang_rerev"] = trr[0] if trr else None
    out["_jang_recost"] = abs(trc[0]) if trc else None

    # 13/14 from 총 보험서비스결과: cols [장기, 일반, 자동차, 해외, 합계].
    res = B._row_nums(_row_by_label(t, "총 보험서비스결과"))
    if res and len(res) >= 5:
        out["_result_row"] = res
        out["_jang_net"] = res[0]              # 장기 손익 (incl 재보험), col0
        out[13] = res[2]                       # 자동차
        out[14] = res[1] + res[3]              # 일반 + 해외지점 (fold overseas into 일반)
    return out


# ============================ 현대 (KR0009) ============================
def _hyundai_section(tables, first_label_starts):
    """현대 note sections are separate tables (caption '2) 손익 현황' or 관계기업).
    Pick the table whose first row label starts with first_label_starts and which is the
    CURRENT period (largest |장기 value|). Each section appears 4x (2 captions x 2 periods);
    current period has the larger magnitude."""
    cands = []
    for t in tables:
        if not t.rows:
            continue
        if _lab0(t.rows[0]).startswith(first_label_starts.replace(" ", "")):
            cands.append(t)
    if not cands:
        return None
    def mag(t):
        n = B._row_nums(t.rows[0])
        return abs(n[0]) if n else 0
    cands.sort(key=mag, reverse=True)
    return cands[0]


def _hyundai_lob_summary(tables):
    """현대 own-company 보험종목별 수지: caption mentions 보험종목별 수지, header 일반/장기/자동차/합계."""
    for t in tables:
        cap = t.caption or ""
        if "보험종목별" in cap and "수지" in cap:
            hb = " ".join(" ".join(h) for h in t.header)
            if "장기" in hb and "자동차" in hb and "일반" in hb:
                r = _row_by_label(t, "보험손익")
                if r:
                    return t, r
    return None, None


def extract_tier2_hyundai(tables):
    out = {}
    rev_t = _hyundai_section(tables, "보험수익,")
    cost_t = _hyundai_section(tables, "보험서비스비용,")
    rerev_t = _hyundai_section(tables, "재보험수익,")
    recost_t = _hyundai_section(tables, "재보험비용,")

    def jang(t, *subs):
        if t is None:
            return None
        r = _row_by_label(t, *subs)
        if r is None:
            return None
        n = B._row_nums(r)
        return n[0] if n else None

    csm = jang(rev_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = jang(rev_t, "비금융위험에 대한 위험조정의 변동분")
    rev_exp = jang(rev_t, "보고기간에 발생한 보험서비스비용")
    cost_act = jang(cost_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_csm = jang(recost_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = jang(recost_t, "비금융위험에 대한 위험조정의 변동분")
    re_rev = jang(rerev_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_cost_exp = jang(recost_t, "보고기간에 발생한 보험서비스비용")

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    # 13/14 + 장기총손익 from the LOB summary table (백만원!)
    _, sumrow = _hyundai_lob_summary(tables)
    if sumrow is not None:
        # header 일반|장기|자동차|합계 -> nums [일반, 장기, 자동차, 합계]
        n = B._row_nums(sumrow)
        if len(n) >= 4:
            out["_lob_ilban"] = n[0]
            out["_lob_jang"] = n[1]
            out["_lob_auto"] = n[2]
            out["_lob_total"] = n[3]
            out[13] = n[2]      # 자동차
            out[14] = n[0]      # 일반
            # 장기총손익 expressed as a single net (no rev/cost split available cleanly):
            out["_jang_net"] = n[1]
    return out


# ============================ 한화 (KR0002) ============================
def _hanwha_section(tables, first_label_starts):
    """한화 correct note = caption '관계기업의 재무정보금액'. Sections by first row label.
    Current period = table whose 장기 (idx0) first-row magnitude is largest (appears 2x:
    관계기업 caption + 손상차손 caption; 관계기업 reconciles to 별도 income statement)."""
    cands = []
    for t in tables:
        cap = t.caption or ""
        if "관계기업의 재무정보금액" not in cap or not t.rows:
            continue
        if _lab0(t.rows[0]).startswith(first_label_starts.replace(" ", "")):
            cands.append(t)
    if not cands:
        return None
    return cands[0]  # 관계기업 caption, first occurrence = 당기


def extract_tier2_hanwha(tables):
    out = {}
    rev_t = _hanwha_section(tables, "보험수익,")
    cost_t = _hanwha_section(tables, "보험서비스비용,")
    rerev_t = _hanwha_section(tables, "재보험수익,")
    recost_t = _hanwha_section(tables, "재보험비용,")

    def jang(t, *subs):
        if t is None:
            return None
        r = _row_by_label(t, *subs)
        if r is None:
            return None
        n = B._row_nums(r)
        return n[0] if n else None

    def jang_sum(t, subs):
        s = 0.0
        any_ = False
        for sub in subs:
            v = jang(t, sub)
            if v is not None:
                s += v
                any_ = True
        return s if any_ else None

    EXP = ("예상 보험금 (기초", "예상 손해조사비 (기초", "예상 유지비 (기초", "예상 투자관리비 (기초")
    ACT = ("발생한 보험금", "발생한 손해조사비", "발생한 유지비", "발생한 투자관리비")
    csm = jang(rev_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = jang(rev_t, "비금융위험에 대한 위험조정의 변동분")
    rev_exp = jang_sum(rev_t, EXP)
    cost_act = jang_sum(cost_t, ACT)
    re_csm = jang(recost_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = jang(recost_t, "비금융위험에 대한 위험조정의 변동분")
    # 재보험수익 실제발생 = 발생한 보험금 + 발생한 손해조사비 (장기 col0)
    re_rev = jang_sum(rerev_t, ("발생한 보험금", "발생한 손해조사비"))
    # 재보험비용 예상 = 예상 보험금 + 예상 손해조사비
    re_cost_exp = jang_sum(recost_t, ("예상 보험금 (기초", "예상 손해조사비 (기초"))

    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev is not None and re_cost_exp is not None:
        out[11] = abs(re_rev) - abs(re_cost_exp)

    # 장기 totals: 보험수익 total row '보험수익' (idx0); cost total '발행한 보험계약에서 생기는 보험서비스비용'.
    rev_tot = jang(rev_t, "보험수익") if rev_t else None  # exact-ish: last row label '보험수익'
    # use the row whose label == '보험수익' (no comma)
    rev_tot_row = None
    for r in (rev_t.rows if rev_t else []):
        if _lab0(r) == "보험수익":
            rev_tot_row = r
    cost_tot_row = _row_by_label(cost_t, "발행한 보험계약에서 생기는 보험서비스비용") if cost_t else None
    out["_jang_rev"] = (B._row_nums(rev_tot_row)[0] if rev_tot_row and B._row_nums(rev_tot_row) else None)
    out["_jang_cost"] = (abs(B._row_nums(cost_tot_row)[0]) if cost_tot_row and B._row_nums(cost_tot_row) else None)

    # 13/14 (자동차/일반): per-LOB total = issued손익 + 재보험손익.
    # issued: 보험수익 total row & cost total row, cols [장기, 일반, 자동차, 합계].
    rev_tot = B._row_nums(rev_tot_row) if rev_tot_row else []
    cost_tot = B._row_nums(cost_tot_row) if cost_tot_row else []
    # 재보험 per-LOB: sum each section's columns. GMM block cols [장기,0,0,합계];
    # PAA block (rows with >=8 nums) cols [GMM장기,_,_,_, PAA장기, PAA일반, PAA자동차, PAA합계].
    def re_lob_sums(t):
        j = i = a = 0.0
        if t is None:
            return j, i, a
        for r in t.rows:
            nums = B._row_nums(r)
            if len(nums) >= 8:
                j += nums[0] + nums[4]
                i += nums[5]
                a += nums[6]
            elif len(nums) == 4:
                j += nums[0]
                i += nums[1]
                a += nums[2]
            elif nums:
                j += nums[0]
        return j, i, a
    rrj, rri, rra = re_lob_sums(rerev_t)
    rcj, rci, rca = re_lob_sums(recost_t)
    if len(rev_tot) >= 4 and len(cost_tot) >= 4:
        # all 천원 here; scaling to 백만 happens in main()
        jang_net = rev_tot[0] - abs(cost_tot[0]) + rrj - rcj
        ilban = rev_tot[1] - abs(cost_tot[1]) + rri - rci
        auto = rev_tot[2] - abs(cost_tot[2]) + rra - rca
        out["_jang_net"] = jang_net
        out[14] = ilban
        out[13] = auto
    return out


# ============================ self-check driver ============================
def selfcheck(code, name, t2, item1_own, item15, item16):
    print(f"\n############ {name} ({code}) ############")
    for k in (4, 5, 6, 9, 10, 11, 13, 14):
        print(f"  item{k} = {t2.get(k)}")
    jang = t2.get("_jang_net")
    print(f"  장기총손익(_jang_net) = {jang}")
    if jang is None or t2.get(13) is None or t2.get(14) is None:
        print("  SELF-CHECK: insufficient data")
        return
    rhs = jang + t2[13] + t2[14] + (item15 or 0) - (item16 or 0)
    gap = (rhs - item1_own) / item1_own * 100 if item1_own else 999
    print(f"  reconstructed item1 = {rhs:.0f}  vs  item1(own) = {item1_own:.0f}  "
          f"gap={gap:.3f}%  {'PASS' if abs(gap) <= 1 else 'FAIL'}")


def main():
    # KB: 연결 보험손익 = 686,332 백만 (note already 백만원). KB's 보험손익 line EXCLUDES
    # 기타사업비용 (the note's 총 보험서비스결과 합계 == 보험손익) -> item16=0 in the identity.
    kb = load("KR0010")
    t2 = extract_tier2_kb(kb)
    selfcheck("KR0010", "KB손해보험", t2, item1_own=686332.0, item15=0.0, item16=0.0)

    # 현대: 별도(own) 보험손익 = 396,111 백만 (LOB summary 백만원; note items 원->/1e6).
    # The LOB summary 합계 == 보험손익, so 기타사업비용 is outside -> item16=0.
    hd = load("KR0009")
    t2 = extract_tier2_hyundai(hd)
    for k in (4, 5, 6, 9, 10, 11):
        if t2.get(k) is not None:
            t2[k] = t2[k] / 1e6
    selfcheck("KR0009", "현대해상", t2, item1_own=396111.0, item15=0.0, item16=0.0)

    # 한화: 별도 보험손익 = 206,270 백만 (note 천원 -> /1000). 한화's 보험손익 INCLUDES
    # 기타사업비용 (128,958) as a deduction -> identity uses -item16.
    hw = load("KR0002")
    t2 = extract_tier2_hanwha(hw)
    for k in (4, 5, 6, 9, 10, 11, 13, 14, "_jang_net"):
        if t2.get(k) is not None:
            t2[k] = t2[k] / 1e3
    selfcheck("KR0002", "한화손해보험", t2, item1_own=206270.0, item15=0.0, item16=128958.0)


if __name__ == "__main__":
    main()
