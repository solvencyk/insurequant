"""
뉴스1·보험매일·보험저널 목록·기사 수집 (model/3_scrapping/scraper.py 기반).
결과는 project_root/DB/News/latest_scrape.json 에 저장.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from scraper_config import (
    BODY_MAX_CHARS,
    DAYS_LOOKBACK,
    FINS_LIST_URLS,
    INSJOURNAL_LIST_URLS,
    MAX_ARTICLES_PER_SOURCE,
    NEWS1_LIST_URLS,
    REQUEST_DELAY_SEC,
    REQUEST_TIMEOUT_SEC,
    SKIP_TITLE_PREFIXES,
    USER_AGENT,
)

KST = ZoneInfo("Asia/Seoul")

# 독립 실행: 스크랩 결과 JSON은 이 모듈 옆(news/latest_scrape.json)에 저장.
# press.html 이 같은 파일을 fetch 한다. (옛 허브의 DB/News 경로 대체)
def _output_path(project_root: Path | None = None) -> Path:
    return Path(__file__).resolve().parent / "latest_scrape.json"


NEWS1_ARTICLE_RE = re.compile(
    r"(?:https?://(?:www\.)?news1\.kr)?/finance/insurance-card/(\d+)(?:\?[^\s\"'<>]*)?"
)


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}


def fetch_html(url: str) -> str:
    r = requests.get(
        url,
        headers=_headers(),
        timeout=REQUEST_TIMEOUT_SEC,
    )
    r.raise_for_status()
    if r.encoding is None or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def parse_dt_kst_dot_ampm(text: str) -> datetime | None:
    text = text.strip()
    m = re.search(
        r"(\d{4})\.(\d{2})\.(\d{2})\s*(오전|오후)\s*(\d{1,2}):(\d{2})",
        text,
    )
    if not m:
        return None
    y, mo, d, ap, hh, mm = m.groups()
    hour = int(hh)
    if ap == "오후" and hour != 12:
        hour += 12
    if ap == "오전" and hour == 12:
        hour = 0
    try:
        return datetime(
            int(y),
            int(mo),
            int(d),
            hour,
            int(mm),
            tzinfo=KST,
        )
    except ValueError:
        return None


def parse_dt_fins_input(text: str) -> datetime | None:
    m = re.search(
        r"(?:입력|등록|발행)\s*(\d{4})\.(\d{2})\.(\d{2})\s+(\d{1,2}):(\d{2})",
        text,
    )
    if not m:
        return None
    y, mo, d, hh, mm = m.groups()
    try:
        return datetime(
            int(y), int(mo), int(d), int(hh), int(mm), tzinfo=KST
        )
    except ValueError:
        return None


def parse_iso_to_kst(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt.astimezone(KST)
    except ValueError:
        return None


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def extract_published_from_soup(soup: BeautifulSoup, html: str) -> datetime | None:
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content"):
        dt = parse_iso_to_kst(meta["content"])
        if dt:
            return dt
    meta = soup.find("meta", attrs={"name": "date"})
    if meta and meta.get("content"):
        dt = parse_iso_to_kst(meta["content"])
        if dt:
            return dt
    t = soup.find("time", datetime=True)
    if t and t.get("datetime"):
        dt = parse_iso_to_kst(t["datetime"])
        if dt:
            return dt
    for sel in ("span.date", ".date", ".article-date"):
        el = soup.select_one(sel)
        if el:
            dt = parse_dt_kst_dot_ampm(el.get_text(" ", strip=True))
            if dt:
                return dt
    dt = parse_dt_kst_dot_ampm(html[:8000])
    if dt:
        return dt
    dt = parse_dt_fins_input(html[:12000])
    if dt:
        return dt
    return None


def extract_title(soup: BeautifulSoup) -> str:
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        t = og["content"].strip()
        if t:
            return t
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    t = soup.find("title")
    return t.get_text(strip=True) if t else ""


def extract_body_excerpt(soup: BeautifulSoup, html: str) -> str:
    for sel in (
        '[itemprop="articleBody"]',
        "#article-view-content-div",
        "#articleBody",
        "#articles_detail",
        ".article-body",
        "article",
    ):
        el = soup.select_one(sel)
        if el:
            for tag in el(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 80:
                return text[:BODY_MAX_CHARS]
    og = soup.find("meta", property="og:description")
    if og and og.get("content"):
        return og["content"].strip()[:BODY_MAX_CHARS]
    soup2 = soup_from_html(html)
    for tag in soup2(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup2.get_text(separator="\n", strip=True)
    return text[:BODY_MAX_CHARS]


def collect_news1_article_urls() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for list_url in NEWS1_LIST_URLS:
        try:
            html = fetch_html(list_url)
            time.sleep(REQUEST_DELAY_SEC)
        except Exception:
            continue
        for m in NEWS1_ARTICLE_RE.finditer(html):
            aid = m.group(1)
            url = f"https://www.news1.kr/finance/insurance-card/{aid}"
            if url not in seen:
                seen.add(url)
                out.append(url)
    return out


def collect_idxno_urls(list_urls: list[str], domain_contains: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    domain_contains = domain_contains.lower()
    for list_url in list_urls:
        try:
            html = fetch_html(list_url)
            time.sleep(REQUEST_DELAY_SEC)
        except Exception:
            continue
        soup = soup_from_html(html)
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "articleView.html" not in href or "idxno=" not in href:
                continue
            full = urljoin(list_url, href)
            host = urlparse(full).netloc.lower()
            if domain_contains not in host:
                continue
            if full not in seen:
                seen.add(full)
                out.append(full)
    return out


def should_skip_title(title: str) -> bool:
    t = title.strip()
    for p in SKIP_TITLE_PREFIXES:
        if t.startswith(p):
            return True
    return False


def scrape_article(url: str, source: str) -> dict[str, Any] | None:
    try:
        html = fetch_html(url)
        time.sleep(REQUEST_DELAY_SEC)
    except Exception:
        return None
    soup = soup_from_html(html)
    title = extract_title(soup)
    if not title or should_skip_title(title):
        return None
    published = extract_published_from_soup(soup, html)
    body = extract_body_excerpt(soup, html)
    return {
        "source": source,
        "title": title,
        "url": url,
        "published_at": published.isoformat() if published else None,
        "body_excerpt": body,
    }


def in_lookback(published_iso: str | None, cutoff: datetime) -> bool:
    if not published_iso:
        return False
    try:
        dt = datetime.fromisoformat(published_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt.astimezone(KST) >= cutoff
    except ValueError:
        return False


def run_scrape(project_root: Path | None = None) -> dict[str, Any]:
    """세 출처 수집 → DB/News/latest_scrape.json."""
    from relevance import load_keyword_weights, sort_articles_by_relevance

    output_json = _output_path(project_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(KST)
    cutoff = now - timedelta(days=DAYS_LOOKBACK)

    buckets: dict[str, list[str]] = {
        "news1": collect_news1_article_urls(),
        "보험매일": collect_idxno_urls(FINS_LIST_URLS, "fins.co.kr"),
        "보험저널": collect_idxno_urls(INSJOURNAL_LIST_URLS, "insjournal.co.kr"),
    }

    articles: list[dict[str, Any]] = []
    errors: list[str] = []

    for source_key, urls in buckets.items():
        n = 0
        for url in urls:
            if n >= MAX_ARTICLES_PER_SOURCE:
                break
            art = scrape_article(url, source_key)
            if not art:
                continue
            if not in_lookback(art.get("published_at"), cutoff):
                continue
            articles.append(art)
            n += 1

    def sort_key(a: dict[str, Any]) -> datetime:
        p = a.get("published_at")
        if not p:
            return datetime.min.replace(tzinfo=KST)
        try:
            dt = datetime.fromisoformat(p)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KST)
            return dt.astimezone(KST)
        except ValueError:
            return datetime.min.replace(tzinfo=KST)

    articles.sort(key=sort_key, reverse=True)

    weights = load_keyword_weights()
    articles = sort_articles_by_relevance(articles, weights)

    payload: dict[str, Any] = {
        "scraped_at": now.isoformat(),
        "since_kst": cutoff.isoformat(),
        "days_lookback": DAYS_LOOKBACK,
        "article_count": len(articles),
        "articles": articles,
        "errors": errors,
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload


def load_latest_scrape(project_root: Path | None = None) -> dict[str, Any] | None:
    output_json = _output_path(project_root)
    if not output_json.exists():
        return None
    with open(output_json, encoding="utf-8") as f:
        return json.load(f)


def articles_to_llm_context(
    data: dict[str, Any],
    articles: list[dict[str, Any]] | None = None,
) -> str:
    arts = articles if articles is not None else (data.get("articles") or [])
    parts = [
        f"스크래핑 시각(KST 기준 메타): {data.get('scraped_at', '')}",
        f"포함 기간: {data.get('since_kst', '')} 이후 게시로 필터됨",
        f"기사 수: {len(arts)}",
        "",
        "--- 기사 목록 (관련도 학습 반영 시 상단이 우선 이슈로 정렬됨) ---",
    ]
    for i, a in enumerate(arts, 1):
        parts.append(f"\n[{i}] 출처: {a.get('source', '')}")
        parts.append(f"제목: {a.get('title', '')}")
        parts.append(f"게시(파싱): {a.get('published_at', '알 수 없음')}")
        parts.append(f"URL: {a.get('url', '')}")
        excerpt = (a.get("body_excerpt") or "").strip()
        if excerpt:
            parts.append(f"본문 일부:\n{excerpt}")
        parts.append("")
    return "\n".join(parts)


if __name__ == "__main__":
    # 로컬 전용 실행: `cd news && python insurance_scraper.py`
    # → news/latest_scrape.json 생성 (relevance 가중치로 정렬). press.html 이 읽는다.
    payload = run_scrape()
    print(
        f"scraped {payload['article_count']} articles → "
        f"{_output_path()}"
    )
