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
    """반기보고서 표준 절 `[채무증권의 발행 등과 관련된 사항] 채무증권 발행실적` 의 행.

    이 표는 **잔액 전량이 아니라 보고창 안의 발행실적**이고 각 행이 상환/미상환을 달고 있다.
    합계를 잔액으로 쓰면 안 되지만(창 밖 발행분이 빠진다), **개별 채권이 기준일 현재 여전히
    미상환인지 확인**하는 데는 정확하다.

    행 배열: [발행회사, 증권종류, 발행방법, 발행일자, 권면총액, 이자율, 평가등급, 만기일,
             상환여부, 주관회사]

    2026-09-01: 처음엔 `증권종류` 에 `신종자본증권` 이 든 행만 걷었는데, **후순위사채는 이
    컬럼에 `회사채` 로 찍힌다.** 그래서 후순위 확인이 전사 0/N 이었다. 종류로 거르지 않고
    전부 걷은 뒤 (발행일자, 권면총액) 으로 짝짓는다 — 날짜+금액 쌍은 충분히 강한 키다.
    """
    out = []
    for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text, re.DOTALL):
        cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                 for t in re.findall(r">([^<]+)", tr.group(0))]
        cells = [c for c in cells if c]
        if len(cells) < 8 or not any("미상환" in c for c in cells):
            continue
        di = next((i for i, c in enumerate(cells)
                   if re.fullmatch(r"\d{4}[.\-]\d{1,2}[.\-]\d{1,2}", c)), None)
        if di is None:
            continue
        issue = parse_kdate(cells[di].replace("-", "."))
        # 권면총액 = 발행일자 **다음** 의 첫 숫자. 아무 데서나 큰 수를 집으면 이자율·등급·
        # 만기일이 섞인다.
        amt = None
        for c in cells[di + 1:]:
            v = c.replace(",", "").strip()
            if re.fullmatch(r"\d+(\.\d+)?", v) and float(v) >= 100:
                amt = float(v)
                break
        if issue and amt:
            out.append({"issue_date": issue, "face_amount_mn": amt,
                        "kind": " ".join(cells[:4])})
    return out


def _issuance_as_of(text: str):
    """`채무증권 발행실적 … (기준일 : …)` 의 기준일.

    2026-09-01: 서식이 두 갈래다 — `2026년 06월 30일`(KR0011·KR0005) 과 `2026.06.30`
    (KR1000·KR0104). 게다가 제목과 기준일 사이에 `등(연결기준) (1) 채무증권 발행실적(연결기준)`
    처럼 한글이 끼는 회사가 있어, 종전 정규식(`[^가-힣]{0,80}`)이 **코리안리를 포함해 8개사에서
    기준일을 못 읽었다**. 못 읽으면 그 회사는 통째로 갱신 대상에서 빠져 화면에 옛 기준일이
    남는다(owner 지적 2026-09-01).
    """
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).replace("&nbsp;", " ")
    for m in re.finditer(r"채무증권\s*발행실적", flat):
        win = flat[m.start():m.start() + 260]
        d = re.search(r"기준일[^0-9]{0,12}(\d{4})\s*[년.]\s*(\d{1,2})\s*[월.]\s*(\d{1,2})", win)
        if d:
            return f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}"
    return None


