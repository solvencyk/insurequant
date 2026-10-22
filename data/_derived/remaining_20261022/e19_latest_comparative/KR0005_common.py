import sys, io, re
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kyobo_pl_restate_dryrun_20261021")
import stmt_parse as P
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT/"data/_derived/remaining_20261022/e19_latest_comparative"
FYS = ["FY2023_Q3","FY2023_Q4","FY2024_Q1","FY2024_Q2","FY2024_Q3","FY2024_Q4","FY2025_Q1","FY2025_Q2"]
def main_xml(fy):
    d = sorted((ROOT/"data/dart"/fy/"raw").glob("KR0005_*"))[0]
    c = [p for p in list(d.glob("*.xml"))+list(d.glob("xml/*.xml")) if not p.stem.endswith("_00760")]
    return sorted(c, key=lambda p: p.stat().st_size, reverse=True)[0]
def rel(p): return str(Path(p).relative_to(ROOT)).replace("\\","/")
def num(t):
    t = t.strip().replace(",","")
    if t in ("","-"): return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v
