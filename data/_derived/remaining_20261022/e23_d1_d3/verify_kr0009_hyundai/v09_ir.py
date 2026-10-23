import openpyxl, json, sys
sys.path.insert(0, ".")
import vmaster
R = vmaster.ROOT
FILES = {"2023.1Q": R + "/data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx",
         "2023.2Q": R + "/data/ir/FY2024_Q2/raw/KR0009_현대해상/d33c3d385303361798f75607750ca360.xlsx",
         "2023.4Q": R + "/data/ir/FY2024_Q4/raw/KR0009_현대해상/2a11f147695dacd4665923059eceed11.xlsx"}
DART = {"2023.1Q": 246045.277087, "2023.2Q": 415652.294609, "2023.4Q": 526589.620124}
PH, PW = vmaster.load_all("PL_breakdown")
prov = vmaster.work("PL_breakdown_provenance.json")
pc = {(c["quarter"], c["item_block"]): c for c in prov["cells"] if c["company_code"] == "KR0009"}
out = []
def P(s=""):
    print(s); out.append(s)
for q, f in FILES.items():
    wb = openpyxl.load_workbook(f, data_only=True, read_only=False)
    ws = wb["(3) UW Income"]
    g = lambda a: ws[a].value
    P("== %s %s sheet dims %s" % (q, f.split("/")[-1], ws.dimensions))
    P(" L4 %r  L6 %r  K6 %r" % (g("L4"), g("L6"), g("K6")))
    for lab, cell, lc, bc in (("장기(2)", "L26", "C26", "B12"), ("자동차(13)", "L30", "C30", "B27"), ("일반(14)", "L11", "C11", "B8")):
        P(" %-10s %s=%r  label %s=%r  block %s=%r  K(3m)=%r" % (lab, cell, g(cell), lc, g(lc), bc, g(bc), g("K" + cell[1:])))
    tot = g("L31"); legs = g("L26") + g("L30") + g("L11")
    P(" L31 total=%r ; sum legs=%r ; DART separate 보험손익(prior cum) 백만원 %r" % (tot, legs, DART[q]))
    P(" total_unit: sheet unit %r => 백만원 legs sum %.6f vs DART %.6f diff %.6f" % (g("L4"), legs, DART[q], legs - DART[q]))
    if q != "2023.4Q":
        for it, c in ((2, "L26"), (13, "L30"), (14, "L11")):
            m = PW[(q, it)]["값"]
            P("   master item %d WORK %s HEAD %s sheet %s diff %.6f" % (it, m, PH[(q, it)]["값"], g(c), m - g(c)))
        # 3-month column
        P("   3-month col K legs: %r / %r / %r ; K31 %r" % (g("K26"), g("K30"), g("K11"), g("K31")))
    else:
        for it, c in ((2, "L26"), (13, "L30"), (14, "L11")):
            m = PW[(q, it)]["값"]
            P("   2023.4Q live item %d = %s ; IR annual %s ; gap %.6f" % (it, m, g(c), m - g(c)))
        P("   live legs sum %.6f vs live item1 %.6f gap %.6f" % (sum(PW[(q, i)]["값"] for i in (2, 13, 14)), PW[(q, 1)]["값"], PW[(q, 1)]["값"] - sum(PW[(q, i)]["값"] for i in (2, 13, 14))))
for q in ("2023.1Q", "2023.2Q"):
    P("%s legs sum from master WORK %.6f ; item1 WORK %.6f ; gap %.6f" % (q, sum(PW[(q, i)]["값"] for i in (2, 13, 14)), PW[(q, 1)]["값"], PW[(q, 1)]["값"] - sum(PW[(q, i)]["값"] for i in (2, 13, 14))))
for (q, b), c in sorted(pc.items()):
    if q in ("2023.1Q", "2023.2Q", "2023.4Q"):
        hows = [(s["how"], s.get("items"), s.get("sheet"), s.get("cells"), s.get("header"), s.get("printed")) for s in c.get("source_files", [])]
        P("prov %s %s source_id %s resolution %s : %s" % (q, b, c.get("source_id"), c.get("resolution"), hows))
open("v09_ir.txt", "w", encoding="utf-8").write("\n".join(out))
