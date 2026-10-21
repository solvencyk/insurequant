import glob, hashlib
from pathlib import Path
def main_xml(fy):
    c = glob.glob(f"data/dart/{fy}/raw/KR0073_*/xml/*.xml") + glob.glob(f"data/dart/{fy}/raw/KR0073_*/*.xml")
    c = [x for x in c if "_00" not in Path(x).name]
    byname = {}
    for x in c: byname.setdefault(Path(x).name, x)
    assert len(byname) == 1, (fy, c)
    return list(byname.values())[0]
