#!/usr/bin/env python3
"""Stage 1 of the reinsurer loss-ratio sweep (ticket 20261012T0100Z): run the EXISTING extractor on KR1101~KR1108 only
and dump the result to data/_derived/reinsurer_loss_ratio_20261012/ (never to data/loss_ratio/).

Nothing here changes extract_loss_ratio.py. It reuses its functions on a restricted PDF set.
Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_loss_ratio_reinsurers_20261012.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_loss_ratio as X  # noqa: E402

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = ROOT / "data" / "_derived" / "reinsurer_loss_ratio_20261012"
REINS = [f"KR110{i}" for i in range(1, 9)] + ["KR1011"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta_all = X.load_company_meta()
    meta = {c: meta_all[c] for c in REINS if c in meta_all}
    print("meta", meta)
    pdfs_all = X.discover_pdfs(meta_all)
    pdfs = {k: v for k, v in pdfs_all.items() if k[1] in REINS}
    print("pdf cells", len(pdfs))
    idx = X.load_index(pdfs)
    results = X.extract_all(pdfs, idx, meta)
    errs = {k: v["error"] for k, v in results.items() if "error" in v}
    print("errors", errs)
    vis = {"A": [], "B": [], "C": []}
    final, census, flags_log = X.assemble(results, vis, [], meta, pdfs)
    X.sort_final(final)
    diffs = X.build_diffs(final, meta)
    survey = X.build_survey(pdfs, idx, meta)
    for name, rows in (("A", final["A"]), ("B", final["B"])):
        (OUT / f"ext_{name}.json").write_text(json.dumps([X.clean_row(r) for r in rows], ensure_ascii=False, indent=1), encoding="utf-8")
    X.write_csv(OUT / "ext_census.csv", X.CENSUS_FIELDS, census)
    X.write_csv(OUT / "ext_survey.csv", X.SURVEY_FIELDS, survey)
    X.write_csv(OUT / "ext_diffs.csv", X.DIFF_FIELDS, diffs)
    print("rows A", len(final["A"]), "B", len(final["B"]), "census", len(census), "diffs", len(diffs))
    for r in census:
        print(r["원보험사코드"], r["공시분기"], r["표"], r["기준연도"], r["상태"], str(r.get("쪽", ""))[:30], str(r.get("근거", ""))[:140])


if __name__ == "__main__":
    main()
