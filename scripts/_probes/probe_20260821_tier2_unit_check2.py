# -*- coding: utf-8 -*-
"""tier2 단위판별 v2 — stdout 대신 파일에 직접 append, PDF별 예외 격리."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import (  # noqa: E402
    DECOR, NUMRE, ZERO, _num, _pdf, q2p,
)

MASTER = REPO / "kics_disclosure.json"
OUT = Path(sys.argv[1])


def find_scr_anchor(pdf: Path):
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

    results = []
    with OUT.open("w", encoding="utf-8") as f:
        for (c, q), items in sorted(by_cq.items()):
            if 47 not in items:
                continue
            pdf = _pdf(q2p(q), c)
            if pdf is None:
                continue
            try:
                anchor = find_scr_anchor(pdf)
            except Exception as e:  # noqa: BLE001
                f.write(f"EXC {c} {name[c]} {q}: {e}\n")
                f.flush()
                continue
            if anchor is None:
                f.write(f"NOANCHOR {c} {name[c]} {q}\n")
                f.flush()
                continue
            raw_pre, raw_post = anchor
            m14 = items.get(14)
            m14_pre = _num(m14.get("값")) if m14 else None
            if not m14_pre:
                f.write(f"NOM14 {c} {name[c]} {q}\n")
                f.flush()
                continue
            ratio = raw_pre / m14_pre
            tag = "SCALE1" if 0.99 < ratio < 1.01 else ("SCALE100" if 99 < ratio < 101 else "AMBIG")
            f.write(f"{tag} {c} {name[c]} {q}  raw전={raw_pre}  master14전={m14_pre}  ratio={ratio:.4f}\n")
            f.flush()
            results.append((tag, c, q))

    from collections import Counter
    cnt = Counter(t for t, _c, _q in results)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"\nSUMMARY: {dict(cnt)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
