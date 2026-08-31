# -*- coding: utf-8 -*-
"""UPSERT fix (2026-09-01) -- 흥국화재(KR0005) 2025.3Q / 2026.2Q TRANSITION_AFTER_MMULT_MISMATCH.

inbox/parser/20260901T0405Z__validation__KR0005_2025.3Q_2026.2Q__irr_transition_leg_not_merged.md

Root cause: item19후(시장위험액 combined)는 ③ 주식위험 경과조치 표의 OWN 단독 소계였다 --
그 표는 금리위험(item36)을 PRE 그대로 두고 주식(item37)만 움직인다. 흥국화재는 ③(EQ)뿐 아니라
④ 금리위험 경과조치(INT axis)도 동시 신청했는데, item36후가 ④ 표를 반영하지 않고 PRE를 그대로
복사(mirror)하고 있었다 -- 두 분기 모두 "item36후 == item36전" 인 것이 그 지문.

같은 회사의 2024.4Q에 이미 있었던 같은 버그(scripts/fix_20260821_kr0005_2024q4_market_combined.py)
와 동일 methodology -- R4/MARKET_M 은 kics_json_rules.py 에서 import(재타이핑 금지).

Raw source (md_inbox/FY2026_Q2/KR0005_흥국화재.md L493-, md_inbox/FY2025_Q3/KR0005_흥국화재.md
L258- -- docling 이 이 표를 놓친 게 아니라 fill 단계가 병합을 안 한 것, extraction 갭이 아니라
merge 갭이라 raw PDF 재확인 불필요, MD 값이 fitz 이전 세션들의 raw-verified 값과도 일치):

  2026.2Q ④ 금리위험 경과조치 표: 금리위험 196,226 -> 아님(오타 방지, 실제 2026.2Q 값):
    금리위험 125,200 -> "-"(대시, 명시적 0) / 시장위험액 454,489 -> 397,646(=3976.46억, 주식/부동산/
    외환/집중은 PRE 그대로 336,516/148,451/38,404/-) -- 다른 leaf 는 PRE 유지가 이 표(INT축 단독)의
    정의이므로, item37(주식, POST)은 ③표 값(1912.77)을 그대로 쓰고 item36(금리, POST)만 이 표에서
    가져와 MARKET_M 으로 재결합한다.
  2025.3Q ④ 금리위험 경과조치 표: 금리위험 196,226 -> 50,828(=508.28억, 직접 인쇄, 대시 아님) /
    시장위험액 582,973 -> 510,368.

item37-40후는 이미 마스터에 올바르게 적재돼 있다(③표 POST 값과 정확히 일치, 확인 완료) --
이 스크립트는 item36후·item19후만 바꾼다.

item15/16/22 는 건드리지 않는다 (owner 판단 대기, 별도 보고 -- item19 변경의 부작용으로 R6_item16
이 새로 RED 가 된다는 사실은 sandbox 게이트 실행으로 확인했고 inbox 답변에 수치로 보고한다).

Computed via scripts/_probes/probe_20260901_kr0005_irr_leg.py (본 스크립트와 쌍, 동일 계산 재현).
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
from solvency.validation.kics_json_rules import MARKET_M, _diversified_sqrt  # noqa: E402

JSON_PATH = ROOT / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_QUARTER = "공시분기"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"

CODE = "KR0005"

# quarter -> {item36_post(억원, raw-read), item37..40_post(억원, 마스터에 이미 정확)}
QUARTERS = {
    "2025.3Q": {
        "item36_post": 508.28,    # ④표 직접 인쇄값 (50,828백만)
        "item37_post": 2954.34,   # ③표 POST (295,434백만) -- 마스터 기존값과 동일, sanity only
        "item38_post": 1035.06,
        "item39_post": 328.89,
        "item40_post": 0.0,
        "item19_before_expected": "4382.73",  # ③-only marginal (마스터 현재값, sanity)
        "item36_before_expected": "1962.26",  # PRE 그대로 mirror 된 오염값 (마스터 현재값, sanity)
    },
    "2026.2Q": {
        "item36_post": 0.0,       # ④표 대시(-) = 명시적 0 (역산으로도 재확인: a=0 root)
        "item37_post": 1912.77,   # ③표 POST (191,277백만) -- 마스터 기존값과 동일, sanity only
        "item38_post": 1484.51,
        "item39_post": 384.04,
        "item40_post": 0.0,
        "item19_before_expected": "3358.88",
        "item36_before_expected": "1252",
    },
}


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
    s = f"{x:.2f}"
    return s


def main():
    data = load()
    before_n = len(data)
    print(f"loaded {before_n} rows")

    all_census = []
    for quarter, cfg in QUARTERS.items():
        print(f"\n=== {CODE} {quarter} ===")

        # sanity: item37-40후 already correct in master (this script does not touch them)
        for item, key in ((37, "item37_post"), (38, "item38_post"),
                          (39, "item39_post"), (40, "item40_post")):
            row = find_row(data, CODE, quarter, item)
            if row is None:
                raise SystemExit(f"ABORT: {CODE} {quarter} item{item} row not found")
            got = row.get(KEY_VALUE_POST)
            want = cfg[key]
            got_f = float(got) if got not in (None, "") else None
            if got_f is None or abs(got_f - want) > 0.01:
                raise SystemExit(
                    f"ABORT: {CODE} {quarter} item{item}후 = {got!r}, expected ~{want} "
                    "(sanity mismatch -- this script assumes item37-40후 already correct)")
            print(f"[sanity] item{item}후 = {got!r} (unchanged, leaf already correct)")

        # sanity: item36/item19 currently at the expected (buggy) mirror/marginal values
        row36 = find_row(data, CODE, quarter, 36)
        row19 = find_row(data, CODE, quarter, 19)
        if row36 is None or row19 is None:
            raise SystemExit(f"ABORT: {CODE} {quarter} item36/item19 row missing")
        if str(row36.get(KEY_VALUE_POST)) != cfg["item36_before_expected"]:
            raise SystemExit(
                f"ABORT: {CODE} {quarter} item36후 = {row36.get(KEY_VALUE_POST)!r}, "
                f"expected {cfg['item36_before_expected']!r} before fix -- master may have "
                "already changed since this script was written")
        if str(row19.get(KEY_VALUE_POST)) != cfg["item19_before_expected"]:
            raise SystemExit(
                f"ABORT: {CODE} {quarter} item19후 = {row19.get(KEY_VALUE_POST)!r}, "
                f"expected {cfg['item19_before_expected']!r} before fix")
        print(f"[sanity] item36후 = {row36.get(KEY_VALUE_POST)!r} (buggy PRE-mirror, about to fix)")
        print(f"[sanity] item19후 = {row19.get(KEY_VALUE_POST)!r} (buggy EQ-only marginal, about to fix)")

        # combine item19 via MARKET_M over the NOW-correct 5 leaves
        v19 = np.array([cfg["item36_post"], cfg["item37_post"], cfg["item38_post"],
                        cfg["item39_post"], cfg["item40_post"]])
        item19_new = _diversified_sqrt(v19, MARKET_M)
        print(f"[compute] item19후 (combined via MARKET_M) = {item19_new:.4f}")

        item36_before = row36.get(KEY_VALUE_POST)
        item19_before = row19.get(KEY_VALUE_POST)
        row36[KEY_VALUE_POST] = fmt(cfg["item36_post"])
        row19[KEY_VALUE_POST] = fmt(item19_new)
        all_census.append((quarter, 36, item36_before, row36[KEY_VALUE_POST]))
        all_census.append((quarter, 19, item19_before, row19[KEY_VALUE_POST]))

    print("\n=== BEFORE / AFTER CENSUS ===")
    for quarter, item, before, after in all_census:
        print(f"  {quarter} item{item}후: {before!r} -> {after!r}")

    after_n = len(data)
    if after_n != before_n:
        raise SystemExit(f"ABORT: row count changed {before_n} -> {after_n}, refusing to save")

    save(data)
    print(f"\nsaved {after_n} rows")

    data2 = load()
    ok = True
    for quarter, item, _before, new_val in all_census:
        r = find_row(data2, CODE, quarter, item)
        if r.get(KEY_VALUE_POST) != new_val:
            print(f"VERIFY FAIL: {quarter} item{item} -> {r.get(KEY_VALUE_POST)!r} (want {new_val!r})")
            ok = False
    print("VERIFY:", "ALL OK" if ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
