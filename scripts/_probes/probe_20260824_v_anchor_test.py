# -*- coding: utf-8 -*-
"""행 귀속 검사기 시제품 — 라벨 L 과 값 V 가 같은 행 밴드에 있고 V 가 L 오른쪽인가."""
import sys, re
from pathlib import Path
import fitz
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
BAND = 14.0


def occurrences(words, needle):
    """공백 제거 연속 매칭 → [(x0, ycenter, x1)]"""
    n = "".join(needle.split())
    out = []
    for i in range(len(words)):
        buf = ""
        for j in range(i, min(i + 12, len(words))):
            buf += "".join(words[j][4].split())
            if n in buf:
                ys = [(w[1] + w[3]) / 2 for w in words[i:j + 1]]
                out.append((words[i][0], sum(ys) / len(ys), words[j][2]))
                break
            if len(buf) > len(n) + 24:
                break
    return out


def anchored(pdf, pages, row, value, band=BAND):
    doc = fitz.open(ROOT / pdf)
    hit = False
    detail = []
    for p in pages:
        if not (0 <= p - 1 < doc.page_count):
            continue
        ws = sorted(doc[p - 1].get_text("words"), key=lambda w: (w[5], w[6], w[7]))
        ls, vs = occurrences(ws, row), occurrences(ws, value)
        for lx0, ly, lx1 in ls:
            for vx0, vy, _ in vs:
                if abs(vy - ly) <= band and vx0 >= lx1 - 1:
                    hit = True
                    detail.append(f"p{p} label_y={ly:.0f} value_y={vy:.0f} dx={vx0 - lx1:.0f}")
        if not ls:
            detail.append(f"p{p}: 라벨 미발견")
    doc.close()
    return hit, detail[:3]


CASES = [
    ("data/disclosure/FY2025_Q4/raw/KR0032_NH농협손해보험.pdf", [46], "해약환급금", "447,254"),
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "해약환급금", "1,543,723"),
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "보완자본 한도 적용 전", "1,210,705"),
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "보완자본 한도", "1,210,705"),
    ("data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf", [15, 16], "보완자본 한도 적용 전", "31,614"),
    ("data/disclosure/FY2024_Q3/raw/KR0075_비엔피파리바카디프생명보험_amended.pdf", [15, 16], "보완자본", "33,067"),
    ("data/disclosure/FY2024_Q3/raw/KR0032_NH농협손해보험_amended.pdf", [12, 13], "해약환급금", "886,613"),
    ("data/disclosure/FY2025_Q1/raw/KR0004_예별손해보험.pdf", [16, 17], "기본자본", "△165,099"),
    # 음성 대조군: 값이 다른 행에 있다고 거짓 주장하면 반증돼야 한다
    ("data/disclosure/FY2025_Q2/raw/KR0087_동양생명.pdf", [15, 16], "해약환급금", "1,210,705"),
    ("data/disclosure/FY2025_Q4/raw/KR0032_NH농협손해보험.pdf", [46], "보완자본 한도", "447,254"),
]
for pdf, pages, row, val in CASES:
    ok, d = anchored(pdf, pages, row, val)
    print(f"{'OK ' if ok else 'NO '} {Path(pdf).name[:26]:26s} '{row}' <- {val:>12s}   {d}")
