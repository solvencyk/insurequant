import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
for fy, st in (("FY2024_Q1", 41440), ("FY2024_Q2", 43099), ("FY2024_Q3", 42167), ("FY2024_Q4", 58224)):
    for t in vlib.tables(fy):
        if t["start"] == st:
            print("==", fy, st)
            for r in t["rows"]:
                print(r["line"], " | ".join(c[1][:48] for c in r["cells"]))
