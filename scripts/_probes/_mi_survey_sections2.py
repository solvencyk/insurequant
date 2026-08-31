"""Survey v2: whitespace-normalized header matching for 1-1 / 1-2 / 5-1 (+ broad variants).
Read-only. Writes report to scripts/_probes/_mi_survey_out2_<period>.txt (utf-8 no BOM).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PERIOD = sys.argv[1] if len(sys.argv) > 1 else "FY2026_Q2"
MD_DIR = ROOT / "md_inbox" / PERIOD


def norm(s: str) -> str:
    # collapse all whitespace, keep the rest, for pattern matching only
    return re.sub(r"\s+", "", s)


PATTERNS = {
    "1-1": re.compile(r"^#{1,3}(?:[-□]?)1-1\.?주요경영지표"),
    "1-2": re.compile(r"^#{1,3}(?:[-□]?)1-2\.?주요경영효율지표"),
    "5-1": re.compile(r"^#{1,3}(?:[-□]?)5-1\.?수[의익]성"),
    "sec1_broad": re.compile(r"^#{1,3}(?:[ⅠI1]\.?)주요경영현황요약"),
    "sec1_alt": re.compile(r"^#{1,3}□?주요경영지표$"),
    "sec5_broad": re.compile(r"^#{1,3}(?:[ⅤV5]\.?)수[의익]성$"),
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
counts = {k: 0 for k in PATTERNS}
matrix = []

for fp in files:
    text = fp.read_text(encoding="utf-8")
    fm = frontmatter(text)
    lines = text.splitlines()
    found = {}
    for i, line in enumerate(lines):
        nline = norm(line.strip())
        for key, pat in PATTERNS.items():
            if key in found:
                continue
            if pat.match(nline):
                end = next_header_idx(lines, i)
                found[key] = (i + 1, end, "\n".join(lines[i:min(end, i + 45)]))
    for k in found:
        counts[k] += 1
    matrix.append((fp.stem, fm.get("source_page_ranges", "?"), found))

out.append("\n=== HEADER HIT COUNTS (v2, whitespace-normalized) ===")
for k, v in counts.items():
    out.append(f"{k}: {v}/{len(files)}")

out.append("\n=== MATRIX (company: which keys found) ===")
for stem, pages, found in matrix:
    flags = ",".join(sorted(found.keys())) if found else "NONE"
    out.append(f"{stem} | pages={pages} | {flags}")

out.append("\n=== DETAIL for companies missing BOTH 5-1 and sec5_broad (need manual check) ===")
for stem, pages, found in matrix:
    if "5-1" not in found and "sec5_broad" not in found:
        out.append(f"\n--- {stem} pages={pages} ---")

out.append("\n=== DETAIL for companies missing BOTH 1-1/1-2 and sec1_broad/sec1_alt (need manual check) ===")
for stem, pages, found in matrix:
    if not ({"1-1", "1-2", "sec1_broad", "sec1_alt"} & set(found.keys())):
        out.append(f"\n--- {stem} pages={pages} ---")

out.append("\n=== FULL PER-COMPANY SNIPPETS ===")
for stem, pages, found in matrix:
    flags = ",".join(sorted(found.keys())) if found else "NONE"
    out.append(f"\n--- {stem} pages={pages} found=[{flags}] ---")
    for key in ["1-1", "1-2", "5-1", "sec1_broad", "sec1_alt", "sec5_broad"]:
        if key in found:
            ln, end, snippet = found[key]
            out.append(f"  [{key}] line {ln}:")
            for sl in snippet.splitlines()[:30]:
                out.append(f"    {sl}")

report_path = Path(__file__).parent / f"_mi_survey_out2_{PERIOD}.txt"
report_path.write_text("\n".join(out), encoding="utf-8")
print(f"wrote {report_path} ({len(out)} lines)")
for k, v in counts.items():
    print(f"{k}: {v}/{len(files)}")
