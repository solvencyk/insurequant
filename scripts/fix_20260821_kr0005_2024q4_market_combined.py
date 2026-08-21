# -*- coding: utf-8 -*-
"""UPSERT fix (2026-08-21) — 흥국화재(KR0005) 2024.4Q TRANSITION_AFTER_MMULT_MISMATCH.

Downloader delivered the CORRECT raw file today (data/disclosure/FY2024_Q4/raw/KR0005_흥국화재.pdf,
96p, image-only data tables — the old DART 사업보고서 that produced the false
"image-only/미공시" exemption is archived at data/_archive/20260821T044328Z/). Rendered at
150dpi (fitz get_pixmap) and read visually; fitz text search on this file also returns 0 hits
for "경과조치" (rasterized tables) so this was NOT reparsed from text.

Raw pages read (page numbers = PDF page index, confirmed via section headers):
  p37   [지급여력비율 총괄]              경과조치 전 154.01% / 후 199.56%  (coordinator-verified)
  p42   ② 장수·사업비·해지·대재해 경과조치 (IR axis)  생명장기위험액후=1,502,133백만=15021.33억
                                                        일반손해위험액후=73,235백만=732.35억
  p42-43 ③ 주식위험 경과조치 (EQ axis)   주식위험후=218,010백만=2180.10억 (다른 leaf 불변)
  p44   ④ 금리위험 경과조치 (INT axis)   금리위험후=39,935백만=399.35억 (다른 leaf 불변)
  p44   5-2-3 최근 3개 사업연도 주요 변동요인 (단위 억원): 경과조치후 지급여력기준금액=13,978
        (=p37 총괄과 일치, item1후=27,894 불변(TAC 미신청) -> item27=27894/13978*100=199.56% 재현)

Root cause of the RED: items 36-40후(금리/주식/부동산/외환/집중 leaf) were ALREADY correct in
the master (matching this raw exactly) — the problem was item19후(시장위험액 combined), which had
been set to 386,081백만=3,860.81억, i.e. table③'s OWN isolated market-risk subtotal (which holds
the INT axis at its 전 value while only moving EQ). 흥국화재 elected BOTH EQ and INT
(`_TRANSITION_KIND["KR0005"] = {"IR","EQ","INT"}`), so the true combined item19후 must move BOTH
leaves simultaneously via MARKET_M — company discloses 4 separate single-axis tables, never a
joint one, matching the established combined-transition methodology (validation,
inbox/_resolved/20260821T0010Z: "선택경과조치 표는 자기 위험만 건드린다 -> 결합 leaf = 그 leaf를
줄인 표의 값, 나머지는 적용전").

Fix (computed via scripts/_probes/compute_kr0005_20260821.py, gate's own R4/MARKET_M imported):
  item19후 3860.81 -> 2801.44   (sqrt(MARKET_M . [36,37,38,39,40]후) — THE flagged RED)
  item15후 18618.66 -> 18129.96 (R4(17,18,19_new,20)후 + 21후 — re-derived so the R4 identity
                                  stays exact; leaving item15 untouched would just move the
                                  mismatch from item19 to item15)
  item16후 4874.83 -> 4304.17   (분산효과 = childrensum(17,18,19_new,20,21) - item15_new)
  item22후 4443.96 -> 4151.96   (법인세조정액 residual = item15_new - item14후(13978, UNCHANGED —
                                  already matches the disclosed headline exactly) + item23후(0))
Guards (all passed, see compute_kr0005_20260821.py output):
  - R4 reproduces 적용전 item15 (23492.98 vs master 23493, rounding-level)
  - combined item15_new (18129.96) < both 전(23493) and the INT-only-isolated table's own
    기본요구자본후 (23,075.55) — monotonicity (combining two benefits reduces more than either alone)
  - item27_post cross-check: 27894/13978*100 = 199.56 = the disclosed ratio exactly
items 17,18,20,21,36,37,38,39,40후 — UNCHANGED (already raw-verified correct).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_QUARTER = "공시분기"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"

CODE, QUARTER = "KR0005", "2024.4Q"

FIXES = {
    15: "18129.96",
    16: "4304.17",
    19: "2801.44",
    22: "4151.96",
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
        if r.get(KEY_CODE) == code and r.get(KEY_QUARTER) == quarter and r.get(KEY_ITEM) == item:
            return r
    return None


def main():
    data = load()
    print(f"loaded {len(data)} rows")

    # sanity: item14후 must already equal the disclosed anchor (13978) — we do NOT write item14.
    row14 = find_row(data, CODE, QUARTER, 14)
    if row14.get(KEY_VALUE_POST) != "13978":
        raise SystemExit(f"ABORT: item14후 expected '13978', found {row14.get(KEY_VALUE_POST)!r}")
    print(f"[sanity] item14후 = {row14.get(KEY_VALUE_POST)!r} (anchor, not modified)")
    for item in (17, 18, 20, 21, 36, 37, 38, 39, 40):
        r = find_row(data, CODE, QUARTER, item)
        print(f"[sanity] item{item}후 = {r.get(KEY_VALUE_POST)!r} (leaf, not modified)")

    census = []
    for item, new_val in FIXES.items():
        row = find_row(data, CODE, QUARTER, item)
        if row is None:
            raise SystemExit(f"ABORT: {CODE} {QUARTER} item{item} row not found")
        before = row.get(KEY_VALUE_POST)
        row[KEY_VALUE_POST] = new_val
        census.append((item, before, new_val))

    print("\n=== BEFORE / AFTER CENSUS ===")
    for item, before, after in census:
        print(f"  item{item}후: {before!r} -> {after!r}")

    save(data)
    print(f"\nsaved {len(data)} rows")

    data2 = load()
    ok = True
    for item, _before, new_val in census:
        r = find_row(data2, CODE, QUARTER, item)
        if r.get(KEY_VALUE_POST) != new_val:
            print(f"VERIFY FAIL: item{item} -> {r}")
            ok = False
    print("VERIFY:", "ALL OK" if ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
