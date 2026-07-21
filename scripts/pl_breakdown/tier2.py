"""Tier-2: generic 발행보험 계약유형별 / 재보험 note extraction."""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
from .common import _label, _norm, _row_nums


# --------------------------------------------------------------------------- #
# Tier 2 — 발행보험 / 재보험 analysis note (items 4,5,6,9,10,11 + 13/14 for 손보)
# --------------------------------------------------------------------------- #
SONBO_LOB = ["장기보험", "자동차보험", "일반보험"]

# row-label variants (손보 | 생보) -- matched by substring on the row label
CSM_AMORT = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "제공된 서비스의 보험계약마진")
RA_CHANGE = ("비금융위험에 대한 위험조정의 변동분", "위험해제로 인한 비금융위험에 대한 위험조정의 변동")
REV_EXPECTED = ("보고기간에 발생한 보험서비스비용 (기초 예상 측정치)",
                "보고기간에 발생한 보험서비스비용(기초 예상 측정치)",
                "예상 발생보험금 및 보험서비스비용")
COST_ACTUAL = ("발생한 보험금 및 그 밖의 발생한 보험서비스비용", "실제 발생보험금 및 보험서비스비용")


def _row_matches(r, variants):
    """True if the row label (col0 or col1) contains any variant string."""
    for c in r[:2]:
        s = _norm(c)
        for v in variants:
            if v.replace(" ", "") in s.replace(" ", ""):
                return True
    return False


def _sonbo_col_idx(t):
    """For a 손보 table with 장기/자동차/일반 columns, numeric cells appear as
    [장기, 자동차, 일반, (합계)].  Returns positions {장기:0, 자동차:1, 일반:2}."""
    return {"장기보험": 0, "자동차보험": 1, "일반보험": 2}


def _is_sonbo_lob_table(t):
    hb = " ".join(" ".join(r) for r in t.header)
    return all(k in hb for k in SONBO_LOB)


def _is_rollforward(t):
    labs = " ".join(_label(r) for r in t.rows)
    return any(k in labs for k in ("기초 보험계약", "기말 보험계약", "기초보험계약",
                                   "기말보험계약", "보험계약부채(자산)"))


def _val_at(r, pos):
    """Numeric cell at LOB position `pos` (손보) or, for 생보 (pos=None), the row TOTAL.
    The 생보 note is single-column (삼성생명) or 계약유형별 with a '계약의 유형 합계' column
    (한화생명: 사망/건강/연금저축/변액/기타 + 합계).  For the rows we extract (CSM 상각,
    RA 변동, 예상/실제 발생보험금) the contract-type components are same-sign, so the row
    total = the cell with the largest |value| (== the 합계 column)."""
    nums = _row_nums(r)
    if pos is None:
        return max(nums, key=abs) if nums else None
    return nums[pos] if len(nums) > pos else None


def _sonbo_lob_tables(tables):
    """Return the four 손보 LOB analysis tables (보험수익/보험서비스비용/재보험수익/재보험비용)
    for the CURRENT period.  Each table type appears twice (당기 then 전기) — we keep the
    FIRST occurrence in document order (DART lists 당기 before 전기)."""
    out = {}
    sig = {
        "보험수익": lambda first: first == "보험수익",
        "보험서비스비용": lambda first: first.startswith("발행한 보험계약에서 생기는 보험서비스비용"),
        "재보험비용": lambda first: first.startswith("재보험자에게 지급된 보험료 배분액"),
        "재보험수익": lambda first: first.startswith("재보험자에게서 회수한 금액"),
    }
    for t in tables:
        if not _is_sonbo_lob_table(t) or _is_rollforward(t) or not t.rows:
            continue
        first = _norm(t.rows[0][0]) if t.rows[0] else ""
        for key, pred in sig.items():
            if key not in out and pred(first):
                out[key] = t
    return out


def _sonbo_row_val(t, variants, pos):
    """Value at LOB position `pos` for the row in `t` matching `variants`."""
    if t is None:
        return None
    for r in t.rows:
        if _row_matches(r, variants):
            v = _val_at(r, pos)
            if v is not None:
                return v
    return None


