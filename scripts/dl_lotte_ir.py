# -*- coding: utf-8 -*-
"""Download 롯데손해보험 (KR0003) quarterly IR materials FY2023.1Q~FY2026.1Q from
the 실적발표자료 board, organize into data/ir/FY{YYYY}_Q{N}/KR0003_롯데손해보험/.

Row->quarter map is taken directly from the rendered board (verified by probe).
Direct /upload/ links download via urllib (CERT_NONE for redirect/cert quirks).
Annual->Q4, 반기->Q2, 3분기->Q3, 1분기->Q1.
"""
import os, ssl, sys, urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://www.lotteins.co.kr'
KR_DIR = 'KR0003_롯데손해보험'
LIST_URL = BASE + '/web/C/D/H/cdh_ir_board04_list_6.jsp'

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# (FY year, quarter, board title, upload url, saved filename)
ITEMS = [
    (2023, 1, '2023년 1분기 실적 현황',  '/upload/C/board/2023/05/9/2023_1Q.pdf',                              'lotte_2023_1Q.pdf'),
    (2023, 2, '2023년 반기 factsheet',    '/upload/C/board/2023/08/14/2Qfactsheet.xlsx',                        'lotte_2023_2Q_factsheet.xlsx'),
    (2023, 3, '2023년 3분기 factsheet',   '/upload/C/board/2023/11/16/3Qfactsheet.xlsx',                        'lotte_2023_3Q_factsheet.xlsx'),
    (2023, 4, '2023년 4분기 factsheet',   '/upload/C/board/2024/02/14/lotteins_2023_4Q_factsheet.xlsx',         'lotte_2023_4Q_factsheet.xlsx'),
    (2024, 1, '2024년 1분기 factsheet',   '/upload/C/board/2024/05/16/2024_1Q_factsheet_vf.xlsx',               'lotte_2024_1Q_factsheet.xlsx'),
    (2024, 2, '2024년 반기 factsheet',    '/upload/C/board/2024/08/14/17236274400942024_1H.xls',               'lotte_2024_2Q_factsheet.xls'),
    (2024, 3, '2024년 3분기 factsheet',   '/upload/C/board/2024/11/14/17315746379862024_3Q_factsheet.xls',     'lotte_2024_3Q_factsheet.xls'),
    (2024, 4, '2024년 4분기 factsheet',   '/upload/C/board/2025/02/21/2024_4Q_factsheet_vf.xls',               'lotte_2024_4Q_factsheet.xls'),
    (2025, 1, '2025년 1분기 Factsheet',   '/upload/C/board/2025/08/21/2025_1Q_factsheet.xls',                  'lotte_2025_1Q_factsheet.xls'),
    (2025, 2, '2025년 2분기 Factsheet',   '/upload/C/board/2025/08/21/2025_2Q_factsheet.xls',                  'lotte_2025_2Q_factsheet.xls'),
    (2025, 3, '2025년 3분기 factsheet',   '/upload/C/board/2025/11/17/2025_3Q_factsheet.xls',                  'lotte_2025_3Q_factsheet.xls'),
    (2025, 4, '2025년 4분기 factsheet',   '/upload/C/board/2026/02/13/17709448612262025_4Q_factsheet.xls',     'lotte_2025_4Q_factsheet.xls'),
    (2026, 1, '2026년 1분기 factsheet',   '/upload/C/board/2026/05/15/2026_1Q_factsheet.xls',                  'lotte_2026_1Q_factsheet.xls'),
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*',
                                               'Referer': LIST_URL})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return r.read()


def main():
    for yr, q, title, path, fname in ITEMS:
        dest_dir = ROOT / 'data' / 'ir' / f'FY{yr}_Q{q}' / KR_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fname
        try:
            data = fetch(BASE + path)
        except Exception as e:
            print(f'FAIL FY{yr}_Q{q} {title}: {e}')
            continue
        # sanity: HTML error page would be tiny + start with '<'
        head = data[:64].lstrip()
        if head[:1] == b'<' and len(data) < 4000:
            print(f'WARN FY{yr}_Q{q} {title}: looks like HTML ({len(data)}b), skipping')
            continue
        dest.write_bytes(data)
        print(f'OK  FY{yr}_Q{q}  {dest.relative_to(ROOT)}  {len(data)} bytes  | {title}')


if __name__ == '__main__':
    main()
