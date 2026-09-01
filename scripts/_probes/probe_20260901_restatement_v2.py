# -*- coding: utf-8 -*-
"""소급재작성(restatement) 전수 재스캔 v2 — **필링 대 필링** 이 정본 판정이다.

v1 의 결함 2개를 고쳤다:
  (a) 인쇄값을 float 로 만든 뒤 `f"{v}"` 로 소수자리를 세서 정수 인쇄("4160")가
      1자리("4160.0")로 잡혔다 -> 악사 8건 등 전부 반올림 오탐. 원 토큰을 보존한다.
  (b) item27(지급여력비율)은 마스터에서 **파생값**(item1/item14x100, 소수 8자리)이라
      인쇄값과 항상 어긋난다. 재작성 축에서 제외하고 따로 표시한다.

판정 축 3개:
  A. **FILING_VS_FILING** (정본): FY2026_Q1 공시본의 `해당분기` 칸  vs
     FY2026_Q2 공시본의 `직전분기` 칸. 둘 다 발행사가 인쇄한 값이다. 다르면 재작성.
  B. MASTER_VS_Q1FILING: 마스터 2026.1Q `값` 이 1Q 원공시본과 같은가(= 마스터가
     원공시본 기준인지 확인). 다르면 그건 재작성이 아니라 **파싱 결함**이다.
  C. 컨트롤: 2Q 공시본의 `해당분기` vs 마스터 2026.2Q. 이게 깨지면 그 회사 추출을
     신뢰하지 않는다(UNVERIFIED).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"
DISC = ROOT / "data" / "disclosure"

NUM_RE = re.compile(r"^[\(\[]?[-△▲−]?[\d,]+(?:\.\d+)?[\)\]]?%?$")

ANCHORS = [
    (1,  ("지급여력금액기본자본", "지급여력금액")),
    (2,  ("기본자본",)),
    (3,  ("보완자본",)),
    (4,  ("건전성감독기준재무상태표",)),
    (5,  ("보통주",)),
    (6,  ("자본항목중보통주이외",)),
    (7,  ("이익잉여금",)),
    (8,  ("자본조정",)),
    (9,  ("기타포괄손익누계액",)),
    (10, ("비지배지분",)),
    (11, ("조정준비금",)),
    (12, ("지급여력금액으로불인정",)),
    (13, ("보완자본으로재분류",)),
    (14, ("지급여력기준금액",)),
    (15, ("기본요구자본",)),
    (16, ("분산효과",)),
    (17, ("생명장기손해보험위험액", "생명장기위험액")),
    (18, ("일반손해보험위험액",)),
    (19, ("시장위험액",)),
    (20, ("신용위험액",)),
    (21, ("운영위험액",)),
    (22, ("법인세조정액",)),
    (23, ("기타요구자본",)),
    (24, ("업권별자본규제",)),
    (25, ("비례성원칙",)),
    (26, ("업권별자본규제",)),
    (27, ("지급여력비율",)),
]
DISAMBIG = {24: "종속회사", 26: "관계회사"}
DERIVED_ITEMS = {27}            # 마스터에서 파생 -> 재작성 축에서 제외


def norm(s):
    return re.sub(r"[^0-9가-힣]", "", s or "")


def parse_num(tok):
    """(value, decimals) — 원 토큰의 소수자리를 보존한다."""
    t = (tok or "").strip().replace(",", "").replace("%", "").replace(" ", "")
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    if t[:1] in ("△", "▲", "-", "−"):
        neg, t = True, t[1:]
    if t in ("", "-", "–", "—"):
        return None, 0
    try:
        v = float(t)
    except ValueError:
        return None, 0
    dec = len(t.split(".")[1]) if "." in t else 0
    return (-v if neg else v), dec


def table_page(doc):
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        if "분산효과" in t and "기본요구자본" in t and "지급여력기준금액" in t:
            return pno
    return None


def pdf_rows(page):
    words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if lines and abs(lines[-1][0] - yc) <= 3.0:
            lines[-1][1].append(w)
        else:
            lines.append([yc, [w]])

    xs = sorted((w[0] + w[2]) / 2 for _, ws in lines for w in ws if NUM_RE.match(w[4]))
    if len(xs) < 20:
        return []
    cl = []
    for x in xs:
        if cl and x - cl[-1][-1] <= 12:
            cl[-1].append(x)
        else:
            cl.append([x])
    cl = [c for c in cl if len(c) >= 8]
    if len(cl) < 3:
        return []
    cols = cl[-3:]
    col_lo = min(cols[0]) - 30

    numl, lbll = [], []
    for yc, ws in lines:
        nums = [((w[0] + w[2]) / 2, w[4]) for w in ws
                if NUM_RE.match(w[4]) and (w[0] + w[2]) / 2 >= col_lo]
        lbl = " ".join(w[4] for w in ws if (w[0] + w[2]) / 2 < col_lo)
        if len(nums) >= 2:
            numl.append([yc, lbl, nums])
        elif lbl.strip():
            lbll.append([yc, lbl])

    # 라벨 전용 줄은 **가장 가까운 숫자 줄** 에 붙이되, 이미 앵커를 가진 숫자 줄에는
    # 새 앵커를 가진 라벨을 붙이지 않는다(다른 항목을 한 행으로 뭉치는 것 방지).
    def anchors_of(s):
        n = norm(s)
        return {it for it, aa in ANCHORS if any(a in n for a in aa)}

    for yc, lbl in lbll:
        if not numl:
            continue
        near = min(numl, key=lambda n: abs(n[0] - yc))
        if abs(near[0] - yc) > 14:
            continue
        if anchors_of(near[1]) and anchors_of(lbl) and \
                not (anchors_of(near[1]) & anchors_of(lbl)):
            continue
        near[1] = (near[1] + " " + lbl) if near[0] > yc else (lbl + " " + near[1])

    out = []
    for yc, lbl, nums in numl:
        vals = []
        for c in cols:
            lo, hi = min(c) - 22, max(c) + 22
            got = [t for x, t in nums if lo <= x <= hi]
            vals.append(parse_num(got[0]) if got else (None, 0))
        out.append((lbl, vals))
    return out


def map_items(rows):
    mapped, unmatched, ai = [], [], 0
    for lbl, vals in rows:
        n = norm(lbl)
        hit = None
        for k in range(ai, len(ANCHORS)):
            item, aa = ANCHORS[k]
            if any(a in n for a in aa):
                if item in DISAMBIG and DISAMBIG[item] not in n:
                    continue
                hit = (k, item)
                break
        if hit is None:
            if n:
                unmatched.append(lbl)
            continue
        ai = hit[0] + 1
        mapped.append((hit[1], lbl, vals))
    return mapped, unmatched


def find_pdf(period, code):
    """분기마다 파일명이 다르다(FY2026_Q1 은 raw/ 에 있고 회사명 표기도 다르다:
    KR0004_예별손해보험 / KR0069_삼성생명보험 / KR0099_KB라이프생명). 코드로 찾는다."""
    for sub in ("pdf", "raw"):
        d = DISC / period / sub
        if not d.is_dir():
            continue
        hits = sorted(p for p in d.glob(f"{code}_*.pdf"))
        if hits:
            return hits[0]
    return None


def extract(period, code):
    p = find_pdf(period, code)
    if p is None:
        return None, f"no pdf for {code} in {period}"
    doc = fitz.open(p)
    pno = table_page(doc)
    if pno is None:
        doc.close()
        return None, "no text table page (scanned)"
    rows = pdf_rows(doc[pno])
    doc.close()
    if not rows:
        return None, "table page found but no numeric grid"
    mapped, unmatched = map_items(rows)
    return {"page": pno + 1, "src": str(p.relative_to(ROOT)),
            "items": {it: v for it, _l, v in mapped},
            "labels": {it: l for it, l, _v in mapped}, "unmatched": unmatched}, None


def diff(a, b):
    """(값,소수) 두 개 비교. 더 거친 소수자리로 맞춰서 반올림 폭 밖인지 본다."""
    (va, da), (vb, db) = a, b
    if va is None or vb is None:
        return None, None
    dec = min(da, db)
    d = round(round(va, dec) - round(vb, dec), max(dec, 3))
    tol = 0.5 if dec == 0 else 0.5 * (10 ** -dec)
    return d, abs(d) > tol + 1e-9


def main():
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    mv = defaultdict(dict)
    for r in master:
        if isinstance(r.get("항목번호"), int):
            mv[(r.get("원보험사코드"), r.get("공시분기"))][r["항목번호"]] = r.get("값")

    stems = sorted(p.stem for p in (DISC / "FY2026_Q2" / "pdf").glob("*.pdf")
                   if p.stem.startswith("KR"))
    report, summary = {}, []
    for stem in stems:
        code = stem.split("_")[0]
        q2, e2 = extract("FY2026_Q2", code)
        q1, e1 = extract("FY2026_Q1", code)
        rec = {"company": stem, "q2_err": e2, "q1_err": e1,
               "q2_src": q2["src"] if q2 else None,
               "q1_src": q1["src"] if q1 else None,
               "q2_page": q2["page"] if q2 else None,
               "q1_page": q1["page"] if q1 else None,
               "unmatched_q2": q2["unmatched"] if q2 else [],
               "cells": [], "status": "OK"}
        if not q2 or not q1:
            rec["status"] = "UNCOVERED"
            report[code] = rec
            summary.append((code, stem, "UNCOVERED", 0, 0, 0, e2 or e1))
            continue

        m1 = mv.get((code, "2026.1Q"), {})
        m2 = mv.get((code, "2026.2Q"), {})
        n_restate = n_ctlbad = n_masterdrift = 0
        for it in range(1, 28):
            v_q2_cur = q2["items"].get(it)
            v_q2_prev = q2["items"].get(it)
            if v_q2_cur is None:
                continue
            cur = q2["items"][it][0]        # (값, 소수자리) 2026.2Q 인쇄
            prev = q2["items"][it][1]       # (값, 소수자리) 2Q본의 직전분기 칸
            q1cur = q1["items"].get(it, [(None, 0)])[0]   # 1Q본의 해당분기 칸
            mm1, mm2 = m1.get(it), m2.get(it)

            d_ff, bad_ff = diff(prev, q1cur)        # A. filing vs filing
            d_ctl, bad_ctl = diff(cur, (float(mm2), 0) if isinstance(mm2, (int, float))
                                  else (None, 0))
            d_mq1, bad_mq1 = diff(q1cur, (float(mm1), 0) if isinstance(mm1, (int, float))
                                  else (None, 0))
            derived = it in DERIVED_ITEMS
            if bad_ctl and not derived:
                n_ctlbad += 1
            if bad_ff and not derived:
                n_restate += 1
            if bad_mq1 and not derived:
                n_masterdrift += 1
            rec["cells"].append({
                "item": it, "derived": derived,
                "label_q2": q2["labels"].get(it, "")[:60],
                "q2_cur": cur[0], "q2_prev": prev[0], "q1_cur": q1cur[0],
                "master_1q": mm1, "master_2q": mm2,
                "d_filing_vs_filing": d_ff, "restated": bool(bad_ff) and not derived,
                "d_control": d_ctl, "control_bad": bool(bad_ctl) and not derived,
                "d_master_vs_q1filing": d_mq1,
                "master_drift": bool(bad_mq1) and not derived,
            })
        if n_ctlbad:
            rec["status"] = "UNVERIFIED"
        report[code] = rec
        summary.append((code, stem, rec["status"], n_restate, n_ctlbad, n_masterdrift, ""))

    out = Path(sys.argv[1])
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'code':8s} {'company':28s} {'status':11s} {'재작성':>6s} {'ctlBAD':>6s} "
          f"{'m!=1Q본':>7s}  note")
    for c, s, st, nr, nb, nd, note in summary:
        print(f"{c:8s} {s[:28]:28s} {st:11s} {nr:6d} {nb:6d} {nd:7d}  {note}")
    print()
    print("companies:", len(summary),
          "| OK:", sum(1 for r in summary if r[2] == "OK"),
          "| UNVERIFIED:", sum(1 for r in summary if r[2] == "UNVERIFIED"),
          "| UNCOVERED:", sum(1 for r in summary if r[2] == "UNCOVERED"))
    print("재작성 셀 합(OK 회사만):", sum(r[3] for r in summary if r[2] == "OK"),
          "| 재작성 회사수:", sum(1 for r in summary if r[2] == "OK" and r[3] > 0))
    print("마스터!=1Q원공시본 셀 합(OK 회사만):",
          sum(r[5] for r in summary if r[2] == "OK"))
    print("JSON ->", out)


if __name__ == "__main__":
    sys.exit(main())
