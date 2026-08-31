# -*- coding: utf-8 -*-
"""Scoped multi-company loader for the 2026.2Q recovery of 6 badly-loaded companies.

Reuses the REAL fill_* modules' tested inner functions (never reimplements matching
logic), runs each stage on an in-memory SCRATCH copy of the live master (so other
companies' rows in the scratch copy may also change -- that's fine, we discard them),
then cherry-picks ONLY the target companies' new/changed rows and reports them. Nothing
is written to the live kics_disclosure.json by this script -- it only prints + optionally
dumps a scratch JSON for inspection. A separate apply step (apply_scoped_loader_diff.py)
does the actual live merge with a fresh read immediately before write.

Usage: PY scripts/_probes/scoped_loader_20260831.py [--codes KR0069,KR0070,...] [--dump PATH]
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

MASTER = REPO / "kics_disclosure.json"
PERIOD_LABEL = "FY2026_Q2"
QUARTER = "2026.2Q"

DEFAULT_CODES = ["KR0069", "KR0070", "KR0082", "KR0001", "KR0073", "KR1011"]


def load_master():
    return json.loads(MASTER.read_text(encoding="utf-8"))


def row_key(r):
    return (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"), r.get("항목명"))


def diff_rows(before, after, codes):
    """Return (added, changed) lists restricted to `codes`, comparing by (code,quarter,item,name)."""
    before_idx = {row_key(r): r for r in before}
    added, changed = [], []
    for r in after:
        if r.get("원보험사코드") not in codes:
            continue
        k = row_key(r)
        if k not in before_idx:
            added.append(r)
        else:
            b = before_idx[k]
            if b.get("값") != r.get("값") or b.get("값_적용후") != r.get("값_적용후"):
                changed.append((b, r))
    return added, changed


def stage_a_core(rows, codes):
    """items 1-26 (28 excluded -- derived) via fill_period_to_disclosure.py's _process."""
    import fill_period_to_disclosure as fp

    F = fp._fields()
    before_snapshot = copy.deepcopy(rows)
    ins, upd, rem = fp._process(rows, [PERIOD_LABEL], False, F, target_quarter=None)
    added, changed = diff_rows(before_snapshot, rows, codes)
    print(f"[stage A core 1-28] global ins={ins} upd={upd} rem={rem} | target-company added={len(added)} changed={len(changed)}")
    return added, changed


def stage_b_subitems(rows, codes):
    import fill_subitems_to_disclosure as fs

    before_snapshot = copy.deepcopy(rows)
    new_rows, updated, summary, warnings = fs._process_period(rows, PERIOD_LABEL, dry_run=True, refresh=False)
    # _process_period does NOT mutate `rows` in place (dry_run semantics return new_rows
    # separately) -- append manually to mirror what --apply (non-dry-run in main()) would do.
    rows.extend(new_rows)
    added, changed = diff_rows(before_snapshot, rows, codes)
    my_summary = [s for s in summary if s[0] in codes]
    print(f"[stage B subitems 29-35] global new={len(new_rows)} upd={updated} | target-company added={len(added)}")
    for code, matched, missed in my_summary:
        print(f"    {code}: matched={matched}/6 missed={missed}")
    for w in warnings:
        if any(c in w for c in codes):
            print(f"    WARN: {w}")
    return added, changed


