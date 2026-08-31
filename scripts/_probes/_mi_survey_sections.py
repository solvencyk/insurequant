"""Survey md_inbox MD files for section 1-1 / 1-2 / 5-1 presence + row labels.
Read-only. Writes a report to scripts/_probes/_mi_survey_out.txt (utf-8, no BOM).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "FY2026_Q2"
MD_DIR = ROOT / "md_inbox" / PERIOD

# candidate header patterns (regex, case-sens korean)
HEADERS = {
    "1-1": re.compile(r"^#{1,3}\s*(?:[-□]\s*)?1-1\.?\s{0,2}주요\s*경영\s*지표"),
    "1-2": re.compile(r"^#{1,3}\s*(?:[-□]\s*)?1-2\.?\s{0,2}주요\s*경영\s*효율\s*지표"),
    "5-1": re.compile(r"^#{1,3}\s*(?:[-□]\s*)?5-1\.?\s{0,2}수[의익]성"),
    # fallback broader headers that might house these without the numeric prefix
    "sec1_broad": re.compile(r"^#{1,3}\s*(?:[ⅠI]\.?|1\.)\s*주요\s*경영\s*현황\s*요약"),
    "sec1_alt": re.compile(r"^#{1,3}\s*□?\s*주요\s*경영지표"),
    "sec5_broad": re.compile(r"^#{1,3}\s*(?:[ⅤV]\.?|5\.)\s*수[의익]성"),
}

def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    d = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                d[k.strip()] = v.strip().strip('"')
    return d

def next_header_idx(lines, start):
    for i in range(start + 1, len(lines)):
        if re.match(r"^#{1,3}\s", lines[i]):
            return i
    return len(lines)

out = []
files = sorted(MD_DIR.glob("*.md"))
out.append(f"PERIOD={PERIOD} files={len(files)}")
counts = {k: 0 for k in HEADERS}
company_rows = []

for fp in files:
    text = fp.read_text(encoding="utf-8")
    fm = frontmatter(text)
    lines = text.splitlines()
    found = {}
    for i, line in enumerate(lines):
        for key, pat in HEADERS.items():
            if key in found:
                continue
            if pat.match(line.strip()):
                end = next_header_idx(lines, i)
                found[key] = (i + 1, end, "\n".join(lines[i:min(end, i + 40)]))
    for k in found:
        counts[k] += 1
    company_rows.append((fp.stem, fm.get("source_page_ranges", "?"), found))

out.append("\n=== HEADER HIT COUNTS ===")
for k, v in counts.items():
    out.append(f"{k}: {v}/{len(files)}")

out.append("\n=== PER-COMPANY DETAIL ===")
for stem, pages, found in company_rows:
    flags = "|".join(sorted(found.keys())) if found else "NONE"
    out.append(f"\n--- {stem} pages={pages} found=[{flags}] ---")
    for key in ["1-1", "1-2", "5-1", "sec1_broad", "sec1_alt", "sec5_broad"]:
        if key in found:
            ln, end, snippet = found[key]
            out.append(f"  [{key}] line {ln}:")
            for sl in snippet.splitlines()[:25]:
                out.append(f"    {sl}")

report_path = Path(__file__).parent / f"_mi_survey_out_{PERIOD}.txt"
report_path.write_text("\n".join(out), encoding="utf-8")
print(f"wrote {report_path} ({len(out)} lines)")
print("\n".join(out[: len(HEADERS) + 5]))
