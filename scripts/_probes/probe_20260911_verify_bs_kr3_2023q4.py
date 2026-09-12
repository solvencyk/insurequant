# -*- coding: utf-8 -*-
"""KR1098/KR0075/KR0150 2023.4Q IFRS17_BS 마스터를 DART 감사보고서 원문(별도재무상태표)과
전수 대조한다. probe_20260902_bs_separate_vs_master.py 의 검증된 파싱 로직(단위/연결·별도
판정, 라벨 정규화, 주석번호-vs-금액 열 판별)을 21개 코어 항목 전체로 확장.

items 5-8(법정준비금 4종)은 별도 주석 표라 이 표에는 보통 없다 -- 있으면 잡고, 없으면
별도로 보고한다(정본 대조 미실시로 표시, 추측하지 않는다).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

# 항목번호 -> 마스터 항목명 (probe_20260911_item_label_map.py 실측)
WANT = {
    1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익누계액",
    10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
    12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산",
    14: "재보험계약자산", 15: "유형자산",
    20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채",
    23: "차입부채", 24: "기타부채",
    30: "자본금", 31: "이익잉여금",
}
# 원문 라벨 변형(회사별로 다른 표기가 쓰일 수 있어 후보를 넓힌다)
ALIASES = {
    4: ["기타포괄손익누계액", "기타자본구성요소", "기타포괄손익누계액(기타자본구성요소)"],
    11: ["당기손익-공정가치측정금융자산", "당기손익-공정가치측정금융자산(FVPL)"],
    12: ["기타포괄손익-공정가치측정금융자산", "기타포괄손익-공정가치측정금융자산(FVOCI)"],
    22: ["투자계약부채"],
}

TARGETS = [
    ("KR1098", "카카오페이손해보험",
     "data/dart/FY2023_Q4/raw/KR1098_카카오페이손해보험_20240329002933/20240329002933_00760.xml"),
    ("KR0075", "비엔피파리바카디프생명보험",
     "data/dart/FY2023_Q4/raw/KR0075_비엔피파리바카디프생명보험_20240403001384/20240403001384_00760.xml"),
    ("KR0150", "서울보증보험",
     "data/dart/FY2023_Q4/raw/KR0150_서울보증보험_20240403001186/20240403001186_00760.xml"),
]
QUARTER = "2023.4Q"
TOL_REL = 0.005
AMOUNT_RE = re.compile(r"\(?-?\d{1,3}(?:,\d{3})+\)?")
SCALE = {"천원": 1e-3, "백만원": 1.0, "억원": 100.0, "원": 1e-6}


def num(t):
    t = t.replace("　", "").replace("&nbsp;", "").strip().replace(",", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    if not re.fullmatch(r"-?\d+", t or ""):
        return None
    return -int(t) if neg else int(t)


def caption_of(text, tbl_start):
    pre = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text[max(0, tbl_start - 900):tbl_start]))
    return pre[-260:]


def norm_label(raw):
    raw = raw.replace("　", " ").replace("&nbsp;", " ")
    lab = re.sub(r"\s*\(주[^)]*\)\s*", "", raw)
    lab = re.sub(r"^[Ⅰ-ⅹXIVxiv0-9().\s\-]*", "", lab)
    return lab.replace(" ", "").strip()


def find_bs_tables(text):
    """별도재무상태표로 보이는 모든 표 후보를 (라벨, 단위배수, 캡션) 로 반환."""
    out = []
    for m in re.finditer(r"<TABLE.*?</TABLE>", text, re.S):
        tab = m.group(0)
        flat = tab.replace(" ", "").replace("　", "")
        if not any(k in flat for k in ("자본과부채총계", "부채와자본총계",
                                        "부채및자본총계", "자본과부채의총계")):
            continue
        cap = caption_of(text, m.start())
        capn = cap.replace(" ", "")
        if "재무상태표" not in capn:
            continue
        if "연결재무상태표" in capn:
            continue
        unit = next((u for u in ("백만원", "천원", "억원", "원")
                     if ("단위:" + u) in capn or ("단위：" + u) in capn), None)
        if unit is None:
            continue
        got = {}
        for tr in re.findall(r"<TR.*?</TR>", tab, re.S):
            cells = re.findall(r"<T[EUDH][^>]*>(.*?)</T[EUDH]>", tr, re.S)
            txts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
            txts = [t for t in txts if t != ""]
            if len(txts) < 2:
                continue
            lab = norm_label(txts[0])
            for item, name in WANT.items():
                if item in got:
                    continue
                cand_labels = set(ALIASES.get(item, [])) | {name}
                if lab not in cand_labels and lab != name + "(결손금)":
                    continue
                v = None
                for cand2 in txts[1:]:
                    if AMOUNT_RE.fullmatch(cand2.replace("　", "").strip()):
                        v = num(cand2)
                        if v is not None:
                            break
                if v is None and len(txts) > 1:
                    v = num(txts[1])
                if v is not None:
                    got[item] = v
        if 1 in got and 3 in got:
            out.append((got, SCALE[unit], cap[-120:]))
    return out


def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in master}

    for code, name, relpath in TARGETS:
        print(f"\n=== {code} {name} {QUARTER} ===")
        xml_path = ROOT / relpath
        if not xml_path.exists():
            print(f"  raw 없음: {relpath}")
            continue
        txt = xml_path.read_text(encoding="utf-8", errors="replace")
        tables = find_bs_tables(txt)
        if not tables:
            print("  별도재무상태표 표를 못 찾음 (스킵)")
            continue
        # 여러 표 후보가 있을 수 있음(본문/부속) -- 항목별로 후보값을 모은다
        cand: dict[int, list[float]] = {}
        for got, scale, cap in tables:
            print(f"  표 발견: 캡션='...{cap}' scale={scale} items={sorted(got)}")
            for item, raw_v in got.items():
                cand.setdefault(item, []).append(raw_v * scale)
        for item in sorted(WANT):
            mv = mi.get((code, QUARTER, item))
            vals = cand.get(item)
            label = WANT[item]
            if vals is None:
                status = "원문표에 항목없음(N/A 가능)" if mv is None else "원문표에서 못 찾음(마스터엔 값 있음!)"
                print(f"  item{item}({label}): 마스터={mv} 원문={vals} -> {status}")
                continue
            if mv is None:
                print(f"  item{item}({label}): 마스터=None 원문={vals} -> 마스터 결측, 채움 후보")
                continue
            match = any(abs(v - mv) / max(abs(v), abs(mv), 1.0) <= TOL_REL for v in vals)
            print(f"  item{item}({label}): 마스터={mv:,.3f} 원문(scaled)={[f'{v:,.3f}' for v in vals]} "
                  f"-> {'MATCH' if match else 'MISMATCH'}")

        # items 5-8 (법정준비금) -- 이 표에는 보통 없음. 원문 전체에서 키워드 존재만 확인.
        print("  --- 법정준비금(5-8) 원문 키워드 존재 확인(별도표 없음, 주석 위치는 미탐색) ---")
        for item, kw in ((5, "해약환급금준비금"), (6, "비상위험준비금"), (7, "대손준비금"), (8, "보증준비금")):
            cnt = txt.count(kw)
            mv = mi.get((code, QUARTER, item))
            print(f"  item{item}({kw}): 마스터={mv} 원문 키워드 등장={cnt}회")


if __name__ == "__main__":
    main()
