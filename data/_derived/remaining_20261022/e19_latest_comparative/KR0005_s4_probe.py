from KR0005_common import *
out = io.open(EVD/"KR0005_s4_probe.txt","w",encoding="utf-8")
for fy in FYS:
    p = main_xml(fy)
    L = P.read_lines(p)
    out.write(f"=== {fy} {rel(p)} lines={len(L)}\n")
    for i,ln in enumerate(L, start=1):
        if "<TITLE" in ln:
            t = P.clean(ln)
            if "재무제표" in t:
                out.write(f"   L{i} {t}\n")
    out.write(f"   sections {P.sections(L)}\n")
out.close()
