# -*- coding: utf-8 -*-
"""READ-ONLY pass4 helper: list the DART XML tables whose cleaned text contains ALL needles (spaces removed), with physical line range, the text just before the table (caption / unit / 당분기-전분기 marker)
and, for the rows whose first cell contains ROWNEEDLE (optional), the numeric cells with their physical lines.
usage: t_find_tables.py <xml path> <needle1,needle2,...> [ROWNEEDLE]"""
import html
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
needles = [n.replace(" ", "") for n in sys.argv[2].split(",")]
rowneedle = sys.argv[3].replace(" ", "") if len(sys.argv) > 3 else None
txt = open(path, encoding="utf-8", errors="replace").read()
lines = txt.split("\n")
_tag = re.compile(r"<[^>]+>")


def clean(s):
    s = _tag.sub("", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


n = 0
for m in re.finditer(r"<TABLE\b.*?</TABLE>", txt, flags=re.S | re.I):
    blob = clean(m.group(0)).replace(" ", "")
    if not all(k in blob for k in needles):
        continue
    n += 1
    start = txt.count("\n", 0, m.start()) + 1
    end = start + m.group(0).count("\n")
    pre = [clean(x) for x in lines[max(0, start - 16):start - 1]]
    print(f"##### table#{n} lines {start}-{end}  preceding: " + " | ".join(x for x in pre if x)[:300])
    if rowneedle:
        for rm in re.finditer(r"<TR\b.*?</TR>", m.group(0), flags=re.S | re.I):
            cells = []
            for cm in re.finditer(r"<(TD|TH|TE|TU)\b(.*?)>(.*?)</\1>", rm.group(0), flags=re.S | re.I):
                cells.append((start + m.group(0).count("\n", 0, rm.start()) + rm.group(0).count("\n", 0, cm.start()), clean(cm.group(3))))
            if any(rowneedle in c.replace(" ", "") for _l, c in cells[:2]):
                lnr = start + m.group(0).count("\n", 0, rm.start())
                print(f"   R{lnr:>6} " + " | ".join(f"{c[:60]}@{l}" if re.search(r"\d", c) and len(c) < 20 else c[:90] for l, c in cells))
print(f"total matching tables: {n}")
