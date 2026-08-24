# -*- coding: utf-8 -*-
"""tier2 표의 '지급여력기준금액' 마지막 행을 앵커로 삼아, 이 표의 진짜 단위가
백만원(scale=100)인지 이미 억원(scale=1)인지 (회사,분기)별로 직접 판별한다."""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from fix_20260821_tier2_limit_lines import (  # noqa: E402
    DECOR, NUMRE, ZERO, _num, _pdf, q2p,
)

MASTER = REPO / "kics_disclosure.json"


def find_scr_anchor(pdf: Path):
    """'(1)공통적용경과조치' 표의 맨 마지막 행 '지급여력기준금액' 2값을 읽는다."""
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()
    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    if not matched:
        return None
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    def norm(s):
        return s.replace(" ", "")

    # "지급여력기준금액" 이 여러번 나올 수 있어(상단 세부표에도 있음) 마지막 occurrence 를 쓴다
    # (1)표는 항상 그 표의 맨 끝 행이므로.
    last_idx = None
    for k, l in enumerate(lines):
        if norm(l) == "지급여력기준금액":
            last_idx = k
    if last_idx is None:
        return None
    vals, j = [], last_idx + 1
    while j < len(lines) and len(vals) < 2:
        t = lines[j].replace(" ", "")
        if t == "" or t in DECOR:
            j += 1
            continue
        if NUMRE.match(t) or t in ZERO:
            vals.append(_num(t))
            j += 1
            continue
        break
    if len(vals) == 2:
        return vals[0], vals[1]
    if len(vals) == 1:
        return vals[0], vals[0]
    return None


def main() -> int:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_cq = {}
    name = {}
    for r in rows:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    scale1, scale100, ambiguous, noanchor = [], [], [], []
    for (c, q), items in sorted(by_cq.items()):
        if 47 not in items:  # 우리가 이미 적재한 (회사,분기)만
            continue
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            continue
        try:
            anchor = find_scr_anchor(pdf)
        except Exception as e:  # noqa: BLE001
            noanchor.append((c, q, f"EXC:{e}"))
            continue
        if anchor is None:
            noanchor.append((c, q))
            continue
        raw_pre, raw_post = anchor
        m14 = items.get(14)
        if m14 is None:
            noanchor.append((c, q))
            continue
        m14_pre = _num(m14.get("값"))
        if not m14_pre:
            noanchor.append((c, q))
            continue
        ratio = raw_pre / m14_pre
        if 0.99 < ratio < 1.01:
            scale1.append((c, q, raw_pre, m14_pre, ratio))
        elif 99 < ratio < 101:
            scale100.append((c, q, raw_pre, m14_pre, ratio))
        else:
            ambiguous.append((c, q, raw_pre, m14_pre, ratio))

    print(f"scale=1(이미 억원) {len(scale1)}  |  scale=100(백만원, /100 맞음) {len(scale100)}  |  "
          f"애매 {len(ambiguous)}  |  앵커없음 {len(noanchor)}")
    print("\n=== scale=1 (억원, 회사) — /100 하면 안 되는 케이스 ===")
    comp1 = sorted({c for c, *_r in scale1})
    print(comp1)
    for c, q, rp, m, ra in scale1[:40]:
        print(f"  {c} {name[c]:<14} {q}  raw전={rp}  master14전={m}  ratio={ra:.4f}")
    print(f"\n=== ambiguous 상세 ({len(ambiguous)}) ===")
    for c, q, rp, m, ra in ambiguous[:30]:
        print(f"  {c} {name[c]:<14} {q}  raw전={rp}  master14전={m}  ratio={ra:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
