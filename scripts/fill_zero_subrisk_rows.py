# -*- coding: utf-8 -*-
"""값이 0 이라 통째로 빠진 하위위험 행/셀을 되살린다 — 단, 행렬 검산이 그 0 을 증명할 때만.

증상: 원천 표에서 값이 "-"(=0) 인 하위위험(대개 item40 자산집중, item32 장기재물)을 추출기가
아예 행으로 만들지 않았다. 그러면 그 부모(item17 생명장기 / item19 시장)의 mmult 검사는
'계산불가'로 조용히 건너뛴다 — 부모후가 틀려도 게이트가 못 본다
(validation inbox `20260821T0010Z` §6, `[[feedback-coverage-census-mandatory]]` 의 SKIP-on-missing).

판정: 결측 leaf 를 0 으로 놓았을 때 sqrt(V'·M·V) 가 **이미 저장된 부모값을 재현하면** 그 0 이
맞다는 증거다(0 이 아니었다면 재현이 안 된다). 재현 못 하면 손대지 않는다 — 그건 진짜 결측이다.
1Q/3Q 간이공시처럼 5개가 통째로 없는 셀은 부모도 없거나 재현이 안 되므로 자연히 걸러진다.

전·후 컬럼을 따로 판정한다. 행이 아예 없으면 같은 (회사,분기)의 형제 행에서 메타를 복사해 만든다.

Usage: ...python scripts/fill_zero_subrisk_rows.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R7, MARKET_M  # noqa: E402

TARGET = REPO / "kics_disclosure.json"
GROUPS = [(17, list(range(29, 36)), R7), (19, list(range(36, 41)), MARKET_M)]
MAX_FILL = 2   # 한 그룹에서 0 으로 채울 수 있는 leaf 최대 개수(전부 없는 셀을 0으로 만들지 않기 위함)


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    by_cq: dict[tuple, dict] = defaultdict(dict)
    label_of: dict[int, str] = {}
    for r in data:
        try:
            it = int(r["항목번호"])
        except (TypeError, ValueError, KeyError):
            continue
        by_cq[(r["원보험사코드"], r["공시분기"])][it] = r
        label_of.setdefault(it, r.get("항목명", ""))

    filled, created, holds = [], [], []
    for (c, q), items in sorted(by_cq.items()):
        for parent, subs, mat in GROUPS:
            for post in (False, True):
                col = "값_적용후" if post else "값"
                pv = _num((items.get(parent) or {}).get(col))
                if pv is None or abs(pv) < 1.0:
                    continue
                vals, missing = [], []
                for s in subs:
                    v = _num((items.get(s) or {}).get(col))
                    if v is None:
                        missing.append(s)
                        vals.append(0.0)
                    else:
                        vals.append(v)
                if not missing or len(missing) > MAX_FILL:
                    continue
                arr = np.array(vals, float)
                calc = float(np.sqrt(arr @ mat @ arr))
                if abs(calc - pv) > max(2.0, 0.002 * abs(pv)):
                    holds.append((c, q, parent, col, missing,
                                  f"0 가정으로 부모 재현 실패 {calc:,.2f} vs {pv:,.2f}"))
                    continue
                for s in missing:
                    row = items.get(s)
                    if row is None:
                        sib = next(iter(items.values()))
                        row = {
                            "원보험사코드": c, "원수사명": sib.get("원수사명", c),
                            "티커": sib.get("티커", "X"), "생손보여부": sib.get("생손보여부", ""),
                            "항목번호": s, "항목명": label_of.get(s, ""), "공시분기": q,
                        }
                        items[s] = row
                        created.append((c, q, s))
                    row[col] = "0"
                    filled.append((c, row.get("원수사명", c), q, s, col))

    print(f"{'DRY-RUN ' if dry else ''}0 확정 채움 {len(filled)}셀 (신설 행 {len(created)}) · "
          f"재현실패로 보류 {len(holds)}")
    for c, nm, q, s, col in filled:
        print(f"  ZERO {c} {nm:<12} {q} item{s} [{col}]")
    for c, q, parent, col, missing, why in holds[:15]:
        print(f"  HOLD {c} {q} parent{parent}[{col}] 결측{missing}: {why}")
    if len(holds) > 15:
        print(f"  ... +{len(holds) - 15} more holds")

    if not dry and filled:
        out = []
        for r in data:
            out.append(r)
        # 신설 행을 같은 (회사,분기) 블록의 항목번호 순서 자리에 끼워 넣는다
        if created:
            out = []
            seen = set()
            for r in data:
                key = (r["원보험사코드"], r["공시분기"])
                out.append(r)
                seen.add((key, int(r["항목번호"])))
            for c, q, s in created:
                row = by_cq[(c, q)][s]
                idxs = [i for i, r in enumerate(out)
                        if r["원보험사코드"] == c and r["공시분기"] == q]
                at = max(idxs) + 1
                for i in idxs:
                    if int(out[i]["항목번호"]) > s:
                        at = i
                        break
                out.insert(at, row)
        TARGET.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
