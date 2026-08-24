# -*- coding: utf-8 -*-
"""'앵커불가' 21건이 정확히 무엇인지: APPLIERS x quarter 전수를 순회해 raw없음 / 기본요구자본
occurrence 없음 / 비율이상 세 버킷으로 분류한다 (leaf_scale_residue_audit.py 의 noanchor 재현).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from rebuild_combined_transition_after import (  # noqa: E402
    APPLIERS, _num, _pdf, q2p, scan_occurrences,
)

MASTER = REPO / "kics_disclosure.json"


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict = {}
    name = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    noraw, no_occ, bad_ratio, ok = [], [], [], []
    for (c, q), items in sorted(by_cq.items()):
        if c not in APPLIERS:
            continue
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            noraw.append((c, q))
            continue
        occ, _hl = scan_occurrences(pdf)
        if not occ.get("기본요구자본"):
            no_occ.append((c, q))
            continue
        base_pre_raw = max(a for a, _b in occ["기본요구자본"])
        item15_pre = _num((items.get(15) or {}).get("값"))
        ratio = (item15_pre or 0) / base_pre_raw if base_pre_raw else 0
        if not (0.009 < ratio < 0.011 or 0.99 < ratio < 1.01):
            bad_ratio.append((c, q, item15_pre, base_pre_raw, ratio))
            continue
        ok.append((c, q))

    print(f"APPLIERS(회사,분기) 총 {len(by_cq) and sum(1 for (c,_q) in by_cq if c in APPLIERS)}")
    print(f"raw없음 {len(noraw)}  |  기본요구자본occ없음 {len(no_occ)}  |  비율이상 {len(bad_ratio)}  |  OK {len(ok)}")
    print(f"  => 앵커불가 합계(no_occ+bad_ratio) = {len(no_occ) + len(bad_ratio)}")
    if noraw:
        print("\n[raw없음]")
        for c, q in noraw:
            print(f"  {c} {name.get(c,c):<14} {q}")
    if no_occ:
        print("\n[기본요구자본 occurrence 없음 — scan_occurrences가 그 라벨을 못 찾음]")
        for c, q in no_occ:
            print(f"  {c} {name.get(c,c):<14} {q}")
    if bad_ratio:
        print("\n[비율이상 — item15전 vs raw 기본요구자본전 스케일 불일치]")
        for c, q, p15, base, ratio in bad_ratio:
            print(f"  {c} {name.get(c,c):<14} {q}  item15전={p15}  raw기본요구자본(max)={base}  ratio={ratio:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
