"""Keyword scan of reinsurer FY2025 filings for line-of-business wording (read-only). Output kw_scan.txt"""
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
KW = re.compile(r"(장기손해|일반손해|장기보험|생명보험|손해보험|생명재보험|장기재보험|사업부문|보험종목)")
lines = []
for code, fn in FILES.items():
    pdf = ROOT / "data" / "disclosure" / "FY2025_Q4" / "raw" / fn
    doc = fitz.open(str(pdf))
    lines.append(f"##### {code} {fn} pages={len(doc)}")
    hits = 0
    for i, pg in enumerate(doc, 1):
        t = pg.get_text("text")
        flat = re.sub(r"\s+", " ", t)
        for m in KW.finditer(flat):
            hits += 1
            if hits <= 60:
                s = max(0, m.start() - 50)
                lines.append(f"  p{i}: ...{flat[s:m.end() + 60]}")
    lines.append(f"  total hits {hits}")
(OUT / "kw_scan.txt").write_text("\n".join(lines), encoding="utf-8")
print("done")
