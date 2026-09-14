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
#: 출처 게이트(JP_SOURCE_*, 2026-09-13 UH-18) 가 읽는 세 파일. 전부 오프라인 입력이다.
SOURCE_HEALTH_PATH = HERE / "source_url_health.json"      # check_source_urls.py --all 의 산출
ESR_HEALTH_PATH = HERE / "esr_in_source_health.json"      # check_esr_in_source.py --all 의 산출
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


def _as_of_label_ja(iso: str) -> str:
    """'2026-03-31' -> '2026年3月31日'.

    화면 라벨은 AS_OF_TARGET 에서 **파생**한다. 손으로 또 적어 두면 같은 사실이 두 벌이 되고,
    기간을 바꾸는 사람은 보통 ISO 쪽만 고친다 — 그러면 9월 데이터에 '3月31日' 라벨이
    붙은 채로 어느 검사에도 안 걸린다(같은 사실 두 벌 = 이 저장소가 골든 표·룰 id 목록에서
    반복해서 데인 형태).
    """
    y, m, d = iso.split("-")
    return f"{y}年{int(m)}月{int(d)}日"


AS_OF_LABEL_JA = _as_of_label_ja(AS_OF_TARGET)
NEXT_UPDATE = "2026-10-31"
BASIS_DEFAULT = "J-ICS"

SECTOR_MAP = {"損保": "nonlife", "生保": "life", "再保険": "reinsurance"}
PRELIM_KEYWORDS = ["속보", "잠정", "速報", "暫定", "監査未済"]  # ticket 규칙: 속보/잠정/速報 류 표현
# 2026-09-13: 일본어 원문 표기(暫定値·監査未済)를 추가. 노트에 원문을 그대로 인용하면
# 한국어 키워드만으로는 안 걸려 かんぽ生命(監査未済の暫定値)이 조용히 확정치로 표시됐다.

# ---------------------------------------------------------------------------
# census 어휘 — census 열 값을 읽는 **유일한 정의**다.
# build() 와 self_check 가 각자 문자열을 적어 두면 한쪽만 고쳐져도 아무도 모른다
# (K-ICS 상관행렬을 검증기에 재타이핑하지 말라는 규칙과 같은 이유).
# ---------------------------------------------------------------------------
POSTED_STATUS = "posted"
#: census `fy2025_esr_status` 가 가질 수 있는 값. 여기 없는 값은 세 카운터 어디에도 안 잡혀
#: `posted+not_yet+not_found == total` 을 깨뜨린다 — 그 행은 화면에도 census 요약에도
#: 없는 유령이 된다. 미분류는 SKIP 이 아니라 RED.
CENSUS_STATUSES = (POSTED_STATUS, "not_yet", "not_found")
#: census `preliminary` 명시열의 어휘. 빈 값은 "명시 안 함"(= PRELIM_KEYWORDS 폴백)이라 정상이고,
#: **모르는 값**은 build() 의 if/elif 어느 쪽에도 안 걸려 조용히 폴백으로 떨어진다(= 오독).
PRELIM_TRUE = ("yes", "true", "1")
PRELIM_FALSE = ("no", "false", "0")
#: 화면에 실리는 `scope` 어휘. sector 어휘는 SECTOR_MAP 의 **값**에서 파생시킨다 —
#: 여기 다시 적으면 SECTOR_MAP 에 업권을 하나 추가하는 순간 그 업권이 전부 RED 가 된다.
SCOPE_VALUES = ("group", "solo")
SECTOR_VALUES = tuple(SECTOR_MAP.values())
#: esr_pct 의 도메인 상·하한. **이건 일부러 리터럴이다** — census 에서 파생할 값이 아니다.
#: 100% 는 J-ICS 규제 하한(밑돌면 사람이 원문을 확인해야 하는 사건)이고, 1000% 는 단위 오류
#: (배수·bp 혼동, 총자산을 esr_pct 칸에 붙여넣기)를 잡는 상식선이다. 데이터에서 파생시키면
#: 틀린 값이 스스로 범위를 넓혔 버려 검사 자체가 사라진다.
ESR_PCT_MIN = 100.0
ESR_PCT_MAX = 1000.0


def census_status(row: dict) -> str:
    return (row.get("fy2025_esr_status") or "").strip()


def census_posted_rows(rows: list[dict]) -> list[dict]:
    """'누가 posted 인가' 의 유일한 정의. 화면 회사 수는 전부 여기서 나온다."""
    return [r for r in rows if census_status(r) == POSTED_STATUS]


