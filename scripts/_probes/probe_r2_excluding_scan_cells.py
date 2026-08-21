# -*- coding: utf-8 -*-
"""R2_순자산합 동어반복 지표를 **image-only 24셀을 뺀 뒤** 다시 잰다 (측정만, 축 정의는 안 건드림).

배경: parser 티켓 `inbox/parser/20260821T1505Z` §③ 이 되맞춤을 걷어내 R2 를 99.7%→67.9% 로
내렸지만 임계(excess 1.20 · z 5.0) 위에 남았고, "남은 초과분은 image-only 24셀이 resid=0 으로
고정된 것이 대부분 설명한다 — 다만 축 정의를 내가 임의로 바꿀 수 없으니 validation 판단"이라고
넘겼다(같은 티켓 §"손 안 댐(정책, 24셀)" 및 후속과제 2번).

이 스크립트는 **결정하지 않는다.** 그 24셀을 뺐을 때 지표가 임계 밑으로 내려가는지 숫자만
만들어 준다. 뺄지 말지는 validation 이 정한다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_r2_excluding_scan_cells.py
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
    _TAUT_ZERO_EPS, KEY_CODE, KEY_ITEM, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST,
    _load_records, _taut_axes, _taut_null_p0,
)

# parser 티켓 20260821T1505Z §"손 안 댐(정책, 24셀)" 이 열거한 image-only 코호트.
# fitz total_chars 실측으로 텍스트레이어 실질 부재가 확인됐고 `IMAGE_OCR_COMPANIES` 와 겹친다.
SCAN_ONLY = {
    "KR0010": None,      # 9분기 — 전 분기
    "KR0079": None,      # 9분기 — 전 분기
    "KR0080": {"2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"},
    "KR0071": {"2024.4Q"},
}


def is_scan(code: str, quarter: str) -> bool:
    if code not in SCAN_ONLY:
        return False
    qs = SCAN_ONLY[code]
    return qs is None or quarter in qs


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def r2_cells() -> list[dict]:
    """게이트의 `_identity_tautology_census` 내부 루프를 R2 축에 대해서만 셀 단위로 재현한다.
    (census 는 축 단위로 집계만 내보내서 셀을 골라낼 수 없다 — 로직은 그대로 베낀다.)"""
    records = _load_records(ROOT / "kics_disclosure.json")
    byq: dict[tuple, dict] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    axes, _drift = _taut_axes()
    spec = [a for a in axes if a[0] == "R2_순자산합"]
    if not spec:
        raise SystemExit("R2_순자산합 축이 _taut_axes 에 없다 — 축 정의가 바뀌었는지 확인할 것")
    _axis, tgt, signs, _desc = spec[0]

    cells = []
    for column, i in (("적용전", 0), ("적용후", 1)):
        for (c, q), m in sorted(byq.items()):
            tv = m.get(tgt, (None, None))[i]
            if tv is None:
                continue
            vals = {it: m.get(it, (None, None))[i] for it in signs}
            if any(v is None for v in vals.values()):
                continue
            k_eff = sum(1 for v in vals.values() if v != 0)
            if k_eff < 2:
                continue
            resid = tv - sum(s * vals[it] for it, s in signs.items())
            cells.append({"code": c, "quarter": q, "column": column, "k_eff": k_eff,
                          "resid": resid, "exact_zero": abs(resid) < _TAUT_ZERO_EPS})
    return cells


def stat(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {"n": 0}
    zero = sum(1 for r in rows if r["exact_zero"])
    exp = sum(_taut_null_p0(r["k_eff"]) for r in rows)
    var = sum((lambda p: p * (1 - p))(_taut_null_p0(r["k_eff"])) for r in rows)
    obs, p0 = zero / n, exp / n
    return {"n": n, "exact0": zero, "pct": round(obs * 100, 1),
            "null_pct": round(p0 * 100, 1),
            "excess": round(obs / p0, 2) if p0 else None,
            "z": round((zero - exp) / var ** 0.5, 1) if var > 0 else None}


def main() -> int:
    cells = r2_cells()
    out = {}
    for col in ("적용전", "적용후"):
        sub = [c for c in cells if c["column"] == col]
        kept = [c for c in sub if not is_scan(c["code"], c["quarter"])]
        dropped = [c for c in sub if is_scan(c["code"], c["quarter"])]
        out[col] = {
            "전체": stat(sub),
            "스캔셀 제외": stat(kept),
            "제외": {"n": len(dropped),
                     "그중 resid=0": sum(1 for c in dropped if c["exact_zero"]),
                     "목록": sorted({(c["code"], c["quarter"]) for c in dropped})},
        }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    print()
    print("임계: excess >= 1.20 AND z >= 5.0 (n >= 30) 이면 RED")
    for col, d in out.items():
        a, b = d["전체"], d["스캔셀 제외"]
        red = (b.get("n", 0) >= 30 and (b.get("excess") or 0) >= 1.20
               and (b.get("z") or 0) >= 5.0)
        print(f"  {col}: 전체 excess {a.get('excess')} z {a.get('z')}"
              f"  →  스캔셀 {d['제외']['n']}칸 제외 후 excess {b.get('excess')} z {b.get('z')}"
              f"   ⇒ {'여전히 RED' if red else '임계 아래'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
