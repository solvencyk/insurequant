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
# KR0003 추가(2026-09-01): 열그룹 colspan 대소문자/폭, 금액 라벨(액면금액), 회차 표기(제N차)
# 세 가지 템플릿 가정 때문에 안 잡히고 있었다. 전기말 합계가 FY2025 기준선(806,732)을
# 그대로 재현해 **기준(장부금액)이 확정**됐고, 10개 트랜치 전량이 고아 없이 대조된다.
SUBORDINATED_REFRESH_CODES = {"KR0011", "KR0003"}

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


def extract_subordinated_current(text: str, period: str = "current"):
    """차입금 주석의 후순위사채 열그룹 표를 읽는다.

    `period="prior"` 는 같은 표의 **전기말** 판을 돌려준다 — 금액 행 라벨이 템플릿마다
    달라(`사채, 명목금액` / `액면금액` / `장부금액`) 어느 것이 우리 FY2025 기준과 같은
    개념인지 알 수 없기 때문이다. 전기말 합계를 FY2025 기준선에 대고 맞춰 보면 그 회사가
    쓰던 기준(액면이냐 장부냐)이 확정되고, 같은 행의 당반기말 값을 쓰면 **기준을 바꾸지 않고
    시점만 갱신**할 수 있다. 이 대조 없이 라벨을 골라 잡으면 롯데손해의 경우 장부 806,732 를
    액면 810,000 으로 조용히 바꿔치기하게 된다(개념 절단).
    """
    CUR = ("당반기말", "당분기말", "당기말", "당기")
    want = CUR if period == "current" else ("전기말", "전분기말", "전반기말", "전기")
    # 2026-09-01: colspan 을 **소문자 + 폭 3 고정**으로 찾고 있었다. DART XML 은 필러 템플릿마다
    # 속성 대소문자가 갈리고(KR0011 은 `colspan`, KR0003 은 `COLSPAN`), 열 폭은 그 회사의
    # 후순위사채 차수 개수다(롯데 = 제8~17차 = 10). 그래서 이 표를 가진 회사가 여럿인데
    # DB손해 하나만 매치됐다 — 템플릿이 하나뿐이라서가 아니라 정규식이 하나만 봤기 때문이다.
    for m in re.finditer(r"<TH[^>]*\bcolspan=['\"]\d+['\"][^>]*>\s*후순위사채\s*</TH>",
                         text, re.IGNORECASE):
        group_start = m.start()
        back = text[max(0, group_start - 3000):group_start]
        pm = list(re.finditer(r"(당반기말|당분기말|당기말|당기|전기말|전분기말|전반기말|전기)", back))
        if not pm or pm[-1].group(1) not in want:
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
        # 2026-09-01: 금액 행 라벨이 템플릿마다 다르다. KR0011 은 `사채, 명목금액`,
        # KR0003 은 `액면금액`(+`장부금액`). 하나만 보고 있어서 롯데 표는 헤더까지 읽어 놓고
        # 금액을 못 찾아 통째로 버려졌다. 셋 다 걷고 소비 측에서 우선순위로 고른다.
        for label in ("차입금, 발행일", "차입금, 만기", "차입금, 이자율",
                      "사채, 명목금액", "액면금액", "장부금액"):
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



