#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IFRS17 BS master (17BS 시트 스키마) -- Simplified high-level BS: assets / liabilities /
equity / AOCI / 법정준비금(해약환급금·비상위험·대손) only. Sole 17BS master since
2026-08-14 (owner archived the earlier equity_composition.json, items 1-49 -- "항목 ㅈㄴ
많은 것들"; see archive/2026-08_equity_composition/README.md).

Source = data/dart/_fs_api_cache/*.json (fetch_dart_fs.py's cache -- standard account_id
match, no new fetching logic) + data/dart/FY*/raw/*.xml (body-XML note fallback for items
5-7, and Tier-2's full BS for 15 non-listed insurers -- both via
build_equity_composition_tier2.py's parse_filing(), reused unchanged, name notwithstanding).
Units 백만원 (API is 원 -> /1e6). Basis: OFS(별도) by default -- owner 2026-08-14 P-1:
BASIS_CFS (삼성생명/메리츠) is a PL-only rule (그 gold 답지가 연결이라 만든 것); applying it
to BS made 삼성생명's 2025.2Q/3Q assets read as a stale-frozen CFS duplicate of 2025.1Q.
Narrow conditional CFS fallback added 2026-08-15 (owner+validation, Q-2): only when OFS's
items 1/2/3 are entirely absent (e.g. 한화손보 2026.2Q's OFS BS is a 4-row blank shell) --
see `extract_quarter()`. corp_code resolved by name at runtime.

Schema (10 columns, no 값_당분기 -- everything here is a stock/point-in-time item):
  원보험사코드 / 원수사명 / 티커 / 생손보여부 / 항목번호 / 항목명 / 섹션 / 레벨 / 공시분기 / 값
섹션 = 자산|부채|자본|준비금 (T자 레이아웃 그룹핑). 레벨 = 1(총계 타일: 1/2/3) | 2(그 외 전부,
드릴다운 세부-- AOCI·준비금 포함). Items 8/10+ (owner 2026-08-15, capped at ~15 lines total
across all three sections -- a curated highlight set, not an exhaustive account census; no
closure/residual accounting against 1/2/3 is attempted or expected). Item8(보증준비금)
added same-day as a 4th 법정준비금 type alongside 5/6/7.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_ifrs17_bs.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, REPRT  # reuse, not copy
from scripts.build_equity_composition_tier2 import TIER2, parse_filing  # reuse, not copy

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
DART = ROOT / "data" / "dart"
OUT = ROOT / "IFRS17_BS.json"
INV_REPRT = {v: k for k, v in REPRT.items()}  # "11013" -> "1Q"
# parse_filing()'s item numbers (its own BS+reserve-note schema) -> this master's 1-7
TIER2_ITEM_MAP = {40: 1, 41: 2, 1: 3, 6: 4, 10: 5, 12: 6, 14: 7}
# Same map, reused for the Tier-1 body-XML note fallback below (item 4/AOCI excluded --
# Tier-1's own FS-API face-of-BS is higher confidence and always tried first for that item).
NOTE_ITEM_MAP = {10: 5, 12: 6, 14: 7}

META = {}
for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    c = r.get("원보험사코드")
    if c and c not in META:
        META[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))

LABELS = {
    1: "자산총계", 2: "부채총계", 3: "자본총계",
    4: "기타포괄손익 누계액", 5: "해약환급금준비금적립액",
    6: "비상위험준비금 기말", 7: "대손준비금 적립액", 8: "보증준비금 기적립액",
    # BS 세부 하이라이트 (owner 2026-08-15: T자 레이아웃 드릴다운용, 전 계정 총망라 아니고
    # 최대 15줄 예산 -- 95개 distinct account_id census 후 재무상태표에서 가장 중요한 지표만
    # 선별, 자산/부채/자본 합쳐 13개). 항목번호는 섹션별 10/20/30대로만 구분, 빈 자리는 향후
    # 여유 -- 폐쇄검산 대상 아님(owner: 전수 분해가 아니라 하이라이트).
    10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
    12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산",
    14: "재보험계약자산", 15: "유형자산",
    20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 23: "차입부채",
    24: "기타부채",
    30: "자본금", 31: "이익잉여금",
}
# T자 레이아웃 그룹핑 (owner 2026-08-15 계약: designer는 항목번호를 하드코딩하지 않고 섹션·
# 레벨로만 그룹핑). 레벨: 1=총계 타일(1/2/3), 그 외 전부 2(드릴다운 세부, AOCI·준비금 포함).
# item8(보증준비금)도 준비금 -- 이익잉여금(31) 내부 적립이라 자본 L2 합에서 제외 그대로.
SECTION = {1: "자산", 2: "부채", 3: "자본", 4: "자본", 5: "준비금", 6: "준비금", 7: "준비금",
           8: "준비금",
           10: "자산", 11: "자산", 12: "자산", 13: "자산", 14: "자산", 15: "자산",
           20: "부채", 21: "부채", 22: "부채", 23: "부채", 24: "부채",
           30: "자본", 31: "자본"}


def _section_level(item: int) -> tuple[str, int]:
    return SECTION.get(item, "?"), (1 if item in (1, 2, 3) else 2)


# item4 (AOCI)'s dart_ 확장태그 fallback is handled separately in extract_quarter() --
# NOT listed here, since it must apply only when the standard tag is absent (see below).
ACCOUNT_IDS = {
    1: ("ifrs-full_Assets",),
    2: ("ifrs-full_Liabilities",),
    3: ("ifrs-full_Equity",),
    4: ("ifrs-full_AccumulatedOtherComprehensiveIncome",),
    5: ("dart_SurrenderValueReserve",),
    # 비상위험준비금, "가능하면" (owner P-5). 2026-08-15: dart_CatastropheReserve는 표준태그
    # 없는 회사 9곳이 대신 쓰는 배타적 대안 라벨(census 확인, ifrs-full_ 표준태그와 동시출현
    # 0건) -- item10 현금 대안 체인과 같은 안전한 패턴, 튜플에 같이 둔다.
    6: ("ifrs-full_ReserveForCatastrophe", "dart_CatastropheReserve"),
    7: ("dart_RegulatoryReserveForCreditLoss",),       # 대손준비금, "가능하면" (owner P-5)
    8: ("dart_GuranteeReserve",),   # 보증준비금, "가능하면" -- 2026-08-15 owner 추가 지시, 2사만 보유(교보생명·미래에셋생명)
    # BS 세부 하이라이트 -- 대안 태그는 회사마다 배타적으로 쓰여(census 확인, 동시출현 無)
    # 튜플에 같이 둬도 안전. item13(상각후원가측정금융자산)은 부모/자식 co-occurrence가
    # 회사마다 다른 유일한 케이스라 별도 처리(AMORTISED_COST_* 아래).
    10: ("ifrs-full_CashAndCashEquivalents", "dart_CashAndDuefromBanks",
         "dart_DueFromBanksAtAmortisedCost"),
    11: ("ifrs-full_FinancialAssetsAtFairValueThroughProfitOrLoss",),
    12: ("ifrs-full_FinancialAssetsAtFairValueThroughOtherComprehensiveIncome",),
    14: ("ifrs-full_ReinsuranceContractsHeldThatAreAssets",),
    15: ("ifrs-full_PropertyPlantAndEquipment",),
    20: ("ifrs-full_InsuranceContractsIssuedThatAreLiabilities",),
    21: ("ifrs-full_ReinsuranceContractsHeldThatAreLiabilities",),
    22: ("ifrs-full_InvestmentContractsLiabilities",),
    23: ("ifrs-full_Borrowings",),
    24: ("ifrs-full_OtherNonfinancialLiabilities",),
    30: ("ifrs-full_IssuedCapital",),
    31: ("ifrs-full_RetainedEarnings",),
}
ALL_ITEMS = tuple(sorted(LABELS))
# item13: 회사마다 부모(총계 태그)만 쓰거나, 자식 3종만 쓰거나, 둘 다 쓰되 일치하거나(진짜
# 부모-자식), 둘 다 쓰는데 액수가 안 맞는(census 2026-08-15: 24사 중 4사 -- KR0001/69/70/83)
# 경우까지 있어 "부모 있으면 무조건 부모 채택, 없을 때만 자식 합산" 규칙으로 통일 -- 이중계상
# 위험이 있는 방향(자식 우선)이 아니라 안전한 방향(부모 우선)으로 고정.
AMORTISED_COST_PARENT = "ifrs-full_FinancialAssetsAtAmortisedCost"
AMORTISED_COST_CHILDREN = ("dart_LoansAtAmortisedCost", "dart_SecuritiesAtAmortisedCost",
                           "dart_OtherFinancialAssetsAtAmortisedCost")
# item4 conditional fallback (owner 2026-08-14 P-2): 한화생명/흥국생명 등 일부 분기는 AOCI를
# 표준태그 대신 이 확장태그로 공시한다(태그만 갈아탄 것 -- 값이 0인 게 아니다, 라벨도 그대로
# "기타자본구성요소"). 채택 조건 = 같은 (회사,분기) BS에 표준태그가 아예 없을 때만(검증:
# 캐시 254건 전수 스캔 결과 표준+확장 동시존재 0건, 확장태그단독 13건 = 한화생명7+흥국생명6,
# 정확히 owner 목록과 일치). 무조건 매핑하면 다른 회사의 진짜 자본조정 계정을 AOCI로 오분류한다.
AOCI_FALLBACK_ID = "dart_ElementsOfOtherStockholdersEquity"


def _num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", "")) / 1e6
    except ValueError:
        return None


def _basis_data(cc: str, year: str, reprt: str, basis: str) -> list[dict]:
    p = CACHE / f"{cc}_{year}_{reprt}_{basis}.json"
    if not p.exists():
        return []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    if d.get("status") != "000":
        return []
    return d.get("list") or []


def _extract_from_list(lst: list[dict]) -> dict[int, float]:
    out = {}
    for item, ids in ACCOUNT_IDS.items():
        for a in lst:
            if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
                continue
            if a.get("account_id") in ids:
                v = _num(a.get("thstrm_amount"))
                if v is not None:
                    out[item] = v
                break
    if 4 not in out:
        for a in lst:
            if a.get("sj_div") == "BS" and a.get("account_detail") == "-" \
                    and a.get("account_id") == AOCI_FALLBACK_ID:
                v = _num(a.get("thstrm_amount"))
                if v is not None:
                    out[4] = v
                break
    # item13: parent tag wins whenever present (never double-count against children);
    # only sum the 3 children when the parent tag is absent entirely for this filer.
    by_id = {}
    for a in lst:
        if a.get("sj_div") == "BS" and a.get("account_detail") == "-":
            by_id.setdefault(a.get("account_id"), a)
    if AMORTISED_COST_PARENT in by_id:
        v = _num(by_id[AMORTISED_COST_PARENT].get("thstrm_amount"))
        if v is not None:
            out[13] = v
    else:
        vs = [_num(by_id[c].get("thstrm_amount")) for c in AMORTISED_COST_CHILDREN if c in by_id]
        vs = [v for v in vs if v is not None]
        if vs:
            out[13] = sum(vs)
    return out


def extract_quarter(cc: str, year: str, reprt: str) -> tuple[dict[int, float], str]:
    """BS series is OFS(별도) by default (owner 2026-08-14 P-1: BASIS_CFS is a PL-only
    rule). Conditional CFS fallback (owner 2026-08-15, validation Q-2,
    inbox/parser/20260815T0018Z): ONLY when OFS's core totals (items 1/2/3) are entirely
    absent -- not merely different, structurally missing, e.g. 한화손보 2026.2Q: OFS's BS
    section is a 4-row blank shell (무형자산/투자부동산/유형자산/사용권자산, all amounts
    blank), while CFS has the real 45-row filing. Narrowly scoped on purpose so this can't
    reopen the bug P-1 fixed (삼성생명's CFS returning a stale same-value duplicate across
    quarters while OFS was fine -- OFS has 1/2/3 there, so this fallback never triggers for
    that case). Returns (values, basis_used) -- caller logs which cells fell back, since this
    master has no provenance sidecar to persist it in."""
    out = _extract_from_list(_basis_data(cc, year, reprt, "OFS"))
    if not all(i in out for i in (1, 2, 3)):
        cfs_out = _extract_from_list(_basis_data(cc, year, reprt, "CFS"))
        if all(i in cfs_out for i in (1, 2, 3)):
            return cfs_out, "CFS"
    return out, "OFS"


def main():
    rows = []
    n_companies = 0
    census: dict[str, list[str]] = {}
    NAME_OVERRIDE = {"KR0029": "AIG"}  # "AIG손해보험" doesn't resolve; DART lists it as "AIG"
    for kr, (name, ticker, sb) in sorted(META.items()):
        cc = resolve_corp(NAME_OVERRIDE.get(kr, name))
        if not cc:
            census[kr] = ["resolve_corp failed"]
            continue
        files = sorted(CACHE.glob(f"{cc}_*_*_*.json"))
        if not files:
            census[kr] = ["no cache files at all"]
            continue
        periods = sorted({(f.stem.split("_")[1], f.stem.split("_")[2]) for f in files})
        got_any = False
        for year, reprt in periods:
            qlabel = INV_REPRT.get(reprt)
            if not qlabel:
                continue
            vals, basis = extract_quarter(cc, year, reprt)
            if not vals:
                continue
            if basis == "CFS":
                print(f"  CFS fallback: {kr} {year}.{qlabel} (OFS had no 자산/부채/자본)")
            got_any = True
            quarter = f"{year}.{qlabel}"
            for item in ALL_ITEMS:
                if item not in vals:
                    continue
                section, level = _section_level(item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": item, "항목명": LABELS[item], "섹션": section, "레벨": level,
                    "공시분기": quarter, "값": round(vals[item], 6),
                })
        if got_any:
            n_companies += 1
        else:
            census[kr] = [f"{len(periods)} periods in cache, none had usable BS rows"]

    # Tier-2 (15 non-listed, no XBRL FS): same body-XML note extractor, item-renumbered
    # onto this master's 1-7 schema via TIER2_ITEM_MAP.
    tier2_added = 0
    for kr, name in sorted(TIER2.items()):
        if kr not in META:
            continue
        _, ticker, sb = META[kr]
        for fy_dir in sorted(DART.glob("FY*_Q*")):
            m = fy_dir.name.replace("FY", "").split("_Q")
            quarter = f"{m[0]}.{m[1]}Q"
            dirs = sorted((fy_dir / "raw").glob(f"{kr}_*"))
            if not dirs:
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                continue
            try:
                vals, _diag = parse_filing(xmls[0])
            except Exception:
                continue
            for src_item, new_item in TIER2_ITEM_MAP.items():
                if src_item not in vals:
                    continue
                section, level = _section_level(new_item)
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                    "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                    "레벨": level, "공시분기": quarter, "값": round(vals[src_item], 6),
                })
                tier2_added += 1
        census.pop(kr, None)

    # Tier-1 reserve-notes fallback (owner P-5: 해약환급금준비금=정규, 비상위험·대손=
    # "가능하면"/pass). Same parse_filing() call Tier-2 already makes -- items 12/14 come
    # back in the same dict at zero extra cost when the table has them ("같은 표에서
    # 딸려 나오면 줍는 정도", not a reason to go fetch anything new). Only fills gaps in
    # what the FS-API cache already produced above; never overwrites a Tier-1 FS-API value.
    by_key: dict[tuple[str, str], set[int]] = {}
    for r in rows:
        by_key.setdefault((r["원보험사코드"], r["공시분기"]), set()).add(r["항목번호"])
    notes_added = 0
    for (kr, quarter), present in sorted(by_key.items()):
        if kr in TIER2 or kr not in META:
            continue
        wanted = {new for old, new in NOTE_ITEM_MAP.items() if new not in present}
        if not wanted:
            continue
        fy, qn = quarter.split(".")
        dirs = sorted((DART / f"FY{fy}_Q{qn[0]}" / "raw").glob(f"{kr}_*"))
        if not dirs:
            continue
        xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
        if not xmls:
            continue
        try:
            vals, _diag = parse_filing(xmls[0])
        except Exception:
            continue
        name, ticker, sb = META[kr]
        for old_item, new_item in NOTE_ITEM_MAP.items():
            if new_item not in wanted or old_item not in vals:
                continue
            section, level = _section_level(new_item)
            rows.append({
                "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "항목번호": new_item, "항목명": LABELS[new_item], "섹션": section,
                "레벨": level, "공시분기": quarter, "값": round(vals[old_item], 6),
            })
            notes_added += 1

    # Item 5 (해약환급금준비금 기적립액) roll-forward gap-fill (owner 2026-08-14, hand-verified
    # in insurequant_master_tables.xlsx before this landed): the reserve balance only moves
    # at the FY-end appropriation, so an interim quarter with no independent disclosure
    # carries the same balance as the FY's own most recent known figure, and a new FY's Q1
    # gap is last FY's Q4 balance plus that FY's own addition (item 11, 적립예정액 -- FY-
    # cumulative, captured at Q4; already sign-corrected in parse_filing() above for filers
    # who frame it as a net-income deduction). Never overrides a value already present from
    # the API tag or a direct note match above -- gap-fill only.
    additions: dict[tuple[str, int], float] = {}   # (kr, fy) -> that FY's item-11 total
    for kr in sorted(META):
        if kr in TIER2:
            continue
        for fy_dir in sorted(DART.glob("FY*_Q4")):
            fy = int(fy_dir.name.replace("FY", "").split("_Q")[0])
            dirs = sorted((fy_dir / "raw").glob(f"{kr}_*"))
            if not dirs:
                continue
            xmls = sorted(dirs[0].glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if not xmls:
                continue
            try:
                vals, _diag = parse_filing(xmls[0])
            except Exception:
                continue
            if 11 in vals:
                additions[(kr, fy)] = vals[11]

    quarters_by_co: dict[str, list[tuple[int, int]]] = {}
    for kr, quarter in by_key:
        y, qn = quarter.split(".")
        quarters_by_co.setdefault(kr, []).append((int(y), int(qn[0])))
    series: dict[str, dict[tuple[int, int], float]] = {}
    for r in rows:
        if r["항목번호"] == 5:
            y, qn = r["공시분기"].split(".")
            series.setdefault(r["원보험사코드"], {})[(int(y), int(qn[0]))] = r["값"]
    rollforward_added = 0
    for kr, qlist in sorted(quarters_by_co.items()):
        if kr in TIER2 or kr not in META:
            continue
        name, ticker, sb = META[kr]
        s = series.setdefault(kr, {})
        for (y, qn) in sorted(qlist):
            if (y, qn) in s:
                continue
            if qn > 1 and (y, qn - 1) in s:
                val = s[(y, qn - 1)]
            elif qn == 1 and (y - 1, 4) in s and (kr, y - 1) in additions:
                val = s[(y - 1, 4)] + additions[(kr, y - 1)]
            else:
                continue
            s[(y, qn)] = val
            section, level = _section_level(5)
            rows.append({
                "원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "항목번호": 5, "항목명": LABELS[5], "섹션": section, "레벨": level,
                "공시분기": f"{y}.{qn}Q", "값": round(val, 6),
            })
            rollforward_added += 1

    rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} rows ({tier2_added} Tier-2, {notes_added} Tier-1 notes, "
          f"{rollforward_added} item5 rollforward), "
          f"{n_companies}/{len(META)} Tier-1 companies + {len(TIER2)} Tier-2 companies")
    if census:
        print(f"  {len(census)} companies with NO usable data:")
        for kr, why in sorted(census.items()):
            print(f"    {kr} ({META[kr][0]}): {why[0]}")


if __name__ == "__main__":
    main()
