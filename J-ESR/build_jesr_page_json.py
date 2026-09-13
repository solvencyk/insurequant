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

HERE = Path(__file__).resolve().parent
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
SOURCES_CSV = HERE / "jesr_sources_2026Q1.csv"
INSURERS_CSV = HERE / "jp_insurers.csv"
MASTER_OUT = HERE / "jesr_master.json"
DEPLOY_OUT = HERE.parent / "jp" / "jesr_esr.json"

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


def self_check(out: dict) -> list[str]:
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
