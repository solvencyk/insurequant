import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
out = []
for c in ["KR0005","KR0032","KR0070","KR0082","KR0083","KR0087","KR0104"]:
    p = json.loads((E / f"plan_{c}.json").read_text(encoding="utf-8"))
    out.append("=== " + c)
    for cell in p["cells"][:3] + [x for x in p["cells"] if x.get("derivation","direct print")!="direct print"][:2]:
        d = {k: cell.get(k) for k in ("quarter","item","old","new","unit","source_unit","xml_file","xml_line","xml_lines","xml_label","derivation","second_source","xml_period_column","xml_column")}
        out.append(json.dumps(d, ensure_ascii=False)[:1200])
(Path(__file__).parent / "peek3.txt").write_text("\n".join(out), encoding="utf-8")
