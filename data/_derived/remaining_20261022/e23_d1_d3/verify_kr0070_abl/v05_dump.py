import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
fy = sys.argv[1]; lo = int(sys.argv[2]); hi = int(sys.argv[3])
for t in vlib.tables(fy):
    if t["start"] <= hi and t["end"] >= lo:
        print("TABLE %d-%d rows=%d" % (t["start"], t["end"], len(t["rows"])))
        for r in t["rows"]:
            print(r["line"], " | ".join(c[1][:46] for c in r["cells"]))
