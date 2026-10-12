"""Find 4-6-2 style tables that print 상품유형 (생명/장기손해/일반/자동차) next to the portfolio labels, per reinsurer filing. Output product_type_scan.txt"""
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
FILES = {
    "KR1101": "KR1101_뮌헨재보험.pdf", "KR1102": "KR1102_스위스리아시아.pdf", "KR1103": "KR1103_제네럴재보험.pdf",
    "KR1104": "KR1104_하노버재보험.pdf", "KR1105": "KR1105_알지에이리인슈어런스.pdf", "KR1106": "KR1106_스코리재보험.pdf",
    "KR1107": "KR1107_퍼시픽라이프리.pdf",
}
PAT = re.compile(r"상\s*품\s*유\s*형")
lines = []
for fy in ("FY2025_Q4", "FY2024_Q4", "FY2023_Q4"):
    for code, fn in FILES.items():
        pdf = ROOT / "data" / "disclosure" / fy / "raw" / fn
        if not pdf.exists():
            lines.append(f"##### {fy} {code}: no pdf")
            continue
        doc = fitz.open(str(pdf))
        lines.append(f"##### {fy} {code} pages={len(doc)}")
        n = 0
        for i, pg in enumerate(doc, 1):
            if i > 40 and code != "KR1104" and code != "KR1105" and code != "KR1106" and code != "KR1107":
                break
            if i > 60:
                break
            t = re.sub(r"\s+", " ", pg.get_text("text"))
            if PAT.search(t) and ("포트폴리" in t.replace(" ", "") or "포트 폴리" in t):
                n += 1
                m = PAT.search(t)
                lines.append(f"  p{i}: {t[max(0, m.start() - 120): m.start() + 1500]}")
        lines.append(f"  pages with 상품유형+포트폴리오: {n}")
(OUT / "product_type_scan.txt").write_text("\n".join(lines), encoding="utf-8")
print("done")