def _issuance_rows(text: str):
    """반기보고서 표준 절 `[채무증권의 발행 등과 관련된 사항] 가. 채무증권 발행실적` 의 행.

    이 표는 **잔액 전량이 아니라 보고창(최근 사업연도들) 안의 발행실적**이고, 각 행이
    상환/미상환 상태를 달고 있다. 그래서 합계를 잔액으로 쓰면 안 되지만(창 밖 발행분이
    빠진다), **개별 채권이 기준일 현재 여전히 미상환인지 확인**하는 데는 정확하다.

    행 배열: [발행회사, 종류, 공모/사모, 발행일, 발행금액, 이자율, 등급, 만기일, 상환여부, 주관사]
    """
    out = []
    for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text, re.DOTALL):
        cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                 for t in re.findall(r">([^<]+)", tr.group(0))]
        cells = [c for c in cells if c]
        if len(cells) < 9 or "미상환" not in cells:
            continue
        kind = next((c for c in cells[:4] if "신종자본증권" in c), None)
        if not kind:
            continue
        issue = next((parse_kdate(c) for c in cells if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", c)), None)
        amt = next((float(c.replace(",", "")) for c in cells
                    if re.fullmatch(r"[\d,]+", c) and float(c.replace(",", "")) >= 100), None)
        if issue and amt:
            out.append({"issue_date": issue, "face_amount_mn": amt})
    return out


def _issuance_as_of(text: str):
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
    m = re.search(r"채무증권\s*발행실적[^가-힣]{0,80}?기준일[^0-9]{0,10}(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})", flat)
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None


def confirm_hybrids_still_outstanding(code, fy25_hybrid_bonds, report):
    """기존 신종자본증권이 기준일 현재 여전히 미상환인지 **확인만** 한다 — 값은 안 바꾼다.

    `자본으로 인정되는 채무증권의 발행` 개별 주석은 24개 제출사 중 9곳에만 있다. 나머지는
    FY2025 를 그대로 이월했는데, 그 결과 화면에 "발행잔액 기준일 2025-12-31" 이 반기 내내
    남았다(owner 지적, 2026-09-01). 그런데 표준 절 `채무증권 발행실적` 은 24곳 전부에 있고
    기준일이 2026-06-30 이다. 기존 채권이 (발행일, 발행금액) 으로 그 표에 **미상환**으로
    그대로 있으면, 값은 한 칸도 안 바꾸고 **시점만** 정직하게 갱신할 수 있다.

    전량 확인된 경우에만 기준일을 돌려준다. 한 건이라도 확인 못 하면 None — 부분 확인을
    전량 확인처럼 보이게 하지 않는다(company as_of 는 bond as_of 의 min 이라 조용히 최신으로
    보이게 만들 수 있다).
    """
    if not fy25_hybrid_bonds:
        return None, None
    xml_path, text = load_h1_xml(code)
    if text is None:
        return None, None
    as_of = _issuance_as_of(text)
    if not as_of:
        return None, None
    rows = _issuance_rows(text)
    unmatched = []
    for b in fy25_hybrid_bonds:
        hit = any(r["issue_date"] == b.get("issue_date")
                  and abs(r["face_amount_mn"] - (b.get("face_amount_mn") or -1)) < 1
                  for r in rows)
        if not hit:
            unmatched.append(b.get("name"))
    if unmatched:
        report.setdefault("hybrid_confirm_partial", {})[code] = unmatched
        return None, None
    return as_of, xml_path.relative_to(ROOT).as_posix()


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
    # 금액 행 라벨은 템플릿마다 다르다. **어느 것을 쓸지는 전기말 합계가 FY2025 기준선을
    # 재현하는지로 정한다** — 그래야 기준(액면/장부)을 바꾸지 않고 시점만 갱신한다.
    _, prior_rows = extract_subordinated_current(text, period="prior")
    fy25_total = sum(x.get("outstanding_mn") or 0 for x in fy25_sub_bonds)

    def _sum(vals):
        t = 0.0
        for v in vals or []:
            v = (v or "").replace(",", "").strip()
            if re.fullmatch(r"-?\d+(\.\d+)?", v):
                t += float(v)
        return t

    # 값 블록이 표 안에서 두 번 반복되는 템플릿이 있다(KR0011·KR0003 실측: 합계가 정확히 2배).
    # 기존 소비 코드가 `amounts[i] for i in range(len(names))` 로 **앞 N개만** 쓰므로,
    # 대조도 같은 슬라이스로 해야 한다. 전체를 더하면 어떤 라벨도 기준선과 안 맞는다.
    n = len(names or [])
    CANDIDATES = ("사채, 명목금액", "액면금액", "장부금액")
    amount_label = None
    if rows and prior_rows and fy25_total and n:
        for k in CANDIDATES:
            if rows.get(k) and prior_rows.get(k) and abs(_sum(prior_rows[k][:n]) - fy25_total) <= 1.0:
                amount_label = k
                break
    if amount_label is None:
        # 대조 실패 = 어떤 기준인지 모른다. 추측해서 갈아끼우지 않고 FY2025 를 유지한다.
        report.setdefault("sub_basis_unreconciled", {})[code] = {
            "fy2025_total_mn": fy25_total,
            "prior_sums": {k: _sum((prior_rows.get(k) or [])[:n]) for k in CANDIDATES
                           if prior_rows and prior_rows.get(k)},
        }
        report.setdefault("sub_extract_failed", []).append(code)
        return None
    if not names:
        report.setdefault("sub_extract_failed", []).append(code)
        return None
    amounts = rows[amount_label]
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
        # 2026-09-01: 짝짓기는 **발행일 우선**이다. 회차 표기가 `제3회`(KR0011) · `제 8차`(KR0003)
        # 로 갈릴 뿐 아니라, FY2025 이름이 `08차 무보증 후순위사채` 처럼 `제` 없이 시작하는
        # 사모 건이 있어 회차만 보면 10건 중 4건이 짝을 잃는다. 짝을 잃으면 `call_date` 가
        # 상속되지 않고 `발행일+5년` 으로 유도돼 **인정금액이 조용히 155억 움직였다**(실측).
        fy_match = None
        if iss:
            cands = [b for b in fy25_sub_bonds if b.get("issue_date") == iss]
            if len(cands) == 1:
                fy_match = cands[0]
        if fy_match is None:
            key_m2 = re.search(r"제?\s*[\d\-]+\s*[회차]", nm)
            key = re.sub(r"[제회차\s]", "", key_m2.group(0)) if key_m2 else None
            if key:
                for b in fy25_sub_bonds:
                    bk = re.search(r"제?\s*[\d\-]+\s*[회차]", b["name"])
                    if bk and re.sub(r"[제회차\s]", "", bk.group(0)) == key:
                        fy_match = b
                        break
        if fy_match is None:
            report.setdefault("sub_unmatched_bond", {}).setdefault(code, []).append(nm)
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
            # 대조로 고른 행이 `장부금액` 이면 그 값은 **잔액**이지 액면이 아니다.
            # 액면까지 덮어쓰면 90,000 이 89,863 이 되는 개념 절단이 된다 — FY2025 액면을 남긴다.
            "face_amount_mn": (base.get("face_amount_mn")
                               if amount_label == "장부금액" and base.get("face_amount_mn")
                               else (amt_mn or base.get("face_amount_mn"))),
            "outstanding_mn": amt_mn,
            "past_call_outstanding": base.get("past_call_outstanding", False),
            "as_of": H1_AS_OF,
            "source_file": src_rel,
        })
    _K = r"제\s*[\d\-]+\s*[회차]"
    def _norm(x):
        # `제 8차` 와 `제8회` 가 같은 채권을 가리킬 수 있어 차/회 를 지우고 번호로만 비교한다.
        return re.sub(r"[회차\s]", "", x)
    fy_keys = {_norm(re.search(_K, b["name"]).group(0))
               for b in fy25_sub_bonds if re.search(_K, b["name"])}
    h1_keys = {_norm(re.search(_K, n).group(0))
               for n in names if re.search(_K, n)}
    if fy_keys - h1_keys:
        report.setdefault("sub_orphans", {})[code] = sorted(fy_keys - h1_keys)
    return merged


def main():
    fy25 = json.loads(FY25_PATH.read_text(encoding="utf-8"))
    report = {}
    out_companies = []
    n_hybrid_refreshed = n_sub_refreshed = n_hybrid_confirmed = 0

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
            # 개별 주석이 없는 회사 — 값은 FY2025 그대로 두되, 표준 발행실적 표로 전량
            # '여전히 미상환' 이 확인되면 시점만 갱신한다(숫자 변경 없음).
            conf_as_of, conf_src = confirm_hybrids_still_outstanding(code, fy25_hybrid, report)
            if conf_as_of:
                fy25_hybrid = [dict(b, as_of=conf_as_of,
                                    source_file=f"{conf_src} (채무증권 발행실적: 미상환 확인, 금액 불변)")
                               for b in fy25_hybrid]
                n_hybrid_confirmed += 1
                notes_extra.append(f"HYBRID unchanged but confirmed still outstanding at {conf_as_of} "
                                   f"via 채무증권 발행실적 ({len(fy25_hybrid)} bond(s))")
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
    print(f"hybrid confirmed-unchanged (as_of only): {n_hybrid_confirmed} companies")
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
