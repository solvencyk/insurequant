# -*- coding: utf-8 -*-
"""Build the /jp/ J-ESR page data JSON from the FY2025 census + 2026Q1 sources CSVs.

Owner ticket: inbox/publishing/20260912T0446Z__owner__JP_MULTI__jesr_page_json.md

Reads
-----
J-ESR/fy2025_esr_census_20260912.csv (utf-8-sig, 79 rows) -- primary source.
    Only rows with fy2025_esr_status == "posted" are used (15 as of 2026-09-12).
J-ESR/jesr_sources_2026Q1.csv (utf-8-sig, 11 rows) -- auxiliary columns
    (ticker / total assets / target ratio / esr basis), joined onto the census
    rows by company_jp. `ticker` is joined regardless of period (a listing
    symbol does not change quarter to quarter). `total_assets_bn_jpy`,
    `target_pct` and `basis` are joined ONLY when the sources row's `as_of`
    matches the census row's `as_of` -- the sources csv still carries stale
    H1/FY2024 figures for 4 mutual companies, and attaching a stale
    balance-sheet snapshot or methodology label to a newer posted record
    would be a silent wrong-source bug, not a join. Unmatched -> null.
J-ESR/jp_insurers.csv (utf-8-sig) -- `parent_group` column, joined onto the
    census rows by company_jp. Used only for the parent-subsidiary dedup
    below; no other column of this csv is consumed here.

Writes (no longer byte-identical -- 2026-09-12 parent-subsidiary dedup,
inbox/publishing/20260912T0530Z)
------------------------------------------------------------------------
J-ESR/jesr_master.json  -- the full posted census, unchanged from before
    (still 15 records as of 2026-09-12). This script is the sole producer of
    this path (full-replace is intentional, not a read-modify-write of a
    shared root master). This file is the source of truth for "who is
    posted"; the dedup below only affects what ships to the page.
jp/jesr_esr.json        -- deploy copy for the /jp/ page fetch, MINUS any
    subsidiary row whose parent group is *also* posted (same capital shown
    twice at two consolidation levels -- see `apply_subsidiary_dedup`
    below). `jp/` is created if it does not exist yet.

Schema is a fixed contract agreed with designer (see the ticket) -- key
names must not change; do not add or rename fields here without re-checking
with that ticket. `_meta.excluded_subsidiaries` on the deploy file is new
(2026-09-12) and additive -- designer does not render it, it exists for
audit/self-check only.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

# EXPIRING_HOSTS 는 jesr_http 에서 **import** 한다 — 여기에 옮겨 적지 않는다. 손으로 복사하면
# 이 빌더가 점검기(check_source_urls.py)와 다른 목록을 보게 되고, 그 순간 두 도구는 이름만 같은
# 다른 룰이 된다(K-ICS 상관행렬 재타이핑 금지와 같은 이유).
# import 는 네트워크를 타지 않는다 — jesr_http 모듈 최상위는 상수·정규식뿐이고 requests 는
# 함수 호출 시점에만 쓰인다. 이 빌더는 여전히 완전 오프라인이다.
# `try: import ... except ImportError: EXPIRING_HOSTS = ()` 류의 폴백을 두지 마라 —
# 빈 튜플로 떨어지면 룰이 조용히 no-op 이 된다(= 이 저장소가 반복해서 데인 false-green).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402

HERE = Path(__file__).resolve().parent
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
SOURCES_CSV = HERE / "jesr_sources_2026Q1.csv"
INSURERS_CSV = HERE / "jp_insurers.csv"
MASTER_OUT = HERE / "jesr_master.json"
DEPLOY_OUT = HERE.parent / "jp" / "jesr_esr.json"
#: 출처 게이트(JP_SOURCE_*, 2026-09-13 UH-18) 가 읽는 두 파일. 둘 다 오프라인 입력이다.
SOURCE_HEALTH_PATH = HERE / "source_url_health.json"      # check_source_urls.py --all 의 산출
SOURCE_EXCEPTIONS_PATH = HERE / "jp_source_exceptions.json"  # owner 승인 면제 등재처

# Generic corporate-suffix abbreviations seen in jp_insurers.csv's parent_group
# column (e.g. "東京海上HD", "ソニーFG"). Not company names -- these two
# abbreviations recur across many groups, so expanding them is reusable logic,
# not a per-company hardcode. Used only to test whether a parent_group value
# is a (possibly abbreviated) substring of an already-posted company_jp.
_SUFFIX_ABBREV = {"HD": "ホールディングス", "FG": "フィナンシャルグループ"}

AS_OF_TARGET = "2026-03-31"
# 2026-09-13 owner: 한국 사이트처럼 법인 단위로 전부 싣는다(교보생명·교보라이프플래닛 각각 게시와 동일). 부모-자회사
# 중복 제거는 끈다. True 로 되돌리면 apply_subsidiary_dedup 이 다시 동작한다(감사 이력용 보존).
SUBSIDIARY_DEDUP = False
AS_OF_LABEL_JA = "2026年3月31日"
NEXT_UPDATE = "2026-10-31"
BASIS_DEFAULT = "J-ICS"

SECTOR_MAP = {"損保": "nonlife", "生保": "life", "再保険": "reinsurance"}
PRELIM_KEYWORDS = ["속보", "잠정", "速報", "暫定", "監査未済"]  # ticket 규칙: 속보/잠정/速報 류 표현
# 2026-09-13: 일본어 원문 표기(暫定値·監査未済)를 추가. 노트에 원문을 그대로 인용하면
# 한국어 키워드만으로는 안 걸려 かんぽ生命(監査未済の暫定値)이 조용히 확정치로 표시됐다.


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _num(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _canon(n: float | None):
    """Whole floats -> int (so 319600.00000003 renders as 319600, not a float)."""
    if n is None:
        return None
    return int(round(n)) if abs(n - round(n)) < 1e-9 else round(n, 4)


def _extract_doc_date(doc_type: str | None) -> str | None:
    """Pull a date out of the census doc_type string, e.g.
    '決算短信/決算説明資料(2026-05-20)' -> '2026-05-20',
    '決算概要(2026年5月)' -> '2026-05'.
    Tries full ISO date, then Japanese Y/M/D, then Japanese Y/M."""
    if not doc_type:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", doc_type)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", doc_type)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})年(\d{1,2})月", doc_type)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def _detect_preliminary(notes: str | None, doc_type: str | None) -> tuple[bool, str | None]:
    haystack = f"{notes or ''} {doc_type or ''}"
    for kw in PRELIM_KEYWORDS:
        if kw in haystack:
            return True, kw
    return False, None


def build() -> dict:
    census_rows = _read_csv(CENSUS_CSV)
    source_rows = _read_csv(SOURCES_CSV)
    sources_by_name = {
        r["company_jp"].strip(): r for r in source_rows if (r.get("company_jp") or "").strip()
    }

    def status(r):
        return (r.get("fy2025_esr_status") or "").strip()

    total = len(census_rows)
    posted_rows = [r for r in census_rows if status(r) == "posted"]
    not_yet = sum(1 for r in census_rows if status(r) == "not_yet")
    not_found = sum(1 for r in census_rows if status(r) == "not_found")

    records = []
    for r in posted_rows:
        company_jp = (r.get("company_jp") or "").strip()
        sector_raw = (r.get("sector") or "").strip()
        as_of = (r.get("as_of") or "").strip() or None
        doc_type = (r.get("doc_type") or "").strip() or None
        notes = (r.get("notes") or "").strip() or None

        src = sources_by_name.get(company_jp)
        src_as_of_matches = bool(src) and (src.get("as_of") or "").strip() == as_of

        ticker = None
        if src:
            ticker = (src.get("ticker") or "").strip() or None

        total_assets_bn_jpy = None
        target_pct = None
        basis = BASIS_DEFAULT
        if src and src_as_of_matches:
            tn = _num(src.get("総資産_tn_jpy"))
            if tn is not None:
                total_assets_bn_jpy = _canon(tn * 1e4)  # 兆円 -> 億円 (x1e4)
            target_pct = (src.get("target_pct") or "").strip() or None
            basis = (src.get("esr_basis") or "").strip() or BASIS_DEFAULT
        # census 의 esr_basis 는 1차 원문에서 확인한 산정기준이라 sources csv 조인보다 우선한다
        # (2026-09-13 실측: 화면 15사 중 규제 표준모델 4 · 내부모델 7 · 내부관리 3 · 미확인 2.
        #  화면은 이 값을 렌더하지 않지만, 서로 다른 기준을 한 줄로 세우고 있다는 사실이
        #  데이터에 남아 있어야 한다 — 표기 방식은 owner 판단 대기)
        census_basis = (r.get("esr_basis") or "").strip()
        if census_basis:
            basis = census_basis

        # census 에 명시열이 있으면 그게 정본이다. 키워드 탐지는 명시값이 없을 때만 쓰는
        # 폴백 — 2026-09-13 실측에서 키워드 방식이 양방향으로 틀렸다(かんぽ는 일본어
        # 원문 인용이라 놓쳤고, 朝日·富国은 notes 안의 *다른 수치*에 붙은 속보 표기를
        # 헤드라인 값의 속보로 잘못 읽었다).
        explicit = (r.get("preliminary") or "").strip().lower()
        if explicit in ("yes", "true", "1"):
            preliminary, kw = True, "census.preliminary=yes"
        elif explicit in ("no", "false", "0"):
            preliminary, kw = False, None
        else:
            preliminary, kw = _detect_preliminary(notes, doc_type)
            if preliminary:
                tag = f"(preliminary 판정: notes 내 '{kw}' 검출)"
                notes = f"{notes} {tag}" if notes else tag

        records.append({
            "company_jp": company_jp,
            "company_en": (r.get("company_en") or "").strip(),
            "ticker": ticker,
            "sector": SECTOR_MAP.get(sector_raw),
            "category": (r.get("category") or "").strip() or None,
            "scope": (r.get("esr_scope") or "").strip() or None,
            "esr_pct": _num(r.get("esr_pct")),
            "basis": basis,
            "as_of": as_of,
            "preliminary": preliminary,
            "total_assets_bn_jpy": total_assets_bn_jpy,
            "target_pct": target_pct,
            "doc_type": doc_type,
            "doc_date": _extract_doc_date(doc_type),
            "source_url": (r.get("source_url") or "").strip() or None,
            "notes": notes,
        })

    records.sort(key=lambda x: x["esr_pct"], reverse=True)

    return {
        "_meta": {
            "as_of": AS_OF_TARGET,
            "as_of_label_ja": AS_OF_LABEL_JA,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "built_from": [CENSUS_CSV.name, SOURCES_CSV.name],
            "next_update": NEXT_UPDATE,
            "census": {
                "total": total,
                "posted": len(posted_rows),
                "not_yet": not_yet,
                "not_found": not_found,
            },
        },
        "records": records,
    }


# ---------------------------------------------------------------------------
# 출처 게이트 JP_SOURCE_* — UH-18 배선 (2026-09-13)
#
# 왜: 2026-09-12 census 로 15사가 화면에 올라갈 때 이 빌더의 self-check 는 전부 통과했는데,
# 다음 날 원문을 열어 보니 3사의 값·출처가 틀려 있었다(東京海上HD 238→268 · かんぽ 220→181 ·
# MS&AD 출처가 ESR 한 줄 없는 합병 보도자료). 못 잡은 이유는 단순하다 — 종전 self-check 는
# 범위·형식·합계만 보는 **자기참조**라 "출처가 살아 있나 / 점검을 돌리긴 했나" 축이 없었다.
# 형식만 맞으면 어떤 출처에서 온 어떤 숫자든 통과한다.
# 근거: docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md §2·§5
#
# 이 블록의 룰은 전부 **오프라인**이다. 네트워크가 필요한 판정은 선행 단계
# (check_source_urls.py --all)가 J-ESR/source_url_health.json 에 박제하고, 빌더는 그 박제를
# 읽는다. 그래서 JP_SOURCE_URL_DEAD 의 이빨은 JP_SOURCE_EVIDENCE_STALE 이 증거를 최신으로
# 유지해 주는 데 전적으로 의존한다 — 둘은 한 쌍이지 독립된 룰이 아니다.
# ---------------------------------------------------------------------------

#: 이 빌더가 거는 출처 룰 id 전체. 레지스트리에 여기 없는 id 가 있으면 RED —
#: 오타난 rule id 는 아무것도 면제하지 못하면서 "면제해 뒀다" 는 착각만 남긴다.
SOURCE_RULE_IDS = (
    "JP_SOURCE_EXPIRING_HOST",
    "JP_SOURCE_URL_DEAD",
    "JP_SOURCE_EVIDENCE_STALE",
    "JP_SOURCE_EVIDENCE_INCOMPLETE",
)
#: 면제 가능한 룰. 나머지 둘은 "점검을 돌렸는가" 를 묻는 **절차 룰**이라 면제하면 룰 자체가
#: 사라진다 — 낡았으면 면제하지 말고 점검을 다시 돌려라.
EXEMPTABLE_RULE_IDS = ("JP_SOURCE_EXPIRING_HOST", "JP_SOURCE_URL_DEAD")

#: 증거 파일에서 **RED 로 읽는 유일한 분류**. blocked(WAF 4xx) · ok_requires_headers(봇차단,
#: 헤더 붙이면 200) · tls_client_issue(파이썬만 실패, curl 200) · spa_shell(200 인 JS 셸) ·
#: error(5xx·타임아웃, 단정 금지) 는 **죽은 URL 이 아니다**. 2026-09-13 전수 실측에서
#: blocked 20 · ok_requires_headers 16 · tls_client_issue 4 가 나왔고, 이걸 dead 와 섞으면
#: 멀쩡한 회사 40건이 한꺼번에 거짓 RED 가 된다. 화면 15사만 보면 ok 12 ·
#: ok_requires_headers 2 · tls_client_issue 1 · dead 0 이다.
DEAD_CLASSIFICATIONS = ("dead",)

_EXCEPTION_REQUIRED_KEYS = ("rule", "company_jp", "field", "reason", "owner_approved_on")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CHECK_SOURCES_CMD = (
    "python3 J-ESR/check_source_urls.py --all --out J-ESR/source_url_health.json"
)


def load_source_exceptions(path: Path | None = None, *, today: str | None = None):
    """`J-ESR/jp_source_exceptions.json` 의 owner 승인 면제를 읽는다.

    *** 등재는 owner 권한이다. *** 에이전트·세션은 이 파일에 항목을 추가하지 않는다.
    RED 가 났으면 출처를 고치거나 담당 stage 에 발주하는 것이 정답이고, 여기에 한 줄
    넣어 통과시키는 것은 false-green 을 손으로 만드는 짓이다.

    fail-closed 규칙:
      - 파일이 아예 없으면 면제 0건으로 진행한다(게이트가 더 엄해지는 방향이라 막지 않는다).
      - 파일이 있는데 못 읽으면 **RED**. "읽을 수 없으니 면제 없음" 으로 조용히 넘기면
        손상된 레지스트리가 보이지 않는다.
      - 필수 키(사유·owner 승인일 포함)가 빠졌으면 **RED** — 익명 면제를 막는다.
      - 모르는 rule id, 면제 불가한 룰을 가리키는 항목도 **RED**.
      - `expires_on` 이 지났으면 면제를 적용하지 않는다(자동으로 엄해진다). RED 는 아니다.

    반환: (면제키 집합 {(rule, company_jp, field)}, errors, notes)
    """
    path = SOURCE_EXCEPTIONS_PATH if path is None else path
    errors: list[str] = []
    notes: list[str] = []
    if not path.exists():
        notes.append(f"[source-gate] 예외 레지스트리 없음({path.name}) — 면제 0건으로 진행")
        return set(), errors, notes
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(
            f"[JP_SOURCE_EXCEPTIONS] {path.name} 을 읽을 수 없다: {type(exc).__name__}: {exc}"
        )
        return set(), errors, notes
    entries = data.get("exceptions") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        errors.append(
            f"[JP_SOURCE_EXCEPTIONS] {path.name}: 'exceptions' 가 배열이 아니다"
            f" ({type(entries).__name__})"
        )
        return set(), errors, notes

    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    keys: set[tuple[str, str, str]] = set()
    for i, entry in enumerate(entries):
        where = f"{path.name}[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"[JP_SOURCE_EXCEPTIONS] {where}: 객체가 아니다")
            continue
        missing = [k for k in _EXCEPTION_REQUIRED_KEYS if not str(entry.get(k) or "").strip()]
        if missing:
            errors.append(
                f"[JP_SOURCE_EXCEPTIONS] {where}: 필수 키 누락 {missing} —"
                f" 사유·owner 승인일 없는 면제는 등재하지 않는다"
            )
            continue
        rule = str(entry["rule"]).strip()
        if rule not in SOURCE_RULE_IDS:
            errors.append(
                f"[JP_SOURCE_EXCEPTIONS] {where}: 알 수 없는 rule id {rule!r}"
                f" (아는 id: {', '.join(SOURCE_RULE_IDS)})"
            )
            continue
        if rule not in EXEMPTABLE_RULE_IDS:
            errors.append(
                f"[JP_SOURCE_EXCEPTIONS] {where}: {rule} 은 면제 불가한 절차 룰이다 —"
                f" 면제하지 말고 점검을 다시 돌려라: {CHECK_SOURCES_CMD}"
            )
            continue
        approved = str(entry["owner_approved_on"]).strip()
        if not _DATE_RE.match(approved):
            errors.append(
                f"[JP_SOURCE_EXCEPTIONS] {where}: owner_approved_on 형식 오류"
                f" {approved!r} (YYYY-MM-DD)"
            )
            continue
        expires = entry.get("expires_on")
        if expires is not None:
            expires = str(expires).strip()
            if not _DATE_RE.match(expires):
                errors.append(
                    f"[JP_SOURCE_EXCEPTIONS] {where}: expires_on 형식 오류"
                    f" {expires!r} (YYYY-MM-DD 또는 null)"
                )
                continue
            if expires < today:
                notes.append(
                    f"[source-gate] 만료된 면제 무시: {where} {rule}"
                    f" {entry['company_jp']} (expires_on={expires} < {today})"
                )
                continue
        keys.add((rule, str(entry["company_jp"]).strip(), str(entry["field"]).strip()))
    return keys, errors, notes


def _census_checked_at_max(census_rows: list[dict]) -> tuple[str | None, list[str]]:
    """census `checked_at` 의 최댓값(YYYY-MM-DD)과 에러.

    posted 행의 `checked_at` 이 비어 있으면 **RED** 다. 비워 두면 최댓값이 조용히 내려가
    낡은 증거가 통과한다 — 즉 결측이 게이트 우회 수단이 된다("결측은 SKIP 이 아니라 RED").
    """
    errors: list[str] = []
    best: str | None = None
    for row in census_rows:
        raw = (row.get("checked_at") or "").strip()
        posted = (row.get("fy2025_esr_status") or "").strip() == "posted"
        company = (row.get("company_jp") or "").strip() or "<이름없음>"
        if not raw:
            if posted:
                errors.append(
                    f"[JP_SOURCE_EVIDENCE_STALE] posted 행의 checked_at 이 비어 있다: {company}"
                    f" — 언제 확인한 출처인지 모르면 증거 신선도를 잴 수 없다"
                )
            continue
        day = raw[:10]
        if not _DATE_RE.match(day):
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] census checked_at 을 못 읽는다:"
                f" {company} = {raw!r} (YYYY-MM-DD 여야 한다)"
            )
            continue
        if best is None or day > best:
            best = day
    return best, errors


def source_gate_check(
    records: list[dict],
    census_rows: list[dict],
    *,
    health_path: Path | None = None,
    exceptions_path: Path | None = None,
    today: str | None = None,
    verbose: bool = True,
) -> list[str]:
    """출처 게이트 4룰. 반환된 문자열은 그대로 self_check 의 errors 로 흘러 exit 1 이 된다.

    scope = census `posted` 행 = `jesr_master.json` records ⊇ `jp/jesr_esr.json` records.
    (부모-자회사 dedup 이 켜져도 마스터 쪽이 상위집합이라 검사가 더 엄해지지, 느슨해지지 않는다.)

    - `JP_SOURCE_EXPIRING_HOST`     source_url netloc 이 jesr_http.EXPIRING_HOSTS 면 RED
    - `JP_SOURCE_URL_DEAD`          증거 파일이 그 URL 을 dead(404/410)로 기록했으면 RED
    - `JP_SOURCE_EVIDENCE_STALE`    증거 파일 부재·scope≠all·census 보다 낡음이면 RED
    - `JP_SOURCE_EVIDENCE_INCOMPLETE`  posted 행 source_url 이 증거에 아예 없으면 RED
    """
    health_path = SOURCE_HEALTH_PATH if health_path is None else health_path
    errors: list[str] = []
    exempt, exc_errors, notes = load_source_exceptions(exceptions_path, today=today)
    errors.extend(exc_errors)

    expiring_hosts = {h.lower() for h in jesr_http.EXPIRING_HOSTS}
    posted_urls: list[tuple[str, str]] = []  # (company_jp, url)
    for rec in records:
        company = (rec.get("company_jp") or "").strip() or "<이름없음>"
        url = (rec.get("source_url") or "").strip()
        if not url:
            continue  # 빈 source_url 은 위쪽 self_check 의 https 룰이 이미 RED 로 잡는다
        posted_urls.append((company, url))
        netloc = urlsplit(url).netloc.lower()
        if netloc in expiring_hosts:
            if ("JP_SOURCE_EXPIRING_HOST", company, "source_url") in exempt:
                notes.append(f"[source-gate] 면제 적용 JP_SOURCE_EXPIRING_HOST · {company}")
                continue
            errors.append(
                f"[JP_SOURCE_EXPIRING_HOST] {company} source_url 의 호스트 {netloc} 는"
                f" 게시가 만료되는 호스트다(지금 200 이어도 반드시 썩는다)."
                f" 회사 IR/디스클로저의 영구 경로로 바꿔라: {url}"
            )

    census_max, census_errors = _census_checked_at_max(census_rows)
    errors.extend(census_errors)

    health: dict | None = None
    if not health_path.exists():
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] 출처 점검 증거가 없다: {health_path.name} —"
            f" census 를 고치기 전에 먼저 돌려라: {CHECK_SOURCES_CMD}"
        )
    else:
        try:
            loaded = json.loads(health_path.read_text(encoding="utf-8"))
            health = loaded if isinstance(loaded, dict) else None
            if health is None:
                errors.append(
                    f"[JP_SOURCE_EVIDENCE_STALE] {health_path.name}: 최상위가 객체가 아니다"
                )
        except Exception as exc:
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] {health_path.name} 을 읽을 수 없다:"
                f" {type(exc).__name__}: {exc}"
            )

    checked_at = None
    if health is not None:
        scope = str(health.get("scope") or "").strip()
        if scope != "all":
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] {health_path.name}: scope={scope!r} 이다."
                f" 'all' 이 아닌 좁은 범위 산출로 게이트를 통과시키면 검사한 척만 하는 것이다 —"
                f" 다시 돌려라: {CHECK_SOURCES_CMD}"
            )
        checked_raw = str(health.get("checked_at") or "").strip()
        checked_at = checked_raw[:10]
        if not _DATE_RE.match(checked_at):
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] {health_path.name}: checked_at 을 못 읽는다"
                f" {checked_raw!r} (YYYY-MM-DD... 여야 한다)"
            )
            checked_at = None
        elif census_max and checked_at < census_max:
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] 증거가 census 보다 낡았다:"
                f" {health_path.name}.checked_at={checked_raw} < census 최신 checked_at"
                f"={census_max}. census 를 고쳤는데 점검을 다시 안 돌렸다는 뜻이다 —"
                f" {CHECK_SOURCES_CMD}"
            )

        rows = health.get("rows")
        if not isinstance(rows, list):
            errors.append(
                f"[JP_SOURCE_EVIDENCE_STALE] {health_path.name}: 'rows' 가 배열이 아니다"
                f" ({type(rows).__name__})"
            )
        else:
            probed: dict[str, str] = {}
            for row in rows:
                if not isinstance(row, dict):
                    continue
                url = str(row.get("url") or "").strip()
                if url:
                    # 같은 URL 이 여러 origin 에 있으면 판정은 같다. 나쁜 쪽을 남긴다.
                    cls = str(row.get("classification") or "").strip()
                    if url not in probed or cls in DEAD_CLASSIFICATIONS:
                        probed[url] = cls
            for company, url in posted_urls:
                if url not in probed:
                    errors.append(
                        f"[JP_SOURCE_EVIDENCE_INCOMPLETE] {company} 의 source_url 이"
                        f" {health_path.name} 에 아예 없다 — 이 URL 은 한 번도 점검된 적이 없다."
                        f" {CHECK_SOURCES_CMD} 를 census 수정 **후에** 돌려라: {url}"
                    )
                elif probed[url] in DEAD_CLASSIFICATIONS:
                    if ("JP_SOURCE_URL_DEAD", company, "source_url") in exempt:
                        notes.append(f"[source-gate] 면제 적용 JP_SOURCE_URL_DEAD · {company}")
                        continue
                    errors.append(
                        f"[JP_SOURCE_URL_DEAD] {company} 의 source_url 이 죽었다"
                        f"(classification={probed[url]}, 404/410). 대체 URL 이 필요하다: {url}"
                    )

    if verbose:
        for note in notes:
            print(note)
        print(
            f"[source-gate] posted {len(posted_urls)}건 · expiring-host 검사 완료 ·"
            f" 증거 {health_path.name} checked_at={checked_at or '?'}"
            f" scope={(health or {}).get('scope', '?')!r}"
            f" · census 최신 checked_at={census_max or '?'} · 면제 {len(exempt)}건"
            f" · RED {len(errors)}건"
        )
    return errors


def self_check(out: dict, census_rows: list[dict] | None = None) -> list[str]:
    errors = []
    recs = out["records"]
    if len(recs) != 15:
        errors.append(f"records count = {len(recs)}, expected 15")
    seen = set()
    for rec in recs:
        name = rec["company_jp"]
        if name in seen:
            errors.append(f"duplicate company_jp: {name}")
        seen.add(name)
        e = rec["esr_pct"]
        if e is None or not isinstance(e, float) or not (100 <= e <= 1000):
            errors.append(f"esr_pct out of range or not float: {name} = {e!r}")
        if rec["scope"] not in ("group", "solo"):
            errors.append(f"bad scope: {name} = {rec['scope']!r}")
        if rec["sector"] not in ("life", "nonlife", "reinsurance"):
            errors.append(f"bad sector: {name} = {rec['sector']!r}")
        su = rec["source_url"]
        if not su or not su.startswith("https://"):
            errors.append(f"source_url not https: {name} = {su!r}")
        if rec["as_of"] != AS_OF_TARGET:
            errors.append(f"as_of != {AS_OF_TARGET}: {name} = {rec['as_of']!r}")
    c = out["_meta"]["census"]
    if c["posted"] + c["not_yet"] + c["not_found"] != c["total"]:
        errors.append(f"census does not sum to total: {c}")
    if c["posted"] != len(recs):
        errors.append(f"census.posted ({c['posted']}) != len(records) ({len(recs)})")
    # 출처 게이트도 같은 errors 리스트로 흘려보낸다 — main() 이 errors 가 있으면 return 1 이므로
    # 여기에 붙이는 것만으로 **실제 exit code 가 바뀐다**(배선했다 ≠ 돈다를 가르는 지점).
    errors.extend(
        source_gate_check(
            recs, _read_csv(CENSUS_CSV) if census_rows is None else census_rows
        )
    )
    return errors


def _expand_abbrev(name: str) -> str | None:
    """If `name` ends with a known corporate-suffix abbreviation, return the
    variant with that suffix spelled out in full. None if no abbreviation
    matches (most parent_group values, e.g. plain "KDDI" or "明治安田")."""
    for abbr, full in _SUFFIX_ABBREV.items():
        if name.endswith(abbr):
            return name[: -len(abbr)] + full
    return None


def _find_parent_record(parent_group: str, records_by_jp: dict, self_jp: str):
    """Return the posted record whose company_jp contains `parent_group`
    (directly, or via the abbreviation-expanded form), else None. Never
    matches the subsidiary's own record."""
    if not parent_group:
        return None
    candidates = [parent_group]
    expanded = _expand_abbrev(parent_group)
    if expanded:
        candidates.append(expanded)
    # 대소문자 무시 — jp_insurers.csv 의 parent_group "Sompo" 가 랭킹의 "SOMPOホールディングス" 와 매칭돼야 한다(2026-09-13).
    cands_l = [c.lower() for c in candidates]
    for jp_name, rec in records_by_jp.items():
        if jp_name == self_jp:
            continue
        if any(cand in jp_name.lower() for cand in cands_l):
            return rec
    return None


