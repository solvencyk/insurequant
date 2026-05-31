#!/usr/bin/env python3
"""F17 — Net-income decomposition for 손보 (non-life) from DART IFRS17 filings.

Tier 1 (universal, works on every annual filing incl. FY2024):
    포괄손익계산서 -> 보험손익 / 투자손익(+보험금융수익·비용) / 영업이익 / 영업외 / 당기순이익.
Tier 2 (손보 LOB, FY2025+ only — the '발행보험의 보험수익/보험서비스비용 분석 by 계약유형' note):
    장기/자동차/일반 보험수익 (장기=일반모형 분해 incl. CSM상각; 자동차·일반=PAA) and 보험서비스비용
    -> 보험손익 by LOB.

Reads DART raw XML under data/dart/raw/<canonical>_<rcept>/.  Output:
    data/dart/viz/net_income_breakdown.json
Reuses csm_extractor._iter_tables_with_context for table parsing.
"""
import json
import re
import sys
import glob
import os
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

RAW_GLOBS = ("data/dart/*/raw", "data/dart/raw")  # new layout first, then legacy
OUT = Path("data/dart/viz/net_income_breakdown.json")

# 손보 canonical name -> KR code (from universe / registry)
SONBO = {
    "삼성화재해상보험": "KR0008", "현대해상": "KR0009", "DB손해보험": "KR0011",
    "KB손해보험": "KR0010", "메리츠화재해상보험": "KR0001", "한화손해보험": "KR0002",
    "롯데손해보험": "KR0003", "흥국화재": "KR0005", "NH농협손해보험": "KR0032",
    "하나손해보험": "KR0050", "코리안리": "KR1000",
}
EOK = 1e8  # 억원


def to_num(s):
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "–", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    # concatenation guard: DART tables occasionally merge several year-columns into
    # one cell with no separator -> a 30+ digit blob. Max plausible 원 value ~ tens of
    # 조 = 10^13-10^14 (≤15 digits). Reject anything longer as a parse artifact.
    digits = s.lstrip("-").split(".")[0]
    if len(digits) > 16:
        return None
    v = float(s)
    return -v if neg else v


def unit_factor(caption, footnotes):
    blob = (caption or "") + " " + " ".join(footnotes or [])
    if "백만" in blob:
        return 1e6
    if "천원" in blob:
        return 1e3
    return 1.0  # 원


def first_val(row):
    """First numeric cell after the label column."""
    for c in row[1:]:
        v = to_num(c)
        if v is not None:
            return v
    return None


