"""Dump AIA's '1.일반사항' PL prose paragraph from every filed year, and test the live
extract_tier2_aia regexes against each, to see exactly which one fails."""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DIRS = sorted(glob.glob(str(ROOT / "data/dart/FY*/raw/KR0080_*")))

NEEDLES = ["당사의 금년도 영업이익은", "재보험손익은", "보험손익", "투자손익", "영업이익"]


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", s)


for d in DIRS:
    print("=" * 100)
    print(d.replace(str(ROOT) + "\\", "").replace("\\", "/"))
    xmls = sorted(glob.glob(d + "/*.xml")) + sorted(glob.glob(d + "/xml/*.xml"))
    print(f"  xml files: {len(xmls)}")
    found_any = False
    for x in xmls:
        try:
            raw = open(x, "rb").read().decode("utf-8")
        except (UnicodeDecodeError, OSError) as e:
            print(f"  [{Path(x).name}] decode fail: {e}")
            continue
        hits = {n: raw.count(n) for n in NEEDLES}
        print(f"  [{Path(x).name}] size={len(raw):,} hits={hits}")
        # the handler's exact trigger
        trig = ("당사의 금년도 영업이익은" in raw and "재보험손익은" in raw)
        print(f"      handler trigger ('당사의 금년도 영업이익은' AND '재보험손익은') = {trig}")
        # look for ANY paragraph mentioning 영업이익 + 보험손익 near each other
        for m in re.finditer(r"영업이익은", raw):
            seg = strip_tags(raw[max(0, m.start() - 400): m.start() + 1600])
            if "보험손익" in seg:
                found_any = True
                print("      --- paragraph context ---")
                print("      " + seg[:1500])
                print("      -------------------------")
                break
    if not found_any:
        print("  (no 영업이익은+보험손익 paragraph found)")