def apply_subsidiary_dedup(records: list[dict], insurers_by_name: dict) -> tuple[list[dict], list[dict]]:
    """Drop any posted subsidiary row whose parent group is *also* posted --
    same underlying capital would otherwise show up twice at two
    consolidation levels (group HD/mutual-parent solo/group vs. subsidiary
    solo). General rule (ticket inbox/publishing/20260912T0530Z, no company
    names hardcoded): a record is a candidate for exclusion only if its
    census `category` starts with "子会社"; its `parent_group` (from
    jp_insurers.csv, joined by company_jp) is then tested against every
    *other* posted record's company_jp. A match (direct or abbreviation-
    expanded substring) excludes it. Empty parent_group, or a parent_group
    that matches no posted record (parent is not an insurer, or not yet
    posted -- e.g. au損害保険's parent KDDI), keeps the row.

    Returns (kept_records, excluded_entries) where excluded_entries carries
    company_en / parent / esr_pct for the `_meta.excluded_subsidiaries` audit
    trail -- not rendered on the page.
    """
    records_by_jp = {r["company_jp"]: r for r in records}
    kept, excluded = [], []
    # 2026-09-13 owner 결정: 한국 사이트 기준(교보생명·교보라이프플래닛을 각각 게시, K-ICS 는 법인 단위)에
    # 맞춰 **자회사도 한 행씩 전부 싣는다** — 이 dedup 은 끈다(SUBSIDIARY_DEDUP=False). 지주 6사의 連結값은
    # 10월 単体 공시가 나오면 사업회사 単体값으로 교체(範囲 열 "連結" 표시로 임시 구분). 함수는 감사 이력용으로 보존.
    if not SUBSIDIARY_DEDUP:
        return list(records), []
    for r in records:
        category = r.get("category") or ""
        parent_rec = None
        if category.startswith("子会社"):
            insurer_row = insurers_by_name.get(r["company_jp"])
            parent_group = (insurer_row.get("parent_group") or "").strip() if insurer_row else ""
            parent_rec = _find_parent_record(parent_group, records_by_jp, r["company_jp"])
            # 2026-09-13 owner: 같은 업권(生保/損保) 표 안에서만 중복이다. 부모가 다른 업권 표에
            # 있으면(明治安田損保 ← 明治安田生命) 자회사는 그 업권의 유일한 데이터 포인트라 남긴다.
            # (ソニー生命 ← ソニーFG 는 둘 다 life 라 계속 제외.)
            if parent_rec is not None and parent_rec.get("sector") != r.get("sector"):
                parent_rec = None
        if parent_rec is not None:
            excluded.append({
                "company_en": r["company_en"],
                "parent": parent_rec["company_en"],
                "esr_pct": r["esr_pct"],
            })
        else:
            kept.append(r)
    return kept, excluded


