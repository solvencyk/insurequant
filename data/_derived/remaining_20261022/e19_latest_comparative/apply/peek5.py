import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
E = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
out = []
for code, q, item in [("KR0032","2024.3Q",17), ("KR0005","2024.2Q",18), ("KR0005","2024.2Q",32)]:
    plan = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
    c = [x for x in plan["cells"] if x["quarter"]==q and x["item"]==item][0]
    out.append(json.dumps({k: c.get(k) for k in ("xml_file","xml_line","xml_lines","new","xml_label")}, ensure_ascii=False)[:900])
    L = (ROOT / c["xml_file"]).read_text(encoding="utf-8", errors="replace").split("\n")
    lns = c["xml_line"] if isinstance(c["xml_line"], list) else [c["xml_line"]]
    for ln in lns:
        out.append(f"--- L{ln}")
        for k in range(ln-6, ln+3):
            out.append(f"{k+1}: {L[k][:200]}")
(Path("peek5.txt")).write_text("\n".join(out), encoding="utf-8")
