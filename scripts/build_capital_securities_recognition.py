# -*- coding: utf-8 -*-
"""자본성증권 **한 건 단위** 인정액 테이블 (owner 설계, 2026-09-01).

## 왜 만들었나

종전에는 회사 단위로 `tier1_hybrid_issued_eok` · `numerator_eok` 같은 **집계값만** 들고 있었다.
그래서 (a) 어느 증권이 얼마를 기본자본으로 인정받는지 되짚을 수 없고, (b) 콜이 도래할 때
기본자본·보완자본에서 각각 얼마가 빠지는지 계산이 회사 단위 뺄셈으로 뭉개졌다.
owner 지시: **증권 단위로 관리하고 그 위에서 소진율과 forward outlook 을 산출한다.**

    회사명  구분          발행일       콜도래일     법정만기     액면가   공시분기 기본자본인정액 보완자본인정액
    메리츠  3호신종자본증권  2021.12.30  2026.12.29  2051.12.30  5,000억  26.2Q   5,000억      0억

## 인정 규칙 (보험업감독업무시행세칙 [별표 22])

**신종자본증권** — Ⅵ.1.가.(1) (p.198)
> 시행일 이전에 발행되어 종전규정에 따라 기본자본으로 인정된 자본증권은 **총요구자본의
> 15%까지는 기본자본으로 분류**하고, 15%를 초과한 금액은 보완자본으로 분류한다.

경과조치분이 한도 **밖**이 아니라 한도 **안**에 들어간다. 경과조치가 면제해 주는 것은
한도가 아니라 자격요건(Step-up 이 있어도 기본자본으로 본다)이다. owner 2026-09-01 결정:
`"종전규정에 따라 기본자본으로 인정된 자본증권"` 이라는 문구상 **신규분과 한도를 공유**한다.
→ 경과조치분·신규분을 **발행일 순**으로 15% 버킷에 채우고, 넘치는 금액은 보완자본으로 분류한다.

**후순위채** — Ⅵ.1.가.(2)(3)
> (2) …보완자본으로 인정된 자본증권과 "(1)"에 따라 보완자본으로 분류된 자본증권은
>     보완자본 **한도초과 여부에 관계없이** 보완자본으로 인정한다.
> (3) 보완자본 한도초과 여부는 "(2)"에 따라 분류된 자본증권을 **제외한** 나머지
>     보완자본 항목만 사용하여 계산한다.

즉 후순위는 신종과 **반대**다 — 경과조치분은 전액 인정되되 한도 계산에서 빠진다.

**후순위 잔존만기 체감** — Ⅲ.3.다.(2)① (p.81)
> 만기시 지급유예조항(Lock-in)을 보유하지 않은 자본증권은 잔존만기가 5년 미만인 시점부터
> 매년 보완자본 불인정금액을 차감하며, 차감율은 **매년 20%씩 상향**한다.
> 경제적 만기는 계약상 만기와 **상환촉진 유인이 있는** 콜옵션의 최초 행사가능일 중 빠른 일자.

연속 직선(`t/5`)이 아니라 **계단식**이다. 차감율 = 20% x ceil(5 - 잔존연수), 0~100%.

**체감 기준 만기 = 법정만기 (owner 2026-09-23 결정).** 종전에는 `min(콜, 법정만기)` 를 써서
콜이 있으면 무조건 콜을 만기로 봤는데, 콜은 발행사의 권리일 뿐 만기가 아니다. 자세한 근거는
`economic_maturity()` 주석에 있다.

**경과조치 종료** — Ⅵ.1.가 본문: **2032-12-31**. 각 채권의 콜이 아니다.

## 아직 못 하는 것 (데이터가 없어서)

`data/bonds/*.json` 127개 채권에 **조건부자본증권 여부 · Step-up 유무 · Lock-in 조항 유무**
플래그가 하나도 없다. 그래서
  - 신규 신종의 한도가 10%인지 15%인지 판정 불가 (지금은 전부 15% 적용)
  - 스텝업이 있는 콜만 경제적 만기로 올릴 수 있는데 판정 불가 (지금은 전부 법정만기 기준)
  - Lock-in 보유채권은 애초에 체감 대상이 아닌데 구분 불가
각 행에 `flags_missing` 로 그 사실을 남긴다 — 조용히 가정하지 않는다.

실행:
  python scripts/build_capital_securities_recognition.py --quarter 2026.2Q \
      --bonds-source data/bonds/capital_securities_fy2026h1.json
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

KICS_START = date(2023, 1, 1)          # K-ICS 시행일
TRANSITION_END = date(2032, 12, 31)    # 공통적용 경과조치 종료 ([별표22] Ⅵ.1.가)
TIER1_LIMIT_RATE = 0.15                # SCR x 15% (조건부자본증권이면 신규분도 15%)
TIER2_LIMIT_RATE = 0.50                # SCR x 50%
_QEND = {"1Q": (3, 31), "2Q": (6, 30), "3Q": (9, 30), "4Q": (12, 31)}


def _pdate(s):
    if not s:
        return None
    try:
        return date(*(int(x) for x in str(s).replace(".", "-").replace("/", "-").split("-")[:3]))
    except Exception:
        return None


def _num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def economic_maturity(b):
    """체감의 기준이 되는 만기 = **계약상(법정) 만기**([별표22] Ⅲ.3.다.(2)①ㄱ).

    조문은 "계약상 만기와 **상환촉진 유인이 있는** 콜옵션의 최초 행사가능일 중 빠른 일자" 다.
    2026-09-23 이전에는 유인 유무를 안 보고 `min(콜, 법정만기)` 를 썼다 — owner 지적으로
    폐기했다. 콜은 발행사의 권리일 뿐 만기가 아니다.

    콜을 만기로 보면 한국 보험사 후순위채의 표준 구조(10년 만기·5년 콜)에서 **발행 직후부터
    체감이 시작된다** — 발행 6개월 된 채권이 80%로 깎였다(흥국생명 2025-12-09·12-31 발행분
    실측). 발행 즉시 20% 할인되는 자본을 발행할 회사는 없다. 5년 콜이 붙는 이유 자체가
    5년째부터 체감이 시작되니 그때 갈아끼우려는 것이므로, 체감은 법정만기에서 세야 한다.

    한화손해보험 제12회(발행 2022-03-07 · 법정만기 2032-03-07) 예 — owner 2026-09-23:
    2027-03 부터 80% -> 2028-03 60% -> 2029-03 40% -> 2030-03 20% -> 2031-03 0%.

    스텝업이 붙은 채권은 콜이 경제적 만기가 되지만 원천에 `step_up` 플래그가 없어 지금은
    한 건도 확인할 수 없다(`flags_missing`). 확인되는 대로 여기에 분기를 넣는다.
    법정만기가 없으면(영구채·만기 미공시) 체감 대상이 아니다.
    """
    return _pdate(b.get("legal_maturity"))


def tier2_recognition_rate(b, as_of: date) -> float:
    """후순위 보완자본 인정율 — 잔존만기 5년 미만부터 **매년 20%p 계단식** 차감."""
    m = economic_maturity(b)
    if m is None:
        return 1.0          # 영구채(법정만기 없음) — 체감 대상이 아니다
    years = (m - as_of).days / 365.25
    if years >= 5:
        return 1.0
    if years <= 0:
        return 0.0
    return max(0.0, 1.0 - 0.20 * math.ceil(5 - years))


def build(quarter: str, bonds_path: Path, scr_by_code: dict[str, float]) -> list[dict]:
    y, q = quarter.split(".")
    as_of = date(int(y), *_QEND[q])
    doc = json.loads(bonds_path.read_text(encoding="utf-8"))
    src_rel = bonds_path.relative_to(ROOT).as_posix()
    rows: list[dict] = []

    for c in doc["companies"]:
        code = c["code"]
        scr = scr_by_code.get(code)
        t1_limit = round(scr * TIER1_LIMIT_RATE, 2) if scr else None
        bonds = [b for b in (c.get("bonds") or []) if (b.get("outstanding_mn") or 0) > 0]

        # --- 신종: 발행일 순으로 15% 버킷을 채운다(경과조치·신규 공유, owner 2026-09-01) ---
        hybrids = sorted([b for b in bonds if b.get("tier") == "hybrid"],
                         key=lambda b: (_pdate(b.get("issue_date")) or date(1900, 1, 1)))
        used = 0.0
        for b in hybrids:
            out_eok = (b.get("outstanding_mn") or 0) / 100.0
            if t1_limit is None:
                t1_rec, t2_rec = None, None
            else:
                room = max(0.0, t1_limit - used)
                t1_rec = min(out_eok, room)
                t2_rec = out_eok - t1_rec      # 15% 초과분 -> 보완자본으로 분류 (Ⅵ.1.가.(1))
                used += t1_rec
            rows.append(_row(c, b, quarter, out_eok, t1_rec, t2_rec, src_rel,
                             t1_limit, scr, "hybrid"))

        # --- 후순위: 전액 보완자본. 잔존만기 체감 적용 ---
        for b in sorted([b for b in bonds if b.get("tier") != "hybrid"],
                        key=lambda b: (_pdate(b.get("issue_date")) or date(1900, 1, 1))):
            out_eok = (b.get("outstanding_mn") or 0) / 100.0
            rate = tier2_recognition_rate(b, as_of)
            rows.append(_row(c, b, quarter, out_eok, 0.0, round(out_eok * rate, 2),
                             src_rel, t1_limit, scr, "subordinated", rate=rate))
    return rows


def _row(c, b, quarter, out_eok, t1_rec, t2_rec, src_rel, t1_limit, scr, tier, rate=None):
    issue = _pdate(b.get("issue_date"))
    gf = bool(issue and issue < KICS_START)
    call = _pdate(b.get("call_date"))
    legal = economic_maturity(b)
    return {
        "원보험사코드": c["code"],
        "회사명": c["company"],
        "구분": b.get("name"),
        "종류": "신종자본증권" if tier == "hybrid" else "후순위채",
        "발행일": issue.isoformat() if issue else None,
        # 콜 최초 행사가능일. 2026-09-23 이전에는 여기에 min(콜, 법정만기) 가 들어 있었다
        # — 체감 기준이 법정만기로 바뀌면서 이 열은 콜 그 자체만 담는다(`콜근거` 와 짝).
        "콜만기도래일": call.isoformat() if call else None,
        # 2026-09-23 신설. **보완자본 체감은 이 열에서 센다**(콜만기도래일이 아니라).
        "법정만기일": legal.isoformat() if legal else None,
        "콜근거": b.get("call_source"),
        "액면가_억": round((b.get("face_amount_mn") or 0) / 100.0, 2),
        "잔액_억": round(out_eok, 2),
        "공시분기": quarter,
        "기본자본인정액_억": None if t1_rec is None else round(t1_rec, 2),
        "보완자본인정액_억": None if t2_rec is None else round(t2_rec, 2),
        "경과조치": gf,
        "경과조치종료일": TRANSITION_END.isoformat() if gf else None,
        "기본자본한도_억": t1_limit,
        "SCR_억": scr,
        "보완자본인정율": rate,
        "잔액기준일": b.get("as_of"),
        "출처": b.get("source_file") or src_rel,
        # 조건부자본증권·Step-up·Lock-in 플래그가 원천에 없다 — 10%/15% 판정과
        # 스텝업 콜의 경제적 만기 승격을 지금 데이터로는 확정할 수 없다. 조용히 가정하지 않는다.
        "flags_missing": ["조건부자본증권여부", "step_up", "lock_in"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quarter", default="2026.2Q")
    ap.add_argument("--bonds-source", default="data/bonds/capital_securities_fy2026h1.json")
    ap.add_argument("--out", default="kics_capital_securities.json")
    a = ap.parse_args()

    t1 = json.loads((ROOT / "kics_tier1_utilization.json").read_text(encoding="utf-8"))
    scr = {r["code"]: r.get("scr_eok") for r in t1["results"] if r.get("scr_eok")}

    rows = build(a.quarter, ROOT / a.bonds_source, scr)
    out = ROOT / a.out
    out.write_text(json.dumps({
        "quarter": a.quarter,
        "unit": "억원",
        "rule_source": "보험업감독업무시행세칙 [별표22] Ⅵ.1.가 (경과조치) · Ⅲ.2.다/마 (한도) · Ⅲ.3.다.(2)① (체감)",
        "hybrid_limit_policy": "경과조치분·신규분이 SCR×15% 한도를 공유 (owner 2026-09-01), 발행일 순 충전",
        "subordinated_limit_policy": "경과조치분은 전액 인정 + 보완자본 한도 계산에서 제외 ([별표22] Ⅵ.1.가.(3))",
        "bonds_source": a.bonds_source,
        "n_rows": len(rows),
        "rows": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    n_hy = sum(1 for r in rows if r["종류"] == "신종자본증권")
    over = [r for r in rows if r["종류"] == "신종자본증권" and (r["보완자본인정액_억"] or 0) > 0]
    print(f"[wrote] {out.relative_to(ROOT)}  {len(rows)}행 "
          f"(신종 {n_hy} · 후순위 {len(rows)-n_hy}) · {a.quarter}")
    print(f"  15% 한도 초과로 보완자본 재분류된 신종: {len(over)}건 "
          f"{sum(r['보완자본인정액_억'] or 0 for r in over):,.0f}억")

    # 체감이 법정만기 하나에 달려 있으므로(2026-09-23~) 그게 없는 후순위는 인정율 1.0 이
    # **체감 대상이 아니라서**가 아니라 **모르기 때문에** 나온 값이다. 조용히 넘기지 않는다.
    nolegal = [r for r in rows if r["종류"] == "후순위채" and not r["법정만기일"]]
    if nolegal:
        print(f"  [주의] 법정만기 미상 후순위 {len(nolegal)}건 — 체감 못 함(인정율 1.0 으로 둠):")
        for r in nolegal:
            print(f"    {r['회사명']} {r['구분']} 잔액 {r['잔액_억']:,.0f}억")
    return 0


if __name__ == "__main__":
    sys.exit(main())