def extract_tier1(tables):
    """Find the 포괄손익계산서 and pull key lines (current period), in 억원.
    Prefers the 연결 statement (largest 당기순이익 magnitude)."""
    def labels(t):
        return [(r[0] if r else "") for r in t.rows]

    cands = []
    for t in tables:
        labs = " ".join(labels(t))
        if "보험손익" in labs and "투자손익" in labs and ("당기순이익" in labs or "순이익" in labs):
            cands.append(t)
    if not cands:
        return None

    def pick_line(t, *needles, exclude=()):
        for r in t.rows:
            lab = (r[0] or "").strip()
            if any(n in lab for n in needles) and not any(x in lab for x in exclude):
                v = first_val(r)
                if v is not None:
                    return v, lab
        return None, None

    MAX_EOK = 150000  # 15조 — above any single 손보 line; reject parse artifacts

    def infer_factor(ni_raw, caption_f):
        """Pick unit factor so 당기순이익 lands in a plausible 손보 range (5~120,000억).
        Caption hint tried first, then 백만/천/원."""
        for f in [caption_f, 1e6, 1e3, 1.0]:
            if f and 5 <= abs(ni_raw * f / EOK) <= 120000:
                return f
        return caption_f or 1.0

    def line_eok(t, f, *needles, **kw):
        v, lab = pick_line(t, *needles, **kw)
        if v is None:
            return None, lab
        e = v * f / EOK
        return (e, lab) if abs(e) <= MAX_EOK else (None, lab)

    scored = []
    for t in cands:
        ni_raw, ni_lab = pick_line(t, "연결당기순이익", "계속영업당기순이익", "당기순이익")
        if ni_raw is None or ni_raw == 0:  # blank/template table -> skip
            continue
        f = infer_factor(ni_raw, unit_factor(t.caption, t.footnotes))
        ni = ni_raw * f / EOK
        if abs(ni) > MAX_EOK:
            continue
        ins, _ = line_eok(t, f, "보험손익")
        inv, _ = line_eok(t, f, "투자손익")
        fin_inc, _ = line_eok(t, f, "보험금융수익", exclude=("재보험",))
        fin_exp, _ = line_eok(t, f, "보험금융비용", exclude=("재보험",))
        op, _ = line_eok(t, f, "영업이익", exclude=("영업외",))
        oi, _ = line_eok(t, f, "영업외수익")
        oe, _ = line_eok(t, f, "영업외비용")
        rec = {
            "보험손익": ins, "투자손익": inv,
            "보험금융수익": fin_inc, "보험금융비용": fin_exp,
            "영업이익": op, "영업외": (((oi or 0) - (oe or 0)) if (oi is not None or oe is not None) else None),
            "당기순이익": ni, "_ni_label": ni_lab, "_unit": f, "_caption": t.caption[:40],
        }
        # primary: internal consistency (보험손익+투자손익 ≈ 영업이익). Then the LARGEST
        # 당기순이익 — consolidated (연결) >= separate (별도) — so Tier1 matches the LOB note
        # (보험서비스결과 is disclosed 연결).
        consistent = (op is not None and ins is not None and inv is not None
                      and abs((ins + inv) - op) <= 0.15 * abs(op) + 1)
        scored.append((1 if consistent else 0, abs(ni), rec))
    if not scored:
        return None
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return scored[0][2]


# ---- Tier 2: LOB (장기/자동차/일반) 보험손익 from 보험서비스결과 note (FY2025+) ----
LOB_ORDER = ["장기보험", "자동차보험", "일반보험"]


def _lob_col_index(header):
    """Map LOB name -> column index using the header rows."""
    idx = {}
    for hr in header:
        for ci, cell in enumerate(hr):
            for lob in LOB_ORDER:
                if cell.strip() == lob and lob not in idx:
                    idx[lob] = ci
    return idx


def _lob_header(t):
    hb = " ".join(" ".join(r) for r in t.header)
    return all(k in hb for k in LOB_ORDER)


def _is_rollforward(t):
    """Balance-sheet rollforward tables (보험계약부채 변동) also carry 보험수익/보험서비스비용
    rows but at BS magnitudes — exclude them so we keep the clean flow-analysis table."""
    labs = " ".join((r[0] or "") for r in t.rows)
    return any(k in labs for k in ("기초 보험계약", "기말 보험계약", "보험계약부채(자산)",
                                   "기초보험계약", "기말보험계약"))


def _row_nums(r):
    """Numeric cells of a row, in order. The LOB analysis tables put values as
    [장기, 자동차, 일반, (합계)] regardless of how many leading label/merged cells the
    header has — so position 0/1/2 = 장기/자동차/일반 (header-index mapping breaks on
    merged '계약의 유형' super-headers)."""
    return [to_num(c) for c in r if to_num(c) is not None]


def _label_is(r, label):
    """A 'total' row: first column == label and the next cell is numeric (not a sub-label)."""
    return (r[0] or "").strip() == label and len(r) > 1 and to_num(r[1]) is not None


def _starts(r, prefix):
    """Component row: label (col0 or col1) starts with '<prefix>,' (e.g. '보험수익, 보고기간에…')."""
    for c in r[:2]:
        if (c or "").strip().startswith(prefix + ","):
            return True
    return False


def _contains(r, needle):
    for c in r[:2]:
        if needle in (c or ""):
            return True
    return False


