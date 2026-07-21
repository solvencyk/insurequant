# -*- coding: utf-8 -*-
"""Download Shinhan FG Fact Book (Excel 실적 supplement) FY2023Q1..FY2026Q1.

attachNo values resolved from the rendered factBook archive
(https://shinhangroup.com/kr/ir/finance/factBook). Each Fact Book breaks out
group subsidiaries including 신한라이프 (Shinhan Life). Files download via
/main/downloadAttach?attachNo=...&seq=1.

Saves to data/ir/FY{YYYY}_Q{N}/_groups/shinhan_financial/<filename>.
Run: python scripts/crawl_ir_shinhan_factbook.py
"""
import os, ssl, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://shinhangroup.com/main/downloadAttach?attachNo={}&seq=1"
REFERER = "https://shinhangroup.com/kr/ir/finance/factBook"

# (FY_year, quarter, attachNo). 2026 1Q .. 2023 4Q .. 2023 1Q
ENTRIES = [
    ("2026", 1, "b696b6e7e58a41b2af53a493f3c4ff93"),
    ("2025", 4, "fed7b8d17b1943d881b245ed07773dcc"),
    ("2025", 3, "41b15b1fa46d4578a916aa4f043ac941"),
    ("2025", 2, "a3b4f378e31c43468bcc7159358ac2f2"),
    ("2025", 1, "bfb52b1de6b74386b2ee27e6f3daa847"),
    ("2024", 4, "8c658d6e2c3348f28afa66afec0dcaa8"),
    ("2024", 3, "c497e7db6775473e92dd4409e264da49"),
    ("2024", 2, "3531be6432f94960928682a939395759"),
    ("2024", 1, "0faf225cd70f450085533276249608fd"),
    ("2023", 4, "afd8db9282264d3ab185f3018cceebe1"),
    ("2023", 3, "0a0a329b28df45e28f2f1a705bffc048"),
    ("2023", 2, "b8f6f658defd4f79b44bcacaedcc132b"),
    ("2023", 1, "b7298a2f02c34fe9b88837eb36e069ce"),
]


def fetch(attach):
    url = BASE.format(attach)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return r.read(), r.headers.get("Content-Disposition", "")


def main():
    log = []
    for yr, q, attach in ENTRIES:
        d = os.path.join(ROOT, "data", "ir", f"FY{yr}_Q{q}", "_groups", "shinhan_financial")
        os.makedirs(d, exist_ok=True)
        fn = f"shinhan_factbook_{yr}_{q}Q.xls"
        try:
            data, disp = fetch(attach)
        except Exception as e:
            log.append(f"FY{yr}_Q{q}: FAIL {e}")
            continue
        head = data[:8]
        # .xls (OLE2) starts D0 CF 11 E0; .xlsx starts PK
        if head[:4] == b"\xd0\xcf\x11\xe0":
            ext = ".xls"
        elif head[:2] == b"PK":
            ext = ".xlsx"
        elif head[:4] == b"%PDF":
            ext = ".pdf"
        else:
            log.append(f"FY{yr}_Q{q}: UNKNOWN type first={head!r} disp={disp}")
            continue
        fn = f"shinhan_factbook_{yr}_{q}Q{ext}"
        dest = os.path.join(d, fn)
        with open(dest, "wb") as f:
            f.write(data)
        log.append(f"FY{yr}_Q{q} OK {fn} {len(data)} bytes")
    print("\n".join(log))


if __name__ == "__main__":
    main()
