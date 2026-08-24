# -*- coding: utf-8 -*-
"""inbox 20260821T2010Z 임무1 진단 (read-only) — 예별손해 item19/36-40, 처브라이프 item35,
아이엠라이프 item17/29-35 를 raw occurrences 와 master 값(전/후) 나란히 덤프한다.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from rebuild_combined_transition_after import (  # noqa: E402
    ITEM_OF, LIFE7, MARKET5, _num, _pdf, q2p, scan_occurrences,
)
from solvency.validation.kics_json_rules import R4, R7, MARKET_M  # noqa: E402
import numpy as np

MASTER = REPO / "kics_disclosure.json"

TARGETS = [
    ("KR0004", "2023.4Q"),
    ("KR0004", "2024.1Q"),
    ("KR0004", "2024.2Q"),
    ("KR0100", "2024.4Q"),
    ("KR0076", "2023.1Q"),
]


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict = {}
    name = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    for c, q in TARGETS:
        items = by_cq.get((c, q), {})
        print("=" * 100)
        print(f"{c} {name.get(c,c)} {q}")
        pdf = _pdf(q2p(q), c)
        print(f"  raw pdf: {pdf}")
        if pdf is None:
            print("  raw 없음")
            continue
        occ, headline = scan_occurrences(pdf)
        print(f"  headline(경과조치후 지급여력비율)={headline}")

        print("  -- master 항목 1,14,15,16,17,18,19,20,21,22 (전 | 후) --")
        for it in (1, 14, 15, 16, 17, 18, 19, 20, 21, 22):
            row = items.get(it)
            if row is None:
                print(f"    item{it}: (행 없음)")
                continue
            print(f"    item{it} {row.get('항목명','')[:20]:<20}: 전={row.get('값')!r}  후={row.get('값_적용후')!r}")

        print("  -- master 생명장기 leaf 29-35 (전 | 후) --")
        for k in LIFE7:
            it = ITEM_OF[k]
            row = items.get(it)
            v = None if row is None else (row.get("값"), row.get("값_적용후"))
            print(f"    item{it} {k:<8}: {v}")

        print("  -- master 시장 leaf 36-40 (전 | 후) --")
        for k in MARKET5:
            it = ITEM_OF[k]
            row = items.get(it)
            v = None if row is None else (row.get("값"), row.get("값_적용후"))
            print(f"    item{it} {k:<8}: {v}")

        print("  -- raw occurrences (라벨: [(전,후), ...] 백만원) --")
        for k in ["기본요구자본", "기준금액", "생명장기", "시장", "일반손해", "신용", "운영", "법인세",
                  *LIFE7, *MARKET5]:
            if occ.get(k):
                print(f"    {k:<8}: {occ[k]}")

        # anchor 계산 재현
        base_occ = occ.get("기본요구자본")
        if base_occ:
            base_pre_raw = max(a for a, _b in base_occ)
            item15_pre = _num((items.get(15) or {}).get("값"))
            ratio = (item15_pre or 0) / base_pre_raw if base_pre_raw else 0
            print(f"  anchor: item15전={item15_pre}  raw기본요구자본전(max)={base_pre_raw}  ratio={ratio}")
        else:
            print("  anchor: 기본요구자본 occurrence 없음 (앵커불가 사유: raw에서 라벨을 못 찾음)")

        # R7/MARKET_M 독립 재계산 (전/후 둘다, occ 있는 값만)
        def recompute(keys, mat, col_idx):
            vals = []
            ok = True
            for k in keys:
                pairs = occ.get(k, [])
                if not pairs:
                    ok = False
                    break
                vals.append(pairs[0][col_idx] if col_idx == 0 else (pairs[-1][1] if pairs[-1][1] is not None else pairs[-1][0]))
            if not ok:
                return None
            arr = np.array(vals, float)
            return float(np.sqrt(arr @ mat @ arr))

        life_pre_calc = recompute(LIFE7, R7, 0)
        mkt_pre_calc = recompute(MARKET5, MARKET_M, 0)
        print(f"  raw-leaf 재계산: 생명장기전={life_pre_calc}  시장전={mkt_pre_calc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
