# -*- coding: utf-8 -*-
"""MARKET5(36-40) dash 해석 규칙 변경을 전 버킷(APPLIERS x quarter)에 시뮬레이션한다 (read-only,
쓰기 없음). 현재 규칙(구법: dash+a!=0 -> carry-forward b=a) vs 제안 규칙(신법: 같은 표의 다른
MARKET5 형제 중 진짜 변화(dash 아닌 채 |a-b|>tol)가 있으면 dash=0 유지, 없으면 기존대로
carry-forward)을 나란히 계산해 어느 (회사,분기,item) 버킷이 달라지는지, 그리고 그 변경이
마스터 저장값과 더 가까워지는지/멀어지는지 표로 낸다.

이 스크립트는 rebuild_combined_transition_after.scan_occurrences() 를 건드리지 않는다 —
그 함수와 동일한 라인 파서를 로컬로 복제해 신/구 두 갈래를 동시에 계산한다(독립 검증 목적).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from rebuild_combined_transition_after import (  # noqa: E402
    APPLIERS, DASH, ITEM_OF, LABELS, LIFE7, MARKET5, NUMRE, ZERO,
    _num, _pdf, q2p, resolve_leaf,
)

DECOR = {"·", "‧", "∙", "(", ")", "%", "(%)", "|", ","}   # scan_occurrences() 내부 상수 로컬 복제

TOL_RESOLVE = 0.5   # resolve_leaf 와 동일한 판정 허용치(백만원)
MASTER = REPO / "kics_disclosure.json"


def scan_dual(pdf: Path):
    """occ_old(현재 코드와 동일) 와 occ_new(제안 규칙)를 동시에 반환."""
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()

    matched = {i for i, text in enumerate(page_texts)
               if "경과조치" in text and "기본요구자본" in text}
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    occ_old: dict[str, list[tuple]] = defaultdict(list)
    occ_new: dict[str, list[tuple]] = defaultdict(list)
    market_dash_idx: dict[str, list[int]] = defaultdict(list)  # key -> [index into occ_new[key] that was a dash-post]
    block = None
    last_key = None
    LIFE_PREV = {"사망", "장수", "장해질병", "장기재물", "해지", "사업비"}
    NL_PREV = {"일반손해", "보험가격"}
    k = 0

    def _norm(x: str) -> str:
        return x.replace("·", "").replace("‧", "").replace("∙", "")

    while k < len(lines):
        s = _norm(lines[k].strip().lstrip("Ⅰ Ⅱ Ⅲ①②③④ .·-").replace(" ", ""))
        key = None
        for kk, pat in LABELS:
            if kk in ("생명대재해", "일반대재해"):
                continue
            pat = _norm(pat)
            if s == pat or s == pat.replace("위험액", "위험") or s.rstrip("()1+2+3") == pat:
                key = kk
                break
        if key is None and s in ("대재해위험", "대재해위험액"):
            if last_key in LIFE_PREV:
                key = "생명대재해"
            elif last_key in NL_PREV:
                key = "일반대재해"
            else:
                key = {"life": "생명대재해", "nl": "일반대재해"}.get(block)
        if key == "생명장기":
            block = "life"
        elif key == "일반손해":
            block = "nl"
        elif key == "시장":
            block = "market"
        elif key in ("신용", "운영", "법인세", "기타요구자본", "기본요구자본", "기준금액"):
            block = None
        if key:
            vals, toks, j = [], [], k + 1
            while j < len(lines) and len(vals) < 2:
                t = lines[j].replace(" ", "")
                if t == "" or t in DECOR:
                    j += 1
                    continue
                if NUMRE.match(t) or t in ZERO:
                    vals.append(_num(t))
                    toks.append(t)
                    j += 1
                    continue
                break
            if len(vals) == 2 and vals[0] is not None:
                a, b = vals
                is_dash_post = key in MARKET5 and toks[1] in DASH and a != 0.0
                # old: 즉시 carry-forward 스냅
                b_old = a if is_dash_post else b
                occ_old[key].append((a, b_old))
                # new: 일단 자연값(0.0) 유지, 나중에 형제 판정으로 되돌릴지 결정
                occ_new[key].append((a, b))
                if is_dash_post:
                    market_dash_idx[key].append(len(occ_new[key]) - 1)
                last_key = key
                k = j
                continue
        k += 1

    # 신규칙 후처리: 이 필링(=이 한 번의 scan_dual 호출) 안에서 MARKET5 중 dash 아닌 채로
    # |a-b|>TOL_RESOLVE 인 진짜 변화가 하나라도 있으면 "선택적용 표" -> dash는 0 유지.
    # 없으면(전부 dash 이거나 전부 불변) 기존처럼 carry-forward. 인덱스 기반으로 판정해
    # 값 중복(예: 0.0 이 여러 개)에도 안전하다.
    real_change_exists = False
    for k5 in MARKET5:
        dash_positions = set(market_dash_idx.get(k5, []))
        for idx, (a, b) in enumerate(occ_new.get(k5, [])):
            if idx in dash_positions:
                continue
            if a is not None and b is not None and abs(a - b) > TOL_RESOLVE:
                real_change_exists = True
    if not real_change_exists:
        for k5 in MARKET5:
            dash_positions = market_dash_idx.get(k5, [])
            for idx in dash_positions:
                a, _b = occ_new[k5][idx]
                occ_new[k5][idx] = (a, a)   # carry-forward (구법과 동일 결과)
    # real_change_exists=True 인 경우 occ_new 는 이미 dash 항목이 (a, 0.0) 그대로 -> 신법 결과

    return occ_old, occ_new


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    changed_buckets = []
    n_scanned = 0
    for (c, q), items in sorted(by_cq.items()):
        if c not in APPLIERS:
            continue
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            continue
        n_scanned += 1
        occ_old, occ_new = scan_dual(pdf)
        for k5 in MARKET5:
            pairs_old = occ_old.get(k5, [])
            pairs_new = occ_new.get(k5, [])
            if not pairs_old:
                continue
            post_old, _n1 = resolve_leaf(pairs_old)
            post_new, _n2 = resolve_leaf(pairs_new)
            if post_old is None or post_new is None:
                continue
            if abs(post_old - post_new) > TOL_RESOLVE:
                row = items.get(ITEM_OF[k5])
                cur = _num((row or {}).get("값_적용후"))
                changed_buckets.append((c, name[c], q, k5, post_old, post_new, cur))

    print(f"스캔 버킷(회사,분기) {n_scanned}  |  구법vs신법 값이 달라진 (회사,분기,item) {len(changed_buckets)}건\n")
    if changed_buckets:
        print(f"{'회사':<14}{'분기':<9}{'item':<8}{'구법(후,백만)':>14}{'신법(후,백만)':>14}{'마스터(억원)':>14}  신법이 마스터와 더 가까운가")
        for c, nm, q, k5, old, new, cur in changed_buckets:
            cur_mn = None if cur is None else cur * 100  # 억원 -> 백만원 비교
            closer = "?"
            if cur_mn is not None:
                d_old = abs(old - cur_mn)
                d_new = abs(new - cur_mn)
                closer = "신법" if d_new < d_old else ("구법" if d_old < d_new else "동일")
            print(f"{nm[:12]:<14}{q:<9}{k5:<8}{old:>14,.2f}{new:>14,.2f}"
                  f"{'' if cur is None else cur:>14}  {closer}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
