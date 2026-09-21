# -*- coding: utf-8 -*-
"""Fix: mirror 적용전 -> 적용후 for 3 confirmed non-applier companies, 2026.2Q only,
in kics_rate_sensitivity.json.

Ticket: inbox/parser/20260921T0057Z__owner__KR0074_2026.2Q__rate_sensitivity_verify.md
(task 3, 2026.2Q coverage census). KR0074 itself needed no fix (already 6/6, verified
cell-for-cell against raw). This script fixes the 3 OTHER gaps the census turned up:

  KR0050 하나손해보험   2026.2Q -- raw MD table's 경과조치후 row cells are BLANK, but the
                                 table's own footnote reads (md_inbox/FY2026_Q2/
                                 KR0050_하나손해보험.md, right under the table):
                                 "주3) (경과조치 미신청 회사) 당사는 선택경과조치를 적용하지
                                 않아 경과조치 전·후 금액 및 비율이 동일함"
  KR0069 삼성생명보험   2026.2Q -- raw MD table's 경과조치후 row cells are literal "-" (dash,
                                 -> parsed None). docling's own reading-order dropped the
                                 footnote from the captured table region, but the SAME
                                 sentence is present verbatim in the raw PDF page text
                                 (fitz page 44/0-idx43 full-text dump, this session):
                                 "주3) 당사는선택경과조치를적용하지않아경과조치전·후금액및비율이동일함"
  KR1098 카카오페이손해보험 2026.2Q -- raw PDF (fitz text AND 480dpi visual render, this
                                 session, artifacts/_kr1098_2026q2_labelzoom_480dpi.png)
                                 shows the filing's OWN vertical row-label literally prints
                                 "경과조치전" TWICE (a filer-side labelling slip -- the 2nd
                                 block's label should read 후) but reprints the identical 5
                                 numbers under it, plus the same 주3) 미신청 footnote. The
                                 extractor's dedup step (comment in extract_kics_rate_
                                 sensitivity.py: "dedup verbatim-duplicate blocks (OCR), e.g.
                                 KR1098 두 적용전 동일") silently discarded this 2nd block as
                                 a redundant duplicate instead of recognizing it as the
                                 (mislabeled) 적용후 block.

None of these 3 are in `_TRANSITION_KIND` (scripts/validate_kics_disclosure.py L536) --
consistent with being TFI-only non-appliers, matching what their own 금리민감도 table
footnotes say. This is NOT the same finding as KR0074 (which already had a correctly
extracted, byte-identical 적용후 block) -- these 3 had the 적용후 phase MISSING outright
(extraction gap, not a data question), which is exactly what the ticket's task-3 census
was designed to surface. Fix = mirror 적용전 -> 적용후 (append only, values 1:1 identical,
듀레이션/컨벡서티 recomputed via the extractor's own duration_convexity() -- not retyped).

Guarded: asserts exact pre-state (3 적용전 rows, 0 적용후 rows) per company before writing,
and asserts every row outside these 9 new ones is byte-identical before/after.
"""
from __future__ import annotations
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_kics_rate_sensitivity import duration_convexity  # noqa: E402  (reuse, don't retype)

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "kics_rate_sensitivity.json"
BACKUP = ROOT / "kics_rate_sensitivity.json.bak_pre_20260921_nonapplier_mirror"
QUARTER = "2026.2Q"
TARGETS = ["KR0050", "KR0069", "KR1098"]


def main() -> int:
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    before_n = len(data)
    before_snapshot = json.dumps(data, ensure_ascii=False, sort_keys=True)

    new_rows = []
    for code in TARGETS:
        pre = [r for r in data
               if r.get("원보험사코드") == code and r.get("공시분기") == QUARTER
               and r.get("경과조치여부") == "적용전"]
        post_existing = [r for r in data
                          if r.get("원보험사코드") == code and r.get("공시분기") == QUARTER
                          and r.get("경과조치여부") == "적용후"]
        assert len(pre) == 3, f"{code} {QUARTER}: expected 3 적용전 rows, found {len(pre)}"
        assert len(post_existing) == 0, f"{code} {QUARTER}: expected 0 적용후 rows, found {len(post_existing)}"
        for r in pre:
            mirror = dict(r)
            mirror["경과조치여부"] = "적용후"
            base, dn100, up100 = r.get("base"), r.get("-100bp"), r.get("+100bp")
            dur, conv = duration_convexity(r["measure구분"], base, dn100, up100)
            mirror["듀레이션"] = dur
            mirror["컨벡서티"] = conv
            new_rows.append(mirror)

    print(f"prepared {len(new_rows)} mirror rows for {TARGETS} @ {QUARTER}")
    for r in new_rows:
        print(f"  {r['원보험사코드']} {r['measure구분']:10s} base={r['base']} "
              f"dur={r['듀레이션']} conv={r['컨벡서티']}")

    BACKUP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    merged = data + new_rows
    MASTER.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    # post-write guard: every pre-existing row must be byte-identical; only append happened.
    reloaded = json.loads(MASTER.read_text(encoding="utf-8"))
    after_old_part = reloaded[:before_n]
    after_old_snapshot = json.dumps(after_old_part, ensure_ascii=False, sort_keys=True)
    if after_old_snapshot != before_snapshot:
        print("ABORT-CHECK-FAILED: pre-existing rows changed -- restoring backup")
        MASTER.write_text(BACKUP.read_text(encoding="utf-8"), encoding="utf-8")
        return 2
    assert len(reloaded) == before_n + len(new_rows)
    print(f"\nOK: {before_n} -> {len(reloaded)} rows (+{len(new_rows)}), "
          f"pre-existing {before_n} rows verified byte-identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
