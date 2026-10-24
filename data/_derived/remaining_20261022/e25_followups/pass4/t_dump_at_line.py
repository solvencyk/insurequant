# -*- coding: utf-8 -*-
"""READ-ONLY pass4 helper: print the DART XML table that contains physical line LINE (rows with physical row line numbers and cleaned cells) plus the 12 text lines that precede the table (caption / unit).
usage: t_dump_at_line.py <xml path> <line> [<line> ...]"""
import html
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
path = sys.argv[1]
targets = [int(x) for x in sys.argv[2:]]
txt = open(path, encoding="utf-8", errors="replace").read()
lines = txt.split("\n")
_tag = re.compile(r"<[^>]+>")


def clean(s):
    s = _tag.sub("", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


for m in re.finditer(r"<TABLE\b.*?</TABLE>", txt, flags=re.S | re.I):
    start = txt.count("\n", 0, m.start()) + 1
    end = start + m.group(0).count("\n")
    for t in targets:
        if start <= t <= end:
            print(f"##### table lines {start}-{end} contains L{t}")
            pre = [clean(x) for x in lines[max(0, start - 14):start - 1]]
            print("   preceding text: " + " | ".join(x for x in pre if x)[:600])
            for rm in re.finditer(r"<TR\b.*?</TR>", m.group(0), flags=re.S | re.I):
                lnr = start + m.group(0).count("\n", 0, rm.start())
                cells = []
                for cm in re.finditer(r"<(TD|TH|TE|TU)\b(.*?)>(.*?)</\1>", rm.group(0), flags=re.S | re.I):
                    cells.append((start + m.group(0).count("\n", 0, rm.start()) + rm.group(0).count("\n", 0, cm.start()), clean(cm.group(3))))
                print(f"   R{lnr:>6} " + " | ".join(f"{c}@{l}" if re.search(r"\d", c) and len(c) < 20 else c for l, c in cells))
