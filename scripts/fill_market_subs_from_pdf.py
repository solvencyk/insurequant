"""Recover market sub-risks (items 36-40) from RAW PDF when the MD table is
absent or mis-parsed (reconcile-gated).

Many insurers disclose the 시장위험액 세부내역 (금리/주식/부동산/외환/자산집중) in the
정기경영공시 PDF but the PDF->MD conversion drops it, so the MD-only loader
(fill_market_subitems_to_disclosure.py) can't extract them. This script reads the
sub-5 directly from the PDF via fitz, auto-detects the unit, and stores ONLY when
the M-matrix sum reconciles item19 within 2% — so a wrong table/column never
enters the master. UPSERT (idempotent; existing rows untouched).

Spec: docs/agents/kics-market-risk-decomposition.md §3, §5.
Usage: PYTHONIOENCODING=utf-8 python scripts/fill_market_subs_from_pdf.py [--dry-run] [--limit N]
"""
from __future__ import annotations
import argparse, io, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import (  # noqa: E402
    _parse_value, _to_eok, mkt_est, _meta_for, MKT_SUBS,
)
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"

LBL = {36: ["금리위험"], 37: ["주식위험"], 38: ["부동산위험"], 39: ["외환위험"],
       40: ["자산집중위험", "자산집중"]}


