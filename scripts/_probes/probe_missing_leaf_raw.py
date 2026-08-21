"""결측 leaf 의 값을 원문 '생명·장기손해보험위험액 현황' / '시장위험액 현황' 표에서 찾는다."""
import io, re, sys
from pathlib import Path
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
LABEL = {29: "사망위험", 30: "장수위험", 31: "장해·질병위험", 32: "장기재물·기타위험",
         33: "해지위험", 34: "사업비위험", 35: "대재해위험",
         36: "금리위험", 37: "주식위험", 38: "부동산위험", 39: "외환위험", 40: "자산집중위험"}
NUM = re.compile(r"^-?[\d,]+(\.\d+)?$")
def q2p(q):
    y, qq = q.split("."); return f"FY{y}_Q{qq[0]}"
for spec in sys.argv[1:]:
    code, q, item = spec.split(":")
    item = int(item)
    pats = {LABEL[item].replace("·", ""), LABEL[item].replace("·", "・"), LABEL[item],
            LABEL[item] + "액"}
    pdfs = sorted((REPO / "data" / "disclosure" / q2p(q) / "raw").glob(f"{code}_*.pdf"))
    if not pdfs:
        print(f"{code} {q} item{item}: raw 없음"); continue
    am = [p for p in pdfs if "_amended" in p.name]
    pdf = max(am or pdfs, key=lambda p: p.stat().st_size)
    doc = fitz.open(pdf)
    found = []
    try:
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if "위험액 현황" not in t and "위험액현황" not in t.replace(" ", ""):
                continue
            lines = [x.strip() for x in t.splitlines()]
            for j, l in enumerate(lines):
                s = l.replace(" ", "")
                if s in {p.replace(" ", "") for p in pats}:
                    nxt = [x.replace(",", "") for x in lines[j+1:j+6]
                           if NUM.match(x.replace(" ", "").replace(",", ""))]
                    if nxt:
                        found.append((i + 1, nxt[:4]))
    finally:
        doc.close()
    print(f"{code} {q} item{item} ({LABEL[item]}) [{pdf.name}]: {found if found else '원문에 행 없음'}")