def extract_subordinated_detail(text: str):
    """후순위사채 **상세표** 행 — 회사별 서식 차이를 뚫는 세 번째 경로.

    2026-09-01: 열그룹(`<TH colspan>후순위사채</TH>`) 서식은 KR0011·KR0003 둘뿐이다. 나머지
    회사들은 주석에 **행 단위 상세표**로 싣는다:

        [명칭, 발행일, 만기일, 이자율, 당반기말, 전기말, 상환방법]

        흥국생명  후순위무보증공모사채 2022년 09월 29일 2032년 09월 29일 6.20% 39,481 39,440 만기일시상환
        KDB생명   ...제10회 보증부후순위사채 2023-06-30 2033-06-30 4.76 72,056 71,121 ...

    두 숫자 열이 무엇인지(당반기말/전기말인지, 액면/장부인지)는 **읽어서 정하지 않는다** —
    호출측에서 `전기말 합계 == FY2025 기준선` 으로 대조해 확정한다. 이자율은 100 미만이라
    금액 필터에 안 걸린다.
    """
    rows = []
    for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text, re.DOTALL):
        cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                 for t in re.findall(r">([^<]+)", tr.group(0))]
        cells = [c for c in cells if c]
        if not any("후순위" in c for c in cells):
            continue
        dates = [(i, c) for i, c in enumerate(cells)
                 if re.fullmatch(r"\d{4}\s*[년.\-]\s*\d{1,2}\s*[월.\-]\s*\d{1,2}\s*일?", c)]
        if len(dates) < 2:
            continue
        nums = [(i, float(c.replace(",", "")))
                for i, c in enumerate(cells)
                if i > dates[-1][0] and re.fullmatch(r"[\d,]+", c) and float(c.replace(",", "")) >= 100]
        if len(nums) < 2:
            continue
        name = next((c for c in cells if "후순위" in c and not re.fullmatch(r"[\d,.]+", c)), cells[0])
        rows.append({
            "name": name,
            # parse_kdate 는 `2022년 09월 29일` 도 그대로 읽는다. 앞에서 손대면 `2022. 09. 29`
            # 처럼 공백이 낀 문자열이 돼 파싱이 실패하고, 그 행이 조용히 버려진다(실측).
            "issue_date": parse_kdate(dates[0][1].replace("-", ".")),
            "legal_maturity": parse_kdate(dates[1][1].replace("-", ".")),
            "col1": nums[0][1],
            "col2": nums[1][1],
        })
    # 같은 채권이 문서에 두 번 실린다 — 당반기말 표와 전기말 표에 각각(신한라이프 실측:
    # 300,000/299,710 과 300,000/299,636). **발행일 하나당 한 행**만 남기고 먼저 나온 것을
    # 취한다(당반기말 표가 앞에 온다). 둘 다 남기면 합계가 2배가 돼 대조가 영원히 실패한다.
    seen, out = set(), []
    for r in rows:
        if not r["issue_date"] or r["issue_date"] in seen:
            continue
        seen.add(r["issue_date"])
        out.append(r)
    return out


def merge_subordinated_detail(code, fy25_sub_bonds, report):
    """상세표에서 후순위 잔액을 갱신한다. **전기말 대조로 열 뜻을 확정한 뒤에만** 쓴다."""
    if not fy25_sub_bonds:
        return None
    xml_path, text = load_h1_xml(code)
    if text is None:
        return None
    rows = extract_subordinated_detail(text)
    if not rows:
        return None
    fy_by_date = {}
    for b in fy25_sub_bonds:
        fy_by_date.setdefault(b.get("issue_date"), []).append(b)
    matched = [r for r in rows if len(fy_by_date.get(r["issue_date"], [])) == 1]
    if len(matched) != len(fy25_sub_bonds):
        report.setdefault("sub_detail_incomplete", {})[code] = {
            "fy2025_bonds": len(fy25_sub_bonds), "matched_rows": len(matched)}
        return None
    fy_total = sum(b.get("outstanding_mn") or 0 for b in fy25_sub_bonds)
    for cur_key, prior_key in (("col1", "col2"), ("col2", "col1")):
        if abs(sum(r[prior_key] for r in matched) - fy_total) <= 1.0:
            break
    else:
        report.setdefault("sub_detail_unreconciled", {})[code] = {
            "fy2025_total_mn": fy_total,
            "col1_sum": sum(r["col1"] for r in matched),
            "col2_sum": sum(r["col2"] for r in matched)}
        return None
    src_rel = xml_path.relative_to(ROOT).as_posix()
    merged = []
    for r in matched:
        base = fy_by_date[r["issue_date"]][0]
        merged.append(dict(base,
                           outstanding_mn=r[cur_key],
                           legal_maturity=r["legal_maturity"] or base.get("legal_maturity"),
                           as_of=H1_AS_OF,
                           source_file=f"{src_rel} (후순위 상세표 {cur_key}, 전기말 대조 확인)"))
    return merged


