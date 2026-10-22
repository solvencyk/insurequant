import sys; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, v10_note_engine as E
R=E.ROOT
for f in ("data/dart/FY2025_Q2/raw/KR0003_롯데손해보험/xml/20250814003966.xml","data/dart/FY2025_Q3/raw/KR0003_롯데손해보험/xml/20251114002985.xml"):
    d=xmlrd.get(R+f)
    pri=E.lotte_split(d)
    print(f.split("/")[-1],[(t["start"],len(t["rows"])) for t in pri])
