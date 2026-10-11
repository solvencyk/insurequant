import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
def row(code, q, item):
    return [(r["원수사명"], r["값"], r.get("값_당분기")) for r in pl if r["원보험사코드"] == code and r["공시분기"] == q and str(r["항목번호"]) == str(item)]
for code, qs in (("KR1102", ["2023.1Q", "2023.2Q", "2023.3Q"]), ("KR1107", ["2024.3Q", "2024.4Q", "2025.3Q", "2025.4Q"])):
    for q in qs:
        print(code, q, "법인세(23)", row(code, q, 23))
specs = [
 ("data/disclosure/FY2023_Q2/raw/KR1102_스위스리아시아.pdf", [5], ["법인세비용(수익)000당기순이익(손실)509", "법인세비용차감전순이익(손실)509-6731,182"]),
 ("data/disclosure/FY2024_Q4/raw_aux/KR1107_퍼시픽라이프리__audit.pdf", [8], ["VI.법인세비용28--VII.당기순이익(손실)4,334,865,096"]),
 ("data/disclosure/FY2025_Q4/raw_aux/KR1107_퍼시픽라이프리__audit.pdf", [8], ["VI.법인세비용28--VII.당기순이익(손실)(12,066,580,579)4,334,865,096"]),
]
for f, pages, marks in specs:
    d = fitz.open(f)
    print("==", f, "pages", d.page_count)
    for pg in pages:
        t = d[pg-1].get_text()
        flat = "".join(t.split())
        for m in marks:
            print("  marker", ("".join(m.split()) in flat), m)
        # show the lines around 법인세
        lines = [l for l in t.splitlines()]
        for i, l in enumerate(lines):
            if "법인세" in l:
                print("   |", " / ".join(x.strip() for x in lines[max(0,i-1):i+6]))
