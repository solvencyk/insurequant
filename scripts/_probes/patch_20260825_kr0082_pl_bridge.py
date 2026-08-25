# -*- coding: utf-8 -*-
"""KR0082(디비생명보험) item1/item16 2023.1Q/2Q 를 PL_breakdown.json(배포본)에 셀단위로
직접 패치한다 (build_root_masters.py::build_pl() 전체 재실행 대신).

build_pl() 을 그냥 재실행했더니(scripts/_probes/run_20260825_build_pl_only.py) 의도한
KR0082 3셀 외에 KR0005/KR0010 item16 6셀이 조용히 None 으로 널링됐다 — 원인은
data/dart/viz/pl_breakdown_master.json(중간산출물)이 배포본 대비 1,307행 stale 이라
그 6셀이 "existing-fallback" 경로로 병합됐다가 _zero_other_expense() 의
"item1 이 item16 없이도 닫히면 널링" 휴리스틱을 (이 세션에서는) 처음 통과하면서
널이 된 것으로 보이는데, 그 6셀이 실제로 틀렸었는지 진짜인지 이 세션에서 raw 로
검증하지 않았다. 파손 0 원칙상 build_pl() 전체 재실행 경로는 버리고, PL_breakdown.json
을 원상태(backup)에서 시작해 KR0082 의 정확히 이 셀들만 직접 바꾼다 — 다른 회사는
바이트 단위로 그대로 둔다.

usage:
    python scripts/_probes/patch_20260825_kr0082_pl_bridge.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\2e98dd9e-be51-411e-a455-ce573b8bf95c\scratchpad"
)
sys.stdout.reconfigure(encoding="utf-8")

PL_OUT = ROOT / "PL_breakdown.json"

# New YTD (값) for the 3 cells being corrected. Everything else (2023.3Q+ YTD, all other
# companies/items) stays exactly as in the backup.
NEW_YTD = {
    ("KR0082", 1, "2023.1Q"): 24548.24847,
    ("KR0082", 1, "2023.2Q"): 59719.308746,
    ("KR0082", 16, "2023.2Q"): 5850.450986,
}


def qkey(q: str):
    return (int(q[:4]), int(q[5]))


def prev_q(q: str):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def main() -> int:
    rows = json.loads((SCRATCH / "PL_breakdown.json.before").read_text(encoding="utf-8"))
    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}

    n_set = 0
    for key, v in NEW_YTD.items():
        r = by_key.get(key)
        if r is None:
            print(f"  MISSING ROW (not patched): {key}")
            continue
        old = r.get("값")
        r["값"] = v
        n_set += 1
        print(f"  SET {key}  값 {old} -> {v}")

    # Recompute 값_당분기 for KR0082 item1 and item16 ONLY (mirrors
    # build_root_masters._flow_dangi: Q1 당분기=YTD; Qn(n>1) 당분기=YTD(Qn)-YTD(Qn-1)
    # within the SAME FY). Recomputing the full series is safe/idempotent — quarters
    # whose YTD didn't change reproduce their existing 당분기 unchanged.
    n_dangi_changed = 0
    for item in (1, 16):
        ytd_by_q = {}
        for k, r in by_key.items():
            if k[0] == "KR0082" and k[1] == item:
                ytd_by_q[k[2]] = r.get("값")
        for q, r in [(k[2], r) for k, r in by_key.items()
                     if k[0] == "KR0082" and k[1] == item]:
            cur = ytd_by_q.get(q)
            if cur is None:
                dangi = None
            else:
                p = prev_q(q)
                if p is None:
                    dangi = cur
                else:
                    prev = ytd_by_q.get(p)
                    dangi = None if prev is None else round(cur - prev, 6)
            old_dangi = r.get("값_당분기")
            if old_dangi != dangi:
                print(f"  DANGI KR0082 item{item} {q}: {old_dangi} -> {dangi}")
                n_dangi_changed += 1
            r["값_당분기"] = dangi

    print(f"\nset {n_set} YTD cells, recomputed 당분기 changed {n_dangi_changed} cells")

    out = list(by_key.values())
    print(f"row count: before={len(rows)} out={len(out)}")
    PL_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {PL_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