def _sonbo_total(t, pos):
    """First (total) row value of an analysis table at LOB position `pos`."""
    if t is None or not t.rows:
        return None
    return _val_at(t.rows[0], pos)


def extract_tier2_sonbo(tables):
    """손보: items 4,5,6 from 보험수익/보험서비스비용 (장기 col); 9,10,11 from 재보험 notes;
    13/14 from 자동차/일반 totals across the four LOB tables."""
    tabs = _sonbo_lob_tables(tables)
    if not tabs:
        return {}
    rev_t = tabs.get("보험수익")
    cost_t = tabs.get("보험서비스비용")
    rec_t = tabs.get("재보험비용")
    rer_t = tabs.get("재보험수익")
    P = _sonbo_col_idx(rev_t or cost_t or rec_t or rer_t)
    p_jang = P["장기보험"]

    out = {}
    csm = _sonbo_row_val(rev_t, CSM_AMORT, p_jang)
    ra = _sonbo_row_val(rev_t, RA_CHANGE, p_jang)
    rev_exp = _sonbo_row_val(rev_t, REV_EXPECTED, p_jang)
    cost_act = _sonbo_row_val(cost_t, COST_ACTUAL, p_jang)
    re_csm = _sonbo_row_val(rec_t, CSM_AMORT, p_jang)
    re_ra = _sonbo_row_val(rec_t, RA_CHANGE, p_jang)
    re_rev = _sonbo_row_val(rer_t, COST_ACTUAL, p_jang)
    re_cost_exp = _sonbo_row_val(rec_t, REV_EXPECTED, p_jang)

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

    # 장기-column totals (for items 3/7/8/12 derivation downstream)
    out["_jang_rev"] = _sonbo_total(rev_t, p_jang)
    out["_jang_cost"] = _sonbo_total(cost_t, p_jang)
    out["_jang_rerev"] = _sonbo_total(rer_t, p_jang)
    out["_jang_recost"] = _sonbo_total(rec_t, p_jang)

    # 13/14 — 자동차/일반 손익 = (보험수익 − 보험서비스비용 + 재보험수익 − 재보험비용) totals
    for item_no, lob in ((13, "자동차보험"), (14, "일반보험")):
        p = P[lob]
        rev = _sonbo_total(rev_t, p)
        cost = _sonbo_total(cost_t, p)
        re_r = _sonbo_total(rer_t, p)
        re_c = _sonbo_total(rec_t, p)
        if rev is None and cost is None:
            continue
        out[item_no] = (rev or 0) - (cost or 0) + (re_r or 0) - (re_c or 0)
    return out


# Format-B 손보 note ('(재)보험손익 상세내역' — 메리츠).  Distinct row labels & a single
# structured table with 4 columns [장기(GMM), 일반-1, 자동차, 일반-2(해외)].
B_CSM = ("당기손익으로 인식한 보험계약마진 금액", "서비스제공에 따른 보험계약마진의 변동")
B_RA = ("위험해제에 따른 위험조정 변동", "위험해제에 따른 비금융위험에 대한 위험조정의 변동")
B_REV_EXP = ("예상보험금 및 보험서비스비용",)
B_COST_ACT = ("보험금 및 보험서비스비용",)            # 보험서비스비용 section
B_RE_REV = ("회수가능 보험금 및 보험서비스비용",)      # 재보험수익 section
B_RE_COST = ("회수예상 보험금 및 보험서비스비용",)     # 재보험비용 section


def _b_note_table(tables):
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(_row_matches(r, B_CSM) for r in t.rows):
                return t
    return None