def _exact_total(t, p, label):
    for r in t.rows:
        if _label_is(r, label):
            nums = _row_nums(r)
            return nums[p] if len(nums) > p else None
    return None


def _row_with(t, p, needle):
    for r in t.rows:
        if _contains(r, needle):
            nums = _row_nums(r)
            if len(nums) > p:
                return nums[p]
    return None


def _comp_sum(t, p, prefix):
    tot, found = 0.0, False
    for r in t.rows:
        if _starts(r, prefix):
            nums = _row_nums(r)
            if len(nums) > p:
                tot += nums[p]
                found = True
    return tot if found else None


def _lob_rev_raw(t, p):
    """장기: GMM components summed; PAA/total LOB: exact '보험수익' total row. Use the larger."""
    ex = _exact_total(t, p, "보험수익")
    cs = _comp_sum(t, p, "보험수익")
    if ex is None and cs is None:
        return None
    if ex is not None and (cs is None or abs(ex) >= abs(cs)):
        return ex
    return cs


def _lob_cost_raw(t, p):
    c = _row_with(t, p, "발행한 보험계약에서 생기는 보험서비스비용")
    if c is None:
        c = _exact_total(t, p, "보험서비스비용")
    if c is None:
        c = _comp_sum(t, p, "보험서비스비용")
    return c


LOB_POS = {"장기보험": 0, "자동차보험": 1, "일반보험": 2}


def extract_tier2_lob(tables, t1_ins=None):
    """Return {'장기':{보험수익,보험서비스비용,보험손익,csm_상각}, ...} in 억원, or None.
    Uses the clean '발행보험의 보험수익/비용 분석' tables (계약유형별), excluding BS rollforwards.
    Unit factor anchored on Tier1 보험손익 (notes are 원/백만/천원 by company)."""
    cands = [t for t in tables if _lob_header(t) and not _is_rollforward(t)]
    if not cands:
        return None

    def lob3(t, fn):
        return sum(abs(fn(t, p)) for p in (0, 1, 2) if fn(t, p))

    rev_cands = [t for t in cands if any("보험수익" in (r[0] or "") or "보험수익" in ((r[1] if len(r) > 1 else "") or "") for r in t.rows)]
    cost_cands = [t for t in cands if any("보험서비스비용" in (r[0] or "") or "보험서비스비용" in ((r[1] if len(r) > 1 else "") or "") for r in t.rows)]
    rev_t = max(rev_cands, key=lambda t: lob3(t, _lob_rev_raw)) if rev_cands else None
    cost_t = max(cost_cands, key=lambda t: lob3(t, _lob_cost_raw)) if cost_cands else None
    if not rev_t and not cost_t:
        return None

    # raw per-LOB rev/cost (note's own unit), then choose factor so Σ(rev-cost) ≈ Tier1 보험손익
    raw = {}
    for lob, p in LOB_POS.items():
        rv = _lob_rev_raw(rev_t, p) if rev_t else None
        cv = _lob_cost_raw(cost_t, p) if cost_t else None
        raw[lob] = (rv, cv)
    raw_pl = sum((rv - cv) for rv, cv in raw.values() if rv is not None and cv is not None)

    def pick_factor():
        cap_f = unit_factor(rev_t.caption, rev_t.footnotes) if rev_t else 1.0
        cands_f = [1.0, 1e6, 1e3, 1e2, 1e4]
        if cap_f and cap_f not in cands_f:
            cands_f.insert(0, cap_f)
        if t1_ins and abs(t1_ins) > 1 and raw_pl:
            best = None
            for f in cands_f:
                e = raw_pl * f / EOK
                err = abs(abs(e) - abs(t1_ins)) / (abs(t1_ins) + 1)
                if best is None or err < best[0]:
                    best = (err, f)
            return best[1]
        # no anchor: put the largest revenue in a plausible band
        mx = max((abs(rv) for rv, _ in raw.values() if rv is not None), default=0)
        for f in cands_f:
            if mx and 50 <= mx * f / EOK <= 600000:
                return f
        return cap_f or 1.0

    f = pick_factor()
    out = {}
    for disp, lob in (("장기", "장기보험"), ("자동차", "자동차보험"), ("일반", "일반보험")):
        p = LOB_POS[lob]
        rv, cv = raw[lob]
        csm = _row_with(rev_t, p, "서비스의 이전으로") if rev_t else None
        rev = rv * f / EOK if rv is not None else None
        cost = cv * f / EOK if cv is not None else None
        if rev is None and cost is None:
            continue
        out[disp] = {
            "보험수익": round(rev, 1) if rev is not None else None,
            "보험서비스비용": round(cost, 1) if cost is not None else None,
            "보험손익": round(rev - cost, 1) if (rev is not None and cost is not None) else None,
            "csm_상각": round(csm * f / EOK, 1) if csm is not None else None,
        }
    return out or None