def stage_c_market(rows, codes):
    import fill_market_subitems_to_disclosure as fm

    before_snapshot = copy.deepcopy(rows)
    existing = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows}
    new_rows = []
    bad_detail = []
    quarter = fm._md_period_to_quarter(PERIOD_LABEL)
    md_dir = fm.MD_INBOX / PERIOD_LABEL
    pdf_dir = fm.DISCLOSURE / PERIOD_LABEL / "raw"
    pdf_dir_fallback = fm.DISCLOSURE / PERIOD_LABEL / "pdf"
    for md_path in sorted(md_dir.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        if code not in codes:
            continue
        meta = fm._meta_for(rows, code)
        if not meta:
            print(f"    {code}: no baseline meta (no prior-quarter row at all) -- skip")
            continue
        subs = fm.extract_mkt_subs(md_path.read_text(encoding="utf-8"))
        v5map = {}
        mkt_rows_pending = []
        item36_stored = None
        for item_no, name, _ in fm.MKT_SUBS:
            if item_no in subs:
                value, unit = subs[item_no]
                eok = fm._to_eok(value, unit)
                v5map[item_no] = float(eok)
                key = (code, item_no, quarter)
                if key not in existing:
                    mkt_rows_pending.append({**meta, "원보험사코드": code, "항목번호": item_no,
                                              "항목명": name, "공시분기": quarter, "값": eok})
        if v5map:
            v5 = [v5map.get(36, 0.0), v5map.get(37, 0.0), v5map.get(38, 0.0), v5map.get(39, 0.0), v5map.get(40, 0.0)]
            item19 = next((float(str(r["값"]).replace(",", "")) for r in rows
                            if r["원보험사코드"] == code and r["공시분기"] == quarter
                            and r["항목번호"] == 19 and fm._parse_value(str(r["값"])) is not None), None)
            if item19 and sum(v5) > 0:
                est = fm.mkt_est(v5)
                rel = abs(est - item19) / item19 * 100
                if rel < 2:
                    new_rows.extend(mkt_rows_pending)
                    item36_stored = v5map.get(36)
                    print(f"    {code}: MKT-OK est={est:.1f} item19={item19:.1f} rel={rel:.2f}% -> +{len(mkt_rows_pending)} rows")
                else:
                    bad_detail.append(f"    {code}: MKT-SKIP est={est:.1f} item19={item19:.1f} rel={rel:.1f}% (NOT stored)")
            else:
                bad_detail.append(f"    {code}: MKT-SKIP no item19 anchor or v5 all-zero (item19={item19})")
        pdfs = sorted((pdf_dir).glob(f"{code}_*.pdf")) if pdf_dir.is_dir() else []
        if not pdfs and pdf_dir_fallback.is_dir():
            pdfs = sorted(pdf_dir_fallback.glob(f"{code}_*.pdf"))
        if pdfs:
            try:
                vals, total = fm.extract_irr_netassets(str(pdfs[0]))
            except Exception as e:
                vals, total = None, None
                bad_detail.append(f"    {code}: IRR extract exception: {e}")
            if vals and total is not None and total > 0:
                rel = abs(fm.derive_irr(vals) - total) / total * 100
                eok_vals = [float(fm._to_eok(v, "백만원")) for v in vals]
                derived_eok = fm.derive_irr(eok_vals)
                if item36_stored is not None:
                    tol = 0.9 * max(2.0, 0.05 * abs(derived_eok))
                    passes = abs(derived_eok - item36_stored) <= tol
                    anchor = f"item36={item36_stored:.1f} derived={derived_eok:.1f} tol={tol:.1f}"
                else:
                    passes = rel < 5
                    anchor = f"no item36 stored; rel_total={rel:.1f}%"
                if passes:
                    n_irr = 0
                    for k, (item_no, name) in enumerate(fm.IRR_SCEN):
                        key = (code, item_no, quarter)
                        if key not in existing:
                            new_rows.append({**meta, "원보험사코드": code, "항목번호": item_no,
                                              "항목명": name, "공시분기": quarter, "값": fm._to_eok(vals[k], "백만원")})
                            n_irr += 1
                    if item36_stored is None and (code, 36, quarter) not in existing and total > 0:
                        new_rows.append({**meta, "원보험사코드": code, "항목번호": 36,
                                          "항목명": "3-1. 금리위험액", "공시분기": quarter, "값": fm._to_eok(total, "백만원")})
                    print(f"    {code}: IRR-OK {anchor} -> +{n_irr} rows")
                else:
                    bad_detail.append(f"    {code}: IRR-SKIP {anchor} rel_total={rel:.1f}% (NOT stored)")
            elif vals:
                bad_detail.append(f"    {code}: IRR-SKIP no disclosed total to verify")
            else:
                bad_detail.append(f"    {code}: IRR-SKIP no vals extracted from raw PDF")
        else:
            bad_detail.append(f"    {code}: no raw PDF found under {pdf_dir}")
    rows.extend(new_rows)
    added, changed = diff_rows(before_snapshot, rows, codes)
    print(f"[stage C market 36-46] target-company added={len(added)}")
    for d in bad_detail:
        print(d)
    return added, changed


def stage_d_post_transition(rows, codes):
    import fill_post_transition_to_disclosure as fpt

    before_snapshot = copy.deepcopy(rows)
    updated, equal_skipped, companies, log = fpt._process_period(rows, PERIOD_LABEL)
    added, changed = diff_rows(before_snapshot, rows, codes)
    print(f"[stage D post-transition 값_적용후] global updated={updated} companies_touched={companies} | target-company added={len(added)} changed={len(changed)}")
    for line in log:
        if any(c in line for c in codes):
            print(f"    {line}")
    return added, changed


PATCH_DIR = REPO / "data" / "_derived"


def stage_e_patches(rows, codes):
    """Apply the hand-verified raw-PDF patch JSONs (_patch_2026q2_<CODE>.json) for
    items the docling MD genuinely never captured (confirmed non-deterministic
    docling table-recognition failures for KR0069/KR0001, gap-covered pages for
    KR0070/KR0082/KR1011 subrisk tables). INSERT-only: a patch cell whose
    (code,quarter,item) key ALREADY exists in `rows` is a surprise -- reported,
    not silently overwritten (patches were authored against a specific diagnosed
    gap; if the gap already closed some other way, human review, not clobber)."""
    added, conflicts = [], []
    for code in sorted(codes):
        path = PATCH_DIR / f"_patch_2026q2_{code}.json"
        if not path.is_file():
            continue
        patch = json.loads(path.read_text(encoding="utf-8"))
        if patch.get("company_code") != code:
            print(f"    !! patch file company_code mismatch: {path.name} says {patch.get('company_code')!r}")
            continue
        quarter = patch.get("quarter")
        meta = next((r for r in rows if r["원보험사코드"] == code), None)
        if meta is None:
            print(f"    !! {code}: no baseline row in master to copy meta from -- skip patch")
            continue
        existing_keys = {
            (r["원보험사코드"], r["공시분기"], r["항목번호"])
            for r in rows if r["원보험사코드"] == code and r["공시분기"] == quarter
        }
        n_added = 0
        for cell in patch["cells"]:
            key = (code, quarter, cell["항목번호"])
            if key in existing_keys:
                if cell.get("_override_verified"):
                    target = next(
                        r for r in rows
                        if r["원보험사코드"] == code and r["공시분기"] == quarter
                        and r["항목번호"] == cell["항목번호"]
                    )
                    old_val = target.get("값")
                    target["값"] = str(cell["값"])
                    if "값_적용후" in cell and cell["값_적용후"] is not None:
                        target["값_적용후"] = str(cell["값_적용후"])
                    conflicts.append((code, quarter, cell["항목번호"],
                                       f"OVERRIDDEN (verified patch): {old_val!r} -> {cell['값']!r}"))
                else:
                    conflicts.append((code, quarter, cell["항목번호"], "already present -- patch NOT applied"))
                continue
            new_row = {
                "원보험사코드": code,
                "원수사명": meta["원수사명"],
                "티커": meta["티커"],
                "생손보여부": meta["생손보여부"],
                "항목번호": cell["항목번호"],
                "항목명": cell["항목명"],
                "공시분기": quarter,
                "값": str(cell["값"]),
            }
            if "값_적용후" in cell and cell["값_적용후"] is not None:
                new_row["값_적용후"] = str(cell["값_적용후"])
            rows.append(new_row)
            added.append(new_row)
            n_added += 1
        print(f"    {code}: patch {path.name} -> +{n_added} rows ({len(patch['cells']) - n_added} skipped)")
    for c in conflicts:
        print(f"    !! CONFLICT {c}")
    print(f"[stage E raw-PDF patches] target-company added={len(added)} conflicts={len(conflicts)}")
    return added, conflicts


def build_scoped_result(original_rows, processed_rows, codes):
    """Reconstruct 'fresh live master, but ONLY `codes`' rows carry the stage
    results' insertions/edits -- every other company's row is restored to its
    EXACT original snapshot, and any insertion the stages made for a non-target
    company is discarded. This lets us reuse the real fill_* functions (which
    have no per-company filter and touch the whole `rows` list) while still
    keeping the live-file blast radius to exactly our 6 companies, per the
    task's 'other sessions are editing the same master -- cell by cell only'
    constraint."""
    original_by_key = {row_key(r): r for r in original_rows}
    processed_by_key = {row_key(r): r for r in processed_rows}
    final = []
    seen = set()
    for r in original_rows:
        k = row_key(r)
        seen.add(k)
        code = r.get("원보험사코드")
        if code in codes and k in processed_by_key:
            final.append(processed_by_key[k])
        else:
            final.append(r)
    # new insertions (keys that didn't exist in original at all) -- only for target codes
    new_inserts = [
        processed_by_key[k] for k in processed_by_key
        if k not in seen and processed_by_key[k].get("원보험사코드") in codes
    ]
    final.extend(new_inserts)
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", default=",".join(DEFAULT_CODES))
    ap.add_argument("--dump", help="optional path to write the full scratch master JSON for inspection")
    ap.add_argument("--stages", default="ABCDE", help="which stages to run, e.g. A or AB or ABCDE")
    ap.add_argument("--apply-live", action="store_true",
                     help="after running stages, write the scoped result back to the LIVE "
                          "kics_disclosure.json (fresh read was already done at top of main; "
                          "only target-codes' rows are touched, everything else restored byte-for-byte)")
    args = ap.parse_args()
    codes = set(args.codes.split(","))

    rows = load_master()
    original_rows = copy.deepcopy(rows)
    print(f"loaded live master: {len(rows)} rows. target codes: {sorted(codes)}\n")

    all_added, all_changed = [], []
    if "A" in args.stages:
        a, c = stage_a_core(rows, codes)
        all_added += a; all_changed += c
    if "B" in args.stages:
        a, c = stage_b_subitems(rows, codes)
        all_added += a; all_changed += c
    if "C" in args.stages:
        a, c = stage_c_market(rows, codes)
        all_added += a; all_changed += c
    if "D" in args.stages:
        a, c = stage_d_post_transition(rows, codes)
        all_added += a; all_changed += c
    if "E" in args.stages:
        a, c = stage_e_patches(rows, codes)
        all_added += a  # conflicts (c) are informational, not row diffs

    print(f"\n=== TOTAL across stages run: added={len(all_added)} changed={len(all_changed)} ===")
    from collections import Counter
    by_code = Counter(r["원보험사코드"] for r in all_added)
    for code in sorted(codes):
        print(f"  {code}: +{by_code.get(code, 0)} rows")

    if args.dump:
        Path(args.dump).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nscratch master dumped to {args.dump} ({len(rows)} rows)")

    if args.apply_live:
        scoped = build_scoped_result(original_rows, rows, codes)
        # sanity: every row NOT belonging to a target code must be byte-identical
        # to the pre-stage snapshot (guards against a stage's global side effect
        # -- e.g. fill_period's cross-company item4 reconcile path -- leaking
        # outside our 6 companies).
        orig_by_key = {row_key(r): r for r in original_rows}
        scoped_by_key = {row_key(r): r for r in scoped}
        offsite_diff = 0
        for k, r in scoped_by_key.items():
            if r.get("원보험사코드") in codes:
                continue
            o = orig_by_key.get(k)
            if o is None or o.get("값") != r.get("값") or o.get("값_적용후") != r.get("값_적용후"):
                offsite_diff += 1
                print(f"  !! OFFSITE CHANGE BLOCKED-CHECK FAILED: {k}")
        removed_offsite = len(orig_by_key) - sum(1 for k in orig_by_key if k in scoped_by_key)
        print(f"\noffsite-company integrity check: diffs={offsite_diff} missing_from_scoped={removed_offsite}")
        if offsite_diff or removed_offsite:
            print("REFUSING to write live master -- offsite integrity check failed.")
            return
        # fresh re-read + FULL byte-level re-diff immediately before write, to shrink
        # the race window against concurrent sessions as much as possible (row-count
        # match alone would miss a concurrent in-place value edit).
        live_now = load_master()
        live_now_json = json.dumps(live_now, ensure_ascii=False, sort_keys=True)
        original_json = json.dumps(original_rows, ensure_ascii=False, sort_keys=True)
        if live_now_json != original_json:
            print(f"\nLIVE MASTER CHANGED SINCE OUR READ ({len(original_rows)} -> {len(live_now)} rows, "
                  f"content differs). Re-run this script (fresh read) rather than force-writing over a "
                  f"concurrent edit.")
            return
        MASTER.write_text(json.dumps(scoped, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWROTE live master: {len(original_rows)} -> {len(scoped)} rows "
              f"(+{len(scoped) - len(original_rows)}, target codes only)")


if __name__ == "__main__":
    main()
