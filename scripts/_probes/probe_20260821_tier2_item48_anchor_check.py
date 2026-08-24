# -*- coding: utf-8 -*-
"""orchestrator 결함 A/B/C 진단 — item48(보완자본 한도) == item14(지급여력기준금액) x 50%
을 적용전/적용후 양쪽에서 전수 검사. 배율(item48/expect)을 찍어 100배·기타 스케일사고와
'적용후=적용전 그대로 복사' 의심 패턴을 한 번에 드러낸다."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = REPO / "kics_disclosure.json"


def _num(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict = {}
    name: dict = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    checked = {"값": 0, "값_적용후": 0}
    ok = {"값": 0, "값_적용후": 0}
    missing48 = {"값": 0, "값_적용후": 0}
    missing14 = {"값": 0, "값_적용후": 0}
    bad = []
    mirrored_48 = 0
    mirrored_48_but14_differs = []

    for (c, q), items in sorted(by_cq.items()):
        r48, r14 = items.get(48), items.get(14)
        for col in ("값", "값_적용후"):
            v48 = _num((r48 or {}).get(col))
            v14 = _num((r14 or {}).get(col))
            if r48 is None or v48 is None:
                missing48[col] += 1
                continue
            if r14 is None or v14 is None:
                missing14[col] += 1
                continue
            checked[col] += 1
            expect = v14 * 0.5
            ratio = v48 / expect if expect else None
            if expect and abs(v48 - expect) <= max(2.0, 0.005 * abs(expect)):
                ok[col] += 1
            else:
                bad.append((c, name[c], q, col, v48, expect, ratio))

        if r48 is not None:
            v48_pre = _num(r48.get("값"))
            v48_post = _num(r48.get("값_적용후"))
            if v48_pre is not None and v48_post is not None:
                if abs(v48_pre - v48_post) < 0.005:
                    mirrored_48 += 1
                    v14_pre = _num((r14 or {}).get("값"))
                    v14_post = _num((r14 or {}).get("값_적용후"))
                    if v14_pre is not None and v14_post is not None and abs(v14_pre - v14_post) > 1.0:
                        mirrored_48_but14_differs.append((c, name[c], q, v48_pre, v14_pre, v14_post))

    print("=== item48 == item14 x 50% 검산 (적용전/적용후 별도) ===")
    for col in ("값", "값_적용후"):
        n = checked[col]
        print(f"  [{col}] 대상={n}  일치={ok[col]}({ok[col]/n*100:.1f}%)  불일치={n-ok[col]}  "
              f"item48결측={missing48[col]}  item14결측={missing14[col]}")

    print(f"\n=== item48 미러링(적용전==적용후) 카운트 ===")
    total48 = sum(1 for (_c, _q), it in by_cq.items() if it.get(48) is not None
                   and _num(it[48].get("값")) is not None and _num(it[48].get("값_적용후")) is not None)
    print(f"  전/후 둘다 있는 (회사,분기) = {total48}  |  전==후(미러) = {mirrored_48} "
          f"({mirrored_48/total48*100:.1f}%)  |  전!=후 = {total48-mirrored_48}")
    print(f"  그 중 item14 자체는 전!=후인데 item48이 미러된 케이스 = {len(mirrored_48_but14_differs)}")
    for row in mirrored_48_but14_differs[:10]:
        print("   ", row)

    print(f"\n=== 배율(item48/expect) 별 분포 ===")
    ratio_buckets: dict[str, list] = {}
    for c, nm, q, col, v48, expect, ratio in bad:
        if ratio is None:
            key = "expect=0"
        elif ratio > 50:
            key = ">50x"
        elif ratio > 10:
            key = "10-50x"
        elif ratio > 2:
            key = "2-10x"
        elif ratio > 1.05:
            key = "1.05-2x"
        elif ratio < 0.5:
            key = "<0.5x"
        else:
            key = "0.5-1.05x(근소불일치)"
        ratio_buckets.setdefault(key, []).append((c, nm, q, col, v48, expect, ratio))
    for key in sorted(ratio_buckets, key=lambda k: -len(ratio_buckets[k])):
        items_ = ratio_buckets[key]
        print(f"  {key}: {len(items_)}건")

    print(f"\n=== 불일치 전수 나열 (회사,분기,컬럼,저장값,기대값,배율) ===")
    for c, nm, q, col, v48, expect, ratio in sorted(bad, key=lambda x: (-1 if x[-1] is None else -x[-1])):
        rs = f"{ratio:.4f}" if ratio is not None else "N/A"
        print(f"  {c} {nm:<14} {q} [{col}]  저장={v48:>14,.2f}  기대={expect:>14,.2f}  배율={rs}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
