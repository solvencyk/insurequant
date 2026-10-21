"""Read-only: YTD and quarterly (값_당분기) closure of KR0073 for the live master and candidate masters.

YTD closure   : I1+I2+I3+I4+I5-I6 using 값
Quarterly     : 값_당분기 I1+I2+I3+I4+I5-I6  (I1 당분기 = previous quarter close; flows = YTD differences)
Prints the gap (억원) per quarter; a quarterly gap != 0 means the YTD openings differ inside the FY (source restatement).
Usage: python quarterly_closure.py <master.json> [<master2.json> ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
QORD = lambda q: int(q[:4]) * 10 + int(q[5])


def vec(rows, fld):
    d = {}
    for r in rows:
        if r.get("원보험사코드") != "KR0073":
            continue
        d.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get(fld)
    return d


def gaps(path):
    rows = json.load(open(path, encoding="utf-8"))
    ytd, qtr = vec(rows, "값"), vec(rows, "값_당분기")
    out = {}
    for q in sorted(ytd, key=QORD):
        y, d = ytd[q], qtr[q]
        gy = round(sum(y[i] for i in (1, 2, 3, 4, 5)) - y[6], 2)
        gq = round(sum(d[i] for i in (1, 2, 3, 4, 5)) - d[6], 2)
        out[q] = (gy, gq)
    return out


def main():
    paths = sys.argv[1:] or [str(ROOT / "CSM_waterfall.json")]
    res = {p: gaps(p) for p in paths}
    qs = sorted({q for g in res.values() for q in g}, key=QORD)
    hdr = f"{'quarter':8s}" + "".join(f" | {Path(p).stem[:18]:>22s}" for p in paths)
    print(hdr)
    print("(each cell: YTD gap / quarterly gap, 억원)")
    for q in qs:
        if QORD(q) > 20262:
            continue
        print(f"{q:8s}" + "".join(f" | {str(res[p].get(q, ('-', '-'))):>22s}" for p in paths))


if __name__ == "__main__":
    main()
