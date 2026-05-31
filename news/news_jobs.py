"""News DB 적재: model/3_scrapping 스크래퍼 연동."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.scraping.insurance_scraper import load_latest_scrape, run_scrape
from src.scraping.relevance import tokenize


def auto_scrape_and_save_news(root: Path) -> tuple[bool, str]:
    """
    자동 스크래핑 → `DB/News/latest_scrape.json`.
    뉴스1·보험매일·보험저널 (최근 N일, scraper_config 참고).
    """
    try:
        payload = run_scrape(root)
        n = payload.get("article_count", 0)
        rel = root / "DB" / "News" / "latest_scrape.json"
        return True, f"{rel.relative_to(root)} ({n}건)"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def scrape_issue_to_news_db(root: Path, issue: str) -> tuple[bool, str]:
    """
    사용자 이슈 키워드로 최신 스크래핑 결과에서 매칭 기사만 추려 News DB에 JSON 추가 저장.
    latest_scrape 가 없으면 한 번 전체 스크래핑을 시도합니다.
    """
    issue = (issue or "").strip()
    if not issue:
        return False, "이슈 텍스트가 비어 있습니다."

    data = load_latest_scrape(root)
    if not data or not data.get("articles"):
        try:
            run_scrape(root)
            data = load_latest_scrape(root)
        except Exception as e:  # noqa: BLE001
            return False, f"스크래핑 실패: {e}"

    if not data or not data.get("articles"):
        return False, "기사를 수집하지 못했습니다. 네트워크·사이트 구조를 확인하세요."

    toks = tokenize(issue)
    if not toks:
        toks = {issue[:20]}

    matched: list[dict] = []
    for a in data.get("articles") or []:
        blob = f"{a.get('title', '')}\n{a.get('body_excerpt', '')}"
        if any(t in blob for t in toks):
            matched.append(a)

    if not matched:
        matched = list(data.get("articles") or [])[:8]

    news_dir = root / "DB" / "News"
    news_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in issue[:40]).strip() or "issue"
    path = news_dir / f"issue_filter_{stamp}_{safe}.json"
    out = {
        "issue_query": issue,
        "created_at": datetime.now().isoformat(),
        "match_count": len(matched),
        "articles": matched,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return True, str(path.relative_to(root))