def census_counts(rows: list[dict]) -> dict:
    """`_meta.census` 요약. 키 순서는 배포 JSON 의 바이트라 바꾸지 마라."""
    counts = {"total": len(rows)}
    for st in CENSUS_STATUSES:
        counts[st] = sum(1 for r in rows if census_status(r) == st)
    return counts


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

    counts = census_counts(census_rows)
    posted_rows = census_posted_rows(census_rows)

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
        if explicit in PRELIM_TRUE:
            preliminary, kw = True, "census.preliminary=yes"
        elif explicit in PRELIM_FALSE:
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

    # esr_pct 가 None 인 행(posted 로 뒤집혔는데 값을 안 채운 census 행)이 섞이면 예전엔
    # 정렬이 TypeError 로 죽어 self_check 가 **도달하지도 못했다**. 막히는 것 자체는 같지만
    # 트레이스백과 "어느 회사의 esr_pct 가 비었다" 는 가치가 다르다 — None 은 맨 뒤로 보내고
    # 이름 붙은 RED 를 self_check 가 내게 한다. 값이 전부 있으면 정렬 결과는 종전과 바이트 동일하다.
    records.sort(key=lambda x: (x["esr_pct"] is not None, x["esr_pct"] or 0.0), reverse=True)

    return {
        "_meta": {
            "as_of": AS_OF_TARGET,
            "as_of_label_ja": AS_OF_LABEL_JA,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "built_from": [CENSUS_CSV.name, SOURCES_CSV.name],
            "next_update": NEXT_UPDATE,
            "census": dict(counts),
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
    "JP_ESR_NOT_IN_SOURCE",
    "JP_ESR_ADJUSTED_FIGURE",
    "JP_ESR_UNVERIFIED_VALUE",
    "JP_SOURCE_EVIDENCE_STALE",
    "JP_SOURCE_EVIDENCE_INCOMPLETE",
)
#: 면제 가능한 룰. 나머지 둘은 "점검을 돌렸는가" 를 묻는 **절차 룰**이라 면제하면 룰 자체가
#: 사라진다 — 낡았으면 면제하지 말고 점검을 다시 돌려라.
EXEMPTABLE_RULE_IDS = ("JP_SOURCE_EXPIRING_HOST", "JP_SOURCE_URL_DEAD",
                       "JP_ESR_NOT_IN_SOURCE", "JP_ESR_ADJUSTED_FIGURE",
                       "JP_ESR_UNVERIFIED_VALUE")

#: 증거 파일에서 **RED 로 읽는 유일한 분류**. blocked(WAF 4xx) · ok_requires_headers(봇차단,
#: 헤더 붙이면 200) · tls_client_issue(파이썬만 실패, curl 200) · spa_shell(200 인 JS 셸) ·
#: error(5xx·타임아웃, 단정 금지) 는 **죽은 URL 이 아니다**. 2026-09-13 전수 실측에서
#: blocked 20 · ok_requires_headers 16 · tls_client_issue 4 가 나왔고, 이걸 dead 와 섞으면
#: 멀쩡한 회사 40건이 한꺼번에 거짓 RED 가 된다. 화면 15사만 보면 ok 12 ·
#: ok_requires_headers 2 · tls_client_issue 1 · dead 0 이다.
DEAD_CLASSIFICATIONS = ("dead",)

#: `esr_in_source_health.json` 의 verdict 어휘. 모르는 값은 RED 다(fail-closed) — 수집기가
#: 새 verdict 를 내기 시작했는데 여기 안 배선돼 있으면 그 행은 **아무 검사도 안 받는다**.
#: (이 저장소가 반복해서 데인 "룰이 순회조차 안 하는 축" 이 정확히 그 모양이다.)
ESR_VERDICT_PASS = ("found",)
ESR_VERDICT_RED = ("not_found",)
#: SKIP+YELLOW. 실측 근거(2026-09-13 posted 15사 전수):
#:  - skip_landing  : `source_url` 이 PDF 가 아니라 상설 IR 페이지(T&D 1사). 문서가 아니라
#:    목록 페이지라 "그 문서에 그 숫자가" 를 물을 대상이 아니다.
#:  - skip_no_text  : 텍스트 레이어 0자(이미지형 PDF). **실측 0사** — 초안 §2 의 "최소 2사
#:    이미지형" 은 추정이었고 실측이 뒤집었다. 방어용으로만 남긴다.
ESR_VERDICT_YELLOW = ("skip_landing", "skip_no_text")
#: 판정이 아니라 "받지 못했다". 네트워크 사고를 데이터 오류로 둔갑시키지 않으려고 수집기가
#: 따로 적는 값이고, 게이트는 절차 룰(EVIDENCE_INCOMPLETE)로 잡는다 — 면제 불가.
ESR_VERDICT_UNJUDGED = ("fetch_failed",)

# --- JP_ESR_ADJUSTED_FIGURE (UH-21, 2026-09-13) -----------------------------
# 위 축(JP_ESR_NOT_IN_SOURCE)은 "그 문서에 그 숫자가 있나" 만 묻는다. 2026-09-12 사고 3건 중
# かんぽ 220% 는 그 축으로 **원리상** 안 걸린다 — 220 은 자료 p35 에 실재하는
# 「大量解約リスクを除いた場合」 조정치다(실측 d=1 → found). 즉 かんぽ형은 "없는 숫자를 썼다"
# 가 아니라 "있는 숫자 중 한정 조건이 붙은 것을 헤드라인으로 골랐다" 이고, 같은 문서에 한정어
# 없는 진짜 헤드라인(181%)이 나란히 있었다. 판정식 정본은 수집기의 `scan_adjusted` docstring.
#
# severity 는 **YELLOW** 다. 한정어 목록이 휴리스틱이고, 조건부 값을 정당하게 헤드라인으로 쓰는
# 회사가 있을 수 있어 RED 로 걸면 정상 배포를 막는다(UH-5·UH-9 선례: 오탐억제를 설계할 수
# 없으면 걸지 않는다). 다만 **"인쇄만 하는 YELLOW" 는 통제가 아니다** — 2026-09-12 에는 census
# notes 에 「特定条件を除いた場合の ESR は 220%」 라고 적혀 있었는데도 그 값이 그대로 나갔다.
# 그래서 배포본 증거에 면제 없는 발화가 남아 있으면 push 묶음의 오프라인 테스트가 막는다
# (tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_adjusted_figure).
ESR_ADJUSTED_PASS = ("unqualified",)
#: 판정하지 않은 분류. **SKIP 이 아니라 따로 세는 분류**다 — 몇 사가 판정 대상이 아니었는지를
#: source-gate 요약이 인쇄한다("룰이 0이라고 말한다" 와 "그 축이 깨끗하다" 는 다르다).
#:  - abstain_no_prose : ESR 라벨과 값이 같이 나오는 산문 조각이 0개(표·차트 전용 문서).
#:    2026-09-13 실측으로 15사 중 7사가 이 형태다 — 기권 조건 없이 걸면 거짓 발화 7건.
#:  - not_applicable   : PDF 가 아니거나 문서를 못 받아 애초에 판정 대상이 아니다.
ESR_ADJUSTED_ABSTAIN = ("abstain_no_prose", "not_applicable")
#: 발화. adjusted_alt 가 **본 룰**(같은 문서에 한정어 없는 대안값이 있다), adjusted_only 는
#: 보조(한정어는 붙었는데 대안이 없다). 둘 다 YELLOW 지만 메시지가 다르다.
ESR_ADJUSTED_YELLOW = ("adjusted_alt", "adjusted_only")

# --- JP_ESR_UNVERIFIED_VALUE (UH-25, 2026-09-14) ----------------------------
# 위 두 축은 각각 "그 문서에 그 숫자가 있나"(1차) 와 "그 숫자가 우리가 싣겠다고 한 정의인가"
# (조정치) 를 묻는다. **둘 다 침묵할 수 있다** — 그리고 그 침묵은 어디에도 안 남았다.
#
# 메커니즘(실측, UH-25): `source_url` 이 PDF 가 아니면 수집기 `check_esr_in_source.py::check_row`
# 의 `is_pdf` 분기가 문서를 `scan_landing` 으로 보내 `verdict="skip_landing"` 을 적고, 같은
# 함수가 `_not_judged_adjusted("PDF 가 아니라 조정치 판정 대상이 아니다")` 로
# `adjusted_verdict="not_applicable"` 을 같이 적는다. 그러면 `JP_ESR_NOT_IN_SOURCE` 는
# ESR_VERDICT_YELLOW 라 인쇄만 하고, `JP_ESR_ADJUSTED_FIGURE` 는 ESR_ADJUSTED_ABSTAIN 이라
# 기권한다 → **그 행의 화면값은 어떤 원문과도 대조된 적이 없는데 빌더는 exit 0 · RED 0** 이다.
# 2026-09-13 라이브에 T&D 222% 1건이 정확히 그 상태로 있었다(증거 evidence 는 「본문에 222
# 표기가 안 보인다」 였는데도 게이트는 green).
#
# 판정식 — posted 행의 증거에서 **두 필드를 각각** 본다. 둘 중 하나라도 참이면 발화:
#   (a) verdict          ∈ ESR_VERDICT_YELLOW      (skip_landing · skip_no_text)
#   (b) adjusted_verdict ∈ ESR_ADJUSTED_NOT_JUDGED (not_applicable)
# 논리곱(= 0축)이 아니라 논리합인 이유: 두 메커니즘은 수집기가 바뀌면 **따로** 재현된다.
# 곱으로 걸면 반쪽 회귀(한 축만 죽은 상태)가 빠져나가고, 그게 이 저장소가 반복해서 데인
# "룰이 순회는 하는데 그 칸은 안 본다" 의 모양이다.
#
# **오탐 억제의 핵심은 `abstain_no_prose` 를 (b) 에서 뺀 것이다.** 그것은 PDF 를 실제로 읽고
# 「라벨동반 산문 조각이 0개」 라고 판정한 결과(표·차트 전용 문서)이고, 그런 행은 1차 축이
# `found` 로 **살아 있다**. 2026-09-14 실측으로 posted 16사 중 8사가 그 모양이라, 여기 넣으면
# 정상 8사가 한꺼번에 거짓 발화한다. `not_applicable` 은 반대로 「문서가 애초에 판정 대상이
# 아니었다」 는 뜻이라 1차 축도 같이 죽어 있다 — 가르는 선은 거기다.
#
# severity 는 **YELLOW** 다(빌더 exit code 를 안 바꾼다). 근거 셋:
#   1. RED 로 걸면 기존 `test_skip_verdicts_are_yellow_not_red` 와 정면으로 모순된다.
#   2. UH-25 가 적은 구조적 긴장 — T&D 가 비-PDF 인 이유는 종전 TDnet URL 이 만료돼
#      `JP_SOURCE_EXPIRING_HOST` 를 피하려고 상설 IR 페이지로 옮긴 것이다. 빌더 RED 는
#      **데이터 오류가 아닌 출처선택 문제로 정상 재빌드를 막는다**(UH-5·UH-9 선례).
#   3. 이빨은 조정치 축과 **같은 자리**에 둔다 — 배포본 증거에 면제 없는 발화가 남아 있으면
#      push 묶음이 막는다(tests/test_jp_source_gate.py::
#      test_live_esr_evidence_has_no_unexempted_unverified_value). UH-25 를 "비대칭" 이라
#      부른 근거가 skip 축에 그 대조가 없다는 것이었으므로, 대칭으로 맞추는 것이 해소다.
#: (b) 축. `abstain_no_prose` 와 **다르게 다룬다** — 위 주석의 실측이 가르는 선이다.
ESR_ADJUSTED_NOT_JUDGED = ("not_applicable",)


def unverified_value_reasons(row: dict) -> list[str]:
    """`JP_ESR_UNVERIFIED_VALUE` 의 판정식 **정본**. 발화 사유를 사람이 읽는 문장으로 돌려준다.

    빌더도 push 묶음의 라이브 대조 테스트도 **이 함수 하나**를 부른다. 판정식을 테스트에
    재타이핑하면 게이트와 테스트가 서로 다른 룰을 검증하게 된다(상관행렬 재타이핑 금지와
    같은 이유). 순수 함수라 네트워크도 파일도 필요 없다.

    빈 리스트 = 최소 한 축은 실제로 판정됐다. 비어 있지 않으면 그 행의 화면값은 **어떤 원문
    대조도 받지 않았다**. `adjusted_verdict` 키 자체가 없는 경우는 여기서 판정하지 않는다 —
    그건 `_adjusted_figure_check` 가 이미 `JP_SOURCE_EVIDENCE_INCOMPLETE` 로 RED 를 낸다.
    """
    reasons: list[str] = []
    verdict = str(row.get("verdict") or "").strip()
    if verdict in ESR_VERDICT_YELLOW:
        reasons.append(
            f"1차 축(JP_ESR_NOT_IN_SOURCE)이 verdict={verdict} 로 판정을 건너뛰었다"
        )
    adjusted = str(row.get("adjusted_verdict") or "").strip()
    if "adjusted_verdict" in row and adjusted in ESR_ADJUSTED_NOT_JUDGED:
        reasons.append(
            f"조정치 축(JP_ESR_ADJUSTED_FIGURE)이 adjusted_verdict={adjusted} 로 기권했다"
            " (문서가 PDF 가 아니거나 받지 못해 판정 대상이 아니었다)"
        )
    return reasons


_EXCEPTION_REQUIRED_KEYS = ("rule", "company_jp", "field", "reason", "owner_approved_on")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CHECK_SOURCES_CMD = (
    "python3 J-ESR/check_source_urls.py --all --out J-ESR/source_url_health.json"
)
CHECK_ESR_CMD = (
    "python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json"
)


def _norm_pct(value) -> str | None:
    """`268` / `268.0` / `"268%"` → `"268"`. 못 읽으면 None.

    census(문자열) · 마스터 record(float) · 증거 파일(문자열)이 같은 값을 서로 다른 표기로
    들고 있어도 같은 값으로 읽혀야 한다. 여기서 갈라지면 "증거는 있는데 못 찾았다" 는
    거짓 RED 가 난다.
    """
    if value is None:
        return None
    s = str(value).strip().rstrip("%").strip()
    if not s:
        return None
    try:
        return "%g" % float(s)
    except ValueError:
        return None


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


def _load_evidence_envelope(path: Path, census_max: str | None, rerun_cmd: str):
    """증거 파일 한 개의 **봉투**를 읽고 신선도를 잰다. 반환 (rows|None, checked_at, scope, errors).

    `source_url_health.json`(출처 생존)과 `esr_in_source_health.json`(값이 문서 안에 있나)은
    **같은 봉투**(`checked_at`/`scope`/`rows`)를 쓴다. 그래서 신선도 검사가 한 벌이면 된다 —
    두 벌로 적어 두면 한쪽만 고쳐져도 아무도 모른다.

    *** 이 함수가 두 룰쌍의 이빨을 전부 쥐고 있다. ***
    `JP_SOURCE_URL_DEAD` 도 `JP_ESR_NOT_IN_SOURCE` 도 **박제된 증거를 읽을 뿐**이라, 증거가
    낡으면 판정도 같이 낡는다. 즉 둘 다 `JP_SOURCE_EVIDENCE_STALE` 과 한 쌍이지 독립된 룰이
    아니다. 신선도 검사를 느슨하게 만들면 두 룰이 동시에 조용히 죽는다.
    """
    errors: list[str] = []
    if not path.exists():
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] 출처 점검 증거가 없다: {path.name} —"
            f" census 를 고치기 전에 먼저 돌려라: {rerun_cmd}"
        )
        return None, None, None, errors
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] {path.name} 을 읽을 수 없다:"
            f" {type(exc).__name__}: {exc}"
        )
        return None, None, None, errors
    if not isinstance(loaded, dict):
        errors.append(f"[JP_SOURCE_EVIDENCE_STALE] {path.name}: 최상위가 객체가 아니다")
        return None, None, None, errors

    scope = str(loaded.get("scope") or "").strip()
    if scope != "all":
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] {path.name}: scope={scope!r} 이다."
            f" 'all' 이 아닌 좁은 범위 산출로 게이트를 통과시키면 검사한 척만 하는 것이다 —"
            f" 다시 돌려라: {rerun_cmd}"
        )
    checked_raw = str(loaded.get("checked_at") or "").strip()
    checked_at = checked_raw[:10]
    if not _DATE_RE.match(checked_at):
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] {path.name}: checked_at 을 못 읽는다"
            f" {checked_raw!r} (YYYY-MM-DD... 여야 한다)"
        )
        checked_at = None
    elif census_max and checked_at < census_max:
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] 증거가 census 보다 낡았다:"
            f" {path.name}.checked_at={checked_raw} < census 최신 checked_at"
            f"={census_max}. census 를 고쳤는데 점검을 다시 안 돌렸다는 뜻이다 —"
            f" {rerun_cmd}"
        )

    rows = loaded.get("rows")
    if not isinstance(rows, list):
        errors.append(
            f"[JP_SOURCE_EVIDENCE_STALE] {path.name}: 'rows' 가 배열이 아니다"
            f" ({type(rows).__name__})"
        )
        rows = None
    return rows, checked_at, scope, errors