def _bond_manager_rows(text: str):
    """`사채관리계약 현황` 표의 행 — 두 번째 미상환 근거원.

    2026-09-01: `채무증권 발행실적` 만 보면 현대해상·KB손해·NH농협손해 등은 0행이 나온다.
    그 회사들의 후순위사채는 대신 **사채관리계약 현황**(`작성기준일 : 2026년 06월 30일`,
    열 = 채권명·발행일·만기일·발행액·사채관리계약체결일·사채관리회사)에 실려 있다.
    이 표는 계약이 살아 있는 **미상환 공모사채**만 싣기 때문에, 그 기준일 현재 등재되어
    있다는 사실 자체가 미상환의 증거다. 사모사채는 사채관리회사가 없어 여기 안 나온다 —
    그래서 발행실적 표와 **합집합**으로 쓴다(둘 다 부분 커버리지다).
    """
    out = []
    for m in re.finditer(r"사채관리", text):
        #  라는 말은 표 **헤더 안**에 있다(열 이름 '사채관리 계약체결일').
        # 앞으로 찾으면 엉뚱하게 다음 표를 잡는다 — 뒤로 찾아 그 표를 연다.
        tstart = text.rfind("<TABLE", 0, m.start())
        if tstart == -1 or m.start() - tstart > 4000:
            continue
        tend = text.find("</TABLE>", tstart)
        if tend == -1:
            continue
        for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text[tstart:tend], re.DOTALL):
            cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                     for t in re.findall(r">([^<]+)", tr.group(0))]
            cells = [c for c in cells if c]
            di = next((i for i, c in enumerate(cells)
                       if re.fullmatch(r"\d{4}[.\-]\d{1,2}[.\-]\d{1,2}", c)), None)
            if di is None:
                continue
            issue = parse_kdate(cells[di].replace("-", "."))
            amt = None
            for c in cells[di + 1:]:
                v = c.replace(",", "").strip()
                if re.fullmatch(r"\d+(\.\d+)?", v) and float(v) >= 100:
                    amt = float(v)
                    break
            if issue and amt:
                out.append({"issue_date": issue, "face_amount_mn": amt,
                            "kind": cells[0][:60]})
    return out


def _bond_manager_as_of(text: str):
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).replace("&nbsp;", " ")
    for m in re.finditer(r"사채관리", flat):
        # 작성기준일은 헤더의  **앞**에 온다. 양쪽으로 창을 연다.
        win = flat[max(0, m.start() - 400):m.start() + 400]
        d = re.search(r"작성기준일[^0-9]{0,12}(\d{4})\s*[년.]\s*(\d{1,2})\s*[월.]\s*(\d{1,2})", win)
        if d:
            return f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}"
    return None


_DATEISH = re.compile(r"\d{4}[.\-]\d{2}")
_HYB_LAB = re.compile(r"^[\dIVXⅠ-Ⅹ.\s\[\]]*신종자본증권[\]\s]*$")
_SUB_LAB = re.compile(r"^[\dIVXⅠ-Ⅹ.\s\[\]]*(사채|차입부채|후순위사채|후순위채권)[\]\s]*(\(주[\d,\s]+\))?$")


