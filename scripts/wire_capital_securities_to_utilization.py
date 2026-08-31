# -*- coding: utf-8 -*-
"""LIVE wire: replace the broken tier1/tier2_utilization numerator (proxy/item3) with the real
DART 신종자본증권/후순위채 발행현황, K-ICS 경과조치 면제 적용 (owner 2026-06-20).

경과조치(transitional grandfathering): 자본증권 issued BEFORE 2023-01-01 (K-ICS 시행 전) is
recognized regardless of the new limit → EXCLUDED from 한도소진 numerator, tracked separately.
한도소진율 분자 = post-2023 신규 발행 인정액 (this is what consumes the new SCR-based limit).

  Tier1(신종) 소진 = new_hybrid_issued / (SCR×15%);  overflow(new_hybrid − limit) → Tier2.
  Tier2(보완) 소진 = (new_sub 인정금액[잔존만기 to CALL straight-line] + new_hybrid overflow) / (SCR×50%).
  경과조치 면제분 = pre-2023 hybrid + pre-2023 sub (shown separately, NOT in 소진 numerator).

Also fixes denom bug (신한이지 tier2_limit 2.68 → SCR×50%). Backs up the live JSONs to .bak.
Updates existing records' fields in place (preserves schema for HTML/gate); companies w/o bonds → 0.
"""
import argparse
import io
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
KICS_START = date(2023, 1, 1)

# 분기는 인자로 받는다 (2026-08-31). 그 전에는 20261Q 와 2026-03-31 이 리터럴로 박혀 있어
# 새 분기를 돌리려면 파일을 고쳐야 했다. 기본값은 종전 동작 그대로다.
_QEND = {"1Q": (3, 31), "2Q": (6, 30), "3Q": (9, 30), "4Q": (12, 31)}
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--quarter", default="2026.1Q", help="예: 2026.2Q")
_ap.add_argument("--as-of", default=None,
                 help="후순위 잔존만기 상각 기준일 (기본: --quarter 의 분기말)")
_ap.add_argument("--bonds-source", default="data/bonds/capital_securities_fy2025.json",
                 help="per-bond 발행잔액 소스 (repo-relative). 기본은 종전 동작 그대로 FY2025 "
                      "연간(2025-12-31). 회사별로 더 최신 반기/분기 데이터가 섞인 파일(예: "
                      "data/bonds/capital_securities_fy2026h1.json)을 넘기면 그걸 쓴다 — 단 "
                      "그 파일도 회사별/채권별 as_of 를 정직하게 달고 있어야 한다(추측 금지, "
                      "2026-09-01 owner 티켓: 분모=2026.2Q인데 분자가 2025.4Q였던 사고).")
_args = _ap.parse_args()
_y, _q = _args.quarter.split(".")
_tag = f"{_y}{_q}"
AS_OF = (date.fromisoformat(_args.as_of) if _args.as_of
         else date(int(_y), *_QEND[_q]))

BONDS_SOURCE_REL = _args.bonds_source
BONDS = {c["code"]: c for c in json.loads((ROOT / BONDS_SOURCE_REL).read_text("utf-8"))["companies"]}
T1F = ROOT / "output" / "tier1_utilization" / f"tier1_utilization_{_tag}.json"
T2F = ROOT / "output" / "tier2_utilization" / f"tier2_utilization_{_tag}.json"
t1doc = json.loads(T1F.read_text("utf-8"))
t2doc = json.loads(T2F.read_text("utf-8"))
SCR = {r["code"]: r.get("scr_eok") for r in t1doc["results"]}


def pdate(s):
    if not s:
        return None
    try:
        return date(*(int(x) for x in s.replace(".", "-").replace("/", "-").split("-")[:3]))
    except Exception:
        return None


def eff_mat(b):
    return pdate(b.get("call_date")) or pdate(b.get("legal_maturity"))


def issue_est(b):
    d = pdate(b.get("issue_date"))
    if d:
        return d
    lm = pdate(b.get("legal_maturity"))            # infer: 신종~30y, 후순위~10y term
    if lm:
        yrs = 30 if b.get("tier") == "hybrid" else 10
        try:
            return lm.replace(year=lm.year - yrs)
        except Exception:
            return date(lm.year - yrs, 1, 1)
    return None


def is_grandfathered(b):
    iss = issue_est(b)
    return (iss is not None) and (iss < KICS_START)


def amort(b):  # K-ICS 후순위 보완자본 인정 (straight-line over final 5y to CALL)
    m = eff_mat(b)
    if m is None:
        return 1.0
    t = (m - AS_OF).days / 365.25
    return max(0.0, min(1.0, t / 5.0))


