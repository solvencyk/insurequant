"""item29(사망위험액)=0 인데 raw '생명·장기손해보험위험액 현황' 표엔 값이 있는 셀 찾기."""
import io, json, re, sys
from collections import defaultdict
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
d = defaultdict(dict); name = {}
for r in rows:
    c, q = r["원보험사코드"], r["공시분기"]; name[c] = r.get("원수사명", c)
    try: d[(c, q)][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass
def q2p(q):
    y, qq = q.split("."); return f"FY{y}_Q{qq[0]}"
NUM = re.compile(r"^-?[\d,]+$")
hits = []
for (c, q), m in sorted(d.items()):
    pre29 = m.get(29, (None, None))[0]
    p17 = m.get(17, (None, None))[0]
    if pre29 is None or pre29 != 0 or not p17:
        continue
    raw = REPO / "data" / "disclosure" / q2p(q) / "raw"
    pdfs = sorted(raw.glob(f"{c}_*.pdf"))
    if not pdfs: continue
    am = [p for p in pdfs if "_amended" in p.name]
    pdf = max(am or pdfs, key=lambda p: p.stat().st_size)
    doc = fitz.open(pdf)
    found = None
    try:
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if "생명" not in t or "사망위험" not in t or "충격후" not in t:
                continue
            lines = [x.strip() for x in t.splitlines()]
            for j, l in enumerate(lines):
                if l.replace(" ", "") in ("사망위험", "사망위험액"):
                    vals = [x.replace(",", "") for x in lines[j+1:j+5]
                            if NUM.match(x.replace(" ", "").replace(",", ""))]
                    if vals:
                        v = max(float(x) for x in vals)
                        if v > 0:
                            found = (v, i + 1)
                            break
            if found: break
    finally:
        doc.close()
    if found:
        hits.append((c, name.get(c, c), q, found[0], found[1]))
print(f"item29전=0 인데 원문에 사망위험 > 0 : {len(hits)}")
for c, nm, q, v, pg in hits:
    print(f"  {c} {nm:<12} {q}  raw 사망위험={v:,.0f} (p{pg})")
