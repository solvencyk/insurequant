#!/usr/bin/env python3
"""Listing census for 2026.2Q 정기경영공시 on the 22 LIFE insurers' OWN sites.

Why this exists (owner, 2026-08-30): the 2026-08-27 and 2026-08-29 sweeps
judged all 22 life insurers by reading ONE page -- the 생명보험협회 bulk grid at
pub.insure.or.kr. That answers "did the association publish it?", not "did the
company publish it?". A company posts to its own 공시실 first; the association
grid lags. So a 22/22 `-` on the bulk grid is not evidence of 22 honest gaps.

This probe is the missing half: it visits each insurer's own 경영공시 listing
and text-anchors the row labels, exactly the way
`scripts/_probes/census_q2_disclosure_listings.py` does for the 17 non-life
insurers. It deliberately IMPORTS that module's regexes and scanner rather than
re-deriving them, so all four traps found on 2026-08-29 apply here unchanged:

  1. year in a different <td> than the quarter  -> row(tr) pass, not just elements
  2. two-digit fiscal-year labels ("FY 26 2분기") -> FY-26 patterns
  3. web-accessibility badge dates faking a hit  -> disclosure-context guard
  4. "never rendered" vs "not posted"            -> not_observed is its own verdict

Five more traps turned up on the life sites and are guarded here (see
LISTING_ROW_RE / PERIOD_WORD_RE / LIFE_Q2_RE / _read_year_quarter_grid below).
Four of the five produce a WRONG VERDICT SILENTLY, which is the whole point:

  5. a persistent NAV MENU satisfies "a disclosure word appeared" on any page,
     so six insurers scored a confident not_posted while standing on their home
     page. A verdict now requires a DATED PERIOD ROW, not a menu word.
  6. 수시공시 rows are listed by REGISTRATION DATE, and one registered
     2026.06.30 read as a 2026-Q2 period label (KB라이프 false `posted`). A Q2
     hit must NAME a period (2분기/상반기/반기), not merely carry a date.
  7. the year and the quarter can be separated inside one label -- 삼성생명
     writes "2026년 회계연도(1분기)". Adjacency-based patterns miss it entirely.
  8. the quarter can be LATIN and year-first -- 라이나 writes "FY2026 1Q
     경영공시". The non-life probe only knew the quarter-first form "2Q 2026".
  9. some insurers publish a YEAR x QUARTER GRID instead of a list (iM라이프),
     so no label ever pairs 2026 with 2분기. The grid cell is read directly and
     outranks the regexes when present.

ACCESS TRAP (recorded 2026-08-21 for 흥국생명, generalized here): several Korean
financial sites reject a cold deep-link -- heungkuklife.co.kr answers "현재
잘못된 접근경로" when you goto the listing URL directly, especially without the
`www.` prefix or as the very first navigation in a fresh headless context. They
want a session/referer that looks like a menu click. The workaround, applied to
EVERY company here by default, is: visit the home page first in the same
browser context, settle, then navigate to the listing. `home_first: False`
turns it off if a site ever dislikes it.

This probe NEVER downloads. Read-only apart from the census JSON + label dumps.

Usage:
  python scripts/_probes/census_q2_life_own_sites.py                 # all 22
  python scripts/_probes/census_q2_life_own_sites.py KR0068 KR0069   # subset
  python scripts/_probes/census_q2_life_own_sites.py --discover KR0072
        # dump every 공시-looking link on the home page AND on the landed page,
        # so a human can find the listing URL / menu label for an insurer whose
        # route we do not know yet
  python scripts/_probes/census_q2_life_own_sites.py --rescan
        # recompute every verdict OFFLINE from the saved label dumps -- use
        # after changing a regex, so a guard fix does not require re-hitting
        # 22 insurers' sites
  python scripts/_probes/census_q2_life_own_sites.py --selftest
        # offline positive/negative control: can this detector still SEE a Q2
        # posting in each of the 22 label dialects? RUN THIS AFTER ANY REGEX
        # EDIT -- a detector that matches nothing also reports "no Q2".

Output:
  data/disclosure/_meta/FY2026_Q2/life_own_site_census.json
  data/disclosure/_meta/FY2026_Q2/life_<KR>_listing_labels.txt
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.sync_api import sync_playwright  # noqa: E402

# Reuse the non-life census scanner verbatim -- one definition of what a
# 2026-Q2 label looks like, one definition of "did the listing render at all".
from census_q2_disclosure_listings import (  # noqa: E402
    CTX_RE,
    UA,
    _collect_labels,
    _norm,
    _requests_fallback,
    _scan,
)

ROOT = Path(__file__).resolve().parents[2]
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
META_DIR.mkdir(parents=True, exist_ok=True)
OUT = META_DIR / "life_own_site_census.json"

# --- two guards this probe adds on top of the non-life scanner --------------
#
# TRAP 5 (found 2026-08-30, life sites): "the listing rendered" is NOT the same
# as "a disclosure word appeared somewhere on the page". Every life insurer's
# site carries 공시실 / 정기공시 / 분기 in its persistent NAV MENU, so the
# non-life OBSERVED_RE fires on the home page, on a 404 shell, on the 상품공시
# page -- anywhere. Six insurers (삼성생명·KDB·iM라이프·미래에셋·푸본현대·동양)
# scored a confident `not_posted` on 2026-08-30 while standing on a page that
# had no disclosure listing on it at all. That is the 2026-08-29 "미관측을
# 미게시로 세지 마라" rule failing through a wider hole.
#
# The fix: demand a DATED PERIOD ROW -- some year bound to some quarter/half/
# 결산 word, for ANY year. A real 정기경영공시 listing always shows its own
# history ("2025년 결산", "2026년 1분기"); a menu never does.
#
# TRAP 7 (found 2026-08-30, 삼성생명): the year and the quarter can sit in the
# SAME label but with words wedged between them -- 삼성생명 writes
# "2026년 회계연도(1분기)". Every year-then-quarter regex in the non-life probe
# is adjacency-based and misses that outright, which is a false not_posted on a
# page that is plainly showing its listing. The separator is allowed to be up to
# ~14 characters BUT MUST CONTAIN NO DIGITS -- that is what keeps a registration
# date ("2026.06.30 ... 2분기 안내") from bridging into a false hit.
GAP = r"[^0-9]{0,14}"
QWORD = r"(?:[1-4]\s*(?:/\s*4\s*)?분기|상반기|하반기|반기|결산|일반)"

LISTING_ROW_RE = re.compile(
    r"(?:(?:20|FY\s*|CY\s*)?(?:20)?[12][0-9]\s*[년.\-/]?\s*" + QWORD + r")"
    r"|(?:20[12][0-9]" + GAP + QWORD + r")",
    re.IGNORECASE,
)

# Same tolerance, but pinned to 2026 and to Q2/H1 words only -- this is what
# actually decides `posted`.
# TRAP 8 (found 2026-08-30, 라이나생명 + BNP파리바카디프): the quarter can be
# written in LATIN, in EITHER order, year-first -- 라이나 writes "FY2026 1Q
# 경영공시" and BNP writes "FY2026 Q1 정기 경영공시". The non-life probe only knew
# "2Q 2026" (quarter first, year last), so neither of these matches anything.
# All three orders are covered now.
LIFE_Q2_RE = re.compile(
    r"(?:20\s*26|FY\s*[.\-]?\s*26)" + GAP
    + r"(?:2\s*/\s*4\s*분기|2\s*분기|상반기|반기|2\s*Q(?![0-9])|Q\s*2(?![0-9]))",
    re.IGNORECASE,
)
LIFE_Q1_RE = re.compile(
    r"(?:20\s*26|FY\s*[.\-]?\s*26)" + GAP
    + r"(?:1\s*/\s*4\s*분기|1\s*분기|1\s*Q(?![0-9])|Q\s*1(?![0-9]))",
    re.IGNORECASE,
)

# TRAP 9 (found 2026-08-30, iM라이프): some insurers do not publish a LIST at
# all -- they publish a YEAR x QUARTER GRID, the same shape as the 생명보험협회
# bulk page, where the answer is whether one cell is filled. No row label ever
# contains "2026" and "2분기" together, so every regex above scores zero and the
# insurer would be stuck at not_observed forever. Read the cell instead: it is
# strictly better evidence than a regex, so when a grid is found it decides.
GRID_JS = r"""() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = [];
  for (const t of document.querySelectorAll('table')) {
    const rows = [...t.querySelectorAll('tr')].map(
        r => [...r.querySelectorAll('th,td')].map(c => norm(c.innerText || c.textContent)));
    if (rows.length) out.push(rows);
  }
  return out;
}"""

_GRID_Q2_HDR = re.compile(r"^2\s*/?\s*4?\s*분기$|^상반기$|^2\s*Q$|^Q\s*2$", re.IGNORECASE)
_GRID_Q1_HDR = re.compile(r"^1\s*/?\s*4?\s*분기$|^1\s*Q$|^Q\s*1$", re.IGNORECASE)


def _read_year_quarter_grid(tables: list) -> dict | None:
    """Find a YEAR x QUARTER table and return 2026's Q1/Q2 cells.

    Returns None when no such table is on the page -- absence of a grid is not
    evidence of anything, so the caller falls back to the label scan.
    """
    for rows in tables:
        hdr_i = q1c = q2c = None
        for i, cells in enumerate(rows):
            for j, c in enumerate(cells):
                if _GRID_Q2_HDR.match(c):
                    hdr_i, q2c = i, j
                if _GRID_Q1_HDR.match(c):
                    q1c = j
            if q2c is not None:
                break
        if q2c is None:
            continue
        for cells in rows[(hdr_i or 0) + 1:]:
            if not cells:
                continue
            if not re.match(r"^\s*(?:FY\s*)?2026\s*(?:년|회계연도)?\s*$", cells[0]):
                continue
            def cell(k):
                return cells[k] if (k is not None and k < len(cells)) else ""
            return {
                "year_row": cells[:8],
                "q1_cell": cell(q1c),
                "q2_cell": cell(q2c),
                "q2_filled": bool(cell(q2c)) and cell(q2c) not in ("-", "–", "—"),
            }
    return None

# TRAP 6 (found 2026-08-30, KB라이프 false `posted`): pages that hold 정기 and
# 수시 disclosures together list 수시 rows by REGISTRATION DATE. A 수시 row
# registered 2026.06.30 matches the bare `2026.06` period pattern and sits in
# obvious disclosure context, so the non-life scanner called KB라이프 `posted`
# when its newest 정기 row was still "2026년 1분기 경영통일공시 (2026.05.29)".
# A Q2 hit must therefore NAME a period, not merely carry a date in one.
PERIOD_WORD_RE = re.compile(
    r"2\s*/\s*4\s*분기|2\s*분기|상반기|반기|6\s*월\s*말|2\s*Q", re.IGNORECASE
)


def _scan_life(texts: list[str]) -> dict:
    """Non-life scan, then apply the life-specific guards above.

    A label counts as a 2026-Q2 hit if EITHER
      (a) the non-life scanner matched it AND it names a period (trap 6), or
      (b) the gap-tolerant 2026->Q2 pattern matched it (trap 7).
    Anything the non-life scanner matched on a bare date alone is recorded in
    `q2_rejected_bare_date` rather than dropped silently -- a rejection a human
    cannot see is just a different way to be wrong.
    """
    rec = _scan(texts)
    accepted, bare = [], []
    for t in rec["q2_labels"]:
        (accepted if PERIOD_WORD_RE.search(t) else bare).append(t)
    for t in texts:
        if t not in accepted and LIFE_Q2_RE.search(t) and CTX_RE.search(t):
            accepted.append(t)
            if t in bare:
                bare.remove(t)
    rec["q2_labels"] = accepted[:12]
    rec["q2_rejected_bare_date"] = bare[:6]
    rec["n_q2"] = len(accepted)
    q1 = [t for t in texts if LIFE_Q1_RE.search(t) and CTX_RE.search(t)]
    rec["n_q1"] = max(rec.get("n_q1", 0), len(q1))
    rec["q1_labels"] = (rec.get("q1_labels") or q1)[:6]
    period_rows = [t for t in texts if LISTING_ROW_RE.search(t)]
    rec["n_period_rows"] = len(period_rows)
    rec["period_row_sample"] = period_rows[:6]
    return rec


def _verdict_life(rec: dict) -> str:
    if rec.get("n_q2"):
        return "posted"
    if not rec.get("n_period_rows"):
        # no dated period row anywhere -> we never saw a listing -> UNKNOWN
        return "not_observed"
    return "not_posted"

# fmt: off
# Per-insurer own-site 경영공시 route. Keys match the KR codes used in
# data/disclosure/*/raw/KR####_<name>.pdf.
#
#   home  : visited first to establish session/referer (the 흥국생명 trap)
#   url   : the 정기경영공시 listing page itself
#   note  : anything a future session needs to know about this site
LIFE_SITES: dict[str, dict] = {
    "KR0068": {
        "name": "한화생명",
        "home": "https://www.hanwhalife.com/index.jsp",
        "url": "https://www.hanwhalife.com/main/disclosure/management/occasionalmanagement/DF_MDRM000_P10000.do",
        "note": "공시실 > 경영공시실 > 정기경영공시. URL path says 'occasionalmanagement' for BOTH 정기(DF_MDRM000) and 수시(DF_MDOM000) -- the discriminator is the DF_ code, not the folder.",
    },
    "KR0069": {
        "name": "삼성생명보험",
        "home": "https://www.samsunglife.com/",
        "url": "https://www.samsunglife.com/individual/products/disclosure/management/PDO-MAMAP010100M",
        "note": "정기경영공시 = PDO-MAMA**P**010100M. PDO-MAMAA010100M is 경영공시실 안내 (a guide page, no listing) and PDO-MAMAN010100M is 수시 -- one letter apart, easy to land on the wrong one. Vue SPA: any path under the app returns the same 3.6KB shell, so a 200 proves nothing; rows arrive from /gw/api/display/board/content/list. The route map is readable at /gw/api/display/menu/all (search the 정기 경영공시 entry's linkTo) -- that is how this URL was found, and how to re-find it if it moves. Labels read '2026년 회계연도(1분기)' = trap 7.",
        "wait_ms": 9000,
    },
    "KR0070": {
        "name": "에이비엘생명보험",
        "home": "https://www.abllife.co.kr/",
        "url": "https://www.abllife.co.kr/st/pban/admPban/fprdPban/2026",
        "note": "YEAR IS IN THE PATH: /st/pban/admPban/fprdPban/<YYYY>. Bump the year each January. PDFs live under /cms/pban/admPban/fprdPban/<YYYY>/__icsFiles/afieldfile/...",
    },
    "KR0071": {
        "name": "흥국생명보험",
        "home": "https://www.heungkuklife.co.kr/",
        "url": "https://www.heungkuklife.co.kr/front/public/manageList.do",
        "note": "ACCESS TRAP ORIGIN (changelog 2026-08-21): direct entry without www., or as the first navigation, returns '현재 잘못된 접근경로'. home_first + www. is the workaround. Separately: this company's FY2024 결산 file is itself a wrong document at source (honest gap).",
    },
    "KR0072": {
        "name": "케이디비생명보험",
        "home": "https://www.kdblife.co.kr/",
        "url": "https://www.kdblife.co.kr/ajax.do?scrId=HDLMA001M03P",
        "note": "정기공시 = /ajax.do?scrId=HDLMA001M03P (수시 M01P, 지배구조 M04P, 공시실 index HDLMA000M00P). The home page only exposes these as javascript:_KDB_.fn_link(...), and /scrId/<id>.do renders empty -- use the /ajax.do?scrId= form directly. Labels read 'FY 2026년 1/4분기 경영공시'.",
    },
    "KR0073": {
        "name": "교보생명보험",
        "home": "https://www.kyobo.com/dgt/web/main",
        "url": "https://www.kyobo.com/dgt/web/notice-management/fixed-term/last-year",
        "wait_ms": 12000,
        "note": "kyobo.com (NOT kyobo.co.kr = legacy portal). COUNTER-INTUITIVE: the live 정기경영공시 page is .../fixed-term/LAST-YEAR; plain .../fixed-term is a 404 ('페이지에 접근할 수 없습니다'). The period is a <select> with one option per published quarter, and the page <title> carries the selected period (e.g. '2026년 1분기-정기경영공시-교보생명') -- title alone answers the question. SPA, renders late; a 우수고객 modal covers <article>.",
    },
    "KR0074": {
        "name": "라이나생명보험",
        "home": "https://www.lina.co.kr/",
        "url": "https://www.lina.co.kr/disclosure/management-public-announcement/regular-announcement",
        "note": "Nuxt SPA; the LNB items carry NO href, so the route cannot be read off the page -- it is in the _nuxt chunk (grep the bundles for '/disclosure/'). 수시 = .../occasional-announcement, 지배구조 = .../governance-announcement. A wrong slug answers HTTP 500, a right one 200 -- that is a usable probe. Labels read 'FY2026 1Q 경영공시' = trap 8. /disclosure/pa1.htm is a dead legacy path.",
    },
    "KR0075": {
        "name": "비엔피파리바카디프생명보험",
        "home": "https://www.cardif.co.kr/",
        "url": "https://www.cardif.co.kr/disclosure/papam001.do",
        "note": "page <title> is the literal string '화면명' -- do not use the title to identify the page.",
    },
    "KR0076": {
        "name": "아이엠라이프생명보험",
        "home": "https://www.imlifeins.co.kr/BA/BA_A010.do",
        "url": "https://www.imlifeins.co.kr/BA/BA_F010.do",
        "note": "구 DGB생명. 정기공시/결산공고 = /BA/BA_F010.do (수시 F020, 지배구조 F030, 공시실 index BA_A010). GRID LAYOUT: a 연도 x 분기 table (rows 2026..2004, columns 1/4~4/4분기·결산·결산공고) whose cells say 공시자료 or are blank -- no row label ever pairs a year with a quarter, so only the grid reader can judge this site (trap 9).",
    },
    "KR0079": {
        "name": "미래에셋생명",
        "home": "https://life.miraeasset.com/",
        "url": "https://life.miraeasset.com/micro/disclosure/management/PC-HO-082000-000000.do",
        "note": "정기공시 = PC-HO-082000-000000.do. PC-HO-081900-000000.do is 공시정보관리규정 (the policy text, no listing) -- an easy wrong-page mistake, they sit next to each other in the menu. 공시실 index = /micro/disclosure/index.do.",
        "alt_urls": ["https://life.miraeasset.com/micro/disclosure/index.do"],
    },
    "KR0082": {
        "name": "DB생명보험",
        "home": "https://www.idblife.com/",
        "url": "https://www.idblife.com/notice/business/fxpd_mgm_pban",
        "note": "idblife.com (NOT dblife.co.kr). 수시 = /notice/business/cnt_tm_mgm_pban.",
    },
    "KR0083": {
        "name": "푸본현대생명보험",
        "home": "https://www.fubonhyundai.com/index.jsp",
        "url": "https://www.fubonhyundai.com/index.jsp",
        "js_eval_first": "goMenu('CUSI150413010000')",
        "click_path": ["경영공시실"],
        "note": "no deep link: every screen is goMenu('<CODE>'). 경영공시실 = CUSI150413010000. /comm/notice/managementList.jsp is a guess that lands on #ERROR0100000000.",
    },
    "KR0087": {
        "name": "동양생명",
        "home": "https://www.myangel.co.kr/",
        "url": "https://pbano.myangel.co.kr/notice/product/WE_PA_AP_01_00_00.jsp",
        "click_path": ["경영공시", "정기경영공시"],
        "note": "공시 lives on a SEPARATE SUBDOMAIN pbano.myangel.co.kr (www.myangel.co.kr/paging/WE_AC_* 404s to /comm/notFound). The 경영공시 menu is href=javascript:void(0) -> must be clicked, no deep link exists.",
    },
    "KR0094": {
        "name": "신한라이프생명보험",
        "home": "https://www.shinhanlife.co.kr/hp/cdhi0310.do",
        "url": "https://www.shinhanlife.co.kr/hp/cdhi0310.do",
        "click_path": ["정기경영공시"],
        "note": "공시실 nav items all carry href='#' -> click, no deep link. cdhi0250t01=상품공시, cdhi0520=입찰공시 for reference.",
    },
    "KR0095": {
        "name": "메트라이프생명보험",
        "home": "https://brand.metlife.co.kr/",
        "url": "https://brand.metlife.co.kr/pn/fxtrmMnnt/retrieveFxtrmMnntMain.do",
        "note": "brand.metlife.co.kr, not www.metlife.co.kr.",
    },
    "KR0097": {
        "name": "하나생명보험",
        "home": "https://www.hanalife.co.kr/",
        "url": "https://www.hanalife.co.kr/home/publicAnn/listPublicAnn.do?gubun=F",
        "note": "gubun=F selects 정기공시 in the 경영공시실 list.",
    },
    "KR0099": {
        "name": "KB라이프생명",
        "home": "https://www.kblife.co.kr/",
        "url": "https://www.kblife.co.kr/customer-common/managementPublicNoticeOffice.do",
        "note": "single 경영공시실 page holding both 정기 and 수시.",
    },
    "KR0100": {
        "name": "처브라이프생명보험",
        "home": "https://www.chubblife.co.kr/",
        "url": "https://www.chubblife.co.kr/front/official/management/list.do",
        "note": "front/official/* is the whole 공시실 tree (sale/, equityLinked/, management/).",
    },
    "KR0104": {
        "name": "농협생명보험",
        "home": "https://www.nhlife.co.kr/",
        "url": "https://www.nhlife.co.kr/ho/on/HOON0001M00.nhl",
        "note": "정기공시 > 경영공시 > 공시실. Site takes scheduled maintenance windows -- a maintenance page must score not_observed, never not_posted.",
    },
    "KR1010": {
        "name": "교보라이프플래닛생명보험",
        "home": "https://www.lifeplanet.co.kr/",
        "url": "https://www.lifeplanet.co.kr/disclosure/admi/HPDC21S0.dev",
        "note": ".dev is the site's own screen extension, not a TLD.",
    },
    "KR1011": {
        "name": "IBK연금보험",
        "home": "https://www.ibki.co.kr/",
        "url": "https://www.ibki.co.kr/process/HP_PBANO_MGMT_FIXTERM_LIST",
        "note": "공시실 index = /process/HP_PBANO_LIST; 정기경영공시 = /process/HP_PBANO_MGMT_FIXTERM_LIST (found 2026-08-30 by crawling the index). WAF prefers plain requests over headless Chromium -- the static fallback carries this one.",
    },
    "KR0080": {
        "name": "에이아이에이생명보험",
        "home": "https://www.aia.co.kr/ko.html",
        "url": "https://www.aia.co.kr/ko/disclosure/management-information/regular.html",
        "note": "static .html tree; 수시 = .../irregular.html.",
    },
}
# fmt: on

DISCOVER_HINT = ("공시", "disclosure", "pban", "notice")


def _discover_links(page) -> list[str]:
    """Every anchor that smells like a disclosure route, with its href.

    Used to FIND a listing URL, not to judge a quarter. Kept separate from the
    verdict path on purpose: a discovery dump must never be able to produce a
    `posted`.
    """
    try:
        raw = page.eval_on_selector_all(
            "a",
            """els => els.map(e => [
                    (e.innerText||e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,120),
                    e.getAttribute('href')||'',
                    e.getAttribute('onclick')||''
               ].join(' \\u2192 '))""",
        )
    except Exception:
        return []
    out = []
    for a in raw:
        s = _norm(a)
        if not s.strip(" →"):
            continue
        if any(h in s.lower() for h in DISCOVER_HINT):
            out.append(s)
    # de-dup, preserve order
    seen: set[str] = set()
    uniq = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def probe_one(p, kr: str, cfg: dict, discover: bool) -> dict:
    rec = {
        "kr": kr,
        "name": cfg["name"],
        "home": cfg.get("home"),
        "url": cfg["url"],
        "note": cfg.get("note", ""),
    }
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent=UA, ignore_https_errors=True, locale="ko-KR"
    )
    page = ctx.new_page()
    page.set_default_timeout(25_000)
    try:
        # --- the 흥국생명 workaround, applied by default -------------------
        # Cold deep-links get "현재 잘못된 접근경로". Visiting home first in the
        # same context gives the listing request a session + a same-origin
        # referer, which is what these sites actually check.
        if cfg.get("home") and cfg.get("home_first", True):
            try:
                page.goto(cfg["home"], wait_until="domcontentloaded", timeout=60_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass
                page.wait_for_timeout(2500)
                rec["home_ok"] = True
                if discover:
                    # Dump the home page's disclosure routes BEFORE navigating
                    # away -- this is how an unknown listing URL gets found.
                    rec["home_links"] = _discover_links(page)[:120]
            except Exception as e:
                rec["home_ok"] = False
                rec["home_error"] = f"{type(e).__name__}: {e}"

        candidates = [cfg["url"]] + list(cfg.get("alt_urls", []))
        last: Exception | None = None
        loaded = None
        for url in candidates:
            for _ in range(2):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                    loaded = url
                    last = None
                    break
                except Exception as e:  # noqa: PERF203
                    last = e
                    page.wait_for_timeout(3000)
            if loaded:
                break
        if loaded is None:
            raise last if last else RuntimeError("no candidate URL loaded")
        rec["loaded_url"] = loaded
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        page.wait_for_timeout(max(cfg.get("wait_ms", 0), 6000))

        if cfg.get("js_eval_first"):
            try:
                page.evaluate(cfg["js_eval_first"])
                page.wait_for_timeout(4000)
            except Exception as e:
                rec["js_eval_warn"] = f"{type(e).__name__}: {e}"

        # --- menu-click flow ----------------------------------------------
        # Some 공시실 menus are pure JS (`href="javascript:void(0)"`, or no href
        # at all) -- 동양생명, 라이나, 신한라이프. There is no deep link to guess:
        # the listing only exists after the click. `click_path` is an ordered
        # list of link texts to click, which is also exactly the session/referer
        # flow the 흥국생명-class sites demand.
        # These menu items are usually INSIDE A COLLAPSED DROPDOWN, so Playwright's
        # actionability wait ("element is not visible") times out on every one of
        # them -- that is what happened to 삼성생명/KDB/라이나/iM라이프 on the first
        # pass. A hidden nav item still runs its onclick handler, so dispatch the
        # click in the page instead of asking Playwright to "really" click it.
        for step in cfg.get("click_path", []):
            done = False
            try:
                loc = page.get_by_text(step, exact=False).first
                loc.scroll_into_view_if_needed(timeout=3000)
                loc.click(timeout=6000)
                done = True
            except Exception:
                pass
            if not done:
                try:
                    done = bool(
                        page.evaluate(
                            """(txt) => {
                                const want = txt.replace(/\\s+/g,'');
                                const els = [...document.querySelectorAll(
                                    'a,button,span,li,dt,dd,div')];
                                for (const e of els) {
                                    const t = (e.innerText||e.textContent||'')
                                        .replace(/\\s+/g,'');
                                    if (t && t === want && e.children.length < 3) {
                                        e.click(); return true;
                                    }
                                }
                                for (const e of els) {
                                    const t = (e.innerText||e.textContent||'')
                                        .replace(/\\s+/g,'');
                                    if (t.startsWith(want) && t.length < want.length + 6) {
                                        e.click(); return true;
                                    }
                                }
                                return false;
                            }""",
                            step,
                        )
                    )
                except Exception:
                    done = False
            if done:
                page.wait_for_timeout(4000)
                try:
                    page.wait_for_load_state("networkidle", timeout=12_000)
                except Exception:
                    pass
                rec.setdefault("clicked", []).append(step)
            else:
                rec.setdefault("click_errors", []).append(f"{step}: not-found")

        rec["final_url"] = page.url
        # A site that bounced us to the home page or an error screen did NOT
        # show us its listing. Record it; the OBSERVED guard decides the verdict.
        body = ""
        try:
            body = page.inner_text("body")[:4000]
        except Exception:
            pass
        for marker in ("잘못된 접근", "정상적인 경로", "점검", "오류가 발생", "Access Denied"):
            if marker in body:
                rec.setdefault("page_warnings", []).append(marker)

        labels = _collect_labels(page)
        rec.update(_scan_life(labels))
        rec["n_labels"] = len(labels)
        # A year x quarter grid, where present, is a direct statement by the
        # issuer and outranks any regex inference (trap 9).
        try:
            grid = _read_year_quarter_grid(page.evaluate(GRID_JS))
        except Exception:
            grid = None
        if grid:
            rec["grid_2026"] = grid
            rec["n_period_rows"] = max(rec.get("n_period_rows", 0), 1)
            if grid["q2_filled"]:
                rec["n_q2"] = max(rec.get("n_q2", 0), 1)
                rec["q2_labels"] = (rec.get("q2_labels") or []) + [
                    "[GRID] 2026 2분기 = " + grid["q2_cell"]
                ]
        rec["verdict"] = _verdict_life(rec)
        dump = META_DIR / f"life_{kr}_listing_labels.txt"
        dump.write_text("\n".join(labels), encoding="utf-8")
        rec["labels_dump"] = str(dump.relative_to(ROOT)).replace("\\", "/")
        if discover or rec["verdict"] in ("not_observed", "unreachable"):
            rec["discovered_links"] = _discover_links(page)[:60]
    except Exception as exc:
        rec["verdict"] = "unreachable"
        rec["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()

    # Same static fallback the non-life census uses: a WAF that refuses headless
    # Chromium often answers a plain requests GET. That is an ordinary HTTP GET,
    # not a bot-detection bypass.
    if rec["verdict"] in ("unreachable", "not_observed"):
        fb = _requests_fallback(cfg["url"])
        if fb is not None:
            labels, note = fb
            scanned = _scan_life(labels)
            # Only let the fallback OVERRIDE when it actually saw a listing.
            if scanned["n_period_rows"] or scanned["n_q2"]:
                rec.update(scanned)
                rec["n_labels"] = len(labels)
                rec["verdict"] = _verdict_life(rec)
                rec["fallback"] = note
                dump = META_DIR / f"life_{kr}_listing_labels.txt"
                dump.write_text("\n".join(labels), encoding="utf-8")
                rec["labels_dump"] = str(dump.relative_to(ROOT)).replace("\\", "/")
            else:
                rec["fallback_uninformative"] = note

    print(
        f"[{kr}] {cfg['name']:<18} {rec['verdict']:<12} "
        f"q2={rec.get('n_q2','-')} q1={rec.get('n_q1','-')} rows={rec.get('n_period_rows','-')} "
        f"{'via=' + rec['fallback'] if rec.get('fallback') else ''} "
        f"{rec.get('q2_labels', [''])[:1]}",
        flush=True,
    )
    return rec


# Every 2026-Q1 label form actually observed on the 22 own sites on 2026-08-30,
# rewritten to Q2, plus the two non-life forms this probe inherits. A census
# that reports 22 not_posted is only worth something if it can be shown to SEE
# a posting -- a detector that matches nothing also "finds no Q2".
SELFTEST_POSITIVE = [
    "2026년 2분기 정기경영공시",                                   # 한화생명
    "2026년 회계연도(2분기)",                                      # 삼성생명 (trap 7)
    "[2026년 2분기 정기경영공시]",                                 # ABL
    "FY2026 2분기 경영공시",                                       # 흥국생명
    "FY 2026년 2/4분기 경영공시",                                  # KDB
    "검색조건 검색조건 선택 2026년 2분기 2026년 2분기",             # 교보 (select option)
    "FY2026 2Q 경영공시",                                          # 라이나 (trap 8)
    "FY2026 Q2 정기 경영공시",                                     # BNP  (trap 8)
    "FY 2026년 2/4 분기",                                          # 미래에셋
    "2026년 2분기 DB생명보험회사의 현황",                          # DB생명
    "FY2026 2/4분기 현황",                                         # 푸본현대
    "FY2026 2분기 정기공시",                                       # 동양
    "2026.04 ~ 2026.06 2026년 2분기 다운로드",                     # 신한라이프
    "2026년 2분기 주요경영현황 (메트라이프생명) 2026년 2분기 경영공시자료.pdf",
    "2026년 2분기 경영통일공시",                                   # KB라이프
    "FY2026 2/4분기 경영공시",                                     # 처브
    "2026년 2/4분기 경영공시",                                     # 농협생명 / IBK연금
    "2026년 2/4분기 교보라이프플래닛생명보험주식회사의 현황",
    "2026년 2분기 결산 경영공시",                                  # AIA
    "[ROW] 2026 | -2/4분기 경영통일공시",                          # KB손해 split <td> (trap 1)
    "FY 26 2분기 경영공시",                                        # 삼성화재 2-digit FY (trap 2)
]
# Things that must NEVER be read as a 2026-Q2 posting.
SELFTEST_NEGATIVE = [
    "[기타] 자본확충(증자 등) 시장공시 2026.06.30 첨부파일",       # 수시 reg date (trap 6)
    "웹접근성 인증 유효기간 2026.06.17~2027.06.16",                # a11y badge (trap 3)
    "2026년 1분기 정기경영공시",
    "FY2026 1Q 경영공시",
    "FY2026 Q1 정기 경영공시",
    "2025년 2분기 경영공시",
    "2026.05.29 등록 1분기 안내 2분기 예정",                       # digits inside the gap
]


def selftest() -> int:
    """Offline positive/negative control on the Q2 detector and the grid reader."""
    missed = [t for t in SELFTEST_POSITIVE if not _scan_life([t])["n_q2"]]
    false = [t for t in SELFTEST_NEGATIVE if _scan_life([t])["n_q2"]]
    grid_no = _read_year_quarter_grid(
        [[["", "1/4분기", "2/4분기", "3/4분기", "결산"], ["2026", "공시자료", "", "", ""]]]
    )
    grid_yes = _read_year_quarter_grid(
        [[["", "1/4분기", "2/4분기"], ["2026", "공시자료", "공시자료"]]]
    )
    ok = (
        not missed
        and not false
        and grid_no is not None
        and not grid_no["q2_filled"]
        and grid_yes is not None
        and grid_yes["q2_filled"]
    )
    print(f"positive {len(SELFTEST_POSITIVE) - len(missed)}/{len(SELFTEST_POSITIVE)}"
          f"  false-positive {len(false)}/{len(SELFTEST_NEGATIVE)}"
          f"  grid {'ok' if grid_no and grid_yes else 'FAIL'}")
    for t in missed:
        print("  MISSED:", t)
    for t in false:
        print("  FALSE POSITIVE:", t)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def rescan_offline(only: set[str] | None) -> int:
    """Recompute verdicts from the saved label dumps -- no network.

    A guard fix must be testable without re-hitting 22 insurers' sites, and a
    re-run is not free: some of these sites rate-limit, and one of them
    (한화손보, non-life) only renders 2 times in 7. Re-scanning the dumps also
    proves the fix on the exact bytes that produced the wrong verdict.
    """
    if not OUT.exists():
        print(f"no census at {OUT}")
        return 1
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    changed = 0
    for r in payload.get("results", []):
        if only and r["kr"] not in only:
            continue
        dump = ROOT / (r.get("labels_dump") or "")
        if not r.get("labels_dump") or not dump.exists():
            continue
        labels = dump.read_text(encoding="utf-8").splitlines()
        before = r.get("verdict")
        grid = r.get("grid_2026")
        r.update(_scan_life(labels))
        r["n_labels"] = len(labels)
        if grid:
            # the grid reading lives in the census, not in the label dump
            r["grid_2026"] = grid
            r["n_period_rows"] = max(r.get("n_period_rows", 0), 1)
            if grid.get("q2_filled"):
                r["n_q2"] = max(r.get("n_q2", 0), 1)
        r["verdict"] = _verdict_life(r)
        if r["verdict"] != before:
            changed += 1
            print(f"[{r['kr']}] {r['name']:<18} {before} -> {r['verdict']}")
    payload["_meta"]["stamp_utc"] = datetime.now(timezone.utc).isoformat()
    payload["_meta"]["last_offline_rescan_utc"] = payload["_meta"]["stamp_utc"]
    payload["_meta"]["counts"] = {
        v: sum(1 for r in payload["results"] if r.get("verdict") == v)
        for v in ("posted", "not_posted", "not_observed", "unreachable")
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[rescan] {changed} verdict(s) changed -> {payload['_meta']['counts']}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:]]
    discover = "--discover" in args
    only = {a for a in args if not a.startswith("--")} or None
    if "--selftest" in args:
        return selftest()
    if "--rescan" in args:
        return rescan_offline(only)

    results = []
    with sync_playwright() as p:
        for kr, cfg in LIFE_SITES.items():
            if only and kr not in only:
                continue
            results.append(probe_one(p, kr, cfg, discover))

    # Merge onto the existing census so a filtered run never wipes other rows,
    # and a no-information re-probe never destroys an informative reading
    # (same policy as the non-life census).
    merged: dict[str, dict] = {}
    if OUT.exists():
        try:
            prior = json.loads(OUT.read_text(encoding="utf-8"))
            for r in prior.get("results", []):
                merged[r["kr"]] = r
        except Exception:
            pass
    NO_INFO = {"not_observed", "unreachable"}
    for r in results:
        prev = merged.get(r["kr"])
        if prev and r["verdict"] in NO_INFO and prev.get("verdict") not in NO_INFO:
            prev = dict(prev)
            prev["stale_reprobe"] = {
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "verdict": r["verdict"],
                "error": r.get("error"),
            }
            merged[r["kr"]] = prev
        else:
            merged[r["kr"]] = r
    out_results = [merged[k] for k in LIFE_SITES if k in merged]

    payload = {
        "_meta": {
            "period": "FY2026_Q2",
            "scope": "22 life insurers, OWN sites (association bulk grid is a separate probe)",
            "stamp_utc": datetime.now(timezone.utc).isoformat(),
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
