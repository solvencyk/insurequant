# -*- coding: utf-8 -*-
"""For a given company code, load its FY2026_Q2 raw XML and print, for every occurrence of
'후순위', the nearest preceding section/note title and a short flattened snippet -- to classify
which table format (열그룹 / 상세표 / 사채관리계약 / 발행실적-only / BS총액만 / none) actually
carries its subordinated-bond balance in H1 2026."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"


def load(code):
    d = next((p for p in RAW_DIR.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    return xml, (xml.read_text(encoding="utf-8", errors="replace") if xml else None)


def nearest_title(text, pos):
    # look backward for the nearest <TITLE...>...</TITLE> or bolded section-like heading
    back = text[max(0, pos - 6000):pos]
    titles = list(re.finditer(r"<TITLE[^>]*>(.*?)</TITLE>", back, re.DOTALL))
    if titles:
        t = re.sub(r"<[^>]+>", "", titles[-1].group(1)).strip()
        return t[:80]
    return "(no TITLE found within 6000 chars back)"


codes = sys.argv[1:]
for code in codes:
    print(f"===== {code} =====")
    xml_path, text = load(code)
    if text is None:
        print("  NO XML FOUND")
        continue
    flat_positions = []
    for m in re.finditer(r"후순위", text):
        flat_positions.append(m.start())
    # cluster nearby hits (within 200 chars) to avoid repeating the same table cell-by-cell
    clusters = []
    for p in flat_positions:
        if clusters and p - clusters[-1][-1] < 300:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    print(f"  total '후순위' hits={len(flat_positions)}  clusters={len(clusters)}")
    for cl in clusters:
        p = cl[0]
        title = nearest_title(text, p)
        snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", text[p - 30:p + 120]))
        print(f"    @{p} title={title!r}")
        print(f"      snippet={snippet!r}")
    print()
