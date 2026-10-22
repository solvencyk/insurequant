import sys, json
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vrd
code, per = sys.argv[1], sys.argv[2]
out = []
for p in vrd.find_xml(code, per):
    out.append("FILE " + p)
    t = vrd.read_text(p)
    for tb in vrd.tables(t):
        if "포괄손익계산서" in tb["title"] or "손익계산서" in tb["title"]:
            out.append("TABLE line=%d title=%s rows=%d firstrow=%s" % (tb["line"], tb["title"], len(tb["rows"]), tb["rows"][:2]))
open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify/v3_dump_%s_%s.txt" % (code, per), "w", encoding="utf-8").write("\n".join(out))
