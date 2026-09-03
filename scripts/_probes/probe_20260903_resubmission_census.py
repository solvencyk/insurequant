# -*- coding: utf-8 -*-
"""Census: which (company, quarter) raw disclosure PDFs show signs of a silent
post-parse replacement (the KR0003 2026.1Q pattern) or an issuer re-submission
bundled in a zip.

Two independent signals, both cheap and repo-wide:
  (A) mtime staleness: raw/*.pdf touched (mtime) meaningfully AFTER its
      matching md_inbox/*.md was generated. This is exactly the KR0003
      signature before today's fix (pdf mtime 2026-09-03, md mtime 2026-06-12).
      A positive here means "the file on disk right now was not the file we
      last parsed" -- it says nothing about WHY (could be a genuine
      re-submission, or just an unparsed backlog item never converted yet --
      distinguished by whether an .md exists at all: no .md = backlog, not
      swap; .md exists but is older = swap, worth checking).
  (B) zip inner-filename signal, for the handful of *.zip archives still on
      disk (most are deleted after extraction -- gitignored data, not a repo
      artifact): flag entries whose issuer-given filename contains 재제출/
      정정/수정, or a zip holding 2+ entries that are BOTH the same document
      type (같은 "경영공시자료" 접두, 감사/검토보고서 동봉은 정상이라 신호 아님).

Read-only. Writes one JSON report to the scratchpad-equivalent location given
by --out (default: stdout summary only).
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DISC = REPO / "data" / "disclosure"
MD_INBOX = REPO / "md_inbox"

_STEM_RE = re.compile(r"^(KR\w+)_(.+?)(?:_amended\d*(?:_amended\d*)*)?$")


def _company_code(stem: str) -> str | None:
    m = re.match(r"^(KR\w+)_", stem)
    return m.group(1) if m else None


def census_mtime_staleness() -> list[dict]:
    out = []
    for period_dir in sorted(DISC.glob("FY*_Q?")):
        period = period_dir.name
        raw_dir = period_dir / "raw"
        if not raw_dir.is_dir():
            continue
        md_dir = MD_INBOX / period
        # index md_inbox by company code -> (path, mtime), keep the NEWEST per code
        md_by_code: dict[str, tuple[Path, float]] = {}
        if md_dir.is_dir():
            for md in md_dir.glob("*.md"):
                code = _company_code(md.stem)
                if not code:
                    continue
                mt = md.stat().st_mtime
                prev = md_by_code.get(code)
                if prev is None or mt > prev[1]:
                    md_by_code[code] = (md, mt)

        for pdf in sorted(raw_dir.glob("*.pdf")):
            code = _company_code(pdf.stem)
            if not code:
                continue
            pdf_mt = pdf.stat().st_mtime
            entry = md_by_code.get(code)
            if entry is None:
                out.append({
                    "period": period, "code": code, "pdf": pdf.name,
                    "status": "NO_MD_YET",
                })
                continue
            md_path, md_mt = entry
            delta_h = (pdf_mt - md_mt) / 3600.0
            if delta_h > 1.0:  # pdf touched >1h after the md we have on file
                out.append({
                    "period": period, "code": code, "pdf": pdf.name,
                    "md": md_path.name, "status": "PDF_NEWER_THAN_MD",
                    "delta_hours": round(delta_h, 1),
                    "pdf_mtime": pdf_mt, "md_mtime": md_mt,
                })
    return out


_REISSUE_MARKERS = ("재제출", "정정", "수정", "재공시", "재발송")


def census_zip_inner_names() -> list[dict]:
    out = []
    for zpath in sorted(DISC.glob("*/raw/*.zip")):
        try:
            with zipfile.ZipFile(zpath) as z:
                names = z.namelist()
                infos = z.infolist()
        except Exception as e:
            out.append({"zip": str(zpath.relative_to(REPO)), "error": str(e)})
            continue
        flagged_names = [n for n in names if any(m in n for m in _REISSUE_MARKERS)]
        pdf_entries = [i for i in infos if i.filename.lower().endswith(".pdf")]
        out.append({
            "zip": str(zpath.relative_to(REPO)),
            "n_entries": len(names),
            "entries": [
                {"name": i.filename, "size": i.file_size, "date_time": list(i.date_time)}
                for i in infos
            ],
            "reissue_marker_hits": flagged_names,
        })
    return out


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    stale = census_mtime_staleness()
    newer = [r for r in stale if r["status"] == "PDF_NEWER_THAN_MD"]
    no_md = [r for r in stale if r["status"] == "NO_MD_YET"]

    print(f"=== mtime staleness census ===")
    print(f"  raw pdf newer than its md_inbox .md by >1h: {len(newer)}")
    for r in sorted(newer, key=lambda x: -x["delta_hours"]):
        print(f"    {r['period']} {r['code']}: pdf newer by {r['delta_hours']}h  ({r['pdf']} vs {r['md']})")
    print(f"  pdf with no corresponding md_inbox .md at all (backlog, not swap): {len(no_md)}")
    for r in no_md:
        print(f"    {r['period']} {r['code']}: {r['pdf']}")

    print()
    print("=== zip inner-filename census (zips still on disk) ===")
    zips = census_zip_inner_names()
    for z in zips:
        if "error" in z:
            print(f"  {z['zip']}: UNREADABLE {z['error']}")
            continue
        print(f"  {z['zip']}  ({z['n_entries']} entries)")
        for e in z["entries"]:
            hit = " <-- REISSUE MARKER" if any(m in e["name"] for m in _REISSUE_MARKERS) else ""
            print(f"      {e['name']}  size={e['size']}  date={e['date_time']}{hit}")

    out_path = REPO / "scripts" / "_probes" / "_out_20260903_resubmission_census.json"
    out_path.write_text(json.dumps({
        "mtime_staleness": stale,
        "zip_inner_names": zips,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nfull report written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