# ---- Tier 2 (per-company) — extract LOB 보험손익 from regulatory disclosure tables.
# Used for filings that don't carry the clean '발행보험 by 계약유형' note (KB/Hana via
# Note 보험손익 directly) or where that note is omitted/aggregated (Meritz/NH/Korean Re,
# whose '보종별 보험 실적' table is the only LOB split available).
# ----------------------------------------------------------------------------

def _row_label(r):
    return (r[0] or "").strip()


def _row_label2(r):
    return (r[1] or "").strip() if len(r) > 1 else ""


def _all_nums(r):
    """All numeric cells of a row, in order."""
    return [to_num(c) for c in r if to_num(c) is not None]


def _all_cells_numeric(r):
    """Numeric or '-' placeholders in order; '-' → 0.0 (table convention)."""
    out = []
    for c in r:
        s = (c or "").strip()
        if s in ("", "-", "–", "—"):
            out.append(0.0)
            continue
        v = to_num(c)
        if v is not None:
            out.append(v)
    return out


def _table_has_caption(t, *needles):
    cap = (t.caption or "")
    return all(n in cap for n in needles)


def _kb_lob(tables, t1_ins):
    """KB: Note '(6) 당기와 전기 중 보험손익의 상세내역', header cols 장기/일반/자동차/해외지점/합계.
    Row '총 보험서비스결과' carries IFRS17 보험손익 directly. Unit: 백만원."""
    for t in tables:
        if "보험손익의 상세내역" not in (t.caption or ""):
            continue
        for r in t.rows:
            if _row_label(r) == "총 보험서비스결과":
                nums = _all_nums(r)
                if len(nums) < 4:
                    continue
                # nums = [장기, 일반, 자동차, 해외지점, 합계]
                f = 1e6  # 백만원 → 원
                jang = nums[0] * f / EOK
                ilban = nums[1] * f / EOK
                auto = nums[2] * f / EOK
                overseas = nums[3] * f / EOK if len(nums) >= 5 else 0.0
                return {
                    "장기": {"보험손익": round(jang, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None},
                    "자동차": {"보험손익": round(auto, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None},
                    "일반": {"보험손익": round(ilban + overseas, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None,
                            "_includes_overseas": round(overseas, 1)},
                    "_basis": "DART_note_total_service_result",
                }
    return None


def _hana_lob(tables, t1_ins):
    """Hana: Note 29 '보험손익 및 재보험손익', header cols 장기/일반/자동차/합계,
    row '순보험손익 합계'. Caption falls under the nearest '<당기>' subcaption so we
    locate the table by row signature: header has 장기/일반/자동차/합계 AND a
    '순보험손익 합계' row. Unit: 천원."""
    for t in tables:
        hb = " ".join(" ".join(r) for r in t.header)
        if not ("장기" in hb and "일반" in hb and "자동차" in hb and "합 계" in hb):
            continue
        for r in t.rows:
            lab = _row_label(r) or _row_label2(r)
            if lab.replace(" ", "") in ("순보험손익합계",):
                nums = _all_nums(r)
                if len(nums) < 3:
                    continue
                # nums = [장기, 일반, 자동차, 합계]
                f = 1e3  # 천원 → 원
                return {
                    "장기": {"보험손익": round(nums[0] * f / EOK, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None},
                    "일반": {"보험손익": round(nums[1] * f / EOK, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None},
                    "자동차": {"보험손익": round(nums[2] * f / EOK, 1), "보험수익": None,
                            "보험서비스비용": None, "csm_상각": None},
                    "_basis": "DART_note_net_insurance_income",
                }
    return None


def _meritz_lob(tables, t1_ins):
    """Meritz: '(1) 보험 종목별 보험 실적 현황' — row per product (화재/해상/자동차/보증/특종/
    해외/장기/개인연금/계), 4 cols per fiscal year [보험수익, 보험서비스비용, 재보험수익, 재보험서비스비용].
    보험손익 per product = 수익 - 비용 + 재수익 - 재비용 (current year only). Unit: 백만원.
    NOTE: this is the regulatory disclosure (별도, 사업실적표 기준) — 사업비용 / 기타사업비용 not
    deducted here, so LOB sum ≠ IFRS17 보험손익 exactly (~10% gap = 기타사업비용)."""
    for t in tables:
        if "보험 종목별 보험 실적 현황" not in (t.caption or ""):
            continue
        groups = {"일반": ["화재", "해상", "보증", "특종", "해외"],
                  "자동차": ["자동차"],
                  "장기": ["장기", "개인연금"]}
        product_pl = {}
        for r in t.rows:
            lab = _row_label(r)
            if lab in ("계",):
                continue
            nums = _all_nums(r)
            if len(nums) < 4:
                continue
            # current FY is the leftmost 4-column block
            pl = nums[0] - nums[1] + nums[2] - nums[3]
            product_pl[lab] = pl
        if not product_pl:
            continue
        f = 1e6
        out = {}
        for lob, members in groups.items():
            tot = sum(product_pl.get(m, 0.0) for m in members if m in product_pl)
            if any(m in product_pl for m in members):
                out[lob] = {"보험손익": round(tot * f / EOK, 1),
                            "보험수익": None, "보험서비스비용": None,
                            "csm_상각": None}
        out["_basis"] = "DART_regulatory_lob_disclosure"
        return out if out else None
    return None


def _nh_lob(tables, t1_ins):
    """NH 농협: 보종별 disclosure with header 화재/해상/자동차/보증/특종/외국수재/장기/합계 and
    row '보험영업실적' = (경과보험료 - 발생손해액 - 순사업비) — regulatory metric, NOT IFRS17 보험손익.
    Caption varies, so match by header signature. Unit: 백만원."""
    for t in tables:
        hb = " ".join(" ".join(r) for r in t.header).replace(" ", "")
        if not ("외국수재" in hb and "장기" in hb and "자동차" in hb and "특종" in hb):
            continue
        for r in t.rows:
            if _row_label(r) == "보험영업실적":
                nums = _all_nums(r)  # to_num handles "(16,971)" → -16971
                if len(nums) < 8:
                    continue
                # 화재/해상/자동차/보증/특종/외국수재/장기/합계
                f = 1e6
                fire, marine, auto, bond, spec, foreign, jang = nums[:7]
                ilban = fire + marine + bond + spec + foreign
                return {
                    "장기": {"보험손익": round(jang * f / EOK, 1),
                            "보험수익": None, "보험서비스비용": None, "csm_상각": None},
                    "자동차": {"보험손익": round(auto * f / EOK, 1),
                            "보험수익": None, "보험서비스비용": None, "csm_상각": None},
                    "일반": {"보험손익": round(ilban * f / EOK, 1),
                            "보험수익": None, "보험서비스비용": None, "csm_상각": None},
                    "_basis": "DART_regulatory_business_result (not IFRS17 보험손익)",
                }
    return None


def _koreanre_lob(tables, t1_ins):
    """Korean Re: '보험종목별 영업규모 및 영업실적'. Row groupings:
    일반손해보험 → 화재/종합, 해상, 근재, 책임, 상해, 기술, 보증, 자동차, 해외, 기타, 소계;
    장기손해보험 (single row); 생명보험 (single row); 총계.
    Cols: 보험수익, 보험비용, 재보험수익, 재보험비용. Reinsurance taxonomy: 자동차 lives INSIDE
    일반손해보험. Map 자동차 → 자동차, rest of 일반 → 일반, 장기손해+생명 → 장기. Unit: 백만원."""

    def _norm(s):
        return (s or "").replace(" ", "").strip()

    for t in tables:
        if "보험종목별 영업규모" not in (t.caption or ""):
            continue
        # walk rows, identify 자동차 / 소계 / 장기손해보험 / 생명보험
        auto_pl = jang_life_pl = jang_health_pl = ilban_subtotal_pl = None
        for r in t.rows:
            lab = _norm(_row_label(r)) or _norm(_row_label2(r))
            nums = _all_nums(r)
            if len(nums) < 4:
                continue
            pl = nums[0] - nums[1] + nums[2] - nums[3]
            if lab == "자동차":
                auto_pl = pl
            elif lab == "소계":
                if ilban_subtotal_pl is None:  # first 소계 = 일반손해보험
                    ilban_subtotal_pl = pl
            elif lab == "장기손해보험":
                jang_health_pl = pl
            elif lab == "생명보험":
                jang_life_pl = pl
        if ilban_subtotal_pl is None or auto_pl is None:
            continue
        f = 1e6
        ilban_only = ilban_subtotal_pl - auto_pl
        jang_total = (jang_health_pl or 0.0) + (jang_life_pl or 0.0)
        return {
            "장기": {"보험손익": round(jang_total * f / EOK, 1),
                    "보험수익": None, "보험서비스비용": None, "csm_상각": None,
                    "_includes_life_reins": round((jang_life_pl or 0.0) * f / EOK, 1)},
            "자동차": {"보험손익": round(auto_pl * f / EOK, 1),
                    "보험수익": None, "보험서비스비용": None, "csm_상각": None},
            "일반": {"보험손익": round(ilban_only * f / EOK, 1),
                    "보험수익": None, "보험서비스비용": None, "csm_상각": None},
            "_basis": "DART_regulatory_lob_disclosure_reinsurance",
        }
    return None


PERCO_LOB = {
    "KR0010": _kb_lob,
    "KR0050": _hana_lob,
    "KR0001": _meritz_lob,
    "KR0032": _nh_lob,
    "KR1000": _koreanre_lob,
}


def _resolve_raw_dirs(name):
    """Return all DART raw dirs for a 손보 company across legacy + per-FY layouts."""
    out = []
    for base in RAW_GLOBS:
        # legacy: data/dart/raw/<name>_<rcept>/   ;  new: data/dart/<fy>/raw/KR*_<name>_<rcept>/
        out.extend(glob.glob(f"{base}/{name}*"))
        out.extend(glob.glob(f"{base}/KR*_{name}*"))
    # dedupe (a path may match both patterns)
    return sorted(set(out))


def main():
    results = []
    for name, kr in SONBO.items():
        dirs = _resolve_raw_dirs(name)
        if not dirs:
            results.append({"company": name, "kr": kr, "status": "no_raw_dir"})
            continue
        # consider all rcept dirs newest-first: Tier1 from the newest filing that yields a
        # valid income statement (FY2025 preferred, FY2024 fallback for thin 사업보고서);
        # Tier2 LOB only from FY2025 filings.
        per_dir = {os.path.basename(d).split("_")[-1]: d for d in dirs}
        t1 = t2 = None
        t1_fy = t1_rcept = t2_fy = t2_rcept = None
        for rcept in sorted(per_dir, reverse=True):
            fy = "FY2025" if rcept >= "20260000000000" else "FY2024"
            xmls = sorted(glob.glob(per_dir[rcept] + "/*.xml")
                          + glob.glob(per_dir[rcept] + "/extracted/*.xml"),
                          key=os.path.getsize, reverse=True)
            if not xmls:
                continue
            need_t1 = t1 is None
            need_t2 = t2 is None and fy == "FY2025"
            if not (need_t1 or need_t2):
                continue
            tables = []
            for x in xmls:
                tables.extend(_iter_tables_with_context(Path(x)))
            c1 = extract_tier1(tables)  # also used as the Tier2 unit anchor for this filing
            if need_t1 and c1:
                t1, t1_fy, t1_rcept = c1, fy, rcept
            if need_t2:
                # per-company override: regulatory disclosure tables (KB direct IFRS17 note,
                # Hana Note 29, Meritz/NH/Korean Re 보종별 표). Falls back to the generic
                # '발행보험 by 계약유형' note extractor when no override is registered.
                override = PERCO_LOB.get(kr)
                c2 = override(tables, (c1 or {}).get("보험손익")) if override else None
                if c2 is None:
                    c2 = extract_tier2_lob(tables, (c1 or {}).get("보험손익"))
                if c2:
                    t2, t2_fy, t2_rcept = c2, fy, rcept
            if t1 and t2:
                break
        # reconciliation gate: only keep LOB if sum(available LOB 보험손익) is within a
        # sane band of Tier1 보험손익 — otherwise the generic parser picked the wrong
        # LOB table / taxonomy / unit (per-company variance) and the numbers are bogus.
        # Basis-aware: regulatory-disclosure extractions (Meritz/NH/Korean Re) have a
        # structural gap vs IFRS17 보험손익 (사업비/기타사업비용 not deducted in 보종별 표),
        # so use a wider band there and never throw the result away.
        lob_status = "none"
        if t2:
            basis = (t2.get("_basis") or "").lower()
            is_regulatory = "regulatory" in basis or "business_result" in basis
            avail = [v["보험손익"] for k, v in t2.items()
                     if isinstance(v, dict) and v.get("보험손익") is not None]
            t1_ins = (t1 or {}).get("보험손익")
            if avail and t1_ins:
                ratio = abs(sum(avail)) / (abs(t1_ins) + 1e-9)
                lo, hi = (0.3, 3.0) if is_regulatory else (0.5, 2.0)
                if lo <= ratio <= hi:
                    lob_status = f"ok (LOB합 {sum(avail):.0f} vs Tier1 보험손익 {t1_ins:.0f})"
                else:
                    lob_status = f"unreliable_parse (LOB합 {sum(avail):.0f} vs 보험손익 {t1_ins:.0f})"
                    if not is_regulatory:
                        t2 = None
            elif avail and not t1_ins:
                # Tier1 missing (e.g. Hana — atypical 손익 statement format), but LOB
                # came from a per-company override → keep with no_t1 flag.
                lob_status = f"ok_no_tier1_anchor (LOB합 {sum(avail):.0f})"
            else:
                lob_status = "unreliable_parse (incomplete)"
                t2 = None
        results.append({
            "company": name, "kr": kr,
            "tier1": t1, "tier1_fy": t1_fy, "tier1_rcept": t1_rcept,
            "tier2_lob": t2, "tier2_fy": t2_fy, "tier2_rcept": t2_rcept,
            "lob_status": lob_status,
            "fy": t1_fy or t2_fy,
            "status": "ok" if t1 else ("lob_only" if t2 else "no_income_statement"),
        })
    payload = {"_meta": {"purpose": "F17 net-income decomposition (손보)", "unit": "억원"},
               "companies": results}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for r in results:
        if r.get("tier1"):
            t = r["tier1"]
            lob = "+LOB" if r.get("tier2_lob") else ""
            print(f"  {r['kr']} {r['company'][:12]:12} [{r['fy']}] 보험손익={t['보험손익']:.0f} 투자손익={t['투자손익']:.0f} "
                  f"당기순이익={t['당기순이익']:.0f}억 {lob}")
        else:
            print(f"  {r['kr']} {r['company'][:12]:12} {r['status']}")


if __name__ == "__main__":
    main()
