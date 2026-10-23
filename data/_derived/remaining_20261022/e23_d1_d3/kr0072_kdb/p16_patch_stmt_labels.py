# -*- coding: utf-8 -*-
"""patch kdb_stmt.py: the original quarterly filings label net income / OCI / total comprehensive income with 분기/반기 instead of 당기."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kdb_stmt.py"
s = p.read_text(encoding="utf-8")


def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('''    "ni": ["당기순이익(손실)", "당기순이익"], "oci": ["당기기타포괄손익"], "tci": ["당기총포괄손익"],''',
    '''    "ni": ["당기순이익(손실)", "당기순이익", "분기순이익(손실)", "분기순이익", "반기순이익(손실)", "반기순이익"],
    "oci": ["당기기타포괄손익", "분기기타포괄손익", "반기기타포괄손익"], "tci": ["당기총포괄손익", "분기총포괄손익", "반기총포괄손익"],''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
