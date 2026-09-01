# -*- coding: utf-8 -*-
"""Search for specific anchor keywords (사채관리, 채무증권 발행실적, 이행상황보고서, 신종자본증권)
and print position + a wider flattened snippet, for classifying table format per company."""
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


KEYWORDS = ["사채관리", "채무증권 발행실적", "이행상황보고서", "신종자본증권", "차입금"]

code = sys.argv[1]
before, after = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (60, 300)
kw_filter = sys.argv[4] if len(sys.argv) > 4 else None
xml_path, text = load(code)
print(f"===== {code}  file={xml_path} =====")
if text is None:
    print("NO XML")
    sys.exit(0)
for kw in (KEYWORDS if not kw_filter else [kw_filter]):
    hits = [m.start() for m in re.finditer(re.escape(kw), text)]
    print(f"--- '{kw}': {len(hits)} hits ---")
    # cluster
    clusters = []
    for p in hits:
        if clusters and p - clusters[-1][-1] < 500:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    for cl in clusters:
        p = cl[0]
        snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", text[max(0, p - before):p + after]))
        print(f"  @{p} (x{len(cl)}) {snippet!r}")