DETAIL_JSON = HERE.parent / "jp" / "jesr_detail.json"


def build_group_children(records: list[dict], insurers_by_name: dict) -> dict:
    """owner 2026-09-13: 랭킹의 지주(연결) 행 ↔ 상세 페이지가 있는 사업회사(単体)를 잇는다.
    상세가 있는 회사(jp/jesr_detail.json companies)의 jp_insurers.csv `parent_group` 을 랭킹 레코드의
    company_jp 에 (약칭 확장 포함) 매칭 → {parent_company_jp: [{"id","company_jp","company_en"}]}.
    화면: index 지주 행 클릭 → 첫 자식 상세, jesr 지주 헤드라인 페이지에 자식 링크. 상세 파일이 없으면 {}."""
    if not DETAIL_JSON.exists():
        return {}
    try:
        detail = json.loads(DETAIL_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    records_by_jp = {r["company_jp"]: r for r in records}
    out: dict = {}
    for c in detail.get("companies", []):
        jp = c.get("company_jp") or ""
        row = insurers_by_name.get(jp)
        parent_group = (row.get("parent_group") or "").strip() if row else ""
        parent = _find_parent_record(parent_group, records_by_jp, jp) if parent_group else None
        if parent is None:
            continue
        # owner 2026-09-13: "지주(연결) ↔ 같은 업권의 사업회사" 만 잇는다. 明治安田生命(생보 본체) → 明治安田損保(손보 자회사)처럼
        # 업권이 다른 모자관계는 별개 회사이므로 연결하지 않는다(자회사는 자기 업권 랭킹에 자기 행이 있다).
        child_sector = c.get("sector")
        if parent.get("scope") != "group" or (child_sector and parent.get("sector") != child_sector):
            continue
        out.setdefault(parent["company_jp"], []).append(
            {"id": c.get("id"), "company_jp": jp, "company_en": c.get("company_en")}
        )
    return out


# owner 2026-09-13: 랭킹 색 기준을 감독 하한 100% 에서 각사 ESR 목표 레인지로. 티켓 20260913T1610Z 산출
# J-ESR/esr_target_ranges.json(census, basis/출처 포함) 을 company_en 으로 레코드에 붙인다 — 값이 없으면 None(페이지는 100% 기준 폴백).
TARGET_RANGES_PATH = Path(__file__).resolve().parent / "esr_target_ranges.json"


def attach_target_ranges(records: list[dict]) -> dict:
    if not TARGET_RANGES_PATH.exists():
        return {"as_of": None, "attached": 0}
    data = json.loads(TARGET_RANGES_PATH.read_text(encoding="utf-8"))
    by_en = {(r.get("company_en") or "").strip().lower(): r for r in data.get("ranges", [])}
    n = 0
    for rec in records:
        tr = by_en.get((rec.get("company_en") or "").strip().lower())
        if tr and tr.get("low_pct") is not None:
            rec["target_range"] = {"low_pct": tr.get("low_pct"), "high_pct": tr.get("high_pct"), "basis": tr.get("basis"),
                                   "inherited_from": tr.get("inherited_from"), "source_doc": tr.get("source_doc"), "source_url": tr.get("source_url"),
                                   "as_of": tr.get("as_of")}
            n += 1
        else:
            rec["target_range"] = None
    return {"as_of": (data.get("_meta") or {}).get("as_of"), "attached": n}


def main() -> int:
    out = build()

    errors = self_check(out)
    if errors:
        for e in errors:
            print(f"SELF-CHECK FAIL: {e}", file=sys.stderr)
        return 1

    insurer_rows = _read_csv(INSURERS_CSV)
    insurers_by_name = {
        r["company_jp"].strip(): r for r in insurer_rows if (r.get("company_jp") or "").strip()
    }
    deploy_records, excluded = apply_subsidiary_dedup(out["records"], insurers_by_name)

    if len(out["records"]) - len(excluded) != len(deploy_records):
        print(
            "SELF-CHECK FAIL: jesr_master records - excluded subsidiaries != "
            f"jp/jesr_esr records ({len(out['records'])} - {len(excluded)} != {len(deploy_records)})",
            file=sys.stderr,
        )
        return 1

    deploy_meta = dict(out["_meta"])
    deploy_meta["excluded_subsidiaries"] = excluded
    deploy_meta["group_children"] = build_group_children(deploy_records, insurers_by_name)
    deploy_meta["target_ranges"] = attach_target_ranges(deploy_records)
    deploy_out = {"_meta": deploy_meta, "records": deploy_records}

    master_text = json.dumps(out, ensure_ascii=False, indent=2)
    deploy_text = json.dumps(deploy_out, ensure_ascii=False, indent=2)

    MASTER_OUT.write_text(master_text, encoding="utf-8")
    DEPLOY_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEPLOY_OUT.write_text(deploy_text, encoding="utf-8")

    print(f"wrote {MASTER_OUT}  ({len(out['records'])} records)")
    print(f"wrote {DEPLOY_OUT}  ({len(deploy_records)} records, excluded={len(excluded)})")
    print(f"  census: {out['_meta']['census']}")
    if excluded:
        print(f"  excluded_subsidiaries: {excluded}")
    prelim = [r['company_en'] for r in out['records'] if r['preliminary']]
    print(f"  preliminary={len(prelim)}: {prelim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
