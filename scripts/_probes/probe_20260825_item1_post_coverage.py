# -*- coding: utf-8 -*-
"""읽기전용 진단: item1[값_적용후] 커버리지 소실 가설을 반증한다.

가설(오케스트레이터 티켓): `50_tfi_tier_split_post` 가 item52 있으면 등식으로 도는데,
item52 가 30버킷 더 실려 458/488 로 늘면서 예전 폴백(범위검사, item1_post 를 범위 상한으로
참조)이 대부분 안 쓰이게 됐고 그게 item1_post 를 지키던 유일한 룰이었다.

이 스크립트는:
  1) 양성대조군 — item1[값](적용전)을 흔들면 반드시 반응한다(엔진이 죽은 게 아님을 증명).
  2) 본시험 — item1[값_적용후]를 흔들면 반응하는지.
  3) 분기별 분해 — 50/51 이 있는 버킷 중 몇 개가 item52_적용후를 갖고 있는지(=범위검사
     폴백이 실제로 몇 버킷에서 살아있는지).
  4) 단일 버킷 정밀조준 — item52_적용후가 없는 버킷 하나를 골라 그 버킷만 item1_후를 흔들어
     50_tfi_tier_split_post 가 반응하는지(폴백 자체는 살아있는지 확인).

마스터·룰엔진 둘 다 읽기전용 — 아무것도 안 쓴다.
"""
from __future__ import annotations

import copy
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from solvency.validation.kics_json_rules import run_validation, TFI_TIER_ITEMS, TFI_TOTAL_ITEM  # noqa: E402
from validate_kics_disclosure import _load_tfi_applicability  # noqa: E402

MASTER = ROOT / "kics_disclosure.json"


def load_rows():
    return json.loads(MASTER.read_text(encoding="utf-8"))


def findings(rows, tfi):
    r = run_validation(rows, tfi_applicability=tfi)
    return r["findings"] if isinstance(r, dict) else r


def sig(fs):
    return {(f["원보험사코드"], f["공시분기"], f["rule"]): f["status"] for f in fs}


def mutate_all(rows, item, col):
    out = copy.deepcopy(rows)
    n = 0
    for r in out:
        if str(r.get("항목번호")) == str(item) and r.get(col) not in (None, ""):
            r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
            n += 1
    return out, n


def mutate_one(rows, item, col, code, quarter):
    out = copy.deepcopy(rows)
    n = 0
    for r in out:
        if (str(r.get("항목번호")) == str(item) and r.get(col) not in (None, "")
                and r.get("원보험사코드") == code and r.get("공시분기") == quarter):
            r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
            n += 1
    return out, n


def main():
    rows = load_rows()
    tfi = _load_tfi_applicability()
    base_f = findings(rows, tfi)
    base = sig(base_f)

    # --- 1) 양성대조군: item1[값](적용전) ------------------------------------
    pre_mut, n_pre = mutate_all(rows, 1, "값")
    pre_after = sig(findings(pre_mut, tfi))
    pre_changed = [k for k in base if base[k] != pre_after.get(k)]
    print(f"[양성대조군] item1[값] {n_pre}칸 흔듦 -> 변화 {len(pre_changed)}건 "
          f"(0이면 하니스 자체가 죽은 것)")
    for k in pre_changed[:5]:
        print(f"    {k}: {base[k]} -> {pre_after.get(k)}")

    # --- 2) 본시험: item1[값_적용후] -------------------------------------------
    post_mut, n_post = mutate_all(rows, 1, "값_적용후")
    post_after = sig(findings(post_mut, tfi))
    post_changed = [k for k in base if base[k] != post_after.get(k)]
    print(f"\n[본시험] item1[값_적용후] {n_post}칸 흔듦 -> 변화 {len(post_changed)}건")
    for k in post_changed[:20]:
        print(f"    {k}: {base[k]} -> {post_after.get(k)}")

    # --- 3) 버킷 분해: 50/51 있는 버킷 중 item52_적용후 있는/없는 수 -----------
    by_bucket = {}
    for r in rows:
        try:
            item = int(r["항목번호"])
        except (KeyError, ValueError, TypeError):
            continue
        key = (r.get("원보험사코드"), r.get("공시분기"))
        b = by_bucket.setdefault(key, {"values": {}, "values_post": {}})
        v = r.get("값")
        vp = r.get("값_적용후")
        if v not in (None, ""):
            b["values"][item] = v
        if vp not in (None, ""):
            b["values_post"][item] = vp

    has_5051_post = [k for k, b in by_bucket.items()
                     if all(i in b["values_post"] for i in TFI_TIER_ITEMS)]
    has_52_post = [k for k in has_5051_post if TFI_TOTAL_ITEM in by_bucket[k]["values_post"]]
    no_52_post = [k for k in has_5051_post if TFI_TOTAL_ITEM not in by_bucket[k]["values_post"]]
    print(f"\n[분해] 50/51 둘 다 있는(적용후) 버킷 {len(has_5051_post)}개 중 "
          f"item52_적용후 있음 {len(has_52_post)} / 없음 {len(no_52_post)}")
    print(f"  item52 없는 버킷(폴백이 살아있어야 하는 곳): {no_52_post}")

    has_5051_pre = [k for k, b in by_bucket.items()
                    if all(i in b["values"] for i in TFI_TIER_ITEMS)]
    has_52_pre = [k for k in has_5051_pre if TFI_TOTAL_ITEM in by_bucket[k]["values"]]
    no_52_pre = [k for k in has_5051_pre if TFI_TOTAL_ITEM not in by_bucket[k]["values"]]
    print(f"[분해] 50/51 둘 다 있는(적용전) 버킷 {len(has_5051_pre)}개 중 "
          f"item52_적용전 있음 {len(has_52_pre)} / 없음 {len(no_52_pre)}")

    # --- 4) 단일 버킷 정밀조준: item52_적용후 없는 버킷 하나만 흔들기 -----------
    if no_52_post:
        code, quarter = no_52_post[0]
        one_mut, n_one = mutate_one(rows, 1, "값_적용후", code, quarter)
        one_after = sig(findings(one_mut, tfi))
        one_changed = [k for k in base if base[k] != one_after.get(k)
                       and k[0] == code and k[1] == quarter]
        print(f"\n[정밀조준] {code} {quarter} (item52_적용후 없음) 만 item1_후 흔듦 "
              f"({n_one}칸) -> 이 버킷 변화 {len(one_changed)}건")
        for k in one_changed:
            print(f"    {k}: {base[k]} -> {one_after.get(k)}")
    else:
        print("\n[정밀조준] item52_적용후 없는 버킷이 0개 — 폴백이 설 자리가 없다")


if __name__ == "__main__":
    main()