def comp(code):
    c = BONDS.get(code)
    scr = SCR.get(code)
    t1lim = round(scr * 0.15, 2) if scr is not None else None
    t1lim_strict = round(scr * 0.10, 2) if scr is not None else None
    t2lim = round(scr * 0.50, 2) if scr is not None else None
    if not c or not (c.get("bonds")):
        return dict(scr=scr, t1lim=t1lim, t1lim_strict=t1lim_strict, t2lim=t2lim,
                    new_hyb=0.0, gf_hyb=0.0, new_sub_recog=0.0, new_sub_gross=0.0, gf_sub=0.0,
                    overflow=0.0, t1_util=0.0, t2_num=0.0, t2_util=0.0, n=0,
                    hyb_as_of=None, sub_as_of=None)
    new_hyb = gf_hyb = new_sub_recog = new_sub_gross = gf_sub = 0.0
    hyb_as_ofs, sub_as_ofs = [], []  # as_of of every bond that actually feeds a numerator > 0
    for b in c["bonds"]:
        out = (b.get("outstanding_mn") or 0) / 100.0
        gf = is_grandfathered(b)
        b_as_of = b.get("as_of") or c.get("as_of")
        if b.get("tier") == "hybrid":
            if gf:
                gf_hyb += out
            else:
                new_hyb += out
                if out and b_as_of:
                    hyb_as_ofs.append(b_as_of)
        else:
            if gf:
                gf_sub += out
            else:
                new_sub_gross += out
                new_sub_recog += out * amort(b)
                if out and b_as_of:
                    sub_as_ofs.append(b_as_of)
    overflow = max(0.0, new_hyb - t1lim) if t1lim is not None else 0.0
    t1_util = round(new_hyb / t1lim * 100, 1) if t1lim else None
    t2_num = new_sub_recog + overflow
    t2_util = round(t2_num / t2lim * 100, 1) if t2lim else None
    # 분자 as_of = 실제로 그 분자에 기여한 채권들의 가장 오래된(=제일 보수적인) as_of.
    # tier2 분자는 후순위 인정액 + 신종 초과분(overflow) 두 소스가 섞일 수 있어 두 as_of 중
    # 더 오래된 쪽을 쓴다 — "숫자는 제일 stale 한 구성요소만큼만 fresh 하다".
    hyb_as_of = min(hyb_as_ofs) if hyb_as_ofs else None
    sub_as_of = min(sub_as_ofs) if sub_as_ofs else None
    if overflow > 0 and hyb_as_of:
        t2_as_of_candidates = [d for d in (sub_as_of, hyb_as_of) if d]
        t2_as_of = min(t2_as_of_candidates) if t2_as_of_candidates else None
    else:
        t2_as_of = sub_as_of
    return dict(scr=scr, t1lim=t1lim, t1lim_strict=t1lim_strict, t2lim=t2lim,
                new_hyb=round(new_hyb, 1), gf_hyb=round(gf_hyb, 1),
                new_sub_recog=round(new_sub_recog, 1), new_sub_gross=round(new_sub_gross, 1),
                gf_sub=round(gf_sub, 1), overflow=round(overflow, 1),
                t1_util=t1_util, t2_num=round(t2_num, 1), t2_util=t2_util, n=len(c["bonds"]),
                hyb_as_of=hyb_as_of, sub_as_of=t2_as_of)


# ---- update tier1 ----
shutil.copy2(T1F, str(T1F) + ".bak")
for r in t1doc["results"]:
    x = comp(r["code"])
    r["tier1_hybrid_limit_eok"] = x["t1lim"]
    r["tier1_hybrid_limit_strict_eok"] = x["t1lim_strict"]
    r["tier1_hybrid_issued_eok"] = x["new_hyb"]
    r["tier1_hybrid_recognized_eok"] = x["new_hyb"]
    r["tier1_hybrid_overflow_eok"] = x["overflow"]
    r["tier1_grandfathered_hybrid_eok"] = x["gf_hyb"]
    # 캡 없음 (owner 2026-06-14 결정, docs/changelog_designer.md:783-789 · designer 프롬프트 L177 LOCKED).
    # 분자=발행액(KOFIA/DART per-bond), 분모=인정한도(공시 SCR 기반) — 독립 소스라 >100% 가 정당하게
    # 나온다. 자르는 것은 **화면의 원호뿐**이고(K-ICS.html L833 Math.min(...,100)), 숫자는 생짜로
    # 넘겨 HTML 이 '100%+' + 툴팁 실제값(L841/L879)으로 표기한다. tier2(L140)와 같은 규약.
    r["utilization_pct"] = x["t1_util"]
    r["utilization_pct_raw"] = x["t1_util"]   # 하위호환 별칭(캡 제거 후 utilization_pct 와 항상 동일)
    r["utilization_pct_strict"] = round(x["new_hyb"] / x["t1lim_strict"] * 100, 1) if x["t1lim_strict"] else None
    # 분자(발행잔액) 기준일은 회사마다 다를 수 있다(2026-09-01 owner 티켓: 분모=2026.2Q인데
    # 분자가 2025.4Q 였던 사고) — 화면 라벨(quarter=denominator 기준)과 절대 혼동하지 말 것.
    r["numerator_as_of"] = x["hyb_as_of"]
    r["data_source"] = f"dart_bonds_asof_{x['hyb_as_of']}_경과조치" if x["hyb_as_of"] else "no_bonds"
    r["quality_flag"] = "ok"
