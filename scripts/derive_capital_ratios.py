# -*- coding: utf-8 -*-
"""결측된 item27(지급여력비율)·item28(기본자본비율)을 산출해 채운다.

이 둘은 MD 에서 추출되는 값이 아니라 **파생 산출**이다:
    item27 = item1(지급여력금액)   / item14(지급여력기준금액) x 100
    item28 = item2(기본자본)       / item14(지급여력기준금액) x 100

산식은 마스터 실측으로 확증했다 — item28 이 이미 있는 (회사,분기) 502 버킷 전부에서
`item2/item14*100` 과 일치했고 **불일치 0** 이었다. 그래서 결측분을 계산해 채우는 것이
추측이 아니다.

왜 스크립트가 필요한가: 이 산출 스텝이 온보딩에서 빠지면 rule8 이 RED 로 뜬다. 2026.2Q
라운드에서 20개사 넘게 item28 이 통째로 비어 있었다. `recalc_basic_capital_ratio_post.py`
는 **이미 있는** item28 행의 값_적용후만 다시 계산할 뿐 없는 행을 만들지 않는다.

동작 원칙:
  - **이미 있는 값은 절대 덮지 않는다.** 없는 행만 새로 만든다(`--overwrite` 로만 갱신).
  - 값_적용후는 item1/2/14 의 값_적용후가 **둘 다** 있을 때만 만든다.
  - 셀 단위로 더하기만 한다 — 마스터 통째 재작성이 아니다(동시 세션 유실 방지).

사용:
  python scripts/derive_capital_ratios.py --period 2026.2Q      # dry-run
  python scripts/derive_capital_ratios.py --period 2026.2Q --apply
  python scripts/derive_capital_ratios.py --all-periods --apply
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "kics_disclosure.json"

CODE, QUARTER, ITEM = "원보험사코드", "공시분기", "항목번호"
VAL, VAL_POST, NAME = "값", "값_적용후", "항목명"

# 산출 대상 -> (분자 항목, 분모 항목, 항목명)
DERIVED = {
    27: (1, 14, "지급여력비율"),
    28: (2, 14, "기본자본비율"),
}


def to_f(v):
    if v in (None, "", "None"):
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def fmt(x: float) -> str:
    """기존 행과 같은 표기(고정 소수점, 꼬리 0 제거)."""
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", help="예: 2026.2Q (생략하면 --all-periods 필요)")
    ap.add_argument("--all-periods", action="store_true")
    ap.add_argument("--apply", action="store_true", help="실제로 쓴다 (기본 dry-run)")
    ap.add_argument("--overwrite", action="store_true",
                    help="이미 있는 값도 갱신 (기본은 결측만 채움)")
    args = ap.parse_args()
    if not args.period and not args.all_periods:
        ap.error("--period 또는 --all-periods 중 하나가 필요하다")

    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    before = len(rows)
    buckets = defaultdict(dict)
    for r in rows:
        buckets[(r.get(CODE), r.get(QUARTER))][int(r[ITEM])] = r

    added, updated, skipped_no_input, mismatch = [], [], [], []
    for (code, q), d in sorted(buckets.items()):
        if not args.all_periods and q != args.period:
            continue
        for item, (num_i, den_i, label) in DERIVED.items():
            num, den = d.get(num_i), d.get(den_i)
            if num is None or den is None:
                continue
            a, b = to_f(num.get(VAL)), to_f(den.get(VAL))
            if a is None or b in (None, 0):
                skipped_no_input.append((code, q, item))
                continue
            pre = a / b * 100
            ap_, bp = to_f(num.get(VAL_POST)), to_f(den.get(VAL_POST))
            post = (ap_ / bp * 100) if (ap_ is not None and bp) else None

            cur = d.get(item)
            if cur is None:
                seed = num  # 회사 메타(원수사명·티커·생손보여부)는 형제 행에서 복사
                new = {k: seed[k] for k in seed if k not in (ITEM, NAME, VAL, VAL_POST)}
                new[ITEM] = item
                new[NAME] = label
                new[VAL] = fmt(pre)
                if post is not None:
                    new[VAL_POST] = fmt(post)
                rows.append(new)
                d[item] = new
                added.append((code, q, item, fmt(pre)))
            else:
                got = to_f(cur.get(VAL))
                if got is not None and abs(got - pre) > max(abs(pre) * 0.002, 0.05):
                    mismatch.append((code, q, item, got, round(pre, 4)))
                if args.overwrite:
                    cur[VAL] = fmt(pre)
                    if post is not None:
                        cur[VAL_POST] = fmt(post)
                    updated.append((code, q, item))
                elif cur.get(VAL_POST) in (None, "", "None") and post is not None:
                    cur[VAL_POST] = fmt(post)
                    updated.append((code, q, item, "값_적용후만"))

    print("신규 %d행 · 갱신 %d행 · 입력결측으로 건너뜀 %d건"
          % (len(added), len(updated), len(skipped_no_input)))
    by_q = defaultdict(list)
    for code, q, item, v in added:
        by_q[q].append((code, item))
    for q in sorted(by_q):
        items = defaultdict(list)
        for code, item in by_q[q]:
            items[item].append(code)
        print("  %-9s %s" % (q, " · ".join(
            "item%d %d사" % (i, len(c)) for i, c in sorted(items.items()))))

    if mismatch:
        print("\n[경고] 기존 값이 산식과 어긋난다 (덮지 않았다):")
        for code, q, item, got, want in mismatch[:20]:
            print("   %s %s item%d 공시=%s 계산=%s" % (code, q, item, got, want))

    if not args.apply:
        print("\n(dry-run — 실제로 쓰려면 --apply)")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = MASTER.with_suffix(".json.bak_%s_derivratios" % stamp)
    shutil.copy2(MASTER, bak)
    # 배포본 포맷 그대로: indent=2 + write_text (Windows 에서 CRLF 로 나간다).
    # fill_period_to_disclosure.py / apply_2026q2_patches.py 와 동일해야
    # 파일 전체가 갈리는 diff 가 안 난다.
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n행수 %d -> %d (백업 %s)" % (before, len(rows), bak.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
