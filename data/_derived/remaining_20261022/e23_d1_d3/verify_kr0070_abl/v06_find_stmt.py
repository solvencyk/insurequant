import sys, re
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    lines = vlib.load(fy)
    txt = "\n".join(lines)
    print(fy, "lines", len(lines), "연결 count", txt.count("연결"), "SUBSID", txt.count("종속"))
    ts = vlib.tables(fy)
    for t in ts:
        if t["rows"] and any(c[1].strip() == "보험손익" for r in t["rows"][:6] for c in r["cells"][:1]):
            # find unit/title text above: scan back 200 lines for <P> text
            prev = []
            for j in range(t["start"] - 1, max(0, t["start"] - 140), -1):
                s = re.sub(r"<[^>]*>", "", lines[j - 1]).strip()
                if s: prev.append((j, s))
                if len(prev) >= 6: break
            print("  stmt table", t["start"], t["end"], "rows", len(t["rows"]), "hdr:", [c[1] for c in t["rows"][0]["cells"]], [c[1] for c in t["rows"][1]["cells"]] if len(t["rows"])>1 else "")
            print("     prev:", prev)
