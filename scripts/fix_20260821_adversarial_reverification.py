# -*- coding: utf-8 -*-
"""Adversarial reverification response (inbox `20260821T0400Z`, items (1)-(4)).

Every value below was read directly from raw PDF (fitz text + pdfplumber word-position
reconstruction for jumbled multi-column tables), independent of the ticket's own
transcriptions and independent of the docling MD. See the parser session report for
the full raw citations per cell; short form repeated in comments below.

Usage: ...python scripts/fix_20260821_adversarial_reverification.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

LABELS = {
    29: "1-1. 사망위험액", 30: "1-2. 장수위험액", 31: "1-3. 장해·질병위험액",
    32: "1-4. 장기재물·기타위험액", 33: "1-5. 해지위험액", 34: "1-6. 사업비위험액",
    35: "1-7. 대재해위험액", 40: "3-5. 자산집중위험액",
}

# (code, quarter, item) -> {"값": (guard, new)?, "값_적용후": (guard, new)?}
# guard=None for a column means "leave untouched" (not part of this fix).
UPDATES = {
    # ---- (1) 한화손해 KR0002 2024.2Q: REVERT item1후 + correct item2/3후 ----
    # raw p14 "공통적용 경과조치": 기본자본 2,638,159->2,872,265 / 보완자본 2,715,975->2,481,870
    # (sums to 5,354,135 = item1전, tier-reclass only). raw p10 headline: 경과조치 후
    # 지급여력금액=53,541 (후=전). Same convention independently confirmed for 2024.1Q/2024.3Q.
    ("KR0002", "2024.2Q", 1): {"값_적용후": ("53537.72", "53541")},
    ("KR0002", "2024.2Q", 2): {"값_적용후": ("26377.97", "28722.65")},
    ("KR0002", "2024.2Q", 3): {"값_적용후": ("27159", "24818.7")},

    # ---- (2) 롯데손해 KR0003 2026.1Q item29-35후: raw p24 ②표 (own read, fitz) ----
    # 사망 103,317->103,317 / 장수 33->19(unchanged, ok) / 장해질병 1,003,161->1,003,161 /
    # 장기재물기타 51,528->51,528 / 해지 922,386->343,533 / 사업비 236,085->47,394 /
    # 대재해 20,710->5,298 (30/35 already matched master, untouched)
    ("KR0003", "2026.1Q", 29): {"값_적용후": ("1033.16", "1033.17")},
    ("KR0003", "2026.1Q", 31): {"값_적용후": ("10031.49", "10031.61")},
    ("KR0003", "2026.1Q", 32): {"값_적용후": ("515.27", "515.28")},
    ("KR0003", "2026.1Q", 33): {"값_적용후": ("3435.29", "3435.33")},
    ("KR0003", "2026.1Q", 34): {"값_적용후": ("473.93", "473.94")},

    # ---- (3) 교보생명 KR0073 2026.1Q item29-35: rows never existed. raw p15 ②표 ----
    # (fitz) both 전/후 columns read directly (전=후 for legs outside TIR scope):
    # 사망 782,849/782,849 · 장수 677,141/257,378 · 장해질병 2,471,949/2,471,949 ·
    # 장기재물기타 0/0 · 해지 3,879,178/1,266,318 · 사업비 951,553/159,550 ·
    # 대재해 334,349/105,385 (백만원). R7-sqrt reconciles item17전=57752(diff -0.09) and
    # item17후=32226.72(diff -0.01) to the tenth of a percent -- high confidence.
    # NOTE: exemption entry ("KR0073","2026.1Q") in _AFTER_SUBRISK_NOT_DISCLOSED claims
    # "섹션 자체 없음" -- false, raw p15 has the full table. Registry edit is validation's
    # call (not made here); values are loaded regardless per "틀린 값을 싣느니 빈 칸"
    # (empty was itself wrong -- raw has real values).
    ("KR0073", "2026.1Q", 29): {"값": (None, "7828.49"), "값_적용후": (None, "7828.49")},
    ("KR0073", "2026.1Q", 30): {"값": (None, "6771.41"), "값_적용후": (None, "2573.78")},
    ("KR0073", "2026.1Q", 31): {"값": (None, "24719.49"), "값_적용후": (None, "24719.49")},
    ("KR0073", "2026.1Q", 32): {"값": (None, "0"), "값_적용후": (None, "0")},
    ("KR0073", "2026.1Q", 33): {"값": (None, "38791.78"), "값_적용후": (None, "12663.18")},
    ("KR0073", "2026.1Q", 34): {"값": (None, "9515.53"), "값_적용후": (None, "1595.5")},
    ("KR0073", "2026.1Q", 35): {"값": (None, "3343.49"), "값_적용후": (None, "1053.85")},

    # ---- (4a) 신한이지 KR0051 2024.4Q: item30 row missing + items31-35 stored /100 wrong ----
    # raw p33 (pdfplumber row reconstruct, 단위:억원 -- already in 억원, NOT 백만원):
    # 사망0 · 장수"-"(=0) · 장해질병4 · 장기재물기타1 · 해지2 · 사업비2 · 대재해2 (both cols,
    # non-applier mirror). Master had 31-35 pre-loaded at 1/100 scale (0.04/0.01/0.02/0.02/0.02)
    # by an earlier pass that wrongly treated this page as 백만원. R7-sqrt of the corrected
    # [0,0,4,1,2,2,2] reconciles item17=7 (diff 0.21); the stored /100 values give diff -6.93
    # (fails even the loose dyn5% tolerance) -- confirms scale bug. Cross-quarter census
    # (item17 vs sum-of-subs ratio) confirms 2024.4Q is the only outlier quarter for KR0051.
    ("KR0051", "2024.4Q", 30): {"값": (None, "0"), "값_적용후": (None, "0")},
    ("KR0051", "2024.4Q", 31): {"값": ("0.04", "4"), "값_적용후": ("0.04", "4")},
    ("KR0051", "2024.4Q", 32): {"값": ("0.01", "1"), "값_적용후": ("0.01", "1")},
    ("KR0051", "2024.4Q", 33): {"값": ("0.02", "2"), "값_적용후": ("0.02", "2")},
    ("KR0051", "2024.4Q", 34): {"값": ("0.02", "2"), "값_적용후": ("0.02", "2")},
    ("KR0051", "2024.4Q", 35): {"값": ("0.02", "2"), "값_적용후": ("0.02", "2")},

    # ---- (4b) 신한이지 KR0051 2023.1Q: item29-35 rows never existed ----
    # raw p10 (pdfplumber row reconstruct; get_text() column order was jumbled and would
    # have mis-assigned these -- pdfplumber word positions resolved it), 단위:백만원,
    # non-applier mirror (전=후), R7-sqrt reconciles item17=2.93 exactly (diff 0.00):
    # 사망17 · 장수"-" · 장해질병146 · 장기재물기타"-" · 해지166 · 사업비67 · 대재해40 (백만원)
    ("KR0051", "2023.1Q", 29): {"값": (None, "0.17"), "값_적용후": (None, "0.17")},
    ("KR0051", "2023.1Q", 30): {"값": (None, "0"), "값_적용후": (None, "0")},
    ("KR0051", "2023.1Q", 31): {"값": (None, "1.46"), "값_적용후": (None, "1.46")},
    ("KR0051", "2023.1Q", 32): {"값": (None, "0"), "값_적용후": (None, "0")},
    ("KR0051", "2023.1Q", 33): {"값": (None, "1.66"), "값_적용후": (None, "1.66")},
    ("KR0051", "2023.1Q", 34): {"값": (None, "0.67"), "값_적용후": (None, "0.67")},
    ("KR0051", "2023.1Q", 35): {"값": (None, "0.4"), "값_적용후": (None, "0.4")},

    # ---- (4c) AIA KR0080 2023.3Q: item19 wrong (scale/parse error, both cols) + item40 missing ----
    # raw p9 headline ("3. 시장위험액 3,779"), p11 ②표 (전 col, 377,947백만=3,779.47억),
    # p12 ③표 (전=후 both 377,947, footnote "주식위험 경과조치를 적용하지 않아 전후 동일") --
    # three independent citations all say 3,779, master had 3643. MARKET_M-sqrt of the
    # existing children [2112.67,1947.3,1032.5,649.08,0] gives 3779.47 (diff 0.47 vs the
    # 3779 fix; diff 136.47 vs the stored 3643) -- matches the tight-reconciliation pattern
    # of every neighboring quarter (all diff <0.5) instead of the loose 5% band that let
    # 3643 slide through undetected. item40(자산집중위험) row never existed; raw states "-"/"-".
    ("KR0080", "2023.3Q", 19): {"값": ("3643", "3779"), "값_적용후": ("3643", "3779")},
    ("KR0080", "2023.3Q", 40): {"값": (None, "0"), "값_적용후": (None, "0")},
}


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    present = {(r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호", -1))): r for r in data}

    modify_done, modify_skip = [], []
    insert_plan = []  # (code, quarter, item, row_dict)

    for (c, q, it), cols in UPDATES.items():
        key = (c, q, it)
        row = present.get(key)
        if row is None:
            # every column for a brand-new row must have guard=None
            if not all(guard is None for guard, _ in cols.values()):
                modify_skip.append((c, q, it, "행 없음인데 guard!=None 지정됨(설정오류)"))
                continue
            sib = next((r for r in data if r["원보험사코드"] == c and r["공시분기"] == q), None)
            if sib is None:
                modify_skip.append((c, q, it, "형제 행 없음(회사·분기 미존재)"))
                continue
            new_row = {
                "원보험사코드": c, "원수사명": sib.get("원수사명", c), "티커": sib.get("티커", "X"),
                "생손보여부": sib.get("생손보여부", ""), "항목번호": it,
                "항목명": LABELS.get(it, ""), "공시분기": q,
                "값": cols["값"][1], "값_적용후": cols["값_적용후"][1],
            }
            insert_plan.append((c, q, it, new_row))
            modify_done.append((c, q, it, "(신설)", cols["값"][1], "값+값_적용후"))
            continue
        # existing row: apply per-column guarded updates
        for col, (guard, new) in cols.items():
            if guard is None:
                continue  # not touching this column on an existing row (shouldn't happen given UPDATES above)
            cur = row.get(col)
            # some legacy cells store the number as a bare JSON int/float rather than a
            # string (KR0080 item19 is one) -- compare value-equivalence, not repr-equality.
            if cur != guard and str(cur) != guard:
                modify_skip.append((c, q, it, f"{col} 현재값 {cur!r} != guard {guard!r}"))
                continue
            modify_done.append((c, q, it, cur, new, col))
            if not dry:
                row[col] = new  # normalize to string form on write (majority convention)

    # Perform insertions one at a time, recomputing the insertion point fresh each time
    # (avoids the multi-insert index-drift bug noted in TODO 2026-08-21).
    inserted = []
    if not dry:
        for c, q, it, new_row in insert_plan:
            if any(r.get("원보험사코드") == c and r.get("공시분기") == q
                   and int(r.get("항목번호", -1)) == it for r in data):
                continue  # raced into existence since we planned -- skip, don't duplicate
            idxs = [i for i, r in enumerate(data) if r["원보험사코드"] == c and r["공시분기"] == q]
            if not idxs:
                continue
            at = max(idxs) + 1
            for i in idxs:
                if int(data[i]["항목번호"]) > it:
                    at = i
                    break
            data.insert(at, new_row)
            inserted.append((c, q, it))

    print(f"{'DRY-RUN ' if dry else ''}modify/insert-plan {len(modify_done)} · skipped {len(modify_skip)}")
    for x in modify_done:
        print("  ", x)
    for x in modify_skip:
        print("  SKIP", x)
    if not dry:
        print(f"actually inserted: {len(inserted)} -> {inserted}")

    total_planned = len(UPDATES)
    total_applied = len(modify_done)
    if not dry and modify_skip:
        print(f"ABORT: {len(modify_skip)} guard mismatch(es), refusing partial write. Investigate before rerunning.")
        return 1
    if not dry:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}  (planned {total_planned}, applied {total_applied})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
