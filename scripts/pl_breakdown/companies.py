"""Per-company DART note handlers + the SONBO/LIFE dispatch tables.

Each insurer lays its 계약유형별 note out differently, so these are
deliberately per-company rather than a generic parser.
"""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
import glob
import re

from scripts.build_net_income_breakdown import to_num

from .common import _SOURCELINE_CAP, _label, _norm, _prefer_ofs, _row_nums
from .tier1 import _header_blob, _pick_line, _ytd_col
from .tier2 import _is_rollforward, _lab0, _row_by_label, _scale, extract_tier2_abl


# ----------------------------- KB 손보 (KR0010) ---------------------------- #
def _kb_note(tables, item1=None):
    # KB publishes this note TWICE — 연결(consolidated, larger 총보험서비스결과) then 별도
    # (separate).  Tier-1 item1 is 별도 from 2024 on but 연결 in FY2023 (FS-API absent → HTML 연결
    # fallback), so select the note whose 총보험서비스결과 합계 matches the pipeline's item1 rather
    # than a fixed 연결/별도 rule.  No <당기> filter in the candidate gate: the 별도 Q4 note has a
    # bare caption (no <당기>), which the old filter wrongly excluded → forced the 연결 note.
    cands = []
    for t in tables:
        cap = t.caption or ""
        if "보험손익" not in cap or "상세내역" not in cap:
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not all(k in hb for k in ("장기", "일반", "자동차")):
            continue
        if _row_by_label(t, "총 보험서비스결과") is None:
            continue
        cands.append(t)
    if not cands:
        return None

    def jang_total(t):
        r = _row_by_label(t, "총 보험서비스결과")
        n = _row_nums(r) if r else []
        return n[-1] if n else None
    if item1 is not None:
        scored = [(t, jang_total(t)) for t in cands]
        scored = [(t, tot) for t, tot in scored if tot is not None]
        if scored:
            scored.sort(key=lambda c: abs(c[1] - item1))
            if abs(scored[0][1] - item1) <= 0.05 * abs(item1) + 2:
                return scored[0][0]
    # fallback (item1 unavailable): old behaviour — period-tagged note, largest 총보험수익.
    tagged = [t for t in cands
              if "<당기>" in (t.caption or "") or "<당분기>" in (t.caption or "")]
    pool = tagged or cands

    def jang_rev(t):
        r = _row_by_label(t, "총 보험수익")
        n = _row_nums(r) if r else []
        return n[0] if n else 0
    pool.sort(key=jang_rev, reverse=True)
    return pool[0]


def _kb_quarterly_note(tables):
    """KB 분기/반기 '보험손익의 상세내역' note — header has 3개월 / 누적 (and no <당기>)."""
    for t in tables:
        cap = t.caption or ""
        if "보험손익" not in cap or "상세" not in cap:
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if "누적" not in hb or not all(k in hb for k in ("장기", "일반", "자동차")):
            continue
        if _row_by_label(t, "총 보험서비스결과") is not None:
            return t
    return None