def _unverified_value_check(company: str, url: str, pct: str, row: dict,
                            exempt: set, notes: list[str], seen: dict) -> list[str]:
    """`JP_ESR_UNVERIFIED_VALUE` — 이 행의 화면값이 **어떤 축으로든 실제로 판정됐나**(UH-25).

    위 두 룰은 각자 자기 축의 결론을 본다. 이 룰은 그 위에서 **"판정이 있었나"** 만 본다 —
    비-PDF 출처는 두 축을 동시에 침묵시키는데, 종전에는 그 침묵이 exit code 에도 요약에도
    안 남아서 화면값이 무검증으로 라이브에 올라갔다(T&D 222%, 2026-09-13).

    판정식 정본은 `unverified_value_reasons()` — 여기서도 push 묶음의 라이브 테스트에서도
    같은 함수를 부른다. severity 는 YELLOW(면제 가능, 셀 단위)이고, 이빨은 배포본 증거를
    대조하는 push 묶음 테스트가 쥔다. 근거는 ESR_ADJUSTED_NOT_JUDGED 위 주석 §severity.

    `seen` 에 판정/미판정 수를 누적해 요약이 인쇄한다 — **세지 않으면 사각이 된다**.
    """
    reasons = unverified_value_reasons(row)
    if not reasons:
        seen["judged"] = seen.get("judged", 0) + 1
        return []
    seen["unverified"] = seen.get("unverified", 0) + 1
    if ("JP_ESR_UNVERIFIED_VALUE", company, "source_url") in exempt:
        seen["exempt"] = seen.get("exempt", 0) + 1
        notes.append(f"[source-gate] 면제 적용 JP_ESR_UNVERIFIED_VALUE · {company}")
        return []
    notes.append(
        f"[source-gate/YELLOW] JP_ESR_UNVERIFIED_VALUE · {company} esr={pct}"
        f" — 이 화면값은 원문 대조를 **한 축도 받지 않았다**: {' / '.join(reasons)}."
        f" 1차 출처를 PDF 등 판정 가능한 문서로 바꾸거나, 정당하게 비-PDF 밖에 없으면"
        f" owner 가 J-ESR/jp_source_exceptions.json 에 등재해야 한다: {url}"
    )
    return []


