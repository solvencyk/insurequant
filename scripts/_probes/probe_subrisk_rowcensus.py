"""Row-level census: (company, quarter) that have SOME of 29-35 (or 36-40) rows but not all."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
have = defaultdict(set)
name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기")
    name[c] = r.get("원수사명", c)
    try:
        have[(c, q)].add(int(r["항목번호"]))
    except (TypeError, ValueError, KeyError):
        pass
for label, group in (("생명장기 29-35", set(range(29, 36))), ("시장 36-40", set(range(36, 41)))):
    out = []
    for (c, q), items in sorted(have.items()):
        got = items & group
        if got and got != group:
            out.append((c, q, sorted(group - got)))
    print(f"\n## {label}: partial-row (회사,분기) = {len(out)}")
    for c, q, miss in out:
        print(f"   {c} {name.get(c,c)} {q}: rows missing {miss}")
