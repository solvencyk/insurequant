# -*- coding: utf-8 -*-
"""[SUPERSEDED · 결함 있음] 이 v1 은 소수자리를 float 문자열에서 세는 버그가 있어
정수 인쇄("4160")를 1자리("4160.0")로 잡고 악사손해 8건 등 반올림 오탐을 냈다.
정본은 `scripts/detect_kics_restatement.py` 다. 이 파일은 그 오탐이 어떻게 났는지
보이는 근거로만 남긴다 — 판정에 쓰지 말 것.

소급재작성(restatement) 전수 재스캔 — 39사 x 항목1~27, 2026.2Q 공시본의 '직전분기' 칸
vs 마스터 2026.1Q `값`.

**오탐 방지 설계 (오케스트레이터의 1차 스캔이 기타포괄손익누계액/신종자본증권을 오탐한 이유:
라벨을 느슨하게 매칭해 단위가 다른 다른 표를 긁었다).**

1. 표를 **정확히 하나** 특정한다: `[경과조치 적용 전 지급여력비율 세부]` (단위 억원, 3컬럼).
   소스는 raw PDF 좌표(fitz words) — docling MD 는 회사에 따라 표를 쪼개거나(KR0087)
   숫자를 이어붙인다(KR0010 '155,3161'). 텍스트가 없는 스캔 PDF 3사만 MD 로 폴백.
2. 행->항목번호 매핑은 **정규화 라벨 앵커 + 순서 단조성**. 못 맞춘 행은 버리지 않고
   UNMATCHED 로 센다(결측은 SKIP 이 아니라 보고 대상).
3. **컨트롤 컬럼**: 같은 표의 `해당분기`(=2026.2Q) 를 마스터 2026.2Q 와 대조한다.
   컨트롤이 깨진 행의 `직전분기` 불일치는 재작성 근거가 못 된다(추출/매핑 오류일 수 있다).
   컨트롤 통과 + 직전분기 불일치 = **재작성 후보**.
4. `전전분기`(=2025.4Q) 도 같은 방식으로 부수 검사한다 — 회사가 2분기 공시에서 2개 과거
   분기를 동시에 재작성했는지 본다.

출력: scratchpad JSON + 사람이 읽는 표.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"
MD_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "parsed"
MASTER = ROOT / "kics_disclosure.json"

CUR_Q, PREV_Q, PREV2_Q = "2026.2Q", "2026.1Q", "2025.4Q"

NUM_RE = re.compile(r"^[\(\[]?[-△▲]?[\d,]+(?:\.\d+)?[\)\]]?%?$")

# 항목 1~27 의 정규화 라벨 앵커. 정규화 = 한글/숫자만 남긴다.
# 순서대로 소비하며(단조성) 매칭한다 — 같은 앵커가 여러 항목에 걸리는 것을 막는다.
ANCHORS = [
    (1,  ("지급여력금액기본자본",  "지급여력금액")),
    (2,  ("기본자본",)),
    (3,  ("보완자본",)),
    (4,  ("건전성감독기준재무상태표",)),
    (5,  ("1보통주", "보통주")),
    (6,  ("2자본항목중보통주이외", "자본항목중보통주이외")),
    (7,  ("3이익잉여금", "이익잉여금")),
    (8,  ("4자본조정", "자본조정")),
    (9,  ("5기타포괄손익누계액", "기타포괄손익누계액")),
    (10, ("6비지배지분", "비지배지분")),
    (11, ("7조정준비금", "조정준비금")),
    (12, ("지급여력금액으로불인정",)),
    (13, ("보완자본으로재분류",)),
    (14, ("지급여력기준금액",)),
    (15, ("기본요구자본",)),
    (16, ("분산효과",)),
    (17, ("1생명장기손해보험위험액", "생명장기손해보험위험액", "생명장기위험액")),
    (18, ("2일반손해보험위험액", "일반손해보험위험액")),
    (19, ("3시장위험액", "시장위험액")),
    (20, ("4신용위험액", "신용위험액")),
    (21, ("5운영위험액", "운영위험액")),
    (22, ("법인세조정액",)),
    (23, ("기타요구자본",)),
    (24, ("1업권별자본규제", "업권별자본규제를활용한종속회사")),
    (25, ("2비례성원칙", "비례성원칙을적용한종속회사")),
    (26, ("3업권별자본규제", "업권별자본규제를활용한관계회사")),
    (27, ("지급여력비율",)),
]
# 24/26 은 앵커가 같은 형태라(업권별자본규제 종속/관계) 구분자를 따로 준다.
DISAMBIG = {24: "종속회사", 26: "관계회사"}


def norm(s: str) -> str:
    return re.sub(r"[^0-9가-힣]", "", s or "")


def parse_num(tok: str):
    t = tok.strip().replace(",", "").replace("%", "")
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    if t[:1] in ("△", "▲", "-", "−"):
        neg, t = True, t[1:]
    if t in ("", "-", "–"):
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


# ---------------------------------------------------------------- PDF 추출
def pdf_table_page(doc):
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "분산효과" in t and "기본요구자본" in t and "지급여력기준금액" in t:
            return pno
    return None


def pdf_rows(page):
    """[(label, [(xc, token), ...]), ...] — y 로 줄을 묶고, 숫자 없는 줄은 가장 가까운
    숫자 줄에 라벨로 합친다(2~3줄에 걸친 셀 처리)."""
    words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if lines and abs(lines[-1][0] - yc) <= 3.0:
            lines[-1][1].append(w)
        else:
            lines.append([yc, [w]])

    # 숫자 x-center 히스토그램에서 우측 3개 컬럼대를 잡는다
    xs = sorted((w[0] + w[2]) / 2 for _, ws in lines for w in ws if NUM_RE.match(w[4]))
    if len(xs) < 20:
        return []
    clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] <= 12:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    clusters = [c for c in clusters if len(c) >= 8]
    if len(clusters) < 3:
        return []
    cols = clusters[-3:]
    col_lo = min(cols[0]) - 30

    numlines, lbllines = [], []
    for yc, ws in lines:
        nums = [((w[0] + w[2]) / 2, w[4]) for w in ws
                if NUM_RE.match(w[4]) and (w[0] + w[2]) / 2 >= col_lo]
        lbl = " ".join(w[4] for w in ws if (w[0] + w[2]) / 2 < col_lo)
        if len(nums) >= 2:
            numlines.append([yc, lbl, nums])
        elif lbl.strip():
            lbllines.append([yc, lbl])

    for yc, lbl in lbllines:
        if not numlines:
            continue
        near = min(numlines, key=lambda n: abs(n[0] - yc))
        if abs(near[0] - yc) <= 14:
            near[1] = (near[1] + " " + lbl) if near[0] > yc else (lbl + " " + near[1])

    out = []
    for yc, lbl, nums in numlines:
        vals = []
        for c in cols:
            lo, hi = min(c) - 22, max(c) + 22
            got = [t for x, t in nums if lo <= x <= hi]
            vals.append(parse_num(got[0]) if got else None)
        out.append((lbl, vals))
    return out


# ---------------------------------------------------------------- MD 폴백
HEAD_RE = re.compile(r"경과조치\s*적용\s*전\s*지급여력비율\s*세부")


def md_rows(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(lines) if HEAD_RE.search(ln)]
    if not hits:
        return []
    out = []
    for h in hits:
        i = h
        while i < len(lines) and not lines[i].lstrip().startswith("|"):
            i += 1
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            c = [x.strip() for x in lines[i].strip().strip("|").split("|")]
            if not all(set(x) <= set("-: ") for x in c) and len(c) >= 4:
                out.append((c[0], [parse_num(x) for x in c[1:4]]))
            i += 1
        if out:
            break
    return out[1:] if out and not any(v is not None for v in out[0][1]) else out


# ---------------------------------------------------------------- 매핑
def map_items(rows):
    """[(item_no, label, vals)] + unmatched 라벨 목록. 순서 단조 소비."""
    mapped, unmatched = [], []
    ai = 0
    for lbl, vals in rows:
        n = norm(lbl)
        if not n:
            unmatched.append(lbl)
            continue
        hit = None
        for k in range(ai, len(ANCHORS)):
            item, anchors = ANCHORS[k]
            if any(a in n for a in anchors):
                if item in DISAMBIG and DISAMBIG[item] not in n:
                    continue
                hit = (k, item)
                break
        if hit is None:
            unmatched.append(lbl)
            continue
        ai = hit[0] + 1
        mapped.append((hit[1], lbl, vals))
    return mapped, unmatched


def main():
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    mv = defaultdict(dict)          # (code, quarter) -> {item: 값}
    names = {}
    for r in master:
        code, q, no = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        if isinstance(no, int):
            mv[(code, q)][no] = r.get("값")
        names[code] = r.get("원수사명")

    report, summary = {}, []
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        stem = pdf.stem
        code = stem.split("_")[0]
        doc = fitz.open(pdf)
        pno = pdf_table_page(doc)
        src = None
        rows = []
        if pno is not None:
            rows = pdf_rows(doc[pno])
            src = f"PDF p{pno+1}"
        doc.close()
        if not rows:
            md = MD_DIR / f"{stem}.md"
            if md.exists():
                rows = md_rows(md)
                src = "docling MD (scanned PDF)"
        if not rows:
            summary.append((code, stem, "NO_TABLE", 0, 0, 0, 0, src))
            report[code] = {"company": stem, "source": src, "status": "NO_TABLE"}
            continue

        mapped, unmatched = map_items(rows)
        cur_m = mv.get((code, CUR_Q), {})
        prev_m = mv.get((code, PREV_Q), {})
        prev2_m = mv.get((code, PREV2_Q), {})

        cells = []
        ctl_ok = ctl_bad = 0
        for item, lbl, vals in mapped:
            printed_cur, printed_prev, printed_prev2 = (vals + [None, None, None])[:3]
            mc, mp, mp2 = cur_m.get(item), prev_m.get(item), prev2_m.get(item)

            def cmp(printed, mval):
                if printed is None or mval is None:
                    return None, None
                try:
                    mval = float(mval)
                except (TypeError, ValueError):
                    return None, None
                # 인쇄 소수자리로 마스터를 반올림해서 비교(마스터 item27 은 파생 고정밀)
                dec = 0
                s = f"{printed}"
                if "." in s:
                    dec = len(s.split(".")[1])
                d = round(round(mval, dec) - printed, max(dec, 2))
                tol = 0.5 if dec == 0 else 0.5 * (10 ** -dec) * 1.01
                return d, abs(d) > tol

            d_cur, bad_cur = cmp(printed_cur, mc)
            d_prev, bad_prev = cmp(printed_prev, mp)
            d_prev2, bad_prev2 = cmp(printed_prev2, mp2)
            if bad_cur is True:
                ctl_bad += 1
            elif bad_cur is False:
                ctl_ok += 1
            cells.append({
                "item": item, "label": lbl.strip(),
                "printed_cur": printed_cur, "master_cur": mc, "d_cur": d_cur,
                "printed_prev": printed_prev, "master_prev": mp, "d_prev": d_prev,
                "printed_prev2": printed_prev2, "master_prev2": mp2, "d_prev2": d_prev2,
                "control_ok": (bad_cur is False),
                "restated_prev": (bad_cur is False and bad_prev is True),
                "restated_prev2": (bad_cur is False and bad_prev2 is True),
            })
        n_re1 = sum(1 for c in cells if c["restated_prev"])
        n_re2 = sum(1 for c in cells if c["restated_prev2"])
        report[code] = {"company": stem, "source": src, "status": "OK",
                        "rows": len(rows), "mapped": len(mapped),
                        "unmatched": unmatched, "control_ok": ctl_ok,
                        "control_bad": ctl_bad, "cells": cells}
        summary.append((code, stem, "OK", ctl_ok, ctl_bad, n_re1, n_re2, src))

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_rescan.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'code':8s} {'company':30s} {'stat':8s} {'ctlOK':>5s} {'ctlBAD':>6s} "
          f"{'RE_1Q':>5s} {'RE_4Q':>5s}  source")
    for row in summary:
        print(f"{row[0]:8s} {row[1][:30]:30s} {row[2]:8s} {row[3]:5d} {row[4]:6d} "
              f"{row[5]:5d} {row[6]:5d}  {row[7]}")
    print()
    print("TOTAL companies:", len(summary),
          "| with 재작성(1Q):", sum(1 for r in summary if r[5] > 0),
          "| 셀 합:", sum(r[5] for r in summary),
          "| control_bad 합:", sum(r[4] for r in summary))
    print("JSON ->", out)


if __name__ == "__main__":
    sys.exit(main())