def extract_tier2_sonbo_structured(tables):
    """Format-B 손보 note (메리츠).  Sections delimited by header rows
    보험수익 / 보험서비스비용 / 재보험수익 / 재보험비용 / 총 보험서비스결과.
    col0 = 장기(GMM); 자동차 & 일반 read from the '총 보험서비스결과' row."""
    t = _b_note_table(tables)
    if t is None:
        return {}
    out = {}
    # Layout drift: 분기/반기 notes double every LOB cell into [3개월, 누적] (read 누적 to match
    # the YTD statement); the annual report is single-period.  st = cell width per LOB.
    hb = " ".join(" ".join(h) for h in t.header)
    st = 2 if ("3개월" in hb and "누적" in hb) else 1
    section = None
    sect_keys = {"보험수익": "rev", "보험서비스비용": "cost",
                 "재보험수익": "re_rev", "재보험비용": "re_cost",
                 "총 보험서비스결과": "result"}
    vals = {}  # (section, kind) -> 장기(GMM) 누적 value

    def col0(r):
        nums = _row_nums(r)
        if not nums:
            return None
        return nums[st - 1] if len(nums) > st - 1 else nums[0]

    totals = {}  # 'rev'/'cost'/'re_rev'/'re_cost' -> col0 of the '총 ...' row
    total_labels = {"총 보험수익": "rev", "총 보험서비스비용": "cost",
                    "총 재보험수익": "re_rev", "총 재보험비용": "re_cost"}
    result_row = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in total_labels:
            totals[total_labels[lab]] = col0(r)
        if lab in sect_keys and (len(_row_nums(r)) == 0 or lab.startswith("총") or lab == "총 보험서비스결과"):
            if lab == "총 보험서비스결과":
                result_row = r
            else:
                section = sect_keys[lab]
            # a pure section header has no numbers
            if not _row_nums(r):
                continue
        if section == "rev":
            if _row_matches(r, B_CSM):
                vals["csm"] = col0(r)
            elif _row_matches(r, B_RA):
                vals["ra"] = col0(r)
            elif _row_matches(r, B_REV_EXP):
                vals["rev_exp"] = col0(r)
        elif section == "cost":
            if _row_matches(r, B_COST_ACT):
                vals["cost_act"] = col0(r)
        elif section == "re_rev":
            if _row_matches(r, B_RE_REV):
                vals["re_rev"] = col0(r)
        elif section == "re_cost":
            if _row_matches(r, B_RE_COST):
                vals["re_cost_exp"] = col0(r)
            elif _row_matches(r, B_CSM):
                vals["re_csm"] = col0(r)
            elif _row_matches(r, B_RA):
                vals["re_ra"] = col0(r)

    if vals.get("csm") is not None:
        out[4] = abs(vals["csm"])
    if vals.get("ra") is not None:
        out[5] = abs(vals["ra"])
    if vals.get("rev_exp") is not None and vals.get("cost_act") is not None:
        out[6] = abs(vals["rev_exp"]) - abs(vals["cost_act"])
    if vals.get("re_csm") is not None:
        out[9] = -abs(vals["re_csm"])
    if vals.get("re_ra") is not None:
        out[10] = -abs(vals["re_ra"])
    if vals.get("re_rev") is not None and vals.get("re_cost_exp") is not None:
        out[11] = abs(vals["re_rev"]) - abs(vals["re_cost_exp"])

    # 장기-column (GMM, col0) totals for items 3/7/8/12 derivation
    if totals.get("rev") is not None:
        out["_jang_rev"] = totals["rev"]
    if totals.get("cost") is not None:
        out["_jang_cost"] = totals["cost"]
    if totals.get("re_rev") is not None:
        out["_jang_rerev"] = totals["re_rev"]
    if totals.get("re_cost") is not None:
        out["_jang_recost"] = totals["re_cost"]

    # 13/14 from the '총 보험서비스결과' row.  Single-period cols [장기, 일반-1, 자동차, 일반-2];
    # 분기/반기 doubles each LOB into [3개월, 누적] -> read 누적 at index st*pos+(st-1).
    if result_row is not None:
        nums = _row_nums(result_row)
        if len(nums) >= 3 * st:
            g1, g2 = 2 * st - 1, 4 * st - 1
            out[13] = nums[3 * st - 1]                                # 자동차 (누적)
            out[14] = nums[g1] + (nums[g2] if len(nums) > g2 else 0)  # 일반 (PAA split)
    return out


