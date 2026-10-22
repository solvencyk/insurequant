import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
out = []
def shape(o, d=0, maxd=3):
    if isinstance(o, dict):
        return {k: (shape(v, d+1, maxd) if d < maxd else type(v).__name__) for k, v in list(o.items())[:30]}
    if isinstance(o, list):
        return [len(o), shape(o[0], d+1, maxd) if o and d < maxd else (type(o[0]).__name__ if o else None)]
    if isinstance(o, str):
        return o[:60]
    return o
for c in ["KR0005","KR0032","KR0070","KR0082","KR0083","KR0087","KR0104"]:
    p = json.loads((E / f"plan_{c}.json").read_text(encoding="utf-8"))
    out.append("=== " + c)
    out.append(json.dumps(shape(p), ensure_ascii=False, indent=1)[:6000])
(Path(__file__).parent / "peek_plans.txt").write_text("\n".join(out), encoding="utf-8")
