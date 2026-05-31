"""
Streamlit: 전체 뉴스 스크래핑 결과 목록 + 기사별 피드백(매우 좋음 / 좋음 / 나쁨).
`insurance_scraper.load_latest_scrape` · `relevance.record_feedback` 사용.
"""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from src.scraping.insurance_scraper import load_latest_scrape
from src.scraping.relevance import (
    is_recommendable_keyword,
    load_feedback_log,
    load_keyword_weights,
    record_feedback,
    reset_learning,
    score_article,
    sort_articles_by_relevance,
)

PAGE_SIZE = 12


def load_sorted_scrape_articles(project_root: Path) -> tuple[dict | None, list]:
    """`latest_scrape.json` 로드 후 관련도 순 정렬. 바이브코딩 프롬프트 등에서 재사용."""
    data = load_latest_scrape(project_root)
    if not data:
        return None, []
    arts_raw: list = list(data.get("articles") or [])
    weights = load_keyword_weights()
    return data, sort_articles_by_relevance(arts_raw, weights)


def render_news_feedback_learning_compact() -> None:
    """이슈 탭 안: 피드백 누적·학습 키워드 요약."""
    weights = load_keyword_weights()
    fb_log = load_feedback_log()
    m1, m2 = st.columns(2)
    with m1:
        st.metric("피드백 누적", f"{len(fb_log)}건")
    with m2:
        n_rec = sum(1 for k in weights if is_recommendable_keyword(k))
        st.metric("학습 키워드 수", f"{n_rec}개")
    if weights:
        rec = [(k, v) for k, v in weights.items() if is_recommendable_keyword(k)]
        top = sorted(rec, key=lambda x: -x[1])[:8]
        if top:
            st.caption("가중치 상위(일부)")
            for tok, wv in top:
                st.caption(f"· {tok}: {wv:+.2f}")
    if st.button(
        "학습 데이터 초기화",
        key="issue_news_reset_learning",
        help="feedback_log.json · keyword_weights.json 삭제",
    ):
        reset_learning()
        st.success("초기화했습니다. 페이지를 새로고침하세요.")
        st.stop()
    st.caption("데이터: `src/scraping/data/`")


def render_news_scrape_list_with_feedback(project_root: Path) -> None:
    """스크래핑 JSON 기준 기사 목록, 관련도 순, 페이지당 피드백 버튼."""
    data, sorted_arts = load_sorted_scrape_articles(project_root)
    weights = load_keyword_weights()

    ss_page = "issue_news_fb_page"
    ss_len = "issue_news_fb_len"
    if ss_page not in st.session_state:
        st.session_state[ss_page] = 0
    if ss_len not in st.session_state or st.session_state[ss_len] != len(sorted_arts):
        st.session_state[ss_page] = 0
        st.session_state[ss_len] = len(sorted_arts)

    max_page = max(0, (len(sorted_arts) - 1) // PAGE_SIZE) if sorted_arts else 0
    st.session_state[ss_page] = min(int(st.session_state[ss_page]), max_page)

    st.subheader("스크래핑 뉴스 목록 · 피드백")
    st.caption(
        "관련도 점수 순으로 표시됩니다. 피드백은 다음 스크래핑·목록 정렬에 반영됩니다. "
        "⭐ 매우 좋음 · 👍 좋음 · 👎 관심 없음"
    )

    with st.expander("관련도 학습 요약", expanded=False):
        render_news_feedback_learning_compact()

    if not data:
        st.info("아직 스크래핑 결과가 없습니다. 위 **전체 뉴스 스크래핑 실행**으로 수집하세요.")
        return

    if not sorted_arts:
        st.warning("수집된 기사가 없습니다.")
        return

    st.success(f"수집 {len(sorted_arts)}건 · 관련도 순 (학습 반영)")
    overview = [
        {
            "관련도": round(score_article(a, weights), 2),
            "출처": a.get("source"),
            "게시": a.get("published_at"),
            "제목": (a.get("title") or "")[:100],
        }
        for a in sorted_arts
    ]
    st.markdown(
        "<style>"
        "div[data-testid='stDataFrame'] > div { font-size: 0.88rem; line-height: 1.25; }"
        "</style>",
        unsafe_allow_html=True,
    )
    st.dataframe(overview, use_container_width=True, hide_index=True, height=260)

    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("◀ 이전", disabled=st.session_state[ss_page] <= 0, key="issue_news_nav_prev"):
            st.session_state[ss_page] -= 1
    with nav2:
        st.caption(
            f"페이지 {st.session_state[ss_page] + 1} / {max_page + 1} · "
            f"기사 {st.session_state[ss_page] * PAGE_SIZE + 1}–"
            f"{min((st.session_state[ss_page] + 1) * PAGE_SIZE, len(sorted_arts))}"
        )
    with nav3:
        if st.button(
            "다음 ▶",
            disabled=st.session_state[ss_page] >= max_page,
            key="issue_news_nav_next",
        ):
            st.session_state[ss_page] += 1

    start = st.session_state[ss_page] * PAGE_SIZE
    chunk = sorted_arts[start : start + PAGE_SIZE]

    st.markdown(
        "<style>"
        "div.issue-news-row-gap { margin: 0 !important; padding: 2px 0 4px 0 !important; }"
        "div.issue-news-row-gap [data-testid='column'] { min-height: 0 !important; }"
        "</style>",
        unsafe_allow_html=True,
    )

    for row_i, art in enumerate(chunk):
        idx_global = start + row_i
        sc = score_article(art, weights)
        title = art.get("title") or "(제목 없음)"
        url = art.get("url") or ""
        meta = (
            f"{art.get('source')} · 게시 {art.get('published_at', '?')} · 관련도 {sc:+.2f}"
        )
        h1, h2 = st.columns([5, 2])
        with h1:
            st.markdown(
                '<div class="issue-news-row-gap">'
                f'<p style="margin:0;line-height:1.25;font-size:0.95rem">'
                f"<b>{idx_global + 1}.</b> "
                f'<a href="{html.escape(url, quote=True)}">{html.escape(title)}</a><br/>'
                f'<span style="font-size:0.8rem;opacity:0.88">{html.escape(meta)}</span>'
                f"</p></div>",
                unsafe_allow_html=True,
            )
        with h2:
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button(
                    "⭐",
                    key=f"issue_news_love_{idx_global}",
                    help="매우 좋음 (가중치 +)",
                ):
                    n_fb, n_kw = record_feedback(art, "love")
                    st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                    st.rerun()
            with b2:
                if st.button(
                    "👍",
                    key=f"issue_news_like_{idx_global}",
                    help="좋음",
                ):
                    n_fb, n_kw = record_feedback(art, "like")
                    st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                    st.rerun()
            with b3:
                if st.button(
                    "👎",
                    key=f"issue_news_meh_{idx_global}",
                    help="관심 없음",
                ):
                    n_fb, n_kw = record_feedback(art, "meh")
                    st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                    st.rerun()
        if row_i < len(chunk) - 1:
            st.markdown(
                "<hr style='margin:0.1rem 0 0.2rem 0;border:none;"
                "border-top:1px solid rgba(250,250,250,0.12)'/>",
                unsafe_allow_html=True,
            )
