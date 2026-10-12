# -*- coding: utf-8 -*-
"""c3: grep the DART 사업보고서 (FY2025) XML of the given companies for the K-ICS capital-detail lines
(보완자본 재분류 / 인정한도 초과 / 보완자본 자본증권), to see whether the filing breaks item 13 down. Read-only."""
import re
import sys
import glob

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pats = ["재분류", "인정한도", "보완자본 자본증권", "보완자본자본증권", "기본자본 자본증권", "신종자본증권"]
for code in sys.argv[1:]:
    for d in sorted(glob.glob(ROOT + "/data/dart/FY2025_Q4/raw/%s_*" % code)):
        for fn in sorted(glob.glob(d + "/*.xml")):
            try:
                txt = open(fn, encoding="utf-8", errors="replace").read()
            except Exception as e:
                print("ERR", fn, e)
                continue
            clean = re.sub(r"<[^>]+>", " ", txt)
            clean = re.sub(r"\s+", " ", clean)
            print("== %s  (%d chars)" % (fn.replace(ROOT + "/", ""), len(clean)))
            for p in pats:
                hits = [m.start() for m in re.finditer(re.escape(p), clean)]
                print("   %-14s hits=%d" % (p, len(hits)))
                for h in hits[:6]:
                    print("      ...%s..." % clean[max(0, h - 90): h + 160])
