"""Full dump of items 1-23,27-40,47-54 for the 16 life companies at 2026.1Q and 2026.2Q,
both 값 and 값_적용후, straight from the live kics_disclosure.json master. Ground truth for
planning which cells genuinely need raw extraction vs. can be derived/mirrored/copied.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

CODES = ["KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0080", "KR0082", "KR0083",
         "KR0087", "KR0094", "KR0097", "KR0099", "KR0100", "KR0104", "KR1010", "KR1011"]
ITEMS = list(range(1, 24)) + [27, 28] + list(range(29, 41)) + list(range(47, 55))

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

idx = {}
name = {}
for r in records:
    c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
    if c not in CODES or q not in ("2026.1Q", "2026.2Q"):
        continue
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue
    name[c] = r.get("회사명", c)
    idx.setdefault((c, q), {})[it] = (r.get("값"), r.get("값_적용후", "<NOKEY>"), r.get("항목명"))

for c in CODES:
    print(f"===== {c} {name.get(c,'?')} =====")
    for q in ("2026.1Q", "2026.2Q"):
        m = idx.get((c, q), {})
        print(f"  --- {q} ---")
        for it in ITEMS:
            if it in m:
                v, vp, nm = m[it]
                print(f"    item{it:<3} [{nm}]  값={v!r}  값_적용후={vp!r}")
    print()
