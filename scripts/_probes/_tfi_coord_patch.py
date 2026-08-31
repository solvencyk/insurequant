# -*- coding: utf-8 -*-
"""Coordinator-approved overwrite of 17 item47/48/50/51/52 cells -- each one
individually raw-confirmed (see the accompanying report). This is NOT the
general fill_tfi_table_to_disclosure.py append-only path: every target here
already has an existing, wrong value, and the coordinator explicitly
authorized replacing it once raw-verified. Safety: each target asserts the
CURRENT value matches what was true when I verified it (protects against a
concurrent session already having fixed or further changed it) before
writing; anything that doesn't match is skipped and reported, not forced.
"""
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "kics_disclosure.json"

# (code, quarter, item_no, expected_current_pre, expected_current_post, new_pre, new_post, evidence)
TARGETS = [
    ("KR0051", "2026.2Q", 48, "17", None, "262", "262",
     "md_inbox/FY2026_Q2/KR0051_신한이지손해보험.md L382-383 '보완자본한도 262 262' (단위 억원, 배율 불필요)"),
    ("KR0051", "2026.2Q", 52, "1131", None, "1197", "1197",
     "md_inbox/FY2026_Q2/KR0051_신한이지손해보험.md L380 '지급여력금액 1,197 1,197' (단위 억원)"),
    ("KR0068", "2026.2Q", 48, "166945", None, "75055.83", "75055.83",
     "md_inbox/FY2026_Q2/KR0068_한화생명.md '보완자본 한도 7,505,583 7,505,583' 백만원=75055.83억"),
    ("KR0071", "2026.2Q", 48, "21329", None, "14131.73", "14131.73",
     "md_inbox/FY2026_Q2/KR0071_흥국생명보험.md '보완자본 한도 1,413,173 1,413,173' 백만원=14131.73억"),
    ("KR0072", "2026.2Q", 48, "16273", None, "7764.66", "7764.66",
     "md_inbox/FY2026_Q2/KR0072_케이디비생명보험.md L333 '보완자본 한도 776,466 776,466' 백만원=7764.66억"),
    ("KR0073", "2026.2Q", 48, "80777", None, "52699.09", "52699.09",
     "md_inbox/FY2026_Q2/KR0073_교보생명보험.md '보완자본한도 5,269,909 5,269,909' 백만원=52699.09억"),
    ("KR0080", "2026.2Q", 48, "2735", None, "8215.65", "8215.65",
     "md_inbox/FY2026_Q2/KR0080_에이아이에이생명보험.md L378 '보완자본 한도 821,565 821,565' 백만원=8215.65억"),
    ("KR0097", "2026.2Q", 48, "8313", None, "3776.78", "3776.78",
     "md_inbox/FY2026_Q2/KR0097_하나생명보험.md L342 '보완자본 한도 377,678 377,678' 백만원=3776.78억"),
    ("KR0099", "2026.2Q", 48, "23531", None, "13586.09", "13586.09",
     "md_inbox/FY2026_Q2/KR0099_케이비라이프생명보험.md '보완자본 한도 1,358,609 1,358,609' 백만원=13586.09억"),
    ("KR0100", "2026.2Q", 48, "1621", None, "683.97", "683.97",
     "md_inbox/FY2026_Q2/KR0100_처브라이프생명보험.md L618 '보완자본 한도 68,397 68,397' 백만원=683.97억"),
    ("KR0104", "2026.2Q", 48, "50532", None, "17197.57", "11925.57",
     "md_inbox/FY2026_Q2/KR0104_농협생명보험.md '보완자본 한도 1,719,757 1,192,557' 백만원=17197.57/11925.57억(전후 다름)"),
    ("KR1098", "2026.2Q", 48, "0", None, "213.19", "213.19",
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md '보완자본 한도 21,319 21,319' 백만원=213.19억(대시 아닌 실값, unit-vote x0.01 검증됨: 같은 표 지급여력금액92,069백만=920.69억=기존item1=921과 정합)"),
    ("KR0029", "2025.2Q", 48, "0", None, "1279.06", "1279.06",
     "md_inbox/FY2025_Q2/KR0029_AIG손해보험.md L360 '보완자본 한도 127,906 127,906' 백만원=1279.06억(같은표 보완자본/한도적용전은 진짜 대시, 한도행만 실값)"),
    ("KR0029", "2025.3Q", 48, "59", None, "1277.76", "1277.76",
     "md_inbox/FY2025_Q3/KR0029_AIG손해보험.md L358 '보완자본 한도 127,776 ... 127,776' 백만원=1277.76억(기존59=보완자본5,870백만=58.70≈59 그대로 복사, item48이 아님)"),
    ("KR0073", "2025.1Q", 47, "33616.13", "33616.13", "33616.13", "22527.14",
     "md_inbox/FY2025_Q1/KR0073_교보생명보험.md L267 '보완자본한도적용전 3,361,613 2,252,714' 백만원 — 기존 적용후는 적용전 미러(오류), 원문은 전≠후"),
    ("KR0073", "2025.1Q", 50, "90163.65", "90163.65", "90163.65", "101252.64",
     "md_inbox/FY2025_Q1/KR0073_교보생명보험.md L265 '기본자본 9,016,365 10,125,264' 백만원 — 기존 적용후는 적용전 미러(오류)"),
    ("KR0073", "2025.1Q", 51, "40703.8", "40703.8", "40703.8", "29614.81",
     "md_inbox/FY2025_Q1/KR0073_교보생명보험.md L266 '보완자본 4,070,380 2,961,481' 백만원 — 기존 적용후는 적용전 미러(오류)"),
]

_raw_text_before = JSON_PATH.read_text(encoding="utf-8")
rows = json.loads(_raw_text_before)
index = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in rows}

