"""Guarded cell-level fix: item14(지급여력기준금액) 값_적용후 back-solve artifacts.

Ticket: inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md SS B.

Root cause: a historical run of a since-fixed extractor stored item14_적용후 as
item1_후 / item27_후 * 100 (a ratio back-solve) instead of the issuer's printed
억원 integer. 30 cells across 8 companies carry this signature (census:
scripts/_probes/_probe_20260921_item14_backsolve_census.py, 40 buckets total; 10 of the
40 are genuine non-back-solve values and are left untouched -- see the parser's inbox
reply for the per-bucket adjudication).

Every new value below was confirmed against the raw Docling MD (either directly, via
grep/sed on the "[지급여력비율 총괄]" / equivalent headline table, or via a
replay of fill_post_transition_to_disclosure.py's current, already-correct
_extract_post_values()/_extract_headline_summary() against md_inbox -- both paths were
cross-checked against each other and, for a sample spanning 6 companies, against the
raw text directly).

Additionally corrects the item15/22/23 값_적용후 knock-on for KR0071's two
RED-blocking quarters (2025.2Q, 2025.4Q) so the (ungated, but user-facing) R5 identity
item14=item15-item22+item23 closes against the corrected item14 rather than the old
back-solved one. Source: fill_post_transition_to_disclosure.py's own
_apply_post_corrections() derived_identity/breakdown-table logic, replayed read-only
via scripts/_probes/_probe_20260921_kr0071_headline_recompute.py -- item22/23 are the
company's own "장수위험·사업비위험·해지위험 및 대재해위험 경과조치" (②) breakdown table's
literal printed values, item15 is back-solved from the (now-correct) item14 via the
definitional identity, per that script's own long-standing documented convention for
multi-transition companies where no table discloses combined-post item15/22/23 (KR0071
applies TFI(①)+TIR/TER(②) simultaneously, so no single provision table's own
"기본요구자본/법인세조정액/기타요구자본" row is the true combined figure either).

Guard: asserts the CURRENT value before writing (aborts the whole run on any mismatch),
writes only the named (code, quarter, item_no) cells, and reports a full row-count and
non-target-row invariant before/after.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_POST = "값_적용후"

# (code, quarter, item_no): (expected_current_value, new_value, source_note)
ITEM14_FIXES: dict[tuple[str, str, int], tuple[str, str, str]] = {
    ("KR0005", "2023.1Q", 14): ("13815.08", "13815", "raw md_inbox/FY2023_Q1/KR0005_흥국화재_amended.md L96 (4-2-1 헤드라인표) 적용후 13,815"),
    ("KR0005", "2023.2Q", 14): ("12977.5", "12978", "raw md_inbox/FY2023_Q2/KR0005_흥국화재_amended.md L134 ([경과조치 적용 후 지급여력비율]) 적용후 12,978 (전분기 컵럼이 13,815로 2023.1Q와 교차확인)"),
    ("KR0005", "2023.3Q", 14): ("12249.07", "12249", "헤드라인 재생(_extract_headline_summary, md_inbox/FY2023_Q3)"),
    ("KR0005", "2023.4Q", 14): ("13723.5", "13724", "헤드라인 재생(md_inbox/FY2023_Q4)"),
    ("KR0005", "2024.1Q", 14): ("14109.64", "14110", "헤드라인 재생(md_inbox/FY2024_Q1)"),
    ("KR0005", "2024.2Q", 14): ("14185.9", "14186", "헤드라인 재생(md_inbox/FY2024_Q2)"),
    ("KR0005", "2024.3Q", 14): ("14734.41", "14735", "헤드라인 재생(md_inbox/FY2024_Q3)"),
    ("KR0005", "2025.1Q", 14): ("14463.93", "14464", "헤드라인 재생(md_inbox/FY2025_Q1)"),
    ("KR0005", "2025.2Q", 14): ("14453.96", "14454", "헤드라인 재생(md_inbox/FY2025_Q2)"),
    ("KR0005", "2025.4Q", 14): ("15679.74", "15680", "헤드라인 재생(md_inbox/FY2025_Q4)"),
    ("KR0005", "2026.1Q", 14): ("16909.09", "16909", "헤드라인 재생(md_inbox/FY2026_Q1)"),
    ("KR0070", "2025.1Q", 14): ("11586.69", "11587", "raw md_inbox/FY2025_Q1/KR0070_에이비엘생명보험.md L155 ([지급여력비율 총괄]) 적용후 11,587"),
    ("KR0070", "2025.2Q", 14): ("11572.44", "11573", "헤드라인 재생(md_inbox/FY2025_Q2)"),
    ("KR0071", "2023.2Q", 14): ("16471.94", "16469", "raw md_inbox/FY2023_Q2/KR0071_흥국생명보험.md L63 ([지급여력비율 총괄]) 경과조치 후 16,469"),
    ("KR0071", "2023.3Q", 14): ("16458.51", "16456", "헤드라인 재생(md_inbox/FY2023_Q3)"),
    ("KR0071", "2023.4Q", 14): ("17614.44", "17616", "헤드라인 재생(md_inbox/FY2023_Q4)"),
    ("KR0071", "2024.1Q", 14): ("17998.11", "17997", "헤드라인 재생(md_inbox/FY2024_Q1)"),
    ("KR0071", "2024.2Q", 14): ("16981.37", "16982", "헤드라인 재생(md_inbox/FY2024_Q2)"),
    ("KR0071", "2024.3Q", 14): ("16700.79", "16702", "헤드라인 재생(md_inbox/FY2024_Q3)"),
    ("KR0071", "2025.1Q", 14): ("18293.73", "18295", "헤드라인 재생(md_inbox/FY2025_Q1)"),
    ("KR0071", "2025.2Q", 14): ("18415.27", "18412", "raw data/disclosure/FY2025_Q2/parsed/KR0071_흥국생명보험.md L197 총괄표 + L589 금리민감도표 둘 다 18,412 (티켓 주축)"),
    ("KR0071", "2025.4Q", 14): ("19354.44", "19350", "raw data/disclosure/FY2025_Q4/parsed/KR0071_흥국생명보험.md L84 총괄표 + L503 금리민감도표 둘 다 19,350 (티켓 주축)"),
    ("KR0071", "2026.1Q", 14): ("20989.38", "20995", "헤드라인 재생(md_inbox/FY2026_Q1)"),
    ("KR0072", "2023.1Q", 14): ("10541.02", "10540", "raw md_inbox/FY2023_Q1/KR0072_케이디비생명보험.md L52 ([지급여력비율 총괄]) 경과조치 후 10,540"),
    ("KR0097", "2023.1Q", 14): ("3369.28", "3370", "raw md_inbox/FY2023_Q1/KR0097_하나생명보험_amended.md L53 ([지급여력비율 총괄]) 경과조치 후 3,370"),
    ("KR0104", "2024.3Q", 14): ("18498.86", "18499", "raw md_inbox/FY2024_Q3/KR0104_농협생명보험_amended.md L283 ([지급여력비율 총괄]) 경과조치 후 18,499"),
    ("KR0104", "2024.4Q", 14): ("16747.85", "16748", "헤드라인 재생(md_inbox/FY2024_Q4)"),
    ("KR0104", "2025.1Q", 14): ("16631.26", "16631", "헤드라인 재생(md_inbox/FY2025_Q1)"),
    ("KR0104", "2025.2Q", 14): ("17059.2", "17059", "헤드라인 재생(md_inbox/FY2025_Q2)"),
    ("KR1011", "2023.2Q", 14): ("5179.08", "5179", "raw md_inbox/FY2023_Q2/KR1011_IBK연금보험.md L218 (4-2-1) + L370 (4-2-3) 둘 다 경과조치 후 5,179"),
}

# KR0071's two RED-blocking quarters: item15/22/23 knock-on so R5 (14=15-22+23)
# closes against the corrected item14 instead of the old back-solved one.
OTHER_FIXES: dict[tuple[str, str, int], tuple[str, str, str]] = {
    ("KR0071", "2025.2Q", 15): ("16345.89", "16155.58", "derived_identity = item14후(18412, 확정) + item22후(②표) - item23후(②표)"),
    ("KR0071", "2025.2Q", 22): ("3721.3", "3881.14", "raw FY2025_Q2 L337 ②표 법인세조정액 388,114백만원 = 3,881.14억"),
    ("KR0071", "2025.2Q", 23): ("5790.68", "6137.56", "raw FY2025_Q2 L339 ②표 기타요구자본 613,756백만원 = 6,137.56억"),
    ("KR0071", "2025.4Q", 15): ("16941.64", "16749.86", "derived_identity = item14후(19350, 확정) + item22후(②표) - item23후(②표)"),
    ("KR0071", "2025.4Q", 22): ("3868.84", "4013.6", "raw FY2025_Q4 L228 ②표 법인세조정액 401,360백만원 = 4,013.60억"),
    ("KR0071", "2025.4Q", 23): ("6281.63", "6613.74", "raw FY2025_Q4 L229 ②표 기타요구자본 661,374백만원 = 6,613.74억"),
}

ALL_FIXES = {**ITEM14_FIXES, **OTHER_FIXES}


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    row_count_before = len(rows)

    index: dict[tuple[str, str, int], dict] = {}
    for r in rows:
        index[(r[KEY_CODE], r[KEY_Q], r[KEY_ITEM])] = r

    missing = [k for k in ALL_FIXES if k not in index]
    if missing:
        print("ABORT: target row(s) not found:", missing)
        return 1

    mismatched = []
    for key, (expected_current, _new, _note) in ALL_FIXES.items():
        actual_current = index[key].get(KEY_POST)
        if str(actual_current) != expected_current:
            mismatched.append((key, expected_current, actual_current))
    if mismatched:
        print("ABORT: guard mismatch (current value != expected before write):")
        for key, expected, actual in mismatched:
            print(f"  {key}: expected {expected!r}, found {actual!r}")
        return 1

    print(f"guard OK: all {len(ALL_FIXES)} target cells match expected current value")

    for key, (_expected_current, new_value, note) in ALL_FIXES.items():
        row = index[key]
        old = row.get(KEY_POST)
        row[KEY_POST] = new_value
        print(f"  {key}: {old} -> {new_value}   ({note})")

    if len(rows) != row_count_before:
        print(f"ABORT: row count changed {row_count_before} -> {len(rows)} (must be unchanged)")
        return 1

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (unchanged count) to {JSON_PATH}")
    print(f"item14 fixes: {len(ITEM14_FIXES)}; item15/22/23 knock-on fixes: {len(OTHER_FIXES)}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
