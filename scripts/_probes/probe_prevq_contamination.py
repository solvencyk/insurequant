"""Sweep: 값_적용후 that equals the PREVIOUS quarter's 값 (3-quarter comparison column-shift).

Signature of the KR0050 2023.2Q bug: the [경과조치 적용 전 지급여력비율 세부] table is laid out as
당분기 / 전분기 / 전전분기 and the extractor landed the 전분기 column in the 값_적용후 slot.
Flags a (company, quarter) when >=3 core items satisfy  후(q) == 전(q-1) != 전(q).
"""
import io, json, sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def qkey(q):
    y, qq = q.split(".")
    return (int(y), int(qq[0]))


byci = defaultdict(dict)  # (code, item) -> {quarter: (pre, post)}
name = {}
for r in rows:
    c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
    name[c] = r.get("원수사명", c)
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue
    if c and q:
        byci[(c, it)][q] = (num(r.get("값")), num(r.get("값_적용후")))

CORE = list(range(1, 29))
hits = defaultdict(list)
for (c, it), qv in byci.items():
    if it not in CORE:
        continue
    qs = sorted(qv, key=qkey)
    for i in range(1, len(qs)):
        q, pq = qs[i], qs[i - 1]
        pre, post = qv[q]
        ppre, _ = qv[pq]
        if post is None or pre is None or ppre is None:
            continue
        if abs(post - pre) < 0.005:
            continue  # 후=전 (정상 미적용)
        if abs(post - ppre) < 0.005:
            hits[(c, q, pq)].append((it, pre, post))

print(f"# (회사,분기) with >=1 item where 후(q) == 전(직전분기) != 전(q)")
for (c, q, pq), items in sorted(hits.items()):
    tag = "  <<< STRONG" if len(items) >= 3 else ""
    print(f"\n{c} {name.get(c,c)} {q} (직전={pq})  items={len(items)}{tag}")
    for it, pre, post in items:
        print(f"    item{it:>2}: 전={pre!s:>14}  후={post!s:>14}  (=직전분기 전)")
