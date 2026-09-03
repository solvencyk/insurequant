# -*- coding: utf-8 -*-
"""For each mtime-flagged (period, code) candidate from
probe_20260903_resubmission_census.py, compare the md_inbox file's recorded
source_sha256 (docling front matter) against the CURRENT raw pdf's actual
sha256. Mismatch = genuine content drift (pdf changed after this md was
generated -- the KR0003 signature). Match = mtime-only noise (pdf touched,
content identical -- e.g. re-download of the same bytes, filesystem restore).
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DISC = REPO / "data" / "disclosure"
MD_INBOX = REPO / "md_inbox"


def sha256_of(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest()


def read_frontmatter(md_path: Path) -> dict:
    if not md_path.exists():
        return {}
    with md_path.open("r", encoding="utf-8") as fp:
        first = fp.readline()
        if first.strip() != "---":
            return {}
        buf = []
        for line in fp:
            if line.strip() == "---":
                break
            buf.append(line)
    meta = {}
    for raw in buf:
        if ":" not in raw:
            continue
        k, _, v = raw.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    return meta


CANDIDATES = [
    ("FY2024_Q4", "KR0005", "KR0005_흥국화재.pdf", "KR0005_흥국화재.md"),
    ("FY2026_Q1", "KR0079", "KR0079_미래에셋생명.pdf", "KR0079_미래에셋생명보험.md"),
    ("FY2023_Q4", "KR0080", "KR0080_에이아이에이생명보험.pdf", "KR0080_에이아이에이생명보험.md"),
    ("FY2024_Q4", "KR0080", "KR0080_에이아이에이생명보험.pdf", "KR0080_에이아이에이생명보험.md"),
    ("FY2023_Q1", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2023_Q2", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2023_Q3", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2023_Q4", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2024_Q1", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2024_Q2", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2024_Q3", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2024_Q4", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2025_Q1", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2025_Q2", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2025_Q3", "KR1011", "KR1011_IBK연금보험.pdf", "KR1011_IBK연금보험.md"),
    ("FY2026_Q2", "KR0095", "KR0095_메트라이프생명보험.pdf", "KR0095_메트라이프생명보험.md"),
    ("FY2026_Q2", "KR0010", "KR0010_KB손해보험.pdf", "KR0010_KB손해보험.md"),
]


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    results = []
    for period, code, pdf_name, md_name in CANDIDATES:
        pdf_path = DISC / period / "raw" / pdf_name
        md_path = MD_INBOX / period / md_name
        if not pdf_path.exists():
            results.append({"period": period, "code": code, "status": "PDF_MISSING"})
            continue
        fm = read_frontmatter(md_path)
        recorded_sha = fm.get("source_sha256", "")
        recorded_size = fm.get("source_size", "")
        actual_sha = sha256_of(pdf_path)
        actual_size = str(pdf_path.stat().st_size)
        drift = bool(recorded_sha) and recorded_sha != actual_sha
        results.append({
            "period": period, "code": code,
            "recorded_sha256": recorded_sha, "actual_sha256": actual_sha,
            "recorded_size": recorded_size, "actual_size": actual_size,
            "has_frontmatter": bool(fm),
            "status": "CONTENT_DRIFT" if drift else ("NO_FRONTMATTER" if not fm else "NO_DRIFT_MTIME_NOISE"),
        })

    for r in results:
        print(f"{r['period']} {r['code']}: {r['status']}"
              + (f"  size {r.get('recorded_size')} -> {r.get('actual_size')}" if r.get("status") == "CONTENT_DRIFT" else ""))

    out_path = Path(__file__).with_name("_out_20260903_fingerprint_check.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {out_path}")
    n_drift = sum(1 for r in results if r["status"] == "CONTENT_DRIFT")
    print(f"\nTOTAL genuine content drift: {n_drift} / {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