def _adjusted_figure_check(company: str, url: str, pct: str, row: dict, path: Path,
                           exempt: set, notes: list[str], seen: dict) -> list[str]:
    """`JP_ESR_ADJUSTED_FIGURE` — 화면값이 **그 문서에서 우리가 싣겠다고 한 정의의 값인가**.

    증거 행의 `adjusted_verdict` 만 읽는다(판정은 수집기가 한다). 세 가지를 fail-closed 로 건다.

      · 필드가 아예 없다      → RED(EVIDENCE_INCOMPLETE). 옛 수집기로 만든 증거라는 뜻이고,
                                없는 것을 통과로 읽으면 이 축이 **조용히 사라진다**.
      · 모르는 값이다          → RED. SKIP 으로 넘기면 그 행은 아무 검사도 안 받는다.
      · adjusted_alt/only      → YELLOW(면제 가능). 메시지에 한정어와 **대안값**을 같이 찍는다.

    `seen` 에 분류별 개수를 누적해 요약이 인쇄한다 — 기권은 세지 않으면 사각이 된다.
    """
    errors: list[str] = []
    if "adjusted_verdict" not in row:
        seen["missing"] = seen.get("missing", 0) + 1
        return [
            f"[JP_SOURCE_EVIDENCE_INCOMPLETE] {company} 의 증거 행에 adjusted_verdict 가 없다"
            f" — {path.name} 이 조정치 축(JP_ESR_ADJUSTED_FIGURE)을 돌리지 않은 옛 산출이다."
            f" 필드가 없는 것을 통과로 읽으면 이 축이 조용히 사라진다 — 다시 돌려라: {CHECK_ESR_CMD}"
        ]
    verdict = str(row.get("adjusted_verdict") or "").strip()
    seen[verdict] = seen.get(verdict, 0) + 1
    if verdict in ESR_ADJUSTED_PASS or verdict in ESR_ADJUSTED_ABSTAIN:
        return errors
    if verdict in ESR_ADJUSTED_YELLOW:
        if ("JP_ESR_ADJUSTED_FIGURE", company, "source_url") in exempt:
            notes.append(f"[source-gate] 면제 적용 JP_ESR_ADJUSTED_FIGURE · {company}")
            return errors
        quals = row.get("adjusted_qualifiers") or []
        alts = row.get("adjusted_alternatives") or []
        if alts:
            alt_txt = " · ".join(f"{a.get('pct')}%(p{a.get('page')})" for a in alts)
            tail = (f" 같은 문서에 **한정어 없는 대안값 {alt_txt} 가 있다** —"
                    f" 어느 쪽이 헤드라인인지 원문에서 확인하고 값을 고쳐라")
        else:
            tail = (" 한정어 없는 대안값은 그 문서에 없다 — 사람이 원문을 열어"
                    " 이 값이 정말 헤드라인인지 확인해야 한다")
        notes.append(
            f"[source-gate/YELLOW] JP_ESR_ADJUSTED_FIGURE · {company} esr={pct}"
            f" — 화면값이 나오는 ESR 라벨동반 조각 {row.get('adjusted_frags')}개가"
            f" **전부** 한정어 {quals} 를 달고 있다.{tail}."
            f" 근거: {str(row.get('adjusted_evidence') or '')[:200]} · {url}"
        )
        return errors
    return [
        f"[JP_ESR_ADJUSTED_FIGURE] {company} 의 adjusted_verdict 를 모르겠다 {verdict!r}."
        f" 아는 값: {sorted(ESR_ADJUSTED_PASS + ESR_ADJUSTED_YELLOW + ESR_ADJUSTED_ABSTAIN)}"
    ]


