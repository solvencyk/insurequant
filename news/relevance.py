"""
기사 관련도 정렬 (scrapping/relevance.py 와 동기).
데이터: src/scraping/data/feedback_log.json, keyword_weights.json

불용·어미류 토큰은 학습·점수·추천(상위 키워드)에서 제외하고,
실손·계리·GA 등 재보험·UW 관련 키워드는 기사 단위로 가점을 줍니다.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# config 와 동일 data 폴더 사용
_DATA_DIR = Path(__file__).resolve().parent / "data"
FEEDBACK_PATH = _DATA_DIR / "feedback_log.json"
WEIGHTS_PATH = _DATA_DIR / "keyword_weights.json"

# 피드백 한 번당 토큰별 가중치 변화 (기사 내 동일 토큰은 1회만 반영)
RATING_DELTA = {
    "love": 2.0,  # 매우 좋아요
    "like": 1.0,  # 좋아요
    "meh": -1.5,  # 관심 없음
}

# 토큰별 누적 가중치 범위 (폭주 방지)
WEIGHT_CAP = 25.0

# 기사 본문·제목에서 키워드 1회 매칭당 가점 (동일 기사 내 총합 상한 DOMAIN_BOOST_CAP)
_DOMAIN_BOOST: tuple[tuple[str, float], ...] = (
    ("실손", 2.8),
    ("계리", 2.8),
    ("절판", 2.2),
    ("진단", 2.2),
    ("고액", 2.2),
    ("소액", 2.2),
    ("치료", 2.2),
)
DOMAIN_BOOST_CAP = 14.0

_GA_SCORE_RE = re.compile(r"(?<![A-Za-z])GA(?![A-Za-z])")

# 한글 토큰 끝 조사/어미 절단 (학습 키 정규화) — 긴 것부터
_TRAILING_PARTICLES: tuple[str, ...] = (
    "으로서",
    "에서는",
    "으로는",
    "에게는",
    "에서의",
    "이라도",
    "이라고",
    "스럽게",
    "에게",
    "에서",
    "부터",
    "까지",
    "처럼",
    "보다",
    "만큼",
    "이나",
    "이니",
    "이든",
    "으로",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "과",
    "와",
    "의",
    "에",
    "도",
    "만",
    "로",
    "한테",
    "께",
)

# 학습·추천에서 제외할 토큰 (완전 일치). 어미·접속·지시·빈도 높은 기능어 위주.
_NOISE_EXACT: frozenset[str] = frozenset(
    {
        # 종결·연결 어미 자주 분리 추출
        "이다",
        "이고",
        "이며",
        "이니",
        "인데",
        "이라",
        "이란",
        "이랑",
        "이다고",
        "이다는",
        "다고",
        "다며",
        "다면",
        "다는",
        "다니",
        "다도",
        "다만",
        "지만",
        "했고",
        "했던",
        "했다",
        "했다고",
        "했다는",
        "했으며",
        "하였다",
        "하였고",
        "하였으며",
        "였고",
        "였다",
        "였던",
        "였으며",
        "었다",
        "었다고",
        "않고",
        "않은",
        "않다",
        "않는",
        "였고",
        "였다",
        "았다",
        "았고",
        "겠다",
        "겠고",
        "겠는",
        "싶다",
        "싶은",
        "싶고",
        "된다",
        "되었다",
        "되었고",
        "된다고",
        "되는",
        "된",
        "된",
        "되고",
        "되며",
        "한다",
        "한다고",
        "하는",
        "하고",
        "하며",
        "한",
        "할",
        "함",
        "해도",
        "해서",
        "하면",
        "한다는",
        "있다",
        "있었다",
        "있었고",
        "있는",
        "있고",
        "있으며",
        "있어",
        "있을",
        "없다",
        "없었다",
        "없는",
        "없고",
        "없이",
        "같다",
        "같은",
        "같이",
        "같고",
        "다른",
        "다르",
        "많다",
        "많은",
        "많이",
        "적은",
        "적게",
        "위해",
        "위한",
        "위해서",
        "통해",
        "통한",
        "대해",
        "대한",
        "관해",
        "관한",
        "때문",
        "때문에",
        "따라",
        "따른",
        "따라서",
        "그래서",
        "그러나",
        "하지만",
        "그리고",
        "또한",
        "또는",
        "및",
        "등이",
        "등을",
        "등은",
        "등의",
        "등에",
        "등으로",
        "중이",
        "중인",
        "중에",
        "중을",
        "중의",
        "경우",
        "경우에",
        "만큼",
        "부터",
        "까지",
        "사이",
        "이번",
        "지난",
        "최근",
        "당시",
        "현재",
        "앞으로",
        "이후",
        "이전",
        "이상",
        "이하",
        "있다는",
        "없다는",
        "한다는",
        "된다는",
        "것으로",
        "것이",
        "것을",
        "것은",
        "것이다",
        "것이고",
        "수가",
        "수는",
        "수를",
        "수도",
        "수에",
        "때",
        "곳",
        "명이",
        "명은",
        "명을",
        "건이",
        "건을",
        "건은",
        "년에",
        "월에",
        "일에",
        "으로써",
        "로써",
        "에서도",
        "에도",
        "에는",
        "에는",
        "으로도",
        "만의",
        "만이",
        "보다는",
        "보다도",
        "처럼",
        "만큼",
        "같은데",
        "그런데",
        "그런",
        "이런",
        "저런",
        "어떤",
        "어느",
        "모든",
        "모두",
        "각각",
        "각종",
        "해당",
        "이에",
        "이를",
        "이가",
        "이는",
        "이의",
        "이와",
        "이도",
        "가능",
        "불가",
        "예정",
        "발표",
        "관계",
        "관련",
        "관련된",
        "관련해",
        "관련한",
        "대해선",
        "대해서",
        "이루",
        "이루어",
        "나타",
        "나타난",
        "나타나",
        "지적",
        "지적했다",
        "설명",
        "밝혔",
        "밝혔다",
        "전했다",
        "전한",
        "덧붙",
        "덧붙였",
        "예상",
        "전망",
        "분석",
        "분석가",
        "기자",
        "보도",
        "보도했다",
        "에따르면",
        "에따라",
        "의하면",
        "의한",
        "의해",
        "의해선",
        "통했다",
        "알려",
        "알려졌",
        "알려진",
        "확인",
        "확인됐",
        "확인된",
        "포함",
        "포함해",
        "포함한",
        "제외",
        "제외한",
        "기준",
        "기준으로",
        "대비",
        "대비해",
        "상승",
        "하락",
        "증가",
        "감소",
        "유지",
        "변경",
        "개편",
        "추진",
        "검토",
        "논의",
        "논의가",
        "논의를",
        "예고",
        "예고한",
        "조치",
        "조치를",
        "방침",
        "방침을",
        "계획",
        "계획을",
        "계획이",
        "오른",
        "올랐",
        "내렸",
        "낮아",
        "높아",
        "커졌",
        "줄어",
        "늘어",
        "이어",
        "이어졌",
        "이어지",
        "이뤄",
        "이뤄진",
        "이루어진",
        "이루어지",
        "되고있",
        "하고있",
        "있을것",
        "있을것으로",
        "것으로보",
        "것으로나",
        "것같",
        "것으로알",
        "것으로전",
        "것으로예",
        "것으로추",
        "것으로판",
        "것으로분",
        "것으로보인",
        "것으로보이",
        "것으로보여",
        "것으로보였",
        "것으로알려",
        "것으로전해",
        "것으로예상",
        "것으로추정",
        "것으로판단",
        "것으로분석",
    }
)

# 영어 불용 (토큰은 소문자로 비교)
_EN_NOISE: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "her",
        "was",
        "one",
        "our",
        "out",
        "day",
        "get",
        "has",
        "him",
        "his",
        "how",
        "its",
        "may",
        "new",
        "now",
        "old",
        "see",
        "two",
        "who",
        "way",
        "use",
        "any",
        "she",
        "has",
        "had",
        "did",
        "let",
        "put",
        "say",
        "too",
    }
)


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def tokenize(text: str) -> set[str]:
    """한글 연속 2자 이상, 영단어 3자 이상을 토큰으로 (원문 추출, 필터 전)."""
    if not text:
        return set()
    tokens: set[str] = set()
    tokens.update(re.findall(r"[가-힣]{2,}", text))
    tokens.update(re.findall(r"[A-Za-z]{3,}", text.lower()))
    return tokens


def is_noise_token(tok: str) -> bool:
    """학습·점수·추천 키워드 목록에서 제외할 토큰."""
    if not tok or len(tok) < 2:
        return True
    if tok in _NOISE_EXACT:
        return True
    if re.fullmatch(r"[A-Za-z]+", tok) and tok.lower() in _EN_NOISE:
        return True
    return False


def strip_trailing_particle(hangul_tok: str) -> str:
    """한글 토큰 끝의 조사·격조사 1회 제거. 도메인 단어 정규화용."""
    t = hangul_tok
    if not re.fullmatch(r"[가-힣]{2,}", t):
        return t
    for p in _TRAILING_PARTICLES:
        if t.endswith(p):
            stem = t[: -len(p)]
            if len(stem) >= 2:
                return stem
            break
    return t


def canonical_learning_key(tok: str) -> str | None:
    """피드백 가중치를 쌓을 키. None이면 학습에서 스킵."""
    if is_noise_token(tok):
        return None
    if re.fullmatch(r"[가-힣]{2,}", tok):
        stem = strip_trailing_particle(tok)
        if is_noise_token(stem):
            return None
        return stem if len(stem) >= 2 else None
    if re.fullmatch(r"[A-Za-z]{3,}", tok):
        return tok.lower()
    return None


def is_recommendable_keyword(tok: str) -> bool:
    """사이드바 등 '추천 키워드' 상위 표시용."""
    if is_noise_token(tok):
        return False
    if re.fullmatch(r"[가-힣]+", tok):
        stem = strip_trailing_particle(tok)
        if stem != tok and is_noise_token(stem):
            return False
    return True


def domain_boost_score(text: str) -> float:
    """제목·본문에 도메인 키가 있으면 가점 (기사당 상한)."""
    if not text:
        return 0.0
    total = 0.0
    for needle, pts in _DOMAIN_BOOST:
        if needle in text:
            total += pts
    if _GA_SCORE_RE.search(text):
        total += 2.8
    return min(total, DOMAIN_BOOST_CAP)


def load_feedback_log() -> list[dict[str, Any]]:
    if not FEEDBACK_PATH.exists():
        return []
    with open(FEEDBACK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_keyword_weights() -> dict[str, float]:
    if not WEIGHTS_PATH.exists():
        return {}
    with open(WEIGHTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in data.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _save_feedback_log(entries: list[dict[str, Any]]) -> None:
    _ensure_data_dir()
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def _save_weights(w: dict[str, float]) -> None:
    _ensure_data_dir()
    capped: dict[str, float] = {}
    for k, v in w.items():
        vv = max(-WEIGHT_CAP, min(WEIGHT_CAP, float(v)))
        if abs(vv) > 1e-6:
            capped[str(k)] = vv
    with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(capped, f, ensure_ascii=False, indent=2)


def article_text_for_tokens(article: dict[str, Any]) -> str:
    t = article.get("title") or ""
    b = (article.get("body_excerpt") or "")[:900]
    return f"{t}\n{b}"


def score_article(article: dict[str, Any], weights: dict[str, float]) -> float:
    blob = article_text_for_tokens(article)
    toks = tokenize(blob)
    # 동일 기사 내 같은 정규 키(예: 실손 / 실손을)는 한 번만 반영
    per_key: dict[str, float] = {}
    for t in toks:
        if is_noise_token(t):
            continue
        k = canonical_learning_key(t)
        if not k:
            continue
        contrib = max(weights.get(k, 0.0), weights.get(t, 0.0))
        per_key[k] = max(per_key.get(k, 0.0), contrib)
    base = sum(per_key.values())
    return base + domain_boost_score(blob)


def sort_articles_by_relevance(
    articles: list[dict[str, Any]],
    weights: dict[str, float],
) -> list[dict[str, Any]]:
    def pub_key(a: dict[str, Any]) -> str:
        return a.get("published_at") or ""

    scored = [(score_article(a, weights), pub_key(a), a) for a in articles]
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [t[2] for t in scored]


def record_feedback(
    article: dict[str, Any],
    rating_key: str,
) -> tuple[int, int]:
    """
    rating_key: 'love' | 'like' | 'meh'
    반환: (총 피드백 건수, 현재 가중치 토큰 수)
    """
    if rating_key not in RATING_DELTA:
        raise ValueError(f"unknown rating: {rating_key}")
    delta = RATING_DELTA[rating_key]
    toks = tokenize(article_text_for_tokens(article))
    if not toks:
        toks = tokenize(article.get("title") or "")

    learn_keys: set[str] = set()
    for t in toks:
        k = canonical_learning_key(t)
        if k:
            learn_keys.add(k)

    log = load_feedback_log()
    log.append(
        {
            "ts": datetime.now(KST).isoformat(),
            "url": article.get("url", ""),
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "rating": rating_key,
            "delta": delta,
            "tokens_sample": sorted(learn_keys)[:40],
        }
    )
    _save_feedback_log(log)

    weights = load_keyword_weights()
    for k in learn_keys:
        weights[k] = weights.get(k, 0.0) + delta
        weights[k] = max(-WEIGHT_CAP, min(WEIGHT_CAP, weights[k]))
    _save_weights(weights)
    return len(log), len(load_keyword_weights())


def reset_learning() -> None:
    _ensure_data_dir()
    if FEEDBACK_PATH.exists():
        FEEDBACK_PATH.unlink()
    if WEIGHTS_PATH.exists():
        WEIGHTS_PATH.unlink()
