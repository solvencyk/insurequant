#!/usr/bin/env python3
"""Listing census for 2026.2Q 정기경영공시 -- the structural fix for the
"latest-row selector silent failure" recorded in docs/changelog_downloader.md
2026-08-27.

That trap: XPaths like tr[1] / tr[3] mean "whatever row is on top". When the
2Q row does not exist yet they silently re-resolve to the still-current 1Q row,
the download succeeds, and the runner reports status: ok. 12/17 non-life
insurers hit this on 2026-08-27 and every one of them produced a byte-identical
copy of the FY2026_Q1 file.

The fix implemented here is to stop asking "did a download succeed?" and start
asking "does the listing page contain a row LABELLED as 2026 2분기/상반기?".
This probe never downloads. It loads each listing page, dumps the visible row
labels (anchor text + title + href, plus the table text), and text-matches for
a 2026-Q2 marker. Output is a per-insurer verdict:

  posted     -- a 2026 2Q/상반기 label is present -> safe to hand to the downloader
  not_posted -- page loaded fine, latest label is 1Q or older -> honest gap
  unreachable-- page did not load (WAF/timeout/DNS) -> unknown, retry later

Read-only apart from the census JSON it writes.

Usage:
  python scripts/_probes/census_q2_disclosure_listings.py [KR0001 KR0010 ...]

Output: data/disclosure/_meta/FY2026_Q2/listing_census.json
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright  # noqa: E402

from download_disclosure_2026q2_nonlife import INSURERS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
META_DIR.mkdir(parents=True, exist_ok=True)
OUT = META_DIR / "listing_census.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)

LIFE_BULK_URL = "https://pub.insure.or.kr/mngtDis/mngtDis/list.do"

# --- period markers -------------------------------------------------------
# A 2026-Q2 label in Korean disclosure listings shows up as one of:
#   2026년 2분기 / 2026년 2/4분기 / 2026 상반기 / 2026.06 / 2026-06-30 / 반기
# plus latin filename forms: 2Q2026, 2026_2.pdf, FY2026-2_4.pdf, 2026_2H
Q2_PATTERNS = [
    r"2026\s*[.\-년]?\s*2\s*/\s*4\s*분기",
    r"2026\s*[.\-년]?\s*\s*2\s*분기",
    r"2026[^0-9]{0,6}상반기",
    r"2026[^0-9]{0,6}반기",
    r"2026\s*[.\-/]\s*0?6",
    r"2026\s*년\s*6\s*월",
    r"2Q\s*2026",
    r"2026[_\-]2(?![0-9])",
    r"2026[_\-]2H",
    r"FY2026[_\-]2",
    # two-digit fiscal-year labels: 삼성화재 lists rows as "FY 26 1분기"
    # (no four-digit year anywhere in the row) -- a four-digit-only regex
    # returns a false not_posted on that layout.
    r"FY\s*[.\-]?\s*26\s*[.\-년]?\s*(?:2\s*/\s*4\s*)?분기",
    r"FY\s*[.\-]?\s*26\s*[.\-년]?\s*2\s*분기",
    r"FY\s*[.\-]?\s*26\s*[.\-년]?\s*상반기",
    r"CY\s*2026\s*[.\-년]?\s*2\s*/\s*4\s*분기",
]
Q1_PATTERNS = [
    r"2026\s*[.\-년]?\s*1\s*/\s*4\s*분기",
    r"2026\s*[.\-년]?\s*\s*1\s*분기",
    r"2026\s*[.\-/]\s*0?3(?![0-9])",
    r"1Q\s*2026",
    r"2026[_\-]1(?![0-9])",
    r"FY\s*[.\-]?\s*26\s*[.\-년]?\s*1\s*분기",
    r"CY\s*2026\s*[.\-년]?\s*1\s*/\s*4\s*분기",
]

# Evidence that the disclosure LISTING actually rendered. Without this a page
# that served only its nav shell (한화손보 2026-08-29: body never filled, 13
# labels total) scores zero Q2 hits and would be misreported as not_posted.
# "not observed" and "not posted" are different answers and must stay apart.
OBSERVED_RE = re.compile(
    r"(?:분기|반기|결산)\s*(?:경영|검토|재무|공시)|"
    r"(?:경영공시|경영통일공시|정기경영공시)|"
    r"(?:FY|CY)\s*[.\-]?\s*2[0-9]\s*[.\-년]?\s*(?:1|2|3|4)\s*분기|"
    r"20[0-2][0-9]\s*[.\-년]\s*[01]?[0-9]",
    re.IGNORECASE,
)

Q2_RE = re.compile("|".join(Q2_PATTERNS), re.IGNORECASE)
Q1_RE = re.compile("|".join(Q1_PATTERNS), re.IGNORECASE)

# A date alone is not a disclosure row. Site chrome (web-accessibility badges,
# ISMS certification validity ranges) carries dates like 2026.06.17~2027.06.16
# and matched the bare-date patterns on 2026-08-29 (KR0008 삼성화재 false
# positive). Require a disclosure word in the same label/row.
CTX_RE = re.compile(r"경영공시|경영통일공시|정기공시|공시|분기|반기|결산|재무제표|검토보고서|disclosure", re.IGNORECASE)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _scan(texts: list[str]) -> dict:
    q2_hits = [t for t in texts if Q2_RE.search(t) and CTX_RE.search(t)]
    q1_hits = [t for t in texts if Q1_RE.search(t) and CTX_RE.search(t)]
    rejected = [t for t in texts if Q2_RE.search(t) and not CTX_RE.search(t)]
    observed = [t for t in texts if OBSERVED_RE.search(t)]
    return {
        "q2_labels": q2_hits[:12],
        "q1_labels": q1_hits[:6],
        "n_q2": len(q2_hits),
        "n_q1": len(q1_hits),
        "n_observed": len(observed),
        "q2_rejected_no_context": rejected[:6],
    }


def _verdict(rec: dict) -> str:
    if rec.get("n_q2"):
        return "posted"
    if not rec.get("n_observed"):
        # listing never rendered -> UNKNOWN, never a not_posted
        return "not_observed"
    return "not_posted"


def _collect_labels(page) -> list[str]:
    """Every string a human would read as a row label.

    Two passes, because two different layouts hide the period marker:
      element pass -- the label lives in one <a>/<li> ("2026년 2분기 경영공시")
      row pass     -- year and title sit in SEPARATE <td>s (KB손해: <td>2026</td>
                      <td>-2/4분기 경영통일공시</td>), so only the joined row
                      text ever contains both halves. Scanning elements alone
                      would report a false not_posted here -- the same class of
                      silent failure this probe exists to kill.
    """
    out: list[str] = []
    try:
        anchors = page.eval_on_selector_all(
            "a, button, li, td, dt, span[onclick], div[onclick]",
            """els => els.map(e => [
                    (e.innerText||e.textContent||'').slice(0,200),
                    e.getAttribute('title')||'',
                    e.getAttribute('href')||'',
                    e.getAttribute('onclick')||'',
                    e.getAttribute('id')||''
               ].join(' | '))""",
        )
        out.extend(_norm(a) for a in anchors if _norm(a).strip(" |"))
    except Exception:
        pass
    try:
        rows = page.eval_on_selector_all(
            "tr, dl, ul > li",
            "els => els.map(e => (e.innerText||e.textContent||'').slice(0,400))",
        )
        out.extend("[ROW] " + _norm(r) for r in rows if _norm(r))
    except Exception:
        pass
    return out


def _requests_fallback(url: str) -> tuple[list[str], str] | None:
    """Static HTML pass for sites whose WAF refuses headless Chromium.

    Returns (labels, note) or None. Only useful for server-rendered listings
    (롯데손보); JS-rendered ones (한화손보) come back with an empty shell and
    correctly stay not_observed.
    """
    try:
        import requests
        import urllib3
        from lxml import html as LH

        urllib3.disable_warnings()
        r = requests.get(
            url,
            headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"},
            timeout=40,
            verify=False,
        )
        r.encoding = r.apparent_encoding or "utf-8"
        if r.status_code != 200 or len(r.text) < 500:
            return None
        doc = LH.fromstring(r.text)
        labels = [
            _norm(e.text_content())
            for e in doc.xpath("//a | //td | //li | //dt")
            if _norm(e.text_content())
        ]
        labels += [
            "[ROW] " + _norm(tr.text_content())
            for tr in doc.xpath("//table//tr")
            if _norm(tr.text_content())
        ]
        labels += [
            "[TITLE] " + _norm(t)
            for t in doc.xpath("//*/@title")
            if _norm(t)
        ]
        if not labels:
            return None
        return labels, f"requests_static({r.status_code},{len(r.text)}B)"
    except Exception:
        return None


def probe_one(p, kr: str, cfg: dict) -> dict:
    url = cfg.get("url") or cfg.get("url1")
    rec = {"kr": kr, "name": cfg["name"], "url": url}
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent=UA, ignore_https_errors=True)
    page = ctx.new_page()
    page.set_default_timeout(25_000)
    try:
        # 한화손보/롯데손보/코리안리 intermittently answer ERR_EMPTY_RESPONSE or
        # time out (known WAF / site-side flakiness, see changelog 2026-08-15).
        # Retry before calling it unreachable -- an unreachable verdict is an
        # UNKNOWN, not a not_posted, and must not be conflated with one.
        last: Exception | None = None
        for attempt in range(3):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                last = None
                break
            except Exception as e:  # noqa: PERF203
                last = e
                page.wait_for_timeout(4000)
        if last is not None:
            raise last
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        if cfg.get("wait_selector"):
            try:
                page.wait_for_selector(cfg["wait_selector"], timeout=15_000)
            except Exception:
                pass
        page.wait_for_timeout(max(cfg.get("wait_ms", 0), 6000))
        if cfg.get("js_eval_first"):
            try:
                page.evaluate(cfg["js_eval_first"])
                page.wait_for_timeout(3000)
            except Exception as e:
                rec["js_eval_warn"] = str(e)
        # For the two_step_direct_url insurers the listing lives on url1; the
        # detail page (url2) is period-specific and would beg the question.
        labels = _collect_labels(page)
        rec.update(_scan(labels))
        rec["n_labels"] = len(labels)
        rec["verdict"] = _verdict(rec)
        # Keep a dump so a human can audit the verdict without re-running.
        dump = META_DIR / f"{kr}_listing_labels.txt"
        dump.write_text("\n".join(labels), encoding="utf-8")
        rec["labels_dump"] = str(dump.relative_to(ROOT)).replace("\\", "/")
    except Exception as exc:
        rec["verdict"] = "unreachable"
        rec["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()

    # Playwright-blocked != site-blocked. 롯데손보's WAF refuses headless
    # Chromium (ERR_EMPTY_RESPONSE) but answers a plain requests GET with 200
    # and the full listing. That is an ordinary HTTP GET, not a bot-detection
    # bypass. Fall back to it rather than reporting a false unreachable.
    if rec["verdict"] in ("unreachable", "not_observed"):
        fb = _requests_fallback(url)
        if fb is not None:
            labels, note = fb
            rec.update(_scan(labels))
            rec["n_labels"] = len(labels)
            rec["verdict"] = _verdict(rec)
            rec["fallback"] = note
            dump = META_DIR / f"{kr}_listing_labels.txt"
            dump.write_text("\n".join(labels), encoding="utf-8")
            rec["labels_dump"] = str(dump.relative_to(ROOT)).replace("\\", "/")

    print(
        f"[{kr}] {cfg['name']:<12} {rec['verdict']:<11} "
        f"q2={rec.get('n_q2','-')} q1={rec.get('n_q1','-')} "
        f"{'via=' + rec['fallback'] if rec.get('fallback') else ''} "
        f"{rec.get('q2_labels', [''])[:1]}",
        flush=True,
    )
    return rec


def probe_life_bulk(p) -> dict:
    """생명보험협회 정기공시 is a company x quarter GRID, not a dated listing.

    Columns are 회사명 | 1분기 | 2분기 | 3분기 | 결산 and each cell is either
    '다운로드' (posted) or '-' (not posted), under a 기준년 <select>. So the
    site states the answer per company directly -- no regex inference and no
    latest-row selector is involved. We read the 2분기 column for all 22 rows,
    which is a stronger verdict than anything the non-life sites give us.
    """
    rec = {"kr": "LIFE_BULK", "name": "생명보험협회 일괄", "url": LIFE_BULK_URL}
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent=UA, ignore_https_errors=True)
    page = ctx.new_page()
    page.set_default_timeout(40_000)
    try:
        last: Exception | None = None
        for _ in range(4):
            try:
                page.goto(LIFE_BULK_URL, wait_until="domcontentloaded", timeout=60_000)
                last = None
                break
            except Exception as e:  # noqa: PERF203
                last = e
                page.wait_for_timeout(5000)
        if last is not None:
            raise last
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        page.wait_for_timeout(6000)

        # Confirm which 기준년 the grid is actually showing. Reading the 2분기
        # column of the wrong year would be the same class of mistake this
        # probe exists to prevent.
        year = page.eval_on_selector(
            "#search_stdYear", "e => e.value"
        )
        rec["std_year"] = year
        headers = page.eval_on_selector_all(
            "table.data_table th", "els => els.map(e => (e.innerText||'').trim())"
        )
        rec["headers"] = headers
        if "2분기" not in headers:
            raise RuntimeError(f"unexpected grid headers: {headers}")
        q2_col = headers.index("2분기")

        grid = page.eval_on_selector_all(
            "table.data_table tbody tr",
            """els => els.map(r => [...r.querySelectorAll('th,td')]
                   .map(c => (c.innerText||'').replace(/\\s+/g,' ').trim()))""",
        )
        per_company = {}
        for cells in grid:
            if len(cells) <= q2_col or not cells[0]:
                continue
            company = cells[0]
            if company in ("회사명", "전체파일"):
                continue
            per_company[company] = {
                "q1": cells[1] if len(cells) > 1 else "",
                "q2": cells[q2_col],
            }
        rec["per_company"] = per_company
        rec["n_companies"] = len(per_company)
        posted = [c for c, v in per_company.items() if "다운로드" in v["q2"]]
        rec["q2_posted_companies"] = posted
        rec["n_q2"] = len(posted)
        rec["n_q1"] = sum(1 for v in per_company.values() if "다운로드" in v["q1"])
        if year != "2026":
            rec["verdict"] = "not_observed"
            rec["error"] = f"grid showed 기준년={year}, expected 2026"
        elif not per_company:
            rec["verdict"] = "not_observed"
        else:
            rec["verdict"] = "posted" if posted else "not_posted"
        dump = META_DIR / "LIFE_BULK_listing_rows.txt"
        dump.write_text(
            "\n".join(f"{c}\tQ1={v['q1']}\tQ2={v['q2']}" for c, v in per_company.items()),
            encoding="utf-8",
        )
        rec["labels_dump"] = str(dump.relative_to(ROOT)).replace("\\", "/")
    except Exception as exc:
        rec["verdict"] = "unreachable"
        rec["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    print(
        f"[LIFE_BULK] year={rec.get('std_year','-')} companies={rec.get('n_companies','-')} "
        f"{rec['verdict']} q2_posted={rec.get('n_q2','-')} q1_posted={rec.get('n_q1','-')}",
        flush=True,
    )
    return rec


def main() -> int:
    only = set(sys.argv[1:]) or None
    results = []
    with sync_playwright() as p:
        if not only or "LIFE_BULK" in only:
            results.append(probe_life_bulk(p))
        for kr, cfg in INSURERS.items():
            if only and kr not in only:
                continue
            results.append(probe_one(p, kr, cfg))

    # A filtered run must not wipe the other insurers' verdicts. Merge onto the
    # existing census keyed by kr, so `... KR0002` re-probes one company and
    # leaves the other 17 rows intact.
    merged: dict[str, dict] = {}
    if OUT.exists():
        try:
            prior = json.loads(OUT.read_text(encoding="utf-8"))
            for r in prior.get("results", []):
                merged[r["kr"]] = r
        except Exception:
            pass
    # A flaky re-probe must not destroy a good reading. 한화손보 renders only
    # sometimes (anti-bot challenge loop); on 2026-08-29 one attempt returned a
    # clean 692-label listing and the next two returned an empty shell. If the
    # new result carries NO information (not_observed / unreachable) and we
    # already hold one that does, keep the informative record and just log the
    # failed attempt. A genuine `posted` always wins, so this cannot hide a
    # later posting.
    NO_INFO = {"not_observed", "unreachable"}
    for r in results:
        prev = merged.get(r["kr"])
        if prev and r["verdict"] in NO_INFO and prev.get("verdict") not in NO_INFO:
            prev = dict(prev)
            prev["stale_reprobe"] = {
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "verdict": r["verdict"],
                "error": r.get("error"),
                "note": "re-probe returned no information; kept earlier observed reading",
            }
            merged[r["kr"]] = prev
        else:
            merged[r["kr"]] = r
    ordered = ["LIFE_BULK"] + list(INSURERS)
    out_results = [merged[k] for k in ordered if k in merged]

    payload = {
        "_meta": {
            "period": "FY2026_Q2",
            "stamp_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "text-anchored listing census; kills latest-row silent failure",
            "probed_this_run": sorted(r["kr"] for r in results),
            "counts": {
                v: sum(1 for r in out_results if r.get("verdict") == v)
                for v in ("posted", "not_posted", "not_observed", "unreachable")
            },
        },
        "results": out_results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] {payload['_meta']['counts']} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
