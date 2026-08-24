# -*- coding: utf-8 -*-
"""원문 leaf 값 vs 마스터 저장값을 **셀 단위로 직접 대조**한다 (read-only).

배경: `rebuild_combined_transition_after.py` 는 원문(백만원)을 마스터(억원)로 옮길 때 앵커
비율(item15전 / 기본요구자본전)로 스케일했다. 그 비율은 반올림 때문에 0.01 에서 ~1.7e-6 만큼
벗어나며, 나중에 `scale = 0.01 if scale < 0.5 else 1.0` 스냅이 추가됐다. 스냅 이전에 쓰인 셀은
그대로 남았고 — 그 스크립트의 재기입 문턱이 `0.0005 * |값|`(39,037억 셀에서 19.5억)이라 **자기가
남긴 오차를 스스로 못 고친다.** mmult 항등식도 스케일 오차에는 불변이라 게이트가 통과시킨다.

그래서 항등식이 아니라 원문과 대조한다. 쓰기는 하지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from rebuild_combined_transition_after import (  # noqa: E402
    APPLIERS, ITEM_OF, LIFE7, MARKET5, _num, _pdf, q2p, resolve_leaf, scan_occurrences,
)

TOL = 0.005          # 억원. 원문→억원 변환은 정확히 재현돼야 한다.
MASTER = REPO / "kics_disclosure.json"


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    bad, checked, noraw, noanchor = [], 0, 0, 0
    for (c, q), items in sorted(by_cq.items()):
        if c not in APPLIERS:
            continue
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            noraw += 1
            continue
        occ, _hl = scan_occurrences(pdf)
        if not occ.get("기본요구자본"):
            noanchor += 1
            continue
        base_pre_raw = max(a for a, _b in occ["기본요구자본"])
        item15_pre = _num((items.get(15) or {}).get("값"))
        ratio = (item15_pre or 0) / base_pre_raw if base_pre_raw else 0
        if not (0.009 < ratio < 0.011 or 0.99 < ratio < 1.01):
            noanchor += 1
            continue
        scale = 0.01 if ratio < 0.5 else 1.0

        for keys in (LIFE7, MARKET5):
            for k in keys:
                pairs = occ.get(k, [])
                if not pairs:
                    continue
                row = items.get(ITEM_OF[k])
                if row is None:
                    continue
                cand = [a for a, _b in pairs]
                # `max(set(cand), key=cand.count)` 였다. 카운트가 동률(1 vs 1)이면 `set` 순회
                # 순서가 승자를 정해서, **원문 첫 occurrence 대신 엉뚱한 값(0.0)을 고르는** 일이
                # 있었다 — 교보생명 item35 3분기가 그 탓에 "마스터가 틀렸다"로 3건 오탐됐다
                # (실제로는 마스터가 맞았다, inbox/_resolved/20260821T1030Z 답변 표).
                # 동률이면 **원문에 먼저 나온 값**을 쓴다: 표를 위에서 아래로 읽는 순서와 같다.
                pre_raw = max(cand, key=lambda v: (cand.count(v), -cand.index(v))) if cand else None
                post_raw, note = resolve_leaf(pairs)
                for col, v in (("값", pre_raw), ("값_적용후", post_raw)):
                    if v is None or note.startswith("두 표"):
                        continue
                    cur = _num(row.get(col))
                    if cur is None:
                        continue
                    checked += 1
                    want = round(v * scale, 2)
                    if abs(cur - want) > TOL:
                        bad.append((c, name[c], q, ITEM_OF[k], col, cur, want, v))

    print(f"대조 셀 {checked:,}  |  불일치 {len(bad)}  |  raw없음 {noraw} (회사,분기)  앵커불가 {noanchor}")
    if bad:
        print(f"\n{'회사':<14}{'분기':<9}{'item':>5} {'열':<9}{'저장':>13}{'원문환산':>13}{'차이':>9}  원문(백만원)")
        for c, nm, q, it, col, cur, want, v in bad:
            print(f"{nm[:12]:<14}{q:<9}{it:>5} {col:<9}{cur:>13,.2f}{want:>13,.2f}"
                  f"{cur-want:>+9.2f}  {v:,.0f}")
        agg: dict[tuple, int] = {}
        for c, nm, q, _it, _col, cur, want, _v in bad:
            agg[(nm, q)] = agg.get((nm, q), 0) + 1
        print(f"\n(회사,분기) {len(agg)}건: " + ", ".join(f"{n} {q}({v})" for (n, q), v in sorted(agg.items())))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
