import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
p = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
L = ["top keys " + str(list(p.keys()))]
for c in p["cells"]:
    if c["company_code"] == "KR0104" and c["quarter"] in ("2023.2Q", "2023.3Q", "2023.4Q"):
        L.append(json.dumps(c, ensure_ascii=False)[:1500])
conf = json.loads((ROOT / "data/_gold/user_pl_confirmed_cells.json").read_text(encoding="utf-8"))
s = json.dumps(conf, ensure_ascii=False)
L.append("confirmed mentions KR0104: %d ; 농협생명: %d" % (s.count("KR0104"), s.count("농협생명")))
(Path(__file__).resolve().parent / "KR0104_peek_prov.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
