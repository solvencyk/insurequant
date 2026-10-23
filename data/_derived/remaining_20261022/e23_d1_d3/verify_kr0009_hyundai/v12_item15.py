import sys
sys.path.insert(0, ".")
import vmaster
PH, PW = vmaster.load_all("PL_breakdown")
for q in ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]:
    print(q, "item15 HEAD", PH[(q,15)]["값"], PH[(q,15)]["값_당분기"], "WORK", PW[(q,15)]["값"], PW[(q,15)]["값_당분기"])
g = vmaster.work("data/_gold/user_pl_cells.json")
n = g["null_dangi"]["cells"]
print(type(n).__name__, [x for x in (n if isinstance(n, list) else n.items()) if "KR0009" in str(x)][:20])
