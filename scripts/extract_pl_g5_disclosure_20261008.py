#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G5 PL 공란(2023.1Q/2Q) 경영공시 §2-1 요약 손익 추출 -> data/_derived/pl_from_disclosure_parts/<KR>.json

대상 6사: KR0009 KR0069 KR0073 KR0099 KR0104 KR1000. 마스터/공유 파일은 안 건드린다(파트 파일만 쓴다).
추출 엔진은 scripts/extract_pl_backfill_disclosure.py 의 find_and_extract 재사용(억원 -> x100 = 백만원).
보정: 겹치는 분기(마스터에 DART 값이 있는 2023.3Q~2026.2Q)의 경영공시 값 vs 마스터 값.
  항목별 통과 = 앞쪽 4개 겹침분기(2023.3Q~2024.3Q) 전부 + 전체 겹침분기 90% 이상 |diff|<=max(0.5%, 1억원); 20 은 17 통과가 전제. 통과 항목만 채운다.
값_당분기: 1Q = 값, 2Q = 2Q누계-1Q누계(같은 소스 안에서만).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_pl_g5_disclosure_20261008.py
"""
import hashlib, json, os, sys
import fitz
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import extract_pl_backfill_disclosure as E  # noqa: E402

G = ["KR0009", "KR0069", "KR0073", "KR0099", "KR0104", "KR1000"]
FILL_Q = ["2023.1Q", "2023.2Q"]
CAL_Q = ["2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
CAL_CORE = CAL_Q[:4]
ITEMS = [1, 16, 17, 20, 22, 23, 24]
NAMES = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익", 22: "세전이익", 23: "법인세", 24: "당기순이익"}
# 텍스트 레이어에서 표 위치 추출이 못 읽은 칸(원문 텍스트로 직접 확인, 표 내 항등식 22=20+21, 24=22-23 로 자체검산)
MANUAL = {
    ("KR0099", "2023.1Q"): {"page": 4, "v": {16: 95, 22: 1722, 23: 424, 24: 1298}},
    ("KR0099", "2023.2Q"): {"page": 5, "v": {16: 168, 22: 3015, 23: 667, 24: 2348}},
    ("KR0069", "2023.2Q"): {"page": 6, "v": {24: 8579}},  # 라벨 '반기순이익'
}
OUT_DIR = os.path.join(ROOT, "data", "_derived", "pl_from_disclosure_parts")
os.makedirs(OUT_DIR, exist_ok=True)

master = json.load(open(os.path.join(ROOT, "PL_breakdown.json"), encoding="utf-8"))
mv = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in master if r["값"] is not None}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


import re
_NUM = re.compile(r"^[(]?-?[0-9,]+([.][0-9]+)?[)]?$")
_LABELS = {16: ("(기타사업비용)",), 22: ("법인세비용차감전순이익",), 23: ("법인세비용",),
           24: ("당기순이익", "반기순이익", "분기순이익")}


def _num(t):
    t = t.strip()
    if not _NUM.match(t):
        return None
    neg = t.startswith("(") or t.startswith("-")
    v = float(t.strip("()-").replace(",", ""))
    return -v if neg else v


def text_fallback(pdf, page, items):
    """표 위치 추출이 못 읽은 항목을 같은 쪽 get_text 줄에서 라벨 다음 첫 숫자로 읽는다(영업이익 라벨 이후만)."""
    d = fitz.open(pdf)
    try:
        lines = [x.strip() for x in d[page - 1].get_text().splitlines() if x.strip()]
    finally:
        d.close()
    start = next((i for i, x in enumerate(lines) if x.startswith("영업이익")), None)
    out = {}
    for it in items:
        lo = 0 if it == 16 else (start or 0)
        for i in range(lo, len(lines)):
            if lines[i].replace(" ", "") in _LABELS[it]:
                for j in range(i + 1, min(i + 6, len(lines))):
                    v = _num(lines[j])
                    if v is not None:
                        out[it] = v
                        break
                break
    return out


def extract(g, q):
    p = E.find_pdf(g, q)
    if not p:
        return None
    st, pg, found, w, bb = E.find_and_extract(p)
    vals = {}
    if found:
        for k, rec in found.items():
            if isinstance(k, int) and rec.get("dash_state", "NORMAL") == "NORMAL" and rec.get("value_eok") is not None:
                vals[k] = rec["value_eok"]
    tvals = {}
    if pg:
        tvals = text_fallback(p, pg, [k for k in (16, 22, 23, 24) if k not in vals])
        for k, v in tvals.items():
            vals[k] = v
    return {"pdf": p, "page": pg, "status": st, "vals": vals, "text_items": sorted(tvals)}


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


report = {}
for g in G:
    cal = {}
    for q in CAL_Q:
        r = extract(g, q)
        cal[q] = r
    passed, calrows = {}, {}
    for it in ITEMS:
        res = []
        for q in CAL_Q:
            r = cal[q]
            m = mv.get((g, q, it))
            if not r or it not in r["vals"] or m is None:
                continue
            d, mm = r["vals"][it], m / 100.0
            diff = d - mm
            ok = abs(diff) <= max(abs(mm) * 0.005, 1.0)
            res.append((q, d, round(mm, 1), round(diff, 1), ok))
        core = [x for x in res if x[0] in CAL_CORE]
        passed[it] = bool(core) and all(x[4] for x in core) and sum(x[4] for x in res) >= 0.9 * len(res)
        calrows[it] = res
    if not passed[17]:
        passed[20] = False  # 영업이익=1+17 이라 17 이 불통과면 20 도 채우지 않는다
    cells, skips = {}, {}
    fills = {}
    for q in FILL_Q:
        r = extract(g, q)
        vals = dict(r["vals"]) if r else {}
        meth = {k: "fitz_find_tables(§2-1 요약 포괄손익계산서 총괄)" for k in vals}
        pg = r["page"] if r else None
        man = MANUAL.get((g, q))
        for k, v in (man["v"].items() if man else []):
            if k not in vals:
                vals[k] = v
                meth[k] = "fitz_get_text 원문 직접판독(표 라벨-값 위치 어긋남 보완)"
        fills[q] = (r, vals, meth, pg)
    for q in FILL_Q:
        r, vals, meth, pg = fills[q]
        # 표내 항등식
        chk = []
        a = vals
        if all(k in a for k in (1, 17, 20)):
            chk.append(("20=1+17", round(a[20] - a[1] - a[17], 1)))
        if 22 in a and 20 in a and 21 not in a:
            pass
        if all(k in a for k in (22, 23, 24)):
            chk.append(("24=22-23", round(a[24] - (a[22] - a[23]), 1)))
        chk_s = "; ".join(f"{n} 차이 {d}억" for n, d in chk)
        for it in ITEMS:
            key = f"{g}|{it}|{q}"
            if it not in vals:
                skips[key] = {"skip_reason": "경영공시 표에서 값 미확보"}
                continue
            if not passed[it]:
                skips[key] = {"skip_reason": "보정 불통과(앞 4개 겹침분기 중 경영공시 값이 마스터 DART 값과 0.5%/1억 초과 이탈) -- 요약표 투자손익 계열은 회사별 정의 차이 전례",
                              "disclosure_value_억원": vals[it],
                              "calibration": calrows[it]}
                continue
            val = round(vals[it] * 100, 6)
            prev = None
            if q == "2023.2Q" and it in fills["2023.1Q"][1] and passed[it]:
                prev = fills["2023.1Q"][1][it] * 100
            qv = val if q == "2023.1Q" else (round(val - prev, 6) if prev is not None else None)
            cells[key] = {
                "값": val, "값_당분기": qv,
                "pdf": rel(r["pdf"]), "page": man_page if (man_page := (MANUAL.get((g, q), {}).get("page") if meth[it].startswith("fitz_get_text") else pg)) else pg,
                "sha256": sha(r["pdf"]), "축척": "억원(x100=백만원)",
                "방법": meth[it],
                "근거": f"정기경영공시 {q} 별도 §2-1 요약 포괄손익계산서(총괄, 금감원 업무보고서 기준) 연누계. 보정 {[(x[0], x[3]) for x in calrows[it]][:4]} (경영공시-마스터, 억원). 표내 검산: {chk_s or '해당없음'}",
            }
    report[g] = {"cells": cells, "skips": skips,
                 "stats": {"cells": len(cells), "skips": len(skips), "calibration_passed_items": [k for k, v in passed.items() if v],
                           "calibration_failed_items": [k for k, v in passed.items() if not v]},
                 "calibration_detail": {str(k): v for k, v in calrows.items()}}
    path = os.path.join(OUT_DIR, f"{g}.json")
    json.dump(report[g], open(path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
    print(g, report[g]["stats"])
