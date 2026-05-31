# -*- coding: utf-8 -*-
"""Download Hana FN IR Databook (Excel 실적 supplement) for FY2023Q1..FY2026Q1.

Download IDs were resolved from the rendered databookDetail.do page by reading each
crossDownload.do Content-Disposition filename (quarter is in the name). One Databook
XLSX per quarter; it breaks out group subsidiaries including 하나생명 and 하나손해보험.

Saves to data/ir/FY{YYYY}_Q{N}/_groups/hana_financial/<orig_filename>.
Run: python scripts/crawl_ir_hana_databook.py
"""
import os, ssl, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
BASE = "https://www.hanafn.com:8002/download/{}/crossDownload.do"
REFERER = "https://www.hanafn.com/ir/financial/databookDetail.do"

# (FY_year, quarter, download_id, expected_filename)  FY = calendar reporting year
# 1Q26 = FY2026 Q1; 4Q25 = FY2025 Q4; etc.
ENTRIES = [
    ("2026", 1, "10075774", "1Q26_HFG_IR_Databook.xlsx"),
    ("2025", 4, "10073253", "4Q25_HFG_IR_Databook.xlsx"),
    ("2025", 3, "10070900", "HFG_IR_Databook_3Q25.xlsx"),
    ("2025", 2, "10070256", "HFG_IR_Databook_2Q25.xlsx"),
    ("2025", 1, "10063426", "HFG_IR_Databook_1Q25.xlsx"),
    ("2024", 4, "10062632", "HFG_IR_Databook_4Q24.xlsx"),
    ("2024", 3, "10061273", "HFG_IR_Databook_3Q24.xlsx"),
    ("2024", 2, "10060528", "HFG_IR_Databook_2Q24.xlsx"),
    ("2024", 1, "10060530", "HFG_IR_Databook_1Q24.xlsx"),
    ("2023", 4, "10060930", "HFG_IR_Databook_4Q23.xlsx"),
    ("2023", 3, "10055354", "HFG_IR_Databook_3Q23.xlsx"),
    ("2023", 2, "10055336", "HFG_IR_Databook_2Q23.xlsx"),
    ("2023", 1, "10050730", "HFG_IR_Databook_1Q23.xlsx"),
]


def fetch(idv):
    url = BASE.format(idv)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": REFERER, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return r.read()


def main():
    log = []
    for yr, q, idv, fn in ENTRIES:
        d = os.path.join(ROOT, "data", "ir", f"FY{yr}_Q{q}", "_groups", "hana_financial")
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, fn)
        try:
            data = fetch(idv)
        except Exception as e:
            log.append(f"FY{yr}_Q{q} {fn}: FAIL {e}")
            continue
        if data[:2] != b"PK" and data[:4] != b"%PDF":
            log.append(f"FY{yr}_Q{q} {fn}: NOT XLSX/PDF (first {data[:8]!r})")
            continue
        with open(dest, "wb") as f:
            f.write(data)
        log.append(f"FY{yr}_Q{q} OK {fn} {len(data)} bytes")
    print("\n".join(log))


if __name__ == "__main__":
    main()
