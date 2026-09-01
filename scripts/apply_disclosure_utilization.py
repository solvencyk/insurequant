# -*- coding: utf-8 -*-
"""자본증권 인정한도 소진율을 **경영공시 항목으로 직접** 산출한다 (owner 2026-09-01 결정).

## 왜 바꿨나

종전에는 DART 채권 발행현황을 회사별로 재구성해 분자를 만들었다. 그게 구조적으로 과소했다 —
**한도는 증권 종류별이 아니라 계정 전체에 걸리기 때문이다.**

  · 기본자본 한도(SCR×15%)의 대상은 `자본항목 중 보통주 이외의 자본증권`(공시 item6) 전체다.
    신종자본증권만이 아니다. 실측: 6개사에서 item6 가 우리 신종잔액보다 크다
    (흥국생명 +2,296억 · 한화손해 +1,881억 · 아이엠라이프 +1,517억 · 하나손해 +999억 …).
  · 보완자본 한도(SCR×50%)의 대상은 보완자본 전체다. 후순위채 말고도 해약환급금 초과분·
    대손충당금 등이 들어간다. 실측: 34사 합계 354,926억이 후순위채가 아닌 부분이었다
    (삼성화재·하나손해는 후순위 0인데 보완자본은 각각 3,090억·2,008억).

그 결과 재구성 분자가 공시와 크게 어긋났다:

    한화생명 공시 222.4% vs 재구성 21.2% · 교보생명 72.7% vs 8.2% · 코리안리 89.1% vs 11.1%
    미래에셋 112.4% vs 21.6% · 아이엠라이프 96.0% vs 33.4%

## 산식

    기본자본 소진율 = item6  (보통주 이외의 자본증권)  / (item14 x 15%)
    보완자본 소진율 = item47 (보완자본 한도 적용 전)   / (item14 x 50%)

분자는 공시에서 받고 **분모는 조문식으로 세운다**. [별표22] Ⅲ.2.다.(1)②·Ⅲ.2.마 가 한도를
총요구자본 비율로 정의하므로 계산이 정확한데, 공시 item48 은 파싱이 깨진 회사가 있다
(2026.2Q 4사, 아래 코드 주석). 분모를 계산으로 세우면 그 결함이 소진율로 새지 않는다.

경과조치분을 **따로 빼지 않는다**. 신종은 [별표22] Ⅵ.1.가.(1) 이 15% 한도 **안**에 넣으라고
하므로 item6 에 포함된 채로 맞다. 보완자본은 Ⅵ.1.가.(3) 이 경과조치분을 한도 계산에서 빼라고
하지만, **item47 은 발행사가 그 조정을 이미 반영해 산출한 값**이다 — DB생명 실측이 근거다:

    item47 = 2,563.95  <  item54 (기발행 후순위채무) = 3,135.91

item47 이 총액이라면 기발행분보다 작을 수 없다. 여기서 item53/54 를 또 빼면 △7.0% 라는
음수 소진율이 나온다(이중차감). 발행사 산출값을 그대로 쓰는 것이 정본이다.

## 채권 단위 데이터는 버리지 않는다

`kics_capital_securities.json`(증권 한 건 단위)과 `data/bonds/**` 는 계속 필요하다 —
**forward outlook** 은 "어느 증권이 언제 빠지는가" 를 알아야 하고, 공시는 그걸 안 알려준다.
소진율에서만 손을 뗀다.

## 부수 효과

분자가 공시 분기말 수치가 되므로 **분자/분모 기준일 불일치가 사라진다**. 화면의
"발행잔액 기준일 2025-12-31" 경고(2026-09-01 owner 지적)는 소진율에 관한 한 무의미해진다.

실행:
  python scripts/apply_disclosure_utilization.py --quarter 2026.2Q [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

KICS = ROOT / "kics_disclosure.json"
T1F = ROOT / "kics_tier1_utilization.json"
T2F = ROOT / "kics_tier2_utilization.json"
# 배포본만 고치면 `validate_live_artifacts` 가 "배포본 != 빌더 산출" 로 RED 를 낸다.
# 불변식 1번(게이트가 검사하는 파일 = 사용자가 보는 파일)의 반대편이라 같은 값을 둘 다 쓴다.
OUT_T1 = ROOT / "output" / "tier1_utilization"
OUT_T2 = ROOT / "output" / "tier2_utilization"

TIER1_RATE = 0.15
TIER2_RATE = 0.50   # [별표22] Ⅲ.2.마 — 보완자본은 총요구자본의 50%를 한도로 한다
_QEND = {"1Q": (3, 31), "2Q": (6, 30), "3Q": (9, 30), "4Q": (12, 31)}

ITEM_T1_SECURITIES = 6    # 2. 자본항목 중 보통주 이외의 자본증권
ITEM_SCR = 14             # 나. 지급여력기준금액
ITEM_T2_PRE_LIMIT = 47    # 보완자본 한도 적용 전
ITEM_T2_LIMIT = 48        # 보완자본 한도
ITEM_GF_HYBRID = 53       # (기발행 신종자본증권)(TFI표)
ITEM_GF_SUB = 54          # (기발행 후순위채무)(TFI표)


def _f(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_disclosure(quarter: str) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = {}
    for r in json.loads(KICS.read_text(encoding="utf-8")):
        if r.get("공시분기") != quarter:
            continue
        out.setdefault(r["원보험사코드"], {})[r["항목번호"]] = _f(r.get("값"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quarter", default="2026.2Q")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    y, q = a.quarter.split(".")
    as_of = date(int(y), *_QEND[q]).isoformat()

    disc = load_disclosure(a.quarter)
    t1doc = json.loads(T1F.read_text(encoding="utf-8"))
    t2doc = json.loads(T2F.read_text(encoding="utf-8"))

    changed = []
    missing = {"item6": [], "item47": [], "item48_mismatch": [], "item14": []}

    for row in t1doc["results"]:
        d = disc.get(row["code"], {})
        sec, scr = d.get(ITEM_T1_SECURITIES), d.get(ITEM_SCR)
        if sec is None:
            missing["item6"].append(row["code"])
        if scr is None:
            missing["item14"].append(row["code"])
        if sec is None or not scr:
            continue
        limit = round(scr * TIER1_RATE, 2)
        pct = round(sec / limit * 100, 1) if limit else None
        before = (row.get("tier1_hybrid_issued_eok"), row.get("utilization_pct"))
        row["tier1_hybrid_issued_eok"] = round(sec, 2)
        # `recognized` 는 종전에도 issued 와 같은 값이었다 — 소진율은 100% 에서 자르지 않는다
        # (owner 2026-06-14 LOCKED). `validate_live_artifacts` 가 소진율 항등식을
        # recognized/limit×100 == utilization_pct 로 검사하므로 여기서 같이 맞춘다.
        row["tier1_hybrid_recognized_eok"] = round(sec, 2)
        row["tier1_hybrid_overflow_eok"] = round(max(0.0, sec - limit), 2)
        row["tier1_hybrid_limit_eok"] = limit
        row["tier1_hybrid_limit_strict_eok"] = round(scr * 0.10, 2)
        row["utilization_pct"] = pct
        row["utilization_pct_strict"] = round(sec / (scr * 0.10) * 100, 1) if scr else None
        row["tier1_grandfathered_hybrid_eok"] = d.get(ITEM_GF_HYBRID)
        row["numerator_as_of"] = as_of
        row["data_source"] = f"kics_disclosure item6 / (item14 x {TIER1_RATE:.0%})"
        row["issued_source"] = "disclosure_item6"
        if before != (row["tier1_hybrid_issued_eok"], row["utilization_pct"]):
            changed.append(("t1", row["code"], row["company"], before,
                            (row["tier1_hybrid_issued_eok"], row["utilization_pct"])))

    for row in t2doc["results"]:
        d = disc.get(row["code"], {})
        num, scr = d.get(ITEM_T2_PRE_LIMIT), d.get(ITEM_SCR)
        # 분모는 **공시 item48 을 그대로 쓰지 않고 item14 x 50% 로 산출**한다.
        # [별표22] Ⅲ.2.마 가 "보완자본은 총요구자본의 50%를 한도로 한다" 로 정의하므로
        # 계산이 정확하고, 공시 item48 은 파싱이 깨진 회사가 있다 — 2026.2Q 실측 4사:
        #   신한라이프 59,367(SCR×50%=26,880) · 롯데 28,741(10,556)
        #   DB손해 124,792(57,550) · AIG손해 754(1,390)
        # 기본자본×100%(RBC 구제도)도 아니어서 값의 정체가 불명이다. 분자만 공시에서 받고
        # 분모는 조문식으로 세우면 그 결함이 소진율로 새지 않는다(별건으로 parser 라우팅).
        lim = round(scr * TIER2_RATE, 2) if scr else None
        disclosed_lim = d.get(ITEM_T2_LIMIT)
        if num is None:
            missing["item47"].append(row["code"])
        if scr is None:
            missing["item14"].append(row["code"])
        if disclosed_lim is not None and lim and abs(disclosed_lim - lim) > max(1.0, lim * 0.005):
            missing["item48_mismatch"].append(row["code"])
        if num is None or not lim:
            continue
        before = (row.get("numerator_eok"), row.get("utilization_pct"))
        row["numerator_eok"] = round(num, 2)
        row["tier2_limit_eok"] = round(lim, 2)
        row["utilization_pct"] = round(num / lim * 100, 1)
        row["grandfathered_subordinated_eok"] = d.get(ITEM_GF_SUB)
        row["grandfathered_hybrid_eok"] = d.get(ITEM_GF_HYBRID)
        row["numerator_as_of"] = as_of
        row["data_source"] = "kics_disclosure item47 / (item14 x 50%)"
        if before != (row["numerator_eok"], row["utilization_pct"]):
            changed.append(("t2", row["code"], row["company"], before,
                            (row["numerator_eok"], row["utilization_pct"])))

    for doc, num, den in ((t1doc, "item6 (자본항목 중 보통주 이외의 자본증권)",
                           f"item14 x {TIER1_RATE:.0%}"),
                          (t2doc, "item47 (보완자본 한도 적용 전)", "item14 x 50% ([별표22] Ⅲ.2.마)")):
        doc["definition"]["numerator"] = num
        doc["definition"]["limit"] = den
        doc["definition"]["source"] = f"kics_disclosure.json ({a.quarter} 경영공시)"
        doc["definition"]["as_of"] = as_of
        doc["definition"]["as_of_note"] = (
            "분자·분모 모두 같은 분기말 경영공시 항목이라 기준일이 어긋나지 않는다. "
            "채권 발행현황(data/bonds/**)은 forward outlook 전용으로 남는다.")

    print(f"[{a.quarter}] 소진율을 공시 산식으로 교체 — 변경 {len(changed)}건")
    for tier, code, name, b, aft in changed:
        print(f"  {tier} {code} {name[:12]:14s} {b[0]}→{aft[0]} 억 · {b[1]}%→{aft[1]}%")
    for k, v in missing.items():
        if v:
            print(f"  결측 {k}: {len(v)}사 {v}")
    if a.dry_run:
        print("(dry-run; 파일 안 씀)")
        return 0
    T1F.write_text(json.dumps(t1doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    T2F.write_text(json.dumps(t2doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written = [T1F.name, T2F.name]
    tag = a.quarter.replace(".", "")
    for doc, outdir, tier in ((t1doc, OUT_T1, "tier1"), (t2doc, OUT_T2, "tier2")):
        f = outdir / f"{tier}_utilization_{tag}.json"
        if f.exists():
            f.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
            written.append(f.relative_to(ROOT).as_posix())
    print("[wrote] " + " · ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
