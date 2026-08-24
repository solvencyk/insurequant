# -*- coding: utf-8 -*-
"""R2_순자산합 축의 셀별 상세(회사/분기/컬럼별 item4, 자식합, 잔차)를 지정 회사코드에 대해 출력.
읽기 전용. probe_r2_excluding_scan_cells.py 의 r2_cells() 로직을 그대로 씀 + item4/children raw values.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_r2_company_detail.py KR0069 KR0008 ...
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from validate_kics_disclosure import (  # noqa: E402
    KEY_CODE, KEY_ITEM, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST, _load_records, _taut_axes,
)


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    codes = set(sys.argv[1:])
    records = _load_records(ROOT / "kics_disclosure.json")
    byq: dict[tuple, dict] = {}
    names: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
        if it == 4 and r.get("회사명"):
            names[c] = r.get("회사명")

    axes, _ = _taut_axes()
    spec = [a for a in axes if a[0] == "R2_순자산합"][0]
    _axis, tgt, signs, _desc = spec

    for code in sorted(codes):
        print(f"===== {code} {names.get(code, '')} =====")
        for column, i in (("적용전", 0), ("적용후", 1)):
            for (c, q), m in sorted(byq.items()):
                if c != code:
                    continue
                tv = m.get(tgt, (None, None))[i]
                if tv is None:
                    continue
                vals = {it: m.get(it, (None, None))[i] for it in signs}
                if any(v is None for v in vals.values()):
                    continue
                s = sum(sign * vals[it] for it, sign in signs.items())
                resid = tv - s
                flag = "  <-- resid!=0" if abs(resid) >= 1e-6 else ""
                child_str = " ".join(f"i{it}={vals[it]:g}" for it in sorted(signs))
                print(f"  {q} [{column}] item4={tv:g} sum_children={s:g} resid={resid:g}{flag}   ({child_str})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
