"""Triage zero-children (29-35) cells: MD-has-it-but-unparsed vs MD-lost-it vs unknown.

For a given list of (code, quarter) cells, for each:
  1. Locate md_inbox/<period>/<code>_*.md
  2. Run _scan_subitem_rows() against it (same function fill_subitems_to_disclosure.py
     uses) -> does the CURRENT extractor find anything?
  3. Count raw label occurrences (사망위험/장수위험/...) in the MD body
  4. Report front-matter source_page_ranges / docling_dropped_pages (v5 fields) if present

Classifies each cell into:
  EXTRACTABLE_NOW   - _scan_subitem_rows finds >=1 item in the CURRENT md -> just needs
                       the fill script run/refreshed (or a JSON append)
  LABELS_PRESENT_NO_PARSE - labels are in the MD body but the scanner finds 0 -> extractor
                       bug (table shape it doesn't handle) worth investigating
  LABELS_ABSENT      - none of the 7 labels appear anywhere in the MD body -> either the
                       docling window dropped the section (check raw PDF next) or genuinely
                       not disclosed
  MD_MISSING         - no md_inbox file at all for this company/period

Usage:
    python scripts/_probes/probe_20260903_life2935_triage.py --cells-file PATH
        (one "CODE\tQUARTER" per line)
    or
    python scripts/_probes/probe_20260903_life2935_triage.py --bucket A
        (uses the classify() function from the census probe directly)
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MD_INBOX = REPO / "md_inbox"
LABELS = ("사망위험", "장수위험", "장해", "장기재물", "해지위험", "사업비위험", "대재해위험")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _quarter_to_period_label(quarter: str) -> str:
    y, q = quarter.split(".")
    return f"FY{y}_Q{q.rstrip('Q')}"


def _body_and_frontmatter(p: Path) -> tuple[str, dict]:
    t = p.read_text(encoding="utf-8")
    if not t.startswith("---"):
        return t, {}
    _, _, rest = t.partition("---\n")
    fm_text, _, body = rest.partition("\n---\n")
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return body, fm


def triage_cell(sub_mod, code: str, quarter: str) -> dict:
    period = _quarter_to_period_label(quarter)
    md_dir = MD_INBOX / period
    mds = sorted(md_dir.glob(f"{code}_*.md")) if md_dir.is_dir() else []
    if not mds:
        return {"code": code, "quarter": quarter, "status": "MD_MISSING", "md_path": None}
    md_path = mds[0]
    body, fm = _body_and_frontmatter(md_path)
    found = sub_mod._scan_subitem_rows(body, quarter)
    label_hits = {lab: body.count(lab) for lab in LABELS if lab in body}
    if found:
        status = "EXTRACTABLE_NOW"
    elif label_hits:
        status = "LABELS_PRESENT_NO_PARSE"
    else:
        status = "LABELS_ABSENT"
    return {
        "code": code,
        "quarter": quarter,
        "status": status,
        "md_path": str(md_path),
        "found": found,
        "label_hits": label_hits,
        "source_page_ranges": fm.get("source_page_ranges"),
        "docling_dropped_pages": fm.get("docling_dropped_pages"),
        "docling_status": fm.get("docling_status"),
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells-file", help="file with CODE<TAB>QUARTER per line")
    ap.add_argument("--bucket", choices=["A", "B", "C"], help="use census classify() bucket")
    ap.add_argument("--json", default=str(REPO / "kics_disclosure.json"))
    args = ap.parse_args(argv)

    cells: list[tuple[str, str]] = []
    if args.cells_file:
        for line in Path(args.cells_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            code, q = line.split("\t")
            cells.append((code, q))
    elif args.bucket:
        census_mod = _load("_census2935", REPO / "scripts" / "_probes" / "probe_20260903_life2935_census.py")
        import json as _json
        rows = _json.loads(Path(args.json).read_text(encoding="utf-8"))
        cl = census_mod.classify(rows)
        cells = sorted(cl["buckets"][args.bucket], key=lambda kv: (kv[1], kv[0]))
    else:
        print("need --cells-file or --bucket")
        return 2

    sub_mod = _load("_sub3", REPO / "scripts" / "fill_subitems_to_disclosure.py")

    counts = {"EXTRACTABLE_NOW": 0, "LABELS_PRESENT_NO_PARSE": 0, "LABELS_ABSENT": 0, "MD_MISSING": 0}
    for code, q in cells:
        r = triage_cell(sub_mod, code, q)
        counts[r["status"]] += 1
        print(f"{r['code']}\t{r['quarter']}\t{r['status']}\tfound={r.get('found')}\t"
              f"label_hits={r.get('label_hits')}\tspr={r.get('source_page_ranges')}\t"
              f"dropped={r.get('docling_dropped_pages')}")

    print()
    print(f"TRIAGE_SUMMARY {' '.join(f'{k}={v}' for k, v in counts.items())} total={len(cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
