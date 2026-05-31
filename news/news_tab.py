"""
뉴스 스크래핑 Agent UI. hub_app 또는 scrapping/app.py 에서 import.
"""

from __future__ import annotations

import streamlit as st

from prompts import NEWS_INSIGHT_SYSTEM_PROMPT
from relevance import (
    is_recommendable_keyword,
    load_feedback_log,
    load_keyword_weights,
    record_feedback,
    reset_learning,
    score_article,
    sort_articles_by_relevance,
)
from scraper import articles_to_llm_context, load_latest_scrape, run_scrape

PAGE_SIZE = 12


def call_openai(api_key: str, system_prompt: str, user_content: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.35,
    )
    return response.choices[0].message.content or ""


def call_gemini(api_key: str, model_id: str, system_prompt: str, user_content: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    # 시스템 지시와 본문 분리: Windows 등에서 한글이 한 문자열로 합쳐질 때 ascii 인코딩 오류가 나는 경우 완화
    user_body = f"[스크래핑 뉴스 묶음]\n\n{user_content}"
    response = client.models.generate_content(
        model=model_id,
        contents=user_body,
        config=types.GenerateContentConfig(
            temperature=0.35,
            system_instruction=system_prompt,
        ),
    )
    return response.text or ""


def render_news_sidebar() -> None:
    """허브 사이드바에서 호출: 뉴스 Agent 전용 블록."""
    st.markdown("### 📰 뉴스 Agent")
    st.caption("관련도 학습 (피드백 누적)")
    weights = load_keyword_weights()
    fb_log = load_feedback_log()
    st.metric("피드백 누적", f"{len(fb_log)}건")
    n_rec = sum(1 for k in weights if is_recommendable_keyword(k))
    st.metric("학습 키워드 수", f"{n_rec}개", help=f"JSON 전체 키 {len(weights)}개 중 불용·어미 제외")
    if weights:
        rec = [(k, v) for k, v in weights.items() if is_recommendable_keyword(k)]
        top = sorted(rec, key=lambda x: -x[1])[:12]
        st.caption("가중치 상위(일부, 불용·어미 제외)")
        if not top:
            st.caption("· (표시 가능한 키워드가 없음 — 기존 JSON에 불용만 남았을 수 있음)")
        for tok, wv in top:
            st.caption(f"· {tok}: {wv:+.2f}")
    if st.button("학습 데이터 초기화", key="news_reset_learning", help="feedback_log.json · keyword_weights.json 삭제"):
        reset_learning()
        st.success("초기화했습니다. 페이지를 새로고침하세요.")
        st.stop()
    st.caption("데이터: `scrapping/data/`")


def render_news_main(
    api_key: str,
    llm_provider: str,
    gemini_model: str,
) -> None:
    st.title("📰 보험 뉴스 스크래핑 · AI 해석")
    st.caption(
        "뉴스1(보험·카드), 보험매일(fins.co.kr), 보험저널 — 최근 7일 수집. "
        "기사별 피드백은 왼쪽 사이드바에서 확인·초기화할 수 있습니다."
    )

    st.subheader("1) 스크래핑")
    st.write(
        "버튼을 누르면 로컬에서 목록 페이지를 읽고 기사별 본문 일부를 수집합니다. "
        "사이트 구조 변경·차단 시 일부 출처만 비어 있을 수 있습니다."
    )

    if st.button("스크래핑 실시", type="primary", use_container_width=False, key="news_do_scrape"):
        with st.spinner("스크래핑 중… (출처당 요청 간 딜레이가 있어 1~3분 걸릴 수 있습니다)"):
            try:
                payload = run_scrape()
                st.success(
                    f"완료: {payload.get('article_count', 0)}건 (저장: scrapping/data/latest_scrape.json)"
                )
            except Exception as e:
                st.error(f"스크래핑 오류: {e}")
                st.stop()

    data = load_latest_scrape()
    arts_raw: list = list(data.get("articles") or []) if data else []
    weights = load_keyword_weights()
    sorted_arts = sort_articles_by_relevance(arts_raw, weights)

    if "news_fb_page" not in st.session_state:
        st.session_state.news_fb_page = 0
    if "news_fb_len" not in st.session_state or st.session_state.news_fb_len != len(sorted_arts):
        st.session_state.news_fb_page = 0
        st.session_state.news_fb_len = len(sorted_arts)

    max_page = max(0, (len(sorted_arts) - 1) // PAGE_SIZE) if sorted_arts else 0
    st.session_state.news_fb_page = min(st.session_state.news_fb_page, max_page)

    if data and sorted_arts:
        st.success(f"수집 {len(sorted_arts)}건 · 관련도 점수 순으로 표시 (학습 반영)")
        overview = [
            {
                "관련도": round(score_article(a, weights), 2),
                "출처": a.get("source"),
                "게시": a.get("published_at"),
                "제목": (a.get("title") or "")[:100],
            }
            for a in sorted_arts
        ]
        st.dataframe(overview, use_container_width=True, hide_index=True)

        st.subheader("기사별 피드백")
        st.caption("⭐ 매우 좋아요 · 👍 좋아요 · 👎 관심 없음 (클릭 시 즉시 저장)")

        nav1, nav2, nav3 = st.columns([1, 3, 1])
        with nav1:
            if st.button("◀ 이전 페이지", disabled=st.session_state.news_fb_page <= 0, key="news_nav_prev"):
                st.session_state.news_fb_page -= 1
        with nav2:
            st.caption(
                f"페이지 {st.session_state.news_fb_page + 1} / {max_page + 1} "
                f"(기사 {st.session_state.news_fb_page * PAGE_SIZE + 1}–"
                f"{min((st.session_state.news_fb_page + 1) * PAGE_SIZE, len(sorted_arts))})"
            )
        with nav3:
            if st.button("다음 페이지 ▶", disabled=st.session_state.news_fb_page >= max_page, key="news_nav_next"):
                st.session_state.news_fb_page += 1

        start = st.session_state.news_fb_page * PAGE_SIZE
        chunk = sorted_arts[start : start + PAGE_SIZE]

        for i, art in enumerate(chunk):
            idx_global = start + i
            sc = score_article(art, weights)
            with st.container():
                h1, h2 = st.columns([5, 1])
                with h1:
                    title = art.get("title") or "(제목 없음)"
                    url = art.get("url") or ""
                    st.markdown(f"**{idx_global + 1}.** [{title}]({url})")
                    st.caption(
                        f"{art.get('source')} · 게시 {art.get('published_at', '?')} · 관련도 **{sc:+.2f}**"
                    )
                with h2:
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("⭐", key=f"news_love_{idx_global}", help="매우 좋아요"):
                            n_fb, n_kw = record_feedback(art, "love")
                            st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                    with b2:
                        if st.button("👍", key=f"news_like_{idx_global}", help="좋아요"):
                            n_fb, n_kw = record_feedback(art, "like")
                            st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                    with b3:
                        if st.button("👎", key=f"news_meh_{idx_global}", help="관심 없음"):
                            n_fb, n_kw = record_feedback(art, "meh")
                            st.toast(f"저장됨 (피드백 {n_fb}건 · 키워드 {n_kw}개)")
                st.divider()

    elif data:
        st.warning("수집된 기사가 없습니다.")
    else:
        st.info("아직 스크래핑 결과가 없습니다. 위 버튼으로 수집하세요.")

    st.divider()
    st.subheader("2) 생성형 AI 해석 · 바이브코딩 프롬프트")

    if st.button("AI 해석 생성", type="primary", use_container_width=False, key="news_run_llm"):
        if not api_key:
            st.error("API Key를 입력해주세요. (왼쪽 사이드바)")
            st.stop()
        if not data or not sorted_arts:
            st.warning("먼저 스크래핑을 실행해 기사가 있어야 합니다.")
            st.stop()
        user_content = articles_to_llm_context(data, articles=sorted_arts)
        with st.spinner("생성형 AI가 분석 중입니다…"):
            try:
                if llm_provider == "OpenAI":
                    report = call_openai(api_key, NEWS_INSIGHT_SYSTEM_PROMPT, user_content)
                else:
                    report = call_gemini(api_key, gemini_model, NEWS_INSIGHT_SYSTEM_PROMPT, user_content)
            except Exception as e:
                st.error(f"LLM 호출 오류: {e}")
                st.stop()

        st.divider()
        st.subheader("📋 AI 해석 결과")
        _, report_col, _ = st.columns([1.5, 2, 1.5])
        with report_col:
            st.markdown(report)
        st.download_button(
            label="📥 해석 결과 다운로드 (TXT)",
            data=report,
            file_name="news_insight_report.txt",
            mime="text/plain",
            key="news_download_report",
        )
