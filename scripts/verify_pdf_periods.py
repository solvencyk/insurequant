"""Verify that each PDF in data/disclosure/<period>/pdf/ actually corresponds
to that period.

For every PDF we open the first ~3 pages, hunt for explicit period markers
(예: "2024년 제2분기", "2024.2Q", "2024년 6월 말 기준"), normalise them into
``FYYYYY_QN`` and compare against the parent period folder. Mismatches are
either reported (default) or moved to ``data/disclosure/_to_be/<detected>/``
when --apply is passed.

Usage:
    python scripts/verify_pdf_periods.py            # dry run, prints report
    python scripts/verify_pdf_periods.py --apply    # actually move mismatches
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\solvency\data\disclosure")
TO_BE_ROOT = ROOT / "_to_be"

PERIOD_FOLDER_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")

# 분기-끝 월/일을 분기로 매핑 (3월말=Q1, 6월말=Q2, 9월말=Q3, 12월말=Q4)
QUARTER_END = {
    (3, 31): 1,
    (6, 30): 2,
    (9, 30): 3,
    (12, 31): 4,
}

# Title-page patterns - high confidence, used to take FIRST hit on page 1.
# Spaces inside digits ("2 0 2 4") are tolerated by pre-collapsing whitespace
# between digits before matching.
TITLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # "2024년 2/4분기" / "2024년 제2/4분기"
    ("y/q", re.compile(r"(20\d{2})\s*년도?\s*(?:제\s*)?([1-4])\s*/\s*4\s*분\s*기")),
    # "2024년 제2분기" / "2024년 2분기"
    ("yqQ", re.compile(r"(20\d{2})\s*년도?\s*(?:제\s*)?([1-4])\s*분\s*기")),
    # "2024.2Q"
    ("y.qQ", re.compile(r"(20\d{2})\s*[.\-]\s*([1-4])\s*Q", re.IGNORECASE)),
    # "FY2024 Q2"
    ("FYyQ", re.compile(r"FY\s*(20\d{2})\s*[.\-_ ]?\s*Q\s*([1-4])", re.IGNORECASE)),
    # "2024년 6월 말" / "2024년 6월말"
    ("ymonth_end", re.compile(r"(20\d{2})\s*년\s*(3|6|9|12)\s*월\s*말")),
    # "기간 : 2024.1.1 - 2024.6.30" - take the END date
    (
        "period_end",
        re.compile(
            r"기\s*간\s*[:：].{0,40}?(20\d{2})\s*[.\-/]\s*(0?[369]|12)\s*[.\-/]\s*(30|31)"
        ),
    ),
    # "(2024.6.30 기준)" / "2024.6.30 현재"
    (
        "ymd_basis",
        re.compile(
            r"(20\d{2})\s*[.\-/]\s*(0?[369]|12)\s*[.\-/]\s*(30|31)\s*\.?\s*"
            r"(?:기\s*준|현\s*재)"
        ),
    ),
    # "2023년 ... 기간 : 2023.1.1-2023.12.31"  (annual disclosure -> Q4)
    ("annual_period", re.compile(r"기\s*간\s*[:：].{0,40}?(20\d{2})\s*[.\-/]\s*1\s*[.\-/]\s*1\s*[.\-/\- ]+\s*(20\d{2})\s*[.\-/]\s*12\s*[.\-/]\s*31")),
    # "2024년 상반기" / "2024년 하반기"
    ("y_half", re.compile(r"(20\d{2})\s*년도?\s*(상|하)반\s*기")),
    # "2024년 6월 30일" / "2024년 6월말"  (Korean date)
    ("ymd_kor", re.compile(r"(20\d{2})\s*년\s*(3|6|9|12)\s*월\s*(?:말|(?:30|31)\s*일)")),
    # "2024년 1월 1일 ~ 2024년 6월 30일"  (Korean period range)
    (
        "kor_period_range",
        re.compile(
            r"(20\d{2})\s*년\s*1\s*월\s*1\s*일\s*[~∼\-]\s*(20\d{2})\s*년\s*"
            r"(3|6|9|12)\s*월\s*(?:30|31)\s*일"
        ),
    ),
]


def _dedup_runs(s: str) -> str:
    """Collapse runs of 2 identical chars (used as fallback for PDFs that
    extract every glyph twice, e.g. some 한화생명 cover pages).

    Only collapses pairs, not 3+ runs, to minimise damage to legitimate
    Korean syllables that happen to repeat (e.g. '이이').
    """
    out: list[str] = []
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i] == s[i + 1]:
            out.append(s[i])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _collapse_digit_spaces(s: str) -> str:
    """Turn '2 0 2 4 년 2 /4 분 기' into '2024 년 2/4 분 기' so regex hits."""
    # collapse spaces between two digits, repeatedly
    prev = None
    cur = s
    while prev != cur:
        prev = cur
        cur = re.sub(r"(\d)\s+(\d)", r"\1\2", cur)
    # also collapse spaces inside common particles
    cur = re.sub(r"(\d)\s+(/)\s*(\d)", r"\1\2\3", cur)
    return cur


def _interpret(tag: str, m: re.Match[str]) -> tuple[int, int] | None:
    if tag in ("y/q", "yqQ", "y.qQ", "FYyQ"):
        year = int(m.group(1))
        q = int(m.group(2))
    elif tag == "ymonth_end":
        year = int(m.group(1))
        month = int(m.group(2))
        q = {3: 1, 6: 2, 9: 3, 12: 4}[month]
    elif tag in ("period_end", "ymd_basis"):
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        qmap = QUARTER_END.get((month, day))
        if qmap is None:
            return None
        q = qmap
    elif tag == "annual_period":
        # 1.1 - 12.31 -> Q4 of the END year
        year = int(m.group(2))
        q = 4
    elif tag == "y_half":
        year = int(m.group(1))
        q = 2 if m.group(2) == "상" else 4
    elif tag == "ymd_kor":
        year = int(m.group(1))
        month = int(m.group(2))
        q = {3: 1, 6: 2, 9: 3, 12: 4}[month]
    elif tag == "kor_period_range":
        year = int(m.group(2))
        month = int(m.group(3))
        q = {3: 1, 6: 2, 9: 3, 12: 4}[month]
    else:
        return None
    if year < 2020 or year > 2030:
        return None
    if not 1 <= q <= 4:
        return None
    return year, q


def detect_period(pdf_path: Path) -> tuple[str | None, str]:
    """Return (canonical_period or None, debug_reason).

    Strategy:
      1. Read page 1, normalise whitespace between digits, then take the
         EARLIEST high-confidence title hit (cover-page title).
      2. If page 1 yields nothing, scan pages 2-4 the same way and use the
         earliest hit there.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = min(len(pdf.pages), 8)
            pages = [pdf.pages[i].extract_text() or "" for i in range(num_pages)]
    except Exception as exc:
        return None, f"open_error:{exc.__class__.__name__}"

    if not any(p.strip() for p in pages):
        return None, "no_text(image_only?)"

    # Pass 1: try each page with normal text.
    # Pass 2: if nothing, try each page with duplicate-char collapsing
    #         (handles PDFs that extract every glyph twice).
    for variant, transform in (("plain", lambda s: s), ("dedup", _dedup_runs)):
        for page_idx, raw in enumerate(pages):
            if not raw.strip():
                continue
            text = _collapse_digit_spaces(transform(raw))
            candidates: list[tuple[int, str, tuple[int, int]]] = []
            for tag, pat in TITLE_PATTERNS:
                for m in pat.finditer(text):
                    interp = _interpret(tag, m)
                    if interp is None:
                        continue
                    candidates.append((m.start(), tag, interp))
            if not candidates:
                continue
            candidates.sort(key=lambda x: x[0])
            pos, tag, (year, q) = candidates[0]
            sample = [f"{t}:{y}Q{qq}@{p}" for p, t, (y, qq) in candidates[:6]]
            return (
                f"FY{year}_Q{q}",
                f"{variant}/page{page_idx + 1} first={tag}->{year}Q{q}; cands={sample}",
            )

    return None, "no_period_marker"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="move mismatches to _to_be/")
    ap.add_argument("--only", help="restrict to a single period folder, e.g. FY2024_Q2")
    args = ap.parse_args()

    pdfs: list[Path] = []
    for period_dir in sorted(ROOT.iterdir()):
        if not period_dir.is_dir():
            continue
        if not PERIOD_FOLDER_RE.match(period_dir.name):
            continue
        if args.only and period_dir.name != args.only:
            continue
        pdf_dir = period_dir / "pdf"
        if not pdf_dir.exists():
            continue
        pdfs.extend(sorted(pdf_dir.glob("*.pdf")))

    print(f"Scanning {len(pdfs)} PDFs ...", flush=True)

    matches: list[tuple[Path, str, str]] = []
    mismatches: list[tuple[Path, str, str, str]] = []  # (path, folder, detected, reason)
    unknown: list[tuple[Path, str, str]] = []

    for i, pdf in enumerate(pdfs, 1):
        folder = pdf.parent.parent.name  # FYYYYY_QN
        detected, reason = detect_period(pdf)
        rel = pdf.relative_to(ROOT)
        if detected is None:
            unknown.append((pdf, folder, reason))
            tag = "?"
        elif detected == folder:
            matches.append((pdf, folder, detected))
            tag = "OK"
        else:
            mismatches.append((pdf, folder, detected, reason))
            tag = "MISMATCH"
        print(f"  [{i:3d}/{len(pdfs)}] {tag:8s} {rel}  -> {detected or '?'}", flush=True)

    print()
    print("=" * 60)
    print(f"OK:        {len(matches)}")
    print(f"MISMATCH:  {len(mismatches)}")
    print(f"UNKNOWN:   {len(unknown)}")
    print("=" * 60)

    if mismatches:
        print("\nMISMATCHES:")
        for path, folder, detected, reason in mismatches:
            print(f"  {path.relative_to(ROOT)}")
            print(f"     folder={folder}  detected={detected}")
            print(f"     reason={reason}")

    if unknown:
        print("\nUNKNOWN (no period marker / image-only / open_error):")
        for path, folder, reason in unknown:
            print(f"  {path.relative_to(ROOT)}  [{reason}]")

    if args.apply and mismatches:
        print("\nApplying moves ...")
        TO_BE_ROOT.mkdir(parents=True, exist_ok=True)
        skipped_lowconf: list[tuple[Path, str, str, str]] = []
        for path, folder, detected, reason in list(mismatches):
            # Confidence filter: only auto-move when the hit was on page 1-3
            # OR multiple candidates corroborate. Single page-4+ hits are
            # almost always forward-looking dates in later sections.
            page_match = re.search(r"page(\d+)", reason)
            page_num = int(page_match.group(1)) if page_match else 99
            cand_count = reason.count(":") - reason.count("first=")  # rough
            if page_num >= 4 and cand_count <= 2:
                skipped_lowconf.append((path, folder, detected, reason))
                mismatches.remove((path, folder, detected, reason))
        if skipped_lowconf:
            print("\nSKIPPED low-confidence mismatches (please review manually):")
            for path, folder, detected, reason in skipped_lowconf:
                print(f"  {path.relative_to(ROOT)}  folder={folder} detected={detected}")
                print(f"     {reason}")
            print()
        for path, folder, detected, _ in mismatches:
            target_dir = TO_BE_ROOT / detected / "pdf"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / path.name
            if target.exists():
                # Don't overwrite - rename with __dup suffix.
                stem, suf = target.stem, target.suffix
                k = 2
                while (target_dir / f"{stem}__dup{k}{suf}").exists():
                    k += 1
                target = target_dir / f"{stem}__dup{k}{suf}"
            print(f"  mv {path.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
            shutil.move(str(path), str(target))
        print(f"Moved {len(mismatches)} files into {TO_BE_ROOT}.")
    elif mismatches and not args.apply:
        print("\n(dry run; rerun with --apply to actually move files)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