def bs_current_balance(text: str, fy25_bs_mn, kind: str):
    """재무상태표 총액의 **당반기말** 값. 행 선택은 `전기말 == FY2025 BS` 로 자체 검증한다.

    2026-09-01: 라벨을 조이지 않으면 자본변동표의 `2025.01.01 (기초자본)` 같은 행이 우연히
    같은 값을 갖고 걸린다(실측 4건). 날짜형 라벨은 배제하고 BS 계정명만 받는다.
    후순위 총액은 회사마다 `사채` · `차입부채` · `후순위채권` 으로 라벨이 갈린다.
    """
    if not fy25_bs_mn:
        return None
    labre = _HYB_LAB if kind == "hybrid" else _SUB_LAB
    tol = max(1.0, abs(fy25_bs_mn) * 2e-6)
    hits = []
    for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text, re.DOTALL):
        cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                 for t in re.findall(r">([^<]+)", tr.group(0))]
        cells = [c for c in cells if c]
        if len(cells) < 3:
            continue
        lab = cells[0]
        if _DATEISH.search(lab) or not labre.match(lab):
            continue
        nums = []
        for c in cells[1:]:
            v = c.replace(",", "").strip()
            if re.fullmatch(r"\d+(\.\d+)?", v):
                n = float(v)
                nums.append(n / 1e6 if n >= 1e9 else n)
        if len(nums) >= 2 and abs(nums[1] - fy25_bs_mn) <= tol:
            hits.append(round(nums[0], 0))
    if not hits:
        return None
    from collections import Counter
    return Counter(hits).most_common(1)[0][0]


def detect_redeemed(code, fy25_sub_bonds, bs_prior_mn, report):
    """반기 중 **상환된** 후순위채를 찾는다. 잠금 두 개를 모두 통과해야 인정한다.

    ① 그 채권이 H1 반기보고서의 **어느 증거원에도 없다**
       (채무증권 발행실적 · 사채관리계약 현황 · 후순위 상세표)
    ② 그것을 뺀 나머지 합이 **BS 당반기말 총액을 재현한다**(0.5% 이내)

    ①만으로는 안 된다 — 세 표 다 부분 커버리지라 사모채는 원래 안 나온다. ②만으로도 안 된다 —
    잔액 차이는 상각·환율로도 난다. 둘이 같은 채권을 가리킬 때만 상환으로 판정한다.

    2026-09-01 owner 지적으로 발견: KB손해 제1회(3,790억) · 미래에셋 제2회(3,000억) ·
    현대해상 제3회(3,500억) · KB라이프 제1회(1,300억) 가 반기 중 상환됐는데 마스터가 계속
    계상하고 있었다. 보완자본 소진율 분자가 그만큼 부풀어 있었다.
    """
    if not fy25_sub_bonds or not bs_prior_mn:
        return None
    xml_path, text = load_h1_xml(code)
    if text is None:
        return None
    cur = bs_current_balance(text, bs_prior_mn, "subordinated")
    if cur is None:
        return None
    evidence = {r["issue_date"] for r in
                (_issuance_rows(text) + _bond_manager_rows(text) + extract_subordinated_detail(text))}
    absent = [b for b in fy25_sub_bonds if b.get("issue_date") not in evidence]
    if not absent:
        return None
    # 증거원은 셋 다 **부분 커버리지**라(사모채는 원래 안 나온다) '증거에 없다' 가 곧 상환은
    # 아니다. 그래서 증거 없는 채권들의 **부분집합**을 전부 시험해, BS 당반기말을 재현하는
    # 조합이 **정확히 하나**일 때만 채택한다. 둘 이상이면 어느 것이 상환됐는지 알 수 없으므로
    # 채택하지 않는다 — 추측으로 채권을 지우면 소진율 분자가 조용히 틀린다.
    # (현대해상 실측: 증거 없는 3건 중 실제 상환은 1건 = 무보증후순위사채3.)
    total = sum((b.get("outstanding_mn") or 0) for b in fy25_sub_bonds)
    tol = max(1.0, cur * 0.005)
    solutions = []
    n = len(absent)
    if n > 12:
        return None
    for mask in range(1, 1 << n):
        drop = [absent[i] for i in range(n) if mask & (1 << i)]
        if abs(total - sum((b.get("outstanding_mn") or 0) for b in drop) - cur) <= tol:
            solutions.append(drop)
    if len(solutions) != 1:
        report.setdefault("redeem_candidate_unreconciled", {})[code] = {
            "bs_current_mn": cur, "fy2025_total_mn": total,
            "absent": [b.get("name") for b in absent],
            "reconciling_subsets": len(solutions)}
        return None
    absent = solutions[0]
    kept = [b for b in fy25_sub_bonds if b not in absent]
    report.setdefault("sub_redeemed_detected", {})[code] = [
        {"name": b.get("name"), "issue_date": b.get("issue_date"),
         "outstanding_mn": b.get("outstanding_mn")} for b in absent]
    src = xml_path.relative_to(ROOT).as_posix()
    return [dict(b, as_of=H1_AS_OF,
                 source_file=f"{src} (H1 전 증거원 부재 + BS 당반기말 {cur:,.0f} 재현으로 잔존 확인)")
            for b in kept]


