"""Full population probe for inbox/parser/
20260828T2100Z__orchestrator__KR0070__abl_yesilcha_both_legs.md (ABL생명 KR0070, item6/item11).

For every quarter with raw XML on disk (2023.1Q-2026.2Q, 14 filings):
  1. Locates the "26/27. 보험영업수익과 보험영업비용" note's TWO tables -- (1) 보험영업수익 (has
     the 보험수익 + 재보험수익 sections) and (2) 보험영업비용 (보험서비스비용 + 재보험비용
     sections) -- section-scanning each table by its own blank-row section headers (NOT
     'N-style' label prefixes, which is what tier2._row_section handles -- ABL's section
     markers are their own row with empty numeric cells).
  2. When both a 연결 and separate 별도 copy of the note exist in the same filing (annual
     사업보고서), prefers OFS (별도) via common._tag_basis/_prefer_ofs, falling back to the
     first occurrence when basis is undetermined -- and reports whether the two copies'
     values actually differ (they were byte-identical for 2024.4Q on inspection).
  3. Reads the correct YTD (당기 누적) column via a generalised tier1._ytd_col: 4-col header
     ([3개월,누적]x2, quarterly/half-year filings) uses its column-1 rule; a 2-col header
     ([당기,전기], annual 사업보고서) uses column 0.
  4. Computes:
       item6  = (예상보험금+예상손해조사비+예상계약유지비+예상투자관리비)
              − (발생보험금+발생손해조사비+발생계약유지비+발생투자관리비)
       item11 = (발생재보험금+발생손해조사비[재보험수익 section])
              − (예상재보험금+예상손해조사비[재보험비용 section])
     (item11's 발생-minus-예상 order, not item6's 예상-minus-발생 order, is deliberate: 예상 sits
     on the COST section for reinsurance and 발생 sits on the REVENUE section -- the opposite
     placement from direct -- so mirroring item6's literal token order would flip the sign.
     This instead keeps the SAME rule item8 itself is built from: revenue-section rows enter
     positively, cost-section rows negatively; see the ticket / commit message for the full
     derivation.)
  5. Cross-checks note 37 prose ("예상 보험금 대비 실제 보험금 차이가 N억원이며, 예상 사업비
     대비 실제 사업비 차이는 M억원") against (예상보험금−발생보험금) and
     ((예상손해조사비+예상계약유지비+예상투자관리비)−(발생손해조사비+발생계약유지비+발생투자관리비)).
  6. Cross-checks item8 (already in the master, sourced independently of this note) against
     this note's 재보험수익 소계 − 재보험비용 소계, and item3 against 보험수익 소계 − 보험서비스비용 소계.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_full_probe.py
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _norm, _row_nums, _tag_basis, _prefer_ofs
from scripts.pl_breakdown.tier2 import _is_rollforward

QUARTER_DIRS = {
    "2023.1Q": "data/dart/FY2023_Q1/raw/KR0070_에이비엘생명보험",
    "2023.2Q": "data/dart/FY2023_Q2/raw/KR0070_에이비엘생명보험",
    "2023.3Q": "data/dart/FY2023_Q3/raw/KR0070_에이비엘생명보험",
    "2023.4Q": "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518",
    "2024.1Q": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험",
    "2024.2Q": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험",
    "2024.3Q": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험",
    "2024.4Q": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358",
    "2025.1Q": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험",
    "2025.2Q": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험",
    "2025.3Q": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험",
    "2025.4Q": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080",
    "2026.1Q": "data/dart/FY2026_Q1/raw/KR0070_에이비엘생명보험",
    "2026.2Q": "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험",
}


def find_xml(rel_dir):
    d = REPO / rel_dir
    xs = glob.glob(str(d / "*.xml")) + glob.glob(str(d / "xml" / "*.xml"))
    xs = [x for x in xs if not x.endswith("document.zip")]
    if not xs:
        return None
    # largest file = main body (matches build_pl_breakdown._xmls_in's own heuristic)
    return Path(sorted(xs, key=lambda p: Path(p).stat().st_size, reverse=True)[0])


def _header_ytd_col(t):
    hb = " ".join(" ".join(h) for h in t.header).replace(" ", "")
    if "누적" in hb and "3개월" in hb:
        return 1 if hb.find("3개월") < hb.find("누적") else 0
    return 0


def _section_scan(t):
    """Yield (section, row) for every DATA row (nums non-empty), where section is whichever
    of the known blank-numeric header rows most recently preceded it."""
    sec = None
    for r in t.rows:
        lab = _norm(r[0])
        nums = _row_nums(r)
        if not nums and lab in ("보험수익", "재보험수익", "보험서비스비용", "재보험비용",
                                 "당기손익으로 인식된 금액", "보험계약금융손익", "재보험계약금융손익",
                                 "기타포괄손익으로 인식된 금액 (세전)"):
            sec = lab
            continue
        if nums:
            yield sec, lab, nums


def find_note26_tables(all_tables):
    """Return list of (rev_table, cost_table) candidate pairs, matched by EXACT row label
    (not substring -- '발생보험금' must not catch '발생보험금 및 기타보험서비스비용' rollforward
    rows) and adjacency (cost table's section-scan must show '예상재보험금' under 재보험비용,
    confirming it's note26's part-(2), not some unrelated 발생보험금-labelled table)."""
    rev_tables, cost_tables = [], []
    for t in all_tables:
        if _is_rollforward(t):
            continue
        labs_exact = {_norm(r[0]) for r in t.rows}
        if "예상보험금" in labs_exact and "소계" in labs_exact:
            rev_tables.append(t)
        if "발생보험금" in labs_exact and "예상재보험금" in labs_exact:
            cost_tables.append(t)
    pairs = []
    # Pair by document order / adjacency: for each cost table, the nearest PRECEDING rev
    # table (note26's (1) always precedes (2) in document order for both 연결/별도 copies).
    for ct in cost_tables:
        best = None
        for rt in rev_tables:
            if rt.line_no < ct.line_no and (best is None or rt.line_no > best.line_no):
                best = rt
        if best is not None:
            pairs.append((best, ct))
    return pairs


def row_val(t, exact_label, col):
    for r in t.rows:
        if _norm(r[0]) == exact_label:
            nums = _row_nums(r)
            if col < len(nums):
                return nums[col]
            return nums[0] if nums else None
    return None


def _find_note37(text):
    """Return (claim_diff_eok, expense_diff_eok) parsed from the '예상 보험금 대비 실제 보험금
    차이가 N억원이며, 예상 사업비 대비 실제 사업비 차이는 M억원' sentence, or (None, None)."""
    num_re = r"(\(-\)|[△▲])?\s*([\d,]+)\s*억\s*원"
    m = re.search(
        r"예상\s*보험금\s*대비\s*실제\s*보험금\s*차이가?\s*" + num_re + r".{0,150}?"
        r"예상\s*사업비\s*대비\s*실제\s*사업비\s*차이는?\s*" + num_re,
        text)
    if not m:
        return None, None
    def numify(sign, digits):
        v = float(digits.replace(",", ""))
        return -v if sign else v
    return numify(m.group(1), m.group(2)), numify(m.group(3), m.group(4))


