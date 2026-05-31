# -*- coding: utf-8 -*-
"""Build data/ir/series/KR0003_롯데손해보험.json from the downloaded Lotte
factsheets.

Lotte (손해보험) factsheets disclose 신계약 CSM (amount, 백만원) and
신계약(월납환산) (APE proxy, 백만원) but DO NOT disclose a 신계약 CSM 배수.
So `multiple_disclosed` is null for every quarter; we additionally compute a
derived ratio (신계약 CSM ÷ 신계약 월납환산) and clearly label it as derived.

For each quarter we read that quarter's OWN factsheet, current-FY block:
  row '신계약 CSM'      -> 신계약 CSM (백만원)  [period column]
  row ' - 신계약 (월납환산)' -> APE (백만원)     [period column]
Column layout (xls/xlsx, 0-based): c4..c8 = current FY 1Q,2Q,3Q,4Q,연간.
2023 factsheets use a different (월별) layout, handled separately/skipped for
amounts where absent.

Fiscal year = calendar year for Lotte. Period key 'YYYY.NQ'.
"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
import xlrd, openpyxl

ROOT = Path(__file__).resolve().parent.parent
KR = 'KR0003_롯데손해보험'
SER = ROOT / 'data' / 'ir' / 'series'

# (period, FY-dir, filename, quarter-column-index 0-based for that quarter's own FY block)
# current-FY block columns: c4=1Q c5=2Q c6=3Q c7=4Q c8=연간
QCOL = {1: 4, 2: 5, 3: 6, 4: 7}

FILES = {
    '2024.1Q': ('FY2024_Q1', 'lotte_2024_1Q_factsheet.xlsx'),
    '2024.2Q': ('FY2024_Q2', 'lotte_2024_2Q_factsheet.xls'),
    '2024.3Q': ('FY2024_Q3', 'lotte_2024_3Q_factsheet.xls'),
    '2024.4Q': ('FY2024_Q4', 'lotte_2024_4Q_factsheet.xls'),
    '2025.1Q': ('FY2025_Q1', 'lotte_2025_1Q_factsheet.xls'),
    '2025.2Q': ('FY2025_Q2', 'lotte_2025_2Q_factsheet.xls'),
    '2025.3Q': ('FY2025_Q3', 'lotte_2025_3Q_factsheet.xls'),
    '2025.4Q': ('FY2025_Q4', 'lotte_2025_4Q_factsheet.xls'),
    '2026.1Q': ('FY2026_Q1', 'lotte_2026_1Q_factsheet.xls'),
}
# 2023 quarters: 2Q/3Q/4Q have factsheets but use the older (월별/Highlight) layout
# without a clean per-quarter 신계약 CSM amount table; 1Q is PDF only.
PDF_ONLY = {'2023.1Q': ('FY2023_Q1', 'lotte_2023_1Q.pdf')}
OLD_LAYOUT = {
    '2023.2Q': ('FY2023_Q2', 'lotte_2023_2Q_factsheet.xlsx'),
    '2023.3Q': ('FY2023_Q3', 'lotte_2023_3Q_factsheet.xlsx'),
    '2023.4Q': ('FY2023_Q4', 'lotte_2023_4Q_factsheet.xlsx'),
}


def load_grid(path):
    """Return list-of-rows (list of cell values), 1 sheet, the quarter sheet."""
    if path.suffix.lower() == '.xls':
        wb = xlrd.open_workbook(str(path))
        sh = wb.sheet_by_index(0)
        return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
    wb = openpyxl.load_workbook(str(path), data_only=True)
    sh = wb.worksheets[0]
    for s in wb.worksheets:
        if '분기' in s.title:
            sh = s; break
    return [[sh.cell(r, c).value for c in range(1, sh.max_column + 1)]
            for r in range(1, sh.max_row + 1)]


def find_row(grid, predicate):
    for i, row in enumerate(grid):
        for v in row:
            if isinstance(v, str) and predicate(v.strip()):
                return i, row
    return None, None


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def extract(path, qcol):
    grid = load_grid(path)
    # 신계약 CSM amount row (label '신계약 CSM' exactly)
    _, csm_row = find_row(grid, lambda s: s == '신계약 CSM')
    # APE proxy: ' - 신계약 (월납환산)' (leading dash/space variants)
    _, ape_row = find_row(grid, lambda s: s.replace(' ', '').startswith('-신계약(월납환산)'))
    csm = num(csm_row[qcol]) if csm_row else None
    ape = num(ape_row[qcol]) if ape_row else None
    return csm, ape


def main():
    series = {}
    # PDF-only quarter: amount not machine-parsed here
    for per, (fy, fn) in PDF_ONLY.items():
        series[per] = {
            'nb_csm_eok': None, 'ape_eok': None,
            'multiple_disclosed': None, 'multiple_derived': None,
            'source_file': fn, 'note': 'PDF 실적자료 only (no Excel factsheet); CSM table not machine-parsed',
        }
    # 2023 Q2-Q4: older layout, amounts not in the clean per-quarter table
    for per, (fy, fn) in OLD_LAYOUT.items():
        series[per] = {
            'nb_csm_eok': None, 'ape_eok': None,
            'multiple_disclosed': None, 'multiple_derived': None,
            'source_file': fn, 'note': '2023 factsheet uses 월별/Highlight layout; no per-quarter 신계약CSM amount table',
        }
    # 2024.1Q+ : clean CSM Movement table
    for per, (fy, fn) in FILES.items():
        q = int(per.split('.')[1][0])
        path = ROOT / 'data' / 'ir' / fy / KR / fn
        try:
            csm, ape = extract(path, QCOL[q])
        except Exception as e:  # noqa: BLE001
            series[per] = {'error': str(e), 'source_file': fn}
            continue
        csm_eok = round(csm / 100.0, 1) if csm is not None else None  # 백만원→억
        ape_eok = round(ape / 100.0, 1) if ape is not None else None
        derived = round(csm / ape, 2) if (csm and ape) else None
        series[per] = {
            'nb_csm_eok': csm_eok,
            'ape_eok': ape_eok,
            'multiple_disclosed': None,
            'multiple_derived': derived,
            'source_file': fn,
        }

    payload = {
        'company': '롯데손해보험',
        'kr_dir': KR,
        'sector': 'Non-life',
        'metric_disclosed': '없음 — 롯데손해보험 IR factsheet는 신계약 CSM 배수를 공시하지 않음',
        'metric_available': '신계약 CSM (억원), 신계약 월납환산 APE (억원); 배수는 파생계산(derived)',
        'source': 'lotteins.co.kr 실적발표자료 factsheet (FY=calendar year)',
        'note': ('Lotte factsheets disclose 신계약 CSM amount and 신계약(월납환산) '
                 'but NOT a 신계약 CSM 배수. multiple_derived = 신계약CSM / 월납환산APE '
                 '(both in 억원, computed here, not an official disclosure). '
                 '신계약 CSM per-quarter values are as printed in each quarter\'s own '
                 'factsheet (current-FY column); they are cumulative YTD figures.'),
        'series': dict(sorted(series.items())),
    }
    SER.mkdir(parents=True, exist_ok=True)
    out = SER / f'{KR}.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('wrote', out)
    for per, rec in sorted(series.items()):
        print(f'  {per}: 신계약CSM={rec.get("nb_csm_eok")}억  APE={rec.get("ape_eok")}억  '
              f'배수(파생)={rec.get("multiple_derived")}  배수(공시)={rec.get("multiple_disclosed")}')


if __name__ == '__main__':
    main()
