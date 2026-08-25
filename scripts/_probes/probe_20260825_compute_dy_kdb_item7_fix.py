# -*- coding: utf-8 -*-
"""동양생명(KR0087) 2024.2Q/3Q, 케이디비생명보험(KR0072) 2023.2Q/3Q item7 재계산.
ABL과 동일 메커니즘: 2026-08-17 item4 override 가 item7(=item3-(4+5+6)) 을
재계산하지 않아 stale plug 로 남았다. item3/5/6 은 그대로 두고 item7 만 새 item4
기준으로 재계산.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_compute_dy_kdb_item7_fix.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

TARGETS = [("KR0087", "2024.2Q"), ("KR0087", "2024.3Q"),
           ("KR0072", "2023.2Q"), ("KR0072", "2023.3Q")]


def main() -> int:
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    by = defaultdict(dict)
    for r in rows:
        by[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r.get("값")

    out = {}
    for code, q in TARGETS:
        m = by[(code, q)]
        i3, i4, i5, i6, i7 = m[3], m[4], m[5], m[6], m[7]
        new7 = i3 - (i4 + i5 + i6)
        resid = i3 - (i4 + i5 + i6 + new7)
        print(f"[{code} {q}] item3={i3:,.6f} item4={i4:,.1f} item5={i5:,.1f} item6={i6:,.1f}")
        print(f"   item7_old={i7:,.6f} -> item7_new={new7:,.6f}   sanity_resid={resid:.9f}")
        out[f"{code}|{q}"] = {"item7_old": i7, "item7_new": round(new7, 6)}

    outp = ROOT / "scripts" / "_probes" / "_compute_dy_kdb_item7_fix_out.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
