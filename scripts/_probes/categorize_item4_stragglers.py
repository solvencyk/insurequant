"""For each of the 43 unmatched item4-tautology stragglers, find the actual
md_inbox file (handling name variants) and search for the item4 row text,
printing whatever's found so a human can eyeball raw values in one pass.
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
MD_INBOX = REPO / "md_inbox"

IMAGE_OCR_COMPANIES = {"KR0010", "KR0079"}

STRAGGLERS = [
    ("KR0051", "2023.1Q"), ("KR0071", "2023.1Q"), ("KR0001", "2023.2Q"),
    ("KR0032", "2023.2Q"), ("KR0074", "2023.2Q"), ("KR0032", "2023.3Q"),
    ("KR0051", "2023.3Q"), ("KR0010", "2023.4Q"), ("KR0051", "2023.4Q"),
    ("KR0079", "2023.4Q"), ("KR0010", "2024.1Q"), ("KR0010", "2024.2Q"),
    ("KR0010", "2024.3Q"), ("KR0049", "2024.3Q"), ("KR0005", "2024.4Q"),
    ("KR0010", "2024.4Q"), ("KR0051", "2024.4Q"), ("KR0069", "2024.4Q"),
    ("KR0071", "2024.4Q"), ("KR0079", "2024.4Q"), ("KR0087", "2024.4Q"),
    ("KR0010", "2025.1Q"), ("KR0049", "2025.1Q"), ("KR0079", "2025.1Q"),
    ("KR0010", "2025.2Q"), ("KR0079", "2025.2Q"), ("KR0010", "2025.3Q"),
    ("KR0079", "2025.3Q"), ("KR0010", "2025.4Q"), ("KR0079", "2025.4Q"),
    ("KR0010", "2026.1Q"), ("KR0049", "2026.1Q"), ("KR0079", "2023.3Q"),
    ("KR0079", "2024.2Q"), ("KR0079", "2024.3Q"), ("KR0080", "2023.2Q"),
    ("KR0080", "2024.4Q"), ("KR0080", "2025.1Q"), ("KR0080", "2025.2Q"),
    ("KR0080", "2026.1Q"), ("KR0087", "2026.1Q"), ("KR1098", "2023.4Q"),
    ("KR0087", "2023.2Q"),
]


def _md_period_to_quarter(period):
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def main():
    md_files_by_code_q = {}
    for period_dir in sorted(MD_INBOX.glob("FY*_Q?")):
        if not period_dir.is_dir():
            continue
        q = _md_period_to_quarter(period_dir.name)
        for md_path in sorted(period_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            md_files_by_code_q.setdefault((code, q), []).append(md_path)

    for code, q in STRAGGLERS:
        tag = "IMAGE_OCR" if code in IMAGE_OCR_COMPANIES else ""
        paths = md_files_by_code_q.get((code, q), [])
        if not paths:
            print(f"{code} {q} [{tag}] NO_MD_FILE_AT_ALL")
            continue
        for p in paths:
            text = p.read_text(encoding="utf-8")
            # find lines containing 순자산 near a Roman-numeral I or "1+2+3"
            hits = []
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "순자산" in line and ("건전성감독기준" in line or "1+2+3" in line):
                    hits.append((i, line.strip()))
                    # grab the next line too in case value wraps
                    if i + 1 < len(lines):
                        hits.append((i + 1, lines[i + 1].strip()))
            print(f"{code} {q} [{tag}] file={p.name} hits={len(hits)}")
            for ln, txt in hits[:6]:
                print(f"    L{ln}: {txt}")


if __name__ == "__main__":
    main()
