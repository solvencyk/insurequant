#!/usr/bin/env python3
"""DART standardized financial-statement API → PL Tier-1 (income statement) source.

Replaces the fragile HTML income-statement parsing.  DART's fnlttSinglAcntAll.json
returns the 포괄손익계산서 keyed by STANDARD account_id (ifrs-full_* / dart_*), so the
mapping is robust even though account_nm varies per insurer (보험손익 vs 보험서비스결과,
당기순이익 vs 반기순이익 vs 연결반기순이익).  Verified against the hand-built golds
(한화생명·KB·삼성·메리츠) — exact match via thstrm_add_amount(누적) for 반기/분기.

Owner directive (2026-06-04): use the FS API for Tier-1 fleet-wide.  Tier-2 (the IFRS17
decomposition: CSM상각/위험조정/예실차, 장기/자동차/일반) is footnote-only → stays hand-parsed.

corp_code is resolved by NAME at runtime (CORPCODE.xml), per the no-permanent-map rule.
Raw API JSON is cached under data/dart/_fs_api_cache/ (external network data)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402

CACHE = Path("data/dart/_fs_api_cache")
REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
# Basis (fs_div): the gold methodology is 별도(OFS) for the standalone insurer.  A few big
# groups headline 연결(CFS) because insurance/financial subsidiaries are material — those
# golds (삼성생명·메리츠) match CFS.  Default OFS; CFS only for the confirmed-연결 codes.
# NOTE: 삼성화재(KR0008) 연결→별도 on 2026-06-05 (owner: 별도 답지 2025.2Q; 연결은 해외 일반/자동차
# 자회사를 끌어와 LOB 분해를 왜곡 — 별도가 본체 보험손익 분해에 맞음).
BASIS_CFS = {"KR0069", "KR0001"}  # 삼성생명, 메리츠 (gold=연결)
# name-search aliases (Korean transliteration the substring search can't reach) — NOT a
# permanent KR↔corp map; just better search terms.
ALIAS = {"KB라이프생명": "케이비라이프생명보험", "IBK연금보험": "아이비케이연금보험"}

# Tier-1 item → exact standard account_id (포괄손익계산서, sj_div IS/CIS)
ACCT = {
    1: "ifrs-full_InsuranceServiceResult",                       # 보험손익/보험서비스결과
    17: "dart_InvestmentIncomeExpenses",                         # 투자손익
    20: "ifrs-full_ProfitLossFromOperatingActivities",           # 영업이익
    22: "ifrs-full_ProfitLossBeforeTax",                         # 세전이익
    23: "ifrs-full_IncomeTaxExpenseContinuingOperations",        # 법인세
    24: "ifrs-full_ProfitLoss",                                  # 당기순/반기순/분기순
    16: "dart_OtherOperatingExpenseInsurance",                   # 기타사업비용
}
# item19 (보험금융손익) = 보험금융수익 − 비용 + 재보험금융수익 − 비용.  Some insurers have no
# 보험금융수익 account (한화생명) → treat missing as 0 (per owner note).
FIN = {
    "ins_inc": "dart_InsuranceFinanceIncomeFromInsuranceContractsIssuedRecognisedInProfitOrLoss",
    "ins_exp": "dart_InsuranceFinanceExpensesFromInsuranceContractsIssuedRecognisedInProfitOrLoss",
    "re_inc": "dart_FinanceIncomeFromReinsuranceContractsHeldRecognisedInProfitOrLoss",
    "re_exp": "dart_FinanceExpensesFromReinsuranceContractsHeldRecognisedInProfitOrLoss",
}
NONOP_INC, NONOP_EXP = "dart_NonOperatingIncome", "dart_NonOperatingExpense"
# hidden keys for Tier-2 item3/8 derivation (보험수익/비용 grand totals), startswith-matched
IS_PREFIX = {
    "_is_rev": "ifrs-full_InsuranceRevenue",
    "_is_cost": "ifrs-full_InsuranceServiceExpenses",
    "_is_rerev": "ifrs-full_IncomeFromAmountsRecovered",
    "_is_recost": "ifrs-full_ExpensesFromAllocationOfPremiums",
}

_client = None
_corp_cache: dict[str, str | None] = {}


def _cl():
    global _client
    if _client is None:
        _client = OpenDARTClient.from_settings()
    return _client


def _to_num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def resolve_corp(name):
    """name → DART corp_code (runtime search, cached in-process).  None if not found."""
    if name in _corp_cache:
        return _corp_cache[name]
    queries = [ALIAS.get(name, name), name]
    if name.endswith("생명보험"):
        queries.append(name[:-2])     # 삼성생명보험→삼성생명
    if name.endswith("재보험"):
        queries.append(name[:-3])     # 코리안리재보험→코리안리
    cc = None
    for q in queries:
        try:
            hits = _cl().find_corp_codes_by_name(q)
        except Exception:
            hits = []
        if not hits:
            continue
        exact = [h for h in hits if h["corp_name"] in (q, name)]
        listed = [h for h in hits if h["stock_code"]]
        pick = exact or listed or hits
        cc = pick[0]["corp_code"]
        break
    _corp_cache[name] = cc
    return cc


def _fetch_raw(cc, year, reprt, fs_div):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{cc}_{year}_{reprt}_{fs_div}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    d = _cl()._get("/api/fnlttSinglAcntAll.json",
                   {"corp_code": cc, "bsns_year": str(year), "reprt_code": reprt,
                    "fs_div": fs_div}).json()
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _parse(d, annual):
    """Parse a fnlttSinglAcntAll response → Tier-1 dict, or None if no income statement."""
    if d.get("status") not in ("000", "013"):
        return None
    vals, is_vals, nm_vals = {}, {}, {}
    # 보험금융 P&L lines some insurers report with '-표준계정코드 미사용-' (no account_id) →
    # collect by NAME for fallback.  OCI uses a distinct name (보험계약자산부채순금융손익), so
    # these exact P&L names don't collide.
    _FIN_NM = ("보험금융수익", "보험금융비용", "재보험금융수익", "재보험금융비용", "보험금융손익")
    for a in d.get("list", []):
        if a.get("sj_div") not in ("IS", "CIS"):
            continue
        aid = a.get("account_id") or ""
        raw = a.get("thstrm_amount") if annual else \
            (a.get("thstrm_add_amount") or a.get("thstrm_amount"))
        v = _to_num(raw)
        if v is None:
            continue
        if aid and aid not in vals:
            vals[aid] = v / 1e6                       # 원 → 백만원
        nm = (a.get("account_nm") or "").replace(" ", "")
        if nm in _FIN_NM and nm not in nm_vals:
            nm_vals[nm] = v / 1e6
        for key, pref in IS_PREFIX.items():
            if aid.startswith(pref) and key not in is_vals:
                is_vals[key] = v / 1e6

    def g(aid):
        return vals.get(aid)

    t1 = {}
    for item, aid in ACCT.items():
        v = g(aid)
        if v is not None:
            t1[item] = round(v, 6)
    if 1 not in t1 and 24 not in t1:
        return None                                   # no income statement in this filing
    fi, fe = g(FIN["ins_inc"]), g(FIN["ins_exp"])
    ri, re = g(FIN["re_inc"]), g(FIN["re_exp"])
    # account_nm fallback for insurers whose 보험금융 lines carry no standard account_id
    # (e.g. KB라이프: 보험금융수익 161,082 − 보험금융비용 925,182 = −764,100).
    if fi is None:
        fi = nm_vals.get("보험금융수익")
    if fe is None:
        fe = nm_vals.get("보험금융비용")
    if ri is None:
        ri = nm_vals.get("재보험금융수익")
    if re is None:
        re = nm_vals.get("재보험금융비용")
    if any(x is not None for x in (fi, fe, ri, re)):
        t1[19] = round((fi or 0) - (fe or 0) + (ri or 0) - (re or 0), 6)
    elif nm_vals.get("보험금융손익") is not None:    # only the net line disclosed
        t1[19] = round(nm_vals["보험금융손익"], 6)
    # item17 (투자손익) gross/net consistency: dart_InvestmentIncomeExpenses is GROSS
    # 투자영업손익 for some insurers (영업이익 = 보험손익+투자손익+보험금융손익, e.g. KB라이프) but
    # already NET for others (영업이익 = 보험손익+투자손익, e.g. 한화생명).  When the FS-API 영업이익
    # confirms the gross form, fold 보험금융손익 in so 영업이익 = item1+item17 holds fleet-wide;
    # item18 (투자이익=gross) then derives as item17−item19.  Guarded: only when 1+17+19 closes
    # and 1+17 doesn't, so the already-net insurers are untouched.
    if None not in (t1.get(1), t1.get(17), t1.get(19), t1.get(20)):
        tol = max(0.01 * abs(t1[20]), 200)
        d_net = abs(t1[20] - (t1[1] + t1[17]))
        d_gross = abs(t1[20] - (t1[1] + t1[17] + t1[19]))
        if d_gross <= tol < d_net:
            t1[17] = round(t1[17] + t1[19], 6)        # gross → net
    # item21 (영업외손익): derive as 세전 − 영업이익 (both direct API accounts) so 22=20+21
    # closes exactly; the raw 영업외수익/비용 accounts can miss a sub-line (e.g. 롯데).
    if t1.get(22) is not None and t1.get(20) is not None:
        t1[21] = round(t1[22] - t1[20], 6)
    else:
        oi, oe = g(NONOP_INC), g(NONOP_EXP)
        if oi is not None or oe is not None:
            t1[21] = round((oi or 0) - (oe or 0), 6)
    t1.setdefault(15, 0.0)                            # 기타영업수익: API has no separate acct → 0
    if t1.get(17) is not None and t1.get(19) is not None:
        t1[18] = round(t1[17] - t1[19], 6)
    for k, v in is_vals.items():
        t1[k] = round(v, 6)
    return t1


def tier1_for(name, quarter, code=None):
    """Tier-1 dict (백만원) for one (company, quarter='YYYY.NQ'), or None.
    Basis = CFS for the few 연결-headline groups (BASIS_CFS), else OFS(별도); falls back to
    the other basis if the preferred one has no income statement.  Items 1,15-24 +
    hidden _is_rev/_is_cost/_is_rerev/_is_recost (for Tier-2 item3/8 derivation)."""
    cc = resolve_corp(name)
    if not cc:
        return None
    reprt = REPRT.get(quarter[5:])
    if not reprt:
        return None
    year, annual = quarter[:4], (quarter[5:] == "4Q")
    primary = "CFS" if (code in BASIS_CFS) else "OFS"
    for fs_div in (primary, "CFS" if primary == "OFS" else "OFS"):
        try:
            t1 = _parse(_fetch_raw(cc, year, reprt, fs_div), annual)
        except Exception:
            t1 = None
        if t1:
            return t1
    return None


if __name__ == "__main__":
    # smoke: validate against the golds
    import openpyxl
    GOLDS = [("삼성화재해상보험", "2025.4Q", "KR0008", "보험손익 breakdown_삼성화재.xlsx"),
             ("메리츠화재해상보험", "2025.4Q", "KR0001", "보험손익 breakdown_메리츠.xlsx"),
             ("삼성생명보험", "2025.4Q", "KR0069", "보험손익 breakdown_삼성생명.xlsx"),
             ("한화생명", "2025.4Q", "KR0068", "보험손익 breakdown_한화생명.xlsx"),
             ("한화생명", "2025.2Q", "KR0068", "보험손익 breakdown_한화생명_2025.2Q.xlsx"),
             ("KB손해보험", "2025.2Q", "KR0010", "보험손익 breakdown_KB.xlsx"),
             ("롯데손해보험", "2024.4Q", "KR0003", "보험손익 breakdown_롯데_2024.xlsx")]
    for nm, q, code, gx in GOLDS:
        wb = openpyxl.load_workbook(gx, data_only=True)
        ws = wb[wb.sheetnames[0]]
        gold = {}
        for row in ws.iter_rows(values_only=True):
            if row and isinstance(row[4], int):
                gold[row[4]] = row[7]
        t1 = tier1_for(nm, q, code) or {}
        line = []
        for it in (1, 17, 19, 20, 22, 23, 24):
            g, v = gold.get(it), t1.get(it)
            ok = g is not None and v is not None and abs(v - g) <= max(1, abs(g) * 0.01)
            line.append(f"{it}:{'OK' if ok else f'{v}vs{g}'}")
        print(f"{nm} {q}: " + "  ".join(line))
