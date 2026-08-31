#!/usr/bin/env python3
"""Apply per-company 2026.2Q cell patches into kics_disclosure.json.

The 2026.2Q onboarding was diagnosed by one subagent per company, each writing a patch
file instead of the master -- six concurrent whole-file read-modify-writes would have
silently dropped each other's rows (this repo has had exactly that incident). This is
the single writer that folds them in, one patch at a time.

Patch shape:
  {"company_code": "KR####", "quarter": "2026.2Q",
   "cells": [{"항목번호": int, "항목명": str, "값": num|null, "값_적용후": num|null,
              "근거": str}, ...],
   "notes": str, "unfixable": [...]}

Rules enforced here (a patch that violates one is rejected whole, not partially applied):
  * every cell must carry 항목번호 and 근거
  * 항목명, when the row already exists, must match the master's label -- a patch may not
    rename an item (labels are schema-wide; validation rules match on them)
  * writes are scoped to (company_code, quarter): no other cell may change
  * the row count may only grow or stay equal
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "kics_disclosure.json"


def load_master() -> list[dict]:
    d = json.loads(MASTER.read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d.get("records", d)


def key_of(r: dict) -> tuple:
    return (r.get("회사코드") or r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))


def apply_patch(rows: list[dict], patch: dict, dry: bool) -> tuple[list[dict], dict]:
    kr, q = patch["company_code"], patch["quarter"]
    idx = {key_of(r): r for r in rows}
    stats = {"updated": 0, "added": 0, "skipped": 0, "errors": []}

    # template row for this company/quarter, to copy the identity columns from
    tmpl = next((r for r in rows if key_of(r)[0] == kr and r.get("공시분기") == q), None)
    if tmpl is None:
        stats["errors"].append(f"{kr} {q}: 이 회사·분기 행이 하나도 없다 — 템플릿 없음")
        return rows, stats

    for c in patch.get("cells", []):
        item = c.get("항목번호")
        if item is None or not c.get("근거"):
            stats["errors"].append(f"item {item}: 항목번호 또는 근거 누락")
            continue
        hit = idx.get((kr, q, item))
        if hit is not None:
            want = c.get("항목명")
            if want and hit.get("항목명") and want != hit["항목명"]:
                stats["errors"].append(
                    f"item {item}: 항목명 불일치 patch={want!r} master={hit['항목명']!r} — 개명 금지")
                continue
            changed = False
            for f in ("값", "값_적용후"):
                if f in c and c[f] is not None and hit.get(f) != c[f]:
                    if not dry:
                        hit[f] = c[f]
                    changed = True
            stats["updated" if changed else "skipped"] += 1
        else:
            new = {k: tmpl[k] for k in tmpl if k not in ("항목번호", "항목명", "값", "값_적용후")}
            new["항목번호"] = item
            new["항목명"] = c.get("항목명")
            new["값"] = c.get("값")
            if c.get("값_적용후") is not None:
                new["값_적용후"] = c["값_적용후"]
            if not dry:
                rows.append(new)
            stats["added"] += 1
    return rows, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patches", nargs="+", help="patch json paths")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = load_master()
    before_n = len(rows)
    before = {key_of(r): (r.get("값"), r.get("값_적용후")) for r in rows}

    all_stats = {}
    for p in args.patches:
        patch = json.loads(Path(p).read_text(encoding="utf-8"))
        rows, st = apply_patch(rows, patch, args.dry_run)
        all_stats[patch["company_code"]] = st
        tag = "DRY " if args.dry_run else ""
        print(f"{tag}{patch['company_code']} {patch['quarter']}: "
              f"+{st['added']} 신규 · {st['updated']} 갱신 · {st['skipped']} 변화없음"
              + (f" · 오류 {len(st['errors'])}" if st["errors"] else ""))
        for e in st["errors"]:
            print(f"    ERROR {e}")

    if any(st["errors"] for st in all_stats.values()):
        print("\n오류가 있어 저장하지 않는다.")
        return 2

    # scope audit: nothing outside the patched (company, quarter) may have moved
    scope = {(pt["company_code"], pt["quarter"]) for pt in
             (json.loads(Path(p).read_text(encoding="utf-8")) for p in args.patches)}
    drift = []
    for r in rows:
        k = key_of(r)
        if (k[0], k[1]) in scope:
            continue
        was = before.get(k)
        if was is not None and was != (r.get("값"), r.get("값_적용후")):
            drift.append(k)
    print(f"\n범위 밖 변경: {len(drift)}건 {drift[:5]}")
    if drift:
        print("범위를 벗어난 변경이 있어 저장하지 않는다.")
        return 2
    if len(rows) < before_n:
        print(f"행이 줄었다 ({before_n} -> {len(rows)}) — 저장하지 않는다.")
        return 2

    if args.dry_run:
        print(f"\n(dry-run) 행 {before_n} -> {len(rows)}; 파일 안 씀")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(MASTER, MASTER.with_suffix(f".json.bak_{stamp}_patch"))
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {MASTER} ({before_n} -> {len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