def confirm_aggregate_unchanged(text: str, fy25_bs_mn, keyword: str):
    """재무상태표 **총액**으로 "이 스택은 반기 동안 안 변했다" 를 확인한다 (네 번째 경로).

    2026-09-01: 채권 단위 표(발행실적·사채관리계약·상세표) 어느 것도 못 뚫는 회사가 남는다.
    그런데 그 회사들도 BS 에는 `신종자본증권` / `후순위사채` 총액을 당반기말·전기말 두 열로
    싣는다. **전기말 값이 우리 FY2025 BS 값을 그대로 재현하면** 그 행이 맞는 행이라는 것이
    자체 검증되고, 당반기말이 전기말과 같으면 그 스택은 반기 동안 변하지 않았다는 뜻이다.
    변하지 않았으면 값은 그대로 두고 **시점만** 정직하게 옮길 수 있다.

    당반기말 != 전기말 이면 뭔가 발행·상환된 것이므로 확인하지 않는다(채권 단위 경로 필요).
    단위가 원인 표(179,195,320,000)와 백만인 표(179,195)가 섞여 있어 둘 다 본다.
    """
    if not fy25_bs_mn:
        return None
    tol = max(1.0, abs(fy25_bs_mn) * 1e-6)
    for tr in re.finditer(r"<TR[^>]*>.*?(?=<TR[^>]*>|</TABLE>)", text, re.DOTALL):
        cells = [re.sub(r"\s+", " ", t).replace("&nbsp;", " ").strip()
                 for t in re.findall(r">([^<]+)", tr.group(0))]
        cells = [c for c in cells if c]
        if not cells or keyword not in cells[0] or len(cells[0]) > 20:
            continue
        nums = []
        for c in cells[1:]:
            v = c.replace(",", "").strip()
            if re.fullmatch(r"\d+", v):
                n = float(v)
                nums.append(n / 1_000_000 if n >= 1e9 else n)
        if len(nums) < 2:
            continue
        # 전기말 = 두 번째 열이 관행이지만, 열 순서가 뒤집힌 표도 있어 둘 다 시험한다.
        for cur, prior in ((nums[0], nums[1]), (nums[1], nums[0])):
            if abs(prior - fy25_bs_mn) <= tol and abs(cur - prior) <= tol:
                return H1_AS_OF
    return None


