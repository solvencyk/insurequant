"""a5b: 코리안리 (KR1000) - TFI table basic-capital columns per quarter (read-only).

Checks the premise of the a5 feasibility verdict: in the TFI-off column, are the legacy hybrids (item53) wholly
outside basic capital (item50 적용후 - item50 값 == item53 or == min(item53, SCR x 15%))? If yes, whatever hybrid
capital stays in basic capital in the TFI-off basis must be the post-2023 issues (= basic-capital type).

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a5b_koreanre_tfi_check.py
Output: a5b_koreanre_tfi_check.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CODE = "KR1000"


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
    t: dict[str, dict] = {}
    for r in kics:
        if r["원보험사코드"] == CODE and r["항목번호"] in (2, 3, 6, 13, 14, 47, 49, 50, 51, 53):
            t.setdefault(r["공시분기"], {})[r["항목번호"]] = (f(r.get("값")), f(r.get("값_적용후")))
    out = ["q | item2 | item50 pre->post (diff) | item53 | min(53,15%SCR) | item6 | item13 | item49 | item3 | item51 pre->post"]
    for q in sorted(t, key=qkey):
        v = t[q]
        g = lambda n, i=0: (v.get(n) or (None, None))[i]
        p50, q50, i53, i14 = g(50), g(50, 1), g(53) or 0.0, g(14)
        diff = None if p50 is None or q50 is None else q50 - p50
        cap = None if i14 is None else min(i53, i14 * 0.15)
        out.append(f"{q} | {g(2)} | {p50} -> {q50} ({diff if diff is None else round(diff, 2)}) | {i53} | "
                   f"{cap if cap is None else round(cap, 2)} | {g(6)} | {g(13)} | {g(49)} | {g(3)} | {g(51)} -> {g(51, 1)}")
    txt = "\n".join(out) + "\n"
    (HERE / "a5b_koreanre_tfi_check.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
