# -*- coding: utf-8 -*-
"""Extract FY2026 H1 (반기보고서, as_of 2026-06-30) per-bond capital-securities data for the
target companies (companies that filed a 2026.2Q 반기보고서 AND had has_capital_securities=True
in the FY2025 baseline).

v2: flexible label matching (label may carry a trailing unit parenthetical like "(억원)"/
"(백만원)") + unit-aware amount parsing (억원 vs 백만원 vs bare 원). Validated first against
KR0011/KR0068/KR0072 (v1 clean matches) and KR0032 (v1 failure diagnosed: label was
"미상환잔액(억원)" with bare-number "4,500" value, not "...백만원" inline).

HYBRID (Tier1): "자본으로 인정되는 채무증권의 발행" section, sequential per-bond <TABLE> blocks.
SUBORDINATED (Tier2): "차입금" note's 후순위사채 column-group table (당반기말/당분기말/당기말
column set vs 전기말 comparative) — unchanged from v1, already validated against KR0011.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"

fy25 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2025.json").read_text(encoding="utf-8"))
FY25_BY_CODE = {c["code"]: c for c in fy25["companies"]}

census = json.loads((ROOT / "data" / "_derived" / "_probe_capsec_h1_census.json").read_text(encoding="utf-8"))
TARGET_CODES = [r["code"] for r in census if r["h1_filing_status"].startswith("FILED") and r["fy25_has_capsec"]]

TAG = r"T[A-Za-z]{1,2}"


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return s.replace("&nbsp;", " ").strip()


def cell_after_label(block: str, label: str):
    """Match a label cell (optionally with a trailing unit parenthetical, e.g. '미상환잔액(억원)')
    followed by the next cell's raw (tag-stripped) text. Returns (value_text, unit_hint)."""
    pat = re.compile(
        rf"<{TAG}[^>]*>\s*{re.escape(label)}\s*(?:\(([^)]{{0,10}})\))?\s*</{TAG}>\s*<{TAG}[^>]*>(.*?)</{TAG}>",
        re.DOTALL,
    )
    m = pat.search(block)
    if not m:
        return None, None
    return strip_tags(m.group(2)), m.group(1)


def parse_amount_mn(value_str, unit_hint=None):
    """Return an amount in 백만원 (mn), or None if genuinely unparseable (never guess)."""
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
    m = re.search(r"^(-?\d+(?:\.\d+)?)$", v)  # bare number — need unit_hint from the label
    if m:
        num = float(m.group(1))
        if unit_hint and "억" in unit_hint:
            return round(num * 100)
        if unit_hint and "백만" in unit_hint:
            return round(num)
        return None  # ambiguous — do not guess
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
    blocks = []
    misses_since_last_hit = 0
    n_scanned = 0
    for m in table_re.finditer(window):
        n_scanned += 1
        if n_scanned > 60:
            break
        block = m.group(0)
        issue_raw, _ = cell_after_label(block, "발행일")
        outstanding_raw, out_unit = cell_after_label(block, "미상환잔액")
        outstanding_mn = parse_amount_mn(outstanding_raw, out_unit)
        if issue_raw and outstanding_mn is not None:
            misses_since_last_hit = 0
            title_m = re.findall(r"<TH[^>]*>(.*?)</TH>", block, re.DOTALL)
            title = strip_tags(title_m[-1]) if title_m else None
            face_raw, face_unit = cell_after_label(block, "발행금액")
            coupon_raw, _ = cell_after_label(block, "발행금리")
            if coupon_raw is None:
                coupon_raw, _ = cell_after_label(block, "발행금리(금리상향조정조건)")
            maturity_raw, _ = cell_after_label(block, "만기 및 조기상환 가능일")
            if maturity_raw is None:
                maturity_raw, _ = cell_after_label(block, "만기일")
            # 농협 style: separate 만기 + 조기상환가능일 cells
            plain_maturity, _ = cell_after_label(block, "만기")
            call_only, _ = cell_after_label(block, "조기상환가능일")
            priority_raw, _ = cell_after_label(block, "우선순위")
            purpose_raw, _ = cell_after_label(block, "발행목적")
            legal_maturity = None
            call_date = None
            if maturity_raw:
                mm = re.search(r"만기일\s*[:：]?\s*([^가-힣]{0,20}[0-9][^가-힣]{0,20}일)", maturity_raw)
                legal_maturity = parse_kdate(mm.group(1)) if mm else parse_kdate(maturity_raw)
                rest = maturity_raw.replace(mm.group(1), "") if mm else maturity_raw
                dates_in_rest = re.findall(r"\d{4}[.\-\s년]\s*\d{1,2}[.\-\s월]\s*\d{1,2}\s*일?", rest)
                for d in dates_in_rest:
                    pd = parse_kdate(d)
                    if pd and pd != legal_maturity:
                        call_date = pd
                        break
            if legal_maturity is None and plain_maturity:
                legal_maturity = parse_kdate(plain_maturity)
            if call_date is None and call_only:
                call_date = parse_kdate(call_only)
            blocks.append({
                "title": title,
                "issue_date": parse_kdate(issue_raw),
                "issue_date_raw": issue_raw,
                "face_amount_mn": parse_amount_mn(face_raw, face_unit),
                "outstanding_mn": outstanding_mn,
                "coupon_pct": parse_pct(coupon_raw),
                "legal_maturity": legal_maturity,
                "call_date": call_date,
                "priority_raw": priority_raw,
                "purpose_raw": purpose_raw,
            })
        else:
            if blocks:
                misses_since_last_hit += 1
                if misses_since_last_hit >= 3:
                    break
    return blocks


