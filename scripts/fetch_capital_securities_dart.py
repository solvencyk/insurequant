# -*- coding: utf-8 -*-
"""Fetch and parse DART 주요사항보고서(자본으로인정되는채무증권발행결정)
for KDB생명/농협생명/교보생명.

Output: data/bonds/disclosure/2026q1_capital_securities.json
Schema compatible with bonds_by_insurer.json (isin/issue_amount_won/effective_call_date/tier/status)
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402

# Known filings: (KR_code, corp_code, rcept_no, use_corrected)
# use_corrected=True means there's a 기재정정 so we use that one
FILINGS = [
    # KDB생명 (KR0072)
    ("KR0072", "케이디비생명보험", "00104069", "20241227000303"),  # 기재정정 of 2024 issue
    ("KR0072", "케이디비생명보험", "20230517000309"),              # 2023 issue
    # 농협생명 (KR0104)
    ("KR0104", "농협생명보험", "00909349", "20230130000405"),      # 기재정정 of 2022 issue
    ("KR0104", "농협생명보험", "20220831001673"),                  # 2022 issue (earlier)
    # 교보생명 (KR0073)
    ("KR0073", "교보생명보험", "00112882", "20231229000300"),      # 기재정정
    ("KR0073", "교보생명보험", "20230426000424"),                  # 2023 original
]

# Simplified: just use the rcept_nos we know
KNOWN_RCEPTIONS = [
    # KDB생명: 2024 issuance (기재정정이 확정치) + 2023 issuance
    ("KR0072", "케이디비생명보험", "00104069", "20241227000303"),
    ("KR0072", "케이디비생명보험", "00104069", "20230517000309"),
    # 농협생명: Aug 2022 (회차4) + Dec 2022
    ("KR0104", "농협생명보험",   "00909349", "20220831001673"),
    ("KR0104", "농협생명보험",   "00909349", "20221227000614"),
    # 교보생명 20231229 = 기재정정 showing 미발행 (not issued) → skip
]

# rcept_nos that contain "미발행" — skip these
SKIP_IF_NOT_ISSUED = {"20231229000300"}

WORK_DIR = REPO / "data" / "bonds" / "disclosure" / "raw_docs"
WORK_DIR.mkdir(parents=True, exist_ok=True)

client = OpenDARTClient.from_settings()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def find_value(text: str, label: str) -> str:
    """Find the value after a label in the document text."""
    idx = text.find(label)
    if idx == -1:
        return ""
    snippet = text[idx + len(label):idx + len(label) + 200]
    # Remove tags
    snippet = re.sub(r"<[^>]+>", " ", snippet)
    return clean(snippet)[:100]


def parse_date(s: str) -> str:
    """Convert various date formats to YYYY-MM-DD."""
    # Korean: 2023년 05월 19일
    m_kr = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", s)
    if m_kr:
        return f"{m_kr.group(1)}-{int(m_kr.group(2)):02d}-{int(m_kr.group(3)):02d}"
    # Dot/dash: 2052.09.28 or 2052-09-28
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def parse_amount_won(s: str) -> int | None:
    """Extract amount in won from string like '3,000억원' or '300,000,000,000원'."""
    s_clean = re.sub(r"[,\s]", "", s[:60])
    # 억원
    m = re.search(r"([\d.]+)억", s_clean)
    if m:
        return int(float(m.group(1)) * 100_000_000)
    # 백만원
    m2 = re.search(r"([\d]+)백만", s_clean)
    if m2:
        return int(m2.group(1)) * 1_000_000
    # 원 직접
    m3 = re.search(r"(\d{10,})", s_clean)
    if m3:
        return int(m3.group(1))
    return None


def parse_filing(kr_code: str, company: str, rcept_no: str, html_text: str) -> dict | None:
    """Extract bond details from 주요사항보고서 XML."""
    t = re.sub(r"<[^>]+>", " ", html_text)
    t = re.sub(r"\s+", " ", t)

    # Determine tier
    tier = "tier2_subordinated"
    if "신종자본" in t or "영구" in t or "하이브리드" in t:
        tier = "tier1_hybrid"

    # 권면총액 (primary amount field in 주요사항보고서)
    amount: int | None = None

    # For 기재정정 docs: look for "정정 후" value after the label
    # Pattern: "권면(전자등록)총액 (원)" followed by number
    m_total = re.search(r"권면\(전자등록\)총액\s*\(원\)\s*([\d,]+)", t)
    if m_total:
        amount = int(m_total.group(1).replace(",", ""))
    else:
        # Try plain number after 권면총액
        m2 = re.search(r"권면총액\s*([\d,]+)", t)
        if m2:
            amount = int(m2.group(1).replace(",", ""))

    # Fallback: Korean text amount (1조 N천억)
    if not amount:
        m3 = re.search(r"([\d]+)\s*조\s*([\d]+)\s*천\s*([\d]*)\s*백억", t)
        if m3:
            amount = (int(m3.group(1)) * 10000 + int(m3.group(2)) * 1000 +
                      int(m3.group(3) or 0) * 100) * 100_000_000
        else:
            m4 = re.search(r"([\d]+)\s*조\s*([\d]+)\s*[백천]억", t)
            if m4:
                amount = (int(m4.group(1)) * 10000 + int(m4.group(2)) * 100) * 100_000_000

    # 납입일 / 발행일 (납입일 is most reliable — it's the actual payment/issue date)
    issue_date = ""
    for label in ["납입일", "사채발행일"]:
        idx = t.find(label)
        if idx != -1:
            snippet = t[idx:idx + 60]
            d = parse_date(snippet)
            if d and "미정" not in snippet[:20]:
                issue_date = d
                break

    # 만기일 (skip if "미정")
    maturity_date = ""
    for label in ["사채만기일", "만기일(기간)"]:
        idx = t.find(label)
        if idx != -1:
            snippet = t[idx:idx + 60]
            if "미정" in snippet[:30]:
                break
            d = parse_date(snippet)
            if d:
                maturity_date = d
                break

    # 조기상환 / 콜옵션 일자
    call_date = ""
    for label in ["최초조기상환청구가능일", "콜옵션행사일", "최초조기상환일"]:
        idx = t.find(label)
        if idx != -1:
            snippet = t[idx:idx + 120]
            if "미정" in snippet[:30]:
                break
            d = parse_date(snippet)
            if d:
                call_date = d
                break
    # Fallback: if no explicit call date but issue_date known, use 5-year convention for 신종자본증권
    if not call_date and issue_date and tier == "tier1_hybrid":
        try:
            y, mo, day = issue_date.split("-")
            call_date = f"{int(y)+5}-{mo}-{day}"
        except Exception:
            pass

    is_perpetual = "영구" in t or (not maturity_date)

    if not amount:
        # Show context for debugging
        idx = t.find("권면")
        ctx = t[max(0, idx-10):idx+100] if idx != -1 else t[:200]
        print(f"  [WARN] {rcept_no}: amount not found. 권면 ctx: {ctx!r}")
        return None

    bond = {
        "isin": None,
        "name": f"{company} ({rcept_no[:8]})",
        "insurer_code": kr_code,
        "insurer_name": company,
        "tier": tier,
        "issue_date": issue_date,
        "issue_amount_won": amount,
        "maturity_date": maturity_date,
        "is_perpetual": is_perpetual,
        "effective_call_date": call_date or maturity_date,
        "next_deduction_date": call_date or maturity_date,
        "status": "outstanding",
        "source": f"dart_주요사항보고서_{rcept_no}",
    }
    return bond


results: dict[str, list[dict]] = {}

for kr_code, company, corp_code, rcept_no in KNOWN_RCEPTIONS:
    print(f"\nFetching {kr_code} {company} rcept={rcept_no} ...")
    zip_path = WORK_DIR / f"{rcept_no}.zip"

    if not zip_path.exists():
        try:
            client.fetch_document_xml(rcept_no, zip_path)
            print(f"  Downloaded → {zip_path.name}")
        except Exception as e:
            print(f"  ERROR downloading: {e}")
            continue
    else:
        print(f"  Cached: {zip_path.name}")

    # Extract HTML from zip
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            html_names = [n for n in names if n.lower().endswith((".htm", ".html", ".xml"))]
            if not html_names:
                print(f"  No HTML in zip: {names}")
                continue
            html_text = zf.read(html_names[0]).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  ERROR reading zip: {e}")
        continue

    if rcept_no in SKIP_IF_NOT_ISSUED:
        if "미발행" in html_text:
            print(f"  SKIP: 미발행 confirmed")
            continue

    bond = parse_filing(kr_code, company, rcept_no, html_text)
    if bond:
        results.setdefault(kr_code, []).append(bond)
        print(f"  OK: tier={bond['tier']} amount={bond['issue_amount_won']//100000000}억 "
              f"issue={bond['issue_date']} call={bond['effective_call_date']}")
    else:
        print(f"  PARSE FAILED for {rcept_no}")

# Dedupe by (amount, issue_date) — 기재정정 and original might be the same bond
deduped: dict[str, list[dict]] = {}
for kr, bonds in results.items():
    seen: set[tuple] = set()
    unique = []
    for b in bonds:
        key = (b["issue_amount_won"], b["issue_date"])
        if key not in seen:
            seen.add(key)
            unique.append(b)
    deduped[kr] = unique

# Build output
out_path = REPO / "data" / "bonds" / "disclosure" / "2026q1_capital_securities.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
payload = {
    "_meta": {
        "generated": stamp,
        "source": "dart_주요사항보고서(자본으로인정되는채무증권발행결정)",
        "note": "per-bond disclosure supplement for FSC-missing companies. "
                "FSC outstanding bonds for other companies remain in data/bonds/normalized/.",
    },
    "companies": {},
}
for kr, bonds in deduped.items():
    total_won = sum(b["issue_amount_won"] for b in bonds)
    payload["companies"][kr] = {
        "insurer_code": kr,
        "bonds_outstanding": len(bonds),
        "amount_outstanding_won": total_won,
        "bonds": bonds,
    }
    print(f"\n{kr}: {len(bonds)} bond(s), total {total_won//100000000}억")
    for b in bonds:
        print(f"  {b['tier']} {b['issue_amount_won']//100000000}억 issue={b['issue_date']} call={b['effective_call_date']}")

out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nWritten: {out_path}")
