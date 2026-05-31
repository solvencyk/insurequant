# -*- coding: utf-8 -*-
"""한화손해보험 (KR0002, 000370) IR: download the quarterly 한화손해보험 현황
(경영공시 / IR) PDFs from the static path
  https://www.hwgeneralins.com/upload/download/company/ir/FY{YEAR}-{Q}_4.pdf
where Q = 1..4 (1분기/2분기/3분기/결산). FY2023-1 .. FY2026-1 requested.

The site's SPA blocks Selenium (anti-devtools alert) and main.do is under
maintenance, but these IR PDFs are served as plain static files.
"""
import json
import ssl
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.hwgeneralins.com/upload/download/company/ir/"
STAGE = Path("data/ir/decks/hanwha_gi").resolve()
STAGE.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/124.0 Safari/537.36"}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# requested range FY2023.1Q .. FY2026.1Q (FY = calendar year for Hanwha GI)
TARGETS = []
for y in range(2023, 2027):
    for q in range(1, 5):
        if y == 2026 and q > 1:
            break
        TARGETS.append((y, q))


def q_to_quarter(y, q):
    return f"FY{y}_Q{q}"


def main():
    manifest = []
    for y, q in TARGETS:
        name = f"FY{y}-{q}_4.pdf"
        url = BASE + name
        out = STAGE / f"FY{y}_Q{q}_{name}"
        req = urllib.request.Request(url, headers=HDR)
        try:
            with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
                data = r.read()
        except Exception as e:
            print(f"  MISS {name}: {e}")
            continue
        out.write_bytes(data)
        rec = {"quarter": q_to_quarter(y, q), "kind": "ir_pdf",
               "file": out.name, "url": url, "bytes": len(data)}
        manifest.append(rec)
        print(f"  OK {q_to_quarter(y, q)}  {out.name}  ({len(data)} B)")
    (STAGE / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n== {len(manifest)} files ==")
    got = sorted({r["quarter"] for r in manifest})
    print("quarters:", got)


if __name__ == "__main__":
    main()
