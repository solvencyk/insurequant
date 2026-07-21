# -*- coding: utf-8 -*-
"""Append owner image-OCR fills (kakao KR1098 missing quarters + AIA KR0080
corrections) into the durable gold data/_gold/user_kics_cells.json so they
survive a parser rebuild (apply_user_kics_gold re-applies / re-creates them).

WHY: owner hand-OCR'd these (image-only PDFs the parser can't read) and synced
them straight into kics_disclosure.json (insert_kakao_missing_quarters.py /
sync_owner_fills_to_json.py), bypassing the gold. build_user_kics_gold.py only
captures cells where xlsx != current JSON, so post-sync the diff is gone and a
rebuild would drop them (inbox 20260619T0811Z 후속2: "parser가 diag/source에 영구
삽입 필수"). This is ADDITIVE: never modifies/removes existing gold entries.

Capture scope (owner-flagged, parser-unreproducible only — NOT derived 27/28):
  - KR1098 kakao: every cell of 2023.4Q + 2024.4Q (absent from HEAD = pure owner
    additions, image-only) + 2025.3Q substantive owner edits.
  - KR0080 AIA: cells whose 값 changed vs HEAD with item not in {27,28}.

Default = DRY RUN (reports only). Pass --apply to write (with .bak).
Usage: python scripts/append_owner_image_fills_to_gold.py [--apply]
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
CUR = REPO / "kics_disclosure.json"
HEAD = REPO / "scripts" / "_probes" / "_head_kics.json"
GOLD = REPO / "data" / "_gold" / "user_kics_cells.json"
DERIVED = {27, 28}

KAKAO = "KR1098"
AIA = "KR0080"
KAKAO_FULL_Q = {"2023.4Q", "2024.4Q"}     # HEAD-absent → capture full
KAKAO_EDIT_Q = {"2025.3Q"}                # capture substantive non-derived edits


def _canon(n):
    if n is None:
        return None
    if abs(n - round(n)) < 1e-6:
        return int(round(n))
    return round(n, 6)


def _numkey(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main(apply: bool) -> int:
    cur_rows = json.loads(CUR.read_text(encoding="utf-8"))
    head_rows = json.loads(HEAD.read_text(encoding="utf-8"))
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    cells = gold.setdefault("cells", {})
    meta = gold.setdefault("_meta", {})
    names = gold.setdefault("_names", {})

    cur_idx = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])): r for r in cur_rows}
    head_val = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])): r.get("값") for r in head_rows}
    co_meta = {}
    for r in cur_rows:
        co_meta.setdefault(r["원보험사코드"],
                           {"원수사명": r["원수사명"], "티커": r.get("티커", "X"),
                            "생손보여부": r.get("생손보여부", "")})

    def in_gold(c, q, it):
        return str(it) in cells.get(c, {}).get(q, {})

    # Build capture list
    targets = []   # (code, q, item, row)
    for (c, q, it), r in cur_idx.items():
        if it in DERIVED:
            continue
        take = False
        if c == KAKAO and q in KAKAO_FULL_Q:
            take = True
        elif c == KAKAO and q in KAKAO_EDIT_Q:
            hv = head_val.get((c, q, it))
            cv = r.get("값")
            if hv is None or str(hv) != str(cv):
                take = True
        elif c == AIA:
            hv = head_val.get((c, q, it))
            cv = r.get("값")
            if hv is not None and str(hv) != str(cv):
                take = True
        if take and r.get("값") is not None:
            targets.append((c, q, it, r))

    added = skipped = 0
    add_log = defaultdict(list)
    for c, q, it, r in sorted(targets, key=lambda x: (x[0], x[1], x[2])):
        if in_gold(c, q, it):
            skipped += 1
            continue
        cell = {"값": _canon(_numkey(r.get("값")))}
        post = r.get("값_적용후")
        if post not in (None, "", "-"):
            cp = _numkey(post)
            if cp is not None:
                cell["값_적용후"] = _canon(cp)
        cells.setdefault(c, {}).setdefault(q, {})[str(it)] = cell
        names.setdefault(c, {})[str(it)] = r.get("항목명", "")
        meta.setdefault(c, co_meta.get(c, {}))
        added += 1
        add_log[(c, q)].append(it)

    print(f"=== capture ({'APPLY' if apply else 'DRY-RUN'}) ===")
    for (c, q), its in sorted(add_log.items()):
        print(f"  +{c} {q}: items {sorted(its)}")
    print(f"\n  added={added}  already-in-gold(skipped)={skipped}")
    print(f"  gold companies now: {sorted(cells)}")

    if apply:
        bak = GOLD.with_suffix(".json.pre_owner_image.bak")
        bak.write_text(GOLD.read_text(encoding="utf-8"), encoding="utf-8")
        GOLD.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {GOLD}  (backup {bak.name})")
    else:
        print("  (dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--apply" in sys.argv))