t1doc["definition"] = {
    "limit_primary": "SCR×15% (KIRI 2024-14 common-transition)", "limit_strict": "SCR×10%",
    "numerator": "신종자본증권 신규(2023~) 발행 인정액; 경과조치(pre-2023)는 별도 제외",
    "source": f"DART per-bond ({BONDS_SOURCE_REL})",
    "as_of": AS_OF.isoformat(),
    "as_of_note": "as_of 는 분모(SCR·한도, item14 기준 분기말)의 기준일이다. 분자(발행잔액)의 "
                  "실제 기준일은 회사마다 다르며 각 결과행의 numerator_as_of 를 봐야 한다 — "
                  "분모와 같다고 가정하지 말 것."}
T1F.write_text(json.dumps(t1doc, ensure_ascii=False, indent=2), "utf-8")

# ---- update tier2 ----
shutil.copy2(T2F, str(T2F) + ".bak")
for r in t2doc["results"]:
    x = comp(r["code"])
    r["tier2_limit_eok"] = x["t2lim"]
    r["numerator_eok"] = x["t2_num"]
    r["utilization_pct"] = x["t2_util"]
    r["numerator_as_of"] = x["sub_as_of"]
    r["data_source"] = f"dart_bonds_asof_{x['sub_as_of']}_경과조치" if x["sub_as_of"] else "no_bonds"
    r["new_subordinated_recognized_eok"] = x["new_sub_recog"]
    r["new_subordinated_gross_eok"] = x["new_sub_gross"]
    r["tier1_overflow_into_tier2_eok"] = x["overflow"]
    r["grandfathered_hybrid_eok"] = x["gf_hyb"]
    r["grandfathered_subordinated_eok"] = x["gf_sub"]
    r["hybrid_eok"] = x["gf_hyb"]            # 면제분 (for legacy field)
    r["subordinated_eok"] = x["gf_sub"]
    r["quality_flag"] = "ok" if (x["t2_util"] is None or x["t2_util"] <= 100) else "util_over_100_legit"
t2doc["definition"] = {
    "limit": "SCR×50% (K-ICS 해설서 Ⅲ.2.마)",
    "numerator": "후순위 신규(2023~) 인정금액(잔존만기 to CALL straight-line) + 신종 한도초과분; 경과조치(pre-2023)는 별도 제외",
    "source": f"DART per-bond ({BONDS_SOURCE_REL})",
    "replaces": "broken proxy(item3 보완자본 − 면제) — 총보완자본 혼동(삼성생명 자본증권0인데 7.76조), 동양240%/KB218% artifact",
    "as_of": AS_OF.isoformat(),
    "as_of_note": "as_of 는 분모(SCR·한도, item14 기준 분기말)의 기준일이다. 분자(발행잔액)의 "
                  "실제 기준일은 회사마다 다르며 각 결과행의 numerator_as_of 를 봐야 한다 — "
                  "분모와 같다고 가정하지 말 것."}
T2F.write_text(json.dumps(t2doc, ensure_ascii=False, indent=2), "utf-8")

# ---- report ----
print(f"{'code':7}{'company':15}{'SCR':>8}{'신종new':>8}{'신종면제':>8}{'후순new인정':>11}{'후순면제':>8}{'T1초과':>7}{'T2분자':>8}{'T1소진':>7}{'T2소진':>7}")
for r in sorted(t2doc["results"], key=lambda r: -(comp(r['code'])['t2_num'] or 0)):
    x = comp(r["code"])
    if not x["n"]:
        continue
    print(f"{r['code']:7}{str(r['company'])[:14]:15}{(x['scr'] or 0):>8.0f}"
          f"{x['new_hyb']:>8.0f}{x['gf_hyb']:>8.0f}{x['new_sub_recog']:>11.0f}{x['gf_sub']:>8.0f}"
          f"{x['overflow']:>7.0f}{x['t2_num']:>8.0f}"
          f"{(str(x['t1_util'])+'%'):>7}{(str(x['t2_util'])+'%'):>7}")
overs = [r['company'] for r in t2doc['results'] if (comp(r['code'])['t2_util'] or 0) > 100]
print(f"\nTier2 소진율 >100% (YELLOW legit, not RED): {overs}")
print(f"[wrote] {T1F.relative_to(ROOT)} (.bak) + {T2F.relative_to(ROOT)} (.bak)")