def _header_has_overseas(t):
    hb = " ".join(" ".join(h) for h in t.header)
    return "해외보험" in hb or "해외" in hb


LIFE_SECTIONS = ("재보험수익", "재보험비용", "보험서비스비용", "보험수익")


def _row_section(r):
    """If the row label is prefixed with a section keyword (한화-style
    '보험수익, …' / '재보험비용, …'), return it, else None.  Order matters: check the
    재보험* prefixes before the plain 보험* ones."""
    lab = (_norm(r[0]) + " " + _norm(r[1] if len(r) > 1 else "")).replace(" ", "")
    for sec in LIFE_SECTIONS:
        if lab.startswith(sec.replace(" ", "")):
            return sec
    return None


def _life_note_total(t, variants, section=None):
    """Domestic 합계 for a 생보 note row: the embedded '계약의 유형 합계' = the max-abs
    numeric of the row (components are same-sign).  If `section` is given and the row is
    section-prefixed (한화-style), require it to match.  Returns None if no match."""
    for r in t.rows:
        if not _row_matches(r, variants):
            continue
        rsec = _row_section(r)
        if section is not None and rsec is not None and rsec != section:
            continue
        nums = _row_nums(r)
        if nums:
            return max(nums, key=abs)
    return None


def _pick_life_table(tables, must_have, context_any, section=None, prefer_no_overseas=True):
    """Among 생보 analysis tables that (a) are not rollforwards, (b) contain a row matching
    `must_have` (in `section` when the row is section-prefixed), and (c) carry one of
    `context_any` substrings, return the best: prefer tables WITHOUT 해외 columns (domestic
    합계 matches the gold), then the simpler note (fewest columns)."""
    cands = []
    for t in tables:
        if _is_rollforward(t):
            continue
        hit = False
        for r in t.rows:
            if not _row_matches(r, must_have):
                continue
            rsec = _row_section(r)
            if section is not None and rsec is not None and rsec != section:
                continue
            hit = True
            break
        if not hit:
            continue
        blob = (t.caption or "") + " " + " ".join(_label(r) + " " + _label(r, 1) for r in t.rows)
        if context_any and not any(c in blob for c in context_any):
            continue
        cands.append(t)
    if not cands:
        return None
    cands.sort(key=lambda t: (1 if (prefer_no_overseas and _header_has_overseas(t)) else 0,
                              max((len(_row_nums(r)) for r in t.rows), default=0)))
    return cands[0]


def extract_tier2_life(tables):
    """생보: items 4,5,6,9,10,11 from the 발행/출재 analysis notes (domestic 합계).
    삼성생명: single 발행 column.  한화생명: 계약유형별 columns + 합계 (excl. 해외)."""
    out = {}
    REV_CTX = ("일반보험서비스수익", "보험수익", "발행한 보험계약")
    COST_CTX = ("일반보험서비스비용", "발행한 보험계약에서 생기는 보험서비스비용", "보험서비스비용")
    RECOST_CTX = ("출재보험서비스비용", "재보험비용", "재보험자에게 지급")
    REREV_CTX = ("출재보험서비스수익", "재보험수익", "재보험자에게서 회수")

    rev_t = _pick_life_table(tables, CSM_AMORT, REV_CTX, section="보험수익")
    cost_t = _pick_life_table(tables, COST_ACTUAL, COST_CTX, section="보험서비스비용")
    rec_t = _pick_life_table(tables, CSM_AMORT, RECOST_CTX, section="재보험비용")
    rer_t = _pick_life_table(tables, COST_ACTUAL, REREV_CTX, section="재보험수익")

    csm = _life_note_total(rev_t, CSM_AMORT, "보험수익") if rev_t else None
    ra = _life_note_total(rev_t, RA_CHANGE, "보험수익") if rev_t else None
    rev_exp = _life_note_total(rev_t, REV_EXPECTED, "보험수익") if rev_t else None
    cost_act = _life_note_total(cost_t, COST_ACTUAL, "보험서비스비용") if cost_t else None
    re_csm = _life_note_total(rec_t, CSM_AMORT, "재보험비용") if rec_t else None
    re_ra = _life_note_total(rec_t, RA_CHANGE, "재보험비용") if rec_t else None
    re_rev = _life_note_total(rer_t, COST_ACTUAL, "재보험수익") if rer_t else None
    re_cost_exp = _life_note_total(rec_t, REV_EXPECTED, "재보험비용") if rec_t else None

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
    return out


