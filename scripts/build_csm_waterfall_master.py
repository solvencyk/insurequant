# -*- coding: utf-8 -*-
"""CSM Movement Waterfall master (손보, all quarters) in the tidy long schema.

Gold formula (validated vs 메리츠 FY2025 hand-built sheet, exact match):
  per stage = SUM of the 3 CSM method columns (수정소급/공정가치/그외) across the
  current-period 원수 일반모형 측정요소별 변동내역 — both 배당요소가 있는 AND 없는
  sub-tables. Stage rows: 기초순장부금액 / 신계약효과 / 순보험금융손익 / 당기손익으로
  인식한 보험계약마진 / 기말순장부금액. 가정·경험 조정 등 = residual (close − others).
  Excludes 출재(재보험자산), prior-period (전기) copies. Falls back to a combined
  원수 일반모형 block when no 배당 split exists (some filings).

Quarter is derived from the FY####_Q# path component (raw layout differs:
quarterly = KR000X_name/xml/<rcept>.xml ; annual = KR000X_name_<rcept>/<rcept>.xml).
Output: CSM_waterfall.json (8 손보 × available quarters × 6 stages).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.measurement_extractor import extract_measurement_tables, to_jsonable
from viz_build_csm_waterfall import (normalize_block_header, deduplicate,
    find_csm_leaf_cols, row_value_start, parse_num, filter_current_period_rows,
    extract_stages, STAGE_PATTERNS)

def _ns(s):  # normalize: drop ALL whitespace incl. \xa0 (KB rows lead with \xa0)
    return re.sub(r"\s", "", s) if isinstance(s, str) else ""

NB_PATS = [_ns(p) for p in STAGE_PATTERNS["new_business"]]

STAGE_ROWS = {
    1: ("기초 CSM", ["기초순장부금액"]),
    2: ("신계약 CSM", ["신계약효과"]),
    3: ("이자 부리", ["순보험금융손익"]),
    5: ("CSM 상각", ["당기손익으로인식한보험계약마진"]),
    6: ("기말 CSM", ["기말순장부금액"]),
}  # 항목 4 = 가정 및 경험 조정 등 = residual

META = {}
for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    c = r.get("원보험사코드")
    if c and c not in META:
        META[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))

# All insurers (손해 + 생명) that actually have DART raw filings (dynamic scan).
# 손보 small/digital filers (AIG·악사·하나·신한이지·서울보증·카카오페이) are PAA-only →
# no GMM CSM rollforward → legitimately yield "none". 생보 carry large 유배당 books →
# 배당합산 is essential there too.
SONBO = sorted(
    c for c, (_nm, _t, sb) in META.items()
    if sb and ("손해" in sb or "생명" in sb)
    and any((ROOT / "data" / "dart").glob(f"FY*_Q*/raw/{c}_*"))
)


def block_stages(b):
    # Reuse the proven label-variation-aware stage extractor (handles 메리츠/KB/
    # 삼성 row-label variants + CSM-column detection). Item 4 (가정·경험) = residual.
    # Some filings stack 당분기 THEN 전분기 in ONE block (미래에셋 product tables: two
    # "기초 잔액" rows, current then prior). extract_stages then reads the PRIOR period's
    # 기초/기말. Cut the block at the 전분기/전반기/전기 boundary so only the current
    # period is seen (no-op for single-period blocks → safe for everything else).
    rows = b.get("rows") or []
    for i, r in enumerate(rows):
        if i == 0 or not (r and isinstance(r[0], str)):
            continue
        if _ns(r[0]).startswith(("전분기", "전반기", "전기")):
            b = {**b, "rows": rows[:i]}
            break
    st = extract_stages(b)
    if not st:
        return None
    g = lambda k: (st.get(k) or {}).get("value_mn_krw")
    out = {1: g("opening"), 2: g("new_business"), 3: g("interest"),
           5: g("amortization"), 6: g("closing")}
    return out if (out.get(1) is not None or out.get(2) is not None) else None


def pick_group(blocks, marker):
    cands = []
    for b in blocks:
        capf = _ns(b.get("caption") or "")
        if marker not in capf or "출재일반모형" in capf or "재보험자산" in capf:
            continue
        if marker == "원수일반모형" and ("배당요소가있는" in capf or "배당요소가없는" in capf):
            continue  # combined-only: skip the 배당 splits (handled separately)
        if not any(rr and isinstance(rr[0], str)
                   and any(p in _ns(rr[0]) for p in NB_PATS)
                   for rr in (b.get("rows") or [])):
            continue
        st = block_stages(b)
        if st and st.get(1) is not None:
            cands.append(st)
    if not cands:
        return None
    opens = [c[1] for c in cands if c.get(1) is not None]
    def is_prior(c):
        cl = c.get(6)
        return cl is not None and any(abs(cl - o) <= max(1.0, abs(o) * 0.001) for o in opens if abs(o) > 1)
    cur = [c for c in cands if not is_prior(c)] or cands
    # A rollforward block missing its CLOSING (기말) is an incomplete/mis-split fragment
    # (흥국화재 2025.4Q 무배당: a duplicate block with 기말=None sits alongside the real
    # open→close block and has the larger opening, so the naive max-opening pick grabbed
    # the fragment → closing collapsed to the 유배당 sub-total only = 34억).  Prefer
    # candidates that expose a closing; fall back to all only if none do.
    complete = [c for c in cur if c.get(6) is not None] or cur
    return max(complete, key=lambda c: abs(c.get(1) or 0))


# --- Pattern 2: single 차이조정 table with 배당있는/없는 as COLUMN GROUPS -------
# (삼성화재 "구성요소별 변동분에 대한 차이조정 공시": one table, data cols laid out
#  [PV, RA, CSM, 합계] per 배당 group → sum the per-group CSM columns per row.)
STAGE_KEYS = {1: "opening", 2: "new_business", 3: "interest", 5: "amortization", 6: "closing"}


def _csm_cols_pattern2(block, data_len):
    hdr = block.get("header") or []
    cells = [c for row in hdr for c in row if isinstance(c, str)]
    fns = _ns(" ".join(cells))
    if "보험계약마진" not in fns or data_len == 0:
        return None
    # 차이조정(CER) 표 = [그룹] × [PV, RA, CSM(1+전환방법), 합계]. 그룹은 배당있는/없는
    # (삼성화재·현대·한화손보), 또는 상품라인 사망/건강/연금 (삼성생명), 또는 단일 발행
    # (한화생명, G=1). G = 그룹 총합계 칼럼 "구성요소별 보험계약 합계" 수가 가장 robust.
    g = sum(1 for c in cells if "구성요소별보험계약합계" in _ns(c))
    if g == 0:  # fallback: 배당/유무배당 group-marker cells
        if "유배당" in fns or "무배당" in fns:
            g = sum(1 for c in cells if _ns(c) in ("유배당보험계약", "무배당보험계약"))
        elif "배당요소가있는" in fns or "배당요소가없는" in fns:
            g = sum(1 for c in cells if _ns(c).startswith(("배당요소가있는", "배당요소가없는")))
    if g < 1 or data_len % g:
        return None
    stride = data_len // g        # data cols per group: [PV, RA, CSM(1+ methods), 합계]
    if stride < 4:                # need at least PV, RA, ≥1 CSM, 합계
        return None
    # CSM = every col between RA (idx 1) and the trailing 합계 (idx stride-1):
    #   삼성/현대 stride 4 → [2]; 한화 stride 6 → [2,3,4] (3 transition methods).
    return [j * stride + k for j in range(g) for k in range(2, stride - 1)]


def pattern2_stages(block):
    rows = filter_current_period_rows(block.get("rows") or [])
    data_len = max((len(r[row_value_start(r):]) for r in rows if r), default=0)
    cols = _csm_cols_pattern2(block, data_len)
    if not cols:
        return None

    def labels_of(r):
        # 한화's rollforward labels span TWO leading columns (col0 parent +
        # col1 detail, e.g. "미래 서비스와 관련된 변동" / "해당 기간에 처음 인식…") →
        # test every leading non-data label cell, not just col0.
        return [_ns(c) for c in r[: row_value_start(r)] if isinstance(c, str) and c.strip()]

    def csm_sum(r):
        data = r[row_value_start(r):]
        vals = [parse_num(data[i]) for i in cols if 0 <= i < len(data)]
        vals = [v for v in vals if v is not None]
        return sum(vals) if vals and any(v != 0 for v in vals) else None

    def find(key, start=False, exclude=(), extra=()):
        pats = [_ns(p) for p in STAGE_PATTERNS[key]] + [_ns(p) for p in extra]
        for r in rows:
            labs = labels_of(r)
            if not labs or any(x in lab for lab in labs for x in exclude):
                continue
            if any((lab.startswith(p) if start else p in lab) for lab in labs for p in pats):
                v = csm_sum(r)
                if v is not None:
                    return v
        return None

    def find_anchored(marker):
        # 동양생명-style 차이조정표: the 기초/기말 marker sits on its own (value-less)
        # row, and the opening/closing CSM lives on the FOLLOWING 발행한 보험계약부채
        # (or 보험계약(순)부채) row, which itself carries no 기초/기말 label. Scan in
        # order: once the section marker is seen, return the first balance-sheet row
        # (부채/순부채) with a non-zero CSM before the next stage marker arrives.
        bs = ("발행한보험계약부채", "보험계약순부채", "보험계약부채")
        other = "기말" if marker == "기초" else "기초"
        armed = False
        for r in rows:
            labs = labels_of(r)
            if any(lab.startswith(marker) for lab in labs):
                armed = True
                v = csm_sum(r)
                if v is not None:
                    return v
                continue
            if not armed:
                continue
            if any(lab.startswith(other) for lab in labs):
                return None  # crossed into the other section without a value
            if any(any(lab.startswith(p) for p in bs) for lab in labs):
                v = csm_sum(r)
                if v is not None:
                    return v
        return None

    def find_interest():
        # 이자 부리 = 보험계약의 순 금융손익 + 환율변동효과 등 (있으면). 삼성생명 IR이
        # CSM 이자효과에 환율변동을 가산 — 2024엔 환율 행 존재(가산), 2025엔 없음(0).
        base = find("interest")
        fx = None
        for r in rows:
            if any("환율변동" in lab for lab in labels_of(r)):
                v = csm_sum(r)
                if v is not None:
                    fx = (fx or 0) + v
        if base is None and fx is None:
            return None
        return (base or 0) + (fx or 0)

    # opening/closing: prefer the 보험계약부채(자산) aggregate that *starts with* 기초/기말;
    # drop the 자산인/부채인 sub-component rows (한화·삼성 split these, 자산인 row = 0).
    # Fall back to the section-anchored 발행한 보험계약부채 row (동양생명) when the
    # 기초/기말 label row itself carries no CSM.
    out = {1: find("opening", start=True, exclude=("자산인", "부채인")) or find_anchored("기초"),
           2: find("new_business", extra=("최초 발행한 계약",)),
           3: find_interest(),
           5: find("amortization"),
           6: find("closing", start=True, exclude=("자산인", "부채인")) or find_anchored("기말")}
    # A genuine rollforward must expose opening+closing AND at least one movement
    # row (신계약 or 상각). DB's 배당×전환방법 6-CSM-column table trips the 배당 gate
    # but its non-uniform layout yields no movement rows → reject (avoid garbage).
    ok = out.get(1) is not None and out.get(6) is not None and (
        out.get(2) is not None or out.get(5) is not None)
    return out if ok else None


def _reins_header(b):
    # Exclude 보유 재보험 CER tables. Test the HEADER only — the CER table's caption
    # is often mis-attributed (삼성화재 caption shows "관계기업"), so caption-based
    # exclusion would wrongly drop the 원수 발행 table.
    h = _ns(" ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
    return any(k in h for k in ("재보험", "출재", "보유한재보험"))


def _select(cands, anchor, fallback="min"):
    """Pick the right CER/rollforward among candidates (별도 당기).
    Two confounds: 전기 copies (prior period) and 연결 copies (larger, +subs).
    - With an FY anchor (prior-year 별도 기말 = this year's opening, in 억): take the
      candidate whose OPENING (normalized to 억) is closest to the anchor. Resolves
      BOTH — 당기 opening ≈ anchor (전기 opening = prior-year start, far) and 별도
      opening ≈ anchor (연결 opening larger, far).
    - Without anchor (first observed year): drop is_prior copies, then MIN opening
      (별도 ≤ 연결; pattern2) or MAX (combined-agn, avoid method/segment sub-blocks)."""
    opens = [s[1] for s in cands if s.get(1) is not None]
    cur = [s for s in cands if not _is_prior_stage(s, opens)] or cands
    if anchor and abs(anchor) > 1:
        allv = [v for s in cur for v in s.values() if v is not None]
        mag = max((abs(v) for v in allv), default=0.0)
        udiv = 1e6 if mag > 1e10 else (1e3 if mag > 1e8 else 1.0)  # raw → 백만
        norm = lambda s: (s.get(1) or 0) / udiv / 100.0            # 백만 → 억
        return min(cur, key=lambda s: abs(norm(s) - anchor))
    return (min if fallback == "min" else max)(cur, key=lambda s: abs(s.get(1) or 0))


def pick_pattern2(blocks, anchor=None):
    cands = [st for b in blocks if not _reins_header(b) and (st := pattern2_stages(b)) is not None]
    return _select(cands, anchor, "min") if cands else None


_EXCLUDE_KW = ("재보험", "출재", "보유한재보험", "관계기업", "종속기업", "관계종속", "공동기업")


def _is_prior_stage(s, opens):
    """A block is a prior-period copy if its CLOSING matches the OPENING of a
    *different* period block (전기.기말 ≈ 당기.기초). Must skip the block's own
    opening: in quarterly filings 기초≈기말 (small one-quarter movement), and a naive
    close≈any-opening test would match the block's own opening and wrongly flag the
    current 당분기 block as prior."""
    cl, op = s.get(6), s.get(1)
    if cl is None:
        return False
    for o in opens:
        if abs(o) <= 1:
            continue
        if op is not None and abs(o - op) <= max(1.0, abs(op) * 0.001):
            continue  # skip own opening (quarterly 기초≈기말 false positive)
        if abs(cl - o) <= max(1.0, abs(o) * 0.001):
            return True
    return False


def _drop_prior(cands):
    opens = [s[1] for s in cands if s.get(1) is not None]
    return [s for s in cands if not _is_prior_stage(s, opens)] or cands


def _is_prior_caption(cap):
    """Quarterly reports split 당분기/전분기 (or 당반기/전반기) into separate blocks
    with the SAME structure. The prior-period block's value continuity (close ≈
    current opening) does NOT hold for YTD quarterly filings (전분기 close = last
    year's same-quarter, not the year-start opening), so is_prior(value) misses it.
    Catch it by caption: a block whose caption (after the leading enumerator) starts
    with 전분기/전반기/전기. Annual 당기/전기 share the caption '...1) 당기' → not
    matched here (handled by is_prior value-continuity instead)."""
    s = re.sub(r"^[\s(]*\d+[\).]\s*", "", (cap or "").strip())
    if s.startswith(("전분기", "전반기", "전기")):
        return True
    # 케이디비생명-style: the prior period is labeled '제37(전)기' — the '(전)기' marker sits
    # AFTER the 기수 (제N) and the block often carries a product enumerator ('나. 제37(전)기',
    # '가. 제38(당)기'), so a leading-anchored test misses it and the prior block survives as a
    # candidate (its opening = prior-year start → poisons the FY anchor → every 2025 quarter
    # copies 2024).  SEARCH the raw caption for the literal '제N(전)기' form anywhere: it is
    # specific to the prior copy — the combined title '당기와 전기 중…' has no parens, and the
    # current segments use '(당)기'.
    return bool(re.search(r"제\s*\d+\s*\(\s*전\s*\)\s*기", cap or ""))


_CUR_HDR = ("당기", "당반기", "당분기", "당기말", "당반기말")
_PRIOR_HDR = ("전기", "전반기", "전분기", "전기말", "전반기말")


def _is_prior_header(b):
    """Annual 당기/전기 filings whose caption is the shared '당기 및 전기 …' often split
    the period into TWO blocks — one with 당기, one with 전기 — distinguished only by a
    standalone period cell in the HEADER (구분 row: ['구분','전기']), NOT the caption.
    is_prior(value) misses the 전기 block when a 사업결합 restatement makes 전기.기말
    (pre-combination) ≠ the extractor's restated 당기 opening (KB라이프 2023: 전기.기말
    2,373,818 vs 당기 기초 3,132,762), so the 전기 block leaks into the segment sum and
    DOUBLE-COUNTS. Drop any block whose header carries a 전기-family period marker and NO
    당기-family marker (a combined 당기|전기 table keeps 당기 → not dropped)."""
    cells = [_ns(c) for row in (b.get("header") or []) for c in row if isinstance(c, str)]
    has_prior = any(c in _PRIOR_HDR for c in cells)
    has_cur = any(c in _CUR_HDR for c in cells)
    return has_prior and not has_cur


def _comparable_min(cands):
    """Pick 별도 among full-book candidates, robust to garbage partials.
    MAX (largest) is the right default — the real 별도 rollforward is the biggest;
    smaller candidates are usually tiny/negative partial blocks (출재 leakage,
    수준3, empty templates). BUT when a legit 연결 full-book coexists with 별도
    (한화생명: 별도 9.24M < 연결 13.30M), MAX wrongly picks 연결. Resolve both:
    keep only candidates whose |opening| ≥ 50% of the max (drops garbage partials),
    then take the MIN (= 별도 in a 별도/연결 pair; = the sole real block otherwise)."""
    opens = [abs(s.get(1) or 0) for s in cands]
    mx = max(opens, default=0.0)
    comp = [s for s, o in zip(cands, opens) if o >= 0.5 * mx] or cands
    return min(comp, key=lambda s: abs(s.get(1) or 0))


def _double_total_sum(cur):
    """Annual no-anchor 별도 reconstruction by SEGMENT SUM, confirmed by a disclosed
    grand total. Generalizes the double-decomposition case: some insurers disclose the
    same 별도 book BOTH as a combined total AND broken into disjoint segments (DB생명:
    14.5 통합 + 무배당/변액/배당여부 splits; 미래에셋·케이디비: 측정요소 통합 + 상품/배당
    segments). Cluster the (prior-dropped) blocks by opening proximity (별도/연결 dups
    collapse, distinct segments stay apart) and take the per-cluster 별도 (MIN). SUM the
    cluster picks ONLY IF some candidate block's opening ~= that sum (the disclosed
    combined total, ≤1%, CONFIRMS the picks form a complete decomposition). This keeps
    safe: a plain 별도/연결 pair (한화생명: 별도 9.24M, 연결 13.30M — no block equals their
    13.30+9.24=22.5M sum) is NEVER summed → falls back to _comparable_min (MIN=별도).
    Requires ≥3 picks (a 2-element set is a 별도/연결 near-pair, never a decomposition).
    Returns the summed stages, or None (no confirmed decomposition)."""
    picks = _opening_clusters(cur)
    if len(picks) < 3:
        return None
    psum = sum(p.get(1) or 0 for p in picks)
    if abs(psum) <= 1:
        return None
    if not any(s.get(1) is not None and abs((s.get(1) or 0) - psum) <= abs(psum) * 0.01
               for s in cur):
        return None
    return {no: sum((p.get(no) or 0) for p in picks) for no in STAGE_KEYS}


def _dedup_axes(picks):
    """Double-decomposition guard for a SEGMENT SUM. Some insurers disclose the same book
    under TWO orthogonal axes within one note (미래에셋 annual: 배당 [유배당+기타] AND 상품별
    [사망/건강/연금/저축/기타] — each axis sums to the whole book). Summing every segment then
    double-counts. Detect it on the per-cluster 별도 picks and return ONLY one axis:
      • partition the picks into two DISJOINT subsets whose opening-sums are ~equal (≤2%,
        i.e. each ≈ half the grand total) → keep the axis with MORE segments (finer split).
    A small subset-partition search (picks count is tiny, ≤~8). When no such balanced
    partition exists (a single-axis decomposition like 교보 무배당+변액+유배당) the picks are
    returned unchanged."""
    from itertools import combinations
    n = len(picks)
    if n < 3:
        return picks
    opens = [abs(p.get(1) or 0) for p in picks]
    total = sum(opens)
    if total <= 1:
        return picks
    half = total / 2.0
    best = None
    idx = list(range(n))
    for r in range(1, n // 2 + 1):
        for combo in combinations(idx, r):
            s = sum(opens[k] for k in combo)
            if abs(s - half) / half > 0.02:
                continue
            other = [k for k in idx if k not in combo]
            if abs(s - sum(opens[k] for k in other)) / max(s, 1) <= 0.02:
                keep = list(combo) if len(combo) >= len(other) else other
                if best is None or len(keep) > len(best):
                    best = keep
    return [picks[k] for k in best] if best else picks


def _segment_min_sum(cands):
    """Product/dividend segment tables: each segment is disclosed as a (별도, 연결) near-
    duplicate pair (삼성생명 2024 annual: 사망/건강/연금 each twice; 미래에셋: 상품별 every
    quarter). Cluster by opening proximity (별도/연결 collapse, distinct segments stay
    apart), take MIN (별도) per cluster, drop any double-decomposition axis (미래에셋 annual
    discloses both 배당 AND 상품별 — _dedup_axes keeps one), then SUM. Returns
    (merged, n_segments)."""
    cur = _drop_prior(cands)
    picks = _dedup_axes(_opening_clusters(cur))
    merged = {no: sum((p.get(no) or 0) for p in picks) for no in STAGE_KEYS}
    return merged, len(picks)


def _opening_clusters(sts):
    """Cluster stage-blocks by opening proximity (>10% apart = a genuinely DISTINCT
    sub-portfolio; ≤10% = the same book's 별도/연결 near-duplicate). Take MIN (=별도)
    per cluster. Returns the list of per-cluster 별도 picks (one per distinct opening
    magnitude). Mirrors _segment_min_sum's clustering so disjoint product/measurement
    segments are summed while 별도/연결 copies collapse to one."""
    order = sorted(range(len(sts)), key=lambda i: abs(sts[i].get(1) or 0), reverse=True)
    used, picks = [False] * len(sts), []
    for i in order:
        if used[i]:
            continue
        oi = abs(sts[i].get(1) or 0)
        grp = [sts[i]]; used[i] = True
        for j in order:
            if not used[j] and oi > 0 and abs(oi - abs(sts[j].get(1) or 0)) / oi <= 0.10:
                grp.append(sts[j]); used[j] = True
        picks.append(min(grp, key=lambda s: abs(s.get(1) or 0)))  # 별도 = smaller
    return picks


def _caption_segment_sum(cands):
    """농협-style annual note that splits the 원수 발행 CSM rollforward into 2+ disjoint
    measurement/product sub-tables (유배당/무배당, or 수정소급·공정가치·그밖) under ONE
    caption (e.g. "(9-1-2) 측정요소별 변동내역"). The 별도 total = SUM of the current-
    period sub-tables. Guards against the confounds the scalar fallbacks already cover:
      • 별도/연결 of the SAME book (교보·한화생명) → openings within 10% → one cluster,
        NOT summed (cluster-MIN keeps 별도).
      • 당기/전기 prior copies share the caption → dropped first by value-continuity.
    Annual (no-anchor) only — quarterly anchored filings are left to _select, which the
    YTD anchor already disambiguates (segmenting them risks hijacking multi-caption
    books whose total spans several notes). Fires only when one caption group has ≥2
    DISTINCT-opening clusters; returns the summed stages or None."""
    from collections import defaultdict
    groups = defaultdict(list)
    for st, cap in cands:
        groups[cap].append(st)
    best = None
    for cap, sts in groups.items():
        sub = _opening_clusters(_drop_prior_pairs(sts))
        if len(sub) < 2:
            continue
        if best is None or len(sub) > len(best):
            best = sub
    if not best:
        return None
    merged = {no: 0.0 for no in STAGE_KEYS}
    for s in best:
        for no in merged:
            merged[no] += (s.get(no) or 0)
    return merged


def _drop_prior_pairs(sts):
    opens = [s[1] for s in sts if s.get(1) is not None]
    return [s for s in sts if not _is_prior_stage(s, opens)] or sts


def _anchor_segment_sum(cands, anchor):
    """Anchored quarterly fallback for a multi-segment 별도 book whose product-line
    caption was truncated (삼성생명 2025.1Q: '상품라인' marker lost → seg flag off, and
    the 출재 sub-segments would pollute a naive sum). When NO single block's opening
    matches the FY anchor (별도 year-start, 억) but the SUM of the MAJOR opening-clusters
    does, return that sum. Safety: (a) skip if a single block already nails the anchor;
    (b) drop 출재/minor clusters (opening < 10% of the largest); (c) accept only if the
    reconstructed opening matches the anchor within 2% — so it never fires for single-
    block filings and never over-counts (the anchor validates the reconstruction)."""
    allv = [v for s in cands for v in s.values() if v is not None]
    mag = max((abs(v) for v in allv), default=0.0)
    udiv = 1e6 if mag > 1e10 else (1e3 if mag > 1e8 else 1.0)   # raw → 백만
    norm = lambda v: (v or 0) / udiv / 100.0                    # 백만 → 억
    tol = max(1.0, abs(anchor) * 0.02)
    if any(abs(norm(s.get(1)) - anchor) <= tol for s in cands):
        return None                                            # a single block = the total
    picks = _opening_clusters(cands)
    if len(picks) < 2:
        return None
    mx = max((abs(p.get(1) or 0) for p in picks), default=0.0)
    major = [p for p in picks if abs(p.get(1) or 0) >= 0.10 * mx]   # drop 출재/minor
    if len(major) < 2:
        return None
    summed = {no: sum((p.get(no) or 0) for p in major) for no in STAGE_KEYS}
    return summed if abs(norm(summed.get(1)) - anchor) <= tol else None


def pick_combined_agnostic(blocks, anchor=None, code=None):
    """Caption-agnostic combined 원수 CSM rollforward (농협·DB·코리안리 method-split,
    + 분기보고서 simple rollforward e.g. 삼성화재 Q1/Q3). Excludes 재보험/관계기업.
    No 기초/기말/신계약 label gate: block_stages already validates open+close+movement
    via STAGE_PATTERNS (the quarterly closing label doesn't start with 기말).
    Three basis confounds resolved here (gold is always 별도):
      • 상품라인 segment tables (삼성생명 2024 annual) → cluster-min-sum 별도 segments.
      • 측정요소/유무배당 segments under one caption (농협 annual) → caption-group sum.
      • full-book 별도/연결 pair (한화생명 2024 annual) → 별도 = MIN opening."""
    cands, seg = [], False
    for b in blocks:
        cap = b.get("caption") or ""
        if _is_prior_caption(cap):  # quarterly 전분기/전반기 prior block
            continue
        if _is_prior_header(b):     # annual 당기/전기 split: drop the 전기-header block
            continue
        ctx = _ns(cap) + _ns(
            " ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
        capn = _ns(cap)
        # A COMBINED net-balance note '순보험계약부채 및 순재보험계약자산' (KB 분기 rollforward)
        # carries BOTH 보험계약부채 AND 재보험계약자산 in one caption; block_stages reads the
        # 원수 보험계약마진 there (gold-matched), with 재보험 in separate rows.  This is the ONLY
        # case where a 재보험-mentioning block is kept — detected by requiring BOTH tokens so it
        # cannot match a pure 출재 note or a generic '기말보험계약부채(자산)' caption (푸본현대).
        combined_net = "보험계약부채" in capn and "재보험계약자산" in capn
        if combined_net:
            if any(k in ctx for k in ("관계기업", "종속기업", "관계종속", "공동기업")):
                continue
            # but still drop it if it is actually a pure 출재 table (first data row → 재보험)
            rows0 = [r for r in (b.get("rows") or [])
                     if isinstance(r, list) and r and isinstance(r[0], str) and _ns(r[0])]
            if rows0 and _ns(rows0[0][0]).startswith(("재보험", "출재")):
                continue
        else:
            # original exclusions (unchanged → no regression for 푸본·농협·DB·코리안리 etc.)
            if any(k in ctx for k in _EXCLUDE_KW):
                continue
            if any(isinstance(r, list) and r and isinstance(r[0], str) and "재보험" in r[0]
                   for r in (b.get("rows") or [])):
                continue
        st = block_stages(b)
        if st and st.get(1) is not None and st.get(6) is not None and (
                st.get(2) is not None or st.get(5) is not None):
            cands.append((st, _ns(cap)))
    if not cands:
        return None
    sts = [st for st, _cap in cands]
    # Product-line segment note: the 별도 book is split by product line and disclosed as
    # separate (별도, 연결) blocks per segment, with NO combined total. Detect via the
    # 상품라인 caption (삼성생명) OR ≥3 distinct product-line markers (미래에셋 every quarter:
    # 사망/건강/연금/저축/기타 — its 상품별 caption is truncated to 'i)사망' etc.). These must
    # be SUMMED, not single-picked; _segment_min_sum clusters (별도/연결 collapse) + drops a
    # double-decomposition axis (미래에셋 annual: 배당 AND 상품별) + sums. Empirically only
    # 미래에셋 triggers the ≥3-marker rule (손보/타 생보 use 배당 or 측정요소 axes, not
    # product lines), so this generalizes the former per-code KR0079 handler.
    _PROD_KW = ("사망", "건강", "연금", "저축", "종신", "보장", "상해")
    if any("상품라인" in cap for _st, cap in cands) or \
            sum(1 for kw in _PROD_KW if any(kw in cap for _st, cap in cands)) >= 3:
        seg = True
    # Disjoint sub-portfolio segmentation: the 별도 book is one DOMINANT block + smaller
    # DISJOINT blocks (무배당 + 유배당 + 변액, or main GMM + 변액/특별계정) that sum to the
    # total, with NO combined-total block. Distinguish from a 별도/연결 pair (the SAME book at
    # two consolidation levels — comparable magnitudes): cluster by opening (별도/연결 collapse,
    # 전기 dropped); if the 2nd-largest cluster is < 40% of the largest, the rest are disjoint
    # sub-portfolios → SUM them; a 별도/연결 pair (2nd ≥ 40%, e.g. 한화생명 별도 9.24M vs 연결
    # 13.30M) is NOT summed. Caption-INDEPENDENT → handles 교보·신한라이프 (explicit 무배당/변액
    # captions) AND 푸본현대 (generic '기말보험계약부채' captions). Product-line segments
    # (미래에셋·삼성생명: comparable sizes, ≥40%) fall through to the seg path below.
    _picks0 = _opening_clusters(_drop_prior(sts))
    if len(_picks0) >= 2:
        _op = sorted((abs(p.get(1) or 0) for p in _picks0), reverse=True)
        if _op[0] > 0 and _op[1] < 0.40 * _op[0]:
            return {no: sum((p.get(no) or 0) for p in _picks0) for no in STAGE_KEYS}
    if seg:  # product-line segments → sum 별도 segments (anchor-independent)
        # Double-decomposition (미래에셋 every quarter: the book is disclosed BOTH on the
        # 배당 axis 유배당+무배당 AND the 상품별 axis 사망/건강/연금/저축 — summing all axes
        # double-counts). When per-product captions exist, sum ONLY the product-marked
        # segments (excluding the 배당-axis blocks). Caption-based → not code-scoped, fires
        # every quarter (fixes 미래에셋 Q1-3 + prior years, not just the annual gold point).
        prod = [st for st, cap in cands if any(kw in cap for kw in _PROD_KW)]
        if len(prod) >= 2:
            picks = _opening_clusters(_drop_prior(prod))
            if len(picks) >= 2:
                return {no: sum((p.get(no) or 0) for p in picks) for no in STAGE_KEYS}
        merged, ncl = _segment_min_sum(sts)   # 삼성생명 상품라인 (no per-product captions)
        if ncl >= 2:
            return merged
    cur = _drop_prior(sts)
    if anchor and abs(anchor) > 1:
        ssum = _anchor_segment_sum(cur, anchor)   # multi-segment book, caption truncated
        if ssum is not None:                       # (삼성생명 2025.1Q)
            return ssum
        return _select(cur, anchor)          # closest-to-anchor (반기/분기 전기·연결)
    # no anchor (annual Q4): 농협-style note splits the 별도 book into 2+ disjoint sub-
    # tables under one caption → sum them; else a total-confirmed segment sum (DB생명·
    # 케이디비 통합+분할 double-decomposition); else 별도 among comparable full-books.
    cseg = _caption_segment_sum(cands)
    if cseg is not None:
        return cseg
    dts = _double_total_sum(cur)
    if dts is not None:
        return dts
    return _comparable_min(cur)


def _seg_cands(blocks):
    """Current-period 원수 CSM rollforward blocks (exclude 재보험/관계기업/전기), each
    tagged (stages, _src, normalized-caption). Shared by pick_segment_760 and
    pick_combined_agnostic so they see the same candidate universe."""
    cands, seg = [], False
    for b in blocks:
        cap = b.get("caption") or ""
        if _is_prior_caption(cap):
            continue
        if _is_prior_header(b):
            continue
        ctx = _ns(cap) + _ns(
            " ".join(" ".join(str(c) for c in row) for row in (b.get("header") or [])))
        if any(k in ctx for k in _EXCLUDE_KW):
            continue
        if any(isinstance(r, list) and r and isinstance(r[0], str) and "재보험" in r[0]
               for r in (b.get("rows") or [])):
            continue
        st = block_stages(b)
        if st and st.get(1) is not None and st.get(6) is not None and (
                st.get(2) is not None or st.get(5) is not None):
            cands.append((st, b.get("_src", ""), _ns(cap)))
            # 상품라인 (삼성생명) / 상품별 (미래에셋) = a product sub-breakdown that is
            # ORTHOGONAL to the 유배당/무배당 (or 별도/연결) split — the same book is
            # disclosed twice, so naively summing every segment double-counts. Route
            # these to _segment_min_sum (in pick_combined_agnostic) instead.
            if "상품라인" in _ns(cap) or "상품별" in _ns(cap):
                seg = True
    return cands, seg


def _strip_aggregate(picks):
    """When the 별도 segment note lists a GRAND-TOTAL block alongside its components
    (메트라이프생명 2025.4Q: a 측정요소별 변동 total + 유/무배당 + 변액 sub-blocks), the
    total's opening ≈ the sum of the component openings.  Naively summing every cluster then
    double-counts (기초 = 2×전년말).  If exactly one pick's opening matches the sum of the
    others (within 2%), it is that aggregate → drop it so the components are counted once.
    No-ops for genuinely disjoint segments (DB손보·롯데: no grand-total block listed)."""
    if len(picks) < 2:
        return picks
    for i, p in enumerate(picks):
        oi = abs(p.get(1) or 0)
        rest = sum(abs(q.get(1) or 0) for j, q in enumerate(picks) if j != i)
        if oi > 0 and rest > 0 and abs(oi - rest) <= 0.02 * oi:
            return [q for j, q in enumerate(picks) if j != i]
    return picks


def pick_segment_760(blocks):
    """Annual 별도 주석 (_00760) that splits the 원수 발행 CSM rollforward into 2+
    disjoint product/dividend segments as separate (current, prior) block pairs —
    e.g. DB손보 (장기무배당 + 일반), 롯데손보 (배당있는·없는 장기). The captions on the
    inner segment blocks are frequently lost/mis-attributed (롯데 inherits '<제80(전)기>'
    on a current-period block), so this is driven by VALUE, not caption:
      • restrict to _00760 (별도, the gold basis) — drops the false-positive 5-row
        rollforwards the main XML yields from unrelated notes (관계기업/액면분할);
      • drop prior copies by value-continuity;
      • cluster the rest by opening proximity (별도/연결 near-duplicates collapse,
        genuinely disjoint segments stay apart) and SUM the per-cluster 별도 picks.
    Skips 상품라인 books (삼성생명: 별도+연결 per segment → handled by _segment_min_sum
    in pick_combined_agnostic, which this would double-count). Annual only (no anchor)."""
    cands, seg = _seg_cands(blocks)
    if seg:
        return None
    sub = [c for c in cands if c[1].endswith("_00760.xml")]
    if not sub:
        return None
    picks = _strip_aggregate(_opening_clusters(_drop_prior([c[0] for c in sub])))
    if len(picks) < 2:
        return None
    return {no: sum((p.get(no) or 0) for p in picks) for no in STAGE_KEYS}


def waterfall(blocks, anchor=None, code=None):
    dang = pick_group(blocks, "배당요소가있는")
    mu = pick_group(blocks, "배당요소가없는")
    # Require BOTH 배당 sub-tables: a real 배당-split filing has 유배당 AND 무배당.
    # When only one matches (롯데 25.4Q has just a tiny 유배당 sub-table) the sum is
    # a partial → fall through to pattern2/combined which sees the full table.
    if dang and mu:
        merged = {no: (dang.get(no) or 0) + (mu.get(no) or 0) for no in STAGE_ROWS}
        # New-business CSM is economically ≥0. A materially negative item-2 means
        # the 배당 sub-tables were mismatched (한화: 유/무배당 in different units +
        # a non-CSM column) → reject and fall through to the combined path.
        if (merged.get(2) or 0) >= -10_000:
            return merged, "배당합산"
    if anchor is None:  # annual 별도(_00760) multi-segment note → sum segments (DB·롯데)
        s760 = pick_segment_760(blocks)
        if s760:
            return s760, "별도세그합산"
    p2 = pick_pattern2(blocks, anchor)   # 삼성·현대·한화·삼성생명 차이조정표
    if p2:
        return p2, "배당칼럼합산"
    comb = pick_group(blocks, "원수일반모형")  # combined 원수 block (caption marker)
    if comb:
        return comb, "combined"
    agn = pick_combined_agnostic(blocks, anchor, code)  # caption-agnostic (농협·DB·코리안리·분기 단순표)
    if agn:
        return agn, "combined-agn"
    return None, None


def quarter_from(path: Path):
    m = re.search(r"FY(\d{4})_Q(\d)", str(path))
    return f"{m.group(1)}.{m.group(2)}Q" if m else None


def blocks_for_dir(rd, name):
    xmls = {}
    for x in list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml")) + list(rd.glob("extracted/*.xml")):
        if x.name.endswith("_00761.xml"):  # drop 연결 주석
            continue
        xmls.setdefault(x.name, x)
    tables = []
    for x in sorted(xmls.values()):
        try:
            for t in extract_measurement_tables(x, company_name=name):
                jt = to_jsonable(t)
                jt["_src"] = x.name          # provenance: _00760 = 별도 주석 (gold basis)
                tables.append(jt)
        except Exception:
            pass
    out = []
    for b in deduplicate(tables):
        nb = normalize_block_header(b)
        nb["_src"] = b.get("_src", "")       # survive normalize
        out.append(nb)
    return out


def _annual_newbiz_from_detail(blocks):
    """Recover 신계약 when the aggregate comes out NEGATIVE.  The annual(4Q) 사업보고서 차이조정 can
    merge the new-business child row into its parent '미래 서비스와 관련된 변동' (rowspan collapse →
    column shift), so the build reads the parent's net (신계약+가정) as 신계약.  The standalone
    '처음/최초 인식한 계약' detail row still carries the true value: per contiguous csm_cols run take
    ONLY the LAST column (the trailing 보험계약마진 in the [PV, RA, 보험계약마진] layout — the run's
    earlier columns are PV/RA in the new-business row, unlike CSM-only movement rows).  Return the
    largest POSITIVE per-row CSM sum (= 당기 원수 발행; 전기/출재 rows are smaller or negative)."""
    best = None
    NB = ("처음인식한계약", "최초인식한계약", "해당기간에처음인식", "당기최초인식한계약")
    for b in blocks:
        rows = filter_current_period_rows(b.get("rows") or [])
        data_len = max((len(r[row_value_start(r):]) for r in rows if r), default=0)
        cols = _csm_cols_pattern2(b, data_len)
        if not cols:
            continue
        last_cols, run = [], [cols[0]]
        for c in cols[1:]:
            if c == run[-1] + 1:
                run.append(c)
            else:
                last_cols.append(run[-1])
                run = [c]
        last_cols.append(run[-1])
        for r in rows:
            lab = _ns("".join(str(c) for c in r[:row_value_start(r)] if isinstance(c, str)))
            if not any(p in lab for p in NB) or "미래서비스" in lab or "손실부담" in lab:
                continue
            data = r[row_value_start(r):]
            s = sum(v for j in last_cols if 0 <= j < len(data)
                    and (v := parse_num(data[j])) is not None)
            if s > 0 and (best is None or s > best):
                best = s
    return best


def waterfall_for_dir(rd, name, anchor=None):
    """Return (vals dict {1..6: 억}, src) for one company-quarter raw dir.
    anchor (억) = this year's opening (= prior-year 별도 Q4 기말); disambiguates
    당기/전기 + 별도/연결 in 반기/분기 차이조정표."""
    blocks = blocks_for_dir(rd, name)
    if not blocks:
        return None, None
    m = re.match(r"(KR\d+)_", rd.name)
    wf, src = waterfall(blocks, anchor, m.group(1) if m else None)
    if not wf:
        return None, src
    if (wf.get(2) or 0) < 0:                      # negative 신계약 = impossible → recover from detail
        nb = _annual_newbiz_from_detail(blocks)
        if nb is not None:
            wf = {**wf, 2: nb}
            src = (src or "") + "+nb"
    mag = max((abs(v) for v in wf.values() if v is not None), default=0.0)
    udiv = 1_000_000.0 if mag > 1e10 else (1_000.0 if mag > 1e8 else 1.0)  # 원/천원→백만
    if udiv != 1.0:
        wf = {no: (v / udiv if v is not None else None) for no, v in wf.items()}
    clo = wf.get(6) or 0
    assum = clo - ((wf.get(1) or 0) + (wf.get(2) or 0) + (wf.get(3) or 0) + (wf.get(5) or 0))
    vals = {1: wf.get(1), 2: wf.get(2), 3: wf.get(3), 4: assum, 5: wf.get(5), 6: wf.get(6)}
    return {no: (round(v / 100, 1) if v is not None else None) for no, v in vals.items()}, src


def _fix_annual_newbiz(rows_out):
    """Annual(4Q) 사업보고서 차이조정표 sometimes merges 신계약 into the parent '미래 서비스와
    관련된 변동' row (parent/child rowspan collapse → column shift), so the extracted 신계약(item2)
    comes out implausibly small/negative.  New-business CSM is cumulative YTD and can NEVER decrease
    within a FY, so 4Q 신계약 < 3Q 신계약 ⇒ mis-merge.  Carry 4Q YTD forward from 3Q and absorb the
    difference into 가정(item4) to preserve the closing identity (the annual note does not separate
    the Q4 standalone 신계약 — it folds into 미래서비스변동, here routed to 가정).  Fires only on the
    impossible-decrease case (한화손해 2025.4Q)."""
    idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows_out}
    fixes = []
    for (kr, q, no), r in list(idx.items()):
        if no != 2 or not q.endswith("4Q"):
            continue
        nb4 = r.get("값")
        q3 = idx.get((kr, f"{q[:4]}.3Q", 2))
        nb3 = (q3 or {}).get("값")
        if nb4 is None or nb3 is None or nb4 >= nb3:
            continue
        delta = round(nb3 - nb4, 1)
        r["값"] = nb3                                   # carry-forward 신계약 YTD
        a4 = idx.get((kr, q, 4))                         # 가정 absorbs to keep 기초+Σ=기말
        if a4 and a4.get("값") is not None:
            a4["값"] = round(a4["값"] - delta, 1)
        fixes.append(f"{r['원수사명']} {q}: 신계약 {nb4}→{nb3} (Δ{delta} 가정 흡수; 연차 병합행 보정)")
    return fixes


def main():
    rows_out = []
    cov = {}
    labels = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정 등",
              5: "CSM 상각", 6: "기말 CSM"}
    def qkey(rd):
        m = re.search(r"FY(\d{4})_Q(\d)", str(rd))
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    for kr in SONBO:
        name, ticker, sb = META.get(kr, (kr, None, "손해보험"))
        dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()), key=qkey)
        # Pass 1 — annual (Q4) WITHOUT anchor: pattern2 min-fallback → 별도 (gold-validated;
        # annual 전기 dropped by is_prior). Record the FY-start (Q4 기초) and FY-end (Q4 기말).
        annual_open, annual_close = {}, {}
        for rd in dirs:
            q = quarter_from(rd)
            if q and q.endswith("4Q"):
                av, _ = waterfall_for_dir(rd, name, None)
                if av:
                    if av.get(1) is not None:
                        annual_open[int(q[:4])] = av[1]
                    if av.get(6) is not None:
                        annual_close[int(q[:4])] = av[6]
        # Pass 2 — emit. Q4 stays no-anchor; Q1/Q2/Q3 anchor on the SAME-year Q4 기초 (=YTD
        # opening, the reliable 별도 year-start); fall back to prior-year FY-end (2026.1Q etc).
        for rd in dirs:
            q = quarter_from(rd)
            if not q:
                continue
            y = int(q[:4])
            anchor = None if q.endswith("4Q") else (annual_open.get(y) or annual_close.get(y - 1))
            vals, src = waterfall_for_dir(rd, name, anchor)
            cov[(kr, q)] = src or "none"
            if not vals:
                continue
            for no in range(1, 7):
                rows_out.append({"원보험사코드": kr, "원수사명": name, "티커": ticker,
                                 "생손보여부": sb, "항목번호": no, "항목명": labels[no],
                                 "공시분기": q, "값": vals[no]})
    for f in _fix_annual_newbiz(rows_out):
        print("  newbiz-fix:", f)
    # NOTE: DIAGNOSTIC file, NOT the canonical CSM_waterfall.json.
    (ROOT / "data" / "dart" / "viz" / "csm_waterfall_master_diag.json").write_text(
        json.dumps(rows_out, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for r in rows_out if r["값"] is not None)
    print(f"wrote csm_waterfall_master_diag.json: {len(rows_out)} rows, {filled} filled")
    qs = sorted({q for _k, q in cov})
    print("coverage (src by company×quarter):")
    for kr in SONBO:
        line = " ".join(f"{q[2:]}:{cov.get((kr,q),'-')[:4]}" for q in qs if (kr, q) in cov)
        print(f"  {kr}: {line}")
    (ROOT / "data" / "dart" / "viz" / "csm_waterfall_master_cov.json").write_text(
        json.dumps({f"{kr}|{q}": src for (kr, q), src in cov.items()},
                   ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
