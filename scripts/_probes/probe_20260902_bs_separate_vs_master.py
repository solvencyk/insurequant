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
# owner 2026-09-02: 소급재작성본을 최종 채택한다. 마스터는 DART FS-API 의 후속 재작성본을
# 담으므로 '원 필링 당시본'과 다른 셀이 구조적으로 생긴다. 그 셀들은 여기 등재돼 있어야
# 하고, 등재된 것만 통과시킨다 -- 등재부에 적어두기만 하고 룰이 안 읽으면 소용이 없다.
RESTATED = ROOT / "data" / "_gold" / "bs_restated_cells.json"
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
    lab = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩXIVxiv0-9().\s\-]*", "", lab)
    return lab.replace(" ", "").strip()

def sep_bs(text):
    """(항목dict, 단위배수) or None"""
    for m in re.finditer(r"<TABLE.*?</TABLE>", text, re.S):
        tab = m.group(0)
        flat = tab.replace(" ", "").replace("　", "")
        # 대차대조 마감행 표기는 회사마다 다르다(삼성화재 '부채와자본총계', 동양생명 '부채및자본총계').
        if not any(k in flat for k in ("자본과부채총계", "부채와자본총계",
                                       "부채및자본총계", "자본과부채의총계")):
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
            cells = re.findall(r"<T[EUDH][^>]*>(.*?)</T[EUDH]>", tr, re.S)
            txts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
            txts = [t for t in txts if t != ""]
            if len(txts) < 2:
                continue
            lab = norm_label(txts[0])
            for item, name in WANT.items():
                if item in got:
                    continue
                if lab == name or lab == name + "(결손금)":
                    # 값 열이 항상 두 번째는 아니다 -- 한화생명 별도 BS 는 주석번호 열이
                    # 먼저 온다(['V. 이익잉여금', '29', '6,079,580,648,258']). 금액은 항상
                    # 콤마 표기이므로 그것으로 주석번호와 가른다.
                    v = None
                    for cand2 in txts[1:]:
                        # 금액은 3자리 콤마 묶음이다. 주석번호도 콤마를 쓸 수 있어서
                        # (악사손해 '21,22') 콤마 유무만으로는 못 가른다 -- 형식을 본다.
                        if AMOUNT_RE.fullmatch(cand2.replace("　", "").strip()):
                            v = num(cand2)
                            if v is not None:
                                break
                    if v is None and len(txts) > 1:
                        v = num(txts[1])
                    if v is not None:
                        got[item] = v
        if 1 in got and 3 in got:
            return got, SCALE[unit]
    return None

def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi = {(r["원수사명"], r["공시분기"], r["항목번호"]): r["값"] for r in master}
    # raw 리프는 'KR####_<DART canonical>' 인데 그 canonical 이 마스터의 원수사명과 다르다
    # (KR0069_삼성생명 vs '삼성생명보험'). 이름으로 매칭하면 원문이 있는데도 '없음'으로
    # 읽힌다 -- 2026-09-02 에 실제로 그렇게 오판했다. 코드로 잇는다.
    code2name = {r["원보험사코드"]: r["원수사명"] for r in master}
    ledger = {}
    if RESTATED.exists():
        ledger = json.loads(RESTATED.read_text(encoding="utf-8")).get("cells", {})
    checked = 0
    mism = []
    adopted = []
    skipped = 0
    cand: dict = {}
    for xml in sorted((ROOT / "data" / "dart").glob("FY*/raw/*/*.xml")):
        qdir = xml.parts[-4]
        quarter = f"{qdir[2:6]}.{qdir[-1]}Q"
        leaf = xml.parts[-2]
        company = code2name.get(leaf.split("_", 1)[0], leaf.split("_", 1)[-1])
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
        # 한 (회사,분기) 에 필링이 여러 개다(사업보고서·감사보고서 등). 파일마다 따로 판정하면
        # 그중 하나가 요약표를 물어 0 을 내는 순간 거짓 불일치가 된다 -- 2026-09-02 실측.
        # 그래서 후보값을 모아 두고 '어느 필링과도 안 맞을 때'만 불일치로 본다.
        for item, raw_v in got.items():
            cand.setdefault((company, quarter, item), []).append(raw_v * scale)
    for (company, quarter, item), vals in sorted(cand.items()):
        mv = mi.get((company, quarter, item))
        if mv is None:
            continue
        checked += 1
        if any(abs(v - mv) / max(abs(v), abs(mv), 1.0) <= TOL_REL for v in vals):
            continue
        best = min(vals, key=lambda v: abs(v - mv))
        ent = ledger.get(f"{company}|{item}|{quarter}")
        if ent and any(abs(ent.get("원_필링_당시본", 0) - v) / max(abs(v), 1.0) <= TOL_REL
                       for v in vals):
            adopted.append((company, quarter, item, mv, ent["원_필링_당시본"]))
        else:
            mism.append((company, quarter, item, mv, best))

    print(f"별도 BS 표를 못 찾아 건너뛴 필링: {skipped}")
    print(f"  (마스터에 그 (회사,분기) 셀이 아예 없어 대조 대상이 아닌 것은 위 수치와 별개)")
    print(f"대조한 셀 {checked}개 · 불일치 {len(mism)}개 · "
          f"소급재작성 채택(등재됨) {len(adopted)}개 (허용 {TOL_REL:.1%})")
    for c, q, i, mv, rv in sorted(adopted):
        print(f"  [재작성채택] {c} {q} item{i}({WANT[i]}): 마스터={mv:,.0f} 원필링={rv:,.0f}")
    for c, q, i, mv, rv in sorted(mism, key=lambda x: -abs(x[3] - x[4]) / max(abs(x[4]), 1)):
        print(f"  {c} {q} item{i}({WANT[i]}): 마스터={mv:,.0f} 원문별도={rv:,.0f} "
              f"차이={abs(mv - rv) / max(abs(rv), 1):.1%}")
    return 1 if mism else 0

if __name__ == "__main__":
    raise SystemExit(main())