def main():
    print(f"{'quarter':8s} {'#pairs':>6s} {'ofs?':>5s} {'diff?':>6s}  "
          f"{'item6(mm)':>10s} {'item11(mm)':>11s}  "
          f"{'note37_claim':>12s} {'calc_claim':>10s} {'note37_exp':>10s} {'calc_exp':>9s}  "
          f"{'item3chk':>9s} {'item8chk':>9s}")
    results = {}
    for q, rel_dir in QUARTER_DIRS.items():
        xml = find_xml(rel_dir)
        if xml is None:
            print(f"{q:8s}  NO XML in {rel_dir}")
            continue
        all_tables = list(_iter_tables_with_context(xml))
        _tag_basis(all_tables, xml)
        pairs = find_note26_tables(all_tables)
        if not pairs:
            print(f"{q:8s}  NOTE26 NOT FOUND ({len(all_tables)} tables scanned)")
            continue

        # Compare values across pairs (if >1) to see if 연결/별도 actually differ.
        def key_vals(rt, ct):
            col_r, col_c = _header_ytd_col(rt), _header_ytd_col(ct)
            return (row_val(rt, "예상보험금", col_r), row_val(ct, "발생보험금", col_c))

        vals_set = {key_vals(rt, ct) for rt, ct in pairs}
        diff = len(vals_set) > 1

        ofs_pairs = [(rt, ct) for rt, ct in pairs
                     if getattr(rt, "_basis", None) == "OFS" or getattr(ct, "_basis", None) == "OFS"]
        chosen = ofs_pairs[0] if ofs_pairs else pairs[0]
        rev_t, cost_t = chosen
        col_r = _header_ytd_col(rev_t)
        col_c = _header_ytd_col(cost_t)

        # revenue-side direct 4종
        exp_claim = row_val(rev_t, "예상보험금", col_r)
        exp_lae = row_val(rev_t, "예상손해조사비", col_r) or 0
        exp_maint = row_val(rev_t, "예상계약유지비", col_r) or 0
        exp_inv = row_val(rev_t, "예상투자관리비", col_r) or 0
        # cost-side direct 4종
        inc_claim = row_val(cost_t, "발생보험금", col_c)
        inc_lae = row_val(cost_t, "발생손해조사비", col_c) or 0
        inc_maint = row_val(cost_t, "발생계약유지비", col_c) or 0
        inc_inv = row_val(cost_t, "발생투자관리비", col_c) or 0

        item6 = None
        if exp_claim is not None and inc_claim is not None:
            item6 = (exp_claim + exp_lae + exp_maint + exp_inv) - (inc_claim + inc_lae + inc_maint + inc_inv)

        # reinsurance leg: revenue-side 발생재보험금/발생손해조사비 (재보험수익 section);
        # cost-side 예상재보험금/예상손해조사비 (재보험비용 section)
        re_inc_claim = row_val(rev_t, "발생재보험금", col_r)
        re_inc_lae = row_val(rev_t, "발생손해조사비", col_r)  # section-ambiguous name, see note
        re_exp_claim = row_val(cost_t, "예상재보험금", col_c)
        re_exp_lae = row_val(cost_t, "예상손해조사비", col_c)

        # '발생손해조사비' is ALSO the direct cost-side label -- need the reinsurance-SECTION
        # occurrence specifically (row_val's first-match is fine on rev_t only if the direct
        # side has no '발생손해조사비' row at all in the REVENUE table -- verify via section scan).
        re_inc_lae_sec = None
        re_exp_lae_sec = None
        for sec, lab, nums in _section_scan(rev_t):
            if sec == "재보험수익" and lab == "발생손해조사비":
                re_inc_lae_sec = nums[col_r] if col_r < len(nums) else nums[0]
        for sec, lab, nums in _section_scan(cost_t):
            if sec == "재보험비용" and lab == "예상손해조사비":
                re_exp_lae_sec = nums[col_c] if col_c < len(nums) else nums[0]

        item11 = None
        if re_inc_claim is not None and re_exp_claim is not None:
            item11 = (re_inc_claim + (re_inc_lae_sec or 0)) - (re_exp_claim + (re_exp_lae_sec or 0))

        # note 37 prose cross-check (search whichever basis; text is shared prose, not table)
        text = xml.read_text(encoding="utf-8", errors="replace")
        n37_claim, n37_exp = _find_note37(text)
        calc_claim_eok = (exp_claim - inc_claim) / 100 if None not in (exp_claim, inc_claim) else None
        calc_exp_eok = ((exp_lae + exp_maint + exp_inv) - (inc_lae + inc_maint + inc_inv)) / 100

        # item3/item8 cross-checks against note26's own subtotals
        rev_sub = row_val(rev_t, "소계", col_r)  # NOTE: two '소계' rows exist (보험/재보험) --
        # need section-aware pick; use section scan instead below.
        rev_secs = {sec: nums for sec, lab, nums in _section_scan(rev_t) if lab == "소계"}
        cost_secs = {}
        sec = None
        for r in cost_t.rows:
            lab = _norm(r[0])
            nums = _row_nums(r)
            if not nums and lab in ("보험서비스비용", "재보험비용"):
                sec = lab
                continue
            if lab == "소계" and nums:
                cost_secs[sec] = nums
        item3_note = None
        item8_note = None
        try:
            rb_rev = rev_secs.get("보험수익")[col_r]
            rb_cost = cost_secs.get("보험서비스비용")[col_c]
            item3_note = rb_rev - rb_cost
            re_rev = rev_secs.get("재보험수익")[col_r]
            re_cost = cost_secs.get("재보험비용")[col_c]
            item8_note = re_rev - re_cost
        except Exception:
            pass

        def f(x, w=10):
            return f"{x:>{w},.0f}" if isinstance(x, (int, float)) else f"{'None':>{w}s}"

        print(f"{q:8s} {len(pairs):>6d} {'Y' if ofs_pairs else 'N':>5s} {'Y' if diff else 'N':>6s}  "
              f"{f(item6)} {f(item11,11)}  "
              f"{f(n37_claim,12)} {f(calc_claim_eok,10)} {f(n37_exp,10)} {f(calc_exp_eok,9)}  "
              f"{f(item3_note,9)} {f(item8_note,9)}")

        results[q] = dict(item6=item6, item11=item11, n37_claim=n37_claim, n37_exp=n37_exp,
                           calc_claim_eok=calc_claim_eok, calc_exp_eok=calc_exp_eok,
                           item3_note=item3_note, item8_note=item8_note,
                           n_pairs=len(pairs), has_ofs=bool(ofs_pairs), pairs_differ=diff,
                           xml=str(xml.relative_to(REPO)))

    out_path = REPO / "scripts/_probes/_tmp_abl_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
