# -*- coding: utf-8 -*-
"""EDINET 공식 코드리스트로 `jp_insurers.csv` 의 EDINET 코드를 채우고 검증한다.

왜 (2026-09-13)
---------------
`jp_insurers.csv` 81행 중 62행이 `edinet_code=TBD` 였고, 기재돼 있던 14행도 출처가
"EDINET 회사검색" 이라고만 적혀 있었다. 키가 생긴 뒤 공식 코드리스트(11,389건)로
실측하니 **기재 13코드 중 6개가 오답**이었다 — E04979 는 SOMPOHD 가 아니라 パーク24,
E04506 은 第一生命HD 가 아니라 九州電力이다. 코드를 그대로 두면 10월 EDINET 조회가
엉뚱한 회사의 有報를 긁는다.

출처
----
https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip
(EDINETコードリスト, cp932 CSV, 1행 헤더 앞에 다운로드일 행이 하나 더 있다.)

이 리스트의 `提出者業種` 이 **有報 제출의무를 가른다**:
- `保険業` 등 실업종 = 有報 제출의무자 → EDINET 루트로 수집 가능
- `内国法人・組合（有価証券報告書等の提出義務者以外）` = EDINET 등록은 있으나 有報 없음
  → 相互会社 5사·第一生命保険·大同/太陽/ネオファースト/FWD 생명 등이 전부 여기다.
  **이 회사들의 ESR 은 EDINET 에 영원히 안 온다** — 각사 디스클로저 PDF 가 1차 출처라는
  owner 2026-09-12 판단의 기계 근거.

사용법
------
  python J-ESR/edinet_codelist.py                 # 캐시로 대조 리포트만(쓰기 없음)
  python J-ESR/edinet_codelist.py --refresh       # 코드리스트 새로 내려받고 대조
  python J-ESR/edinet_codelist.py --apply         # jp_insurers.csv 실제 갱신(확신 매칭만)

산출
----
J-ESR/raw/edinet/EdinetcodeDlInfo.csv   캐시(gitignore)
J-ESR/edinet_code_match.json            대조 결과 전량(추적 대상, 증거)
"""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import re
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402

HERE = Path(__file__).resolve().parent
CACHE_DIR = HERE / "raw" / "edinet"
CACHE_CSV = CACHE_DIR / "EdinetcodeDlInfo.csv"
INSURERS_CSV = HERE / "jp_insurers.csv"
REPORT_JSON = HERE / "edinet_code_match.json"
CODELIST_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"

COL_CODE = "ＥＤＩＮＥＴコード"
COL_NAME = "提出者名"
COL_KIND = "提出者種別"
COL_INDUSTRY = "提出者業種"
COL_LISTED = "上場区分"
COL_TICKER = "証券コード"

NON_FILER_MARK = "提出義務者以外"

# 법인격·약칭 정규화. 순서가 의미 있다(긴 것 먼저).
_DROP = ("株式会社", "相互会社", "有限会社", "合同会社", "㈱")
_ABBREV = (
    ("インシュアランスグループホールディングス", "インシュアランスグループHD"),
    ("フィナンシャルグループ", "FG"),
    ("ホールディングス", "HD"),
    ("フィナンシャルホールディングス", "FHD"),
)


def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def normalize(name: str) -> str:
    """전각/반각·법인격·약칭을 걷어낸 비교용 키."""
    s = unicodedata.normalize("NFKC", name or "").strip()
    for token in _DROP:
        s = s.replace(token, "")
    for long, short in _ABBREV:
        s = s.replace(long, short)
    s = re.sub(r"[\s・,.()（）]", "", s)
    return s.upper()


