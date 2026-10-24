# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/verify_independent/v30_dy_nh_p4.py")
s = p.read_text(encoding="utf-8")
anchor = "# identities on the master itself (원 단위 정밀도 유지)\n"
assert s.count(anchor) == 1
add = '''# item 15 (기타영업수익) of 2023.2Q is a structural zero: the FY2024_Q2 separate statement has no such row; the 보험손익 bridge adj form (2 + 15 - 16 = 1) then closes within rounding
_p, (_ln, _rs) = stmt_rows("2024.2Q")
_labels = [c[0].replace(" ", "") for _, c in _rs if c]
chk("NH FY2024_Q2 statement rows named 기타영업수익 (expected 0)", 0.0, float(sum(1 for L in _labels if L.startswith("기타영업수익"))), tol=0)
chk("NH 2023.2Q item 15 = 0.0 (structural zero, same as every other NH quarter)", 0.0, mv("KR0032", "2023.2Q", 15))
for _q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    _b = mv("KR0032", _q, 2) + mv("KR0032", _q, 15) - mv("KR0032", _q, 16) - mv("KR0032", _q, 1)
    chk("NH %s 보험손익 bridge adj form 2 + 15 - 16 - 1 (|.| <= 2 백만원)" % _q, 0.0, _b, tol=2.0)
chk("NH 2023.3Q item 15 single quarter = 0 - 0", 0.0, mv("KR0032", "2023.3Q", 15, "값_당분기"))
'''
s = s.replace(anchor, add + anchor)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
