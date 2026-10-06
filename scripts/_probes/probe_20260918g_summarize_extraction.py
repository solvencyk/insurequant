# -*- coding: utf-8 -*-
"""추출 결과 요약: 상태별 셀 목록 + OK 인데 8항목 미만인 셀 상세."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    p = os.path.join(ROOT, "data", "_derived", "pl_backfill_disclosure_20260918.json")
    doc = json.loads(open(p, encoding="utf-8").read())
    by_status = {}
    partial = []
    for c in doc["cells"]:
        by_status.setdefault(c["status"], []).append(f"{c['원보험사코드']}/{c['공시분기']}")
        if c["status"] == "OK" and len(c["items"]) < 8:
            missing = sorted(set(range(1, 33)) & {1, 16, 17, 20, 21, 22, 23, 24} - {int(k) for k in c["items"]})
            partial.append((c["원보험사코드"], c["공시분기"], len(c["items"]), missing, c.get("warnings")))

    for st, lst in by_status.items():
        if st == "OK":
            continue
        print(f"\n=== {st} ({len(lst)}) ===")
        for x in lst:
            print(" ", x)

    print(f"\n=== OK but <8 items ({len(partial)}) ===")
    for code, q, n, missing, warn in partial:
        print(f"  {code}/{q}: {n}/8 items, missing={missing}, warnings={warn}")


if __name__ == "__main__":
    main()
