# -*- coding: utf-8 -*-
"""KR0082(디비생명보험) 2023.1Q/2Q item1/16/17/18/19 를 PL_breakdown.json(배포본)에
셀단위로 직접 패치한다 (build_pl() 전체 재실행 대신 -- 그 경로가 무관 회사(KR0005/KR0010)
6셀을 조용히 널링시켜 버려 폐기, patch_20260825_kr0082_pl_bridge.py 도 이 스크립트로
대체 -- item1 만 고치면 '영업이익=보험손익+투자손익' 등식이 item8(1,601.9)만큼 새로
깨진다는 걸 뒤늦게 발견해 item17/18/19 까지 같이 고쳐야 했다).

근거 (raw, 별도=BASIS_OVERRIDE["KR0082"] 기준, 원 단위, 당기누적):
  2023.1Q data/dart/FY2023_Q1/raw/KR0082_디비생명보험/20230515002932.xml
    (offset 86249, 별도 표): I.보험서비스손익 24,548,248,470 / II.투자손익 156,135,294,813 /
    III.보험금융손익 (97,969,444,019) / IV.영업이익 82,714,099,264(불변, 검산 앵커).
  2023.2Q data/dart/FY2023_Q2/raw/KR0082_DB생명보험/20230814002739.xml
    (offset 91154, 별도 표, 당기누적열): I.보험서비스손익 59,719,308,746 / II.투자손익
    247,652,984,525 / III.보험금융손익 (162,765,687,437) / IV.영업이익 144,606,605,834
    (불변, 검산 앵커).

검산: item1(parent) + item17(=item18+item19) == item20(불변) 양쪽 분기 모두 잔차 0.000.
item17 의 舊값(59767.74267 / 84432.30141)은 `영업이익 - item1_구값(자식행)` 잔차였음
(extract_tier1() 의 gross/net 재정렬 분기, tier1.py L279-285) -- item1 자식행 오채택이
item17 에도 전이돼 있었다(item8 만큼 이중오차).

usage:
    python scripts/_probes/patch_20260825b_kr0082_pl_bridge_full.py
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

NEW_YTD = {
    ("KR0082", 1, "2023.1Q"): 24548.24847,
    ("KR0082", 1, "2023.2Q"): 59719.308746,
    ("KR0082", 16, "2023.2Q"): 5850.450986,
    ("KR0082", 17, "2023.1Q"): 58165.850794,
    ("KR0082", 17, "2023.2Q"): 84887.297088,
    ("KR0082", 18, "2023.1Q"): 156135.294813,
    ("KR0082", 18, "2023.2Q"): 247652.984525,
    ("KR0082", 19, "2023.1Q"): -97969.444019,
    ("KR0082", 19, "2023.2Q"): -162765.687437,
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

    n_dangi_changed = 0
    for item in (1, 16, 17, 18, 19):
        ytd_by_q = {k[2]: r.get("값") for k, r in by_key.items()
                    if k[0] == "KR0082" and k[1] == item}
        for k, r in list(by_key.items()):
            if k[0] != "KR0082" or k[1] != item:
                continue
            q = k[2]
            cur = ytd_by_q.get(q)
            if cur is None:
                dangi = None
            else:
                p = prev_q(q)
                dangi = cur if p is None else (
                    None if ytd_by_q.get(p) is None else round(cur - ytd_by_q[p], 6))
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