def extract_tier2_kb_quarterly(t):
    """KB 분기 note: columns are [3개월 …, 누적 …]; the schema is YTD so read the 누적 half.
    Recovers the gold-clean decomposition: 원수 CSM상각(4)/위험조정(5), 재보험 CSM상각(9)/
    위험조정(10) from the GMM 장기 column, and 자동차(13) from 총 보험서비스결과.  The segment
    손익 (장기 item2 / 일반 item14) is NOT emitted here: KB nets 기타사업비용 BY SEGMENT in a
    separate table, so 총 보험서비스결과's 장기/일반 are pre-기타사업비용 and would be wrong; that
    allocation + Tier-1 item1 come from elsewhere (DART FS API)."""
    def cum0(r):                      # first value of the 누적 half = GMM 장기 column
        if r is None:
            return None
        n = _row_nums(r)
        return n[len(n) // 2] if n else None

    out = {}
    csm = cum0(_row_by_label(t, "보험계약마진 상각", "제공된 서비스의 보험계약마진"))
    re_csm = cum0(_row_by_label(t, "제공받은 서비스의 재보험계약마진"))
    ra1 = ra2 = None
    seen = 0
    for r in t.rows:
        if "위험해제로인한위험조정의변동" in _lab0(r):
            seen += 1
            if seen == 1:
                ra1 = cum0(r)          # 보험수익 section (원수)
            elif seen == 2:
                ra2 = cum0(r)          # 재보험비용 section (출재)
    if csm is not None:
        out[4] = abs(csm)
    if ra1 is not None:
        out[5] = abs(ra1)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if ra2 is not None:
        out[10] = -abs(ra2)
    res = _row_nums(_row_by_label(t, "총 보험서비스결과"))
    if res:                            # 누적 half LOB layout [장기, 일반, 자동차, 해외, 합계]
        cum = res[len(res) // 2:]
        if len(cum) >= 3:
            out[13] = cum[2]           # 자동차 (gold-clean; no 기타사업비용 allocation)
    return out


def extract_tier2_kb(tables, item1=None):
    t = _kb_note(tables, item1=item1)
    if t is None:
        qt = _kb_quarterly_note(tables)        # KB 분기: 누적-column decomposition (KR0010 only)
        return extract_tier2_kb_quarterly(qt) if qt is not None else {}
    out = {}
    # Interim 3개월/누적 split note (Q3): read the 누적 half so the YTD decomposition matches the
    # YTD income statement (item1).  Annual/Q1 notes have no split → first-column behaviour.
    hb = " ".join(" ".join(h) for h in t.header)
    _cum = ("3개월" in hb and "누적" in hb)

    def _pick(n):
        if not n:
            return None
        return n[len(n) // 2] if _cum else n[0]

    def jang(r):
        if r is None:
            return None
        return _pick(_row_nums(r))
    csm = jang(_row_by_label(t, "제공된 서비스의 보험계약마진", "보험계약마진 상각"))
    ra = jang(_row_by_label(t, "위험해제로 인한 위험조정의 변동"))
    rev_exp = jang(_row_by_label(t, "예상 보험금 및 보험서비스비용"))
    cost_act = None
    for r in t.rows:
        if _lab0(r) == "보험금및보험서비스비용":
            cost_act = _pick(_row_nums(r))
            break
    re_csm = jang(_row_by_label(t, "제공받은 서비스의 재보험계약마진"))
    re_cost_exp = jang(_row_by_label(t, "회수예상 보험금 및 보험서비스비용"))
    re_ra = None
    seen_ra = 0
    for r in t.rows:
        if "위험해제로인한위험조정의변동" in _lab0(r):
            seen_ra += 1
            if seen_ra == 2:
                re_ra = _pick(_row_nums(r))
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

    tr = _row_nums(_row_by_label(t, "총 보험수익"))
    tc = _row_nums(_row_by_label(t, "총 보험서비스비용"))
    trr = _row_nums(_row_by_label(t, "총 재보험수익"))
    trc = _row_nums(_row_by_label(t, "총 재보험비용"))
    out["_jang_rev"] = _pick(tr)
    out["_jang_cost"] = abs(_pick(tc)) if tc else None
    out["_jang_rerev"] = _pick(trr)
    out["_jang_recost"] = abs(_pick(trc)) if trc else None

    res = _row_nums(_row_by_label(t, "총 보험서비스결과"))
    if res:
        half = res[len(res) // 2:] if _cum else res
        if len(half) >= 5:
            out["_jang_net"] = half[0]
            out[13] = half[2]
            out[14] = half[1] + half[3]
    return out  # 백만원 already


# ---------------------------- 현대 손보 (KR0009) --------------------------- #
def _hyundai_period_marker(tables, ti):
    """당기/전기 marker for the NEW-form note: each leg table is preceded by a 1-2 row
    header table whose last row is exactly '당기'/'당분기' (annual/quarterly) or
    '전기'/'전분기'.  Scan the 2 preceding tables; None when no marker found."""
    for j in range(ti - 1, max(ti - 3, -1), -1):
        for r in tables[j].rows:
            lab = _lab0(r)
            if lab in ("당기", "당분기", "당반기"):
                return "cur"
            if lab in ("전기", "전분기", "전반기"):
                return "prev"
    return None


def _hyundai_section(tables, first_label_starts):
    cands = []
    for ti, t in enumerate(tables):
        if not t.rows:
            continue
        if _lab0(t.rows[0]).startswith(first_label_starts.replace(" ", "")):
            cands.append((ti, t))
    if not cands:
        return None
    # 당기/당분기 leg only — the 전기/전분기 twin has IDENTICAL row labels, and its row0
    # magnitude can exceed the current period's (mag-sort alone is not safe).
    cur = [c for c in cands if _hyundai_period_marker(tables, c[0]) == "cur"]
    if cur:
        cands = cur

    def mag(c):
        n = _row_nums(c[1].rows[0])
        return abs(n[0]) if n else 0
    cands.sort(key=mag, reverse=True)
    return cands[0][1]


def _hyundai_lob_summary(tables):
    for t in tables:
        cap = t.caption or ""
        if "보험종목별" in cap and "수지" in cap:
            hb = " ".join(" ".join(h) for h in t.header)
            if "장기" in hb and "자동차" in hb and "일반" in hb:
                r = _row_by_label(t, "보험손익")
                if r:
                    return t, r
    return None, None


def _hyundai_old_components(tables):
    """현대해상 OLD form (2023.4Q–2025.1Q): one combined component table, header
    [구분, 장기, 자동차, 일반, 합계], col0 = 장기.  Two section-header rows ('보험수익' /
    '재보험서비스비용', each label-only).  Unit 천원 → /1e3.  Returns {4,5,9,10}
    (원수/재보 CSM상각·위험조정).  item6/11 (예실차) are not disclosed in this form.  The NEW
    form (2025.2Q+) is handled by extract_tier2_hyundai's _hyundai_section path, which already
    populates 4/5/9/10 — so this is merged ONLY when those are None."""
    comp = None
    for t in tables:
        labs = [_lab0(r) for r in t.rows]
        if labs and labs[0].startswith("보험수익") \
                and any(l.startswith("재보험서비스비용") for l in labs[1:]):
            comp = t
            break
    if comp is None:
        return {}
    out, sec = {}, None
    for r in comp.rows:
        lab = _lab0(r)
        if lab.startswith("보험수익"):
            sec = "dir"
            continue
        if lab.startswith("재보험서비스비용"):
            sec = "re"
            continue
        n = _row_nums(r)
        col0 = n[0] if n else None      # 장기
        if col0 is None:
            continue
        if lab.startswith("위험조정변동"):
            if sec == "dir" and 5 not in out:
                out[5] = col0
            elif sec == "re" and 10 not in out:
                out[10] = -col0
        elif lab.startswith("보험계약마진상각"):
            if sec == "dir" and 4 not in out:
                out[4] = col0
            elif sec == "re" and 9 not in out:
                out[9] = -col0
    _scale(out, 1e-3, (4, 5, 9, 10))    # 천원 → 백만원
    return out


def _hyundai_old_split(tables):
    """현대해상 OLDER split layout (2023.1Q–2023.3Q): 원수/재보 CSM·RA in ONE table captioned
    '(1) 당분기' (반기보고서: '(1) 당반기'), header [구분 | 보험계약부채 | 재보험(계약)자산].
      - 2023.2Q/3Q: each leg split into (3개월, 누적) → numerics [원수3M, 원수누적, 재보3M,
        재보누적] → read 누적 ([1] 원수, [3] 재보).
      - 2023.1Q: single column per leg (header '재보험자산', no 3개월/누적) → [원수, 재보].
    천원→/1e3.  Returns {4,5,9,10}; item6/11 not separable.  {} unless the table matches."""
    comp = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if not (cap.startswith("(1)당분기") or cap.startswith("(1)당반기")):
            continue
        hb = _header_blob(t)
        if "보험계약부채" not in hb or "재보험" not in hb:
            continue
        labs = [_lab0(r) for r in t.rows]
        if any(l.startswith("보험계약마진상각") for l in labs) \
                and any(l.startswith("위험조정변동") for l in labs):
            comp = t
            break
    if comp is None:
        return {}
    hb = _header_blob(comp)
    paired = "3개월" in hb and "누적" in hb
    out = {}
    for r in comp.rows:
        lab = _lab0(r)
        n = _row_nums(r)
        if paired:
            if len(n) < 4:
                continue
            dir_cum, re_cum = n[1], n[3]  # 원수 누적, 재보 누적
        else:
            if len(n) < 2:
                continue
            dir_cum, re_cum = n[0], n[1]  # 원수, 재보 (single-column 1Q)
        if lab.startswith("보험계약마진상각"):
            out.setdefault(4, dir_cum)
            out.setdefault(9, -re_cum)
        elif lab.startswith("위험조정변동"):
            out.setdefault(5, dir_cum)
            out.setdefault(10, -re_cum)
    _scale(out, 1e-3, (4, 5, 9, 10))      # 천원 → 백만원
    return out


def extract_tier2_hyundai(tables):
    out = {}
    rev_t = _hyundai_section(tables, "보험수익,")
    cost_t = _hyundai_section(tables, "보험서비스비용,")
    rerev_t = _hyundai_section(tables, "재보험수익,")
    recost_t = _hyundai_section(tables, "재보험비용,")
    # 분기보고서 NEW form (2025.2Q/3Q·2026.1Q): the cost / 재보험수익 legs DROP the
    # '보험서비스비용,'/'재보험수익,' row0 prefix — row0 reads '발생한 보험금 및 그 밖의 발생한
    # 보험서비스비용(/재보험수익)에 따른 증가분…'.  The annual (감사보고서) keeps the prefixed
    # form, so these are pure fallbacks (item6/11 were silently None on quarters without them).
    if cost_t is None:
        cost_t = _hyundai_section(tables, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    if rerev_t is None:
        rerev_t = _hyundai_section(tables, "발생한 보험금 및 그 밖의 발생한 재보험수익")

    def jang(t, *subs):
        if t is None:
            return None
        r = _row_by_label(t, *subs)
        if r is None:
            return None
        n = _row_nums(r)
        if not n:
            return None
        # 분기보고서 NEW form: each LOB splits into (3개월, 누적) column pairs → 장기 누적
        # = n[1].  (연차/1Q: one column per LOB → 장기 = n[0].)  Without this, 반기/3Q
        # quarters picked the 3-month leg (e.g. 2025.3Q item4 248,784 vs YTD 730,615).
        if len(n) >= 2 and "3개월" in _header_blob(t) and "누적" in _header_blob(t):
            return n[1]
        return n[0]

    # 2026.2Q 반기부터 라벨 재구성된 회사가 다수 확인됨(같은 개념, 어순만 다름) -- 기존 라벨
    # 유지, 신규 라벨도 인정.
    _NEW_CSM = "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진"
    csm = jang(rev_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진", _NEW_CSM)
    ra = jang(rev_t, "비금융위험에 대한 위험조정의 변동분")
    rev_exp = jang(rev_t, "보고기간에 발생한 보험서비스비용")
    cost_act = jang(cost_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_csm = jang(recost_t, "서비스의 이전으로 당기손익에 인식한 보험계약마진", _NEW_CSM)
    re_ra = jang(recost_t, "비금융위험에 대한 위험조정의 변동분")
    re_rev = jang(rerev_t, "발생한 보험금 및 그 밖의 발생한 보험서비스비용",
                  "발생한 보험금 및 그 밖의 발생한 재보험수익")
    re_cost_exp = jang(recost_t, "보고기간에 발생한 보험서비스비용")

    # unit auto-detect: DART changed this company's disclosed note unit between filings
    # (2026.1Q "(단위 : 원)" vs 2026.2Q 반기 "(단위 : 천원)" -- inbox/parser/20260816T2312Z).
    # Probe magnitude of whichever raw value is available: 원-denominated CSM-amortization
    # figures run ~1e11-1e12; 천원-denominated ones ~1e8-1e9 for the same real-world size.
    _probe = next((abs(x) for x in (csm, ra, re_csm) if x), None)
    _unit_scale = 1e-3 if (_probe is not None and _probe < 1e10) else 1e-6

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

    # LOB totals [장기, 자동차, 일반] from the 분석공시 (gold-anchored, 2026.1Q):
    #   rev    = single-row 합계-variant '보험수익' table (PAA twin has 장기=0 → max-|장기| pick)
    #   cost   = total row '보험서비스 비용에 따른 총 증가분…' inside cost_t
    #   rerev  = total row '재보험수익에 따른 총 증가분…' inside rerev_t
    #   recost = single-row '재보험서비스비용' 합계 variant (PAA twin smaller → max-|장기|)
    # assemble derives 3 = rev−cost, 8 = rerev−recost, 7/12 residuals, 2 = 3+8
    # (gold: 3=279,302 / 8=−5,993 / 7=127,592 / 12=−4,504).  13/14 = full gross LOB P&L
    # incl. reinsurance (gold 자동차 935,162−944,833−20−1,200 = −10,891 exact) — replaces the
    # LOB-summary netted legs (those allocate 기타사업비용 into each LOB; schema keeps item16).
    def _ytd_triple(t, row):
        n = _row_nums(row)
        if not n:
            return None
        hb = _header_blob(t)
        trip = n[1::2][:3] if ("3개월" in hb and "누적" in hb and len(n) >= 6) else n[:3]
        return trip if len(trip) == 3 else None

    def total_row_triple(t, *labels):
        if t is None:
            return None
        r = _row_by_label(t, *labels)
        return _ytd_triple(t, r) if r is not None else None

    def single_row_triple(label):
        best = None
        for ti2, st in enumerate(tables):
            if not st.rows or len(st.rows) > 2 or _lab0(st.rows[0]) != label:
                continue
            if _hyundai_period_marker(tables, ti2) != "cur":
                continue
            trip = _ytd_triple(st, st.rows[0])
            # >= : on 장기-ties (연결/별도 duplicates share the 장기 column) keep the LATER
            # table — DART body order is 연결주석 → 별도주석, and KR0009 basis is 별도
            # (자동차/일반 columns differ between the two).
            if trip and (best is None or abs(trip[0]) >= abs(best[0])):
                best = trip               # 합계 variant: 장기 ≠ 0 / PAA: 장기 = 0(or small)
        return best

    rev3 = single_row_triple("보험수익")
    cost3 = total_row_triple(cost_t, "보험서비스 비용에 따른 총 증가분", "보험서비스비용에 따른 총 증가분",
                             "발행한 보험계약에서 생기는 보험서비스비용")   # annual form
    rerev3 = total_row_triple(rerev_t, "재보험수익에 따른 총 증가분",
                              "재보험자에게서 회수한 금액에서 생기는 수익")  # annual form
    recost3 = single_row_triple("재보험서비스비용")
    if rev3 and cost3:
        out["_jang_rev"], out["_jang_cost"] = rev3[0], abs(cost3[0])
    if rerev3 and recost3:
        out["_jang_rerev"], out["_jang_recost"] = rerev3[0], abs(recost3[0])
    if rev3 and cost3 and rerev3 and recost3:
        out["_lob_gross_13"] = rev3[1] - abs(cost3[1]) + rerev3[1] - abs(recost3[1])
        out["_lob_gross_14"] = rev3[2] - abs(cost3[2]) + rerev3[2] - abs(recost3[2])
    # note items are in 원 (or 천원, this quarter -- see _unit_scale probe above) -> 백만원
    _scale(out, _unit_scale, (4, 5, 6, 9, 10, 11,
                              "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost",
                              "_lob_gross_13", "_lob_gross_14"))

    # 13/14 + 장기 net from the LOB summary table (already 백만원!)
    _, sumrow = _hyundai_lob_summary(tables)
    if sumrow is not None:
        n = _row_nums(sumrow)
        if len(n) >= 4:
            out[13] = n[2]          # 자동차
            out[14] = n[0]          # 일반
            out["_jang_net"] = n[1]  # 장기 net (no clean rev/cost split)
    # OLD form (2023.4Q–2025.1Q): the NEW _hyundai_section legs above don't match the older
    # combined table, so 4/5/9/10 are still None.  Backfill from the combined component table;
    # merge ONLY when None → NEW quarters (already populated) untouched.
    if any(out.get(k) is None for k in (4, 5, 9, 10)):
        for k, val in _hyundai_old_components(tables).items():
            if out.get(k) is None:
                out[k] = val
    if any(out.get(k) is None for k in (4, 5, 9, 10)):   # 2023.3Q older split layout
        for k, val in _hyundai_old_split(tables).items():
            if out.get(k) is None:
                out[k] = val
    # OLD form (≤2025.1Q) LOB totals fallback: combined [구분|장기|자동차|일반|합계] notes
    # (단위 천원) — sections 보험수익/재보험서비스비용 in one table, 보험서비스비용/재보험수익 in
    # the sibling.  Per-section 합계 row carries the LOB triple.
    if out.get("_jang_rev") is None:
        secs = {}
        for st in tables:
            if not st.rows:
                continue
            hb2 = _header_blob(st)
            if not ("장기" in hb2 and "자동차" in hb2 and "일반" in hb2):
                continue
            cap = str(getattr(st, "caption", "") or "")
            if "전" in cap.replace(" ", "")[:5]:        # (2) 전분기 / 전기 twin
                continue
            cur_sec, found = None, {}
            for r in st.rows:
                lab2 = _lab0(r)
                n3 = _row_nums(r)
                if lab2 in ("보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용") and not n3:
                    cur_sec = lab2
                elif lab2 in ("합계", "합 계") and cur_sec and len(n3) >= 4:
                    found[cur_sec] = n3[:3]
                    cur_sec = None
            for k2, v3 in found.items():
                if k2 not in secs or abs(v3[0]) > abs(secs[k2][0]):   # 누적 > 3개월
                    secs[k2] = v3
        K = 1e-3                                        # 천원 → 백만원
        rv, cv = secs.get("보험수익"), secs.get("보험서비스비용")
        rrv, rcv = secs.get("재보험수익"), secs.get("재보험서비스비용")
        if rv and cv:
            out["_jang_rev"], out["_jang_cost"] = rv[0] * K, abs(cv[0]) * K
        if rrv and rcv:
            out["_jang_rerev"], out["_jang_recost"] = rrv[0] * K, abs(rcv[0]) * K
        if rv and cv and rrv and rcv:
            out["_lob_gross_13"] = (rv[1] - abs(cv[1]) + rrv[1] - abs(rcv[1])) * K
            out["_lob_gross_14"] = (rv[2] - abs(cv[2]) + rrv[2] - abs(rcv[2])) * K
    # gross LOB legs (incl. reinsurance, 사업비 미차감) replace the LOB-summary netted 13/14 —
    # keeps the bridge item1 = 2+13+14−16 closed once item2 moves to the gross basis (3+8).
    if out.get("_lob_gross_13") is not None:
        out[13] = out.pop("_lob_gross_13")
    if out.get("_lob_gross_14") is not None:
        out[14] = out.pop("_lob_gross_14")
    return out


# ---------------------------- 한화 손보 (KR0002) --------------------------- #
def _hanwha_sep_rev_idx(tables):
    """Document index of the 별도(개별) 발행보험 '보험수익' table (당기 leg).
    한화손해 NEW filings carry the 보험수익/비용/재보험 component note TWICE — the 연결
    재무제표 주석 FIRST, then the 별도(개별) 주석 — each split into [당기, 전기].  The 연결
    leg folds in 캐롯손해보험(자동차/일반 자회사), so its PAA LOBs (자동차/일반) over-state by
    the subsidiary; only 별도 reconciles with the FS-API 별도 Tier-1 보험손익.  The 장기(GMM)
    leg is identical 별도=연결 (no subsidiary 장기 book), which is why items 4/5/6 were already
    gold-exact off the first (연결) table — but 13/14 were not.  Grand-total magnitude does NOT
    separate them (e.g. 2025.4Q 연결전기 < 별도당기), so cluster the '보험수익,'-led candidates
    by document position (a large index gap divides the 연결 block from the later 별도 block)
    and take the 당기 (first) table of the LATER (별도) cluster."""
    idxs = [ti for ti, t in enumerate(tables)
            if t.rows and _lab0(t.rows[0]).startswith("보험수익,")]
    if not idxs:
        return None
    clusters = [[idxs[0]]]
    for a, b in zip(idxs, idxs[1:]):
        (clusters[-1].append(b) if b - a < 100 else clusters.append([b]))
    return clusters[-1][0]            # later cluster = 별도 주석; its first table = 당기


def _hanwha_section_from(tables, start, first_label_starts):
    """First table at-or-after `start` whose row0 label starts with `first_label_starts`.
    Anchoring forward from the 별도 보험수익 table keeps cost/재보험 legs inside the same
    별도 block (the 연결 block is entirely earlier; within the block 당기 precedes 전기)."""
    p = first_label_starts.replace(" ", "")
    for t in tables[start:]:
        if t.rows and _lab0(t.rows[0]).startswith(p):
            return t
    return None


def extract_tier2_hanwha(tables):
    """한화손해 (KR0002): NEW standardized component note (2025.2Q+).  Each leg is a separate
    table whose row0 label is '보험수익,…' / '보험서비스비용,…' / '재보험수익,…' / '재보험비용,…',
    laid out as columns [장기, 일반, 자동차] × ([3개월, 누적] for 반기/3Q | single for Q1/연차).
    Unit 천원 → /1e3.  당기 별도 = first table of the LATER (별도) cluster — the note is filed
    TWICE (연결 주석 first, then 별도), so _hanwha_sep_rev_idx skips the 연결 block; all legs are
    then anchored forward from that index (_hanwha_section_from) to stay inside the 별도 block.
      - items 4/5 (원수 CSM상각 / 위험조정) = 장기 누적.
      - item6 (원수 예실차) = Σ(예상 보험금/손조비/유지비/투자관리비) − Σ(발생 동일 4종) — INCL
        투자관리비 (한화 convention; cf. 흥국/코리안리 EXCLUDE it).
      - items 9/10 = −(재보비용 CSM/RA) 장기 누적.
      - item11 (재보 예실차) = (재보수익 발생 보험금+손조비) − (재보비용 예상 보험금+손조비).
        Owner's gold additionally nets a '재보험비용, 보고기간 발생 (기초예상)' line not present in
        this note → item11 carries a small (~0.3% of item1) residual vs gold; assemble derives 12.
      - _jang_* totals → assemble derives 2/3/7/8/12 (all gold-exact: 2=252,200 3=250,697 8=1,503).
      - 13 자동차 / 14 일반 = PAA LOB net (원수 [rev−cost] + 재보 [회수수익−총재보험비용]), read off
        the 별도 tables.  (Earlier the 연결 leg was read by mistake, folding 캐롯손보's auto/general
        into 13/14 → ~21bn over-statement vs gold; the 별도 anchor resolves it.  gold 2025.2Q:
        13=-5,650.034  14=18,664.691, both now exact.)"""
    sep = _hanwha_sep_rev_idx(tables)
    if sep is None:
        return {}
    rev_t = tables[sep]
    cost_t = _hanwha_section_from(tables, sep, "보험서비스비용,")
    rerev_t = _hanwha_section_from(tables, sep, "재보험수익,")
    recost_t = _hanwha_section_from(tables, sep, "재보험비용,")
    summ_t = None
    for t in tables[sep:]:
        if t.rows and "재보험자에게서 회수" in _norm(t.rows[0][0]):
            summ_t = t
            break
    if not (rev_t and cost_t and recost_t):
        return {}
    rev_tot_row = None
    for r in rev_t.rows:
        if _lab0(r) == "보험수익":
            rev_tot_row = r
    rev_tot = _row_nums(rev_tot_row) if rev_tot_row else []
    if not rev_tot:
        return {}
    # LOB column order = [장기, 일반, 자동차]; paired [3개월, 누적] for 반기/3Q else single.
    paired = len(rev_tot) >= 6
    JC, GEN, AUTO = (1, 3, 5) if paired else (0, 1, 2)

    def rnum(t, *subs):
        r = _row_by_label(t, *subs) if t else None
        if r is None:
            return None
        n = _row_nums(r)
        return n[JC] if len(n) > JC else None

    def rsum(t, subs):
        s = 0.0
        any_ = False
        for sub in subs:
            x = rnum(t, sub)
            if x is not None:
                s += x
                any_ = True
        return s if any_ else None

    out = {}
    EXP = ("보험수익, 예상 보험금 (기초", "보험수익, 예상 손해조사비 (기초",
           "보험수익, 예상 유지비 (기초", "보험수익, 예상 투자관리비 (기초")
    ACT = ("보험서비스비용, 발생한 보험금", "보험서비스비용, 발생한 손해조사비",
           "보험서비스비용, 발생한 유지비", "보험서비스비용, 발생한 투자관리비")
    # 2026.2Q 반기보고서부터 라벨 재구성(같은 개념, 어순만 다름 -- 삼성화재/DB손보에서 먼저
    # 확인). "보험수익," 접두 없이 라벨 자체에 포함된 형태라 별도 문자열로 추가.
    csm = rnum(rev_t, "보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진",
               "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    ra = rnum(rev_t, "보험수익, 비금융위험에 대한 위험조정의 변동분")
    rev_exp = rsum(rev_t, EXP)
    cost_act = rsum(cost_t, ACT)
    re_csm = rnum(recost_t, "재보험비용, 서비스의 이전으로 당기손익에 인식한 보험계약마진",
                  "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    re_ra = rnum(recost_t, "재보험비용, 비금융위험에 대한 위험조정의 변동분")
    re_rev_dev = rsum(rerev_t, ("재보험수익, 발생한 보험금", "재보험수익, 발생한 손해조사비")) \
        if rerev_t else None
    re_cost_exp = rsum(recost_t, ("재보험비용, 예상 보험금 (기초", "재보험비용, 예상 손해조사비 (기초"))
    if csm is not None:
        out[4] = csm
    if ra is not None:
        out[5] = ra
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    if re_rev_dev is not None and re_cost_exp is not None:
        out[11] = re_rev_dev - re_cost_exp

    cost_tot_row = _row_by_label(cost_t, "발행한 보험계약에서 생기는 보험서비스비용")
    cost_tot = _row_nums(cost_tot_row) if cost_tot_row else []
    re_rev_lob = _row_nums(summ_t.rows[0]) if (summ_t and summ_t.rows) else []
    re_cost_lob = _row_nums(summ_t.rows[1]) if (summ_t and len(summ_t.rows) > 1) else []
    if len(rev_tot) > JC and len(cost_tot) > JC:
        out["_jang_rev"] = rev_tot[JC]
        out["_jang_cost"] = cost_tot[JC]
    if len(re_rev_lob) > JC and len(re_cost_lob) > JC:
        out["_jang_rerev"] = re_rev_lob[JC]
        out["_jang_recost"] = re_cost_lob[JC]

    def lobnet(idx):
        rv = rev_tot[idx] if len(rev_tot) > idx else 0.0
        cv = cost_tot[idx] if len(cost_tot) > idx else 0.0
        rr = re_rev_lob[idx] if len(re_rev_lob) > idx else 0.0
        rc = re_cost_lob[idx] if len(re_cost_lob) > idx else 0.0
        return (rv - cv) + (rr - rc)
    if len(rev_tot) > AUTO and len(cost_tot) > AUTO:
        out[13] = lobnet(AUTO)
        out[14] = lobnet(GEN)
    # note is in 천원 -> 백만원
    _scale(out, 1e-3, (4, 5, 6, 9, 10, 11, 13, 14,
                       "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost"))
    return out


def extract_tier2_hanwha_old(tables):
    """한화손해 (KR0002) pre-2025.2Q component note (2023.1Q–2025.1Q).  Three single-period
    sibling tables per period block, each [장기, 일반, 자동차, 합계]:
      • 보험(영업)수익  row0='예상보험금수익' + 보험계약마진상각수익 row
      • 보험(영업)비용  row0='발생보험금비용'
      • 출재보험수익및비용  row0='출재보험수익' (2 sections: 수익 합계 then 비용 합계)
    별도(=smallest current-period grand total; 연결 folds 퇴직연금/subsidiary into 일반/자동차).
    Quarterly notes pair [3개월, 누적] → 누적 장기 at RAW cell index 5; annual = single period
    → RAW index 1.  Index RAW cells (NOT _row_nums, which drops '-' and shifts columns).
    Unit 천원 → /1e3.  item6/11 예실차 INCL 투자관리비 (한화 convention).  13/14 = pure 3-LOB
    별도 PAA net — 한화's 퇴직연금 LOB sits OUTSIDE this note and is NOT split out (differs from
    the owner's hand-built gold by that allocation, same caveat as the NEW handler).
    Returns {} for the 2025.2Q+ single-table form (caller keeps extract_tier2_hanwha)."""
    Z = lambda v: v or 0.0
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def fl(t):
        return _norm(t.rows[0][0]).replace(" ", "") if (t.rows and t.rows[0]) else ""

    def hasrow(t, kw):
        k = kw.replace(" ", "")
        return any(k in _norm(r[0]).replace(" ", "") for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]).strip("()") if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [t for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    rev_c = cands(lambda t: fl(t) == "예상보험금수익" and hasrow(t, "보험계약마진상각수익"))
    cost_c = cands(lambda t: fl(t) == "발생보험금비용")
    re_c = cands(lambda t: fl(t) == "출재보험수익" and hasrow(t, "출재보험계약마진상각비용"))
    if not (rev_c and cost_c and re_c):
        return {}

    def gtot(t):  # 별도 selector: LAST 합계 row's last numeric cell
        g = float("inf")
        for r in t.rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                ns = _row_nums(r)
                if ns:
                    g = abs(ns[-1])
        return g

    rev_t, cost_t, re_t = min(rev_c, key=gtot), min(cost_c, key=gtot), min(re_c, key=gtot)

    hb = _header_blob(rev_t)
    paired = ("3개월" in hb and "누적" in hb)
    JC, GEN, AUTO = (5, 6, 7) if paired else (1, 2, 3)   # RAW 누적-장기 / 일반 / 자동차

    def cell(t, col, *needles):
        for r in t.rows:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                return to_num(r[col]) if len(r) > col else None
        return None

    def tot(t, col, which=0):  # which-th 합계 row, RAW column `col`
        haps = [r for r in t.rows if _norm(r[0]).replace(" ", "") == "합계"]
        return to_num(haps[which][col]) if (len(haps) > which and len(haps[which]) > col) else None

    out = {}
    csm = cell(rev_t, JC, "보험계약마진상각수익")
    ra = cell(rev_t, JC, "위험조정변동수익")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    exp = sum(Z(cell(rev_t, JC, n)) for n in
              ("예상보험금수익", "예상손해조사비수익", "예상계약유지비수익", "예상투자관리비수익"))
    act = sum(Z(cell(cost_t, JC, n)) for n in
              ("발생보험금비용", "발생손해조사비", "발생계약유지비용", "발생투자관리비"))
    out[6] = exp - act                                   # 예상 − 발생 (incl 투자관리비)
    re_csm = cell(re_t, JC, "출재보험계약마진상각비용")
    re_ra = cell(re_t, JC, "출재위험조정변동비용")
    if re_csm is not None:
        out[9] = -re_csm                                 # item9/10 = −(재보비용측 raw)
    if re_ra is not None:
        out[10] = -re_ra
    re_act = sum(Z(cell(re_t, JC, n)) for n in ("발생출재보험금수익", "발생수입손해조사비"))
    re_exp = sum(Z(cell(re_t, JC, n)) for n in ("예상출재보험금비용", "예상수입손해조사비"))
    out[11] = re_act - re_exp

    out["_jang_rev"] = tot(rev_t, JC)
    out["_jang_cost"] = tot(cost_t, JC)
    out["_jang_rerev"] = tot(re_t, JC, which=0)          # 출재수익 합계
    out["_jang_recost"] = tot(re_t, JC, which=1)         # 출재비용 합계

    def lobnet(col):                                     # pure 3-LOB net (퇴직연금 NOT separated)
        return (Z(tot(rev_t, col)) - Z(tot(cost_t, col))) \
            + (Z(tot(re_t, col, 0)) - Z(tot(re_t, col, 1)))
    out[13] = lobnet(AUTO)
    out[14] = lobnet(GEN)

    _scale(out, 1e-3, (4, 5, 6, 9, 10, 11, 13, 14,
                       "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost"))
    return out


def _hanwha_dispatch(tables):
    """NEW single-table form (2025.2Q+) first; fall through to the pre-2025.2Q component note.
    The two forms are structurally disjoint, so neither can corrupt the other."""
    out = extract_tier2_hanwha(tables)
    if out and any(out.get(i) is not None for i in (4, 5, 6)):
        return out
    return extract_tier2_hanwha_old(tables)


# ----------------------------- DB 손보 (KR0011) ---------------------------- #
# 2026.2Q 반기보고서부터 일부 회사가 "서비스의 이전으로 당기손익에 인식한 보험계약마진"을
# "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진"으로 재구성했다
# (같은 개념, 어순만 다름 — 삼성화재 확인, DB손보 등도 같은 note 구조 공유). 기존 라벨은
# 사라지지 않았으니 추가만, 제거는 안 함.
_S2_CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "보험계약마진 상각",
           "제공된 서비스의 보험계약마진",
           "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
_S2_RA = ("비금융위험에 대한 위험조정의 변동분", "위험조정 변동",
          "위험해제로 인한 비금융위험에 대한 위험조정의 변동")
_EXP_SPLIT = ("예상 보험금 (기초 예상 측정치)", "예상 유지비 (기초 예상 측정치)",
              "예상 손해조사비 (기초 예상 측정치)", "예상 투자관리비 (기초 예상 측정치)")
_ACT_SPLIT = ("발생한 보험금", "발생한 유지비", "발생한 손해조사비", "발생한 투자관리비")
_RE_EXP_COST = ("재보험비용, 예상 보험금 (기초 예상 측정치)",
                "재보험비용, 예상 기타 보험서비스비용 (기초 예상 측정치)",
                "보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
                "회수예상 보험금 및 기타보험서비스비용")


def _fl(t):
    return _norm(t.rows[0][0]) if t.rows else ""


def extract_tier2_db(tables):
    """DB손해 (KR0011): Tier-2 from notes "5. 보험수익 및 비용" + "6. 재보험수익 및 비용".

    The notes print 당기/전기 × 연결/별도, each laid out as 장기보험|일반보험|자동차보험 columns
    with [3개월, 누적] sub-pairs (annual report = a single 당기 column).  Gold-validated recipe
    (DB 2025.2Q gold sheet) wants the CURRENT-period 별도 figures, 누적(YTD) — the same basis as
    the FS-API Tier-1 (DB = OFS):
      - current period: a data table whose immediate predecessor is a 전기/전반기 marker row is
        the comparative — skip it (`is_prior`).
      - 별도 vs 연결: 별도 ⊆ 연결 (연결 adds the DB생명 subsidiary), so among current-period
        candidates pick the SMALLEST grand total.
    장기 원수 components (CSM상각/위험조정/예실차) sit in the first column-pair of the detail
    tables; 자동차/일반 net LOB from the summary + 재보 tables.  Emits the 4 _jang_* totals so
    `assemble` derives items 2/3/7/8/12 uniformly.  All values 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def lastlab(t):
        return _norm(t.rows[-1][0]) if (t.rows and t.rows[-1]) else ""

    def has(t, kw):
        return kw in " ".join(_norm(r[0]) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [(i, t) for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    # ≥4 numeric cols: 반기/3Q notes pair [3개월, 누적] (8 cols); Q1/annual are single-column
    # per LOB (4 cols: 장기/일반/자동차/합계).  The 연결 LOB summary carries an extra 비생명/
    # 생명 split (6 cols) — pmin (smallest grand total) still resolves to the 별도 table.
    rev_sums = cands(lambda t: _fl(t) == "보험수익" and "장기보험" in _header_blob(t)
                     and "자동차보험" in _header_blob(t)
                     and t.rows and len(_row_nums(t.rows[-1])) >= 4)
    cost_sums = cands(lambda t: _fl(t) == "보험비용" and "장기보험" in _header_blob(t)
                      and t.rows and len(_row_nums(t.rows[-1])) >= 4)
    rerev = cands(lambda t: lastlab(t) == "재보험자에게서 회수한 금액에서 생기는 수익")
    recost = cands(lambda t: lastlab(t) == "재보험자에게 지급된 보험료 배분액에서 생기는 비용")
    # 2026.2Q 반기보고서부터 라벨 재구성(같은 개념, 어순만 다름 -- 삼성화재에서 먼저 확인,
    # _S2_CSM에 이미 추가돼 있음) -- 이 게이트는 하드코드 문자열이라 _S2_CSM을 안 거쳐서 별도로
    # 반영 필요.
    rev_d = cands(lambda t: _fl(t).startswith("보험수익, 예상 보험금")
                  and any(has(t, k) for k in _S2_CSM))
    cost_d = cands(lambda t: _fl(t).startswith("보험서비스비용, 발생한 보험금"))
    recost_d = cands(lambda t: _fl(t).startswith("재보험비용, 예상 보험금"))
    if not all((rev_sums, cost_sums, rerev, recost, rev_d, cost_d, recost_d)):
        return {}

    def pmin(cs):  # 별도 = smallest current-period grand total
        return min(cs, key=lambda it: abs(_row_nums(it[1].rows[-1])[-1]))[1]
    rs, cs, rr, rc = pmin(rev_sums), pmin(cost_sums), pmin(rerev), pmin(recost)
    rd, cd, rcd = pmin(rev_d), pmin(cost_d), pmin(recost_d)

    # 누적(YTD) offset / per-LOB stride: quarterly notes pair [3개월, 누적]; annual = single col.
    hb = _header_blob(rs)
    off, st = (1, 2) if ("3개월" in hb and "누적" in hb) else (0, 1)

    def rownums(t, *needles):
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns:
                    return ns
        return None

    def d1(t, *needles):  # 장기-원수 (first LOB) 누적-column value of the matched row
        ns = rownums(t, *needles)
        return ns[off] if (ns and len(ns) > off) else None

    def at(arr, i):
        return arr[i] if 0 <= i < len(arr) else 0.0

    def lc(lob):
        return off + lob * st

    csm, ra = d1(rd, *_S2_CSM), d1(rd, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = [d1(rd, n) for n in _EXP_SPLIT]
    act = [d1(cd, n) for n in _ACT_SPLIT]
    if None not in exp and None not in act:
        out[6] = sum(exp) - sum(act)
    re_csm, re_ra = d1(rcd, *_S2_CSM), d1(rcd, *_S2_RA)
    if re_csm is not None:                          # 재보 CSM상각/위험조정 = −(cost-side raw)
        out[9] = -re_csm                            # cost CSM is negative → item9 positive
    if re_ra is not None:
        out[10] = -re_ra
    re_act = [d1(rr, "재보험수익, 발생한 보험금"), d1(rr, "재보험수익, 발생한 손해조사비")]
    re_exp = [d1(rcd, "재보험비용, 예상 보험금"), d1(rcd, "재보험비용, 예상 기타 보험서비스비용")]
    if None not in re_act and None not in re_exp:
        out[11] = sum(re_act) - sum(re_exp)

    rsr, csr = _row_nums(rs.rows[-1]), _row_nums(cs.rows[-1])
    rrr, rcr = _row_nums(rr.rows[-1]), _row_nums(rc.rows[-1])

    def recost_lob(lob):  # 재보험비용 last row = non-PAA block then PAA block (4 LOB groups each)
        return at(rcr, lc(lob)) + at(rcr, 4 * st + lc(lob))

    # item13 자동차 / item14 일반 = (보험수익 − 보험비용) + (재보수익 − 재보비용), per LOB 누적
    out[14] = (at(rsr, lc(1)) - at(csr, lc(1))) + (at(rrr, lc(1)) - recost_lob(1))
    out[13] = (at(rsr, lc(2)) - at(csr, lc(2))) + (at(rrr, lc(2)) - recost_lob(2))
    # 장기 누적 totals → assemble derives items 2/3/7/8/12
    out["_jang_rev"] = at(rsr, lc(0))
    out["_jang_cost"] = at(csr, lc(0))
    out["_jang_rerev"] = at(rrr, lc(0))
    out["_jang_recost"] = recost_lob(0)
    return out  # 백만원 already


# ------------- 삼성화재(KR0008) + generic 손보 component note --------------- #
def extract_tier2_sonbo_component(tables):
    """Generic 손보 Tier-2 from the standard IFRS17 component note (삼성화재 gold-validated).

    Layout (삼성화재 2025.2Q gold): each of the four notes is a SINGLE table whose FIRST row is
    the LOB total — 보험수익 / 발행한 보험계약에서 생기는 보험서비스비용 / 재보험자에게서 회수한
    금액에서 생기는 수익 / 재보험자에게 지급된 보험료 배분액에서 생기는 비용 — with the component
    rows (CSM상각·위험조정·보고기간 발생(기초예상)) below.  Columns are LOB×[3개월,누적]; the LOB
    ORDER varies (삼성화재 = 장기/자동차/일반) so it is read from the header.  Basis = 별도
    (별도 ⊆ 연결): among current-period candidates take the smallest grand total.  예실차 accepts
    BOTH the combined 기초예상 line and the 4-way split.  Emits the 4 _jang_* totals → assemble
    derives items 2/3/7/8/12.  All 백만원.  Returns {} when the note layout doesn't match, so the
    caller can fall back to Format-A / Format-B."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "자동차보험", "일반보험")

    def fr(t):
        return _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""

    def hasrow(t, kw):
        return any(kw in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                first = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and first in PRIOR:
                    return True
        return False

    def cands(pred):
        return [(i, t) for i, t in enumerate(tables) if pred(t) and not is_prior(i)]

    # 2026.2Q 반기보고서부터 이 행 라벨이 재구성됐다(같은 개념, 어순만 다름): "서비스의 이전으로
    # 당기손익에 인식한 보험계약마진" -> "보험계약서비스의 이전 때문에 당기손익으로 인식된
    # 보험수익, 보험계약마진" (삼성화재 확인). 둘 다 인정 — 원래 라벨이 사라진 건 아니라서
    # 유지, 새 라벨만 추가.
    revd = cands(lambda t: fr(t) == "보험수익"
                 and (hasrow(t, "서비스의 이전으로 당기손익에 인식한 보험계약마진")
                      or hasrow(t, "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진"))
                 and "자동차보험" in _header_blob(t))
    costd = cands(lambda t: fr(t).startswith("발행한 보험계약에서 생기는 보험서비스비용")
                  and hasrow(t, "발생한 보험금"))
    rerevd = cands(lambda t: fr(t).startswith("재보험자에게서 회수한 금액에서 생기는 수익"))
    recostd = cands(lambda t: fr(t).startswith("재보험자에게 지급된 보험료 배분액에서 생기는 비용"))
    if not all((revd, costd, rerevd, recostd)):
        return {}

    def pmin_idx(cs):  # 별도 = smallest current-period grand total; skip rows with no numbers
        c = [it for it in cs if _row_nums(it[1].rows[0])]
        return min(c, key=lambda it: abs(_row_nums(it[1].rows[0])[-1])) if c else None

    def first_from(cs, start):  # first leg candidate at-or-after `start` (same 별도 block)
        c = [it for it in cs if it[0] >= start and _row_nums(it[1].rows[0])]
        return min(c, key=lambda it: it[0])[1] if c else None

    # Anchor all four legs to ONE basis.  The note is filed twice (연결 주석 먼저, 별도 뒤);
    # 별도 ⊆ 연결 holds for 보험수익/비용 (연결 adds subsidiary volume) so the 별도 rev = the
    # smaller grand total — but NOT for the reinsurance legs: 연결 eliminates intra-group
    # 재보험, so 별도 재보험회수(수익) can EXCEED 연결 (삼성화재 2026.1Q: 별도 80,446 > 연결
    # 78,380).  A per-leg "smallest grand total" then mixes bases (rev 별도 + rerev 연결),
    # short-changing one LOB by the elimination (일반 by 2,067).  Fix: pick the 별도 rev (min
    # grand total), then take cost/재보험 legs from the SAME document block (first at-or-after).
    rdi = pmin_idx(revd)
    if rdi is None:
        return {}
    sep, rd = rdi[0], rdi[1]
    pmin = lambda cs: (lambda it: it[1] if it else None)(pmin_idx(cs))
    cd = first_from(costd, sep) or pmin(costd)
    rr = first_from(rerevd, sep) or pmin(rerevd)
    rc = first_from(recostd, sep) or pmin(recostd)
    if None in (rd, cd, rr, rc):
        return {}

    hb = _header_blob(rd)
    off, st = (1, 2) if ("3개월" in hb and "누적" in hb) else (0, 1)
    order = sorted((hb.find(k), k) for k in LOBS)
    if any(p < 0 for p, _ in order):
        return {}
    lobpos = {k: idx for idx, (_, k) in enumerate(order)}

    def col(lob):
        return off + lobpos[lob] * st

    def d(t, *needles):  # 장기-LOB 누적-column value of the first row matching a needle
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > off:
                    return ns[off]
        return None

    def at(arr, i):
        return arr[i] if 0 <= i < len(arr) else 0.0

    csm, ra = d(rd, *_S2_CSM), d(rd, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}

    # 예실차 = expected − actual service.  Combined 기초예상 line if present, else 4-way split.
    exp = d(rd, "보고기간에 발생한 보험서비스비용")
    if exp is not None:
        act = d(cd, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    else:
        exps = [d(rd, n) for n in _EXP_SPLIT]
        acts = [d(cd, n) for n in _ACT_SPLIT]
        exp = sum(exps) if all(x is not None for x in exps) else None
        act = sum(acts) if all(x is not None for x in acts) else None
    if exp is not None and act is not None:
        out[6] = exp - act

    re_csm, re_ra = d(rc, *_S2_CSM), d(rc, *_S2_RA)
    if re_csm is not None:                          # 재보 CSM상각/위험조정 = −(cost-side raw)
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = d(rr, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    re_exp = d(rc, "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    rsr, csr = _row_nums(rd.rows[0]), _row_nums(cd.rows[0])
    rrr, rcr = _row_nums(rr.rows[0]), _row_nums(rc.rows[0])
    out[13] = (at(rsr, col("자동차보험")) - at(csr, col("자동차보험"))) \
        + (at(rrr, col("자동차보험")) - at(rcr, col("자동차보험")))
    out[14] = (at(rsr, col("일반보험")) - at(csr, col("일반보험"))) \
        + (at(rrr, col("일반보험")) - at(rcr, col("일반보험")))
    out["_jang_rev"] = at(rsr, col("장기보험"))
    out["_jang_cost"] = at(csr, col("장기보험"))
    out["_jang_rerev"] = at(rrr, col("장기보험"))
    out["_jang_recost"] = at(rcr, col("장기보험"))
    return out  # 백만원 already


# ----------------------------- 흥국화재 (KR0005) --------------------------- #
def extract_tier2_heungkuk(tables):
    """흥국화재 (KR0005, gold-validated 2025.2Q): each leg (보험수익 / 보험서비스비용 /
    재보험수익 / 재보험비용) is ONE combined table whose LOB total sits on a row found by LABEL
    (not position) with component rows below.  Columns are non-PAA[장기/일반/자동차/합계] then
    PAA[…] × [3개월,누적]; 장기 is GMM (non-PAA) but 재보험 carries a small PAA 장기 too, so each
    LOB 누적 = nonPAA + PAA (summed).  Basis 별도 (smallest grand total).  예실차 (item6/11) =
    expected(보고기간 발생 기초예상) − actual(발생 보험금 및 그 밖) — the gold's 과거/미래서비스 +
    보험취득CF 차이 stay in 기타(item7/12), NOT 예실차 (owner confirmed 2026-06-05).  All 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "일반보험", "자동차보험")

    def first(t):
        return _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):  # nums of the row whose col0..4 EXACTLY equals label
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        # cum() below reads this list by FIXED [LOB x 3개월/누적] column
                        # OFFSET (not label) -- so a cell DART rendered as a bare empty
                        # string instead of "0" gets silently dropped by _row_nums() (which
                        # only keeps cells where to_num() succeeds), shifting every later
                        # index left by one and reading the wrong LOB's number entirely.
                        # 2026.2Q 흥국화재: the "보험서비스비용" 총계 row has its 자동차보험
                        # 비PAA/3개월 cell blank (siblings in the same row are literal "0"),
                        # which pulled item13(자동차손익) to -620,653 -- 55x 2026.1Q's
                        # -11,182 -- and tripped assemble()'s RC gate, nulling items 2-14
                        # wholesale (inbox/parser/20260829T2010Z). Re-parse this ONE row
                        # position-preserving (blank/dash -> 0.0 IN PLACE, label col r[0]
                        # dropped) so the offsets stay valid; row SELECTION is unchanged
                        # (still gated on the plain _row_nums(r) above) and the returned
                        # values are IDENTICAL to _row_nums() whenever no cell is blank --
                        # verified against the two gold-validated quarters this function
                        # was built for (2025.2Q/2025.3Q: all four legs' total rows are
                        # fully populated, len(r)==17 same 1-label+16-data shape, output
                        # unchanged) and against every other on-disk KR0005 quarter (no
                        # dispatch-visible change outside 2026.2Q).
                        return [(to_num(c) if to_num(c) is not None else 0.0) for c in r[1:]]
        return None

    def find(totlabel, must):
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "장기보험" in _header_blob(t)]
        return min(cs, key=lambda it: abs(totrow(it[1], totlabel)[-1]))[1] if cs else None

    # 2026.2Q 반기부터 라벨 재구성된 회사가 있어(같은 개념, 어순만 다름 -- 삼성화재/한화손보/
    # DB손보에서 먼저 확인) 두 라벨 중 아무거나 있으면 통과.
    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("보험수익", "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    cost = find("보험서비스비용", "발생한 보험금")
    rerev = find("재보험수익", "재보험수익, 발생한 보험금")
    recost = find("재보험비용", "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("재보험비용", "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    if None in (rev, cost, rerev, recost):
        return {}

    hb = _header_blob(rev)
    lobpos = {k: i for i, (_, k) in enumerate(sorted((hb.find(x), x) for x in LOBS))}

    def cum(ns, lob):  # nonPAA + PAA 누적 for one LOB (non-PAA block = 4 LOB-groups × 2 cols)
        p = lobpos[lob]
        a = ns[1 + 2 * p] if len(ns) > 1 + 2 * p else 0.0
        b = ns[9 + 2 * p] if len(ns) > 9 + 2 * p else 0.0
        return a + b

    def comp(t, *needles):  # 장기 non-PAA 누적 of the first row matching a needle
        idx = 1 + 2 * lobpos["장기보험"]
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    rt = totrow(rev, "보험수익")
    ct = totrow(cost, "보험서비스비용")
    rrt = totrow(rerev, "재보험수익")
    rct = totrow(recost, "재보험비용")

    csm, ra = comp(rev, *_S2_CSM), comp(rev, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = comp(rev, "보고기간에 발생한 보험서비스비용")
    act = comp(cost, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    if exp is not None and act is not None:
        out[6] = exp - act
    re_csm, re_ra = comp(recost, *_S2_CSM), comp(recost, *_S2_RA)
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = comp(rerev, "재보험수익, 발생한 보험금 및 그 밖", "재보험수익, 발생한 보험금")
    re_exp = comp(recost, "재보험비용, 보고기간에 발생한 보험서비스비용", "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    out[13] = (cum(rt, "자동차보험") - cum(ct, "자동차보험")) \
        + (cum(rrt, "자동차보험") - cum(rct, "자동차보험"))
    out[14] = (cum(rt, "일반보험") - cum(ct, "일반보험")) \
        + (cum(rrt, "일반보험") - cum(rct, "일반보험"))
    out["_jang_rev"] = cum(rt, "장기보험")
    out["_jang_cost"] = cum(ct, "장기보험")
    out["_jang_rerev"] = cum(rrt, "장기보험")
    out["_jang_recost"] = cum(rct, "장기보험")
    return out  # 백만원 already


def extract_tier2_heungkuk_old(tables):
    """흥국화재 (KR0005) pre-2025.2Q 보험종류별 leg-split note (2023.1Q–2025.1Q).
    REV/RECOST = one COMBINED 구분/계정과목 table [장기, 일반, 자동차, 합계]; COST/REREV split
    into 일반모형(장기-only) + PAA(일반/자동차) tables.  Each note prints 당기누적/당기3개월/전기
    누적/전기3개월 with NO prior marker → FIRST matching table = current YTD; grand total = LAST
    합계 (소계 is the 장기 sub-block).  Annual (Q4) collapses 일반모형 LOB cols to period cols
    (장기 stays at numeric col0) and renames 예상지급보험금→예상발생보험금.  Captions vary
    (재보험/출재보험/재보험종류별) → matching is purely structural.  item6/11 예실차 EXCLUDES
    투자관리비.  Returns {} for the 2025.2Q+ single-table form (caller keeps extract_tier2_heungkuk)."""
    JANG, ILBAN, AUTO = "장기", "일반", "자동차"
    CSM = "보험계약마진상각"
    RA = ("비금융위험에대한위험조정변동", "위험조정변동", "위험조정의변동")
    z = lambda v: v or 0.0

    def hdr(t):
        for r in t.rows[:3]:
            cells = [_norm(c).replace(" ", "") for c in r]
            if cells and cells[0] in ("구분", "계정과목", "항목"):
                return cells
        return []

    def lobidx(cells):
        m, j = {}, 0
        for c in cells[1:]:
            if c in (JANG, ILBAN, AUTO):
                m[c] = j
            if c in (JANG, ILBAN, AUTO, "합계"):
                j += 1
        return m

    def totrow(t):
        last = None
        for r in t.rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                ns = _row_nums(r)
                if ns:
                    last = ns
        return last

    def rowblob(t):
        return "".join(_norm(r[0]).replace(" ", "") for r in t.rows)

    def rv(rows, idx, *needles):
        for r in rows:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    def pick_combined(sig_all, sig_none=()):
        for t in tables:
            cells = hdr(t)
            if not cells or not (JANG in cells and AUTO in cells):
                continue
            blob = rowblob(t)
            if all(s in blob for s in sig_all) and not any(s in blob for s in sig_none):
                tr = totrow(t)
                if tr:
                    return (t, cells, tr)
        return None

    def pick_jang(sig_all):
        for t in tables:
            cells = hdr(t)
            if not cells or AUTO in cells or ILBAN in cells:
                continue
            if all(s in rowblob(t) for s in sig_all):
                tr = totrow(t)
                if tr:
                    return (t, tr)
        return None

    def find_paa(sig_all, sig_none=()):
        for t in tables:
            cells = hdr(t)
            if not cells or not (ILBAN in cells and AUTO in cells):
                continue
            blob = rowblob(t)
            if all(s in blob for s in sig_all) and not any(s in blob for s in sig_none):
                tr = totrow(t)
                if tr:
                    return (t, cells, tr)
        return None

    rev = pick_combined([CSM, "보험료배분법적용수익"],
                        sig_none=["예상출재보험금", "기타재보험계약비용", "발생재보험금"])
    recost = pick_combined(["예상출재보험금", CSM])
    cost = pick_jang(["발생보험금", "직접유지비", "직접신계약비상각비"])
    rerev = pick_jang(["발생재보험금", "발생사고부채조정"])
    if None in (rev, cost, rerev, recost):
        return {}

    revT, revC, revTot = rev
    recT, recC, recTot = recost
    li, rli = lobidx(revC), lobidx(recC)
    jrev, jrec = li[JANG], rli[JANG]

    out = {4: abs(z(rv(revT.rows, jrev, CSM))),
           5: abs(z(rv(revT.rows, jrev, *RA)))}
    exp = z(rv(revT.rows, jrev, "예상지급보험금", "예상발생보험금")) \
        + z(rv(revT.rows, jrev, "예상직접유지비")) + z(rv(revT.rows, jrev, "예상손해조사비"))
    act = z(rv(cost[0].rows, 0, "발생보험금")) \
        + z(rv(cost[0].rows, 0, "직접유지비")) + z(rv(cost[0].rows, 0, "손해조사비"))
    out[6] = exp - act
    out[9] = -z(rv(recT.rows, jrec, CSM))
    out[10] = -z(rv(recT.rows, jrec, *RA))
    re_act = z(rv(rerev[0].rows, 0, "발생재보험금")) \
        + z(rv(rerev[0].rows, 0, "발생수입손해조사비")) + z(rv(rerev[0].rows, 0, "발생사고부채조정"))
    re_exp = z(rv(recT.rows, jrec, "예상출재보험금")) + z(rv(recT.rows, jrec, "예상수입손해조사비"))
    out[11] = re_act - re_exp

    def lobtot(tr, m, lob):
        i = m.get(lob)
        return tr[i] if (i is not None and i < len(tr)) else 0.0

    rev_l = {lob: lobtot(revTot, li, lob) for lob in (JANG, ILBAN, AUTO)}
    rec_l = {lob: lobtot(recTot, rli, lob) for lob in (JANG, ILBAN, AUTO)}
    cost_l = {JANG: cost[1][0], ILBAN: 0.0, AUTO: 0.0}
    rerev_l = {JANG: rerev[1][0], ILBAN: 0.0, AUTO: 0.0}
    paacost = find_paa(["발생보험금", "직접유지비"],
                       sig_none=[CSM, "예상출재보험금", "발생재보험금"])
    paarerev = find_paa(["발생재보험금", "발생사고부채조정"], sig_none=["예상출재보험금"])
    if paacost:
        pm = lobidx(paacost[1])
        for lob in (ILBAN, AUTO):
            cost_l[lob] = lobtot(paacost[2], pm, lob)
    if paarerev:
        prm = lobidx(paarerev[1])
        for lob in (ILBAN, AUTO):
            rerev_l[lob] = lobtot(paarerev[2], prm, lob)

    out[13] = (rev_l[AUTO] - cost_l[AUTO]) + (rerev_l[AUTO] - rec_l[AUTO])
    out[14] = (rev_l[ILBAN] - cost_l[ILBAN]) + (rerev_l[ILBAN] - rec_l[ILBAN])
    out["_jang_rev"] = rev_l[JANG]
    out["_jang_cost"] = cost_l[JANG]
    out["_jang_rerev"] = rerev_l[JANG]
    out["_jang_recost"] = rec_l[JANG]
    return out  # 백만원 already


def extract_tier2_heungkuk_single(tables):
    """흥국화재 (KR0005) single-period note (2025.4Q annual, 2026.1Q+): the NEW combined-table
    note dropped the 3개월/누적 column split AND collapsed the non-PAA LOB columns (장기 is the
    only non-PAA LOB).  Every value row therefore has the non-PAA 장기 figure as its FIRST
    numeric; each leg's total row carries the PAA split as its last three numerics
    [일반, 자동차, 합계].  Schema is YTD (the single column = 누적).  Returns {} (dispatch falls
    through to wide / OLD paths) unless all four legs match."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        # Sibling of extract_tier2_heungkuk.totrow() (fixed 2026-08-29,
                        # fb9c9bf, same blank-cell hazard): this row's consumers
                        # (jang_tot()/paa_lob() below) read it by FIXED offset (ns[0],
                        # ns[-1]/-2/-3), so a cell DART renders as a bare empty string
                        # instead of "0" silently drops out of _row_nums() and shifts every
                        # later index.  Confirmed live in 2026.1Q: the "보험수익" totrow
                        # prints ['보험수익','660,961','','0','660,961','0','39,692',
                        # '33,824','73,516'] -- pos2 is a bare blank, not "0" -- the blank
                        # happened to land away from the endpoints this quarter's readers
                        # use, so the output was unaffected (inbox/parser/
                        # 20260829T2200Z__orchestrator__MULTI__row_nums_blank_compression_census.md),
                        # but the next quarter that blanks an endpoint reproduces the
                        # 2026.2Q incident.  Re-parse position-preserving (blank/dash ->
                        # 0.0 IN PLACE, label col r[0] dropped) so the fixed offsets stay
                        # valid; row SELECTION is unchanged (still gated on the plain
                        # _row_nums(r) truthy check above).
                        return [(to_num(c) if to_num(c) is not None else 0.0) for c in r[1:]]
        return None

    def find(totlabel, must):
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "장기보험" in _header_blob(t)
              and "3개월" not in _header_blob(t) and "누적" not in _header_blob(t)]
        return min(cs, key=lambda it: it[0])[1] if cs else None  # current = first printed

    # find()'s `must` only takes one string; 2026.2Q 반기부터 라벨이 재구성된 회사가 있어
    # (같은 개념, 어순만 다름 -- 삼성화재/한화손보에서 먼저 확인) 두 라벨 중 아무거나 있으면
    # 통과하도록 별도 호출 후 병합.
    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("보험수익", "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    cost = find("보험서비스비용", "발생한 보험금")
    rerev = find("재보험수익", "재보험수익, 발생한 보험금")
    recost = find("재보험비용", "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("재보험비용", "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진")
    if None in (rev, cost, rerev, recost):
        return {}

    def jang(t, *needles):  # non-PAA 장기 = FIRST numeric of the first matching component row
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns:
                    return ns[0]
        return None

    def paa_lob(t, label):  # total row's PAA block: last three numerics = [일반, 자동차, 합계]
        ns = totrow(t, label)
        if not ns or len(ns) < 3:
            return (0.0, 0.0)
        return (ns[-3], ns[-2])  # (일반, 자동차)

    csm, ra = jang(rev, *_S2_CSM), jang(rev, *_S2_RA)
    if csm is None or ra is None:
        return {}
    out = {4: abs(csm), 5: abs(ra)}
    exp = jang(rev, "보고기간에 발생한 보험서비스비용")
    act = jang(cost, "발생한 보험금 및 그 밖의 발생한 보험서비스비용", "발생한 보험금")
    if exp is not None and act is not None:
        out[6] = exp - act
    re_csm, re_ra = jang(recost, *_S2_CSM), jang(recost, *_S2_RA)
    if re_csm is not None:
        out[9] = -re_csm
    if re_ra is not None:
        out[10] = -re_ra
    re_act = jang(rerev, "재보험수익, 발생한 보험금 및 그 밖", "재보험수익, 발생한 보험금")
    re_exp = jang(recost, "보고기간에 발생한 보험서비스비용")
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    rev_il, rev_au = paa_lob(rev, "보험수익")
    cost_il, cost_au = paa_lob(cost, "보험서비스비용")
    rrev_il, rrev_au = paa_lob(rerev, "재보험수익")
    rcost_il, rcost_au = paa_lob(recost, "재보험비용")
    out[13] = (rev_au - cost_au) + (rrev_au - rcost_au)
    out[14] = (rev_il - cost_il) + (rrev_il - rcost_il)
    def jang_tot(t, label):
        # 장기손익 = non-PAA 장기 (FIRST numeric) + PAA 장기.  흥국 cedes some 장기 reinsurance
        # under PAA, so rerev/recost carry a PAA-장기 column the first-numeric read drops (→ 재보험
        # 장기 understated → 장기손익 over → ΣLOB over by 888−2572=1,684 in 2025.4Q, 968 in 2026.1Q).
        # PAA 장기 = PAA합계 − PAA일반 − PAA자동차 (last 3 numerics) — robust to 0-column dropping.
        ns = totrow(t, label)
        if not ns:
            return None
        paa_jang = (ns[-1] - ns[-3] - ns[-2]) if len(ns) >= 3 else 0.0
        return ns[0] + paa_jang
    out["_jang_rev"] = jang_tot(rev, "보험수익")
    out["_jang_cost"] = jang_tot(cost, "보험서비스비용")
    out["_jang_rerev"] = jang_tot(rerev, "재보험수익")
    out["_jang_recost"] = jang_tot(recost, "재보험비용")
    return out  # 백만원 already


def _heungkuk_dispatch(tables):
    """single-period (2025.4Q+) → wide (2025.2Q/3Q) → pre-2025.2Q leg-split.  All three forms
    are structurally disjoint (header 3개월/누적 presence + row0 signatures), so no cross-corruption."""
    out = extract_tier2_heungkuk_single(tables)        # 2025.4Q+ single-period form
    if out and any(out.get(i) is not None for i in (4, 5)):
        return out
    out = extract_tier2_heungkuk(tables)               # 2025.2Q/3Q wide form
    if out and any(out.get(i) is not None for i in (4, 5)):
        return out
    return extract_tier2_heungkuk_old(tables)          # pre-2025.2Q leg-split note


def _coreanre_old(tables):
    """코리안리 pre-2025.2Q: a SINGLE merged 구분-rows note (구분|장기|생명|일반|합계) holding all
    four legs as section-label rows.  Same dual schema as extract_tier2_coreanre (생명→2-12,
    장기→2-1…12-1, 일반→14).  Agent-derived + RC-validated 2023.3Q–2025.1Q (≤1 백만)."""
    def r0(t):
        return _norm(t.rows[0][0]).replace(" ", "") if (t.rows and t.rows[0]) else ""

    def is_note(t):
        hb = _header_blob(t)
        return (hb.startswith("구분") and "장기" in hb and "생명" in hb and "일반" in hb
                and len(t.rows) > 20 and any(_norm(r[0]) == "보험수익" for r in t.rows if r))
    cands = [i for i, t in enumerate(tables)
             if is_note(t) and i > 0 and r0(tables[i - 1]) == "기초순장부금액"]
    if not cands:
        return {}
    t = tables[max(cands)]                                   # 별도 = last current-period note
    hb = _header_blob(t)
    COL = {"장기": 1, "생명": 3, "일반": 5} if ("3개월" in hb and "누적" in hb) \
        else {"장기": 0, "생명": 1, "일반": 2}
    SECMAP = {"보험수익": "REV", "보험비용": "COST", "재보험수익": "REREV", "재보험비용": "RECOST"}
    secs = {}
    cur = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in SECMAP and not _row_nums(r):
            cur = SECMAP[lab]; secs.setdefault(cur, [])
        elif cur is not None and r:
            secs[cur].append(r)
    if not all(k in secs for k in ("REV", "COST", "REREV", "RECOST")):
        return {}

    z = lambda v: v or 0.0

    def val(sec, lob, *needles):
        idx = COL[lob]
        for r in secs[sec]:
            lab = _norm(r[0]).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                # Raw-indexed on r[1+idx] (NOT _row_nums(r), which drops '-'/blank cells and
                # shifts every later column left) -- same fix as _nh_gmm_re_incurred /
                # extract_tier2_heungkuk.totrow().  census (inbox/parser/
                # 20260829T2200Z__orchestrator__MULTI__row_nums_blank_compression_census.md) found
                # dashes fixed at raw position 5-6 in 2023.3Q/2024.2Q/2024.3Q -- exactly
                # COL["일반"]=5 (the paired-quarter 일반 column).  No corruption observed
                # yet because every call site so far reads idx 1/3 (장기/생명), never idx 5
                # (일반), but a compacting read would silently misalign item14 the day a
                # component/total row's 일반 column itself goes blank.
                if len(r) > 1 + idx:
                    v = to_num(r[1 + idx])
                    return v if v is not None else 0.0
        return None

    def leg(lob):
        suje = z(val("REV", lob, "총보험수익")) - z(val("COST", lob, "총보험비용"))
        csm = abs(z(val("REV", lob, "보험계약마진상각")))
        ra = abs(z(val("REV", lob, "위험조정변동")))
        yes = sum(z(val("REV", lob, n)) for n in ("예상발생보험금", "예상손해조사비", "예상계약유지비")) \
            - sum(z(val("COST", lob, n)) for n in ("발생보험금", "발생손해조사비", "발생계약유지비"))
        chuljae = z(val("REREV", lob, "총재보험수익")) - z(val("RECOST", lob, "총재보험비용"))
        recsm = -z(val("RECOST", lob, "보험계약마진상각"))
        rera = -z(val("RECOST", lob, "위험조정변동"))
        reyes = z(val("REREV", lob, "발생재보험금")) - z(val("RECOST", lob, "예상재보험금"))
        return {2: suje + chuljae, 3: suje, 4: csm, 5: ra, 6: yes, 7: suje - csm - ra - yes,
                8: chuljae, 9: recsm, 10: rera, 11: reyes, 12: chuljae - recsm - rera - reyes}

    life, jang = leg("생명"), leg("장기")
    if not life[4] or abs(life[4]) <= 1:
        return {}
    out = {k: life[k] for k in range(4, 13)}
    out["_jang_rev"] = z(val("REV", "생명", "총보험수익"))
    out["_jang_cost"] = z(val("COST", "생명", "총보험비용"))
    out["_jang_rerev"] = z(val("REREV", "생명", "총재보험수익"))
    out["_jang_recost"] = z(val("RECOST", "생명", "총재보험비용"))
    out[14] = (z(val("REV", "일반", "총보험수익")) - z(val("COST", "일반", "총보험비용"))) \
        + (z(val("REREV", "일반", "총재보험수익")) - z(val("RECOST", "일반", "총재보험비용")))
    _N = {2: "장기재보험 손익", 3: "장기재보험 수재손익", 4: "수재 CSM상각",
          5: "수재 위험조정 변동", 6: "수재 예실차", 7: "기타 장기재보험 수재손익",
          8: "장기재보험 출재손익", 9: "출재 CSM상각", 10: "출재 위험조정 변동",
          11: "출재 예실차", 12: "기타 장기재보험 출재손익"}
    out["_extra_items"] = [{"항목번호": f"{k}-1", "항목명": _N[k], "값": jang[k]} for k in range(2, 13)]
    out["_extra_lob"] = jang[2]
    return out


# ------------------------------ 코리안리 (KR1000) -------------------------- #
def extract_tier2_coreanre(tables):
    """코리안리재보험 (KR1000, gold-validated 2025.2Q) — a REINSURER, so the note splits by
    생명보험 / 장기보험 / 일반보험 (NO 자동차) and each GMM line of business carries a full
    수재(inward, = 발행보험 보험수익−비용) + 출재(ceded, = 재보험수익−비용) decomposition.  The
    owner's schema maps 생명재보험 → items 2-12 (standard slots) and 장기재보험 → items 2-1…12-1
    (a parallel set returned via `_extra_items`); 일반재보험 → item14.  Columns are
    non-PAA[장기/생명/일반] then PAA[…] × [3개월,누적]; 장기·생명 are GMM (non-PAA), 일반 PAA, so
    each LOB 누적 = nonPAA + PAA.  Basis 별도 = the LATER document occurrence (연결 주석 precedes
    별도; min-total is unsafe here because 연결 재보험수익 < 별도).  예실차: 수재 = expected
    (4 예상 lines) − actual (발생 보험금+손조비+유지비, 발생투자관리비 제외); 출재 = 재보험수익
    발생보험금 − (재보험비용 예상보험금 + 보고기간 발생) — owner-confirmed 2026-06-05.  All 백만원."""
    PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
    LOBS = ("장기보험", "생명보험", "일반보험")

    def has(t, sub):
        return any(sub in (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")) for r in t.rows if r)

    def is_prior(i):
        for j in (i - 1, i - 2):
            if 0 <= j < len(tables):
                tj = tables[j]
                f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
                if len(tj.rows) <= 1 and f in PRIOR:
                    return True
        return False

    def totrow(t, label):
        for r in t.rows:
            if not r:
                continue
            for c in range(min(5, len(r))):
                if _norm(r[c]) == label:
                    ns = _row_nums(r)
                    if ns:
                        return ns
        return None

    def find(totlabel, must):  # latest current-period occurrence = 별도
        cs = [(i, t) for i, t in enumerate(tables)
              if not is_prior(i) and totrow(t, totlabel) is not None
              and has(t, must) and "생명보험" in _header_blob(t) and "장기보험" in _header_blob(t)]
        return max(cs, key=lambda it: it[0])[1] if cs else None

    # 2026.2Q 반기부터 라벨 재구성된 회사가 다수 확인됨(같은 개념, 어순만 다름) -- 기존 라벨
    # 유지, OR로 신규 라벨도 인정.
    _NEW_CSM = "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진"
    rev = find("보험수익", "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("보험수익", _NEW_CSM)
    cost = find("보험비용", "발생한 보험금")
    rerev = find("재보험자에게서 회수한 금액에서 생기는 수익", "재보험수익, 발생한 보험금")
    recost = find("재보험자에게 지급된 보험료 배분액에서 생기는 비용",
                  "서비스의 이전으로 당기손익에 인식한 보험계약마진") \
        or find("재보험자에게 지급된 보험료 배분액에서 생기는 비용", _NEW_CSM)
    if None in (rev, cost, rerev, recost):
        return _coreanre_old(tables)          # pre-2025.2Q 구분-rows merged note

    hb = _header_blob(rev)
    lobpos = {k: i for i, (_, k) in enumerate(sorted((hb.find(x), x) for x in LOBS))}
    # Layout drift: 2023.3Q~2025.3Q quarterly notes double each LOB cell into [3개월, 누적];
    # FY2025 annual + 2026.1Q onward dropped the doubling -> single-period cells.  step = the
    # cell width per LOB, off = the 누적 index within a cell (0 when single-period).
    quarterly = ("3개월" in hb and "누적" in hb)
    step = 2 if quarterly else 1
    off = 1 if quarterly else 0

    def cum(ns, lob):                      # nonPAA(누적) + PAA(누적) for this LOB
        p = lobpos[lob]
        a = ns[off + step * p] if len(ns) > off + step * p else 0.0
        b = ns[step * 4 + off + step * p] if len(ns) > step * 4 + off + step * p else 0.0
        return a + b

    def comp(t, lob, *needles):            # nonPAA(누적) component value, this LOB
        idx = off + step * lobpos[lob]
        for r in t.rows:
            if not r:
                continue
            lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")
                   + (_norm(r[2]) if len(r) > 2 else "")).replace(" ", "")
            if any(n.replace(" ", "") in lab for n in needles):
                ns = _row_nums(r)
                if ns and len(ns) > idx:
                    return ns[idx]
        return None

    rt = totrow(rev, "보험수익")
    ct = totrow(cost, "보험비용")
    rrt = totrow(rerev, "재보험자에게서 회수한 금액에서 생기는 수익")
    rct = totrow(recost, "재보험자에게 지급된 보험료 배분액에서 생기는 비용")

    def leg(lob):
        """Full 수재/출재 decomposition for one GMM LOB → dict of item-suffix → value."""
        suje = cum(rt, lob) - cum(ct, lob)                      # item3
        csm = abs(comp(rev, lob, *_S2_CSM) or 0)                # item4
        ra = abs(comp(rev, lob, *_S2_RA) or 0)                  # item5
        exp = sum(comp(rev, lob, n) or 0 for n in _EXP_SPLIT)
        act = sum(comp(cost, lob, n) or 0
                  for n in ("발생한 보험금", "발생한 손해조사비", "발생한 유지비"))  # 발생투자관리비 제외
        yes = exp - act                                         # item6
        other_s = suje - csm - ra - yes                         # item7 (residual)
        chuljae = cum(rrt, lob) - cum(rct, lob)                 # item8
        recsm = -(comp(recost, lob, *_S2_CSM) or 0)             # item9
        rera = -(comp(recost, lob, *_S2_RA) or 0)               # item10
        re_act = comp(rerev, lob, "재보험수익, 발생한 보험금") or 0
        re_exp = (comp(recost, lob, "재보험비용, 예상 보험금") or 0) \
            + (comp(recost, lob, "재보험비용, 보고기간에 발생한 보험서비스비용") or 0)
        reyes = re_act - re_exp                                 # item11
        other_r = chuljae - recsm - rera - reyes                # item12
        return {2: suje + chuljae, 3: suje, 4: csm, 5: ra, 6: yes, 7: other_s,
                8: chuljae, 9: recsm, 10: rera, 11: reyes, 12: other_r}

    life = leg("생명보험")    # 생명재보험 → standard items 2-12
    jang = leg("장기보험")    # 장기재보험 → items 2-1 … 12-1

    out = {k: life[k] for k in range(4, 13)}                    # 4-12 direct (3/7/12/2/8 below)
    # 생명: feed assemble's _jang_* so it derives item2/3/8 the standard way
    out["_jang_rev"] = cum(rt, "생명보험")
    out["_jang_cost"] = cum(ct, "생명보험")
    out["_jang_rerev"] = cum(rrt, "생명보험")
    out["_jang_recost"] = cum(rct, "생명보험")
    out[14] = (cum(rt, "일반보험") - cum(ct, "일반보험")) \
        + (cum(rrt, "일반보험") - cum(rct, "일반보험"))    # 일반재보험

    _N = {2: "장기재보험 손익", 3: "장기재보험 수재손익", 4: "수재 CSM상각",
          5: "수재 위험조정 변동", 6: "수재 예실차", 7: "기타 장기재보험 수재손익",
          8: "장기재보험 출재손익", 9: "출재 CSM상각", 10: "출재 위험조정 변동",
          11: "출재 예실차", 12: "기타 장기재보험 출재손익"}
    out["_extra_items"] = [{"항목번호": f"{k}-1", "항목명": _N[k], "값": jang[k]}
                           for k in range(2, 13)]
    out["_extra_lob"] = jang[2]                                 # 장기재보험 손익 → RC
    return out  # 백만원 already


# ------------------------ 서울보증보험 (KR0150) ---------------------------- #
_SGI_LOB5 = ("보증", "해외", "상해", "자동차", "기타")
_SGI_LOB_IDX = {lob: i for i, lob in enumerate(_SGI_LOB5)}     # position within r[1:]


def _sgi_row(r):
    """r[1:] parsed POSITIONALLY -- blanks/dashes -> 0.0 IN PLACE, never skipped (unlike the
    shared _row_nums(), which drops them and shifts every later cell left).  SGI's LOB notes
    routinely render a true-zero LOB cell (원수 표의 상해/자동차, 수재 표의 보증) as '-'
    sitting between populated columns -- exactly the compression trap that silently wiped
    흥국화재 2026.2Q's LOB legs (fb9c9bf); this table has that shape in EVERY quarter, not
    just as an occasional glitch, so positional parsing is mandatory here, not defensive
    boilerplate."""
    return [(to_num(c) or 0.0) for c in r[1:]]


def _sgi_5col_header(t):
    hb = " ".join(" ".join(h) for h in t.header)
    return "항목" in hb and all(k in hb for k in _SGI_LOB5)


def _sgi_totrow(t):
    for r in t.rows:
        if _norm(r[0]).replace(" ", "") == "합계":
            vals = _sgi_row(r)
            if len(vals) >= len(_SGI_LOB5) + 1:      # 5 LOB + 합계
                return vals
    return None


def _sgi_re_legs(t):
    """note '24.재보험수익 및 비용' (ceded/outward) -- ONE table, 4 columns [보증,해외,기타,
    합계] (no 자동차/상해: SGI cedes no auto/injury risk out), with TWO '합계' rows under
    section headers '재보험수익:' (ceded recoveries, income) and '재보험서비스비용:' (ceded
    premium paid, cost).  Returns (rerev, recost) dicts keyed by LOB name, or (None, None)."""
    cols = [_norm(c) for c in t.header[0][1:-1]]     # ['보증','해외','기타'] (drop 항목/합계)
    section = None
    out = {}
    for r in t.rows:
        lab = _norm(r[0])
        if lab in ("재보험수익:", "재보험서비스비용:"):
            section = lab[:-1]
            continue
        if section and lab.replace(" ", "") == "합계":
            vals = _sgi_row(r)
            if len(vals) >= len(cols) + 1:
                out[section] = dict(zip(cols, vals))
    return out.get("재보험수익"), out.get("재보험서비스비용")


def extract_tier2_sgi(tables):
    """서울보증보험 (KR0150) -- Korea's sole comprehensive guarantee-insurance company.  It
    never had a dedicated handler (nor did the generic Format-A/B fallbacks match it), which
    is why item2/13/14 were ALL None for every quarter -- this is the LEG-COVERAGE gap
    inbox/parser ticket 20260829T1700Z asks to close for it.

    SGI's LOB taxonomy is NOT the schema's default 장기/자동차/일반 -- it splits ALL THREE
    flows (원수 direct / 수재 inward-assumed reinsurance / 재보험 ceded-outward) by product:
    보증(surety, its core book)/해외(overseas)/상해(injury)/자동차(auto)/기타(other).  There is
    NO 생명장기 leg at all (assemble() already sets item2=0.0 for a 손보 code).  item13
    (자동차손익) = the 자동차 column alone; item14 (일반손익) = 보증+해외+상해+기타 summed
    (이 저장소 컨벤션의 '일반' = non-auto/non-장기 P&C; SGI writes no 장기 book, so 일반
    legitimately absorbs everything but 자동차).

    Each LOB 손익 = 원수(rev−cost) + 수재(rev−cost) + 재보험(ceded rev−cost):
      - note 23 (보험수익): ONE table carries both a '..._원수' row and a '..._수재' row plus
        a 합계 row (원수+수재 COMBINED) -- only that 합계 row is read as the revenue side.
      - note 25 (보험서비스비용): TWO SEPARATE tables, '(1)원수' and '(2)수재' (identical row
        labels, so distinguished by 보증-column: SGI's own 보증 product is never reinsured
        FROM anyone else, so 수재's 보증 cell is always '-'/0 while 원수's is always large --
        confirmed every quarter 2025.1Q-2026.1Q).  BOTH totals must be summed: 수재 cost is a
        real, large flow (e.g. 15.9억원 자동차 in 2025.1Q alone) -- dropping it is what would
        leave item13 at roughly double its true (loss-making) magnitude, with the wrong sign.
      - note 24 (재보험수익 및 비용, ceded/outward): see `_sgi_re_legs`; its missing
        자동차/상해 columns contribute 0 to those two legs BY DESIGN (no ceded exposure), not
        by omission -- confirmed against the note's own column header, not inferred.

    Basis matters: note 25's 원수 손해조사비 sub-line genuinely differs 연결 vs 별도 (a
    consolidation-level adjustment on a claims-handling subsidiary), unlike notes 23/24 which
    are basis-invariant for this company -- `_prefer_ofs` is applied so the 별도(OFS) copy is
    read, matching the master's basis convention.

    Closure validated (2026-08-29, inbox/parser ticket 20260829T1700Z 답변) to <3백만원
    residual against item1 = item13+item14+item15−item16 for ALL FIVE quarters this shape
    covers (2025.1Q/2Q/3Q/4Q, 2026.1Q) via `parse_filing`+`assemble()` on the live pipeline,
    not hand arithmetic.  2026.2Q is OUT OF SCOPE: that filing restructured this disclosure
    into a deeper matrix note (원수/수재 grouped under '발행한 원보험계약'/'발행한
    재보험계약' parent columns, single '보험수익' row instead of separate 원수/수재 rows) --
    the same repo-wide 2026.2Q 반기 label-reconstruction other handlers' docstrings note (e.g.
    코리안리, 흥국화재).  The row-label signatures this handler matches on
    ('보험료배분접근법적용수익_원수' etc.) simply don't exist in that shape, so it falls
    through to {} rather than guess a mapping onto the new columns -- left for a follow-up
    ticket, not silently wrong."""
    pool = _prefer_ofs(tables)

    rev_t = None
    for t in pool:
        if not _sgi_5col_header(t):
            continue
        labs = [_norm(r[0]) if r else "" for r in t.rows]
        if any("보험료배분접근법적용수익_원수" in l for l in labs) \
                and any("보험료배분접근법적용수익_수재" in l for l in labs):
            rev_t = t
            break
    rev_tot = _sgi_totrow(rev_t) if rev_t is not None else None

    cost_cands = []
    for t in pool:
        if not _sgi_5col_header(t):
            continue
        labs = [_norm(r[0]) if r else "" for r in t.rows]
        if any(l == "당기발생사고보험금" for l in labs) and any(l == "손실부담부채관련손실" for l in labs):
            tot = _sgi_totrow(t)
            if tot is not None:
                cost_cands.append(tot)
    won_tot = next((tot for tot in cost_cands if tot[_SGI_LOB_IDX["보증"]] != 0), None)
    su_tot = next((tot for tot in cost_cands if tot[_SGI_LOB_IDX["보증"]] == 0), None)

    re_t = None
    for t in pool:
        if _sgi_5col_header(t):
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not ("보증" in hb and "해외" in hb and "기타" in hb
                and "자동차" not in hb and "상해" not in hb):
            continue
        labs = [_norm(r[0]) if r else "" for r in t.rows]
        if any(l == "재보험수익:" for l in labs) and any(l == "재보험서비스비용:" for l in labs):
            re_t = t
            break
    rerev, recost = _sgi_re_legs(re_t) if re_t is not None else (None, None)

    if not (rev_tot and won_tot and su_tot and rerev is not None and recost is not None):
        return {}

    def lobval(lob):
        i = _SGI_LOB_IDX[lob]
        rev = rev_tot[i]
        cost = won_tot[i] + su_tot[i]
        rr = rerev.get(lob, 0.0) or 0.0
        rc = recost.get(lob, 0.0) or 0.0
        return rev - cost + rr - rc

    out = {13: lobval("자동차") / 1000.0,                       # 천원 -> 백만원
           14: sum(lobval(l) for l in ("보증", "해외", "상해", "기타")) / 1000.0}
    return out


# -------------------- 구형식 (pre-2025.2Q) 손보 OLD note --------------------- #
# Before the standardized 2025.2Q disclosure, several insurers used a "구분=행 / LOB=열" note
# (DB "6. 보험수익 및 비용"; 삼성·현대 "보험서비스결과" 구분-rows).  Two structural variants —
#   • 삼성-style: 보험수익/비용/재보 sections are LABEL-rows inside merged tables; 예실차 = combined
#     "예상보험금 및 보험서비스비용" − "발생보험금 및 발생보험서비스비용"; LOBs 장기/자동차/일반 (no 생명).
#   • DB-style: each leg is a SEPARATE caption-identified table (6-1…6-4); 예실차 = 4-way split;
#     LOBs 장기/일반/자동차/생명 (생명 column EXCLUDED per gold); 원수 total = 소계 (before <수재>).
# Both share: 누적(YTD) column, header-driven LOB order, and the same robust LOB-total reader that
# survives dropped zero-LOB columns in the (often irregular) 재보 합계 rows.  Gold-validated against
# DB 2024.2Q + 삼성화재 2024.2Q.  Basis 별도 (smallest grand total per leg).  코리안리 old (장기/생명
# dual) and 흥국 old (보험종류별) use other layouts and are NOT handled here.
_OLD_LOBS = ("장기", "자동차", "일반", "생명")
_OLD_SEC = {"보험수익": "REV", "보험서비스비용": "COST", "보험비용": "COST",
            "재보험수익": "REREV", "재보험비용": "RECOST"}
_OLD_PRIOR = {"전기", "전반기", "전분기", "전기말", "전년", "전년동기"}
_CSM_OLD = ("보험계약마진상각", "보험계약마진 상각")
_RA_OLD = ("위험조정상각", "위험조정의 변동", "비금융위험에 대한 위험조정")
_EXP4_OLD = ("예상보험금", "예상유지비", "예상손해조사비", "예상투자관리비")
_ACT4_OLD = ("발생보험금", "발생직접유지비", "손해조사비", "투자관리비")


def _old_prior(tables, i):
    cap = _norm(tables[i].caption or "")
    if ("(전)" in cap) or (("전반기" in cap or "전기" in cap or "전분기" in cap) and "당" not in cap):
        return True
    for j in (i - 1, i - 2):
        if 0 <= j < len(tables):
            tj = tables[j]
            f = _norm(tj.rows[0][0]) if (tj.rows and tj.rows[0]) else ""
            # marker rows may be bracketed, e.g. '<전반기>' — substring match, but never when a
            # 당기 marker ('<당반기>'/'당기') is what precedes the table.
            if len(tj.rows) <= 1 and f and "당" not in f and any(p in f for p in _OLD_PRIOR):
                return True
    return False


def _old_order(t):
    hb = _header_blob(t)
    return [k for _, k in sorted((hb.find(x), x) for x in _OLD_LOBS if hb.find(x) >= 0)]


def _old_rv(rows, idx, *needles):
    for r in rows:
        lab = _norm(r[0]).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles):
            ns = _row_nums(r)
            if ns and len(ns) > idx:
                return ns[idx]
    return None


def _old_total(rows, before=None):
    end = len(rows)
    if before:
        for k, r in enumerate(rows):
            if _norm(r[0]) == before:
                end = k
                break
    for r in rows[:end]:
        if _norm(r[0]).replace(" ", "") in ("합계", "소계"):
            return _row_nums(r)
    return None


def _old_present(rows, order):
    """PAA LOBs materially non-zero — from the fullest aligned row (relative threshold)."""
    full = (len(order) + 1) * 2
    best = None
    for r in rows:
        ns = _row_nums(r)
        if ns and len(ns) >= full and (best is None or len(ns) > len(best)):
            best = ns
    pres = set()
    if best:
        thr = max(1.0, 0.005 * abs(best[-1]))
        for i, lob in enumerate(order):
            if i and abs(best[2 * i + 1]) > thr:
                pres.add(lob)
    return pres


def _old_lobcum(total_nums, order, pres, st=2):
    """누적 per LOB from a possibly-short total row: 장기 left, 합계 right, middle→present PAA.
    st = cell width per LOB (2 = paired [3개월,누적] 반기/3Q; 1 = single-col Q1/연차)."""
    res = {lob: 0.0 for lob in order}
    if not total_nums:
        return res
    full = (len(order) + 1) * st
    if len(total_nums) >= full:
        for i, lob in enumerate(order):
            res[lob] = total_nums[(st - 1) + i * st]
        return res
    res[order[0]] = total_nums[st - 1] if len(total_nums) > st - 1 else 0.0
    if st == 1:                       # single-col short row: positional best-effort
        for i, lob in enumerate(order):
            if i < len(total_nums) - 1:
                res[lob] = total_nums[i]
        return res
    mid = total_nums[2:-2]
    midc = [mid[2 * j + 1] for j in range(len(mid) // 2)]
    for lob in order[1:]:
        if lob in pres and midc:
            res[lob] = midc.pop(0)
    return res


def _old_sections(t):
    out = {}
    cur = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in _OLD_SEC and not _row_nums(r):
            cur = _OLD_SEC[lab]
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(r)
    return out


def _old_assemble_jang(rev, cost, rerev, recost, order, combined_exp, st=2):
    """Common item math for a single 장기-GMM company (삼성·DB-style).  Returns the 4/5/6/9/10/11
    direct items + LOB totals via robust reader.  st = cell width per LOB (2 = paired 반기/3Q;
    1 = single-col Q1/연차 — then the 장기 component sits at col0 not col1)."""
    z = lambda v: v or 0.0
    idx = st - 1
    csm = abs(z(_old_rv(rev, idx, *_CSM_OLD)))
    ra = abs(z(_old_rv(rev, idx, *_RA_OLD)))
    if combined_exp:
        exp = z(_old_rv(rev, idx, "예상보험금 및 보험서비스비용", "보고기간에 발생한 보험서비스비용"))
        act = z(_old_rv(cost, idx, "발생보험금 및 발생보험서비스비용", "발생한 보험금 및 그 밖"))
    else:
        exp = sum(z(_old_rv(rev, idx, n)) for n in _EXP4_OLD)
        act = sum(z(_old_rv(cost, idx, n)) for n in _ACT4_OLD)
    out = {4: csm, 5: ra, 6: exp - act,
           9: -z(_old_rv(recost, idx, *_CSM_OLD)), 10: -z(_old_rv(recost, idx, *_RA_OLD))}
    re_act = z(_old_rv(rerev, idx, "발생출재보험금", "재보험수익, 발생한 보험금"))
    re_exp = z(_old_rv(recost, idx, "예상출재보험금", "재보험비용, 예상 보험금"))
    out[11] = re_act - re_exp
    re_present = _old_present(rerev, order) | _old_present(recost, order)
    RC = _old_lobcum(_old_total(rev), order, _old_present(rev, order), st)
    CC = _old_lobcum(_old_total(cost), order, _old_present(cost, order), st)
    RR = _old_lobcum(_old_total(rerev), order, re_present, st)
    RX = _old_lobcum(_old_total(recost), order, re_present, st)
    out["_jang_rev"] = RC["장기"]; out["_jang_cost"] = CC["장기"]
    out["_jang_rerev"] = RR["장기"]; out["_jang_recost"] = RX["장기"]
    for lob, it in (("자동차", 13), ("일반", 14)):
        if lob in order:
            out[it] = (RC[lob] - CC[lob]) + (RR[lob] - RX[lob])
    return out


def _old_samsung(tables):
    """삼성-style: section-label rows inside merged tables, combined 예상, LOBs w/o 생명."""
    legs_all = {}
    order = None
    st = 2
    for i, t in enumerate(tables):
        hb = _header_blob(t)
        if not hb.startswith("구분") or "장기" not in hb:
            continue
        # reject non-flat LOB layouts: 메리츠 nests LOBs under 국내/해외 and 배당요소 splits, so the
        # 장기 column isn't where header order implies — leave those to Format-B.
        if "생명" in hb or ("국내" in hb and "해외" in hb) or "배당요소" in hb or _old_prior(tables, i):
            continue
        secs = _old_sections(t)
        if not secs:
            continue
        blob = " ".join(_norm(r[0]) for r in t.rows if r)
        if not any(n in blob for n in _CSM_OLD) and not any(k in secs for k in ("COST", "REREV")):
            continue
        if order is None and any(k in secs for k in ("REV", "COST")):
            order = _old_order(t)
            st = 2 if ("3개월" in hb and "누적" in hb) else 1
        for leg, rows in secs.items():
            legs_all.setdefault(leg, []).append(rows)
    if order is None or not all(k in legs_all for k in ("REV", "COST", "REREV", "RECOST")):
        return {}
    legs = {leg: min(lst, key=lambda rs: abs((_old_total(rs) or [float("inf")])[-1]))
            for leg, lst in legs_all.items()}
    return _old_assemble_jang(legs["REV"], legs["COST"], legs["REREV"], legs["RECOST"],
                              order, combined_exp=True, st=st)


def _old_db(tables):
    """DB-style: separate caption-identified legs (6-1…6-4), 4-way 예상.  Anchor the 별도 block
    (3 LOBs, NO 생명 column = DB생명 subsidiary); LOB total = 합계 row (원수+수재, 수재 sits in 일반)."""
    def leg_of(t):
        # DB caption carries a long prefix "6. 보험수익 및 비용과 재보험수익 및 비용" before the
        # sub-caption, so match the SPECIFIC sub-phrase (or the 재보 tables' row0 markers).
        cap = _norm(t.caption or "").replace(" ", "")
        r0 = _norm(t.rows[0][0]) if (t.rows and t.rows[0]) else ""
        if "재보험계약의재보험수익" in cap or r0 == "발생출재보험금":
            return "REREV"
        if "재보험계약의재보험비용" in cap or r0 == "예상출재보험금":
            return "RECOST"
        if "발행한보험계약의보험비용" in cap:
            return "COST"
        if "발행한보험계약의보험수익" in cap:
            return "REV"
        if r0 == "<원수>":
            blob = "".join(_norm(r[0]) for r in t.rows if r)
            if "발생보험금" in blob and "발생사고부채" in blob:
                return "COST"
            if "예상보험금" in blob and "보험계약마진상각" in blob:
                return "REV"
        return None

    # DB files this note TWICE: 연결 (header carries a 생명 column = the DB생명 subsidiary) and
    # 별도 (3 LOBs, NO 생명).  FS-API Tier-1 is OFS (별도), so anchor to the 별도 block — the 연결
    # 생명 column would otherwise leak the subsidiary AND the per-LOB intra-group reinsurance
    # elimination, short-changing item14 (일반).  Prefer 별도; fall back to 연결.
    sep, con = {}, {}
    order_sep = order_con = None
    st = 2
    for i, t in enumerate(tables):
        hb = _header_blob(t)
        if not hb.startswith("구분") or "자동차" not in hb:
            continue
        if _old_prior(tables, i):
            continue
        leg = leg_of(t)
        if leg is None:
            continue
        if "생명" in hb:
            con.setdefault(leg, t.rows)
            if order_con is None:
                order_con = _old_order(t)
                st = 2 if ("3개월" in hb and "누적" in hb) else 1
        else:
            sep.setdefault(leg, t.rows)
            if order_sep is None:
                order_sep = _old_order(t)
                st = 2 if ("3개월" in hb and "누적" in hb) else 1
    if all(k in sep for k in ("REV", "COST", "REREV", "RECOST")):
        legs, order = sep, order_sep
    elif all(k in con for k in ("REV", "COST", "REREV", "RECOST")):
        legs, order = con, order_con
    else:
        return {}
    rev, cost, rerev, recost = legs["REV"], legs["COST"], legs["REREV"], legs["RECOST"]
    z = lambda v: v or 0.0
    idx = st - 1
    out = {4: abs(z(_old_rv(rev, idx, *_CSM_OLD))), 5: abs(z(_old_rv(rev, idx, *_RA_OLD)))}
    out[6] = sum(z(_old_rv(rev, idx, n)) for n in _EXP4_OLD) - sum(z(_old_rv(cost, idx, n)) for n in _ACT4_OLD)
    out[9] = -z(_old_rv(recost, idx, *_CSM_OLD))
    out[10] = -z(_old_rv(recost, idx, *_RA_OLD))
    out[11] = z(_old_rv(rerev, idx, "발생출재보험금")) - z(_old_rv(recost, idx, "예상출재보험금"))
    re_present = _old_present(rerev, order) | _old_present(recost, order)

    def grand_or_sub(rows):
        # LOB-total row = 원수+수재 (DB's 수재 inward reinsurance sits only in 일반, so the 원수
        # 소계 alone under-states 일반).  Prefer the LAST full-width 합계 (after the 수재 소계);
        # the single-total 재보 tables carry no 합계 → first 소계/합계.
        g = None
        for r in rows:
            if _norm(r[0]).replace(" ", "") == "합계":
                g = r
        if g is None:
            for r in rows:
                if _norm(r[0]).replace(" ", "") in ("소계", "합계"):
                    g = r
                    break
        return _row_nums(g) if g else None
    RC = _old_lobcum(grand_or_sub(rev), order, _old_present(rev, order), st)
    CC = _old_lobcum(grand_or_sub(cost), order, _old_present(cost, order), st)
    RR = _old_lobcum(grand_or_sub(rerev), order, re_present, st)
    RX = _old_lobcum(grand_or_sub(recost), order, re_present, st)
    out["_jang_rev"] = RC["장기"]; out["_jang_cost"] = CC["장기"]
    out["_jang_rerev"] = RR["장기"]; out["_jang_recost"] = RX["장기"]
    for lob, it in (("자동차", 13), ("일반", 14)):
        out[it] = (RC[lob] - CC[lob]) + (RR[lob] - RX[lob])
    return out


def extract_tier2_old(tables):
    """Dispatcher for the pre-2025.2Q 구분-rows note: 삼성-style first (no 생명 col), then DB-style
    (생명+자동차).  Returns {} when neither layout matches (caller falls back to Format-A/B)."""
    # item4 (CSM상각) is always materially non-zero for a 장기 insurer; a ~0 means the columns
    # were mis-read (wrong layout) → reject so the caller falls back to Format-A/B.
    out = _old_samsung(tables)
    if out and out.get(4) and abs(out[4]) > 1:
        return out
    out = _old_db(tables)
    if out and out.get(4) and abs(out[4]) > 1:
        return out
    return {}


# ----------------------------- NH 손보 (KR0032) ---------------------------- #
def _nh_gmm_incurred4(tables):
    """Locate the (3) GMM-only (장기손해보험) '가. 잔여보장부채(자산) 및 발생사고부채(자산)의
    변동내역' rollforward's CURRENT-period table (the caption also covers a following 전(반/분)
    기 comparative table with identical row labels -- take the FIRST match, which document
    order puts before the comparative one) and return its '발생보험금 및 기타보험서비스비용'
    row's LC-EXCLUDED sum: 손실요소 외 column + 발생사고부채 column, i.e. dropping the row's
    own 손실요소 column.  See extract_tier2_nh docstring for why that column is dropped rather
    than kept.  Matched by exact label (not substring) so the '...등의 지급' cash-paid row
    later in the same table is never picked up.  Returns None (never guesses) when the note,
    row, or expected 5-column shape [손실요소외, 손실요소, 소계, 발생사고부채, 합계] isn't
    found -- caller leaves item6 unset in that case."""
    note3 = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "보험료배분접근법을적용하지않는보험계약" not in cap or "장기손해보험" not in cap:
            continue
        if not any(_norm(r[0]) == "발생보험금 및 기타보험서비스비용" for r in t.rows):
            continue
        note3 = t
        break
    if note3 is None:
        return None
    for r in note3.rows:
        if _norm(r[0]) != "발생보험금 및 기타보험서비스비용":
            continue
        # Raw-indexed on r[1:6] (NOT _row_nums, which SKIPS '-' cells) -- mirrors the fix
        # already applied to _nh_gmm_re_incurred (item11, the reinsurance-leg twin of this
        # function): a blank/dash in any of the 5 columns would otherwise silently shift
        # this fixed [손실요소외, 손실요소, 소계, 발생사고부채, 합계] layout and misalign
        # the remaining values.  '-' reads as 0.0.
        if len(r) < 6:
            return None
        cells = []
        for c in r[1:6]:
            v = to_num(c)
            cells.append(v if v is not None else 0.0)
        excl_lc, _lc, _lrc_sub, lic, _total = cells
        return excl_lc + lic
    return None


def _nh_gmm_re_incurred(tables):
    """Mirror of _nh_gmm_incurred4 for the REINSURANCE leg (item11).  Locates the (5) GMM-only
    (장기비례재보험) '가. 잔여보장자산(부채) 및 발생사고자산(부채)의 변동내역' rollforward's
    CURRENT-period table (same first-match-wins rule as note3: the caption also covers a
    following 전(반/분)기 comparative table with identical row labels) and returns its '발생
    재보험금 및 기타재보험수익' row's LC-EXCLUDED sum: 손실회수요소 외 column + 발생사고자산(부채)
    column, dropping the row's own 손실회수요소 column.

    Cells are read via to_num() directly on r[1:6] (NOT via _row_nums, which SKIPS '-' cells --
    since 손실회수요소외 is '-' in every observed quarter, _row_nums would silently shift the
    fixed 5-column layout and misalign the remaining values).  '-' reads as 0.0.

    Same LC-exclusion boundary as _nh_gmm_incurred4, independently re-verified for THIS leg
    (not assumed from symmetry) via inbox/parser/
    20260828T1900Z__orchestrator__KR0032__reinsurance_yesilcha_item11.md: note8 (보험영업이익
    내역)'s '손실회수요소배분' row -- shown as its own peer line on BOTH the 재보험수익 and
    재보험비용 sections, never nested inside either -- matches this row's 손실회수요소 column
    within KRW 1mm rounding in 11/11 quarters this note format exists (2023.4Q-2026.2Q; see
    scripts/_probes/nh_yesilcha_reinsurance_boundary_probe.py, LCok column).  Same IFRS17
    mechanics as the direct leg apply: a loss-recovery-component allocation draws down the
    pre-existing loss-recovery component and would double-count if left inside the incurred
    figure a second time.

    Returns None (never guesses) when the note, row, or expected 5-column shape isn't found --
    caller leaves item11 unset in that case."""
    note5 = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "보험료배분접근법을적용하지않는재보험계약" not in cap or "장기비례재보험" not in cap:
            continue
        if not any(_norm(r[0]) == "발생재보험금 및 기타재보험수익" for r in t.rows):
            continue
        note5 = t
        break
    if note5 is None:
        return None
    for r in note5.rows:
        if _norm(r[0]) != "발생재보험금 및 기타재보험수익":
            continue
        if len(r) < 6:
            return None
        cells = []
        for c in r[1:6]:
            v = to_num(c)
            cells.append(v if v is not None else 0.0)
        excl_lc, _lc, _sub, incurred_asset, _total = cells
        return excl_lc + incurred_asset
    return None


def extract_tier2_nh(tables):
    """NH농협손해 (KR0032): 보험손익 only as a single whole-company note '(N) 보험영업이익의
    내역' (note number drifts by year, matched on caption+row content, not the number) — NO
    장기/일반/자동차 LOB columns.  Reads 누적(YTD) column (분기/반기 note prints [당기 3개월,
    당기 누적, 전기 …]; annual is single 당기).  재보험비용 section header drifts: annual
    '재보험비용' vs 분기/반기 '재보험서비스비용'.  Items 13/14 (자동차/일반) are data-absent — NH
    discloses no LOB-split income note, so item3/item8 carry the WHOLE-company insurance
    result (this is what lets RC close).

    item6 (원수 예실차, GMM-only) IS separable — see `_nh_gmm_incurred4` above.  Settled by
    DATA after two wrong closes (inbox/parser/
    20260828T1400Z__orchestrator__KR0032__yesilcha_via_gmm_rollforward_total_column.md):
    round 1 folded 4종-밖 items (취득CF상각/발생사고부채 이행현금흐름 변동/손실요소 인식및
    환입) into 발생; round 2 used a LIABILITY BALANCE column (발생사고부채, 351,114) as if it
    were a P&L incurred amount.  This note's own '예상 보험금 및 기타서비스비용' row (revenue
    section) is already GMM-only — the note's 보험료배분접근법 보험수익 sits on its OWN row,
    so the 5 rows above it (예상보험금/위험조정변동/CSM상각/취득CF상각/손실요소배분) sum to the
    (3) rollforward's GMM-only 보험수익 (population identity, re-verified below).  The
    matching GMM-only 발생(incurred) figure has no separate P&L-note home — it only exists
    inside the (3) rollforward's '발생보험금 및 기타보험서비스비용' row, split across
    [손실요소외, 손실요소, 소계, 발생사고부채, 합계] columns.

    The row's 손실요소 (loss-component) column is EXCLUDED from item6 — i.e. item6 uses
    (손실요소외 + 발생사고부채), NOT the row's 합계.  Both candidates close the row's own
    arithmetic trivially (that's just algebra on a 5-column row, not evidence either way),
    so the boundary was settled by three independent checks, each re-run across every
    quarter this note format exists (2023.4Q-2026.2Q, 11 filings — 2023 Q1-3 predate this
    note format entirely and are skipped, not guessed):
      1. THIS note discloses '손실요소배분' as its OWN peer row — not nested inside either
         예상 보험금 (revenue side) or 발생 보험금 (whole-company cost side) — on both the
         revenue and cost sections.  Its value exactly equals the (3) rollforward's 손실요소
         column entry for the 발생보험금 row in 10 of 11 quarters (2025.2Q off by KRW 1mm,
         rounding) — the identical transaction, disclosed twice via two different
         presentations (a peer line here, a column memo there).  Since this note already
         keeps 예상 보험금 clean of it, symmetry requires 발생 to exclude it too.
      2. Existing codebase precedent (extract_tier2_aia, same file): loss-component-family
         rows (손실요소의 전입 / 손실요소 인식 및 환입 / 발생사고요소조정) are routed to
         item7, never item6, everywhere this schema has met them before.
      3. IFRS17 mechanics: a loss-component allocation draws down the pre-existing onerous-
         contract loss component and is explicitly excluded from being recognised as
         발생보험금/기타보험서비스비용 P&L expense a second time — the (3) rollforward row's
         합계 column bundles it back in only because that table is a LIABILITY view combining
         both movements under one row label; the P&L-comparable figure is the column subset
         that excludes it.
    Population identity (own probe, independently re-derived, not reused from the ticket):
    (3) rollforward 보험수익 합계 == this note's 보험수익 소계 minus its 보험료배분접근법
    보험수익 row, exact within KRW 2mm rounding in all 11 quarters — confirms the two notes
    cover the same GMM population before combining their figures.

    item11 (재보험 예실차, GMM-only) is ALSO separable — see `_nh_gmm_re_incurred` above.  The
    (5) reinsurance rollforward is structurally symmetric to (3) (same [손실회수요소외,
    손실회수요소, 소계, 발생사고자산, 합계] 5-column row shape), but the boundary was NOT
    copied from item6 on the strength of that symmetry alone — it was independently re-run
    (inbox/parser/20260828T1900Z__orchestrator__KR0032__reinsurance_yesilcha_item11.md):
    note8's '손실회수요소배분' row (again a peer line on both 재보험수익/재보험비용 sections,
    never nested) matches the (5) rollforward's LC column for the '발생재보험금 및 기타재보험
    수익' row within KRW 1mm in 11/11 quarters (2023.4Q-2026.2Q) — same identity, same
    conclusion: exclude the LC column from the incurred-recovery figure.  The population
    identity also re-verified independently: note's 재보험비용 소계 minus its 보험료배분접근법
    재보험서비스비용 row == the (5) rollforward's '재보험서비스비용' row, exact within KRW 2mm
    in all 11 quarters.

    SIGN IS REVERSED FROM item6 — 출재(ceded) runs the opposite direction through this note's
    OWN section layout, not just a business-direction intuition.  item8 (생명장기 재보험손익)
    = jang_rerev(재보험수익 소계) − jang_recost(재보험비용 소계) [see assemble()], i.e. 재보험비용
    is the SUBTRACTED role — the same role recsm/rera already occupy, which is why item9/item10
    are stored NEGATED (out[9]=-abs(recsm)).  '예상재보험비용' (exp4_re) sits in that same
    재보험비용/subtracted section.  The (5) rollforward's '발생재보험금 및 기타재보험수익' row,
    by contrast, is nested under note (5)'s OWN '재보험수익' parent line — the ADDED role
    (matching jang_rerev), mirroring how note3's '발생보험금' row for item6 was nested under
    '보험서비스비용' (jang_cost's role, the SUBTRACTED side of item3=jang_rev−jang_cost).  So
    item6's pattern is really "(rev-role term) − (cost-role term)"; for item6 that happens to
    read 예상−발생 because 예상 IS the rev-role term there, but for item11 the rev-role term is
    발생 (재보험수익-side) and the cost-role term is 예상 (재보험비용-side) — so item11 =
    발생(excl LC) − 예상, REVERSED from item6's order.  Cross-checked against
    orchestrator's own un-vetted hand calc (8,802−13,526=△4,724 for 2026.2Q, flagged in the
    ticket as "reference only, don't trust — 3 wrong closes on item6 came from exactly this
    kind of unverified arithmetic"): the correctly-signed value is the negation of that,
    +4,724 — the naive copy-item6's-formula-literally sign is the wrong one."""
    note = None
    for t in tables:
        labs = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
        if ("보험영업이익" in (t.caption or "")) and "보험계약마진 상각" in labs \
                and "보험료배분접근법 보험수익" in labs:
            note = t
            break
    if note is None:
        return {}
    col = _ytd_col(note)
    SEC = {"보험수익": "보험수익", "보험서비스비용": "보험서비스비용",
           "재보험수익": "재보험수익", "재보험비용": "재보험비용",
           "재보험서비스비용": "재보험비용"}

    def colval(r):
        ns = _row_nums(r)
        if not ns:
            return None
        return ns[col] if len(ns) > col else ns[0]

    section = None
    vals = {}
    for r in note.rows:
        lab0 = _norm(r[0])
        lab1 = _norm(r[1]) if len(r) > 1 else ""
        if lab0 in SEC:
            section = SEC[lab0]
        lab = (lab0 + " " + lab1).replace(" ", "")
        v = colval(r)
        if v is None:
            continue
        if section == "보험수익":
            if "보험계약마진상각" in lab:
                vals["csm"] = v
            elif "위험조정변동" in lab:
                vals["ra"] = v
            elif "예상보험금및기타서비스비용" in lab:
                vals["exp4"] = v
        elif section == "재보험비용":
            if "보험계약마진상각" in lab:
                vals["recsm"] = v
            elif "위험조정변동" in lab:
                vals["rera"] = v
            elif "예상재보험비용" in lab:
                vals["exp4_re"] = v
    out = {}
    if "csm" in vals:
        out[4] = abs(vals["csm"])
    if "ra" in vals:
        out[5] = abs(vals["ra"])
    if "recsm" in vals:
        out[9] = -abs(vals["recsm"])
    if "rera" in vals:
        out[10] = -abs(vals["rera"])
    if "exp4" in vals:
        inc4 = _nh_gmm_incurred4(tables)
        if inc4 is not None:
            out[6] = vals["exp4"] - inc4
    if "exp4_re" in vals:
        inc_re = _nh_gmm_re_incurred(tables)
        if inc_re is not None:
            # REVERSED order from item6 (발생 − 예상, not 예상 − 발생) — see docstring
            # "SIGN IS REVERSED FROM item6" for why.
            out[11] = inc_re - vals["exp4_re"]
    # item 13/14 (자동차/일반) still data-absent — see docstring.

    def subtotal(after_section):
        sec = None
        for r in note.rows:
            l0 = _norm(r[0])
            if l0 in SEC:
                sec = SEC[l0]
            if l0 == "소계" and sec == after_section:
                v = colval(r)
                if v is not None:
                    return v
        return None
    out["_jang_rev"] = subtotal("보험수익")
    out["_jang_cost"] = subtotal("보험서비스비용")
    out["_jang_rerev"] = subtotal("재보험수익")
    out["_jang_recost"] = subtotal("재보험비용")
    # NH discloses the 보험수익/보험서비스비용 SUBTOTALS (→ item3 = rev − cost in assemble) but
    # NOT the 예상-vs-발생 claim split, so 예실차(item6/11) is NOT separable.  The combined
    # residual (원수손익 − CSM상각 − RA) is pushed into 기타(item7/12) by the generic closure in
    # assemble() — owner decision 2026-06-08 (do NOT fabricate a 예실차 split).
    return out  # 백만원 already


# ---------------------------- 롯데 손보 (KR0003) --------------------------- #
_LOTTE_SEC = {"보험수익": "rev", "보험비용": "cost",
              "재보험수익": "re_rev", "재보험비용": "re_cost"}


def _extract_tier2_lotte_combined(tables):
    """롯데 보험손익 note — quarter-agnostic, section-aware.

    The note structure changed across years: FY2025 splits it into two tables
    (30. 보험손익 + 31. 재보험손익) while FY2023/FY2024 combine all four sections into one
    (31. 보험손익 및 재보험손익).  Both share identical [장기, 일반, 자동차, 합계] columns and
    row labels, with empty-value section-header rows (보험수익/보험비용/재보험수익/재보험비용).
    So instead of matching the note NUMBER (30./31.) and 기수 (<제81(당)기>), we collect every
    current-period table whose caption mentions 보험손익 and walk its rows by section.  This
    removes the fiscal-period hardcoding and makes FY2023/FY2024 extract like FY2025."""
    def is_cand(t):
        cap = (t.caption or "")
        if "보험손익" not in cap:
            return False
        if "(전)기" in cap.replace(" ", ""):       # skip the prior-period table
            return False
        h = " ".join(" ".join(_norm(c) for c in hr) for hr in t.header)
        return all(k in h for k in ("장기", "일반", "자동차")) and not _is_rollforward(t)

    sect = {}        # secname -> [(label_nospace, nums)], first occurrence wins
    seen_caps = set()
    for t in tables:
        if not is_cand(t) or (t.caption or "") in seen_caps:
            continue
        seen_caps.add(t.caption or "")
        section = None
        for r in t.rows:
            lab0 = _norm(r[0])
            nums = _row_nums(r)
            sk = _LOTTE_SEC.get(lab0)
            if sk is not None and not nums:          # section-header row (no values)
                section = sk
                continue
            if section is None or not nums:
                continue
            sect.setdefault(section, []).append((lab0.replace(" ", ""), nums))
    if not all(k in sect for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}

    def g(sec, *needles, exclude=()):
        for lab, nums in sect.get(sec, []):
            if any(n.replace(" ", "") in lab for n in needles) \
                    and not any(e.replace(" ", "") in lab for e in exclude):
                return nums
        return None

    def tot(sec):
        for lab, nums in sect.get(sec, []):
            if lab.startswith("총"):
                return nums
        return None

    out = {}
    csm = g("rev", "보험계약마진 상각")
    ra = g("rev", "위험조정 변동")
    rev_exp = g("rev", "예상보험금 및 예상기타보험서비스비용")
    cost_act = g("cost", "발생보험금 및 기타서비스비용")
    re_csm = g("re_cost", "보험계약마진 상각")
    re_ra = g("re_cost", "위험조정 변동")
    re_rev_act = g("re_rev", "발생보험금 및 기타재보험수익")
    re_cost_exp = g("re_cost", "회수예상 보험금 및 기타보험서비스비용")
    if csm:
        out[4] = abs(csm[0])
    if ra:
        out[5] = abs(ra[0])
    if rev_exp and cost_act:
        out[6] = rev_exp[0] - cost_act[0]
    if re_csm:
        out[9] = -abs(re_csm[0])
    if re_ra:
        out[10] = -abs(re_ra[0])
    if re_rev_act and re_cost_exp:
        out[11] = abs(re_rev_act[0]) - abs(re_cost_exp[0])

    rev_tot = tot("rev")
    cost_tot = tot("cost")
    rerev_tot = tot("re_rev")
    recost_tot = tot("re_cost")
    if not all(x and len(x) >= 4 for x in (rev_tot, cost_tot, rerev_tot, recost_tot)):
        return out

    def net(i):
        return rev_tot[i] - cost_tot[i] + rerev_tot[i] - recost_tot[i]
    out[14] = net(1)
    out[13] = net(2)
    out["_jang_rev"] = rev_tot[0]
    out["_jang_cost"] = cost_tot[0]
    out["_jang_rerev"] = rerev_tot[0]
    out["_jang_recost"] = recost_tot[0]
    return out  # 백만원 already


# ---- 롯데 NEW layouts: caption-stripped combined (2024.2Q/3Q) + per-segment split
#      (2025.3Q/2026.1Q).  Driven by table content / row-0 sub-headings, not the <P> caption
#      (DART clobbers it to '관계기업…' / '<제N(당)기 반기>').  누적-aware for interim doublings. ----
def _lotte_lob_pos(t):
    """Numeric-cell index per LOB ({jang,ilban,auto,tot}) for a Lotte component table,
    누적-aware.  None if the 장기/일반/자동차 header isn't present."""
    hdr_lob, has_cum = None, False
    for hr in t.header:
        cells = [_norm(c).replace(" ", "") for c in hr if _norm(c)]
        joined = "".join(cells)
        if "장기" in joined and "자동차" in joined and hdr_lob is None:
            hdr_lob = cells
        if "누적" in joined:
            has_cum = True
    if not hdr_lob:
        return None
    lobs = []
    for c in hdr_lob:
        if c.startswith("장기"):
            lobs.append("jang")
        elif c.startswith("일반"):
            lobs.append("ilban")
        elif c.startswith("자동차"):
            lobs.append("auto")
        elif "합계" in c or c.startswith("계"):
            lobs.append("tot")
    if "jang" not in lobs:
        return None
    step, off = (2, 1) if has_cum else (1, 0)   # 누적 = 2nd of each (3개월, 누적)
    return {lob: k * step + off for k, lob in enumerate(lobs)}


def _lotte_row_val(rows, idx, *needles, exclude=()):
    for r in rows:
        lab = (_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles) \
                and not any(e.replace(" ", "") in lab for e in exclude):
            nums = _row_nums(r)
            if len(nums) > idx:
                return nums[idx]
    return None


def _lotte_from_sections(sect):
    """Shared assembler.  sect: secname -> list[(rows, lob_pos)].  Emits 4,5,6,9,10,11,13,14
    + _jang_* with the legacy section-walker formulas."""
    def comp(sec, *needles):
        for rows, pos in sect.get(sec, []):
            v = _lotte_row_val(rows, pos["jang"], *needles)
            if v is not None:
                return v
        return None

    out = {}
    # First needle of each pair = 롯데 고유 label (2025.3Q+ split / legacy combined);
    # second = DART 표준양식 label (2025.2Q standardized component note).
    csm = comp("rev", "보험계약마진 상각", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    ra = comp("rev", "위험조정 변동", "비금융위험에 대한 위험조정의 변동분")
    rev_exp = comp("rev", "예상보험금 및 예상기타보험서비스비용", "보고기간에 발생한 보험서비스비용")
    cost_act = comp("cost", "발생보험금 및 기타서비스비용",
                    "발생한 보험금 및 그 밖의 발생한 보험서비스비용")
    re_csm = comp("re_cost", "보험계약마진 상각", "서비스의 이전으로 당기손익에 인식한 보험계약마진")
    re_ra = comp("re_cost", "위험조정 변동", "비금융위험에 대한 위험조정의 변동분")
    re_rev_act = comp("re_rev", "발생보험금 및 기타재보험수익")
    re_cost_exp = comp("re_cost", "회수예상 보험금 및 기타보험서비스비용",
                       "보고기간에 발생한 보험서비스비용")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev_act is not None and re_cost_exp is not None:
        out[11] = abs(re_rev_act) - abs(re_cost_exp)

    def grand(sec):
        for rows, pos in sect.get(sec, []):
            for r in rows:
                if _norm(r[0]).replace(" ", "").startswith("총"):
                    return _row_nums(r), pos
        # 표준양식 (2025.2Q): no '총…' rows — the section's LAST table is the '…합계' /
        # all-LOB leg and its LAST numeric row is the section total.
        entries = sect.get(sec) or []
        if entries:
            rows, pos = entries[-1]
            for r in reversed(rows):
                n = _row_nums(r)
                if n:
                    return n, pos
        return None, None

    rev_n, rev_p = grand("rev")
    cost_n, cost_p = grand("cost")
    rerev_n, rerev_p = grand("re_rev")
    recost_n, recost_p = grand("re_cost")

    def at(nums, pos, lob):
        if nums is None or pos is None:
            return None
        i = pos.get(lob)
        return nums[i] if i is not None and len(nums) > i else None

    if all(x is not None for x in (rev_n, cost_n, rerev_n, recost_n)):
        def net(lob):
            a, b = at(rev_n, rev_p, lob), at(cost_n, cost_p, lob)
            c, d = at(rerev_n, rerev_p, lob), at(recost_n, recost_p, lob)
            return None if None in (a, b, c, d) else a - b + c - d
        if net("ilban") is not None:
            out[14] = net("ilban")
        if net("auto") is not None:
            out[13] = net("auto")
        out["_jang_rev"] = at(rev_n, rev_p, "jang")
        out["_jang_cost"] = at(cost_n, cost_p, "jang")
        out["_jang_rerev"] = at(rerev_n, rerev_p, "jang")
        out["_jang_recost"] = at(recost_n, recost_p, "jang")
    return out


def _extract_tier2_lotte_combined_bycontent(tables):
    """Caption-stripped OLD combined single-table note (2024.2Q/2024.3Q): identify by content
    (4 section-header rows + 장기/자동차 header), slice rows per section."""
    sect = {}
    for t in tables:
        if _is_rollforward(t) or not t.rows:
            continue
        labs0 = {_norm(r[0]) for r in t.rows if not _row_nums(r)}
        if not ({"보험수익", "보험비용", "재보험수익", "재보험비용"} <= labs0):
            continue
        pos = _lotte_lob_pos(t)
        if pos is None:
            continue
        section, buf = None, []
        for r in t.rows:
            sk = _LOTTE_SEC.get(_norm(r[0]))
            if sk and not _row_nums(r):
                if section is not None:
                    sect.setdefault(section, []).append((buf, pos))
                section, buf = sk, []
                continue
            if section is not None:
                buf.append(r)
        if section is not None:
            sect.setdefault(section, []).append((buf, pos))
        break
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}
    return _lotte_from_sections(sect)


def _extract_tier2_lotte_split(tables):
    """NEW per-segment split layout (2025.3Q/2026.1Q): group tables by row-0 sub-heading;
    keep only 당분기/당반기 tables."""
    def subhead_leg(s):
        s = s.replace(" ", "")
        if "재보험비용의보험서비스비용분석공시" in s:
            # 표준양식 (2025.2Q): heading of the 재보험 회수수익 leg ('재보험자에게서 회수한
            # 금액에서 생기는 수익' tables) — despite the '재보험비용의…' wording.
            return "re_rev"
        if "재보험비용분석공시" in s:
            return "re_cost"
        if "재보험수익분석공시" in s:
            return "re_rev"
        if "보험서비스비용분석공시" in s and "재보험" not in s:
            return "cost"
        if "보험수익분석공시" in s:
            return "rev"
        return None

    sect = {}
    cur, cur_ok = None, True
    for t in tables:
        if not t.rows:
            continue
        r0 = " ".join(_norm(c) for c in t.rows[0])
        lg = subhead_leg(r0)
        if lg is not None:
            cur, cur_ok = lg, ("전분기" not in r0 and "전반기" not in r0)
            continue
        r0c = r0.replace(" ", "")
        if r0c.startswith(("당분기", "당반기")):
            cur_ok = True
            continue
        if r0c.startswith(("전분기", "전반기", "전기")):
            cur_ok = False
            continue
        if cur is None or not cur_ok or _is_rollforward(t):
            continue
        pos = _lotte_lob_pos(t)
        if pos is None:
            continue
        sect.setdefault(cur, []).append((t.rows, pos))
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}
    return _lotte_from_sections(sect)


def extract_tier2_lotte(tables):
    """롯데 dispatcher: legacy combined-caption note first (working quarters, untouched); fall
    through to caption-stripped combined (2024.2Q/3Q) + per-segment split (2025.3Q/2026.1Q)
    only when the primary path finds nothing."""
    out = _extract_tier2_lotte_combined(tables)
    if out and any(out.get(i) is not None for i in (4, 5, 6)):
        return out
    for fn in (_extract_tier2_lotte_combined_bycontent, _extract_tier2_lotte_split):
        alt = fn(tables)
        if alt and any(alt.get(i) is not None for i in (4, 5, 6)):
            return alt
    return out


# ----------------------------- 악사손해 (KR0049) ---------------------------- #
_AXA_SEC = {"보험수익": "rev", "보험서비스비용": "cost",
            "출재보험수익": "re_rev", "출재보험비용": "re_cost",
            # 2023.4Q annual filing uses the shorter 재보험수익/재보험비용 labels for the
            # same two sections; 2024.4Q/2025.4Q switch to 출재보험수익/출재보험비용. Both
            # map to the same re_rev/re_cost bucket.
            "재보험수익": "re_rev", "재보험비용": "re_cost"}


def extract_tier2_axa(tables):
    """악사손해 연차 감사보고서 '(6) 보험손익 상세내역' note (2024.4Q/2025.4Q identical form).

    Columns [자동차|일반|장기|합계] (header-mapped — NOT 장기-first; the generic Format-A
    fallback collapsed '-' cells via _row_nums and mis-assigned the columns), unit 천원.
    Four no-value section-header rows (보험수익/보험서비스비용/출재보험수익/출재보험비용),
    '총 …' total rows, final '총 보험서비스결과' row.  Within a section a label can repeat
    (비PAA vs PAA sub-blocks) — take the first row whose target-LOB cell is numeric (the PAA
    twin prints '-' in 장기 and vice versa).  FIRST captioned table = 당기 (IS-verified for
    both years; the twin is 전기).

    2023.4Q ('(5) 보험손익 상세내역', same shape) folds the [구분|자동차|일반|장기|합계]
    header into rows[0] instead of note.header (docling/DART table split quirk) — fall back
    to treating rows[0] as the header candidate when note.header is empty, and drop it from
    the data rows so it can't be mistaken for a section marker.

    악사's income statement nests 기타사업비용 INSIDE Ⅰ.보험손익 ('3) 기타사업비용' row, 원
    unit), and Tier-1 mis-reads it as ~0 (the '16,25' footnote-ref cell → 1625원).  Emit
    item16 from that IS row so the RC gate's adjusted bridge item1 = ΣLOB + 15 − 16 closes
    (2024.4Q: −7,078.456 − 10,561.922 = −17,640.378 = item1 exactly)."""
    note = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "보험손익상세내역" in cap and t.rows:
            note = t
            break
    if note is None:
        return {}
    f = 1e-3 if "천원" in (note.caption or "") else 1.0

    rows = note.rows
    header_src = note.header
    if not header_src and rows:
        header_src, rows = [rows[0]], rows[1:]

    col = None
    for hr in header_src:
        cells = [_norm(c).replace(" ", "") for c in hr if _norm(c)]
        joined = "".join(cells)
        if "장기" not in joined or "자동차" not in joined:
            continue
        col, k = {}, 0
        for c in cells:
            if c.startswith("구분"):
                continue
            if c.startswith("자동차"):
                col["auto"] = k
            elif c.startswith("일반"):
                col["ilban"] = k
            elif c.startswith("장기"):
                col["jang"] = k
            elif "합계" in c:
                col["tot"] = k
            k += 1
        break
    if not col or "jang" not in col:
        return {}

    def pick(sec_want, needle, lob="jang"):
        sec, nd = None, needle.replace(" ", "")
        for r in rows:
            lab = _norm(r[0]).replace(" ", "")
            vals = [to_num(_norm(c)) for c in r[1:]]
            if lab in _AXA_SEC and not any(v is not None for v in vals):
                sec = _AXA_SEC[lab]
                continue
            if sec != sec_want or nd not in lab:
                continue
            i = col.get(lob)
            if i is not None and len(vals) > i and vals[i] is not None:
                return vals[i] * f
        return None

    out = {}
    csm = pick("rev", "당기손익으로 인식한 보험계약마진")
    ra = pick("rev", "위험해제에 따른 위험조정 변동")
    rev_exp = pick("rev", "예상보험금 및 보험서비스비용")
    cost_act = pick("cost", "보험금 및 보험서비스비용")
    re_csm = pick("re_cost", "당기손익으로 인식한 보험계약마진")
    re_ra = pick("re_cost", "위험해제에 따른 위험조정 변동")
    re_rev_act = pick("re_rev", "회수가능 보험금 및 보험서비스비용")
    re_cost_exp = pick("re_cost", "회수예상 보험금 및 보험서비스비용")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if rev_exp is not None and cost_act is not None:
        out[6] = rev_exp - cost_act
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    if re_rev_act is not None and re_cost_exp is not None:
        out[11] = re_rev_act - re_cost_exp

    out["_jang_rev"] = pick("rev", "총 보험수익")
    out["_jang_cost"] = pick("cost", "총 보험서비스비용")
    out["_jang_rerev"] = pick("re_rev", "총 재보험수익")
    out["_jang_recost"] = pick("re_cost", "총 재보험비용")
    for lob, item in (("auto", 13), ("ilban", 14)):
        v = pick("re_cost", "총 보험서비스결과", lob=lob)   # final row sits after 출재보험비용
        if v is not None:
            out[item] = v

    # item16 (기타사업비용) from the income statement (원 단위; cell r[1] is the 주석 ref)
    for t in tables:
        labs = [_norm(r[0]).replace(" ", "") for r in t.rows]
        if not any(l.startswith(("Ⅰ.보험손익", "I.보험손익")) for l in labs):
            continue
        for r in t.rows:
            if re.sub(r"^\d+\)\s*", "", _norm(r[0])).replace(" ", "") == "기타사업비용":
                vals = [to_num(_norm(c)) for c in r[2:]]
                cur = next((v for v in vals if v is not None), None)
                if cur is not None:
                    out[16] = cur / 1e6
                break
        if 16 in out:
            break
    return out


# ===== 생보: component-decomposition notes (교보/DB생명/동양, single column) ===== #
def _life_flat(t):
    return "".join(_norm(c) for r in t.rows for c in r[:2]).replace(" ", "")


def _life_label_flat(r):
    return (_norm(r[0]) + _norm(r[1] if len(r) > 1 else "")).replace(" ", "")


def _life_is_rollforward(t):
    f = _life_flat(t)
    return any(k in f for k in ("기초순장부금액", "기말순장부금액", "기초보험계약", "기말보험계약",
                                "기초보유", "기말보유", "총현금흐름", "수취한보험료", "순장부금액"))


def _life_cum_col(t):
    """0 for a plain [당기,전기] row; 1 when the table's header shows a 3개월/누적 split
    (반기보고서: 당반기[3개월,누적] | 전반기[3개월,누적], or a bare [3개월,누적] pair with no
    inline prior-period block) -- 누적 is always the 2nd cell of whichever half it's in, so
    index 1 is right for both a 4-col and a 2-col 누적-bearing row. A plain 당기/전기 row has no
    '누적' in its header, so this returns 0 and _life_first_num's prior behavior is unchanged
    (DB생명/교보생명/동양생명 2026.2Q half-year-filing bug, inbox/parser/20260816T2312Z)."""
    hb = "".join(c for row in (t.header or []) for c in row)
    return 1 if "누적" in hb else 0


def _life_first_num(t, label_variants):
    """Numeric cell of the FIRST row whose flattened label contains any variant -- index 0
    (당기) normally, or index 1 (누적, i.e. half-year cumulative) when the table header carries
    a 3개월/누적 split -- see _life_cum_col."""
    if t is None:
        return None
    col = _life_cum_col(t)
    for r in t.rows:
        lf = _life_label_flat(r)
        nums = _row_nums(r)
        if not nums:
            continue
        for v in label_variants:
            if v.replace(" ", "") in lf:
                return nums[col] if col < len(nums) else nums[0]
    return None


def extract_tier2_kyobo(tables):
    def pick(cap_contains_all, must_row):
        for t in tables:
            cap = t.caption or ""
            if all(s in cap for s in cap_contains_all) and "당사" in cap \
                    and not _life_is_rollforward(t):
                if must_row.replace(" ", "") in _life_flat(t):
                    return t
        return None
    rev = pick(("발행한 보험계약", "보험수익"), "당기손익에인식한보험계약마진")
    cost = pick(("발행한 보험계약", "보험서비스비용"), "보험계약에대한보험비용")
    rerev = pick(("재보험계약", "재보험수익"), "발생재보험금")
    recost = pick(("재보험계약", "재보험비용"), "보험계약마진상각")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["당기손익에인식한보험계약마진"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험에대한위험조정변동"]) or 0) or None
        exp = _life_first_num(rev, ["발생한보험서비스비용"])   # 교보 row label (was …수익 → item6 None)
    if cost:
        ac = _life_first_num(cost, ["실제보험금"])
        am = _life_first_num(cost, ["실제계약유지비용"])
        ai = _life_first_num(cost, ["실제투자관리비"])
        act = sum(x for x in (ac, am, ai) if x is not None) if ac is not None else None
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["위험조정변동", "비금융위험에대한위험조정"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상재보험금"])
    if rerev:
        re_act = _life_first_num(rerev, ["발생재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


def extract_tier2_dblife(tables):
    def pick(cap_frag, must_row=None):
        for t in tables:
            cap = t.caption or ""
            if cap_frag in cap and not _life_is_rollforward(t):
                if must_row is None or must_row.replace(" ", "") in _life_flat(t):
                    return t
        return None
    rev = pick("발행한 보험계약의 보험수익", "보험계약마진상각")
    cost = pick("발행한 보험계약의 보험비용", "발생보험금")
    rerev = pick("재보험계약의 재보험수익", "발생출재보험금")
    recost = pick("재보험계약의 재보험비용", "예상출재보험금")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험에대한위험조정상각"]) or 0) or None
        exp = sum(x for x in (
            _life_first_num(rev, ["예상보험금"]),
            _life_first_num(rev, ["예상유지비"]),
            _life_first_num(rev, ["예상손해조사비"]),
            _life_first_num(rev, ["예상투자관리비"]),
        ) if x is not None)
    if cost:
        act = sum(x for x in (
            _life_first_num(cost, ["발생보험금"]),
            _life_first_num(cost, ["발생직접유지비"]),
            _life_first_num(cost, ["손해조사비"]),
            _life_first_num(cost, ["투자관리비"]),
        ) if x is not None)
        if rev:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["비금융위험에대한위험조정상각"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상출재보험금"])
    if rerev:
        re_act = _life_first_num(rerev, ["발생출재보험금"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


def extract_tier2_dongyang(tables):
    def pick(first_label, must_row):
        for t in tables:
            if not t.rows or _life_is_rollforward(t):
                continue
            if _norm(t.rows[0][0]) != first_label:
                continue
            if must_row.replace(" ", "") in _life_flat(t):
                return t
        return None
    rev = pick("보험수익", "예상발생보험금및기타보험서비스비용")
    cost = pick("보험서비스비용", "실제발생보험금및기타보험서비스비용")
    rerev = pick("재보험수익", "실제재보험금및기타재보험서비스비용")
    recost = pick("재보험비용", "예상재보험금및기타재보험서비스비용")
    out = {}
    exp = re_exp = None
    if rev:
        out[4] = abs(_life_first_num(rev, ["보험계약마진상각"]) or 0) or None
        out[5] = abs(_life_first_num(rev, ["비금융위험위험조정변동"]) or 0) or None
        exp = _life_first_num(rev, ["예상발생보험금및기타보험서비스비용"])
    if cost:
        act = _life_first_num(cost, ["실제발생보험금및기타보험서비스비용"])
        if rev and exp is not None and act is not None:
            out[6] = abs(exp) - abs(act)
    if recost:
        out[9] = -abs(_life_first_num(recost, ["보험계약마진상각"]) or 0) or None
        out[10] = -abs(_life_first_num(recost, ["비금융위험위험조정변동"]) or 0) or None
        re_exp = _life_first_num(recost, ["예상재보험금및기타재보험서비스비용"])
    if rerev:
        re_act = _life_first_num(rerev, ["실제재보험금및기타재보험서비스비용"])
        if recost and re_exp is not None and re_act is not None:
            out[11] = abs(re_act) - abs(re_exp)
    return out  # 백만원 already


# ===== 생보: comprehensive positional-section note (신한/농협/흥국/케이디비/푸본) ===== #
_SECT = {
    "보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost",
    "재보험수익": "re_rev", "재보험비용": "re_cost", "재보험서비스비용": "re_cost",
    "출재보험수익": "re_rev", "출재보험비용": "re_cost",
}
_V_CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "제공된 서비스의 보험계약마진",
          "제공받은 서비스의 보험계약마진", "보험계약마진 상각", "제공받은 서비스의 재보험계약마진",
          "당기손익에 인식한 보험계약마진")
_V_RA = ("비금융위험에 대한 위험조정의 변동분", "위험해제로 인한 비금융위험에 대한 위험조정의 변동",
         "위험해제로 인한 위험조정의 변동", "위험조정 변동", "위험조정의 변동")
_V_REV_EXP = ("예상 보험금 및 기타보험 서비스비용", "예상보험금 및 기타보험 서비스비용",
              "예상 발생보험금 및 비용", "예상 발생보험금 및 보험서비스비용",
              "예상 보험금 및 보험서비스비용", "예상발생보험금",
              "예상 보험금 및 기타보험서비스 수익")
_V_COST_ACT = ("발생 보험금 및 기타보험서비스 비용", "발생보험금 및 기타보험 서비스비용",
               "실제 발생보험금 및 비용", "실제 발생보험금 및 보험서비스비용",
               "보험금 및 보험서비스비용", "실제발생보험금",
               "발생 보험금 및 기타보험서비스 비용")
_V_RE_REV_ACT = ("당기 발생재보험금", "발생재보험금", "회수가능 보험금 및 보험서비스비용",
                 "실제 출재보험금 및 비용", "실제발생재보험금",
                 "발생 재보험금 및 재보험서비스비용",        # 신한라이프
                 "실제 출재보험금 및 재보험비용",            # 케이디비 2025.x
                 "실제 출재보험금 및 재보험서비스비용",      # 케이디비 2026.1Q
                 "발생 출재보험금 및 재보험서비스비용")      # 흥국생명
_V_RE_COST_EXP = ("예상 재보험금 및 기타보험서비스비용", "회수예상보험금", "회수예상 보험금 및 보험서비스비용",
                  "예상 출재보험금 및 비용", "예상발생재보험금",
                  "예상 재보험금 및 기타 재보험서비스비용",  # 신한라이프
                  "예상 출재보험금 및 재보험비용",           # 케이디비 2025.x
                  "예상 출재보험금 및 재보험서비스비용")     # 케이디비 2026.1Q / 흥국생명


def _life2_match(lbl, variants):
    s = lbl.replace(" ", "")
    return any(v.replace(" ", "") in s for v in variants)


def _life2_first_num(r):
    for c in r:
        v = to_num(c)
        if v is not None:
            return v
    return None


def _life2_sect_of(lbl):
    s = lbl.replace(" ", "")
    s = re.sub(r"^[0-9]+\.", "", s)
    s = s.lstrip("(0-9). ")
    for k, val in _SECT.items():
        if s == k.replace(" ", "") or s.startswith(k.replace(" ", "")):
            return val
    return None


def _life2_rowblob(t):
    return " ".join(_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)


def _life2_is_rollfwd(t):
    b = _life2_rowblob(t)
    return any(k in b for k in ("기초 순장부금액", "기말 순장부금액", "기초 보험계약", "기말 보험계약",
                                "기초보험계약", "기말보험계약", "수취한 보험료", "순장부금액",
                                "보험계약부채(자산)", "기초 장부금액", "기말 장부금액"))


def _life_comprehensive(tables):
    """Family A: positional-section P&L-analysis note with 당기/전기 columns.
    2026-08-26 (inbox/parser/20260825T1415Z follow-up): the note this scans for is filed
    TWICE in a both-basis filing (연결 note, then 별도 note -- same row labels, independent
    note numbers e.g. "36. 보험영업수익(비용)" 연결 vs "35. ..." 별도).  `add()`'s
    first-occurrence-wins (non-accumulate kinds) / sum-all (accumulate kinds) semantics
    then silently locks in whichever comes first in `tables` = 연결 (document order), or
    double-counts an accumulate kind across both notes.  Confirmed via raw for 신한라이프
    (item4 2025.4Q: 연결 735,862 vs 별도 735,229; master had 735,862).  Try the OFS-only
    pool first so 별도 wins without a per-company code check; if that finds nothing (e.g.
    a filing whose 별도 attachment doesn't carry this note in the exact shape/caption this
    scan needs -- 한화생명 2025.4Q was observed dropping to empty this way even though its
    ORIGINAL result was already 별도, via the no-해외-columns pick inside `_pick_life_table`'s
    사촌 note, not this function -- confirmed empty here too), fall back to the full pool
    so a filing with no usable OFS candidate does not silently lose a previously-populated
    cell (빈 칸 우선, but not at the cost of a coverage regression when the unfiltered pool
    already carried the right basis)."""
    ofs_only = _prefer_ofs(tables)
    secvals, totals = _life_comprehensive_core(ofs_only)
    if secvals.get("rev", {}).get("csm") is None and ofs_only is not tables:
        secvals, totals = _life_comprehensive_core(tables)
    return secvals, totals


def _life_comprehensive_core(tables):
    secvals = {}
    totals = {}

    def add(sec, kind, val, accumulate=False):
        d = secvals.setdefault(sec, {})
        if accumulate:
            d[kind] = (d.get(kind) or 0) + val
        elif kind not in d:
            d[kind] = val

    seen_caps = set()
    for t in tables:
        if _life2_is_rollfwd(t):
            continue
        b = _life2_rowblob(t)
        if "보험계약마진" not in b:
            continue
        if not any(s in b for s in ("보험수익", "보험서비스비용", "보험비용",
                                    "재보험수익", "재보험비용", "재보험서비스비용")):
            continue
        cap = (t.caption or "")
        capn = cap.replace(" ", "")
        if any(k in capn for k in ("최초인식", "최초 인식", "전환방법별", "전환 방법별",
                                   "신규로체결", "신규로 체결", "신용건전성", "신용위험",
                                   "지분의장부금액", "위험노출")):
            continue
        is_pl_cap = any(k in capn for k in ("보험손익", "보험서비스결과", "보험영업손익",
                                            "재보험영업손익", "구성내역", "상세내역",
                                            "보험계약관련손익", "보험수익및보험비용",
                                            "출재보험관련손익"))
        bn = b.replace(" ", "")
        has_tot_boundary = any(k in bn for k in ("총보험수익", "총보험서비스비용",
                                                 "총재보험수익", "총재보험서비스비용"))
        if not (is_pl_cap or has_tot_boundary):
            continue
        if cap in seen_caps:
            continue
        seen_caps.add(cap)
        section = None
        has_header_rows = any(_life2_sect_of(_norm(r[0])) for r in t.rows)
        shinhan_form = has_tot_boundary and not has_header_rows
        is_re_table = ("재보험영업손익" in capn) or ("출재보험관련손익" in capn) \
            or ("재보험서비스비용" in capn)
        if shinhan_form:
            section = "re_rev" if is_re_table else "rev"

        def value_of(r):
            return (max((v for v in (to_num(c) for c in r) if v is not None),
                        key=abs, default=None) if shinhan_form else _life2_first_num(r))

        for r in t.rows:
            lab0 = _norm(r[0]) if r else ""
            lab1 = _norm(r[1]) if len(r) > 1 else ""
            lbl = (lab0 + lab1)
            nums = [v for v in (to_num(c) for c in r) if v is not None]
            sec_hdr = _life2_sect_of(lab0)
            if sec_hdr and (not nums or lab1):
                section = sec_hdr
                if not nums:
                    continue
                lbl = lab1
            if section is None:
                continue
            cur = value_of(r)
            if cur is None:
                continue
            plain = lab0.replace(" ", "")
            l1 = lab1.replace(" ", "")
            if any(k in plain for k in ("소계", "합계", "총보험수익", "총보험서비스비용",
                                        "총재보험수익", "총재보험서비스비용", "총재보험비용")) \
                    or l1 in ("소계", "합계"):
                totals.setdefault(section, cur)
                if shinhan_form:
                    if "총보험수익" in plain:
                        section = "cost"
                    elif "총재보험수익" in plain:
                        section = "re_cost"
                continue
            if section == "rev":
                if _life2_match(lbl, _V_CSM):
                    add("rev", "csm", cur)
                elif _life2_match(lbl, _V_RA):
                    add("rev", "ra", cur)
                elif _life2_match(lbl, _V_REV_EXP):
                    add("rev", "exp", cur, accumulate=True)
            elif section == "cost":
                if _life2_match(lbl, _V_COST_ACT):
                    add("cost", "act", cur, accumulate=True)
            elif section == "re_rev":
                if _life2_match(lbl, _V_RE_REV_ACT):
                    add("re_rev", "act", cur, accumulate=True)
            elif section == "re_cost":
                if _life2_match(lbl, _V_CSM):
                    add("re_cost", "csm", cur)
                elif _life2_match(lbl, _V_RA):
                    add("re_cost", "ra", cur)
                elif _life2_match(lbl, _V_RE_COST_EXP):
                    add("re_cost", "exp", cur, accumulate=True)
    return secvals, totals


def _life_product_split(tables):
    """Family B: 미래에셋 product-split notes. Only items 4,5,9,10 recoverable."""
    def hdr_blob(x):
        return " ".join(" ".join(h) for h in x.header)

    def block_sum(group):
        csm = ra = None
        for x in group:
            cur = "dang"
            for r in x.rows:
                lab0 = _norm(r[0])
                if lab0 == "당기":
                    cur = "dang"
                elif lab0 == "전기":
                    cur = "jeon"
                nums = [v for v in (to_num(c) for c in r) if v is not None]
                if cur != "dang" or not nums:
                    continue
                key = (lab0 + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
                v = nums[-1]
                if _life2_match(key, _V_CSM):
                    csm = (csm or 0) + v
                elif _life2_match(key, _V_RA):
                    ra = (ra or 0) + v
        return csm, ra

    def fingerprint(x):
        return tuple(round(v, 1) for r in x.rows
                     for v in (to_num(c) for c in r) if v is not None)

    rev_group, recost_group = [], []
    seen_fp = set()
    for x in tables:
        rows0 = [_norm(r[0]) for r in x.rows]
        body = " ".join(_norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in x.rows)
        if "당기" not in rows0 or "전기" not in rows0 or "보험계약마진" not in body:
            continue
        fp = fingerprint(x)
        if fp in seen_fp:
            continue
        seen_fp.add(fp)
        hb = hdr_blob(x)
        if "재보험서비스비용" in hb:
            recost_group.append(x)
        elif "보험수익" in hb and "재보험" not in hb:
            rev_group.append(x)
    if not rev_group and not recost_group:
        return {}
    out = {}
    csm, ra = block_sum(rev_group)
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    re_csm, re_ra = block_sum(recost_group)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out


def _life_build_items(secvals, totals):
    rev = secvals.get("rev", {})
    cost = secvals.get("cost", {})
    re_rev = secvals.get("re_rev", {})
    re_cost = secvals.get("re_cost", {})
    out = {}
    if rev.get("csm") is not None:
        out[4] = abs(rev["csm"])
    if rev.get("ra") is not None:
        out[5] = abs(rev["ra"])
    if rev.get("exp") is not None and cost.get("act") is not None:
        out[6] = abs(rev["exp"]) - abs(cost["act"])
    if re_cost.get("csm") is not None:
        out[9] = -abs(re_cost["csm"])
    if re_cost.get("ra") is not None:
        out[10] = -abs(re_cost["ra"])
    if re_rev.get("act") is not None and re_cost.get("exp") is not None:
        out[11] = abs(re_rev["act"]) - abs(re_cost["exp"])
    return out


# ----------------------------- KB라이프생명 (KR0099) ----------------------- #
def _kblife_block_total(note, which, needle):
    """합계 of the wanted period block in KB라이프's 계약유형별 P&L note.  Cell layout after the
    col0 label is one or two 6-column blocks (사망/건강/연금저축/변액/복합/합계); 합계 is the
    block's rightmost data col.  `which`='first' → 당기 block (당기/전기 annual note); 'last' →
    누적 block (3개월/누적 반기 note) or the only block (single-period quarter)."""
    nd = needle.replace(" ", "")
    for r in note.rows:
        if nd not in _norm(r[0]).replace(" ", ""):
            continue
        data = r[1:]
        b1, b2 = data[0:6], data[6:12]
        if which == "last" and any(to_num(c) is not None for c in b2):
            block = b2
        else:
            block = b1
        for c in reversed(block):          # 합계 = last non-blank col of the block
            v = to_num(c)
            if v is not None:
                return v
        return None
    return None


def extract_tier2_kblife(tables):
    """KB라이프생명 (KR0099): 푸르덴셜+KB생명 merger note.  계약유형별 P&L-analysis note with
    KB-specific row labels that none of the shared variant lists match (CSM상각 = '서비스제공에
    따른 보험계약마진의 변동', etc.) — code-keyed so only KR0099 takes this path.  Picks the
    correct period block: 당기(1st) for the 당기/전기 annual note, 누적(2nd) for the 3개월/누적
    반기 note, the only block otherwise."""
    note = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap \
                or "보험영업비용" not in cap:
            continue
        if _is_rollforward(t):
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        if not any(k in hb for k in ("당분기", "당반기", "당기")):
            continue
        if not any(_norm(r[0]).replace(" ", "") == "서비스제공에따른보험계약마진의변동"
                   for r in t.rows):
            continue                        # the current-period table that carries the rows
        note = t
        break
    if note is None:
        return {}

    hbn = " ".join(" ".join(h) for h in note.header).replace(" ", "")
    which = "first" if "전기" in hbn else "last"   # 누적/single → last; 당기/전기 → first
    g = lambda nd: _kblife_block_total(note, which, nd)

    csm = g("서비스제공에 따른 보험계약마진의 변동")
    ra = g("위험해제에 따른 위험조정의 변동")
    rev_exp = g("예상보험금 및 예상보험서비스 비용")
    cost_act = g("실제보험금 및 실제보험서비스비용")
    re_csm = g("제공받은 서비스의 재보험계약마진")
    re_ra = g("위험해제로 인한 위험조정의 변동")
    re_rev = g("발생 재보험금 및 재보험서비스비용 회수액")
    re_cost_exp = g("회수예상 보험금 및 보험서비스비용")

    out = {}
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
    # 발행/출재 grand totals for item3/8 (assemble also has the FS-API _is_* fallback)
    jr, jc = g("총 보험수익"), g("총 보험서비스비용")
    jrr, jrc = g("총 재보험수익"), g("총 재보험비용")
    if jr is not None:
        out["_jang_rev"] = abs(jr)
    if jc is not None:
        out["_jang_cost"] = abs(jc)
    if jrr is not None:
        out["_jang_rerev"] = abs(jrr)
    if jrc is not None:
        out["_jang_recost"] = abs(jrc)
    return out


# ============ 구형식 (pre-2025.2Q) 생보 OLD note family (3 layouts) ============ #
_OLD_L_SECT = {"보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost",
               "보험영업수익": "rev", "보험영업비용": "cost",
               "재보험수익": "re_rev", "재보험비용": "re_cost", "재보험서비스비용": "re_cost",
               "재보험영업수익": "re_rev", "재보험영업비용": "re_cost",
               "출재보험수익": "re_rev", "출재보험비용": "re_cost"}
_OLD_L_CSM = ("보험계약마진 상각", "제공된 서비스의 보험계약마진", "제공받은 서비스의 보험계약마진",
              "제공받은 서비스의 재보험계약마진", "서비스제공에 따른 보험계약마진의 변동",
              "당기손익에 인식한 보험계약마진")
_OLD_L_RA = ("위험조정 변동", "위험해제로 인한 위험조정의 변동", "위험해제에 따른 위험조정의 변동",
             "위험해제로 인한 비금융위험에 대한 위험조정의 변동", "비금융위험에 대한 위험조정의 변동")
_OLD_L_REVEXP = ("예상 보험금 및 보험서비스비용", "예상발생보험금", "예상 발생보험금 및 보험서비스비용",
                 "예상 보험금 및 기타보험 서비스비용", "예상보험금 및 예상보험서비스 비용")
_OLD_L_COSTACT = ("실제발생보험금", "실제 발생보험금 및 보험서비스비용", "보험금 및 보험서비스비용",
                  "발생보험금", "실제보험금 및 실제보험서비스비용")
_OLD_L_RE_REVACT = ("회수가능 보험금 및 보험서비스비용", "실제 출재보험금 및 보험서비스비용",
                    "발생 재보험금", "실제출재보험금", "실제발생재보험금", "발생재보험금")
_OLD_L_RE_COSTEXP = ("회수예상 보험금 및 보험서비스비용", "예상 출재보험금 및 보험서비스비용",
                     "회수예상보험금", "예상출재보험금", "예상발생재보험금")


def _oll_sn(s):
    return re.sub(r"^[\(0-9\)\.\s]+", "", _norm(s)).replace(" ", "")


def _oll_match(lbl, vs):
    s = _norm(lbl).replace(" ", "")
    return any(v.replace(" ", "") in s for v in vs)


def _oll_ytd(t):
    """('pair', 1) for [3개월,누적] columns else ('single', 0)."""
    hb = _header_blob(t)
    return ("pair", 1) if ("누적" in hb and "3개월" in hb) else ("single", 0)


def _oll_num(r, mi):
    mode, idx = mi
    ns = [to_num(c) for c in r if to_num(c) is not None]
    if not ns:
        return None
    return (ns[idx] if len(ns) > idx else ns[0]) if mode == "pair" else ns[0]


def _oll_l1_pure(t):
    hb = _header_blob(t)
    return not any(k in hb for k in ("손해보험", "장기", "자동차"))


def _oll_l1_hassec(t, name):
    return any(_oll_sn(r[0]) == name and not [to_num(c) for c in r if to_num(c) is not None]
               for r in t.rows)


def _oll_l1_is(t):
    if _life2_is_rollfwd(t):
        return False
    hb = _header_blob(t)
    if "합계" not in hb and "합 계" not in hb:
        return False
    if "보험계약마진" not in "".join(_norm(r[0]) for r in t.rows):
        return False
    return sum(1 for r in t.rows if _oll_sn(r[0]) in _OLD_L_SECT
               and not [to_num(c) for c in r if to_num(c) is not None]) >= 2


def _oll_l1_collect(t):
    sec, d = None, {}
    for r in t.rows:
        key = _oll_sn(r[0])
        nums = [to_num(c) for c in r if to_num(c) is not None]
        if key in _OLD_L_SECT and not nums:
            sec = _OLD_L_SECT[key]
            continue
        if sec is None or key.startswith("총") or key in ("소계", "합계"):
            continue
        v = nums[-1] if nums else None
        if v is None:
            continue
        if sec == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d.setdefault("exp", v)
        elif sec == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d.setdefault("cact", v)
        elif sec == "re_rev":
            if _oll_match(r[0], _OLD_L_RE_REVACT):
                d.setdefault("ract", v)
        elif sec == "re_cost":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("recsm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("rera", v)
            elif _oll_match(r[0], _OLD_L_RE_COSTEXP):
                d.setdefault("rexp", v)
    return d


def _oll_layout1(tables):
    """2026-08-26: this OLD-format layout has no basis check of its own ('별도 (pure life)
    preferred' below is a LOB-purity filter, not a 연결/별도 one) -- try the OFS-only pool
    first, fall back to the full pool if that finds nothing, same pattern as the other
    generic 생보 Tier-2 paths."""
    out = _oll_layout1_core(_prefer_ofs(tables))
    if out.get(4) is None:
        out2 = _oll_layout1_core(tables)
        if out2.get(4) is not None:
            out = out2
    return out


def _oll_layout1_core(tables):
    rc = [t for t in tables if _oll_l1_is(t)]
    pool = [t for t in rc if _oll_l1_pure(t)] or rc        # 별도 (pure life) preferred
    rev_t = next((t for t in pool if _oll_l1_hassec(t, "보험수익")), None)
    re_t = next((t for t in pool if _oll_l1_hassec(t, "재보험수익")), None)
    out = {}
    if rev_t:
        d = _oll_l1_collect(rev_t)
        if "csm" in d:
            out[4] = abs(d["csm"])
        if "ra" in d:
            out[5] = abs(d["ra"])
        if "exp" in d and "cact" in d:
            out[6] = abs(d["exp"]) - abs(d["cact"])
    if re_t:
        d = _oll_l1_collect(re_t)
        if "recsm" in d:
            out[9] = -abs(d["recsm"])
        if "rera" in d:
            out[10] = -abs(d["rera"])
        if "ract" in d and "rexp" in d:
            out[11] = abs(d["ract"]) - abs(d["rexp"])
    return out


def _oll_secs(t):
    return [_OLD_L_SECT[_oll_sn(r[0])] for r in t.rows if _oll_sn(r[0]) in _OLD_L_SECT]


def _oll_l2_parse(t, want):
    mi = _oll_ytd(t)
    sec, d = None, {}
    for r in t.rows:
        key = _oll_sn(r[0])
        nums = [to_num(c) for c in r if to_num(c) is not None]
        if key in _OLD_L_SECT:
            sec = _OLD_L_SECT[key]
            if sec == want and nums:
                d.setdefault("_agg", _oll_num(r, mi))
            continue
        if sec != want or key in ("소계", "합계"):
            continue
        v = _oll_num(r, mi)
        if v is None:
            continue
        if want == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d["exp"] = d.get("exp", 0) + v
        elif want == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d["act"] = d.get("act", 0) + v
        elif want == "re_rev":
            if _oll_match(r[0], _OLD_L_RE_REVACT):
                d["act"] = d.get("act", 0) + v
        elif want == "re_cost":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_RE_COSTEXP):
                d["exp"] = d.get("exp", 0) + v
    return d


def _oll_l2_caption_leg(cap):
    c = (cap or "").replace(" ", "")
    if "재보험" in c and ("손익" in c or "구성" in c):
        return "re"
    if "보험수익의구성" in c:
        return "rev"
    if "보험비용의구성" in c or "보험서비스비용의구성" in c:
        return "cost"
    return None


def _oll_l2_whole(t, want):
    mi = _oll_ytd(t)
    d = {}
    for r in t.rows:
        if _oll_sn(r[0]) in ("소계", "합계"):
            continue
        v = _oll_num(r, mi)
        if v is None:
            continue
        if want == "rev":
            if _oll_match(r[0], _OLD_L_CSM):
                d.setdefault("csm", v)
            elif _oll_match(r[0], _OLD_L_RA):
                d.setdefault("ra", v)
            elif _oll_match(r[0], _OLD_L_REVEXP):
                d["exp"] = d.get("exp", 0) + v
        elif want == "cost":
            if _oll_match(r[0], _OLD_L_COSTACT):
                d["act"] = d.get("act", 0) + v
    return d


def _oll_layout2(tables):
    cands = [t for t in tables
             if (not _life2_is_rollfwd(t))
             and "보험계약마진" in "".join(_oll_sn(r[0]) for r in t.rows)
             and _oll_secs(t)]
    legs = {}
    for sec in ("rev", "cost", "re_rev", "re_cost"):       # best (별도, smallest total) per leg
        src = [t for t in cands if sec in _oll_secs(t)]
        if not src:
            continue

        def keyf(t):
            agg = _oll_l2_parse(t, sec).get("_agg")
            return (abs(agg) if agg is not None else float("inf"), -len(t.rows))
        legs[sec] = _oll_l2_parse(min(src, key=keyf), sec)
    if "rev" not in legs or "cost" not in legs:            # 푸본-FY2023 caption-leg fallback
        rv = [t for t in tables if _oll_l2_caption_leg(t.caption) == "rev" and not _life2_is_rollfwd(t)]
        cs = [t for t in tables if _oll_l2_caption_leg(t.caption) == "cost" and not _life2_is_rollfwd(t)]
        if rv and "rev" not in legs:
            legs["rev"] = _oll_l2_whole(rv[0], "rev")
        if cs and "cost" not in legs:
            legs["cost"] = _oll_l2_whole(cs[0], "cost")
    if "re_rev" not in legs or "re_cost" not in legs:
        rsrc = [t for t in tables if _oll_l2_caption_leg(t.caption) == "re"
                and not _life2_is_rollfwd(t) and _oll_secs(t)]
        for sec in ("re_rev", "re_cost"):
            if sec in legs:
                continue
            s = [t for t in rsrc if sec in _oll_secs(t)]
            if s:
                legs[sec] = _oll_l2_parse(s[0], sec)
    if not legs:
        return {}
    rev, cost = legs.get("rev", {}), legs.get("cost", {})
    rr, rcst = legs.get("re_rev", {}), legs.get("re_cost", {})
    out = {}
    if "csm" in rev:
        out[4] = abs(rev["csm"])
    if "ra" in rev:
        out[5] = abs(rev["ra"])
    e, a = rev.get("exp", rev.get("_agg")), cost.get("act", cost.get("_agg"))
    if e is not None and a is not None:
        out[6] = abs(e) - abs(a)
    if "csm" in rcst:
        out[9] = -abs(rcst["csm"])
    if "ra" in rcst:
        out[10] = -abs(rcst["ra"])
    ra_, re_ = rr.get("act", rr.get("_agg")), rcst.get("exp", rcst.get("_agg"))
    if ra_ is not None and re_ is not None:
        out[11] = abs(ra_) - abs(re_)
    return out


def extract_tier2_life_old(tables):
    """Dispatcher for pre-2025.2Q 생보 notes: 한화 LOB-column (L1) → 구분-row period-column
    (L2, 농협/흥국/KDB/푸본) → per-product rollforward (L3, 미래에셋, items 4/5/9/10 only).
    Returns {} when none match — and, as a guard, when the NEW standardized CSM label is present
    (a 2025.2Q+ filing) so the NEW handlers/comprehensive keep precedence and golds never regress."""
    for t in tables:
        if _life2_is_rollfwd(t):
            continue          # 미래에셋 L3 rollforward CSM line shares this wording — not a NEW note
        for r in t.rows:
            if "서비스의이전으로당기손익에인식한보험계약마진" in _norm(r[0]).replace(" ", ""):
                return {}
    out = _oll_layout1(tables)
    if out and out.get(4):
        return out
    out = _oll_layout2(tables)
    if out and out.get(4):
        return out
    # 미래에셋 (L3 rollforward) is left to comprehensive's own _life_product_split fallback —
    # calling it here would override a good comprehensive result on recent quarters.
    return {}


def extract_tier2_life_comprehensive(tables, code=None):
    """생보 Family A/B dispatcher: comprehensive note, with 미래에셋 product-split
    fallback for items 4,5,9,10.  Emits the note 발행/출재 grand totals (_jang_*) for
    item3/8, EXCEPT 신한라이프 (KR0094) — its note 총 over-states by a PAA-presentation
    reclass, so we leave _jang_* unset and let assemble fall back to the plain 별도
    income-statement 보험수익/보험서비스비용 lines (which reconcile exactly)."""
    # pre-2025.2Q OLD note (누적/합계 basis) takes precedence — the comprehensive note misreads
    # old quarters (3개월 / single-product); life_old defers on NEW filings via its guard.
    old = extract_tier2_life_old(tables)
    if old and old.get(4):
        return old
    secvals, totals = _life_comprehensive(tables)
    out = _life_build_items(secvals, totals)
    if not any(out.get(i) is not None for i in (4, 5)):
        for k, val in _life_product_split(tables).items():
            out.setdefault(k, val)
    if code != "KR0094":
        for k, sec in (("_jang_rev", "rev"), ("_jang_cost", "cost"),
                       ("_jang_rerev", "re_rev"), ("_jang_recost", "re_cost")):
            if sec in totals:
                out[k] = totals[sec]
    return out


def extract_tier2_samsung_life(tables):
    """삼성생명(KR0069) OLD-format combined 보험서비스수익/비용 notes (2023.1Q–2025.1Q).
    Reads the 당기 누적 column; 재보 lives under the 출재보험서비스수익/비용 col0 sections
    (재보 CSM labelled '제공받은 서비스의 보험계약마진').  2025.2Q+ uses dedicated 재보 tables →
    handler returns {} there and parse_filing's generic fallback (extract_tier2_life) handles it.
    2026-08-26: this note is filed both-basis (연결/별도); the caption match below took
    whichever came first (연결, confirmed via raw XBRL ConsolidatedMember tag vs master) --
    try the OFS-only pool first so 별도 wins; if that finds nothing (별도 attachment lacks
    this exact caption for some filing), fall back to the full pool rather than losing a
    previously-populated cell."""
    out = _samsung_life_core(_prefer_ofs(tables))
    if out.get(4) is None:
        out2 = _samsung_life_core(tables)
        if out2.get(4) is not None:
            out = out2
    return out


def _samsung_life_core(tables):
    def cum(r):                       # 당기 누적 = last col of the 당기 block
        n = _row_nums(r)
        return n[max(1, len(n) // 2) - 1] if n else None

    def rf(t, *nd):
        for r in t.rows:
            lab = (_norm(r[0]) + "|" + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
            if any(x.replace(" ", "") in lab for x in nd):
                return r
        return None
    rev = cost = None
    for t in tables:
        cap = t.caption or ""
        if rev is None and "보험서비스수익의 내역" in cap:
            rev = t
        if cost is None and "보험서비스비용의 내역" in cap:
            cost = t
    if not (rev and cost):
        return {}
    out = {}
    out[4] = abs(cum(rf(rev, "제공된 서비스의 보험계약마진")) or 0) or None
    r5 = next((r for r in rev.rows if "위험해제" in _norm(r[0]).replace(" ", "")), None)
    out[5] = abs(cum(r5) or 0) or None
    rev_exp = cum(rf(rev, "일반보험서비스수익"))      # 원수 예상 (col1 line-item)
    re_act = cum(rf(rev, "출재보험서비스수익"))       # 재보 실제
    cost_act = cum(rf(cost, "일반보험서비스비용"))    # 원수 실제
    out[9] = -abs(cum(rf(cost, "제공받은 서비스의 보험계약마진")) or 0) or None
    seen = False
    r10 = None                                        # 재보 RA = 위험해제 row AFTER 출재 header
    for r in cost.rows:
        if "출재보험서비스비용" in _norm(r[0]).replace(" ", ""):
            seen = True
        if seen and "위험해제" in _norm(r[0]).replace(" ", ""):
            r10 = r
            break
    out[10] = -abs(cum(r10) or 0) or None
    re_exp = cum(rf(cost, "출재보험서비스비용"))       # 재보 예상
    if rev_exp is not None and cost_act is not None:
        out[6] = abs(rev_exp) - abs(cost_act)
    if re_act is not None and re_exp is not None:
        out[11] = abs(re_act) - abs(re_exp)
    return out


# --------------------------- 미래에셋생명 (KR0079) ------------------------- #
# 2026.2Q 반기부터 라벨 재구성된 회사가 다수 확인됨(같은 개념, 어순만 다름) -- 기존 라벨 유지,
# 신규 라벨 추가.
_MA_CSM_KEYS = ("서비스의이전으로당기손익에인식한보험계약마진",   # both note forms
                "보험계약서비스의이전때문에당기손익으로인식된보험수익,보험계약마진")
_MA_RA_KEYS = ("위험조정변동분",
               "미래또는과거서비스와관련없는비금융위험에대한위험조정의변동",
               "비금융위험에대한위험조정의변동분")


def _ma_block_val(t, keys, last_only):
    """First 당기/당분기/당반기-block row matching `keys`.  last_only=True → 합계 col
    (nums[-1], 백만원 note); else whole-row sum (원-wide)."""
    cur = "dang"
    for r in t.rows:
        lab0 = _norm(r[0]).replace(" ", "")
        if lab0 in ("당기", "당분기", "당반기"):
            cur = "dang"
        elif lab0 in ("전기", "전분기", "전반기"):
            cur = "jeon"
        if cur != "dang":
            continue
        lab = (_norm(r[0]) + "|" + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(k in lab for k in keys):
            nums = [v for v in (to_num(c) for c in r) if v is not None]
            if not nums:
                continue
            return nums[-1] if last_only else sum(nums)
    return None


# item6 (원수 예실차), Era-2 XBRL note only (inbox/parser 20260828T2300Z, survey
# inbox/_resolved/20260828T2110Z).  This note ("18-1. 보험계약부채(자산) 변동분의 차이조정
# 공시") splits 예상 4종 into a dedicated P&L-shaped table (5 products x 3 전환구분 cols) and
# 발생 4종 into a separate LRC/LIC rollforward table (5 products x [손실요소외,손실요소,LIC]
# cols) -- NOT the same table `_ma_block_val` reads for item4/5 (that one is the CSM/RA/PV
# 구성요소별 조정내역 note; confirmed by item4 matching both tables' CSM row but item5 NOT
# matching the P&L-shaped table's RA row -- a pre-existing item4/5 quirk, left untouched).
_MA_EXP4_ROW = "발생한 보험금 및 그 밖의 발생한 보험서비스비용을 통한 증가"
# 2025.2Q/2025.3Q word the SAME row differently in DART's XBRL taxonomy (a longer paraphrase,
# not a different concept) -- found + triple-reconciled to the 원 (boundary rule + both
# population checks below, exact match) for those two quarters specifically, inbox/parser/
# 20260829T1600Z `## 답변`.  A quick sanity check there also found 2026.1Q's t_exp matches
# ONLY this ALT wording (original needle: 0 candidates) with both checks passing exactly --
# reported as a follow-up candidate but its master cell was deliberately NOT patched in that
# ticket (out of its explicit 2-quarter scope, and not hand-verified row-by-row like the two
# quarters below); do not assume it's equivalent to a full re-check before filling it.
_MA_EXP4_ROW_ALT = "발생한 보험금 및 그 밖의 발생한 보험서비스비용에 따른 증가분"
_MA_EXP4_ROW_VARIANTS = (_MA_EXP4_ROW, _MA_EXP4_ROW_ALT)
_MA_ACT4_ROW = "발생한 보험금 및 기타 보험서비스비용"
# The 예상측 table's 7 P&L components (their SUM must equal the 발생측 table's own 보험수익
# lump row -- population check A below).  손실요소배분액 sits OUTSIDE the 4-species boundary
# (same NH ruling, inbox/_resolved/20260828T1400Z) -- excluded from `_MA_ACT4_ROW`'s full-row
# sum via subtraction in `_ma_yesilcha_direct`, not by omitting it from this list.  Components
# 1/3/5 carry a second (needle, alt) tuple for the 2025.2Q/2025.3Q wording; 2/4/6/7 use
# wording that's a substring-match under BOTH label eras already (confirmed against the raw
# 2025.2Q/2025.3Q dump), so they needed no second variant.
_MA_7COMP_ROWS = (
    _MA_EXP4_ROW_VARIANTS,
    "비금융위험에 대한 위험조정의 변동분",
    ("보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익",
     "서비스의 이전으로 당기손익에 인식한 보험계약마진"),
    "손실요소배분액",
    ("경험 조정을 통한 증가",
     "경험조정에 따른 증가분(감소분), 보험계약부채(자산)"),
    "기타 변동에 의한 증가",
    "보험취득 현금흐름의 회수와 관련되는 보험료",
)


def _ma_row_sum(t, needle):
    """Sum of numeric cells in the first row of `t` whose (구분 label + 하위 라벨) contains
    `needle` -- mirrors scripts/_probes/mirae_yesilcha_survey.py's row_sum() exactly (that
    probe's values were verified cell-by-cell against the raw 2026.2Q XML before this was
    ported into the handler).  `needle` may be a str or a tuple of label variants (different
    filing eras word the same row differently, inbox/parser/20260829T1600Z); the first variant
    matched, in document row order, wins."""
    needles = (needle,) if isinstance(needle, str) else needle
    for r in t.rows:
        joined = "".join(r[:2])
        if any(n in joined for n in needles):
            nums = _row_nums(r)
            if nums:
                return sum(nums)
    return None


def _ma_find_product_table(ofs_tables, row_needle):
    """별도(OFS)-only table whose header carries the 5-product breakout (사망/건강보험 cue
    excludes the 2-category (배당여부별 구분) sibling table that shares the same row labels)
    and whose rows contain `row_needle` (str or tuple of label variants -- see `_ma_row_sum`).
    Ties broken by lowest line_no = document order = 당반기/당분기 block (DART prints the
    current period before the comparative one, verified against the raw 2026.2Q XML: 당반기
    table precedes 전반기 by ~240-990 lines in every (표2,표3) pair found there).

    EXCEPTION -- an all-candidates-capped tie is UNRESOLVABLE, not just unbroken (2026-08-30,
    inbox/parser/20260830T0000Z): lxml's HTMLParser saturates `.sourceline` at
    `_SOURCELINE_CAP` (65535) for every element past that line (common.py), so "lowest
    line_no" carries zero document-order information once every candidate reports the same
    65535 -- `cands[0]` would then be whichever table `ofs_tables` happens to list first, not
    "당기/당반기".  Root-caused on 미래에셋생명(KR0079) 2025.4Q by direct raw-XML inspection
    (`scripts/_probes/mirae_2025q4_basis_check.py`): the note's 연결(CFS)-tagged rendering
    sits at real, un-capped line numbers and is byte-verified intact (row labels line up with
    their values), but `_prefer_ofs` correctly drops it as CFS per this project's 별도-only
    convention -- and EVERY 별도(OFS)-tagged rendering of the SAME note sits past the cap
    (reported line_no=65535) and is corrupted in the raw DART XML itself (row values shifted
    one line down from their labels; confirmed cell-by-cell against the CFS copy, not a
    parser artifact -- COLSPAN/ROWSPAN are identical between the two).  There is no clean OFS
    candidate to prefer among such a tie, by construction: any tie surviving `_prefer_ofs`
    with every member capped means every surviving candidate came from the same
    (indistinguishable-by-position) tail region.  Returning None here closes that door
    directly instead of relying on `_ma_yesilcha_direct`'s check A/B to catch a bad pick by
    numeric luck -- important because a smaller row-shift than KR0079's could stay inside
    check A's tolerance and ship silently wrong."""
    needles = (row_needle,) if isinstance(row_needle, str) else row_needle
    cands = [t for t in ofs_tables
              if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
              and any(any(n in "".join(r[:2]) for n in needles) for r in t.rows)]
    if not cands:
        return None
    cands.sort(key=lambda t: t.line_no)
    if len(cands) > 1 and cands[0].line_no == _SOURCELINE_CAP:
        return None                            # unresolvable tie -- see docstring EXCEPTION
    return cands[0]


def _ma_tier1_ins_rev(ofs_tables):
    """별도 '일반보험서비스수익' 당기누적(YTD) value from the Tier-1 포괄손익계산서 table, used
    only as the item6 population-check anchor (NOT written to any item -- item3/8 already
    come from the FS income-statement legs in assemble())."""
    for t in ofs_tables:
        for r in t.rows:
            if _label(r, 0) == "일반보험서비스수익":
                col = _ytd_col(t)
                nums = _row_nums(r)
                if len(nums) > col:
                    return nums[col]
    return None


def _ma_yesilcha_direct(tables):
    """item6 (원수 예실차, 백만원) for the Era-2 XBRL note, gated on TWO independent
    population checks so a quarter whose note layout has drifted (confirmed to happen --
    2025.4Q's cue match fails check A and self-aborts, 2023.2Q-2025.1Q lack the note entirely,
    all empirically checked via scripts/_probes/mirae_item6_extract_test.py /
    mirae_full_sweep_with_alt.py, not assumed) silently returns None instead of shipping a
    wrong number on a closed-form axis no gate can catch (PL_YESILCHA_ZERO_OTHER_PLUG).  Two
    label eras for the 예상측 EXP4 row are tried via `_MA_EXP4_ROW_VARIANTS` (2026.2Q: the
    original wording; 2025.2Q/2025.3Q, and 2026.1Q too: the ALT paraphrase -- see that
    constant's comment, inbox/parser/20260829T1600Z).  Boundary rule (손실요소배분액 excluded
    from the 4-species 발생 side, mirroring NH inbox/_resolved/20260828T1400Z): `act` = the
    발생 row's full sum (all LRC_손실요소외/손실요소/LIC cols) MINUS the 예상측 table's own
    손실요소배분액 row -- NOT a naive LIC-only column pick (that happened to equal this exact
    formula for every quarter checked so far because LRC_손실요소외 is 0 in every product
    column there, verified cell-by-cell, not the general case)."""
    ofs_tables = _prefer_ofs(tables)
    t_exp = _ma_find_product_table(ofs_tables, _MA_EXP4_ROW_VARIANTS)
    t_act = _ma_find_product_table(ofs_tables, _MA_ACT4_ROW)
    if t_exp is None or t_act is None:
        return None
    exp = _ma_row_sum(t_exp, _MA_EXP4_ROW_VARIANTS)
    loss_alloc = _ma_row_sum(t_exp, "손실요소배분액")
    full_row = _ma_row_sum(t_act, _MA_ACT4_ROW)
    if exp is None or loss_alloc is None or full_row is None:
        return None
    act = full_row - loss_alloc

    total7 = sum(v for v in (_ma_row_sum(t_exp, c) for c in _MA_7COMP_ROWS) if v is not None)
    rev_lump = _ma_row_sum(t_act, "보험수익")
    if rev_lump is None or abs(abs(total7) - abs(rev_lump)) >= 1.0:
        return None                                        # check A (internal) failed
    anchor = _ma_tier1_ins_rev(ofs_tables)
    if anchor is None or abs(abs(total7) - abs(anchor)) >= 1.0:
        return None                                        # check B (Tier-1 anchor) failed

    return (exp - act) / 1e6


def extract_tier2_miraeasset(tables):
    """미래에셋생명 (KR0079) per-product CSM/RA → items 4,5,9,10 (백만원).  Two note eras:
      1. 백만원 보험수익 note (annual + 2023.3Q–2025.1Q quarters): 5 separate product tables,
         당분기/당기 block, 합계 = last numeric col.
      2. 원 wide rollforward (2025.2Q/3Q, 2026.1Q): products are COLUMNS; the CSM-amort row
         carries values ONLY in CSM cols (PV/RA cols 0) → whole-row sum = item4; /1e6 → 백만원.
    Era-1 preferred.  item3/8 + RC come from the FS income-statement legs in assemble().
    item6 (원수 예실차): only when `_ma_yesilcha_direct`'s dual population-check gate passes
    (verified for 2026.2Q and, via `_MA_EXP4_ROW_VARIANTS`, 2025.2Q/2025.3Q; the gate ALSO
    passes for 2026.1Q under the same variant but that quarter's master cell was deliberately
    left unpatched, inbox/parser/20260829T1600Z -- see that constant's docstring).  item11
    (재보험 예실차): still data-absent -- the mirror-image
    재보험 note's Tier-1 population check ('출재보험서비스수익') would not close within the
    investigation ticket's scope (inbox/_resolved/20260828T2110Z §4), so no extraction is
    wired for it; do not add one without first closing that reconciliation."""
    def hb(t):
        return " ".join(" ".join(h) for h in t.header).replace(" ", "")

    def has_amort(t):
        flat = " ".join(
            _norm(r[0]) + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows
        ).replace(" ", "")
        return any(k in flat for k in _MA_CSM_KEYS)

    # ---- Era 1: 백만원 per-product 보험수익 note ----
    seen = set()
    rev_c = rev_a = re_c = re_a = None
    for t in tables:
        h = hb(t)
        if "단위:백만원" not in h or not has_amort(t):
            continue
        is_recost = "재보험서비스비용" in h
        is_rev = ("보험수익" in h) and not is_recost
        if not (is_rev or is_recost):
            continue
        fp = tuple(to_num(c) for r in t.rows for c in r if to_num(c) is not None)
        if fp in seen:
            continue
        seen.add(fp)
        c = _ma_block_val(t, _MA_CSM_KEYS, last_only=True)
        a = _ma_block_val(t, _MA_RA_KEYS, last_only=True)
        if is_recost:
            if c is not None:
                re_c = (re_c or 0) + c
            if a is not None:
                re_a = (re_a or 0) + a
        else:
            if c is not None:
                rev_c = (rev_c or 0) + c
            if a is not None:
                rev_a = (rev_a or 0) + a
    if rev_c is not None:
        out = {4: abs(rev_c)}
        if rev_a is not None:
            out[5] = abs(rev_a)
        if re_c is not None:
            out[9] = -abs(re_c)
        if re_a is not None:
            out[10] = -abs(re_a)
        return out

    # ---- Era 2: 원 wide product-column rollforward (first table = 당기) ----
    first_issue = first_re = None
    seen2 = set()
    for t in tables:
        h = hb(t)
        if "사망보험" not in h or not has_amort(t) or len(t.rows) < 5:
            continue
        fp = tuple(to_num(c) for r in t.rows for c in r if to_num(c) is not None)
        if fp in seen2:
            continue
        seen2.add(fp)
        if "발행한보험계약" in h and "보유재보험계약" not in h:
            if first_issue is None:
                first_issue = t
        elif "보유재보험계약" in h:
            if first_re is None:
                first_re = t
    out = {}
    if first_issue is not None:
        c = _ma_block_val(first_issue, _MA_CSM_KEYS, last_only=False)
        a = _ma_block_val(first_issue, _MA_RA_KEYS, last_only=False)
        if c is not None:
            out[4] = abs(c) / 1e6
        if a is not None:
            out[5] = abs(a) / 1e6
    if first_re is not None:
        c = _ma_block_val(first_re, _MA_CSM_KEYS, last_only=False)
        a = _ma_block_val(first_re, _MA_RA_KEYS, last_only=False)
        if c is not None:
            out[9] = -abs(c) / 1e6
        if a is not None:
            out[10] = -abs(a) / 1e6
    item6 = _ma_yesilcha_direct(tables)
    if item6 is not None:
        out[6] = item6
    return out


def extract_tier2_hana(tables):
    """하나생명(KR0097): disaggregated 보험수익/보험서비스비용 notes (NOT a P&L-analysis note).
    4 separate tables captioned '발행한 보험계약…보험수익/보험서비스비용' + the 재보험 pair.
    Unit 천원 → 백만원 (×1e-3); current period = col 0.  (Tier-1 item1=순보험서비스손익,
    item16←기타보험비용 are fixed in extract_tier1.)

    2023.4Q label-variant gap (found via inbox/parser 20260825T0230Z follow-up,
    PL_CSM_AMORT_VS_WATERFALL RED): that filing's raw XML has the target-caption table
    TWICE -- a "13-4" note-13 companion summary (document order: first, so `pick()` binds
    to it) that words the CSM/RA rows differently, and the standard "21. 보험수익 및
    재보험수익" note (document order: later) using the literal labels below. Both cite the
    SAME underlying figures (CSM row: 27,913,708천원 in both) -- confirmed byte-identical
    against `data/dart/extracted/..._measurement.json`'s FY2023 rollforward amortization
    stage (279.14억, CSM_waterfall.json). FY2024/FY2025 filings only ever have ONE
    matching-caption table (the "21."/"20." form with the literal labels already handled),
    so these extra variants are 2023-only fallbacks and don't touch those years' output."""
    f = 1e-3

    def pick(*cap_frags):
        for t in tables:
            cap = (t.caption or "")
            if all(s in cap for s in cap_frags) and not _life_is_rollforward(t):
                return t
        return None
    rev = pick("발행한 보험계약", "보험수익")
    cost = pick("발행한 보험계약", "보험서비스비용")
    rerev = pick("재보험계약", "보험수익")
    recost = pick("재보험계약", "보험서비스비용")
    out = {}
    # 발행(원수) 합계 → item3 = 보험수익 − 보험서비스비용 (assemble).  Without these, item3 would
    # fall back to the income-statement _is_rev/_is_cost, but 하나's _is_cost is a mis-pick
    # (≈9% of 보험수익) that the materiality guard rejects → item3/item2 went None.
    if rev:
        out["_jang_rev"] = _life_first_num(rev, ["합 계", "합계"])
    if cost:
        out["_jang_cost"] = _life_first_num(cost, ["합 계", "합계"])
    if rev:
        csm = _life_first_num(rev, ["보험계약마진상각", "당기손익에인식한보험계약마진"])
        ra = _life_first_num(rev, ["비금융위험에 대한 위험조정 변동",
                                    "비금융위험에 대한 위험조정의 변동분"])
        if csm is not None:
            out[4] = abs(csm)
        if ra is not None:
            out[5] = abs(ra)
        exp = _life_first_num(rev, ["소 계"])      # first 소계 = 예상 발생 보험서비스비용
        if cost and exp is not None:
            act = sum(x for x in (
                _life_first_num(cost, ["발생보험금"]),
                _life_first_num(cost, ["발생사고부채변동"]),
                _life_first_num(cost, ["직접유지비"]),
                _life_first_num(cost, ["손해조사비"]),
                _life_first_num(cost, ["투자관리비"]),
            ) if x is not None)
            out[6] = abs(exp) - abs(act)
    if recost:
        rc = _life_first_num(recost, ["보험계약마진상각"])
        rr = _life_first_num(recost, ["위험조정 변동", "비금융위험에 대한 위험조정 변동"])
        if rc is not None:
            out[9] = -abs(rc)
        if rr is not None:
            out[10] = -abs(rr)
        re_exp = _life_first_num(recost, ["예상출재보험금"])
        if rerev and re_exp is not None:
            re_act = _life_first_num(rerev, ["발생재보험금"])
            if re_act is not None:
                out[11] = abs(re_act) - abs(re_exp)
    return {k: (v * f if isinstance(v, (int, float)) else v) for k, v in out.items() if v is not None}


def extract_tier2_yebyeol(tables):
    """예별손해보험(구 MG손해보험, KR0004) 감사보고서 '(N) 당기 및 전기 중 인식된
    보험료배분접근법이 적용된 보험계약의 변동내역' note -- 자동차보험/일반보험 2개
    직접(원수) LOB 테이블만 존재(장기 직접 LOB 없음; '장기보험-비비례보험'은 별도
    재보험(출재) note에만 있음 -- 이 회사는 장기 리스크를 직접 인수하지 않고 출재만
    받는 것으로 보임, raw 확인). 각 LOB 테이블의 '보험서비스결과 소계' 행 합계
    (마지막)열이 그 LOB의 순보험손익(items 13/14 자동차손익/일반손익).

    재보험(출재) 버전 note가 캡션까지 유사/중복돼 캡션만으로 구분 불가 -- 행0
    (구분열)에 '재보험' 접두 라벨이 있는지로 직접/재보험을 구분(직접 테이블만 채택).
    같은 캡션이 당기/전기 두 번 반복되는 해(FY2024)가 있어 문서상 첫 매치(document
    order)만 채택 -- 이 저장소 기존 관행(extract_tier2_axa 등)과 동일한 컨벤션.
    단위(천원)는 note 전체의 첫 캡션에만 있고 개별 LOB 서브캡션엔 없어 하드코드
    (raw로 두 회계연도 모두 확인).

    측정요소(CSM/RA/예실차, items 4/5/6 -- GMM 장기보험분)는 이 note에 없다. 이미
    적재된 CSM_waterfall.json의 KR0004 CSM은 별도 note에서 나온 것으로 추정되나
    그 note는 아직 못 찾음 -- item1(보험손익) 대비 13+14 합의 잔차가 크므로(FY2024
    -59535.8 vs -5300.1, FY2025 -22136.1 vs -13101.4) 미확보 장기 GMM 기여분이
    상당하다는 신호. items 4/5/6 및 재보험(9/10/11) 확보는 별도 후속 조사
    (2026-08-15 inbox/parser/20260616T0210Z 참조)."""
    out = {}
    for lob, item in (("자동차보험", 13), ("일반보험", 14)):
        for t in tables:
            cap = t.caption or ""
            if lob not in cap or not t.rows:
                continue
            if any("재보험" in (r[0] if r else "") for r in t.rows[:3]):
                continue  # ceded-reinsurance twin, skip
            for r in t.rows:
                lab = (r[0] or "").replace(" ", "")
                if lab != "보험서비스결과소계":
                    continue
                nums = []
                for c in r[1:]:
                    c = (c or "").replace(",", "").replace(" ", "")
                    neg = c.startswith("(") and c.endswith(")")
                    c2 = c.strip("()")
                    try:
                        v = float(c2)
                        nums.append(-v if neg else v)
                    except ValueError:
                        pass
                if nums:
                    out[item] = nums[-1] * 1e-3   # 천원 -> 백만원
                break
            break  # first direct-LOB match in document order == 당기
    return out


# --------------------- 에이아이에이생명보험 (KR0080) ------------------------ #
# Both KR0080 and 처브라이프생명보험(KR0100) turned out to have NO table-form 손익분해 at
# all for KR0080 -- disclosed only as a PROSE PARAGRAPH inside the "1. 일반사항" note of
# their (annual-only) DART 감사보고서.  The standard pipeline (extract_tier1 for the
# income-statement top line, every note-table LIFE_HANDLERS for the LOB breakdown) never
# sees this data, so both companies were entirely absent from PL_breakdown (owner ticket
# inbox/parser/20260819T0058Z__owner__KR0080_2025.4Q__aia_chubb_pl_disclosed_in_prose.md).
# KR0100 turned out to ALSO carry a full structured note (see extract_tier2_chubb below)
# so it does NOT need this prose path -- only KR0080 genuinely has no table form at all.
def _eok(m):
    """(sign_marker, digits) regex match -> signed 억원 float, or None."""
    if not m:
        return None
    sign = -1.0 if m.group(1) else 1.0
    return sign * float(m.group(2).replace(",", ""))


def extract_tier2_aia(tables, dirs=None):
    """에이아이에이생명보험(KR0080): the ENTIRE PL breakdown -- including the top-level
    보험손익/투자손익/영업외손익/법인세/당기순이익 that every other company gets from Tier-1
    (extract_tier1 / the DART FS-API) -- is disclosed ONLY as a prose paragraph in 주석 '1.
    일반사항' (raw: data/dart/FY2025_Q4/raw/KR0080_에이아이에이생명보험_20260407002100/
    20260407002100_00760.xml, verified 2026-08-19 byte-for-byte against the owner's ticket
    transcription). There is no table anywhere in the filing carrying this data (Tier-1 AND
    every Tier-2 note-table path already returned None for every filed year -- pre-fix
    data/_derived/pl_breakdown_coverage.json showed status=no_income_statement, all 24
    items missing, for 2022.4Q/2023.4Q/2024.4Q/2025.4Q), so this reads the raw XML directly
    via `dirs` (parse_filing() in build_pl_breakdown.py special-cases this handler to pass
    dirs=dirs) rather than `tables` (_iter_tables_with_context only ever yields <TABLE>
    elements, never bare <P> prose -- this company's income statement has no such table).

    Company files ONLY a 사업보고서 (annual) -- no quarterly filings exist (confirmed:
    data/dart/FY2026_Q{1,2}/raw/KR0080_.../meta.json says "no_filing":true) -- so this
    naturally only ever fires on a 4Q raw dir; no quarterly grid is fabricated.  It is
    written as a genuine regex parser (not a hardcoded per-quarter override) so a future
    year's 사업보고서, if it repeats the same sentence template, backfills automatically;
    if the wording changes it safely returns {} (see sanity gate below) rather than mis-fire.

    3 figures from the prose the owner's ticket left unmapped -- 손실요소의 전입 (-)65억,
    발생사고요소조정 +258억, 기타사업비용 (-)591억:
      * 손실요소전입 + 발생사고요소조정 (=+193억) -> item7 (기타 생명장기 원수손익).  Both are
        IFRS17 LRC/CSM adjustments the 24-item schema has no dedicated slot for; item7 is
        exactly the schema's residual/catch-all for items 4/5/6-adjacent 원수 components
        (assemble(): item7 = item3-(item4+item5+item6)).
      * 기타사업비용 (591억) -> item16, NOT item7 -- despite being narrated as one of
        several "금년도 보험손익 392억원 중" components (i.e. nominally inside item1 in this
        company's own prose), it keeps the schema's dedicated item16 slot because (a) it is
        a VERBATIM literal-name match to ITEM_NAMES[16]="기타사업비용", and (b) this exact
        "기타사업비용 disclosed INSIDE 보험손익" situation already has a codebase precedent --
        악사손해(KR0049)'s extract_tier2_axa, which also assigns it to item16 and relies on
        assemble()'s RC-gate 'adj' bridge (item1 = ΣLOB(item2) + item15 - item16) to
        reconcile.  That bridge is what makes THIS company's gate close at all: lob=item2=
        99,300, item1=39,200 -> bare gap 60,100 (fails the 25% tolerance) but
        adj=|99,300+0-59,100-39,200|=1,000 (comfortably passes) -- i.e. item16 pulling 591억
        out of the LOB side is *why* the RC gate accepts this breakdown, not an arbitrary
        choice.  (Folding all 3 figures into item7 instead and leaving item16 unset also
        numerically clears the gate via the looser 'bare' formula, but has no comparable
        structural justification and would leave item16 empty for a company whose own text
        names it verbatim -- and 처브라이프생명보험's independently-derived income statement,
        see extract_tier2_chubb, confirms the SAME filer-family convention: its own
        '3.기타사업비용' line is what closes ITS 보험손익 identity too.)

    item18/19 (투자이익/보험금융손익) are deliberately NOT populated even though the same
    paragraph also states "보험계약에서 발생하는 보험금융비용은 (-)7,446억원입니다" (which
    would cleanly close item18=item17-item19, the same way KR0100/처브라이프's independently
    confirmed 보험금융수익-보험금융비용 table split validates the analogous figure there --
    see extract_tier2_chubb) -- held back because for THIS company there is only the one
    already-netted prose sentence and no second, independent citation (structured table) to
    confirm the netting convention, unlike 처브.  Flagged for the owner rather than guessed.

    Sanity gate before returning anything: 영업이익 must equal 보험손익+투자손익, and
    당기순이익 must equal 영업이익+영업외손익-법인세, both within 2억원 (matches the owner's
    own cross-check, which found a 1억 rounding gap on the 2nd identity) -- protects against
    the regexes partial-matching a differently-worded paragraph in a future filing year."""
    text = None
    for d in dirs or []:
        for x in sorted(glob.glob(d + "/*.xml")):
            try:
                raw = open(x, "rb").read().decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if "당사의 금년도 영업이익은" in raw and "재보험손익은" in raw:
                text = raw
                break
        if text:
            break
    if text is None:
        return {}

    # Bound the search window to just this one paragraph -- re.search on the full ~900KB
    # document with loose per-figure patterns could otherwise cross-match an unrelated note
    # that happens to reuse the same label words elsewhere in the filing.
    m0 = re.search(
        r"당사의\s*금년도\s*영업이익은.+?재보험손익은\s*(\(-\))?\s*[\d,]+억원입니다\.",
        text, re.S)
    if not m0:
        return {}
    para = m0.group(0)

    def find(pat):
        return _eok(re.search(pat, para, re.S))

    op = find(r"당사의\s*금년도\s*영업이익은\s*(\(-\))?\s*([\d,]+)억원입니다")
    ins = find(r"영업이익\s*[\d,]+억원\s*중\s*보험손익은\s*(\(-\))?\s*([\d,]+)억원이며")
    inv = find(r"보험손익은\s*[\d,]+억원이며,\s*투자손익은\s*(\(-\))?\s*([\d,]+)억원입니다")
    oth_op = find(r"영업외손익은\s*(\(-\))?\s*([\d,.]+)억원입니다\.\s*법인세는")
    tax = find(r"법인세는\s*(\(-\))?\s*([\d,]+)억원이며,\s*영업이익에서")
    ni = find(r"차감한\s*당기순이익은\s*(\(-\))?\s*([\d,]+)억원입니다")
    csm = find(r"보험계약마진은\s*총.+?%인\s*(\(-\))?\s*([\d,]+)억원이\s*상각되어\s*수익으로\s*인식")
    ra = find(r"위험조정은\s*총.+?%인\s*(\(-\))?\s*([\d,]+)억원이\s*상각되어\s*수익으로\s*인식")
    claim_diff = find(r"실제\s*보험금\s*차이가\s*(\(-\))?\s*([\d,]+)억원이고")
    exp_diff = find(r"실제\s*사업비\s*차이가\s*(\(-\))?\s*([\d,]+)억원,\s*손실요소")
    loss_comp = find(r"손실요소의\s*전입으로\s*발생한\s*손실은\s*(\(-\))?\s*([\d,]+)억원입니다")
    incurred_adj = find(r"발생사고요소조정은\s*(\(-\))?\s*([\d,]+)억원,\s*기타사업비용")
    oth_cost = find(r"기타사업비용은\s*(\(-\))?\s*([\d,]+)억원입니다\.\s*재보험손익")
    reins = find(r"재보험손익은\s*(\(-\))?\s*([\d,]+)억원입니다")

    if any(x is None for x in (op, ins, inv, oth_op, tax, ni, csm, ra, claim_diff,
                                exp_diff, loss_comp, incurred_adj, oth_cost, reins)):
        return {}
    if abs((ins + inv) - op) > 2 or abs((op + oth_op - tax) - ni) > 2:
        return {}

    f = 100.0  # 억원 -> 백만원
    item4, item5 = csm * f, ra * f
    item6 = (claim_diff + exp_diff) * f
    item7 = (loss_comp + incurred_adj) * f
    item3 = item4 + item5 + item6 + item7
    return {
        1: ins * f, 3: item3, 4: item4, 5: item5, 6: item6, 7: item7,
        8: reins * f, 15: 0.0, 16: oth_cost * f, 17: inv * f,
        21: oth_op * f, 23: tax * f, 24: ni * f,
    }


# ----------------------------- 처브라이프생명보험 (KR0100) ------------------- #
def _chubb_note_table(tables, cap_needle):
    """Second (data) table whose caption contains cap_needle -- 처브 prints EACH note(4)
    sub-table's caption twice: a unit-only placeholder (header=[], one row '(단위:백만원)')
    immediately followed by the real [구분|당기|전기] table (the mini unit-table sits
    between the <P> caption and the real <TABLE> but doesn't reset _iter_tables_with_context's
    last_caption, so both tables share the identical caption string -- filter on a populated
    header to skip the placeholder)."""
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if cap_needle in cap and t.header:
            return t
    return None


def extract_tier2_chubb(tables):
    """처브라이프생명보험(KR0100) 감사보고서 주석 '(4) 보험손익 및 재보험손익' -- FOUR
    [구분|당기|전기] sub-tables (1)보험영업수익 2)보험영업비용 3)재보험수익 4)재보험비용의
    내역), 단위 백만원.  Confirmed via raw (2026-08-19,
    data/dart/FY2025_Q4/raw/KR0100_처브라이프생명보험_20260408003172/20260408003172_00760.xml):
    each sub-table's own '합계' row matches, to the 백만원, the corresponding
    1.보험영업수익/2.재보험수익/1.보험영업비용/2.재보험비용 sub-line of the SAME filing's
    audited 포괄손익계산서 (Ⅰ.영업수익/Ⅱ.영업비용) -- a 4-for-4 cross-check between two
    independent parts of the filing, high confidence.

    The owner's ticket (inbox/parser/20260819T0058Z) suspected this company uses the SAME
    prose-paragraph pattern as KR0080/에이아이에이생명보험 ("보험손익 4회 등장" in the raw) --
    it does NOT, on closer look.  처브's '1. 일반사항' note does carry a short prose summary
    (보험손익 (-)105억원 등) but it only gives NET (원수+재보험 combined) CSM/RA/예실차
    figures that don't match the schema's 원수-only items 4/5/6 (e.g. prose CSM=48억 vs this
    note's direct-only CSM=61.22억; 48 = 61.22 - 12.82, i.e. direct MINUS the
    reinsurance-ceded CSM found in this same note's table 4) -- the FULL split the schema
    wants is only available here (table), so the prose is not used at all for this company.

    재보험 sign/mirroring convention: the "재보험수익" note mirrors the DIRECT-COST
    ("actual incurred") structure and the "재보험비용" note mirrors the DIRECT-REVENUE
    ("expected"/CSM/RA) structure -- standard IFRS17 reinsurance-held presentation, the same
    convention already used by extract_tier2_axa/extract_tier2_hana in this file. item9/10
    (재보험 CSM/RA) are forced negative (-abs), matching those precedents.

    item1(보험손익)/item17(투자손익) are NOT printed anywhere in this filing -- the income
    statement is 성격별 (nature-of-expense: Ⅰ.영업수익/Ⅱ.영업비용 lump insurance AND
    investment lines together), unlike the 기능별 Ⅰ.보험손익/Ⅱ.투자손익 layout most other
    insurers use, so extract_tier1()'s _is_income_statement() never matches it (tier1.py
    requires "보험손익"/"보험서비스결과" as a literal row label). item1 is instead computed
    via the SAME 'adj' reconciliation bridge assemble() already uses for a company whose
    기타사업비용 sits inside 보험손익 (item1 = item2+item15-item16 -- see
    extract_tier2_axa/KR0049 and extract_tier2_aia/KR0080 above for that precedent):
    -3,704(lob) + 27.5(기타영업수익) - 6,834(기타사업비용) = -10,510 백만원 = -105.1억,
    matching the prose's rounded "보험손익은 (-)105억원" -- cross-validated. item17 =
    item20(Ⅲ.영업이익, printed exactly) - item1, so item1+item17=item20 holds by
    construction (assemble() only ever derives item20 FROM item1+item17, never the reverse,
    so item17 must be supplied here or it would stay None)."""
    rev = _chubb_note_table(tables, "보험영업수익의내역")
    cost = _chubb_note_table(tables, "보험영업비용의내역")
    rerev = _chubb_note_table(tables, "재보험수익의내역")
    recost = _chubb_note_table(tables, "재보험비용의내역")
    if not (rev and cost and rerev and recost):
        return {}

    out = {}
    rev_tot = _life_first_num(rev, ["합계", "합 계"])
    cost_tot = _life_first_num(cost, ["합계", "합 계"])
    if rev_tot is not None and cost_tot is not None:
        out[3] = rev_tot - cost_tot
    csm = _life_first_num(rev, ["당기 서비스의 이전으로 당기손익에 인식된 보험계약마진"])
    ra = _life_first_num(rev, ["비금융위험에 대한 위험조정 변동"])
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    exp_claim = _life_first_num(rev, ["기초 예상 당기 발생보험금 및 기타 보험서비스비용"])
    act_claim = _life_first_num(cost, ["발생보험금 및 기타보험서비스비용"])
    if exp_claim is not None and act_claim is not None:
        out[6] = exp_claim - act_claim

    rerev_tot = _life_first_num(rerev, ["합계", "합 계"])
    recost_tot = _life_first_num(recost, ["합계", "합 계"])
    if rerev_tot is not None and recost_tot is not None:
        out[8] = rerev_tot - recost_tot
    re_csm = _life_first_num(recost, ["당기 서비스의 이전으로 당기손익에 인식된 보험계약마진"])
    re_ra = _life_first_num(recost, ["비금융위험에 대한 위험조정 변동"])
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    re_act = _life_first_num(rerev, ["재보험 발생보험금 및 기타보험서비스비용"])
    re_exp = _life_first_num(recost, ["기초 예상 당기 발생보험금 및 이익수수료"])
    if re_act is not None and re_exp is not None:
        out[11] = re_act - re_exp

    # Tier-1 substitute: find the audited 포괄손익계산서 by ROW CONTENT (not caption -- its
    # actual preceding <P> is the audit-report boilerplate disclaimer, since the real title
    # "포 괄 손 익 계 산 서" lives in a non-<P> tag that _iter_tables_with_context never
    # registers as a caption).
    is_t = None
    for t in tables:
        labs = " ".join(_norm(r[0] if r else "") for r in t.rows)
        if "당기순이익" in labs and "법인세비용" in labs and "영업이익" in labs:
            is_t = t
            break
    if is_t is None:
        return out  # note(4) alone still gives 3/4/5/6/8/9/10/11 -- better than nothing

    f = 1e-6  # 원 -> 백만원
    op = _pick_line(is_t, "영업이익", exclude=("영업외",))       # Ⅲ. 영업이익
    oth_op = _pick_line(is_t, "영업외손익")                      # Ⅳ. 영업외손익
    ni = _pick_line(is_t, "당기순이익")                          # Ⅶ. 당기순이익
    oth_exp = _pick_line(is_t, "기타사업비용")                   # 3. 기타사업비용 (Ⅱ항)
    oth_inc = _pick_line(is_t, "기타영업수익")                   # 9. 기타영업수익 (Ⅰ항)
    if op is None or ni is None:
        return out
    out[20] = op * f
    out[21] = (oth_op * f) if oth_op is not None else None
    out[24] = ni * f
    out[16] = (oth_exp * f) if oth_exp is not None else None
    out[15] = (oth_inc * f) if oth_inc is not None else 0.0

    if out.get(3) is not None and out.get(8) is not None and out.get(16) is not None:
        lob = out[3] + out[8]
        out[1] = lob + (out.get(15) or 0.0) - abs(out[16])
        if out.get(20) is not None:
            out[17] = out[20] - out[1]
    return out


# Per-company routing tables (FY2025+ annual Tier-2 handlers).
SONBO_HANDLERS = {
    "KR0010": extract_tier2_kb,
    "KR0009": extract_tier2_hyundai,
    "KR0002": _hanwha_dispatch,                # 한화손해 (NEW 2025.2Q+ → OLD pre-2025.2Q)
    "KR0004": extract_tier2_yebyeol,           # 예별손해(구MG) 자동차/일반 (장기 직접분 없음)
    "KR0008": extract_tier2_sonbo_component,   # 삼성화재 (gold-validated 2025.2Q)
    "KR0005": _heungkuk_dispatch,              # 흥국화재 (NEW 2025.2Q+ → OLD pre-2025.2Q)
    "KR0011": extract_tier2_db,
    "KR0032": extract_tier2_nh,
    "KR0003": extract_tier2_lotte,
    "KR0049": extract_tier2_axa,               # 악사손해 연차 '보험손익 상세내역' (자동차|일반|장기 columns)
    "KR1000": extract_tier2_coreanre,          # 코리안리 재보험 (gold-validated 2025.2Q; 생명/장기/일반)
    "KR0150": extract_tier2_sgi,                # 서울보증보험 (보증/해외/상해/자동차/기타, 생명장기 無)
}
LIFE_HANDLERS = {
    "KR0070": extract_tier2_abl,               # 에이비엘 ([구분|당기|전기] 2-period note → pick 당기)
    "KR0073": extract_tier2_kyobo,
    "KR0082": extract_tier2_dblife,
    "KR0087": extract_tier2_dongyang,
    "KR0094": extract_tier2_life_comprehensive,
    "KR0104": extract_tier2_life_comprehensive,
    "KR0071": extract_tier2_life_comprehensive,
    "KR0072": extract_tier2_life_comprehensive,
    "KR0079": extract_tier2_miraeasset,        # 미래에셋생명 (per-product CSM/RA, 백만원+원 eras)
    "KR0083": extract_tier2_life_comprehensive,
    "KR0099": extract_tier2_kblife,            # KB라이프생명 (KB-specific row labels)
    "KR0069": extract_tier2_samsung_life,      # 삼성생명 OLD combined note (9/10/11); NEW→generic
    "KR0097": extract_tier2_hana,              # 하나생명 (disaggregated 보험수익/비용 notes)
    "KR0080": extract_tier2_aia,               # 에이아이에이생명보험 (prose-only, 주석 1.일반사항)
    "KR0100": extract_tier2_chubb,             # 처브라이프생명보험 ('(4) 보험손익 및 재보험손익' note)
}
