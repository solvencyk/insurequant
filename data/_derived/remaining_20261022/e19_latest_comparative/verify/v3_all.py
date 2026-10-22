import sys, os
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vrd
V = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
B = {"KR0082": ["2023.3Q"], "KR0032": ["2023.4Q","2024.1Q","2024.2Q","2024.3Q"], "KR0104": ["2023.3Q"],
     "KR0087": ["2023.4Q","2024.1Q","2024.2Q","2024.3Q"], "KR0070": ["2024.1Q","2024.2Q","2024.3Q"],
     "KR0083": ["2024.1Q","2024.2Q"], "KR0005": ["2023.3Q","2023.4Q","2024.1Q","2024.2Q"]}
def later(q):
    y, r = q.split("."); return "%d.%s" % (int(y) + 1, r)
os.makedirs(V + "stmts", exist_ok=True)
log = []
seen = set()
for code, qs in B.items():
    for q in qs:
        for per in (q, later(q)):
            if (code, per) in seen: continue
            seen.add((code, per))
            files = vrd.find_xml(code, per)
            log.append("%s %s files=%s" % (code, per, [os.path.basename(f) for f in files]))
            for p in files:
                t = vrd.read_text(p)
                n = 0
                lines = []
                for tb in vrd.tables(t):
                    if "손익계산서" in tb["title"] and len(tb["rows"]) > 15 and "자본변동" not in tb["rows"][0][0]:
                        n += 1
                        lines.append("TABLE line=%d title=%s file=%s" % (tb["line"], tb["title"], os.path.basename(p)))
                        for r in tb["rows"]:
                            lines.append(" | ".join(r))
                        lines.append("")
                log.append("   tables=%d" % n)
                open(V + "stmts/%s_%s_%s.txt" % (code, per, os.path.basename(p)), "w", encoding="utf-8").write("\n".join(lines))
open(V + "v3_all_log.txt", "w", encoding="utf-8").write("\n".join(log))
