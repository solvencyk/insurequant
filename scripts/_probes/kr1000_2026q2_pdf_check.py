import fitz, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

doc = fitz.open("data/disclosure/FY2026_Q2/pdf/KR1000_코리안리재보험.pdf")
print(f"pages: {len(doc)}")
targets = ["보완자본 한도", "해약환급금", "기발행", "지급여력비율의 경과조치 적용에 관한 사항", "공통적용 경과조치"]
for i, page in enumerate(doc):
    text = page.get_text()
    hits = [t for t in targets if t in text]
    if hits:
        print(f"p{i+1} (len={len(text)}): {hits}")