def extract_subordinated_table(text: str):
    for m in re.finditer(r"<TH[^>]*colspan=['\"]3['\"][^>]*>\s*후순위사채\s*</TH>", text):
        group_start = m.start()
        back = text[max(0, group_start - 3000):group_start]
        period_matches = list(re.finditer(r"(당반기말|당분기말|당기말|당기|전기말|전분기말|전반기말|전기)", back))
        if not period_matches:
            continue
        period_label = period_matches[-1].group(1)
        if period_label not in ("당반기말", "당분기말", "당기말", "당기"):
            continue
        header_block_end = text.find("</THEAD>", group_start)
        if header_block_end == -1:
            continue
        header_block = text[group_start:header_block_end]
        name_ths = re.findall(r"<TH[^>]*>(.*?)</TH>", header_block, re.DOTALL)
        names = [strip_tags(t) for t in name_ths]
        names = [n for n in names if n and n != "후순위사채"]
        body_start = text.find("<TBODY>", header_block_end)
        body_end = text.find("</TBODY>", body_start)
        if body_start == -1 or body_end == -1:
            continue
        body = text[body_start:body_end]
        rows = {}
        for label in ("차입금, 발행일", "차입금, 만기", "차입금, 이자율", "사채, 명목금액"):
            row_m = re.search(
                rf"<T[DEH][^>]*>\s*{re.escape(label)}\s*</T[DEH]>((?:\s*<T[DEH][^>]*>.*?</T[DEH]>)+)",
                body, re.DOTALL)
            if not row_m:
                continue
            cells = re.findall(r"<T[DEH][^>]*>(.*?)</T[DEH]>", row_m.group(1), re.DOTALL)
            rows[label] = [strip_tags(c) for c in cells]
        return names, rows, period_label
    return None, None, None