print(f"loaded {len(rows)} rows, {len(index)} combos")
applied = []
skipped = []
for code, quarter, item_no, exp_pre, exp_post, new_pre, new_post, evidence in TARGETS:
    row = index.get((code, quarter, item_no))
    if row is None:
        skipped.append((code, quarter, item_no, "ROW_VANISHED (concurrent edit?)"))
        continue
    cur_pre = row.get("값")
    cur_post = row.get("값_적용후")
    def _f(x):
        try:
            return float(x) if x is not None else None
        except (TypeError, ValueError):
            return None
    pre_ok = (exp_pre is None and cur_pre is None) or (_f(cur_pre) is not None and _f(exp_pre) is not None and abs(_f(cur_pre) - _f(exp_pre)) < 0.01)
    post_ok = (exp_post is None and cur_post is None) or (_f(cur_post) is not None and _f(exp_post) is not None and abs(_f(cur_post) - _f(exp_post)) < 0.01)
    if not (pre_ok and post_ok):
        skipped.append((code, quarter, item_no, f"CURRENT_VALUE_DRIFTED: expected pre={exp_pre!r} post={exp_post!r}, now pre={cur_pre!r} post={cur_post!r}"))
        continue
    old_pre, old_post = row.get("값"), row.get("값_적용후")
    row["값"] = new_pre
    row["값_적용후"] = new_post
    applied.append((code, quarter, item_no, old_pre, old_post, new_pre, new_post, evidence))

print(f"\napplied: {len(applied)}  skipped: {len(skipped)}")
for s in skipped:
    print("  SKIPPED:", s)

if applied:
    backup_path = JSON_PATH.with_name(JSON_PATH.name + ".bak_pre_coord_overwrite")
    backup_path.write_text(_raw_text_before, encoding="utf-8")
    print(f"backup written: {backup_path}")
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows to {JSON_PATH}")

print("\n=== APPLIED TABLE ===")
for a in applied:
    print(f"{a[0]}\t{a[1]}\titem{a[2]}\told(pre={a[3]!r},post={a[4]!r})\tnew(pre={a[5]!r},post={a[6]!r})")
    print(f"   근거: {a[7]}")
