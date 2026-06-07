# -*- coding: utf-8 -*-
"""Broadened diagnostic for 생보 Tier-2 PL-analysis notes (발행/출재 계약유형별 분석).

Unlike _diag_pl_notes.py (which surfaces rollforwards and requires >=2 analysis-row
hits), this dumps ANY table whose rows mention the CSM-amortization phrase
("서비스의 이전으로 당기손익에 인식한 보험계약마진" and variants) OR
("발행한 보험계약" + "보험수익"), so we can find P&L-analysis notes that the
original diagnostic misses.  Read-only.

Usage:
  python scripts/_plprobe_life2.py KR0094 2025.4Q
  python scripts/_plprobe_life2.py KR0094 2025.4Q --csm     # only CSM-phrase tables
  python scripts/_plprobe_life2.py KR0094 2025.4Q --rows 40 # more rows per table
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


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


# CSM amortization phrase variants (the signature row of the analysis note).
CSM_PHRASES = (
    "서비스의 이전으로 당기손익에 인식한 보험계약마진",
    "제공된 서비스의 보험계약마진",
    "제공한 서비스의 보험계약마진",
    "보험계약마진 상각",
    "보험계약마진의 상각",
    "당기손익으로 인식한 보험계약마진",
    "당기손익에 인식한 보험계약마진",
    "이전한 서비스에 대한 보험계약마진",
)
ROLLFWD = ("기초 순장부금액", "기말 순장부금액", "기초 보험계약", "기말 보험계약",
           "기초보험계약", "기말보험계약", "수취한 보험료", "순장부금액",
           "보험계약부채(자산)", "기초 장부금액", "기말 장부금액")


def rowblob(t):
    return " ".join(_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)


def has_csm_phrase(t):
    b = rowblob(t).replace(" ", "")
    return any(p.replace(" ", "") in b for p in CSM_PHRASES)


def has_issued_rev(t):
    b = rowblob(t).replace(" ", "")
    cap = (t.caption or "").replace(" ", "")
    blob = b + cap
    return "발행한보험계약" in blob and "보험수익" in blob


def is_rollfwd(t):
    b = rowblob(t)
    return any(k in b for k in ROLLFWD)


def fmt_row(r):
    lab = _norm(r[0])
    lab1 = _norm(r[1]) if len(r) > 1 else ""
    nums = [to_num(c) for c in r]
    nums = [round(n, 1) for n in nums if n is not None]
    label = lab if not lab1 else f"{lab} | {lab1}"
    return f"    {label[:70]:<70}  nums={nums}"


def main():
    code, q = sys.argv[1], sys.argv[2]
    csm_only = "--csm" in sys.argv
    maxrows = 40
    if "--rows" in sys.argv:
        maxrows = int(sys.argv[sys.argv.index("--rows") + 1])
    y, qq = re.match(r"(\d{4})\.(\d)Q", q).groups()
    base_glob = f"data/dart/FY{y}_Q{qq}/raw/{code}_*"
    dirs = glob.glob(base_glob)
    if not dirs:
        print("no raw dir for", code, q, "glob=", base_glob)
        return
    tables = []
    for d in dirs:
        xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
        for x in sorted(set(xs), key=os.path.getsize, reverse=True):
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception as e:
                print("  parse error", x, e)
    print(f"=== {code} {q} : {len(tables)} tables ===")
    n = 0
    for ti, t in enumerate(tables):
        csm = has_csm_phrase(t)
        issued = has_issued_rev(t)
        if csm_only and not csm:
            continue
        if not (csm or issued):
            continue
        rf = is_rollfwd(t)
        n += 1
        tag = ("CSM " if csm else "") + ("ISSUED " if issued else "") + ("[ROLLFWD]" if rf else "")
        print(f"\n[table {n} idx={ti}] {tag} caption={t.caption!r}")
        for h in t.header:
            print("   H:", [_norm(c) for c in h])
        for r in t.rows[:maxrows]:
            print(fmt_row(r))
    print(f"\n-> {n} candidate tables shown (csm_only={csm_only})")


# =========================================================================== #
# Candidate Tier-2 extractor for the "single comprehensive 보험손익 내역" note
# family (당기/전기 columns, positional 보험수익/보험서비스비용/재보험수익/재보험비용
# sections, value = FIRST numeric = 당기) plus the 미래에셋 product-split family.
# This is a PROTOTYPE to validate the additions; the real fix goes into
# build_pl_breakdown.py (see deliverable).
# =========================================================================== #
from scripts.build_pl_breakdown import to_num as _to_num  # noqa: E402

# Section header detection (a row whose col0 is exactly a section name, no numbers).
SECT = {
    "보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost",
    "재보험수익": "re_rev", "재보험비용": "re_cost", "재보험서비스비용": "re_cost",
    "출재보험수익": "re_rev", "출재보험비용": "re_cost",
}
# numbered prefixes ("1. 보험수익", "2.재보험수익")
import re as _re  # noqa: E402

# Row-label variants (union of all 생보 forms seen).
V_CSM = ("서비스의 이전으로 당기손익에 인식한 보험계약마진", "제공된 서비스의 보험계약마진",
         "제공받은 서비스의 보험계약마진", "보험계약마진 상각", "제공받은 서비스의 재보험계약마진",
         "당기손익에 인식한 보험계약마진")
V_RA = ("비금융위험에 대한 위험조정의 변동분", "위험해제로 인한 비금융위험에 대한 위험조정의 변동",
        "위험해제로 인한 위험조정의 변동", "위험조정 변동", "위험조정의 변동")
V_REV_EXP = ("예상 보험금 및 기타보험 서비스비용", "예상보험금 및 기타보험 서비스비용",
             "예상 발생보험금 및 비용", "예상 발생보험금 및 보험서비스비용",
             "예상 보험금 및 보험서비스비용", "예상발생보험금",
             "예상 보험금 및 기타보험서비스 수익")  # 신한 (수익 side)
V_COST_ACT = ("발생 보험금 및 기타보험서비스 비용", "발생보험금 및 기타보험 서비스비용",
              "실제 발생보험금 및 비용", "실제 발생보험금 및 보험서비스비용",
              "보험금 및 보험서비스비용", "실제발생보험금",
              "발생 보험금 및 기타보험서비스 비용")  # 신한
# reinsurance side
V_RE_REV_ACT = ("당기 발생재보험금", "발생재보험금", "회수가능 보험금 및 보험서비스비용",
                "실제 출재보험금 및 비용", "실제발생재보험금")
V_RE_COST_EXP = ("예상 재보험금 및 기타보험서비스비용", "회수예상보험금", "회수예상 보험금 및 보험서비스비용",
                 "예상 출재보험금 및 비용", "예상발생재보험금")


def _match(lbl, variants):
    s = lbl.replace(" ", "")
    return any(v.replace(" ", "") in s for v in variants)


def _first_num(r):
    """당기 (first numeric) of a 당기/전기 row."""
    for c in r:
        v = _to_num(c)
        if v is not None:
            return v
    return None


def _sect_of(lbl):
    s = lbl.replace(" ", "")
    s = _re.sub(r"^[0-9]+\.", "", s)  # drop "1." / "2." numbering
    s = s.lstrip("(0-9). ")
    for k, v in SECT.items():
        if s == k.replace(" ", "") or s.startswith(k.replace(" ", "")):
            # only treat as a header when the row carries no numbers
            return v
    return None


def extract_comprehensive(tables):
    """Family A: single/dual comprehensive note with positional sections and 당기/전기
    columns (신한라이프, 농협생명, 흥국생명, 케이디비, 푸본현대).  Walk every candidate
    note table; track the current section by header rows; sum the per-section component
    rows.  '발행 예상발생' may be split into multiple sub-rows (푸본) -> we sum *all* rows
    whose label matches V_REV_EXP within the rev section (and similarly for actual)."""
    secvals = {}  # section -> {kind: value or summed value}
    totals = {}   # section -> 소계/합계/총 value (당기)

    def add(sec, kind, val, accumulate=False):
        d = secvals.setdefault(sec, {})
        if accumulate:
            d[kind] = (d.get(kind) or 0) + val
        elif kind not in d:
            d[kind] = val

    seen_caps = set()  # dedupe: the same note appears in 별도+연결 filings & 당기/전기 copies
    for t in tables:
        if is_rollfwd(t):
            continue
        b = rowblob(t)
        if "보험계약마진" not in b:
            continue
        # must look like a P&L analysis note (has section header + CSM/RA rows)
        if not any(s in b for s in ("보험수익", "보험서비스비용", "보험비용",
                                    "재보험수익", "재보험비용", "재보험서비스비용")):
            continue
        cap = (t.caption or "")
        capn = cap.replace(" ", "")
        # exclude non-P&L tables that also carry 보험계약마진/재보험서비스비용 rows:
        # 신계약/재보험 최초인식 (BS effect), 전환방법별 (transition-method) tables.
        if any(k in capn for k in ("최초인식", "최초 인식", "전환방법별", "전환 방법별",
                                   "신규로체결", "신규로 체결", "신용건전성", "신용위험",
                                   "지분의장부금액", "위험노출")):
            continue
        # require a P&L-note caption signature OR an implicit 총-boundary structure
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
        # Detect the 신한 "총-boundary, transition-method columns + 합계" form: no header
        # rows, value = 합계 (max-abs of row), sections flip after a 총 row.
        has_header_rows = any(_sect_of(_norm(r[0])) for r in t.rows)
        shinhan_form = has_tot_boundary and not has_header_rows
        is_re_table = ("재보험영업손익" in capn) or ("출재보험관련손익" in capn) or ("재보험서비스비용" in capn)
        if shinhan_form:
            section = "re_rev" if is_re_table else "rev"

        def value_of(r):
            return (max((v for v in (_to_num(c) for c in r) if v is not None),
                        key=abs, default=None) if shinhan_form else _first_num(r))

        for r in t.rows:
            lab0 = _norm(r[0]) if r else ""
            lab1 = _norm(r[1]) if len(r) > 1 else ""
            lbl = (lab0 + lab1)
            nums = [v for v in (_to_num(c) for c in r) if v is not None]
            # section header: col0 is a section name.  Two forms:
            #   (a) standalone header row, no numbers (푸본/흥국/케이디비)
            #   (b) col0=section, col1=first sub-row label, with numbers (농협)
            sec_hdr = _sect_of(lab0)
            if sec_hdr and (not nums or lab1):
                section = sec_hdr
                if not nums:
                    continue
                # form (b): col0 carries section, col1 the sub-row label -> fall through
                lbl = lab1
            if section is None:
                continue
            cur = value_of(r)
            if cur is None:
                continue
            # 소계/합계/총 row -> section total, and (신한 form) advance the section.
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
            if section in ("rev",):
                if _match(lbl, V_CSM):
                    add("rev", "csm", cur)
                elif _match(lbl, V_RA):
                    add("rev", "ra", cur)
                elif _match(lbl, V_REV_EXP):
                    add("rev", "exp", cur, accumulate=True)
            elif section == "cost":
                if _match(lbl, V_COST_ACT):
                    add("cost", "act", cur, accumulate=True)
            elif section == "re_rev":
                if _match(lbl, V_RE_REV_ACT):
                    add("re_rev", "act", cur, accumulate=True)
            elif section == "re_cost":
                if _match(lbl, V_CSM):
                    add("re_cost", "csm", cur)
                elif _match(lbl, V_RA):
                    add("re_cost", "ra", cur)
                elif _match(lbl, V_RE_COST_EXP):
                    add("re_cost", "exp", cur, accumulate=True)
    return secvals, totals


def extract_product_split(tables):
    """Family B: 미래에셋 — the 발행 보험수익 / 출재 재보험서비스비용 notes are split by
    product (사망/건강/연금/저축/기타 or 사망/사망외), each its own small table with a
    transition-method breakdown + 합계 column.  Each table stacks a 당기 block then a 전기
    block (first cell of the block-leading row == '당기'/'전기').  We sum the 당기-block
    CSM & RA 합계 (last numeric) across all product tables, deduping the note set that
    appears in both 별도 and 연결 filings (identical values -> take first complete set).

    Only items 4,5 (발행 CSM/RA) and 9,10 (출재 CSM/RA) are recoverable; this note family
    is an LRC-release decomposition that does NOT disclose 예상/실제 발생보험금, so item6 is
    unavailable here (left to the item7/12 residual)."""
    def hdr_blob(x):
        return " ".join(" ".join(h) for h in x.header)

    def block_sum(group):
        csm = ra = None
        seen_first_product = set()
        for x in group:
            cur = "dang"
            for r in x.rows:
                lab0 = _norm(r[0])
                if lab0 == "당기":
                    cur = "dang"
                elif lab0 == "전기":
                    cur = "jeon"
                nums = [v for v in (_to_num(c) for c in r) if v is not None]
                if cur != "dang" or not nums:
                    continue
                key = (lab0 + (_norm(r[1]) if len(r) > 1 else "")).replace(" ", "")
                v = nums[-1]  # 합계 column
                if _match(key, V_CSM):
                    csm = (csm or 0) + v
                elif _match(key, V_RA):
                    ra = (ra or 0) + v
        return csm, ra

    def fingerprint(x):
        """Content signature robust to caption typos (별도/연결 filings differ only by a
        '당기와'/'당기과' typo).  Use the rounded numeric content of all rows."""
        return tuple(round(v, 1) for r in x.rows
                     for v in (_to_num(c) for c in r) if v is not None)

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


def build_items(secvals, totals):
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
    for k, sec in (("_jang_rev", "rev"), ("_jang_cost", "cost"),
                   ("_jang_rerev", "re_rev"), ("_jang_recost", "re_cost")):
        if sec in totals:
            out[k] = totals[sec]
    return out


def _pick_is_line(tables, code, *needles, exclude=()):
    """Read a single line (백만원) off the company's canonical income statement.  Reuses
    extract_tier1's statement selection by re-finding the chosen statement: we look for
    the income statement whose 보험손익 == tier1 item1 and unit-scale via 당기순이익."""
    from scripts.build_pl_breakdown import (_is_income_statement, _pick_line,
                                            _income_unit_factor, extract_tier1)
    t1 = extract_tier1(tables, code=code) or {}
    target_ins = t1.get(1)
    best = None
    for t in tables:
        if not _is_income_statement(t):
            continue
        ni = _pick_line(t, "연결당기순이익", "당기순이익(손실)", "당기순이익")
        ins = _pick_line(t, "보험손익", "보험서비스결과")
        if ni is None or ins is None:
            continue
        f = _income_unit_factor(ni)
        if target_ins is not None and abs(ins * f - target_ins) <= max(1.0, 0.001 * abs(target_ins)):
            val = _pick_line(t, *needles, exclude=exclude)
            return None if val is None else round(val * f, 6)
    return None


def selfcheck(quarter="2025.4Q"):
    """Run extract_comprehensive + tier1 self-check for the 6 target companies."""
    import glob as _glob
    import re as _re2
    from scripts.build_pl_breakdown import extract_tier1
    y, qq = _re2.match(r"(\d{4})\.(\d)Q", quarter).groups()
    codes = {"KR0094": "신한라이프", "KR0104": "농협생명", "KR0071": "흥국생명",
             "KR0072": "케이디비", "KR0079": "미래에셋", "KR0083": "푸본현대"}
    print("########## quarter = %s ##########" % quarter)
    for code, name in codes.items():
        dirs = _glob.glob("data/dart/FY%s_Q%s/raw/%s_*" % (y, qq, code))
        tables = []
        for d in dirs:
            xs = _glob.glob(d + "/*.xml") + _glob.glob(d + "/xml/*.xml") + _glob.glob(d + "/extracted*/*.xml")
            for x in sorted(set(xs), key=os.path.getsize, reverse=True):
                try:
                    tables.extend(_iter_tables_with_context(Path(x)))
                except Exception:
                    pass
        t1 = extract_tier1(tables, code=code) or {}
        secvals, totals = extract_comprehensive(tables)
        t2 = build_items(secvals, totals)
        # Family B fallback (미래에셋 product-split) for items 4,5,9,10.
        if not any(t2.get(i) is not None for i in (4, 5)):
            t2b = extract_product_split(tables)
            for k, v in t2b.items():
                t2.setdefault(k, v)
        print("\n==== %s %s ====" % (code, name))
        print(" t2:", {k: round(v, 1) if isinstance(v, float) else v for k, v in sorted(t2.items(), key=lambda kv: str(kv[0]))})
        # _jang totals priority: note 총 (comprehensive) -> 미래에셋 income-statement
        # 일반보험* sub-lines (_life_*) -> generic.  For 신한 the note 총 over-states by the
        # PAA-presentation reclass, so we ALSO try the matching income-statement 보험수익/
        # 보험서비스비용 line and prefer it when it reconciles item1 better.
        jr = t2.get("_jang_rev")
        jc = t2.get("_jang_cost")
        jrr = t2.get("_jang_rerev")
        jrc = t2.get("_jang_recost")
        if t1.get("_life_rev") is not None:
            jr = abs(t1["_life_rev"])
        if t1.get("_life_cost") is not None:
            jc = abs(t1["_life_cost"])
        if t1.get("_life_rerev") is not None:
            jrr = abs(t1["_life_rerev"])
        if t1.get("_life_recost") is not None:
            jrc = abs(t1["_life_recost"])
        item1 = t1.get(1)
        item16 = t1.get(16)
        if item16 is None:
            item16 = _pick_is_line(tables, code, "기타사업비용")
        # 신한: prefer the income-statement 보험수익/보험서비스비용 standalone lines, which
        # reconcile exactly (note 총 includes a small PAA line the IS nets elsewhere).
        if code == "KR0094":
            isr = _pick_is_line(tables, code, "보험수익", exclude=("재보험", "보험영업"))
            isc = _pick_is_line(tables, code, "보험서비스비용", exclude=("재보험",))
            if isr is not None:
                jr = isr
            if isc is not None:
                jc = isc
        item3 = (jr - jc) if (jr is not None and jc is not None) else None
        item8 = (jrr - jrc) if (jrr is not None and jrc is not None) else None
        item2 = (item3 + item8) if (item3 is not None and item8 is not None) else None
        print(" item3=%s item8=%s item2=%s | item1=%s item16=%s" % (item3, item8, item2, item1, item16))
        if item2 is not None and item1 and item16 is not None:
            recon = item2 + 0 - item16
            gap = (recon - item1) / item1 * 100
            print(" RECON = item2+item15-item16 = %.1f vs item1 = %.1f | gap=%.2f%% -> %s"
                  % (recon, item1, gap, "PASS" if abs(gap) <= 1.5 else "FAIL"))
        else:
            print(" RECON: insufficient (item2=%s item1=%s item16=%s)" % (item2, item1, item16))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        selfcheck(sys.argv[2] if len(sys.argv) > 2 else "2025.4Q")
    else:
        main()