def _esr_in_source_check(
    posted_rows: list[tuple[str, str, str | None]],
    rows: list,
    path: Path,
    exempt: set,
    notes: list[str],
    adjusted_seen: dict | None = None,
    unverified_seen: dict | None = None,
) -> list[str]:
    """`JP_ESR_NOT_IN_SOURCE` — 화면값이 1차 출처 문서 **안에** 있나.

    2026-09-12 사고의 東京海上HD 238% 는 어느 1차 문서에도 없는 2차보도 인용값이었고,
    MS&AD 의 출처는 ESR 이 한 줄도 없는 합병 보도자료였다. URL 은 둘 다 살아 있었으므로
    `JP_SOURCE_URL_DEAD`·`JP_SOURCE_EXPIRING_HOST` 로는 못 잡는다.

    판정은 네트워크가 필요하므로 선행 단계(check_esr_in_source.py)가 문서를 열어 박제하고
    이 함수는 **박제만 읽는다**(빌드는 완전 오프라인). 증거 신선도는 위 봉투 검사가 쥔다.

    증거 행의 키는 **(url, esr_pct)** 다. url 만으로 잡으면 census 값만 바꾸고 수집기를
    다시 안 돌린 상태가 옛 값의 `found` 를 그대로 물려받아 통과한다 — 그게 정확히
    2026-09-12 의 사고 모양이다.

    이 룰이 **못 잡는 것**(설계상의 한계, 숨기지 말 것): 문서 안에 실재하지만 **다른 정의**의
    값(かんぽ 220% = 「大量解約リスクを除いた場合」 조정치)은 여기서 `found` 로 통과한다.
    그 축은 `JP_ESR_ADJUSTED_FIGURE`(UH-21, 2026-09-13 배선)가 같은 증거 행에서 잡는다 —
    `_adjusted_figure_check` 를 **RED 가 아닌 모든 행에 대해** 이어서 부른다.
    """
    errors: list[str] = []
    adjusted_seen = {} if adjusted_seen is None else adjusted_seen
    unverified_seen = {} if unverified_seen is None else unverified_seen
    by_key: dict[tuple[str, str], dict] = {}
    by_url: dict[str, list[dict]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        by_url.setdefault(url, []).append(row)
        pct = _norm_pct(row.get("esr_pct"))
        if pct is not None:
            by_key[(url, pct)] = row

    for company, url, pct in posted_rows:
        if pct is None:
            # esr_pct 를 수로 못 읽는 상태는 self_check 의 범위 룰이 이미 RED 로 잡는다.
            continue
        row = by_key.get((url, pct))
        if row is None:
            seen = sorted({str(_norm_pct(r.get("esr_pct"))) for r in by_url.get(url, [])})
            detail = (f" 이 URL 은 {seen} 에 대해서만 점검됐다" if seen
                      else " 이 URL 은 한 번도 점검된 적이 없다")
            errors.append(
                f"[JP_SOURCE_EVIDENCE_INCOMPLETE] {company} 의 (source_url, esr_pct={pct})"
                f" 조합이 {path.name} 에 없다 —{detail}."
                f" 값이나 출처를 고쳤으면 수집기를 **다시** 돌려라: {CHECK_ESR_CMD}"
            )
            continue
        verdict = str(row.get("verdict") or "").strip()
        where = f"p{row.get('page')}" if row.get("page") else "?"
        # UH-25. **verdict 분기보다 먼저, 회사·verdict 필터 없이** 전 행에 돈다. 아래 분기들은
        # 각자 자기 축의 결론을 보는데, 이 룰은 "판정이 있었나" 를 보므로 어느 분기에 걸어도
        # 그 분기에 안 들어오는 행은 순회조차 안 하게 된다 — 이 저장소의 반복 사고 모양이다.
        errors.extend(_unverified_value_check(company, url, pct, row, exempt,
                                              notes, unverified_seen))
        if verdict in ESR_VERDICT_PASS:
            # found 라고 끝이 아니다 — "그 숫자가 있다" 와 "그 정의의 숫자다" 는 다른 축이다.
            errors.extend(_adjusted_figure_check(company, url, pct, row, path, exempt,
                                                 notes, adjusted_seen))
            continue
        if verdict in ESR_VERDICT_YELLOW:
            notes.append(
                f"[source-gate/YELLOW] JP_ESR_NOT_IN_SOURCE · {company} esr={pct}"
                f" — {verdict}: {str(row.get('evidence') or '')[:120]}"
            )
            errors.extend(_adjusted_figure_check(company, url, pct, row, path, exempt,
                                                 notes, adjusted_seen))
            continue
        if verdict in ESR_VERDICT_UNJUDGED:
            errors.append(
                f"[JP_SOURCE_EVIDENCE_INCOMPLETE] {company} 의 출처를 수집기가 받지 못해"
                f" **판정하지 못했다**(verdict={verdict}). 판정 없는 행을 통과시키면"
                f" 네트워크 사고가 검증 통과로 둔갑한다 — 다시 돌려라: {CHECK_ESR_CMD}"
            )
            continue
        if verdict in ESR_VERDICT_RED:
            if ("JP_ESR_NOT_IN_SOURCE", company, "source_url") in exempt:
                notes.append(f"[source-gate] 면제 적용 JP_ESR_NOT_IN_SOURCE · {company}")
                continue
            errors.append(
                f"[JP_ESR_NOT_IN_SOURCE] {company} 의 화면값 {pct}% 가 1차 출처 문서 안에 없다"
                f"({row.get('pages')}페이지 전수, ESR 라벨 근처 미검출). 2차보도 인용값이거나"
                f" 출처가 다른 문서다 — 원문을 열어 값이나 URL 을 고쳐라: {url}"
            )
            continue
        # 모르는 verdict. SKIP 으로 넘기면 그 행은 아무 검사도 안 받는다.
        errors.append(
            f"[JP_ESR_NOT_IN_SOURCE] {company} 의 증거 verdict 를 모르겠다 {verdict!r}"
            f" ({where}). 아는 값: {sorted(ESR_VERDICT_PASS + ESR_VERDICT_RED + ESR_VERDICT_YELLOW + ESR_VERDICT_UNJUDGED)}"
        )
    return errors


def source_gate_check(
    records: list[dict],
    census_rows: list[dict],
    *,
    health_path: Path | None = None,
    esr_health_path: Path | None = None,
    exceptions_path: Path | None = None,
    today: str | None = None,
    verbose: bool = True,
) -> list[str]:
    """출처 게이트(`SOURCE_RULE_IDS`). 반환된 문자열은 그대로 self_check 의 errors 로 흘러
    exit 1 이 된다. `notes` 로만 나가는 YELLOW 는 exit code 를 바꾸지 않는다.

    scope = census `posted` 행 = `jesr_master.json` records ⊇ `jp/jesr_esr.json` records.
    (부모-자회사 dedup 이 켜져도 마스터 쪽이 상위집합이라 검사가 더 엄해지지, 느슨해지지 않는다.)

    - `JP_SOURCE_EXPIRING_HOST`     source_url netloc 이 jesr_http.EXPIRING_HOSTS 면 RED
    - `JP_SOURCE_URL_DEAD`          증거 파일이 그 URL 을 dead(404/410)로 기록했으면 RED
    - `JP_ESR_NOT_IN_SOURCE`        화면값이 그 문서 안에 없으면 RED (증거: esr_in_source_health)
    - `JP_ESR_ADJUSTED_FIGURE`      화면값이 그 문서의 **조건부 조정치**로만 나오면 YELLOW
                                    (같은 증거 행의 `adjusted_verdict`. 필드 부재·모르는 값은 RED)
    - `JP_ESR_UNVERIFIED_VALUE`     위 두 축이 **둘 다 판정을 안 했으면** YELLOW (UH-25).
                                    verdict=skip_* 또는 adjusted_verdict=not_applicable.
                                    이빨은 push 묶음의 라이브 증거 대조 테스트가 쥔다.
    - `JP_SOURCE_EVIDENCE_STALE`    증거 파일 부재·scope≠all·census 보다 낡음이면 RED (**두 파일 다**)
    - `JP_SOURCE_EVIDENCE_INCOMPLETE`  posted 행이 증거에 아예 없으면 RED (**두 파일 다**)
    """
    health_path = SOURCE_HEALTH_PATH if health_path is None else health_path
    esr_health_path = ESR_HEALTH_PATH if esr_health_path is None else esr_health_path
    errors: list[str] = []
    exempt, exc_errors, notes = load_source_exceptions(exceptions_path, today=today)
    errors.extend(exc_errors)

    expiring_hosts = {h.lower() for h in jesr_http.EXPIRING_HOSTS}
    # (company_jp, url, 정규화 esr_pct). esr_pct 는 **화면에 실리는 record 값**에서 딴다 —
    # census 원문이 아니라 사용자가 보는 값을 검사해야 불변식 1번(게이트가 검사하는 파일 =
    # 사용자가 보는 파일)이 닫힌다.
    posted_urls: list[tuple[str, str, str | None]] = []
    for rec in records:
        company = (rec.get("company_jp") or "").strip() or "<이름없음>"
        url = (rec.get("source_url") or "").strip()
        if not url:
            continue  # 빈 source_url 은 위쪽 self_check 의 https 룰이 이미 RED 로 잡는다
        posted_urls.append((company, url, _norm_pct(rec.get("esr_pct"))))
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

    # --- 증거 1: 출처 URL 생존(check_source_urls.py) -------------------------
    rows, checked_at, scope, ev_errors = _load_evidence_envelope(
        health_path, census_max, CHECK_SOURCES_CMD)
    errors.extend(ev_errors)
    if rows is not None:
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
        for company, url, _pct in posted_urls:
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

    # --- 증거 2: 화면값이 그 문서 안에 있나(check_esr_in_source.py) -----------
    # 같은 봉투를 쓰므로 신선도·범위 검사는 위와 **같은 함수**가 잰다. 증거가 낡으면
    # JP_ESR_NOT_IN_SOURCE 도 같이 낡는다 — 한 쌍이지 독립된 룰이 아니다.
    esr_rows, esr_checked_at, esr_scope, esr_ev_errors = _load_evidence_envelope(
        esr_health_path, census_max, CHECK_ESR_CMD)
    errors.extend(esr_ev_errors)
    adjusted_seen: dict[str, int] = {}
    unverified_seen: dict[str, int] = {}
    if esr_rows is not None:
        errors.extend(_esr_in_source_check(posted_urls, esr_rows, esr_health_path, exempt,
                                           notes, adjusted_seen, unverified_seen))

    if verbose:
        for note in notes:
            print(note)
        # 조정치 축은 **분류별로 센다**. "발화 0" 만 찍으면 몇 사가 판정 대상이 아니었는지
        # (기권)가 사라져 "룰이 0이라고 말한다" 가 "그 축이 깨끗하다" 로 읽힌다.
        adj = " ".join(f"{k}={adjusted_seen.get(k, 0)}"
                       for k in ESR_ADJUSTED_PASS + ESR_ADJUSTED_YELLOW + ESR_ADJUSTED_ABSTAIN)
        print(
            f"[source-gate] posted {len(posted_urls)}건 · expiring-host 검사 완료 ·"
            f" 증거 {health_path.name} checked_at={checked_at or '?'} scope={scope!r}"
            f" · 증거 {esr_health_path.name} checked_at={esr_checked_at or '?'}"
            f" scope={esr_scope!r}"
            f" · census 최신 checked_at={census_max or '?'} · 면제 {len(exempt)}건"
            f" · YELLOW {sum(1 for n in notes if '/YELLOW]' in n)}건"
            f" · RED {len(errors)}건"
        )
        print(f"[source-gate] 조정치 축(JP_ESR_ADJUSTED_FIGURE) 판정 분포: {adj}")
        # UH-25 remedy ②. 종전에는 조정치 축만 분포를 찍고 **1차 축은 안 찍었다** — 그래서
        # 「기권은 세지 않으면 사각이 된다」 를 한쪽 축에만 적용한 꼴이었다. 두 축을 대칭으로
        # 인쇄한다: 분포가 skip_* 로 쏠려 있는데 RED 0 이면 그건 깨끗한 게 아니라 안 본 것이다.
        prim_counts: dict[str, int] = {}
        if esr_rows is not None:
            by_k = {(str(r.get("url") or "").strip(), _norm_pct(r.get("esr_pct"))): r
                    for r in esr_rows if isinstance(r, dict)}
            for _c, _u, _p in posted_urls:
                _r = by_k.get((_u, _p))
                _v = str((_r or {}).get("verdict") or "").strip() or "<행없음>"
                prim_counts[_v] = prim_counts.get(_v, 0) + 1
        prim = " ".join(f"{k}={prim_counts[k]}" for k in sorted(prim_counts)) or "없음"
        print(f"[source-gate] 1차 축(JP_ESR_NOT_IN_SOURCE) 판정 분포: {prim}")
        print(
            f"[source-gate] 값검증 축(JP_ESR_UNVERIFIED_VALUE) census:"
            f" 판정됨={unverified_seen.get('judged', 0)}"
            f" 무검증={unverified_seen.get('unverified', 0)}"
            f" (그중 면제={unverified_seen.get('exempt', 0)})"
        )
    return errors


# ---------------------------------------------------------------------------
# census <-> 마스터 <-> 배포 항등식 (2026-09-13, TODO_jp(27) ②)
#
# 왜: 종전 self-check 의 회사 수 검사는 `len(records) != 15` 였다. 10월 말 J-ICS 공시기한
# 직후 라운드에서 census 의 posted 가 15사 -> 60~70사로 한꺼번에 뒤집히면(현재 not_yet 62사)
# 그 리터럴은 **정상 데이터를 RED 로 막는다** — 게이트가 사실이 아니라 옛 숫자를 지키는 상태다.
# 이 저장소는 2026-08-29 에 같은 형태로 데였다: 게이트 세 곳이 각자 분기 목록을 리터럴로
# 들고 있어서 2026.2Q 를 배포한 날 그 분기를 **순회조차 안 했다**(RED=0 = "안 봤다").
# 그때 남은 것이 `tests/test_quarter_horizon.py` 이고 거기 적힌 교훈이 그대로 여기 적용된다:
# "하드코딩 자체가 재발 구조다."
#
# 그래서 기대값을 census 에서 파생시키되 **검사를 없애지는 않는다**. 숫자가 아니라 항등식:
#
#     census posted 행 수 == _meta.census.posted == len(마스터 records)
#                          == len(배포 records) + len(excluded)
#
# 두 가지를 더 지킨다:
#  · **수가 아니라 집합으로 건다.** 한 건 빠지고 한 건 중복되면 수는 그대로 맞는다.
#  · **0 으로 닫히는 등식은 등식이 아니다.** posted 가 0 이면 산수는 전부 맞고 화면만 빈다.
#    status 열 이름이 바뀌거나 census 가 잘리면 정확히 그 모양이 되므로 posted == 0 이 RED 다.
# ---------------------------------------------------------------------------


def _exception_reason_by_key(path: Path | None = None) -> dict[tuple[str, str, str], str | None]:
    """`(rule, company_jp, field) -> reason` 텍스트만 뽑는다. **검증은 하지 않는다** —
    유효성(필수 키·rule id·날짜 형식·만료)은 이미 `load_source_exceptions()` 가 유일하게 쥐고
    있고, 그 결과(검증된 `exempt` 키 집합)와 여기서 교집합을 내는 쪽(호출부)이 유효성 재검사를
    대신한다. 여기서 같은 검증을 다시 적으면 두 벌의 판정식이 생긴다."""
    path = SOURCE_EXCEPTIONS_PATH if path is None else path
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    entries = data.get("exceptions") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return {}
    out: dict[tuple[str, str, str], str | None] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = (
            str(entry.get("rule") or "").strip(),
            str(entry.get("company_jp") or "").strip(),
            str(entry.get("field") or "").strip(),
        )
        out[key] = str(entry.get("reason") or "").strip() or None
    return out


def compute_value_verified(
    records: list[dict],
    *,
    esr_health_path: Path | None = None,
    exceptions_path: Path | None = None,
    today: str | None = None,
) -> dict[str, dict]:
    """`value_verified` 계약(2026-09-14, UH-25 화면축, designer 합의) -- posted record 마다
    {"state": "verified"|"unverified"|"exempt", "reason": null|str}.

    판정은 **재타이핑하지 않는다** -- 게이트가 이미 쓰는 두 정본을 그대로 부른다:
      - 판정식   = `unverified_value_reasons()` (JP_ESR_UNVERIFIED_VALUE 의 유일한 정의)
      - 면제 조회 = `load_source_exceptions()` (jp_source_exceptions.json, 유효성 검증 포함)
    이 함수는 `main()`이 `self_check()`(source_gate_check 포함, 증거 신선도 RED 게이트)를
    통과한 **뒤**에만 불린다 -- 그래서 여기서는 증거 파일의 신선도를 재검사하지 않는다
    (신선도가 깨졌으면 이미 exit 1 로 멈춰 있다).

    반환: {company_jp: {"state", "reason"}}. esr_pct/source_url 이 없어 애초에 대조 불가한
    행, 증거 파일 자체가 없는 행은 모두 "unverified"로 떨어진다(추측 금지 -- 빈 칸 대신
    이유를 남긴다).
    """
    esr_health_path = ESR_HEALTH_PATH if esr_health_path is None else esr_health_path
    exceptions_path = SOURCE_EXCEPTIONS_PATH if exceptions_path is None else exceptions_path

    exempt, _exc_errors, _notes = load_source_exceptions(exceptions_path, today=today)
    reason_by_key = _exception_reason_by_key(exceptions_path)

    out: dict[str, dict] = {}

    def _mark_all_unverified(reason: str) -> None:
        for rec in records:
            company = (rec.get("company_jp") or "").strip()
            out[company] = {"state": "unverified", "reason": reason}

    if not esr_health_path.exists():
        _mark_all_unverified(f"{esr_health_path.name} 증거 파일이 없다")
        return out
    try:
        loaded = json.loads(esr_health_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _mark_all_unverified(f"{esr_health_path.name} 을 읽을 수 없다: {type(exc).__name__}: {exc}")
        return out
    rows = loaded.get("rows") if isinstance(loaded, dict) else None
    by_key: dict[tuple[str, str], dict] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url") or "").strip()
            pct = _norm_pct(row.get("esr_pct"))
            if url and pct is not None:
                by_key[(url, pct)] = row

    for rec in records:
        company = (rec.get("company_jp") or "").strip()
        url = (rec.get("source_url") or "").strip()
        pct = _norm_pct(rec.get("esr_pct"))
        if not url or pct is None:
            out[company] = {
                "state": "unverified",
                "reason": "source_url 또는 esr_pct 가 없어 증거와 대조할 수 없다",
            }
            continue
        row = by_key.get((url, pct))
        if row is None:
            out[company] = {
                "state": "unverified",
                "reason": f"(source_url, esr_pct) 조합이 {esr_health_path.name} 에 없다"
                f" -- 수집기를 다시 돌려야 한다: {CHECK_ESR_CMD}",
            }
            continue
        reasons = unverified_value_reasons(row)
        if not reasons:
            out[company] = {"state": "verified", "reason": None}
            continue
        key = ("JP_ESR_UNVERIFIED_VALUE", company, "source_url")
        if key in exempt:
            out[company] = {
                "state": "exempt",
                "reason": reason_by_key.get(key) or "; ".join(reasons),
            }
        else:
            out[company] = {"state": "unverified", "reason": "; ".join(reasons)}
    return out


def check_census_row_shape(census_rows: list[dict]) -> list[str]:
    """posted 행이 헤더와 같은 열 수인가 — CSV **구조** 자체의 검사.

    `csv.DictReader` 는 열이 남으면 `None` 키에 흘려 담고 모자라면 `None` 값으로 채운다.
    둘 다 조용하다: 따옴표 없는 쉼표 하나로 그 행의 마지막 열이 첫 쉼표에서 **잘린 채**
    읽히는데 아무도 모른다. 실측(2026-09-13): census 14행 第一ライフグループ 이 16열 헤더에
    18열이고 notes 가 잘려 있다 — 지금은 `not_yet` 이라 화면에 안 나가지만 10/31 에 posted 로
    뒤집히면 그대로 실린다(`jesr_sources_2026Q1.csv` 6행 · `jp_insurers.csv` 3·14·16·57행도
    같은 모양이지만 이 빌더가 그 파일들에서 읽는 열은 넘침 앞쪽이라 영향이 없다).

    **왜 posted 행만 보나.** 화면에 나가는 행만 이 빌더의 책임이고, 지금 census 를 고칠 수
    있는 것은 jp 레인이다(티켓 발주함). 전 행을 RED 로 하면 오늘 당장 아무도 push 를 못 하는데
    오늘 그 행은 아무 화면에도 안 나간다. 대신 그 행이 posted 로 뒤집히는 순간 RED 다.

    쉼표가 **중간 열**에 들어가면 뒤 열이 통째로 밀리는데, 그건 이 검사 말고도
    JP_CENSUS_STATUS(모르는 status) · esr_pct 범위 · source_url https · as_of 검사가 같이 잡는다.
    """
    errors: list[str] = []
    for row in census_posted_rows(census_rows):
        company = (row.get("company_jp") or "").strip() or "<이름없음>"
        if None in row:
            extra = row[None]
            errors.append(
                f"[JP_CENSUS_SHAPE] {company}: CSV 열이 헤더보다 {len(extra)}개 많다 —"
                f" 따옴표 없는 쉼표 때문에 마지막 열이 잘려서 읽힌다. 넘친 조각: {extra!r}."
                f" 해당 셀을 \"...\" 로 감싸라"
            )
        short = sorted(k for k, v in row.items() if k is not None and v is None)
        if short:
            errors.append(
                f"[JP_CENSUS_SHAPE] {company}: CSV 열이 모자라 {short} 이 아예 없다"
                f"(빈 문자열이 아니라 결측) — 열을 채워라"
            )
    return errors


def check_preliminary_vocabulary(census_rows: list[dict]) -> list[str]:
    """posted 행의 `preliminary` 명시값이 아는 어휘인가.

    빈 값은 정상이다(명시 안 함 -> PRELIM_KEYWORDS 폴백). 문제는 **모르는 값**이다:
    `preliminary=Y` 라고 적으면 build() 의 if/elif 어느 쪽에도 안 걸려 조용히 폴백으로
    떨어지고, 폴백 키워드가 못 잡으면 속보치가 확정치로 화면에 실린다. 결측(빈칸)과
    오독(모르는 값)은 다르게 다뤄야 한다 — 후자는 RED.
    2026-09-13 かんぽ 사고가 정확히 '속보인데 확정치로 표시' 였고, 10/31 에 62행이 사람 손으로
    채워진다는 것이 이 검사를 지금 거는 이유다.
    """
    known = set(PRELIM_TRUE) | set(PRELIM_FALSE)
    errors: list[str] = []
    for row in census_posted_rows(census_rows):
        raw = (row.get("preliminary") or "").strip()
        if raw and raw.lower() not in known:
            company = (row.get("company_jp") or "").strip() or "<이름없음>"
            errors.append(
                f"[JP_CENSUS_PRELIM] {company}: preliminary={raw!r} 는 모르는 값이라"
                f" 조용히 키워드 폴백으로 떨어진다(= 속보 표시가 사라질 수 있다)."
                f" 아는 값: {', '.join(sorted(known))} / 빈칸은 '명시 안 함' 으로 정상"
            )
    return errors


def check_census_identity(out: dict, census_rows: list[dict]) -> list[str]:
    """census 파일 <-> `_meta.census` <-> `records` 의 항등식(위 블록 주석 참조)."""
    errors: list[str] = []
    recs = out["records"]
    meta = out["_meta"]["census"]

    unknown = sorted({census_status(r) for r in census_rows} - set(CENSUS_STATUSES))
    if unknown:
        errors.append(
            f"[JP_CENSUS_STATUS] 모르는 fy2025_esr_status {unknown} —"
            f" 세 카운터({', '.join(CENSUS_STATUSES)}) 어디에도 안 잡혀 census 요약에서 사라진다."
            f" 오타면 고치고, 새 상태면 CENSUS_STATUSES 에 등재해라"
        )

    counts = census_counts(census_rows)
    missing_keys = [k for k in ("total",) + CENSUS_STATUSES if k not in meta]
    if missing_keys:
        errors.append(f"[JP_CENSUS_COUNT] _meta.census 에 키가 없다: {missing_keys}")
    else:
        for key in ("total",) + CENSUS_STATUSES:
            if meta[key] != counts[key]:
                errors.append(
                    f"[JP_CENSUS_COUNT] _meta.census.{key} = {meta[key]!r} 인데"
                    f" census 파일 재계수는 {counts[key]} 다"
                )
        if sum(meta[k] for k in CENSUS_STATUSES) != meta["total"]:
            errors.append(f"[JP_CENSUS_COUNT] census does not sum to total: {meta}")

    if counts[POSTED_STATUS] == 0:
        errors.append(
            "[JP_CENSUS_EMPTY] census 에 posted 행이 0 건이다 — 0 == 0 으로 닫히는 등식은"
            " 검사가 아니다. status 열 이름·값이 바뀌었는지, census 가 잘리지 않았는지 확인해라"
        )

    # 수가 아니라 집합. 한 건 빠지고 한 건 중복되면 수는 맞는다.
    want = [(r.get("company_jp") or "").strip() for r in census_posted_rows(census_rows)]
    got = [(r.get("company_jp") or "").strip() for r in recs]
    if len(got) != len(want):
        errors.append(
            f"[JP_CENSUS_RECORDS] records {len(got)}건 != census posted {len(want)}건."
            f" 기대값은 census 에서 파생한다 — 이 수를 코드에 다시 적지 마라"
        )
    missing = sorted(set(want) - set(got))
    extra = sorted(set(got) - set(want))
    if missing:
        errors.append(f"[JP_CENSUS_RECORDS] census 는 posted 인데 records 에 없다: {missing}")
    if extra:
        errors.append(f"[JP_CENSUS_RECORDS] records 에 있는데 census posted 가 아니다: {extra}")

    errors.extend(check_census_row_shape(census_rows))
    errors.extend(check_preliminary_vocabulary(census_rows))
    return errors


VALUE_VERIFIED_STATES = ("verified", "unverified", "exempt")


def check_value_verified(records: list[dict]) -> list[str]:
    """`value_verified` 계약을 지키는지 — 상태 어휘·reason null 규칙·필드 존재.
    판정 자체(누가 verified 인가)는 `compute_value_verified()`/`unverified_value_reasons()`
    가 정본이다 — 여기서는 **그 출력의 모양**만 검사한다(재판정 아님)."""
    errors = []
    for rec in records:
        name = rec.get("company_jp")
        vv = rec.get("value_verified")
        if not isinstance(vv, dict):
            errors.append(f"value_verified missing or not an object: {name} = {vv!r}")
            continue
        state = vv.get("state")
        reason = vv.get("reason")
        if state not in VALUE_VERIFIED_STATES:
            errors.append(f"value_verified.state unknown: {name} = {state!r}")
        if state == "verified" and reason is not None:
            errors.append(f"value_verified state=verified but reason is not null: {name} = {reason!r}")
        if state in ("unverified", "exempt") and not reason:
            errors.append(f"value_verified state={state} but reason is empty: {name}")
    return errors


def check_deploy_identity(
    master_records: list[dict],
    deploy_records: list[dict],
    excluded: list[dict],
    census_rows: list[dict],
) -> list[str]:
    """마스터 <-> 배포 <-> 제외의 항등식.

        census posted 행 수 == len(master) == len(deploy) + len(excluded)

    종전 main() 의 검사는 `len(master) - len(excluded) != len(deploy)` 한 줄이었다. census 를
    한쪽 끝에 묶지 않으면 세 수가 사이좋게 같이 틀려도 통과하고, 수만 보면 한 건 빠지고 한 건
    중복돼도 통과한다. 그래서 집합으로도 건다 — 키는 `company_en`: 하류
    `build_jesr_detail_json.py` 가 `{company_en: record}` 로 마스터를 훑고
    `attach_target_ranges` 도 company_en 으로 목표레인지를 붙인다.
    """
    errors: list[str] = []
    n_posted = len(census_posted_rows(census_rows))
    if not (n_posted == len(master_records) == len(deploy_records) + len(excluded)):
        errors.append(
            f"[JP_DEPLOY_COUNT] census posted {n_posted} == 마스터 {len(master_records)} =="
            f" 배포 {len(deploy_records)} + 제외 {len(excluded)} 이 성립하지 않는다"
        )

    def ens(rows, key="company_en"):
        return [(r.get(key) or "").strip() for r in rows]

    m, d, x = set(ens(master_records)), set(ens(deploy_records)), set(ens(excluded))
    overlap = sorted(d & x)
    if overlap:
        errors.append(f"[JP_DEPLOY_SET] 배포와 제외에 동시에 있다: {overlap}")
    lost = sorted(m - d - x)
    if lost:
        errors.append(
            f"[JP_DEPLOY_SET] 마스터에 있는데 배포에도 제외에도 없다(조용히 사라진 회사): {lost}"
        )
    ghost = sorted((d | x) - m)
    if ghost:
        errors.append(f"[JP_DEPLOY_SET] 마스터에 없는 회사가 배포/제외에 있다: {ghost}")
    return errors


def self_check(out: dict, census_rows: list[dict] | None = None) -> list[str]:
    errors = []
    recs = out["records"]
    census_rows = _read_csv(CENSUS_CSV) if census_rows is None else census_rows
    # 회사 수 기대값은 census 에서 파생한다(위 블록). 하드코딩된 15 는 2026-09-13 에 제거됐다.
    errors.extend(check_census_identity(out, census_rows))
    seen = set()
    seen_en = set()
    for rec in recs:
        name = rec["company_jp"]
        if name in seen:
            errors.append(f"duplicate company_jp: {name}")
        seen.add(name)
        # company_en 도 유일해야 한다 — 하류가 이 키로 조인하기 때문이다. 중복이면 한쪽이
        # 조용히 덮여 **다른 회사의 목표레인지·상세**가 붙는다. 2026-09-13 커밋 `6e051be`
        # (第一ネオ生命保険이 다른 회사 영문명을 달고 있었다)가 실사고였고, 그때 이 검사가
        # 없어서 게이트는 아무 말도 안 했다.
        en = (rec.get("company_en") or "").strip()
        if not en:
            errors.append(f"company_en 이 비어 있다: {name}")
        elif en in seen_en:
            errors.append(f"duplicate company_en: {en} ({name})")
        seen_en.add(en)
        e = rec["esr_pct"]
        if e is None or not isinstance(e, float) or not (ESR_PCT_MIN <= e <= ESR_PCT_MAX):
            errors.append(
                f"esr_pct out of range or not float: {name} = {e!r}"
                f" (도메인 상식선 {ESR_PCT_MIN:g}~{ESR_PCT_MAX:g}%; 벗어나면 census 를 고치지 말고"
                f" 먼저 원문을 확인해라 — 단위 오류이거나 기사가 날 사건이다)"
            )
        if rec["scope"] not in SCOPE_VALUES:
            errors.append(f"bad scope: {name} = {rec['scope']!r}")
        if rec["sector"] not in SECTOR_VALUES:
            errors.append(f"bad sector: {name} = {rec['sector']!r}")
        su = rec["source_url"]
        if not su or not su.startswith("https://"):
            errors.append(f"source_url not https: {name} = {su!r}")
        if rec["as_of"] != AS_OF_TARGET:
            errors.append(f"as_of != {AS_OF_TARGET}: {name} = {rec['as_of']!r}")
    # 출처 게이트도 같은 errors 리스트로 흘려보낸다 — main() 이 errors 가 있으면 return 1 이므로
    # 여기에 붙이는 것만으로 **실제 exit code 가 바뀐다**(배선했다 ≠ 돈다를 가르는 지점).
    errors.extend(source_gate_check(recs, census_rows))
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

    # 게이트는 census **파일을 다시 읽는다**. build() 가 이미 센 숫자를 그대로 넘겨받으면
    # 검사가 자기참조가 된다(이 저장소가 반복해서 데인 false-green 의 형태).
    census_rows = _read_csv(CENSUS_CSV)
    errors = self_check(out, census_rows)
    if errors:
        for e in errors:
            print(f"SELF-CHECK FAIL: {e}", file=sys.stderr)
        return 1

    # value_verified (2026-09-14, UH-25 화면축) -- self_check() 가 이미 source_gate_check 를
    # 통과시킨 뒤에만 계산한다(증거 신선도는 그 게이트가 RED 로 쥔다). records 는 master/deploy가
    # dedup 전까지 같은 dict 객체를 공유하므로 여기서 한 번만 붙이면 둘 다에 실린다.
    vv_map = compute_value_verified(out["records"])
    vv_counts: dict[str, int] = {}
    for rec in out["records"]:
        vv = vv_map.get((rec.get("company_jp") or "").strip(),
                        {"state": "unverified", "reason": "value_verified 매핑에 없다"})
        rec["value_verified"] = vv
        vv_counts[vv["state"]] = vv_counts.get(vv["state"], 0) + 1
    vv_errors = check_value_verified(out["records"])
    if vv_errors:
        for e in vv_errors:
            print(f"SELF-CHECK FAIL: {e}", file=sys.stderr)
        return 1

    insurer_rows = _read_csv(INSURERS_CSV)
    insurers_by_name = {
        r["company_jp"].strip(): r for r in insurer_rows if (r.get("company_jp") or "").strip()
    }
    deploy_records, excluded = apply_subsidiary_dedup(out["records"], insurers_by_name)

    deploy_errors = check_deploy_identity(out["records"], deploy_records, excluded, census_rows)
    if deploy_errors:
        for e in deploy_errors:
            print(f"SELF-CHECK FAIL: {e}", file=sys.stderr)
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
    print(f"  value_verified: {vv_counts}")
    print(f"  census: {out['_meta']['census']}")
    if excluded:
        print(f"  excluded_subsidiaries: {excluded}")
    prelim = [r['company_en'] for r in out['records'] if r['preliminary']]
    print(f"  preliminary={len(prelim)}: {prelim}")
    # next_update 는 데이터에서 파생할 수 없는 편집상의 약속이라 리터럴로 둔다. 대신 지나면
    # 말은 한다. **RED 로 하지 않는 이유**: 데이터가 하나도 안 바뀐 날짜 경계에서 빌더와
    # `tests/test_jp_deploy_matches_census.py` 가 동시에 터지는 시한폭탄이 된다.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if NEXT_UPDATE < today:
        print(
            f"  [warn] next_update={NEXT_UPDATE} 가 이미 지났다(오늘 {today}) —"
            f" 화면이 지난 날짜를 '다음 갱신' 으로 약속하고 있다. 다음 공시 기한으로 올려라."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
