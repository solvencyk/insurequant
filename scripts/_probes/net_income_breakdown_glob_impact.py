"""Measure the real impact of build_net_income_breakdown.py:550's missing xml/ glob (inbox/
parser/20260829T1600Z part 2), using the ACTUAL production `_resolve_raw_dirs` from that
module (not reimplemented) against the 11 SONBO companies it targets. For each company: how
many raw dirs does `_resolve_raw_dirs` find, how many collapse into the SAME `per_dir` key
(the dict-overwrite collision this probe also checks for, since quarterly dirs share an
rcept-less basename), and of the surviving per_dir entries, how many have zero XML under the
top-level/extracted/ glob (i.e. would `continue`-skip in main()'s loop) despite having real
XML under xml/. Read-only -- does not run main() or write net_income_breakdown.json.
"""
import glob
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os as _os
_os.chdir(ROOT)  # the module's glob patterns are relative to repo root

from scripts.build_net_income_breakdown import SONBO, _resolve_raw_dirs  # noqa: E402

total_dirs = 0
total_per_dir_entries = 0
total_collisions = 0
total_xml_miss = 0
total_xml_miss_but_has_xmlsubdir = 0

for name, kr in SONBO.items():
    dirs = _resolve_raw_dirs(name)
    total_dirs += len(dirs)
    per_dir = {}
    collisions = []
    for d in dirs:
        key = os.path.basename(d).split("_")[-1]
        if key in per_dir and per_dir[key] != d:
            collisions.append((key, per_dir[key], d))
        per_dir[key] = d
    total_per_dir_entries += len(per_dir)
    total_collisions += len(collisions)

    xml_miss = []
    for rcept, d in per_dir.items():
        xmls = glob.glob(d + "/*.xml") + glob.glob(d + "/extracted/*.xml")
        if not xmls:
            has_sub = os.path.isdir(d + "/xml") and bool(glob.glob(d + "/xml/*.xml"))
            xml_miss.append((rcept, d, has_sub))
            total_xml_miss += 1
            if has_sub:
                total_xml_miss_but_has_xmlsubdir += 1

    print(f"\n{kr} {name}: _resolve_raw_dirs found {len(dirs)} dirs -> "
          f"per_dir collapses to {len(per_dir)} keys "
          f"({len(collisions)} dict-overwrite collisions, i.e. dirs silently discarded)")
    if collisions:
        for key, lost, kept in collisions[:3]:
            print(f"    COLLISION key={key!r}: discarded={lost}  kept={kept}")
        if len(collisions) > 3:
            print(f"    ... ({len(collisions) - 3} more collisions)")
    for rcept, d, has_sub in xml_miss:
        flag = "HAS xml/ subdir with real XML (the reported blind spot)" if has_sub else "genuinely no xml"
        print(f"    per_dir entry key={rcept!r} dir={d}: 0 xml via current glob -- {flag}")

print(f"\n=== TOTALS across {len(SONBO)} SONBO companies ===")
print(f"_resolve_raw_dirs total dirs found:        {total_dirs}")
print(f"per_dir surviving entries (post-collision): {total_per_dir_entries}")
print(f"dirs silently discarded by key collision:   {total_collisions}")
print(f"per_dir entries with 0 xml via current glob: {total_xml_miss}")
print(f"  of which DO have real xml under xml/ (the blind spot): {total_xml_miss_but_has_xmlsubdir}")
