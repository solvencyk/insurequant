"""보험 뉴스 스크래핑 설정 (model/3_scrapping/config.py 기반)."""

from __future__ import annotations

from pathlib import Path

# 수집 기간 (게시일 기준, 한국 시간)
DAYS_LOOKBACK = 7

BODY_MAX_CHARS = 2000

NEWS1_LIST_URLS = [
    f"https://www.news1.kr/finance/insurance-card?page={p}" if p > 1 else "https://www.news1.kr/finance/insurance-card"
    for p in range(1, 11)
]
FINS_LIST_URLS = [
    "https://www.fins.co.kr/news/articleList.html?sc_day=7&sc_order_by=C&view_type=sm",
    "https://www.fins.co.kr/news/articleList.html?sc_day=7&sc_order_by=C&view_type=sm&page=2",
]
INSJOURNAL_LIST_URLS = [
    "https://www.insjournal.co.kr/news/articleList.html?sc_day=7&view_type=sm",
    "https://www.insjournal.co.kr/news/articleList.html?sc_day=7&view_type=sm&page=2",
]

MAX_ARTICLES_PER_SOURCE = 35

REQUEST_TIMEOUT_SEC = 22
REQUEST_DELAY_SEC = 0.35

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SKIP_TITLE_PREFIXES = ("[채용]", "[알림]", "[공지]")


def latest_scrape_path(project_root: Path) -> Path:
    """에이전트 News DB 경로."""
    return project_root / "DB" / "News" / "latest_scrape.json"