report = {}
for code in TARGET_CODES:
    d = next((p for p in RAW_DIR.iterdir() if p.name.startswith(code + "_")), None)
    xml = next(d.glob("*.xml"), None) if d else None
    if xml is None:
        report[code] = {"error": "no xml"}
        continue
    text = xml.read_text(encoding="utf-8", errors="replace")

    hyb_start = text.find("자본으로 인정되는 채무증권")
    hybrid_blocks = extract_hybrid_blocks(text, hyb_start) if hyb_start != -1 else []

    names, rows, period_label = extract_subordinated_table(text)
    sub_bonds = []
    if names and rows.get("사채, 명목금액"):
        amounts = rows["사채, 명목금액"]
        issue_dates = rows.get("차입금, 발행일", [])
        maturities = rows.get("차입금, 만기", [])
        rates = rows.get("차입금, 이자율", [])
        for i, nm in enumerate(names):
            amt_raw = amounts[i] if i < len(amounts) else None
            amt_mn = None
            if amt_raw and re.match(r"^-?[\d,]+$", amt_raw.replace(" ", "")):
                amt_mn = parse_amount_mn(amt_raw + "백만원")
            iss_raw = issue_dates[i] if i < len(issue_dates) else None
            mat_raw = maturities[i] if i < len(maturities) else None
            rate_raw = rates[i] if i < len(rates) else None
            rate_pct = None
            if rate_raw:
                try:
                    rate_pct = round(float(rate_raw) * 100, 4)
                except ValueError:
                    rate_pct = None
            sub_bonds.append({
                "name": nm,
                "outstanding_mn": amt_mn,
                "outstanding_raw": amt_raw,
                "issue_date": parse_kdate(iss_raw) if iss_raw else None,
                "legal_maturity": parse_kdate(mat_raw) if mat_raw else None,
                "coupon_pct": rate_pct,
            })

    fy = FY25_BY_CODE.get(code, {})
    fy_hybrid = [b for b in fy.get("bonds", []) if b["tier"] == "hybrid"]
    fy_sub = [b for b in fy.get("bonds", []) if b["tier"] == "subordinated"]

    report[code] = {
        "company": fy.get("company"),
        "hybrid_h1": hybrid_blocks,
        "hybrid_h1_sum_mn": sum(b["outstanding_mn"] for b in hybrid_blocks if b["outstanding_mn"]),
        "hybrid_fy25_sum_mn": sum(b["outstanding_mn"] for b in fy_hybrid),
        "hybrid_fy25_n": len(fy_hybrid),
        "hybrid_h1_n": len(hybrid_blocks),
        "sub_h1": sub_bonds,
        "sub_h1_period_label": period_label,
        "sub_h1_sum_mn": sum(b["outstanding_mn"] for b in sub_bonds if b["outstanding_mn"]),
        "sub_fy25_sum_mn": sum(b["outstanding_mn"] for b in fy_sub),
        "sub_fy25_n": len(fy_sub),
        "sub_h1_n": len(sub_bonds),
    }

print(f"{'code':7}{'company':14}{'hyb_fy25':>10}{'hyb_h1':>10}{'n':>4}{'sub_fy25':>10}{'sub_h1':>10}{'n':>4}  sub_period")
for code, r in report.items():
    if "error" in r:
        print(f"{code:7}{'?':14} ERROR: {r['error']}")
        continue
    flag = ""
    if r["hybrid_h1_sum_mn"] != r["hybrid_fy25_sum_mn"]:
        flag += " HYB_DIFF"
    if r["sub_h1_sum_mn"] != r["sub_fy25_sum_mn"]:
        flag += " SUB_DIFF"
    if r["hybrid_h1_n"] == 0 and r["hybrid_fy25_n"] > 0:
        flag += " HYB_MISSING!"
    if r["sub_h1_n"] == 0 and r["sub_fy25_n"] > 0:
        flag += " SUB_MISSING!"
    print(f"{code:7}{str(r['company'])[:13]:14}{r['hybrid_fy25_sum_mn']:>10}{r['hybrid_h1_sum_mn']:>10}"
          f"{r['hybrid_h1_n']:>4}{r['sub_fy25_sum_mn']:>10}{r['sub_h1_sum_mn']:>10}{r['sub_h1_n']:>4}"
          f"  {r['sub_h1_period_label']}{flag}")

out = ROOT / "data" / "_derived" / "_probe_capsec_h1_extract.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n[wrote] {out.relative_to(ROOT)}")