def download_codelist() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log(f"[GET] {CODELIST_URL}")
    resp = jesr_http.get(CODELIST_URL, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        member = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        CACHE_CSV.write_bytes(zf.read(member))
    log(f"[OK] {CACHE_CSV} ({CACHE_CSV.stat().st_size:,} bytes)")
    return CACHE_CSV


def load_codelist(refresh: bool = False) -> list[dict]:
    if refresh or not CACHE_CSV.exists():
        download_codelist()
    text = CACHE_CSV.read_bytes().decode("cp932", errors="replace")
    lines = text.splitlines()
    # 1행은 "ダウンロード実行日,…,件数,…" 메타행이라 버린다.
    reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
    return list(reader)


def build_index(rows: list[dict]) -> tuple[dict, dict]:
    by_ticker: dict[str, dict] = {}
    by_name: dict[str, list[dict]] = {}
    for r in rows:
        ticker = (r.get(COL_TICKER) or "").strip()
        if ticker:
            by_ticker.setdefault(ticker, r)
        by_name.setdefault(normalize(r.get(COL_NAME, "")), []).append(r)
    return by_ticker, by_name


def obligated(row: dict) -> bool:
    """有報 제출의무자인가 — 업종 라벨에 '提出義務者以外' 가 없으면 의무자."""
    return NON_FILER_MARK not in (row.get(COL_INDUSTRY) or "")


def match_one(ins_row: dict, by_ticker: dict, by_name: dict, all_rows: list[dict]) -> dict:
    """한 보험사 행 → (방법, 매칭행, 후보들)."""
    ticker = (ins_row.get("ticker") or "").strip()
    if ticker:
        hit = by_ticker.get(f"{ticker}0") or by_ticker.get(ticker)
        if hit:
            return {"method": "ticker", "row": hit, "candidates": []}

    key = normalize(ins_row.get("company_jp", ""))
    hits = by_name.get(key) or []
    if len(hits) == 1:
        return {"method": "name_exact", "row": hits[0], "candidates": []}
    if len(hits) > 1:
        return {"method": "name_ambiguous", "row": None, "candidates": hits[:5]}

    # 접두 일치(정식명이 더 긴 경우: "au損害保険" ↔ "au損害保険株式会社" 는 위에서 잡히고,
    # 여기 걸리는 건 "PGF生命" ↔ "PGF生命保険" 같은 축약형이다)
    prefix = [r for r in all_rows if normalize(r.get(COL_NAME, "")).startswith(key) and len(key) >= 4]
    if len(prefix) == 1:
        return {"method": "name_prefix", "row": prefix[0], "candidates": []}
    if len(prefix) > 1:
        return {"method": "name_prefix_ambiguous", "row": None, "candidates": prefix[:5]}

    close = difflib.get_close_matches(key, list(by_name.keys()), n=5, cutoff=0.82)
    cands = [by_name[c][0] for c in close]
    return {"method": "none", "row": None, "candidates": cands}


def cand_brief(row: dict) -> dict:
    return {
        "edinet_code": row.get(COL_CODE),
        "name": row.get(COL_NAME),
        "industry": row.get(COL_INDUSTRY),
        "ticker": (row.get(COL_TICKER) or "").strip() or None,
        "listed": row.get(COL_LISTED),
        "yuho_obligated": obligated(row),
    }



# jp_insurers.csv 열 순서(헤더 고정). notes 는 **마지막 열**로 잡는다 — 열이 12개인
# 기형 행 2개도 마지막 칸이 notes 라 인덱스 -1 이 안전하다.
_COL_IDX = {"company_jp": 0, "company_en": 1, "ticker": 2, "sector": 3, "category": 4,
            "edinet_code": 5, "edinet_eligible": 6, "parent_group": 7, "ir_url": 8,
            "ir_health_url": 9}


def _row_view(row: list) -> dict:
    view = {k: (row[i] if i < len(row) else "") for k, i in _COL_IDX.items()}
    view["notes"] = row[-1] if len(row) > len(_COL_IDX) else ""
    return view


def _row_set(row: list, col: str, value: str) -> None:
    idx = len(row) - 1 if col == "notes" else _COL_IDX[col]
    row[idx] = value


NOTE_ABSENT = f"EDINET未登録({date.today().isoformat()} コードリスト全件検索0件)"


def _append_note(existing: str, addition: str) -> str:
    existing = (existing or "").strip()
    if addition in existing:
        return existing
    return f"{existing} / {addition}" if existing else addition


def _apply_note(existing: str, entry: dict, hit: dict) -> str:
    """정정·의무자여부만 노트에 남긴다(전 행에 노트를 붙이면 csv 가 읽히지 않는다)."""
    note = (existing or "").strip()
    stamp = date.today().isoformat()
    if entry.get("recorded_code_belongs_to"):
        note = _append_note(
            note,
            f"EDINETコード訂正{stamp}: 旧{entry['recorded_code']}は"
            f"{entry['recorded_code_belongs_to']}のコード",
        )
    if not obligated(hit):
        note = note.replace("EDINET非対象", "").strip(" /")
        note = _append_note(note, f"EDINET登録あり・有報提出義務者以外({stamp})")
    return note


def main() -> int:
    ap = argparse.ArgumentParser(description="EDINET 코드리스트 대조 / jp_insurers.csv 갱신")
    ap.add_argument("--refresh", action="store_true", help="코드리스트를 새로 내려받는다")
    ap.add_argument("--apply", action="store_true", help="jp_insurers.csv 를 실제로 갱신")
    args = ap.parse_args()

    code_rows = load_codelist(refresh=args.refresh)
    log(f"[codelist] {len(code_rows):,} rows  "
        f"(保険業 {sum(1 for r in code_rows if r.get(COL_INDUSTRY) == '保険業')})")
    by_ticker, by_name = build_index(code_rows)

    # DictReader 를 쓰지 않는다 — 이 csv 에는 열이 12개인 행이 2개 있고(중복 정리 보류분,
    # TODO_jp) DictWriter 로 되쓰면 그 행이 통째로 날아간다. 행 배열 그대로 읽고
    # 인덱스로만 손대 원본 형태를 보존한다(왕복 바이트 동일 확인).
    raw_rows = list(csv.reader(INSURERS_CSV.open(encoding="utf-8", newline="")))
    header, data_rows = raw_rows[0], raw_rows[1:]
    ins_rows = [_row_view(r) for r in data_rows]

    report: list[dict] = []
    counts = {"ticker": 0, "name_exact": 0, "name_prefix": 0, "none": 0, "ambiguous": 0}
    corrections: list[dict] = []

    for idx, row in enumerate(ins_rows):
        res = match_one(row, by_ticker, by_name, code_rows)
        method, hit = res["method"], res["row"]
        old_code = (row.get("edinet_code") or "").strip()
        entry = {
            "company_jp": row.get("company_jp"),
            "company_en": row.get("company_en"),
            "category": row.get("category"),
            "recorded_code": old_code,
            "match_method": method,
            "matched": cand_brief(hit) if hit else None,
            "candidates": [cand_brief(c) for c in res["candidates"]],
        }
        if hit:
            counts[method if method in counts else "ambiguous"] += 1
            new_code = hit[COL_CODE]
            entry["agrees_with_record"] = (old_code == new_code)
            if old_code not in ("TBD", "none", "") and old_code != new_code:
                wrong = next((r for r in code_rows if r[COL_CODE] == old_code), None)
                entry["recorded_code_belongs_to"] = wrong[COL_NAME] if wrong else "코드리스트에 없음"
                corrections.append(entry)
            if args.apply:
                _row_set(data_rows[idx], "edinet_code", new_code)
                _row_set(data_rows[idx], "edinet_eligible", "yes" if obligated(hit) else "no")
                _row_set(data_rows[idx], "notes", _apply_note(row["notes"], entry, hit))
        else:
            counts["ambiguous" if "ambiguous" in method else "none"] += 1
            entry["agrees_with_record"] = None
            # 이름으로는 안 잡혔는데 기재 코드가 코드리스트에 살아 있으면 십중팔구 개명이다
            # (2026-09-13: 第一ネオ生命=ネオファースト生命 E35324, 第一アイペット損保=
            #  アイペット損害保険 E33935 — 둘 다 2026-04-01 개명). 사람이 판정한 결과를
            #  덮지 않도록 매칭은 안 하고 사실만 적는다.
            if old_code.startswith("E"):
                listed = next((r for r in code_rows if r[COL_CODE] == old_code), None)
                if listed:
                    entry["recorded_code_in_codelist"] = listed[COL_NAME]
                    entry["rename_suspected"] = True
            stale = (old_code.startswith("E")
                     and not any(r[COL_CODE] == old_code for r in code_rows))
            if args.apply and not res["candidates"] and stale:
                # 기재 코드가 현행 코드리스트에 아예 없고 이름으로도 안 잡힌다.
                # 폐지된 옛 코드로 보고 none 처리하되, 옛 코드를 노트에 남겨 추적 가능하게.
                entry["recorded_code_belongs_to"] = "현행 코드리스트에 없음(폐지 추정)"
                _row_set(data_rows[idx], "edinet_code", "none")
                _row_set(data_rows[idx], "edinet_eligible", "no")
                _row_set(data_rows[idx], "notes", _append_note(
                    row["notes"], f"旧コード{old_code}は現行EDINETコードリストに無し"
                                  f"({date.today().isoformat()} 全件実測) — 有報提出者から外れたとみられる"))
            elif args.apply and not res["candidates"] and old_code in ("TBD", ""):
                # 코드리스트 11,389건에 이름이 아예 없다 = EDINET 등록 자체가 없는 회사.
                # (증권 미발행 자회사·외자계 자회사. 매칭 실패가 아니라 실측 결과다.)
                _row_set(data_rows[idx], "edinet_code", "none")
                _row_set(data_rows[idx], "edinet_eligible", "no")
                _row_set(data_rows[idx], "notes", _append_note(row["notes"], NOTE_ABSENT))
        report.append(entry)

    matched = sum(1 for e in report if e["matched"])
    obligated_n = sum(1 for e in report if e["matched"] and e["matched"]["yuho_obligated"])
    log("")
    log(f"[match] {matched}/{len(ins_rows)} 매칭  "
        f"(ticker {counts['ticker']} / name_exact {counts['name_exact']} / prefix {counts['name_prefix']})")
    log(f"[match] 有報 제출의무자 {obligated_n} · 의무자 이외 {matched - obligated_n} · 미매칭 {len(ins_rows) - matched}")
    if corrections:
        log(f"\n[!] 기재 코드 오류 {len(corrections)}건 — 종전 코드는 다른 회사다")
        for e in corrections:
            log(f"    {e['company_jp']}: {e['recorded_code']}"
                f"({e['recorded_code_belongs_to']}) -> {e['matched']['edinet_code']}({e['matched']['name']})")

    payload = {
        "generated_at": date.today().isoformat(),
        "codelist_rows": len(code_rows),
        "source": CODELIST_URL,
        "summary": {
            "insurers": len(ins_rows),
            "matched": matched,
            "yuho_obligated": obligated_n,
            "registered_but_not_obligated": matched - obligated_n,
            "unmatched": len(ins_rows) - matched,
            "recorded_code_errors": len(corrections),
        },
        "rows": report,
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"\n[out] {REPORT_JSON}")

    if args.apply:
        with INSURERS_CSV.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(data_rows)
        log(f"[out] {INSURERS_CSV} 갱신 ({len(data_rows)} rows)")
    else:
        log("[dry-run] jp_insurers.csv 는 건드리지 않았다 — 적용하려면 --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
