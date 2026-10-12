"""a3: quarterly series of item54 ('(기발행 후순위채무)', TFI table) and item47 pre/post for the companies whose
2026.2Q item54 exceeds the bond ledger's pre-2023 subordinated balance (read-only). A jump in item54 in the quarter a
2023+ subordinated bond was issued = the issuer prints new debt in the legacy row.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a3_item54_series.py
Output: a3_item54_series.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CODES = ["KR0001", "KR0071", "KR0068", "KR0010", "KR0070", "KR1011", "KR0082", "KR0079", "KR0104", "KR0083"]


def f(v):
    try:
        return float(str(v).replace(",", "").replace("△", "-"))
    except (TypeError, ValueError):
        return None


def qkey(q):
    y, p = q.split(".")
    return int(y), int(p[0])


def main() -> int:
    kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    t: dict[tuple, dict] = {}
    names = {}
    for r in kics:
        c = r["원보험사코드"]
        if c in CODES and r["항목번호"] in (3, 47, 49, 53, 54):
            t.setdefault((c, r["공시분기"]), {})[r["항목번호"]] = (f(r.get("값")), f(r.get("값_적용후")))
            names[c] = r.get("원수사명")
    out = []
    for c in CODES:
        out.append(f"== {c} {names.get(c)}   q: item54 | item53 | item47 pre -> post | item3 | item49")
        prev54 = None
        for q in sorted({q for (cc, q) in t if cc == c}, key=qkey):
            v = t[(c, q)]
            i54 = (v.get(54) or (None,))[0]
            d54 = "" if prev54 is None or i54 is None else f"  d54={i54 - prev54:+,.1f}"
            p47 = v.get(47) or (None, None)
            out.append(f"  {q}: {i54} | {(v.get(53) or (None,))[0]} | {p47[0]} -> {p47[1]} | {(v.get(3) or (None,))[0]} | "
                       f"{(v.get(49) or (None,))[0]}{d54}")
            if i54 is not None:
                prev54 = i54
    txt = "\n".join(out) + "\n"
    (HERE / "a3_item54_series.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
