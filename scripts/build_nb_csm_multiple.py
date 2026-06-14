# -*- coding: utf-8 -*-
"""ROOT master: 신계약 CSM 배수 (NB CSM multiple), 연누계(YTD) + 당분기 columns.

Schema (matches NB_CSM_multiple.xlsx):
  원보험사코드, 원수사명, 티커, 생손보여부, 공시분기,
  신계약CSM_연누계, 월납월초보험료_연누계, 신계약CSM배수_연누계,
  신계약CSM_당분기, 월납월초보험료_당분기, 신계약CSM배수_당분기

Sources:
  - 신계약CSM (억원): CSM_waterfall.json 항목2 (신계약 CSM).  값 = 연누계(YTD), 값_당분기 = 당분기.
  - 월납월초 (억원): data/kidi/premium_summary.json — KIDI INCOS ML01(생보)/MN07(손보) 합계행,
    denominator_eok = 월납 초회 + 기타 초회 (일시납 제외), YTD 누적.  Joined by KR code (no name match).
    연누계 = denominator_eok; 당분기 = YTD(Q) − YTD(Q-1).

배수 = 신계약CSM ÷ 월납월초 (연누계·당분기 각각).  월납 없으면 배수=null (회사 행은 유지).
신계약CSM 당분기가 음수(4Q 연차 재서술 artifact)면 배수_당분기는 의미 없어 null 처리 + flag.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSM = ROOT / "CSM_waterfall.json"
KIDI = ROOT / "data" / "kidi" / "premium_summary.json"
OUT = ROOT / "NB_CSM_multiple.json"

_QMAP = {"03": 1, "06": 2, "09": 3, "12": 4}


def _qkey(q):
    return (int(q[:4]), int(q[5]))


def _prev_q(q):
    y, n = _qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def load_csm():
    rows = json.loads(CSM.read_text(encoding="utf-8"))
    out = {}   # 원보험사코드 -> {name, ticker, sb, q -> (연누계, 당분기)}
    for r in rows:
        if r.get("항목번호") != 2:                      # 2 = 신계약 CSM
            continue
        code = r.get("원보험사코드")
        d = out.setdefault(code, {"name": r.get("원수사명"), "ticker": r.get("티커"),
                                  "sb": r.get("생손보여부"), "q": {}})
        d["q"][r["공시분기"]] = (r.get("값"), r.get("값_당분기"))
    return out


def load_wolnap():
    d = json.loads(KIDI.read_text(encoding="utf-8"))
    out = {}   # KR code -> {quarter: 월납 초회(YTD 억)}
    for key, v in d["entries"].items():
        kr, ym = key.split("|")
        q = _QMAP.get(ym[4:6])
        if q is None:
            continue
        # Denominator = 월납 초회(VAL4) ONLY. 기타 초회(VAL8, mostly 단체물량) excluded —
        # owner review 2026-06-10: including 기타 deflates 농협생명 3.71→/NH손해 1.74→ etc.;
        # 삼성생명 EX-기타 tracks the IR-disclosed multiple closer (MAE 0.43x vs 1.10x),
        # and IR's own definition is 신계약CSM ÷ 월납월초.
        wol = v.get("month_premium_cheonwon")
        out.setdefault(kr, {})[f"{ym[:4]}.{q}Q"] = (
            round(wol / 100_000.0, 4) if wol is not None else v.get("denominator_eok")
        )
    return out


def _dangi(ytd_by_q, q):
    cur = ytd_by_q.get(q)
    if cur is None:
        return None
    p = _prev_q(q)
    if p is None:
        return round(cur, 4)
    prev = ytd_by_q.get(p)
    return None if prev is None else round(cur - prev, 4)


_MULT_CAP = 40.0    # real NB CSM multiples ≈ 5-22; >40 (or <0) = divide-by-tiny / bad input → null
_MULT_FLOOR = 1.0   # <1.0 = numerator way too small (e.g. 아이엠 분자오염 0.02) — keep value, flag it


def _ratio(num, den):
    if num is None or den is None or den == 0 or num <= 0:
        return None
    r = round(num / den, 4)
    return None if r > _MULT_CAP else r


def main():
    csm = load_csm()
    wol = load_wolnap()
    rows, flags = [], []
    matched = 0
    for code, d in sorted(csm.items(), key=lambda kv: kv[1]["name"] or ""):
        wser = wol.get(code, {})
        if wser:
            matched += 1
        for q in sorted(d["q"], key=_qkey):
            csm_ytd, csm_dangi = d["q"][q]
            wol_ytd = wser.get(q)
            wol_dangi = _dangi(wser, q)
            mult_ytd = _ratio(csm_ytd, wol_ytd)
            mult_dangi = _ratio(csm_dangi, wol_dangi)
            # surface why a 배수 was nulled (impossible ratio = CSM/월납 추출 의심; surfaced not hidden)
            if csm_ytd is not None and wol_ytd not in (None, 0) and mult_ytd is None:
                raw = round(csm_ytd / wol_ytd, 2)
                flags.append(f"{d['name']} {q}: 배수_연누계 null (CSM={csm_ytd} 월납={wol_ytd} → {raw} 비현실)")
            elif mult_ytd is not None and mult_ytd < _MULT_FLOOR:
                flags.append(f"{d['name']} {q}: 배수_연누계 {mult_ytd} < {_MULT_FLOOR} (분자 과소 의심 — 신계약CSM 추출 확인)")
            rows.append({
                "원보험사코드": code, "원수사명": d["name"], "티커": d["ticker"],
                "생손보여부": d["sb"], "공시분기": q,
                "신계약CSM_연누계": csm_ytd,
                "월납월초보험료_연누계": wol_ytd,
                "신계약CSM배수_연누계": mult_ytd,
                "신계약CSM_당분기": csm_dangi,
                "월납월초보험료_당분기": wol_dangi,
                "신계약CSM배수_당분기": mult_dangi,
            })

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    n_w = sum(1 for r in rows if r["월납월초보험료_연누계"] is not None)
    print(f"wrote {OUT}  ({len(rows)} rows, {len(csm)} companies; "
          f"월납 matched={matched}, rows-with-월납={n_w})")
    no_wol = sorted({r["원수사명"] for r in rows if r["월납월초보험료_연누계"] is None})
    if no_wol:
        print(f"월납 없음 (배수 null): {no_wol}")
    if flags:
        print(f"-- flags ({len(flags)}) --")
        for fl in flags[:40]:
            print("  ", fl)


if __name__ == "__main__":
    main()
