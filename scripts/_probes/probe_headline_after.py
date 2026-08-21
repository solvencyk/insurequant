"""Extract 주요경영지표의 '지급여력비율 (경과조치 후)' from raw PDF and compare with stored item27후."""
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
st = defaultdict(dict); name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기"); name[c] = r.get("원수사명", c)
    try: st[(c, q)][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass

NUMRE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")
def headline_after(period, code):
    raw = REPO / "data" / "disclosure" / period / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
    if not pdfs: return None, "raw 없음"
    am = [p for p in pdfs if "_amended" in p.name]
    pdf = max(am or pdfs, key=lambda p: p.stat().st_size)
    doc = fitz.open(pdf)
    try:
        for i in range(min(8, doc.page_count)):
            lines = [l.strip() for l in doc[i].get_text().splitlines()]
            for j, l in enumerate(lines):
                if "경과조치" in l and ("후" in l) and "지급여력비율" not in l.replace("지급여력비율", "", 1):
                    pass
            for j, l in enumerate(lines):
                joined = (lines[j - 1] + l) if j else l
                if ("경과조치" in l and "후" in l) and ("지급여력비율" in l or "지급여력비율" in lines[max(0, j - 1)]):
                    for k in range(j + 1, min(j + 5, len(lines))):
                        t = lines[k].replace(" ", "")
                        if t and NUMRE.match(t):
                            return float(t.strip("()%").replace(",", "")), f"{pdf.name} p{i+1}"
                        if t and t not in ("—", "-", "", "|"):
                            break
    finally:
        doc.close()
    return None, f"{pdf.name}: 헤드라인 못 찾음"

def q2p(q):
    y, qq = q.split("."); return f"FY{y}_Q{qq[0]}"

targets = [a for a in sys.argv[1:]]
print(f"{'회사':<13}{'분기':<9}{'raw 헤드라인후':>13}{'저장 item27후':>13}{'차':>10}  출처")
for t in targets:
    code, q = t.split(":")
    v, src = headline_after(q2p(q), code)
    s27 = st.get((code, q), {}).get(27, (None, None))[1]
    d = "" if (v is None or s27 is None) else f"{s27 - v:,.2f}"
    flag = "" if (v is None or s27 is None or abs(s27 - v) <= 0.6) else "   <<< 불일치"
    print(f"{name.get(code, code):<13}{q:<9}{v!s:>13}{s27!s:>13}{d:>10}  {src}{flag}")
