import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vrd
code, per = sys.argv[1], sys.argv[2]
out = []
for p in vrd.find_xml(code, per):
    t = vrd.read_text(p)
    for tb in vrd.tables(t):
        if "포괄손익계산서" in tb["title"] and len(tb["rows"]) > 20:
            out.append("TABLE line=%d title=%s" % (tb["line"], tb["title"]))
            for r in tb["rows"]:
                out.append(" | ".join(r))
open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify/v3_rows_%s_%s.txt" % (code, per), "w", encoding="utf-8").write("\n".join(out))