def extract_tier2_abl(tables):
    """에이비엘생명 (KR0070).  Its IFRS17 보험수익/재보험비용 reconciliation note uses a
    [구분 | 당기 | 전기] TWO-PERIOD header, not a 계약유형별 합계 layout.  The generic
    extract_tier2_life reads each leg via _life_note_total = max(nums, key=abs), which picks
    the LARGER cell — and here 전기 > 당기 (2025.4Q CSM 88,926 > 82,804; RA 12,282 > 8,346),
    so the master published the PRIOR-period column (a 당기/전기 leg bug, audit 2026-06-08).
    Fix: read the 당기 column EXPLICITLY (= first data cell).  item6/11(예실차) is only a
    partial premium-side 경험조정 here → left to the generic closure (residual→기타)."""
    out = {}

    def find(cap_needs, cap_excl=()):
        needs = [c.replace(" ", "") for c in cap_needs]
        excl = [e.replace(" ", "") for e in cap_excl]
        for t in tables:
            if _is_rollforward(t):
                continue
            capf = _norm(t.caption or "").replace(" ", "")
            if all(n in capf for n in needs) and not any(e in capf for e in excl):
                return t
        return None

    def dangi(t, *labels):
        """First numeric (= 당기 column) of the first row whose col0 label matches any label."""
        if t is None:
            return None
        keys = [l.replace(" ", "") for l in labels]
        for r in t.rows:
            lab = _label(r).replace(" ", "")
            if any(k in lab for k in keys):
                nums = _row_nums(r)
                if nums:
                    return nums[0]
        return None

    rev_t = find(["잔여보장", "회수", "보험수익"], cap_excl=("재보험",))
    re_t = find(["잔여보장", "회수", "재보험"])
    csm = dangi(rev_t, "서비스의이전으로", "인식한 보험계약마진")
    ra = dangi(rev_t, "비금융위험에 대한 위험조정")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    re_csm = dangi(re_t, "서비스의이전으로", "인식한 보험계약마진")
    re_ra = dangi(re_t, "비금융위험에 대한 위험조정")
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out


# =========================================================================== #
# Per-company Tier-2 handlers (FY2025+ annual notes).
# Each returns {item_no: 백만원} + hidden 장기-block totals.  Where only a single
# 장기 net is recoverable, the handler emits _jang_net (assemble sets item2 = it,
# leaving item3/7/8 None).  Note units differ by company; each handler scales to
# 백만원 internally (손보 현대 = 원 /1e6; 한화 = 천원 /1e3; everyone else 백만원).
# Ported from the tested probe files (_plprobe_*.py); see those for derivation.
# =========================================================================== #
def _lab0(r):
    return _norm(r[0]).replace(" ", "") if r else ""


def _row_by_label(t, *subs, exact=False):
    """First row whose col0 label (spaces stripped) matches any sub."""
    for r in t.rows:
        lab = _lab0(r)
        for s in subs:
            s2 = s.replace(" ", "")
            if (lab == s2) if exact else (s2 in lab):
                return r
    return None


def _firstlab(t, *needles, exclude=()):
    """First numeric cell of the first row whose col0/col1 label contains a needle."""
    if t is None:
        return None
    for r in t.rows:
        lab = (_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
        if any(n.replace(" ", "") in lab for n in needles) \
                and not any(e.replace(" ", "") in lab for e in exclude):
            ns = _row_nums(r)
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


def _scale(out, factor, keys):
    for k in keys:
        if out.get(k) is not None:
            out[k] = out[k] * factor
    return out