def quarter_to_period(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def _norm(s):
    return re.sub(r"[\s\(\)\[\]\.\,\:·\-\+\*Ⅰ-Ⅹⅰ-ⅸ㈜주\)]+", "", s or "")


def _is_label_line(ln):
    """Return item_no if the line IS a bare sub-risk label (not a sentence)."""
    n = _norm(ln)
    if len(ln) > 14:  # a sentence, not a label cell
        return None
    for item, kws in LBL.items():
        for kw in kws:
            nk = _norm(kw)
            if n == nk or n == nk + "액":
                return item
    return None


def _nums_in(ln):
    out = []
    for tok in re.findall(r"-?[\d,]+\.?\d*", ln):
        v = _parse_value(tok)
        if v is not None:
            out.append(float(v))
    return out


def cand_interleaved(lines):
    """label line followed (within 3 lines) by its value; col0 = first numeric."""
    out = {}
    for j, ln in enumerate(lines):
        item = _is_label_line(ln)
        if item is None or item in out:
            continue
        for k in range(j + 1, min(j + 4, len(lines))):
            nums = _nums_in(lines[k])
            if nums:
                out[item] = nums[0]
                break
            if _is_label_line(lines[k]) is not None:
                break  # next label before any number -> this one has no value (=0)
    return out if 36 in out and 37 in out else {}


def cand_grouped(lines):
    """A run of label-lines then a run of value-lines, aligned by order;
    also handles a single line with several space-joined labels + a value line."""
    # (a) single-line concat: a line containing >=3 sub-risk keywords
    for j, ln in enumerate(lines):
        hits = [item for item, kws in LBL.items() if any(k in ln for k in kws)]
        if len(set(hits)) >= 3 and "시장위험" in ln:
            # the value row: next line with >= len(labels) numbers
            labels_in_order = _labels_in_order(ln)
            for k in range(j + 1, min(j + 4, len(lines))):
                nums = _nums_in(lines[k])
                if len(nums) >= len(labels_in_order) >= 3:
                    return _map_labels_vals(labels_in_order, nums)
    # (b) consecutive label-lines then consecutive value-lines
    j = 0
    while j < len(lines):
        if _is_label_line(lines[j]) is not None:
            labels = []
            k = j
            while k < len(lines) and _is_label_line(lines[k]) is not None:
                labels.append(_is_label_line(lines[k]))
                k += 1
            if len(labels) >= 3:
                vals = []
                while k < len(lines) and len(vals) < len(labels):
                    nums = _nums_in(lines[k])
                    if not nums and _is_label_line(lines[k]) is None and lines[k] not in ("",):
                        # a non-numeric, non-label line breaks the value run unless it's a dash
                        if _norm(lines[k]):
                            break
                    vals.extend(nums if nums else ([0.0] if lines[k].strip() in ("-", "─") else []))
                    k += 1
                if len(vals) >= len(labels):
                    out = {}
                    for idx, item in enumerate(labels):
                        if item not in out:
                            out[item] = vals[idx]
                    if 36 in out and 37 in out:
                        return out
            j = k
        else:
            j += 1
    return {}


def _labels_in_order(line):
    """Return sub-risk item_nos in the order their keyword appears in the line."""
    positions = []
    for item, kws in LBL.items():
        pos = min((line.find(k) for k in kws if line.find(k) >= 0), default=-1)
        if pos >= 0:
            positions.append((pos, item))
    seen = set()
    ordered = []
    for _, item in sorted(positions):
        if item not in seen:
            ordered.append(item); seen.add(item)
    return ordered


def _map_labels_vals(labels, nums):
    out = {}
    for idx, item in enumerate(labels):
        if idx < len(nums) and item not in out:
            out[item] = nums[idx]
    return out


def extract_candidates(pdf_path):
    import fitz
    cands = []
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return cands
    for i in range(doc.page_count):
        try:
            txt = doc[i].get_text()
        except Exception:
            continue
        if "시장위험" not in txt or "금리위험" not in txt or "주식위험" not in txt:
            continue
        # skip pure-narrative pages (method description) — require a numeric near a label
        lines = [l.strip() for l in txt.split("\n")]
        lines = [l for l in lines if l != ""]
        for fn in (cand_interleaved, cand_grouped):
            c = fn(lines)
            if c:
                cands.append((i, fn.__name__, c))
    doc.close()
    return cands


def best_v5(cands, item19):
    """Pick the candidate whose M-sum reconciles item19 (<2%), auto unit."""
    best = None
    for page, strat, c in cands:
        v5 = [c.get(36, 0.0), c.get(37, 0.0), c.get(38, 0.0), c.get(39, 0.0), c.get(40, 0.0)]
        if v5[0] == 0 or v5[1] == 0:  # need at least 금리 & 주식
            continue
        est = mkt_est(v5)
        if est <= 0:
            continue
        for scale, unit in ((100.0, "백만원"), (1.0, "억원")):
            rel = abs(est / scale - item19) / item19 * 100 if item19 else 999
            if rel < 2 and (best is None or rel < best[0]):
                best = (rel, scale, unit, c, page, strat)
    return best


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")
    existing = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows}

    # work-list: every (code, quarter) with item19 present but some of 36-40 missing
    item19 = {}
    have_sub = {}
    for r in rows:
        key = (r["원보험사코드"], r["공시분기"])
        if r["항목번호"] == 19:
            v = _parse_value(str(r["값"]))
            if v is not None:
                item19[key] = float(v)
        if r["항목번호"] in (36, 37, 38, 39, 40):
            have_sub.setdefault(key, set()).add(r["항목번호"])

    worklist = [k for k, v19 in item19.items()
                if len(have_sub.get(k, set())) < 5 and v19 > 0]
    worklist.sort()
    if args.limit:
        worklist = worklist[:args.limit]
    print(f"worklist (item19 present, <5 subs): {len(worklist)} (code,quarter)\n")

    new_rows, ok, fail, nopdf = [], [], [], 0
    for code, quarter in worklist:
        period = quarter_to_period(quarter)
        pdfs = disclosure_pdfs(period, code)
        if not pdfs:
            nopdf += 1
            continue
        cands = extract_candidates(pdfs[0])
        if not cands:
            continue
        best = best_v5(cands, item19[(code, quarter)])
        if best is None:
            fail.append((code, quarter))
            continue
        rel, scale, unit, c, page, strat = best
        meta = _meta_for(rows, code)
        if not meta:
            continue
        stored = []
        for item_no, name, _ in MKT_SUBS:
            if item_no not in c:
                continue  # absent sub-risk -> not stored (=0)
            if (code, item_no, quarter) in existing:
                continue
            eok = _to_eok(c[item_no], unit)
            new_rows.append({**meta, "원보험사코드": code, "항목번호": item_no,
                             "항목명": name, "공시분기": quarter, "값": eok})
            stored.append(item_no)
        ok.append((code, quarter, rel, unit, strat, stored))

    print(f"RECONCILED & storable: {len(ok)} quarters")
    for code, q, rel, unit, strat, stored in ok:
        print(f"  +{code} {q:9s} rel={rel:.2f}% {unit} {strat} items={stored}")
    print(f"\nNOT reconciled (table present, gate rejected): {len(fail)}")
    for code, q in fail[:40]:
        print(f"  -{code} {q}")
    print(f"no pdf: {nopdf}")
    print(f"\nnew rows to add: {len(new_rows)}")

    if args.dry_run:
        print("(dry-run; no write)")
        return 0
    if not new_rows:
        print("nothing to write")
        return 0
    rows.extend(new_rows)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