def confirm_bonds_still_outstanding(code, fy25_bonds, report, tier_label):
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
    if not fy25_bonds:
        return None, None
    xml_path, text = load_h1_xml(code)
    if text is None:
        return None, None
    # 근거원 둘의 합집합. 어느 하나도 전량을 담지 못한다(발행실적 = 보고창 안 발행분,
    # 사채관리계약 = 공모 only). 기준일은 둘 중 실제로 근거를 준 쪽에서 가져온다.
    rows = _issuance_rows(text)
    mgr_rows = _bond_manager_rows(text)
    as_of = _issuance_as_of(text) or _bond_manager_as_of(text)
    mgr_as_of = _bond_manager_as_of(text) or as_of
    if not as_of and not mgr_as_of:
        return None, None
    rows = rows + mgr_rows
    as_of = as_of or mgr_as_of
    unmatched = []
    for b in fy25_bonds:
        hit = any(r["issue_date"] == b.get("issue_date")
                  and abs(r["face_amount_mn"] - (b.get("face_amount_mn") or -1)) < 1
                  for r in rows)
        # 이 표가 보증하는 것은 **권면(액면)총액**이다. 우리가 싣는 `outstanding_mn` 이
        # 액면과 다르면(상각된 장부금액) 그 값까지 새 기준일로 보증되지는 않는다 —
        # 시점만 옮기면 "확인했다" 는 거짓 진술이 된다.
        if hit and (b.get("outstanding_mn") is not None
                    and abs((b.get("outstanding_mn") or 0) - (b.get("face_amount_mn") or 0)) >= 1):
            hit = False
            b = dict(b, name=f"{b.get('name')} (장부≠액면, 액면만 확인됨)")
        if not hit:
            unmatched.append(b.get("name"))
    if unmatched:
        report.setdefault(f"{tier_label}_confirm_partial", {})[code] = unmatched
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
    n_hybrid_refreshed = n_sub_refreshed = n_hybrid_confirmed = n_sub_confirmed = n_sub_detail = n_sub_redeem = 0

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
            conf_as_of, conf_src = confirm_bonds_still_outstanding(code, fy25_hybrid, report, "hybrid")
            if not conf_as_of:
                xml_p, _txt = load_h1_xml(code)
                agg = (confirm_aggregate_unchanged(_txt, c.get("bs_hybrid_mn"), "신종자본증권")
                       if _txt else None)
                if agg:
                    conf_as_of = agg
                    conf_src = f"{xml_p.relative_to(ROOT).as_posix()} (BS 신종자본증권 총액 당반기말==전기말==FY2025)"
                    report.setdefault("hybrid_confirm_by_aggregate", []).append(code)
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
            red = detect_redeemed(code, fy25_sub, c.get("bs_subordinated_mn"), report)
            if red is not None:
                new_bonds.extend(red)
                n_sub_redeem += 1
                notes_extra.append(f"SUBORDINATED: 반기 중 상환 {len(fy25_sub) - len(red)}건 제거 "
                                   f"(H1 증거 부재 + BS 당반기말 재현 이중확인)")
                fy25_sub = []
            det = merge_subordinated_detail(code, fy25_sub, report) if fy25_sub else None
            if det is not None:
                new_bonds.extend(det)
                n_sub_detail += 1
                notes_extra.append(f"SUBORDINATED refreshed from 상세표 to H1 2026, {len(det)} bond(s)")
                fy25_sub = []
            conf_as_of, conf_src = (confirm_bonds_still_outstanding(code, fy25_sub, report, "sub")
                                    if fy25_sub else (None, None))
            if fy25_sub and not conf_as_of:
                xml_p, _txt = load_h1_xml(code)
                agg = None
                if _txt:
                    for kw in ("후순위사채", "후순위채권", "후순위"):
                        agg = confirm_aggregate_unchanged(_txt, c.get("bs_subordinated_mn"), kw)
                        if agg:
                            break
                if agg:
                    conf_as_of = agg
                    conf_src = f"{xml_p.relative_to(ROOT).as_posix()} (BS 후순위 총액 당반기말==전기말==FY2025)"
                    report.setdefault("sub_confirm_by_aggregate", []).append(code)
            if conf_as_of:
                fy25_sub = [dict(b, as_of=conf_as_of,
                                 source_file=f"{conf_src} (채무증권 발행실적: 미상환 확인, 금액 불변)")
                            for b in fy25_sub]
                n_sub_confirmed += 1
                notes_extra.append(f"SUBORDINATED unchanged but confirmed still outstanding at "
                                   f"{conf_as_of} via 채무증권 발행실적 ({len(fy25_sub)} bond(s))")
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
    print(f"subordinated confirmed-unchanged (as_of only): {n_sub_confirmed} companies")
    print(f"subordinated refreshed from 상세표: {n_sub_detail} companies")
    print(f"subordinated 상환검출: {n_sub_redeem} companies")
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
