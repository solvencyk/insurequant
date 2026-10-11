#!/usr/bin/env python3
"""PDF 원문 텍스트의 프로세스 내 읽기 캐시 (게이트 속도 전용, 판정 불변).

**왜 있나 (2026-10-12).** `validate_kics_disclosure.py` 는 등재 예외의 인용 원천을 매 실행
다시 열어 재검산한다(`_exemption_provenance_findings` · `_marker_grade_census` ·
`_row_anchor_check`). 같은 PDF(2,372쪽) 의 `get_text()` 를 게이트 1회에 여러 번, 커버리지
변이시험(`tests/test_rule_coverage_manifest.py`)은 게이트를 49번 돌려 그만큼 또 반복한다.
변이시험이 바꾸는 것은 K-ICS 마스터 값뿐이라 PDF 는 그대로인데 매번 처음부터 읽었다.

**캐시하는 것은 텍스트뿐이다.** 판정(마커 존재·행 귀속·밀도)은 호출부가 매번 새로 계산한다.

**캐시 키 = (절대경로, 파일 크기, mtime_ns).** 파일이 바뀌면(크기나 수정시각) 키가 달라져
옛 항목은 자동으로 버려진다 — 같은 경로에 다른 내용의 PDF 를 두면 새로 읽는다.
**메모리 상한**: 항목(파일) 단위 LRU, 추정 바이트 합이 `MAX_BYTES` 를 넘으면 오래된 파일부터 버린다.

호출부와 같은 예외 계약을 지킨다: 열기 실패는 그대로 예외로 올라가고(호출부가 try/except 로
처리), 범위 밖 쪽 번호는 호출부가 `page_count` 로 걸러낸다. 실패는 캐시하지 않는다.
"""
from __future__ import annotations

import os
from collections import OrderedDict

# 추정 바이트 상한. 실측(2026-10-12): 인용 원천 PDF 59개 중 전체 쪽을 읽는 것은 16개로,
# 텍스트 합계는 수십 MB 수준이다. 상한은 폭주 방지용이다.
MAX_BYTES = 400 * 1024 * 1024
_WORD_BYTES = 160          # get_text("words") 튜플 1개의 추정 크기

_ENTRIES: "OrderedDict[tuple, _Entry]" = OrderedDict()
_total = 0
STATS = {"open": 0, "text_hit": 0, "text_miss": 0, "words_hit": 0, "words_miss": 0}


class _Entry:
    __slots__ = ("page_count", "texts", "words", "bytes")

    def __init__(self, page_count: int):
        self.page_count = page_count
        self.texts: dict[int, str] = {}
        self.words: dict[int, tuple] = {}
        self.bytes = 0


def _key(path) -> tuple:
    p = os.path.abspath(os.fspath(path))
    st = os.stat(p)
    return (p, st.st_size, st.st_mtime_ns)


def clear() -> None:
    global _total
    _ENTRIES.clear()
    _total = 0


def _open(path):
    import fitz  # 지연 임포트: 인용 PDF 를 실제로 읽는 호출에서만
    STATS["open"] += 1
    return fitz.open(path)


def _entry(path) -> tuple[tuple, _Entry]:
    global _total
    key = _key(path)
    ent = _ENTRIES.get(key)
    if ent is not None:
        _ENTRIES.move_to_end(key)
        return key, ent
    # 같은 경로의 옛 상태(크기·mtime 이 다른 키)는 즉시 버린다 — 바뀐 파일의 유령 텍스트 방지
    for k in [k for k in _ENTRIES if k[0] == key[0]]:
        _total -= _ENTRIES.pop(k).bytes
    doc = _open(path)
    try:
        ent = _Entry(doc.page_count)
    finally:
        doc.close()
    _ENTRIES[key] = ent
    return key, ent


def _account(key: tuple, ent: _Entry, added: int) -> None:
    global _total
    ent.bytes += added
    _total += added
    while _total > MAX_BYTES and len(_ENTRIES) > 1:
        old_key = next(iter(_ENTRIES))
        if old_key == key:       # 방금 쓴 항목은 지키고 그다음으로 오래된 것을 버린다
            _ENTRIES.move_to_end(key)
            continue
        _total -= _ENTRIES.pop(old_key).bytes


def page_count(path) -> int:
    """PDF 쪽수 (`fitz.open(path).page_count` 와 같은 값)."""
    return _entry(path)[1].page_count


def page_text(path, n: int) -> str:
    """0-기준 쪽 n 의 `page.get_text()` (호출부가 0 <= n < page_count 를 보장한다)."""
    key, ent = _entry(path)
    t = ent.texts.get(n)
    if t is not None:
        STATS["text_hit"] += 1
        return t
    STATS["text_miss"] += 1
    doc = _open(path)
    try:
        t = doc[n].get_text()
    finally:
        doc.close()
    ent.texts[n] = t
    _account(key, ent, len(t) * 2)
    return t


def page_texts(path, idx) -> list[str]:
    """쪽 번호 목록(0-기준)의 `get_text()` 리스트. 안 읽은 쪽만 한 번 열어 채운다."""
    idx = list(idx)
    key, ent = _entry(path)
    missing = [n for n in idx if n not in ent.texts]
    if missing:
        doc = _open(path)
        try:
            added = 0
            for n in missing:
                if n in ent.texts:
                    continue
                t = doc[n].get_text()
                ent.texts[n] = t
                added += len(t) * 2
                STATS["text_miss"] += 1
        finally:
            doc.close()
        _account(key, ent, added)
    STATS["text_hit"] += len(idx) - len(missing)
    return [ent.texts[n] for n in idx]


def page_words_many(path, idx) -> list[tuple]:
    """쪽 번호 목록(0-기준)의 words 튜플 리스트. 안 읽은 쪽만 한 번 열어 채운다."""
    idx = list(idx)
    key, ent = _entry(path)
    missing = [n for n in idx if n not in ent.words]
    if missing:
        doc = _open(path)
        try:
            added = 0
            for n in missing:
                if n in ent.words:
                    continue
                w = tuple(doc[n].get_text("words"))
                ent.words[n] = w
                added += len(w) * _WORD_BYTES
                STATS["words_miss"] += 1
        finally:
            doc.close()
        _account(key, ent, added)
    STATS["words_hit"] += len(idx) - len(missing)
    return [ent.words[n] for n in idx]


def page_words(path, n: int) -> tuple:
    """0-기준 쪽 n 의 `page.get_text("words")` (튜플로 고정 — 호출부는 정렬 사본만 쓴다)."""
    key, ent = _entry(path)
    w = ent.words.get(n)
    if w is not None:
        STATS["words_hit"] += 1
        return w
    STATS["words_miss"] += 1
    doc = _open(path)
    try:
        w = tuple(doc[n].get_text("words"))
    finally:
        doc.close()
    ent.words[n] = w
    _account(key, ent, len(w) * _WORD_BYTES)
    return w
