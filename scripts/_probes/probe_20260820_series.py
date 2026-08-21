"""Print item 1/2/3/14/15/27/28 전/후 series across quarters for given companies."""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
codes = sys.argv[1].split(",")
items = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["1","2","3","14","15","27"])]
for code in codes:
    sub = [r for r in rows if r["원보험사코드"] == code and r["항목번호"] in items]
    qs = sorted({r["공시분기"] for r in sub}, key=lambda q: (q.split(".")[0], q.split(".")[1]))
    name = sub[0]["원수사명"] if sub else "?"
    print(f"\n===== {code} {name} =====")
    hdr = "분기".ljust(9) + "".join(f"| i{i} 전/후".ljust(30) for i in items)
    print(hdr)
    for q in qs:
        line = q.ljust(9)
        for i in items:
            cell = next((r for r in sub if r["공시분기"] == q and r["항목번호"] == i), None)
            if cell is None:
                line += "| -".ljust(30)
            else:
                line += f"| {cell.get('값')} / {cell.get('값_적용후')}".ljust(30)
        print(line)
