"""Step 6: is a K-ICS-era 신종자본증권 tier1-type (III.2.다.(1) 10% 한도) or tier2-type (III.2.다.(2) 보완자본 자본증권)?

Test (read-only, master time series): when item6 (보통주 이외 자본증권) jumps by a new issue and the company stays
under SCR x 10%, a tier1-type security stays in 기본자본 -> X = item13 - item49 (equity-side non-lapse reclass) does
not move; a tier2-type security is reclassified -> X rises by about the issue amount.
Output: s6_tier1_type_test.txt

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s6_tier1_type_test.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CODES = ["KR0068", "KR0072", "KR0097", "KR0050", "KR0032", "KR1000", "KR0073", "KR0005", "KR0011", "KR0104", "KR0083", "KR0071", "KR0002"]


def f(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def qkey(q):
    y, p = q.split(".")
    return int(y), int(p[0])


def main() -> int:
    d = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    t: dict[tuple[str, str], dict[int, float]] = {}
    names = {}
    for r in d:
        if r["원보험사코드"] in CODES and r["항목번호"] in (6, 13, 14, 49, 53):
            t.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = f(r.get("값"))
            names[r["원보험사코드"]] = r.get("원수사명")
    out = []
    for code in CODES:
        out.append(f"== {code} {names.get(code)}  (q: item6 | item13 item49 X=13-49 | SCR x10% | dItem6 dX)")
        prev = None
        for q in sorted({q for c, q in t if c == code}, key=qkey):
            v = t[(code, q)]
            i6, i13, i49, i14 = v.get(6), v.get(13), v.get(49), v.get(14)
            x = None if i13 is None or i49 is None else round(i13 - i49, 1)
            cap = None if i14 is None else round(i14 * 0.10, 1)
            dd = ""
            if prev and i6 is not None and prev[0] is not None and x is not None and prev[1] is not None:
                dd = f"d6={i6 - prev[0]:+.0f} dX={x - prev[1]:+.0f}"
            out.append(f"  {q}: {i6} | {i13} {i49} {x} | {cap} | {dd}  item53={v.get(53)}")
            prev = (i6, x)
    (HERE / "s6_tier1_type_test.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
