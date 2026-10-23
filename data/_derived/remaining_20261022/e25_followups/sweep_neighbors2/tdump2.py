# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E
import s2lib
import e21_t2 as T
code, fy = sys.argv[1:3]
KEY = re.compile(sys.argv[3] if len(sys.argv) > 3 else r"예상|발생.*보험금|실제|회수|보험계약마진.*(상각|제공|이전)|제공.*보험계약마진|위험(조정|해제)")
path = T.main_path(code, fy)
lines, s0, tabs = s2lib.tables_sep2(path)
print(path.name, "sep", s0, "ntabs", len(tabs))
for t, rows in tabs:
    labs = [E.lab(r) for r in rows]
    hit = [r for r in rows if KEY.search(E.lab(r)) and any(c["val"] is not None for c in r["cells"][1:])]
    hasrev = sum(1 for x in labs if re.search(r"위험(조정|해제)", x)) and sum(1 for x in labs if re.search(r"보험계약마진", x))
    if not hit or not hasrev: continue
    print(f"--- table@L{t['start']} rows={len(rows)} cap={E.nl(t['caption'] or '')[:60]!r}")
    for r in rows[:3]:
        print("   H", " | ".join(c["text"][:14] for c in r["cells"])[:150])
    for r in rows:
        lb = E.lab(r)
        nonum = not any(c["val"] is not None or c["text"].strip() in ("-",) for c in r["cells"][1:])
        if KEY.search(lb) or (nonum and len(lb) < 14):
            print("   ", f"L{r['tr_line']}", " | ".join(c["text"][:22] for c in r["cells"])[:200])
