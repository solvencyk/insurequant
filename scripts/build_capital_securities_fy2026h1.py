# -*- coding: utf-8 -*-
"""Build data/bonds/capital_securities_fy2026h1.json: per-company capital-securities bonds,
using FY2026 H1 (2026.2Q 반기보고서, as_of 2026-06-30) data where it could be extracted with
high confidence, and carrying forward FY2025 annual data (as_of 2025-12-31) everywhere else.

Why a MIXED-vintage file, not a pure "FY2026H1" one (owner ticket, 2026-09-01)
-------------------------------------------------------------------------------
`kics_tier{1,2}_utilization.json` labels the WHOLE numerator with the denominator's quarter-end
(as_of=2026-06-30), even though the numerator (bond issuance) actually came from FY2025 annual
filings (as_of 2025-12-31) — e.g. DB손보 tier1 showed 8,670억/50.2% sourced from Dec-2025, under
a "2026.2Q" label. Investigation (census over all 39 companies' FY2026_Q2 raw filings) found:
  - 14 companies never file a 반기보고서/분기보고서 at all (still-private subs, exempt under
    자본시장법) → FY2025 remains the only source, permanently, until their FY2026 사업보고서.
  - Of the 24 that filed, only 9 carry the itemized "자본으로 인정되는 채무증권의 발행" per-bond
    note (KR0011/32/68/70/71/72/94/99/104); the other 15 either lack capital securities (fy2025
    has_capital_securities=False) or only disclose an un-itemized maturity-bucket total.
  - Only 1 company (KR0011 DB손해보험) has a cleanly-parseable subordinated-bond refresh source
    (a "차입금" note 후순위사채 column-group table, 당반기말 vs 전기말) — this is NOT a shared
    XBRL template across insurers; the other 8 hybrid-refreshed companies' subordinated legs
    stay FY2025-sourced for now (open follow-up, see TODO_parser_kics.md).
  - DB손보 is not a cosmetic case: H1 2026 shows 3 NEW 신종자본증권 issuances (제3~5회, Feb/Jun
    2026, 442,000+410,000+30,000백만) and 제2회 무보증후순위사채(499,000백만) 조기상환(explicit
    footnote "당반기 중 조기상환하였습니다"). Serving the stale FY2025 numerator here would be
    materially wrong (50.2% vs a true tier1 utilization north of 100%), not just mislabeled.

So instead of pretending every company got a uniform refresh, this builder is explicit at the
PER-BOND level: every bond carries its own `as_of` + `source_file`, and every company's top-level
`as_of` = the MOST RECENT of its bonds' as_of (so a still-100%-fy2025 company stays honestly
2025-12-31, not silently bumped to look current).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_capital_securities_fy2026h1.py
      (writes data/bonds/capital_securities_fy2026h1.json; prints a per-company refresh report)
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"
FY25_PATH = ROOT / "data" / "bonds" / "capital_securities_fy2025.json"
OUT_PATH = ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json"

H1_AS_OF = "2026-06-30"

# Companies where the itemized hybrid (신종자본증권) section was found & cleanly parsed
# (validated manually against raw XML: KR0011/KR0068/KR0072 read in full; KR0032/71/99/104
# cross-checked bond-for-bond against the fy2025 baseline below before being trusted).
HYBRID_REFRESH_CODES = {"KR0011", "KR0032", "KR0068", "KR0070", "KR0071", "KR0072", "KR0094", "KR0099", "KR0104"}
# Company where the 차입금-note 후순위사채 column-group table was found & parsed (only one
# template variant recognized so far — see module docstring).
SUBORDINATED_REFRESH_CODES = {"KR0011"}

TAG = r"T[A-Za-z]{1,2}"


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&nbsp;", " ").strip()


def cell_after_label(block: str, label: str):
    pat = re.compile(
        rf"<{TAG}[^>]*>\s*{re.escape(label)}\s*(?:\(([^)]{{0,10}})\))?\s*</{TAG}>\s*<{TAG}[^>]*>(.*?)</{TAG}>",
        re.DOTALL,
    )
    m = pat.search(block)
    return (None, None) if not m else (strip_tags(m.group(2)), m.group(1))


def parse_amount_mn(value_str, unit_hint=None):
    if not value_str:
        return None
    v = value_str.replace(",", "").replace(" ", "").strip()
    if v in ("-", "", "－", "―", "해당없음", "해당사항없음"):
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)백만원", v)
    if m:
        return round(float(m.group(1)))
    m = re.search(r"(-?\d+(?:\.\d+)?)억원", v)
    if m:
        return round(float(m.group(1)) * 100)
    m = re.search(r"^(-?\d+(?:\.\d+)?)원$", v)
    if m:
        return round(float(m.group(1)) / 1_000_000)
    m = re.search(r"^(-?\d+(?:\.\d+)?)$", v)
    if m:
        num = float(m.group(1))
        if unit_hint and "억" in unit_hint:
            return round(num * 100)
        if unit_hint and "백만" in unit_hint:
            return round(num)
        return None
    return None


def parse_pct(s):
    if not s:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", s)
    return float(m.group(1)) if m else None


def parse_kdate(s):
    if not s:
        return None
    m = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", s)
    if m:
        return f"{int(m.group(1))}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", s)
    if m:
        return f"{int(m.group(1))}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def extract_hybrid_blocks(text: str, start_idx: int):
    table_re = re.compile(r"<TABLE\b.*?</TABLE>", re.DOTALL | re.IGNORECASE)
    window = text[start_idx:start_idx + 150_000]
    blocks, misses = [], 0
    for n_scanned, m in enumerate(table_re.finditer(window), 1):
        if n_scanned > 60:
            break
        block = m.group(0)
        issue_raw, _ = cell_after_label(block, "발행일")
        outstanding_raw, out_unit = cell_after_label(block, "미상환잔액")
        outstanding_mn = parse_amount_mn(outstanding_raw, out_unit)
        if issue_raw and outstanding_mn is not None:
            misses = 0
            face_raw, face_unit = cell_after_label(block, "발행금액")
            coupon_raw, _ = cell_after_label(block, "발행금리")
            if coupon_raw is None:
                coupon_raw, _ = cell_after_label(block, "발행금리(금리상향조정조건)")
            maturity_raw, _ = cell_after_label(block, "만기 및 조기상환 가능일")
            if maturity_raw is None:
                maturity_raw, _ = cell_after_label(block, "만기일")
            plain_maturity, _ = cell_after_label(block, "만기")
            call_only, _ = cell_after_label(block, "조기상환가능일")
            legal_maturity = call_date = None
            if maturity_raw:
                mm = re.search(r"만기일\s*[:：]?\s*([^가-힣]{0,20}[0-9][^가-힣]{0,20}일)", maturity_raw)
                legal_maturity = parse_kdate(mm.group(1)) if mm else parse_kdate(maturity_raw)
                rest = maturity_raw.replace(mm.group(1), "") if mm else maturity_raw
                for d in re.findall(r"\d{4}[.\-\s년]\s*\d{1,2}[.\-\s월]\s*\d{1,2}\s*일?", rest):
                    pd = parse_kdate(d)
                    if pd and pd != legal_maturity:
                        call_date = pd
                        break
            if legal_maturity is None and plain_maturity:
                legal_maturity = parse_kdate(plain_maturity)
            if call_date is None and call_only:
                call_date = parse_kdate(call_only)
            blocks.append({
                "issue_date": parse_kdate(issue_raw),
                "face_amount_mn": parse_amount_mn(face_raw, face_unit),
                "outstanding_mn": outstanding_mn,
                "coupon_pct": parse_pct(coupon_raw),
                "legal_maturity": legal_maturity,
                "call_date": call_date,
            })
        elif blocks:
            misses += 1
            if misses >= 3:
                break
    return blocks


def extract_subordinated_current(text: str):
    for m in re.finditer(r"<TH[^>]*colspan=['\"]3['\"][^>]*>\s*후순위사채\s*</TH>", text):
        group_start = m.start()
        back = text[max(0, group_start - 3000):group_start]
        pm = list(re.finditer(r"(당반기말|당분기말|당기말|당기|전기말|전분기말|전반기말|전기)", back))
        if not pm or pm[-1].group(1) not in ("당반기말", "당분기말", "당기말", "당기"):
            continue
        header_end = text.find("</THEAD>", group_start)
        if header_end == -1:
            continue
        header_block = text[group_start:header_end]
        names = [strip_tags(t) for t in re.findall(r"<TH[^>]*>(.*?)</TH>", header_block, re.DOTALL)]
        names = [n for n in names if n and n != "후순위사채"]
        body_start = text.find("<TBODY>", header_end)
        body_end = text.find("</TBODY>", body_start)
        if body_start == -1 or body_end == -1:
            continue
        body = text[body_start:body_end]
        rows = {}
        for label in ("차입금, 발행일", "차입금, 만기", "차입금, 이자율", "사채, 명목금액"):
            rm = re.search(
                rf"<T[DEH][^>]*>\s*{re.escape(label)}\s*</T[DEH]>((?:\s*<T[DEH][^>]*>.*?</T[DEH]>)+)",
                body, re.DOTALL)
            if rm:
                rows[label] = [strip_tags(c) for c in re.findall(r"<T[DEH][^>]*>(.*?)</T[DEH]>", rm.group(1), re.DOTALL)]
        return names, rows
    return None, None


def load_h1_xml(code):
    d = next((p for p in RAW_DIR.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    if xml is None:
        return None, None
    return xml, xml.read_text(encoding="utf-8", errors="replace")


def merge_hybrid(code, fy25_hybrid_bonds, report):
    xml_path, text = load_h1_xml(code)
    start = text.find("자본으로 인정되는 채무증권")
    h1_blocks = extract_hybrid_blocks(text, start)
    src_rel = xml_path.relative_to(ROOT).as_posix()

    remaining_fy25 = list(fy25_hybrid_bonds)
    merged, used_fy25_idx = [], set()
    for blk in h1_blocks:
        # match by (issue_date, face_amount) compound key first, fall back to issue_date if unique
        match_i = None
        cands = [i for i, b in enumerate(remaining_fy25)
                 if i not in used_fy25_idx and b["issue_date"] == blk["issue_date"]]
        if len(cands) == 1:
            match_i = cands[0]
        elif len(cands) > 1:
            exact = [i for i in cands if remaining_fy25[i]["face_amount_mn"] == blk["face_amount_mn"]]
            match_i = exact[0] if len(exact) == 1 else None
        if match_i is not None:
            used_fy25_idx.add(match_i)
            base = dict(remaining_fy25[match_i])
            merged.append({
                "name": base["name"],
                "tier": "hybrid",
                "issue_date": blk["issue_date"],
                "legal_maturity": blk["legal_maturity"] or base["legal_maturity"],
                "call_date": blk["call_date"] or base["call_date"],
                "call_source": "disclosed" if blk["call_date"] else base["call_source"],
                "coupon_pct": blk["coupon_pct"] if blk["coupon_pct"] is not None else base["coupon_pct"],
                "face_amount_mn": blk["face_amount_mn"] or base["face_amount_mn"],
                "outstanding_mn": blk["outstanding_mn"],
                "past_call_outstanding": base.get("past_call_outstanding", False),
                "as_of": H1_AS_OF,
                "source_file": src_rel,
            })
        else:
            merged.append({
                "name": f"{code} 신종자본증권 (발행 {blk['issue_date']}, H1 2026 신규확인)",
                "tier": "hybrid",
                "issue_date": blk["issue_date"],
                "legal_maturity": blk["legal_maturity"],
                "call_date": blk["call_date"],
                "call_source": "disclosed" if blk["call_date"] else None,
                "coupon_pct": blk["coupon_pct"],
                "face_amount_mn": blk["face_amount_mn"],
                "outstanding_mn": blk["outstanding_mn"],
                "past_call_outstanding": False,
                "as_of": H1_AS_OF,
                "source_file": src_rel,
                "notes": "H1 2026 신규 발행 확인 — FY2025 baseline에 대응 채권 없음(신규 발행으로 판단)",
            })
    # an fy2025 bond already recorded at outstanding_mn==0 (i.e. already fully redeemed as of
    # 2025-12-31, e.g. KR0094's 2025-08-12 조기상환) has nothing to match in H1's per-bond
    # table by construction (a zero-balance bond isn't listed) -- that's not a data-loss orphan;
    # carry it forward unchanged (contributes 0 either way, preserves the historical record).
    zero_bonds = [remaining_fy25[i] for i in range(len(remaining_fy25))
                  if i not in used_fy25_idx and not remaining_fy25[i].get("outstanding_mn")]
    orphans = [remaining_fy25[i] for i in range(len(remaining_fy25))
               if i not in used_fy25_idx and remaining_fy25[i].get("outstanding_mn")]
    clean = not orphans
    if orphans:
        report.setdefault("hybrid_orphans", {})[code] = [o["name"] for o in orphans]
    if clean:
        merged = merged + zero_bonds
    return merged, clean, src_rel


def merge_subordinated(code, fy25_sub_bonds, report):
    xml_path, text = load_h1_xml(code)
    names, rows = extract_subordinated_current(text)
    src_rel = xml_path.relative_to(ROOT).as_posix()
    if not names or not rows.get("사채, 명목금액"):
        report.setdefault("sub_extract_failed", []).append(code)
        return None
    amounts = rows["사채, 명목금액"]
    issue_dates = rows.get("차입금, 발행일", [])
    maturities = rows.get("차입금, 만기", [])
    rates = rows.get("차입금, 이자율", [])
    merged = []
    for i, nm in enumerate(names):
        amt_raw = amounts[i] if i < len(amounts) else None
        amt_mn = parse_amount_mn(amt_raw + "백만원") if amt_raw and re.match(r"^-?[\d,]+$", amt_raw.replace(" ", "")) else None
        iss = parse_kdate(issue_dates[i]) if i < len(issue_dates) and issue_dates[i] else None
        mat = parse_kdate(maturities[i]) if i < len(maturities) and maturities[i] else None
        rate_raw = rates[i] if i < len(rates) else None
        rate_pct = None
        if rate_raw:
            try:
                rate_pct = round(float(rate_raw) * 100, 4)
            except ValueError:
                pass
        # match against fy2025 by 회차 fragment inside the name (e.g. '제1-2회','제2회','제3회')
        key_m = re.search(r"제\s*[\d\-]+\s*회", nm)
        key = re.sub(r"\s+", "", key_m.group(0)) if key_m else None
        fy_match = None
        if key:
            for b in fy25_sub_bonds:
                if key in re.sub(r"\s+", "", b["name"]):
                    fy_match = b
                    break
        base = dict(fy_match) if fy_match else {}
        if amt_mn == 0:
            report.setdefault("sub_redeemed", {}).setdefault(code, []).append(nm)
            continue  # fully redeemed — drop from current bonds (matches K-ICS footnote evidence)
        merged.append({
            "name": base.get("name", nm),
            "tier": "subordinated",
            "issue_date": iss or base.get("issue_date"),
            "legal_maturity": mat or base.get("legal_maturity"),
            "call_date": base.get("call_date"),  # derived issue+5y methodology unchanged, inherit
            "call_source": base.get("call_source", "derived_issue_plus_5y"),
            "coupon_pct": rate_pct if rate_pct is not None else base.get("coupon_pct"),
            "face_amount_mn": amt_mn or base.get("face_amount_mn"),
            "outstanding_mn": amt_mn,
            "past_call_outstanding": base.get("past_call_outstanding", False),
            "as_of": H1_AS_OF,
            "source_file": src_rel,
        })
    fy_keys = {re.sub(r"\s+", "", re.search(r"제\s*[\d\-]+\s*회", b["name"]).group(0))
               for b in fy25_sub_bonds if re.search(r"제\s*[\d\-]+\s*회", b["name"])}
    h1_keys = {re.sub(r"\s+", "", re.search(r"제\s*[\d\-]+\s*회", n).group(0))
               for n in names if re.search(r"제\s*[\d\-]+\s*회", n)}
    if fy_keys - h1_keys:
        report.setdefault("sub_orphans", {})[code] = sorted(fy_keys - h1_keys)
    return merged


def main():
    fy25 = json.loads(FY25_PATH.read_text(encoding="utf-8"))
    report = {}
    out_companies = []
    n_hybrid_refreshed = n_sub_refreshed = 0

    for c in fy25["companies"]:
        code = c["code"]
        bonds = [dict(b, as_of=c["as_of"], source_file=c["source_file"]) for b in c.get("bonds", [])]
        fy25_hybrid = [b for b in bonds if b["tier"] == "hybrid"]
        fy25_sub = [b for b in bonds if b["tier"] == "subordinated"]
        new_bonds = []
        notes_extra = []

        if code in HYBRID_REFRESH_CODES:
            merged_hyb, clean, src = merge_hybrid(code, fy25_hybrid, report)
            if clean:
                new_bonds.extend(merged_hyb)
                n_hybrid_refreshed += 1
                notes_extra.append(f"HYBRID refreshed to H1 2026 ({src}), {len(merged_hyb)} bond(s)")
            else:
                new_bonds.extend(fy25_hybrid)  # unclean match -> stay conservative on fy2025
                notes_extra.append("HYBRID refresh attempted but left an unmatched FY2025 bond "
                                    "(orphan) -> kept FY2025 values for safety, see hybrid_orphans in report")
        else:
            new_bonds.extend(fy25_hybrid)

        if code in SUBORDINATED_REFRESH_CODES:
            merged_sub = merge_subordinated(code, fy25_sub, report)
            if merged_sub is not None:
                new_bonds.extend(merged_sub)
                n_sub_refreshed += 1
                notes_extra.append(f"SUBORDINATED refreshed to H1 2026, {len(merged_sub)} bond(s) "
                                    f"(1 redeemed bond confirmed & dropped, see sub_redeemed in report)")
            else:
                new_bonds.extend(fy25_sub)
        else:
            new_bonds.extend(fy25_sub)

        # MIN (oldest), not max: a company is only as fresh as its STALEST bond -- e.g. hybrid
        # refreshed to 2026-06-30 but subordinated still 2025-12-31 must show 2025-12-31 here,
        # never overstate freshness. Tier1/Tier2 each get their OWN as_of from the relevant bond
        # subset downstream in wire_capital_securities_to_utilization.py; this field is a
        # whole-company summary only.
        company_as_of = min((b.get("as_of", c["as_of"]) for b in new_bonds), default=c["as_of"])
        out_companies.append({
            "code": code,
            "company": c["company"],
            "as_of": company_as_of,
            "source_file": c["source_file"],  # legacy top-level field kept for schema compat;
                                               # per-bond source_file is now the authoritative one
            "has_capital_securities": c["has_capital_securities"],
            "bs_hybrid_mn": c.get("bs_hybrid_mn"),
            "bs_subordinated_mn": c.get("bs_subordinated_mn"),
            "total_hybrid_outstanding_mn": sum(b["outstanding_mn"] for b in new_bonds if b["tier"] == "hybrid" and b.get("outstanding_mn")),
            "total_subordinated_outstanding_mn": sum(b["outstanding_mn"] for b in new_bonds if b["tier"] == "subordinated" and b.get("outstanding_mn")),
            "confidence": c.get("confidence"),
            "bonds": new_bonds,
            "notes": (c.get("notes", "") + (" | " if c.get("notes") else "") + "; ".join(notes_extra))
                     if notes_extra else c.get("notes", ""),
        })

    out = {
        "as_of": "mixed (per-company; see each company's as_of + each bond's as_of/source_file)",
        "source": "FY2025 annual (data/bonds/capital_securities_fy2025.json) carried forward, "
                   "overridden per-company by FY2026 H1 반기보고서 (data/dart/FY2026_Q2/raw) where "
                   "cleanly extractable — see docstring of scripts/build_capital_securities_fy2026h1.py",
        "unit": "백만원 (mn)",
        "n_companies": len(out_companies),
        "companies": out_companies,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[wrote] {OUT_PATH.relative_to(ROOT)}  n_companies={len(out_companies)}")
    print(f"hybrid refreshed: {n_hybrid_refreshed}/{len(HYBRID_REFRESH_CODES)} target companies")
    print(f"subordinated refreshed: {n_sub_refreshed}/{len(SUBORDINATED_REFRESH_CODES)} target companies")
    if report:
        print("\n[report / anomalies]")
        print(json.dumps(report, ensure_ascii=False, indent=2))

    # integrity: never drop a company, never drop a bond silently vs fy2025 (except explicit
    # confirmed-redeemed subordinated bonds, logged above)
    fy25_n = len(fy25["companies"])
    assert len(out_companies) == fy25_n, f"company count changed: fy25={fy25_n} out={len(out_companies)}"
    for c25, cout in zip(fy25["companies"], out_companies):
        assert c25["code"] == cout["code"]
        n25 = len(c25.get("bonds", []))
        nout = len(cout["bonds"])
        redeemed = len(report.get("sub_redeemed", {}).get(c25["code"], []))
        if nout != n25 and (nout - n25) != -redeemed:
            # only new-issuance growth or explicit-redemption shrink is expected; anything else -> loud
            extra_new = sum(1 for b in cout["bonds"] if "H1 2026 신규확인" in b.get("name", ""))
            if nout - n25 != extra_new - redeemed:
                print(f"  [CHECK] {c25['code']}: bond count fy25={n25} -> out={nout} "
                      f"(new={extra_new}, redeemed={redeemed}) -- verify manually")
    print("\n[integrity] company count preserved; bond-count deltas explained by new-issuance/redemption only (see [CHECK] lines above, if any)")


if __name__ == "__main__":
    main()
