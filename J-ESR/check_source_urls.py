# -*- coding: utf-8 -*-
"""jp 레인 출처 URL 전수 생존 점검 — 10월 재census 전 선행 단계.

왜 (2026-09-13 리허설)
----------------------
기게시 15사의 1차 출처를 전수 확인했더니 5건이 실패했고, **원인이 둘로 갈렸다.**
403 2건은 URL 이 멀쩡한데 기본 fetcher 가 봇차단당한 것이고(브라우저 헤더 붙이면 200),
404 3건만 진짜 이동이었다. 이 둘을 구분하지 않으면 10/31 재census 가 멀쩡한 출처를
`not_found` 로 잘못 적재한다. 게다가 東京海上HD IR 처럼 200 이면서 링크가 0개인
SPA 셸도 있어서 "정적 fetch 로 자료를 딸 수 있는 사이트인가" 를 미리 갈라놔야 한다.

그래서 이 스크립트가 census 전에 먼저 돈다. 판정은 `jesr_http.probe()` 가 하고
여기서는 어디서 URL 을 모아 어떻게 보고할지만 정한다.

  ok                  정적으로 읽힌다(meta refresh 는 따라간 뒤 판정)
  ok_requires_headers 브라우저 헤더 필요 — **살아있다**. not_found 로 적지 말 것
  spa_shell           200 이지만 JS 렌더링 — 정적 링크수집 불가, 헤드리스 필요
  blocked             404 아닌 4xx(WAF/봇룰) — 브라우저에선 열릴 수 있다. 죽음 아님
  tls_client_issue    파이썬 TLS 악수 실패인데 curl 은 200 — 우리 쪽 문제, 죽음 아님
  dead                404/410 — 대체 URL 필요
  error               5xx·타임아웃 — 재시도 대상, 단정 금지

추가로 `release.tdnet.info` 처럼 **게시가 만료되는 호스트**는 지금 200 이어도
`expiring_host` 로 표시한다(1차 출처로 쓰면 안 된다, 도메인 문서 §4c).

사용법
------
  python J-ESR/check_source_urls.py                 # 화면 출처(15사 + 상세 10사)
  python J-ESR/check_source_urls.py --census        # + census 79행 ir_url/disclosure_url
  python J-ESR/check_source_urls.py --insurers      # + jp_insurers.csv ir_url
  python J-ESR/check_source_urls.py --all --out J-ESR/source_url_health.json

종료코드: dead 또는 expiring_host 가 하나라도 있으면 1.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE_JSON = ROOT / "jp" / "jesr_esr.json"
DETAIL_JSON = ROOT / "jp" / "jesr_detail.json"
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
INSURERS_CSV = HERE / "jp_insurers.csv"
DEFAULT_OUT = HERE / "source_url_health.json"

CLASS_ORDER = ["dead", "error", "blocked", "tls_client_issue", "spa_shell",
               "ok_requires_headers", "ok"]

#: 넓은 범위의 산출을 좁은 범위가 덮어쓰면 증거가 조용히 줄어든다(2026-09-13 실측:
#: 기본 실행 한 번에 254건 산출이 24건짜리로 교체됐다). 범위에 등급을 매겨 강등을 막는다.
SCOPE_RANK = {"page": 1, "insurers": 2, "census": 3, "all": 4}


def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def collect_targets(use_census: bool, use_insurers: bool) -> list[dict]:
    """(origin, company, field, url) 목록. 같은 URL 이 여러 곳에 있으면 전부 남긴다."""
    targets: list[dict] = []

    if PAGE_JSON.exists():
        data = json.loads(PAGE_JSON.read_text(encoding="utf-8"))
        for rec in data.get("records", []):
            if rec.get("source_url"):
                targets.append({"origin": "jp/jesr_esr.json", "company": rec.get("company_jp"),
                                "field": "source_url", "url": rec["source_url"]})

    if DETAIL_JSON.exists():
        data = json.loads(DETAIL_JSON.read_text(encoding="utf-8"))
        for comp in data.get("companies", []):
            if comp.get("source_url"):
                targets.append({"origin": "jp/jesr_detail.json", "company": comp.get("company_jp"),
                                "field": "source_url", "url": comp["source_url"]})

    if use_census and CENSUS_CSV.exists():
        with CENSUS_CSV.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                for field in ("ir_url", "disclosure_url", "source_url"):
                    url = (row.get(field) or "").strip()
                    if url.startswith("http"):
                        targets.append({"origin": CENSUS_CSV.name, "company": row.get("company_jp"),
                                        "field": field, "url": url})

    if use_insurers and INSURERS_CSV.exists():
        rows = list(csv.reader(INSURERS_CSV.open(encoding="utf-8", newline="")))
        for row in rows[1:]:
            for idx, field in ((8, "ir_url"), (9, "ir_health_url")):
                url = (row[idx] if idx < len(row) else "").strip()
                if url.startswith("http"):
                    targets.append({"origin": INSURERS_CSV.name, "company": row[0],
                                    "field": field, "url": url})
    return targets


def main() -> int:
    ap = argparse.ArgumentParser(description="jp 출처 URL 생존 점검")
    ap.add_argument("--census", action="store_true", help="census csv 의 URL 도 포함")
    ap.add_argument("--insurers", action="store_true", help="jp_insurers.csv 의 URL 도 포함")
    ap.add_argument("--all", action="store_true", help="--census --insurers 둘 다")
    ap.add_argument("--workers", type=int, default=4, help="동시 요청 수(예의상 기본 4)")
    ap.add_argument("--timeout", type=int, default=45)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--force", action="store_true",
                    help="좁은 범위 결과로 넓은 범위 산출을 덮어쓴다(기본 금지)")
    args = ap.parse_args()

    targets = collect_targets(args.census or args.all, args.insurers or args.all)
    # 같은 URL 은 한 번만 두드리고 결과를 공유한다(회사 사이트에 예의).
    uniq = sorted({t["url"] for t in targets})
    log(f"[check] 대상 {len(targets)}건 · 고유 URL {len(uniq)}건 · workers={args.workers}")

    def run(url: str) -> tuple[str, dict]:
        return url, jesr_http.probe(url, timeout=args.timeout)

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for url, res in pool.map(run, uniq):
            results[url] = res
            mark = res["classification"].upper()
            extra = " [EXPIRING-HOST]" if res.get("expiring_host") else ""
            log(f"  {mark:20} {res.get('status') or res.get('error','')!s:>6}  {url[:96]}{extra}")

    rows = []
    for t in targets:
        res = results[t["url"]]
        rows.append({**t, **{k: v for k, v in res.items() if k != "url"}})

    counts = {c: sum(1 for r in rows if r["classification"] == c) for c in CLASS_ORDER}
    expiring = [r for r in rows if r.get("expiring_host")]
    dead = [r for r in rows if r["classification"] == "dead"]

    log("")
    log("[summary] " + " · ".join(f"{c}={counts[c]}" for c in CLASS_ORDER))
    if dead:
        log(f"[dead] {len(dead)}건 — 대체 URL 필요")
        for r in dead:
            log(f"    {r['company']} ({r['origin']}:{r['field']}) {r['url']}")
    if expiring:
        log(f"[expiring-host] {len(expiring)}건 — 만료되는 호스트를 1차 출처로 인용했다")
        for r in expiring:
            log(f"    {r['company']} ({r['origin']}:{r['field']}) {r['url']}")

    scope = ("all" if (args.census or args.all) and (args.insurers or args.all)
             else "census" if (args.census or args.all)
             else "insurers" if args.insurers else "page")
    payload = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "scope": scope,
        "targets": len(rows),
        "unique_urls": len(uniq),
        "summary": counts,
        "dead": len(dead),
        "expiring_host": len(expiring),
        "rows": rows,
    }
    out = Path(args.out)
    if out.exists() and not args.force:
        try:
            prev = json.loads(out.read_text(encoding="utf-8")).get("scope", "all")
        except Exception:
            prev = "all"
        if SCOPE_RANK.get(scope, 0) < SCOPE_RANK.get(prev, 0):
            out = out.with_suffix(f".{scope}.json")
            log(f"[guard] 기존 산출이 더 넓은 범위({prev})라 덮어쓰지 않는다 — {out} 로 쓴다"
                f" (덮어쓰려면 --force)")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"[out] {out}  (scope={scope})")
    return 1 if (dead or expiring) else 0


if __name__ == "__main__":
    raise SystemExit(main())
