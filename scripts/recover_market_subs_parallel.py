# -*- coding: utf-8 -*-
"""Parallel, timeout-isolated 시장위험 36-40 PDF recovery (K-ICS).

The monolithic market_subrisk_pdf_recover.py runs pdfplumber sequentially over
~250 disclosure PDFs; a single pathological PDF (huge/scan) makes the whole run
hang (observed 56 min). This driver runs extract_from_pdf in a ProcessPool with a
HARD per-PDF timeout, so one stuck file is isolated (marked TIMEOUT) instead of
blocking everything — and the rest extract in parallel.

It REUSES the proven extraction (extract_from_pdf, _bare_subrisk_item, _row_value,
reconcile gate mkt_est) so values are identical to the sequential path.

It does NOT write kics_disclosure.json (validation may edit it concurrently).
Instead it writes a review artifact:
  artifacts/kics_validation/market_subs_recovered.json  (RECOVERED cells, ready to apply)
  artifacts/kics_validation/market_subs_census.md        (full classification)
Apply step is a separate, controlled single-writer pass after review.

Usage: PYTHONIOENCODING=utf-8 python scripts/recover_market_subs_parallel.py [--workers 6] [--timeout 30]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FTimeout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from market_subrisk_pdf_recover import (  # noqa: E402
    extract_from_pdf, quarter_to_period, NAMES,
)
from fill_market_subitems_to_disclosure import (  # noqa: E402
    _parse_value, _to_eok, mkt_est, _meta_for, MKT_SUBS,  # noqa: F401
)

JSON_PATH = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"
ART = REPO / "artifacts" / "kics_validation"


def _worklist():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    item19, have, name = {}, defaultdict(set), {}
    for r in rows:
        it = int(r["항목번호"]); key = (r["원보험사코드"], r["공시분기"])
        name[r["원보험사코드"]] = r["원수사명"]
        if it == 19:
            v = _parse_value(str(r["값"]))
            if v is not None:
                item19[key] = float(v)
        if 36 <= it <= 40 and _parse_value(str(r["값"])) is not None:
            have[key].add(it)
    existing = {(r["원보험사코드"], int(r["항목번호"]), r["공시분기"]) for r in rows}
    work = sorted(k for k, v in item19.items() if v > 0 and len(have[k]) < 5)
    return rows, item19, name, existing, work


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=30, help="hard per-PDF seconds")
    args = ap.parse_args(argv)

    rows, item19, name, existing, work = _worklist()
    # map (co,q) -> first disclosure PDF
    targets, buckets = [], defaultdict(list)
    for code, quarter in work:
        pdfs = sorted(glob.glob(str(DISCLOSURE / quarter_to_period(quarter) / "raw" / f"{code}_*.pdf")))
        if not pdfs:
            buckets["NO_PDF"].append((code, quarter)); continue
        targets.append((code, quarter, pdfs[0]))

    print(f"worklist={len(work)}  with_pdf={len(targets)}  no_pdf={len(buckets['NO_PDF'])}  "
          f"workers={args.workers} timeout={args.timeout}s", flush=True)

    results = {}  # (code,quarter) -> (got, npg, had_text) or None on timeout/err
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(extract_from_pdf, pdf): (code, quarter) for code, quarter, pdf in targets}
        done = 0
        for f, (code, quarter) in list(fut.items()):
            try:
                results[(code, quarter)] = f.result(timeout=args.timeout)
            except FTimeout:
                buckets["TIMEOUT"].append((code, quarter)); results[(code, quarter)] = None
            except Exception as e:
                buckets["ERR"].append((code, quarter, str(e)[:50])); results[(code, quarter)] = None
            done += 1
            if done % 25 == 0:
                print(f"  ...{done}/{len(targets)}", flush=True)
        ex.shutdown(wait=False, cancel_futures=True)

    # classify + collect RECOVERED (reconcile-gated), do NOT write kics json
    recovered = []
    for code, quarter, _pdf in targets:
        res = results.get((code, quarter))
        if res is None:
            continue  # already in TIMEOUT/ERR
        got, npg, had_text = res
        if not had_text:
            buckets["SCAN"].append((code, quarter)); continue
        v19 = item19[(code, quarter)]
        found = sorted(got)
        if len(found) >= 4:
            v5 = [float(_to_eok(got.get(i, 0), "백만원")) for i in (36, 37, 38, 39, 40)]
            rel = abs(mkt_est(v5) - v19) / v19 * 100
            if rel < 2:
                stored = []
                for i in (36, 37, 38, 39, 40):
                    if i in got and (code, i, quarter) not in existing:
                        recovered.append({"code": code, "quarter": quarter, "item": i,
                                          "name": NAMES[i], "value_eok": _to_eok(got[i], "백만원")})
                        stored.append(i)
                buckets["RECOVERED"].append((code, quarter, found, round(rel, 1), stored))
                continue
            buckets["PARTIAL_NORC"].append((code, quarter, found, round(rel, 1)))
        elif found and set(found) <= {36}:
            buckets["G36_ONLY"].append((code, quarter))
        elif found:
            buckets["PARTIAL_NORC"].append((code, quarter, found, None))
        else:
            buckets["AGGREGATE"].append((code, quarter, npg))

    ART.mkdir(parents=True, exist_ok=True)
    (ART / "market_subs_recovered.json").write_text(
        json.dumps(recovered, ensure_ascii=False, indent=2), encoding="utf-8")
    order = ["RECOVERED", "PARTIAL_NORC", "G36_ONLY", "AGGREGATE", "SCAN", "TIMEOUT", "NO_PDF", "ERR"]
    lines = ["# 시장위험 하위 PDF recover + census (parallel)", ""]
    for b in order:
        items = buckets.get(b, [])
        lines.append(f"## {b}: {len(items)}")
        for it in items:
            lines.append("- " + " ".join(str(x) for x in it) + f"  ({name.get(it[0], '')})")
        lines.append("")
    (ART / "market_subs_census.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n=== census ===")
    for b in order:
        print(f"  {b}: {len(buckets.get(b, []))}")
    print(f"\nRECOVERED cells (item rows) ready to apply: {len(recovered)}")
    print(f"artifact: {ART / 'market_subs_recovered.json'}")


if __name__ == "__main__":
    main(sys.argv[1:])
