"""Blind spot: 적용사 (company,quarter) where the 적용후 세부(29-35 / 36-40) can never be
verified because the PARENT 적용후 (item17 / item19) is missing -> mmult check skips.
Also flags subs후 == subs전 while the parent전!=후 (i.e. ③표 미반영 signature)."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
APPLIERS = frozenset({"KR0070","KR0071","KR0072","KR0073","KR0076","KR0082","KR0083",
                      "KR0097","KR0100","KR1010","KR1011","KR0104","KR0049","KR0002",
                      "KR0003","KR0004","KR0005","KR0032"})
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
m = defaultdict(dict); name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기"); name[c] = r.get("원수사명", c)
    try: it = int(r["항목번호"])
    except (TypeError, ValueError, KeyError): continue
    m[(c, q)][it] = (num(r.get("값")), num(r.get("값_적용후")))
PARENTS = {17: range(29, 36), 19: range(36, 41)}
orphan, copied = [], []
for (c, q), d in sorted(m.items()):
    if c not in APPLIERS: continue
    for p, kids in PARENTS.items():
        pre_p, post_p = d.get(p, (None, None))
        subs = [(k, d.get(k, (None, None))) for k in kids if k in d]
        if not subs: continue
        n_post = sum(1 for _, (_, po) in subs if po is not None)
        if post_p is None and n_post:
            orphan.append((c, q, p, n_post, len(subs)))
        # ③표 미반영 signature: 부모전!=부모후 여야 하는데 세부후가 전부 전값 그대로
        if post_p is not None and pre_p is not None and abs(post_p - pre_p) > 1.0:
            same = [k for k, (pr, po) in subs if pr is not None and po is not None and abs(pr - po) < 0.005]
            if len(same) == len(subs) and subs:
                copied.append((c, q, p, len(subs)))
print(f"## 부모후 결측인데 세부후는 있음 (mmult 영구 skip) = {len(orphan)}")
for c, q, p, n, tot in orphan:
    print(f"   {c} {name.get(c,c)} {q} parent item{p}: 세부후 {n}/{tot} present, 부모후 결측")
print(f"\n## 부모 전!=후 인데 세부후 전량 == 세부전 (표 미반영 의심) = {len(copied)}")
for c, q, p, n in copied:
    print(f"   {c} {name.get(c,c)} {q} parent item{p}: 세부 {n}개 전부 후=전")
