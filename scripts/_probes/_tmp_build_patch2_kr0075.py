# -*- coding: utf-8 -*-
"""Build data/_derived/_patch2_2026q2_KR0075.json for the 47_tier2_census RED.

항목명 strings are copied programmatically from this company's own 2026.1Q rows
(already loaded, byte-correct) -- never hand-retyped, to avoid the U+318D vs
U+00B7 mismatch that got a previous patch rejected.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
MASTER = REPO / "kics_disclosure.json"
OUT = REPO / "data" / "_derived" / "_patch2_2026q2_KR0075.json"

CODE = "KR0075"
QUARTER = "2026.2Q"
REF_QUARTER = "2026.1Q"  # source of exact 항목명 strings for items 47/48/49


def _fmt(x: float) -> str:
    s = f"{x:.2f}"
    if s.endswith("0"):
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def main() -> int:
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    ref = {r["항목번호"]: r for r in data
           if r.get("원보험사코드") == CODE and r.get("공시분기") == REF_QUARTER}
    for n in (47, 48, 49, 53, 54):
        if n not in ref:
            print(f"ABORT: item{n} missing from {CODE} {REF_QUARTER} reference row")
            return 1

    # raw p21 "[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 관련" table
    # (md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L403-418, 단위 백만원, %):
    #   보완자본 한도 적용 전   23,386 / 23,386
    #   보완자본 한도          50,840 / 50,840
    #   해약환급금 부족분...초과분  10,631 / 10,631
    # /100 -> 억원. 전=후 (both columns print identical numbers, consistent with this
    # company's own p19 statement "당사는 경과조치 적용하고 있지 않음", already used to
    # justify mirroring 값_적용후=값 across items 1-46 in the prior patch for this
    # company/quarter -- data/_derived/_patch_2026q2_KR0075.json).
    RAW_EOK = {
        47: 23386 / 100,
        48: 50840 / 100,
        49: 10631 / 100,
        53: 0.0,
        54: 0.0,
    }

    evidence = (
        "PDF p21 / md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L403-418 "
        "'[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 관련' 표 "
        "(단위 백만원,%), 경과조치 적용 전 / 적용 후 두 컬럼 완전 동일: "
        "보완자본 한도 적용 전 23,386/23,386, 보완자본 한도 50,840/50,840, "
        "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 10,631/10,631 "
        "(/100 -> 억원). Verified against item14_적용전=1017 via the independent "
        "axis-D identity item48==item14_적용전x50%: 1016.80(raw TFI 지급여력기준금액 "
        "row, unrounded) x 0.5 = 508.40, exact match -- this disproves the previously "
        "stored item48=234, which was item3(보완자본)'s value miscopied into item48's "
        "cell (same label-matcher confusion already confirmed on KR0050/KR0095/KR0002: "
        "'보완자본 한도' vs '보완자본'). Composition check (axis B/_tier2_branch, "
        "target=item3=234): this company is a company-level INCL-scope filer "
        "(_tier2_i47_scope_map, 18/18 prior decisive quarters vote INCL, this bucket "
        "adds a 19th INCL vote) with debt=item47-item49=127.55 <= item48=508.40 (not "
        "capped), so the uncapped test |item3-item47|=|234-233.86|=0.14 <= tol(2.0) "
        "closes the identity directly (branch=I49_IN_I47_UNCAPPED, excess=0) -- item49 "
        "is NOT additive this quarter. This is NOT the CAPPED formula "
        "'item51==min(47,48)+49[+54]' verified on 한화손해(KR0002)/KR0050 -- that "
        "formula assumes the CAPPED branch, which does not apply to BNP카디프. It IS "
        "this company's own dominant historical pattern: item47==item51(TFI표 보완자본) "
        "exactly in 10 of its 13 prior loaded quarters (2023.1Q-2023.4Q, 2024.1Q, "
        "2024.2Q, 2025.2Q-2026.1Q); the 3 exceptions (2024.3Q/2024.4Q/2025.1Q) are "
        "already-documented TIER2_DUPLICATE_ROW/issuer-inconsistent exemptions in "
        "scripts/validate_kics_disclosure.py _TIER2_ISSUER_INCONSISTENT, and the code's "
        "own docstring (src/solvency/validation/kics_json_rules.py ~L906-908) names "
        "BNP카디프 as a known UNCAPPED-branch counter-example to the universal-formula "
        "assumption."
    )

    memo_evidence = (
        "PDF p21 / md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L416-417 -- "
        "raw fitz word-extract of page 21 (scripts/_probes/_tmp_kr0075_p21_words.py) shows "
        "each memo row prints a SINGLE '-' token with no second value following before the "
        "next label ('지급여력기준금액') starts -- unlike every other row in this table, which "
        "prints two numbers (전/후). This matches the MD table exactly (docling did not drop "
        "a cell; the source itself only prints one dash per memo row, most likely a column-"
        "spanning cell). '-' loads as 0 per this table's own convention (fix_20260821_"
        "tier2_limit_lines.py ZERO set; kics_json_rules.py _validate_tfi_memo_rows docstring: "
        "'대시는 0 으로 적재된다'), and every other row in this table is 전=후 identical this "
        "quarter, so 0/0 is applied to both columns. Loaded to close a second-order RED this "
        "patch itself would otherwise create: once 47/48/49 (TIER2_ITEMS) are all present, "
        "rule 53_tfi_memo_rows's census step requires 53/54 too (same table, 'TFI 표 본문"
        "(47/48/49)은 읽었는데 같은 표의 메모행이 없다 — 행 유실이다') -- verified this is a "
        "real (not hypothetical) side effect via a --master dry run with only 47/48/49 "
        "patched: 53_tfi_memo_rows flipped SKIP->RED for this bucket while 47_tier2_census "
        "flipped RED->GREEN, net RED count unchanged (38->38). This company's own 2025.2Q/"
        "2025.3Q rows already carry 53=0/54=0 with 값_적용후=0 too (precedent for mirroring "
        "the dash into both columns, not just 적용전)."
    )

    cells = []
    for n in (47, 48, 49, 53, 54):
        val = _fmt(RAW_EOK[n])
        cells.append({
            "항목번호": n,
            "항목명": ref[n]["항목명"],
            "값": float(val),
            "값_적용후": float(val),
            "근거": evidence if n in (47, 48, 49) else memo_evidence,
        })

    notes = (
        "47_tier2_census RED (TIER2_PARTIAL_ROWS: [48] present, [47,49] missing) for "
        f"{CODE} {QUARTER}. A previous pass read the correct raw values off p21 "
        "(233.86/508.40/106.31 eok) but withheld them because the KR0050-style "
        "self-check item51==min(47,48)+49[+54] did not reconcile (gave 340.17 vs an "
        "assumed-actual 233.86). That caution was correct to withhold, but the premise "
        "was wrong: KR0075 is not a CAPPED-branch filer like KR0050/한화손해(KR0002) -- "
        "it is UNCAPPED (company-level INCL-scope, 18/18 prior votes, and its own "
        "item47==item51 pattern in 10/13 loaded quarters). Under the UNCAPPED identity "
        "(item3 ~= item47, tol 2.0), the residual is 0.14 -- it closes, just via a "
        "different (and for this company, the historically dominant) branch than the "
        "one tested. item48 is independently confirmed correct (not the item3-copy "
        "contamination bug) via axis D: item48(508.40) == item14_적용전(1016.80, "
        "unrounded raw TFI total row) x 50% = 508.40, exact. All three values mirror "
        "값_적용후=값 (raw table pre/post columns are numerically identical), consistent "
        "with this company's own p19 statement '당사는 경과조치 적용하고 있지 않음' "
        "already used for items 1-46 in data/_derived/_patch_2026q2_KR0075.json (the "
        "first, already-applied patch for this company/quarter -- that patch explicitly "
        "did not touch 47/48/49, deferring this rule to a follow-up). Scope: this patch "
        "adds items 47/48/49 (TIER2_ITEMS, closes the named RED) plus 53/54 (TFI_MEMO_ITEMS, "
        "see memo_evidence below -- required because loading 47/48/49 alone was verified via "
        "--master dry run to flip a NEW RED on rule 53_tfi_memo_rows for this exact bucket, "
        "net RED count unchanged 38->38; adding 53/54 as their raw-disclosed '-'=0 value "
        "closes that side effect too, verified 38->37 in the real before/after gate run). "
        "Items 50/51 remain absent for this quarter and are out of scope (no rule requires "
        "them to close for this ticket) -- their absence was already a non-blocking SKIP "
        "(TFI_TIER_ROWS_ABSENT_BACKLOG, axis 50_tfi_tier_split / TFI_COMPOSITION_INPUT_MISSING, "
        "axis 51_tfi_tier2_composition) before this patch and stays a non-blocking SKIP after "
        "it -- verified by gate re-run, not just reasoning."
    )

    patch = {
        "company_code": CODE,
        "quarter": QUARTER,
        "cells": cells,
        "notes": notes,
        "unfixable": [],
    }

    OUT.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    for c in cells:
        print(f"  item{c['항목번호']} {c['항목명']!r} 값={c['값']} 값_적용후={c['값_적용후']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
