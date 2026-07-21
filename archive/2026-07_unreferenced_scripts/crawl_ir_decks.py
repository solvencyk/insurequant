# -*- coding: utf-8 -*-
"""Download quarterly IR earnings decks for 현대해상 (Hyundai Marine) and
DB손해보험 (DB Insurance). Saves raw PDFs under data/ir/decks/<slug>/.

Approach:
- DB: each IR list entry links to an .shtm detail page; the detail page HTML
  (EUC-KR-ish, with stray bytes) contains an <a href="/pcweb/.../__etc/<name>.pdf">.
  We read raw bytes, locate the href byte-range, and URL-quote those exact bytes
  so the Korean filename downloads correctly regardless of decode issues.
- Hyundai: hi.co.kr IR pages are JS-rendered; we rely on known direct PDF URLs
  (alphasquare mirror + hi.co.kr file endpoints discovered via search) passed in.

Run: python scripts/crawl_ir_decks.py
"""
import ssl
import os
import re
import sys
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch_bytes(url, referer=None):
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
        return r.read()


def save(slug, filename, data):
    d = os.path.join(ROOT, "data", "ir", "decks", slug)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, filename)
    with open(p, "wb") as f:
        f.write(data)
    return p, len(data)


def db_pdf_paths_from_detail(detail_url):
    """Return list of (raw_href_bytes,) absolute PDF URLs from a DB .shtm page."""
    raw = fetch_bytes(detail_url)
    out = []
    # match href="...pdf" capturing raw bytes between quotes
    for m in re.finditer(rb'href="([^"]+?\.pdf)"', raw):
        href = m.group(1)
        out.append(href)
    return out


def quote_path_bytes(path_bytes):
    """Percent-encode a raw path (bytes) keeping /._- and existing structure."""
    # split on b'/' to keep slashes, quote each segment's bytes
    parts = path_bytes.split(b"/")
    qparts = [urllib.parse.quote(p, safe="._-()") for p in parts]
    return "/".join(qparts)


def main():
    log = []

    # ---- DB Insurance ----
    db_base = "https://www.idbins.com"
    # (label, detail .shtm path) — from IR report list 2023.3Q..2026.1Q
    db_entries = [
        ("2026.1Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_260514.shtm"),
        ("2026.1Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_260514(1).shtm"),
        ("2025.4Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_69.shtm"),
        ("2025_results_2026_outlook", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_68.shtm"),
        ("2025.3Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_67.shtm"),
        ("2025.3Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_66.shtm"),
        ("2025.2Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_65(1).shtm"),
        ("2025.2Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_65.shtm"),
        ("2025.1Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_64.shtm"),
        ("2025.1Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_61(2).shtm"),
        ("2024.4Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_62.shtm"),
        ("2024_results_2025_outlook", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_61(1).shtm"),
        ("2024.3Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_59.shtm"),
        ("2024.3Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_60.shtm"),
        ("2024.2Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_57.shtm"),
        ("2024.2Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_58.shtm"),
        ("2024.1Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_55.shtm"),
        ("2024.1Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_202405.shtm"),
        ("2023.4Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_53(1).shtm"),
        ("2023_results_2024_outlook", "/pc/bizxpress/cmy/inv/ir/FMCOMV1487_54(1).shtm"),
        ("2023.3Q_factsheet", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_52.shtm"),
        ("2023.3Q_IR", "/pc/bizxpress/cmy/inv/ir/FWCOMV1705_51.shtm"),
    ]

    for label, path in db_entries:
        detail = db_base + path
        try:
            hrefs = db_pdf_paths_from_detail(detail)
        except Exception as e:
            log.append(f"DB {label}: DETAIL FAIL {e}")
            continue
        if not hrefs:
            log.append(f"DB {label}: no pdf href on {path}")
            continue
        # prefer the first (Korean) pdf
        got = False
        for idx, href in enumerate(hrefs):
            qpath = quote_path_bytes(href)
            pdf_url = db_base + qpath if href.startswith(b"/") else db_base + "/" + qpath
            try:
                data = fetch_bytes(pdf_url, referer=detail)
            except Exception as e:
                log.append(f"DB {label}[{idx}]: DL FAIL {e} :: {pdf_url[:120]}")
                continue
            if not data[:4] == b"%PDF":
                log.append(f"DB {label}[{idx}]: NOT PDF (first bytes {data[:8]!r})")
                continue
            suffix = "" if idx == 0 else f"_{idx}"
            fn = f"db_{label}{suffix}.pdf"
            p, n = save("db_insurance", fn, data)
            log.append(f"DB OK  {fn}  {n} bytes")
            got = True
            break
        if not got:
            log.append(f"DB {label}: all hrefs failed")

    # ---- Hyundai Marine ----
    # Known direct PDF URLs (alphasquare mirror of hi.co.kr IR decks).
    hy_entries = []  # filled by caller / second pass

    print("\n".join(log))


if __name__ == "__main__":
    main()
