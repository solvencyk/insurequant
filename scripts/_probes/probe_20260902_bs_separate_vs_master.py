# -*- coding: utf-8 -*-
"""IFRS17_BS.json 의 코어 BS 항목(1/2/3/31)을 DART 본문 XML 의 **별도(OFS) 재무상태표**와
전수 대조한다. 빌더 로직을 신뢰하지 않고 원문에서 독립적으로 다시 읽는 것이 요점.

동기(2026-09-02): 한화손보 2026.2Q 가 FS-API 의 OFS 빈껍데기 -> CFS 폴백으로 **연결** 값이
들어가 있었다(owner 라이브 QA 발견). 항등식(자산-부채=자본)은 그 상태에서도 정확히 닫혔다
-- 행 전체가 일관되게 연결이었기 때문이다. **항등식만으로는 기준(basis) 오류를 못 잡는다.**

방법: 표 바로 앞 캡션으로 (a) 연결/별도 (b) 단위(원/천원/백만원)를 판정한다. 캡션이
'연결 재무상태표' 면 건너뛰고, '재무상태표' 면 별도로 본다. 첫 값 열 = 당기.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

WANT = {1: "자산총계", 2: "부채총계", 3: "자본총계", 31: "이익잉여금"}
TOL_REL = 0.005
SCALE = {"천원": 1e-3, "백만원": 1.0, "억원": 100.0, "원": 1e-6}

def num(t):
    t = t.strip().replace(",", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    if not re.fullmatch(r"-?\d+", t or ""):
        return None
    return -int(t) if neg else int(t)

def caption_of(text, tbl_start):
    pre = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text[max(0, tbl_start - 900):tbl_start]))
    return pre[-260:]

def norm_label(raw):
    lab = re.sub(r"\s*\(주[^)]*\)\s*", "", raw)
    lab = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩXIVxiv0-9().\s\-]*", "", lab)
    return lab.replace(" ", "").strip()

def sep_bs(text):
    """(항목dict, 단위배수) or None"""
    for m in re.finditer(r"<TABLE.*?</TABLE>", text, re.S):
        tab = m.group(0)
        if "자본과부채총계" not in tab.replace(" ", ""):
            continue
        cap = caption_of(text, m.start())
        capn = cap.replace(" ", "")
        if "재무상태표" not in capn:
            continue
        if "연결재무상태표" in capn:          # 연결 표는 건너뛴다
            continue
        unit = next((u for u in ("백만원", "천원", "억원", "원") if ("단위:" + u) in capn or ("단위：" + u) in capn), None)
        if unit is None:
            continue
        got = {}
        for tr in re.findall(r"<TR.*?</TR>", tab, re.S):
            cells = re.findall(r"<T[EU][^>]*>(.*?)</T[EU]>", tr, re.S)
            txts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
            txts = [t for t in txts if t != ""]
            if len(txts) < 2:
                continue
            lab = norm_label(txts[0])
            for item, name in WANT.items():
                if item in got:
                    continue
                if lab == name or lab == name + "(결손금)":
                    v = num(txts[1])
                    if v is not None:
                        got[item] = v
        if 1 in got and 3 in got:
            return got, SCALE[unit]
    return None

def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi = {(r["원수사명"], r["공시분기"], r["항목번호"]): r["값"] for r in master}
    checked = 0
    mism = []
    skipped = 0
    for xml in sorted((ROOT / "data" / "dart").glob("FY*/raw/*/*.xml")):
        qdir = xml.parts[-4]
        quarter = f"{qdir[2:6]}.{qdir[-1]}Q"
        company = xml.parts[-2].split("_", 1)[-1]
        try:
            txt = xml.read_text(encoding="utf-8", errors="replace")
        except Exception:
            skipped += 1
            continue
        res = sep_bs(txt)
        if not res:
            skipped += 1
            continue
        got, scale = res
        for item, raw_v in got.items():
            mv = mi.get((company, quarter, item))
            if mv is None:
                continue
            checked += 1
            rv = raw_v * scale
            if abs(rv - mv) / max(abs(rv), abs(mv), 1.0) > TOL_REL:
                mism.append((company, quarter, item, mv, rv))
    print(f"별도 BS 표를 못 찾아 건너뛴 필링: {skipped}")
    print(f"대조한 셀 {checked}개 · 불일치 {len(mism)}개 (허용 {TOL_REL:.1%})")
    for c, q, i, mv, rv in sorted(mism, key=lambda x: -abs(x[3] - x[4]) / max(abs(x[4]), 1)):
        print(f"  {c} {q} item{i}({WANT[i]}): 마스터={mv:,.0f} 원문별도={rv:,.0f} "
              f"차이={abs(mv - rv) / max(abs(rv), 1):.1%}")
    return 1 if mism else 0

if __name__ == "__main__":
    raise SystemExit(main())
