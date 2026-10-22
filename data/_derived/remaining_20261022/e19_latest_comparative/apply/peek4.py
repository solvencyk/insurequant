import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
out = []
for c in ["KR0005","KR0032","KR0070","KR0082","KR0083","KR0087","KR0104"]:
    p = json.loads((E / f"plan_{c}.json").read_text(encoding="utf-8"))
    out.append("=== " + c)
    kinds = {}
    for cell in p["cells"]:
        k = (type(cell.get("xml_line")).__name__, type(cell.get("xml_lines")).__name__, cell.get("derivation"), cell.get("source_unit"), cell.get("unit"))
        kinds.setdefault(k, []).append((cell["quarter"], cell["item"]))
    for k, v in kinds.items():
        out.append(f"{k}: n={len(v)} e.g. {v[:4]}")
    # print one multi-line example
    for cell in p["cells"]:
        if isinstance(cell.get("xml_line"), list) or (isinstance(cell.get("xml_lines"), list) and len(cell["xml_lines"])>1):
            out.append("MULTI " + json.dumps({k: cell.get(k) for k in ("quarter","item","new","xml_line","xml_lines","derivation")}, ensure_ascii=False)[:900])
            break
    for cell in p["cells"][:1]:
        out.append("SINGLE " + json.dumps({k: cell.get(k) for k in ("quarter","item","new","xml_line","xml_lines","derivation")}, ensure_ascii=False)[:600])
(Path(__file__).parent / "peek4.txt").write_text("\n".join(out), encoding="utf-8")
