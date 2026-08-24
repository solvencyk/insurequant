# -*- coding: utf-8 -*-
"""Read-only: for the 5 re-audit buckets, dump (a) live rule findings, (b) master cells.

재현:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
    scripts/_probes/probe_20260824_reaudit_kr0003_kr0004_state.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

TARGETS = [
    ("KR0003", "2023.1Q"),
    ("KR0003", "2024.4Q"),
    ("KR0003", "2025.1Q"),
    ("KR0003", "2026.1Q"),
    ("KR0004", "2025.1Q"),
]
# 대조군(같은 발행사 이웃 분기)
CONTROLS = [
    ("KR0003", "2023.2Q"), ("KR0003", "2023.3Q"), ("KR0003", "2023.4Q"),
    ("KR0003", "2024.1Q"), ("KR0003", "2024.2Q"), ("KR0003", "2024.3Q"),
    ("KR0003", "2025.2Q"), ("KR0003", "2025.3Q"), ("KR0003", "2025.4Q"),
    ("KR0004", "2024.4Q"), ("KR0004", "2025.2Q"), ("KR0004", "2025.3Q"),
    ("KR0004", "2025.4Q"), ("KR0004", "2026.1Q"), ("KR0004", "2024.3Q"),
]

ITEMS = [1, 2, 3, 4, 12, 13, 14, 47, 48, 49, 50, 51, 52, 53, 54]


def main() -> None:
    from src.solvency.validation.kics_json_rules import (
        run_validation, _tier2_i47_scope_map, _group_records,
    )
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res

    tset = set(TARGETS)
    print("=" * 100)
    print("PART 1 — live findings (non-GREEN) for the 5 buckets")
    print("=" * 100)
    for f in findings:
        key = (f["원보험사코드"], f["공시분기"])
        if key not in tset:
            continue
        if f["status"] == "GREEN":
            continue
        print(f"\n[{f['status']}] {key[0]} {key[1]} {f['rule']}")
        print(f"    expected={f.get('expected')!r} actual={f.get('actual')!r} diff={f.get('diff')!r}")
        print(f"    detail={f.get('detail','')}")

    print("\n" + "=" * 100)
    print("PART 1b — ALL findings (incl GREEN) rule names for the 5 buckets")
    print("=" * 100)
    for t in TARGETS:
        rr = [(f["rule"], f["status"], f.get("diff")) for f in findings
              if (f["원보험사코드"], f["공시분기"]) == t]
        print(f"\n{t}: {len(rr)} findings")
        for r, s, d in sorted(rr):
            if s != "GREEN":
                print(f"    {s:<7} {r:<34} diff={d}")

    # master cells
    print("\n" + "=" * 100)
    print("PART 2 — master cells (값 / 값_적용후)")
    print("=" * 100)
    idx: dict[tuple[str, str], dict[int, dict]] = {}
    for r in rows:
        k = (r.get("원보험사코드"), r.get("공시분기"))
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        idx.setdefault(k, {})[it] = r
    for t in TARGETS + CONTROLS:
        d = idx.get(t, {})
        if not d:
            print(f"\n### {t[0]} {t[1]} — NO ROWS")
            continue
        print(f"\n### {t[0]} {t[1]}  ({'TARGET' if t in tset else 'control'})")
        for it in ITEMS:
            r = d.get(it)
            if r is None:
                print(f"    item{it:<3} MISSING")
                continue
            print(f"    item{it:<3} {str(r.get('항목명'))[:34]:<36} 전={r.get('값')!r:>16}  후={r.get('값_적용후')!r:>16}")

    # scope map
    print("\n" + "=" * 100)
    print("PART 3 — item47 scope vote per company")
    print("=" * 100)
    try:
        buckets = _group_records(rows)
    except Exception:
        buckets = None
    if buckets is not None:
        smap = _tier2_i47_scope_map(buckets, 2.0)
        for c in ("KR0003", "KR0004", "KR0068", "KR0075"):
            print(f"    {c}: {smap.get(c)}")
        print("    full map:", dict(sorted(smap.items())))


if __name__ == "__main__":
    main()
