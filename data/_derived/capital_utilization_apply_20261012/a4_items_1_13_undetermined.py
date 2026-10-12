"""a4: item names 1..13 and 47..54 + 2026.2Q values (pre/post) for the four undetermined tier1 companies
(코리안리 KR1000 · 농협생명 KR0104 · 푸본현대 KR0083 · 흥국생명 KR0071) and two reference companies whose
type is known (하나생명 KR0097 = basic-capital type, KDB생명 KR0072 = supplementary-capital type). Read-only.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a4_items_1_13_undetermined.py
Output: a4_items_1_13_undetermined.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = "2026.2Q"
CODES = ["KR1000", "KR0104", "KR0083", "KR0071", "KR0097", "KR0072"]
ITEMS = list(range(1, 15)) + list(range(47, 55))


def main() -> int:
    kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    names: dict[int, str] = {}
    vals: dict[tuple, tuple] = {}
    for r in kics:
        n = r.get("항목번호")
        if n in ITEMS and n not in names:
            names[n] = r.get("항목명")
        if r.get("공시분기") == Q and r["원보험사코드"] in CODES and n in ITEMS:
            vals[(r["원보험사코드"], n)] = (r.get("값"), r.get("값_적용후"))
    out = ["item names: " + " | ".join(f"{n}={names.get(n)}" for n in ITEMS)]
    for c in CODES:
        out.append(f"== {c}")
        for n in ITEMS:
            v = vals.get((c, n))
            if v is not None:
                out.append(f"   {n:>2} {str(names.get(n))[:28]:28s} 값={v[0]}  적용후={v[1]}")
    txt = "\n".join(out) + "\n"
    (HERE / "a4_items_1_13_undetermined.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
