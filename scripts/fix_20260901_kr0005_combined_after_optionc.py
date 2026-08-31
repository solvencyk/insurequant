# -*- coding: utf-8 -*-
"""UPSERT fix (2026-09-01) -- 흥국화재(KR0005) 2025.3Q / 2026.2Q item15/16/22 값_적용후.

inbox/parser/20260901T0405Z__validation__KR0005_2025.3Q_2026.2Q__irr_transition_leg_not_merged.md
3번 항목("파서 단독 결정 범위 밖") -- owner 가 옵션 (c) R4 재도출을 승인했다(2026-09-01, 별도
지시). item19/36후 결합수정(scripts/fix_20260901_kr0005_irr_leg_merge.py, 이전 세션 적용완료)의
부작용으로 R6_item16 항등식이 새로 깨졌던 것을, item15/16/22후를 R4 로 재도출해 복원한다.

  item15후 = sqrt(W' R4 W) + item21후,   W = (item17,18,19,20)후   (전부 MASTER 현재값, 이미 확정)
  item14후 = 불변 (원문 헤드라인 앵커)
  item22후 = item15후 - item14후 + item23후   (앵커 잔차 역산)
  item16후 = Σ(item17..21)후 - item15후

R4 는 src/solvency/validation/kics_json_rules.py 에서 import(재타이핑 금지). 값은
data/_derived/_patch_2026q2_KR0005.json(기존, 2026-08-31 계산분 그대로 일치 확인) +
data/_derived/_patch_2025q3_KR0005.json(신규, 이번 세션) 과 동일 -- 이번 세션이 독립적으로
scripts/_probes/compute_20260901_kr0005_option_c.py 로 재검산해 소수점까지 일치함을 확인했고,
scripts/_probes/verify_20260901_kr0005_combined_after.py(raw 재스캔) + rebuild_combined_
transition_after.py --dry-run --only KR0005(정본 스크립트 자체) 두 독립 경로로도 0.4 이내
수렴을 교차검증했다(게이트 허용오차 2.0 이내).

item17/18/19/20/21/14/23후는 건드리지 않는다(이미 올바름, 이번 세션 범위 밖).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from solvency.validation.kics_json_rules import R4  # noqa: E402

JSON_PATH = ROOT / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_QUARTER = "공시분기"
KEY_VALUE_POST = "값_적용후"

CODE = "KR0005"

# quarter -> expected BEFORE (값_적용후, frozen stale values) for items 15/16/22, sanity-gated.
BEFORE = {
    "2025.3Q": {15: "19452.79", 16: "5073.64", 22: "4663.79"},
    "2026.2Q": {15: "23496.92", 16: "4610.98", 22: "5778.92"},
}


def _num(x):
    if x is None or x == "":
        return None
    return float(str(x).replace(",", ""))


def load():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    text = json.dumps(data, indent=2, ensure_ascii=False)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(JSON_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def find_row(data, code, quarter, item):
    for r in data:
        c = r.get(KEY_CODE) or r.get("회사코드")
        if c == code and r.get(KEY_QUARTER) == quarter and r.get(KEY_ITEM) == item:
            return r
    return None


def fmt(x: float) -> str:
    return f"{x:.2f}"


def main():
    data = load()
    before_n = len(data)
    print(f"loaded {before_n} rows")

    all_census = []
    for quarter in ("2025.3Q", "2026.2Q"):
        print(f"\n=== {CODE} {quarter} ===")
        items = {}
        for it in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
            row = find_row(data, CODE, quarter, it)
            if row is None:
                raise SystemExit(f"ABORT: {CODE} {quarter} item{it} row not found")
            items[it] = row

        # sanity: item15/16/22 currently at the expected (pre-fix) frozen values
        for it in (15, 16, 22):
            got = items[it].get(KEY_VALUE_POST)
            want = BEFORE[quarter][it]
            if str(got) != want:
                raise SystemExit(
                    f"ABORT: {CODE} {quarter} item{it}후 = {got!r}, expected {want!r} before fix "
                    "-- master may have already changed since this script was written")
        print("[sanity] item15/16/22후 at expected pre-fix frozen values -- OK")

        it17 = _num(items[17][KEY_VALUE_POST])
        it18 = _num(items[18][KEY_VALUE_POST])
        it19 = _num(items[19][KEY_VALUE_POST])
        it20 = _num(items[20][KEY_VALUE_POST])
        it21 = _num(items[21][KEY_VALUE_POST])
        it14 = _num(items[14][KEY_VALUE_POST])
        it23 = _num(items[23][KEY_VALUE_POST]) or 0.0
        for label, v in (("17", it17), ("18", it18), ("19", it19), ("20", it20),
                          ("21", it21), ("14", it14)):
            if v is None:
                raise SystemExit(f"ABORT: {CODE} {quarter} item{label}후 missing, cannot derive")

        W = np.array([it17, it18, it19, it20], float)
        item15_new = float(np.sqrt(W @ R4 @ W)) + it21
        item16_new = (it17 + it18 + it19 + it20 + it21) - item15_new
        item22_new = item15_new - it14 + it23
        print(f"[compute] item15후 = {item15_new:.4f} -> {fmt(item15_new)}")
        print(f"[compute] item16후 = {item16_new:.4f} -> {fmt(item16_new)}")
        print(f"[compute] item22후 = {item22_new:.4f} -> {fmt(item22_new)}")

        # self-check: identities close exactly with the new values
        r6 = (it17 + it18 + it19 + it20 + it21) - item15_new - item16_new
        r5 = item15_new - item22_new + it23 - it14
        if abs(r6) > 1e-6 or abs(r5) > 1e-6:
            raise SystemExit(f"ABORT: {CODE} {quarter} self-check failed R6={r6} R5={r5}")

        for it, new_val in ((15, item15_new), (16, item16_new), (22, item22_new)):
            before = items[it][KEY_VALUE_POST]
            items[it][KEY_VALUE_POST] = fmt(new_val)
            all_census.append((quarter, it, before, items[it][KEY_VALUE_POST]))

    print("\n=== BEFORE / AFTER CENSUS ===")
    for quarter, item, before, after in all_census:
        print(f"  {quarter} item{item}후: {before!r} -> {after!r}")

    after_n = len(data)
    if after_n != before_n:
        raise SystemExit(f"ABORT: row count changed {before_n} -> {after_n}, refusing to save")

    save(data)
    print(f"\nsaved {after_n} rows")

    data2 = load()
    if len(data2) != before_n:
        raise SystemExit(f"VERIFY FAIL: row count on disk {len(data2)} != {before_n}")
    ok = True
    for quarter, item, _before, new_val in all_census:
        r = find_row(data2, CODE, quarter, item)
        if r.get(KEY_VALUE_POST) != new_val:
            print(f"VERIFY FAIL: {quarter} item{item} -> {r.get(KEY_VALUE_POST)!r} (want {new_val!r})")
            ok = False
    print("VERIFY:", "ALL OK" if ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
