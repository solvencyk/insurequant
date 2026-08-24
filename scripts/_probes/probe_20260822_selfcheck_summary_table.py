# -*- coding: utf-8 -*-
"""read-only: build the item50+item51==item1 self-check summary table (회사×분기),
classifying every mismatch by known root-cause pattern for the final report.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

by_bq: dict[tuple, dict] = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    by_bq.setdefault(key, {})[int(r["항목번호"])] = (r.get("값"), r.get("값_적용후"), r.get("원수사명"))


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


rows = []
for (c, q), items in sorted(by_bq.items()):
    if 50 not in items or 51 not in items:
        continue
    name = items[50][2]
    i50p, i50q = fnum(items[50][0]), fnum(items[50][1])
    i51p, i51q = fnum(items[51][0]), fnum(items[51][1])
    i1p, i1q = (fnum(items[1][0]), fnum(items[1][1])) if 1 in items else (None, None)
    i47p = fnum(items.get(47, (None, None, None))[0])
    i48p = fnum(items.get(48, (None, None, None))[0])
    i49p = fnum(items.get(49, (None, None, None))[0])
    i13p = fnum(items.get(13, (None, None, None))[0])

    diff_pre = (i50p + i51p) - i1p if None not in (i50p, i51p, i1p) else None
    diff_post = (i50q + i51q) - i1q if None not in (i50q, i51q, i1q) else None

    tag = ""
    if diff_pre is not None and abs(diff_pre) > 3.0:
        if i47p is not None and i51p is not None and abs(i47p - i51p) <= 2.0:
            tag = "UNCAPPED(item51=item47)"
        elif i47p == 0 and i48p == 0 and i13p is not None and abs(i51p - i13p) <= 2.0:
            tag = "TFI_NA(item51=item13)"
        else:
            tag = "SOURCE_MISMATCH(review)"
    rows.append({
        "code": c, "name": name, "q": q,
        "diff_pre": diff_pre, "diff_post": diff_post, "tag_pre": tag,
    })

n = len(rows)
bad_pre = [r for r in rows if r["diff_pre"] is not None and abs(r["diff_pre"]) > 3.0]
bad_post = [r for r in rows if r["diff_post"] is not None and abs(r["diff_post"]) > 3.0]
print(f"item50+item51==item1 자체검산 대상 (회사,분기) = {n}")
print(f"  적용전 불일치(|diff|>3.0) = {len(bad_pre)} / {n}")
print(f"  적용후 불일치(|diff|>3.0) = {len(bad_post)} / {n}")

print("\n=== 적용전 불일치 상세 ===")
for r in bad_pre:
    print(f"  {r['code']} {r['name']} {r['q']}: diff={r['diff_pre']:.2f} tag={r['tag_pre']}")

print("\n=== 적용후 불일치 상세 (스코프차 구조패턴 여부 포함) ===")
for r in bad_post:
    same_pre_ok = r["diff_pre"] is None or abs(r["diff_pre"]) <= 3.0
    note = "PRE는 정상(스코프차 구조패턴)" if same_pre_ok else "PRE도 불일치"
    print(f"  {r['code']} {r['name']} {r['q']}: diff={r['diff_post']:.2f} ({note})")

# 회사 단위로 묶어서 요약
by_company: dict[str, list] = {}
for r in rows:
    by_company.setdefault(r["code"], []).append(r)
print(f"\n=== 회사 단위 요약 ({len(by_company)}개사) ===")
for c in sorted(by_company):
    rs = by_company[c]
    name = rs[0]["name"]
    n_pre_bad = sum(1 for r in rs if r["diff_pre"] is not None and abs(r["diff_pre"]) > 3.0)
    n_post_bad = sum(1 for r in rs if r["diff_post"] is not None and abs(r["diff_post"]) > 3.0)
    print(f"  {c} {name:<16} 버킷수={len(rs):>2}  적용전불일치={n_pre_bad:>2}  적용후불일치={n_post_bad:>2}")
