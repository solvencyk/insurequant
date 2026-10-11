# -*- coding: utf-8 -*-
"""scripts/_pdf_text_cache.py 변이시험 (2026-10-12, 게이트 속도 티켓).

캐시는 속도만 바꾸고 판정은 바꾸면 안 된다. 그래서 ① 캐시 값 = fitz 직접 값 ② 재호출이 PDF 를
다시 읽지 않는다 ③ **같은 경로에 다른 내용의 PDF 를 두면 반드시 새로 읽는다**(stale 방지,
이 시험이 핵심) ④ 메모리 상한이 작동한다 ⑤ 게이트 함수(`_verify_absent_markers`)가 파일을
바꾸면 판정이 바뀐다 — 를 확인한다.
"""
import os
import sys
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import _pdf_text_cache as C  # noqa: E402


def _make_pdf(path: Path, pages: list[str]) -> None:
    doc = fitz.open()
    for t in pages:
        pg = doc.new_page()
        pg.insert_text((72, 100), t)
    doc.save(str(path))
    doc.close()


@pytest.fixture(autouse=True)
def _fresh():
    C.clear()
    for k in C.STATS:
        C.STATS[k] = 0
    yield
    C.clear()


def test_values_equal_direct_fitz(tmp_path):
    p = tmp_path / "a.pdf"
    _make_pdf(p, ["alpha 111", "beta 222", "gamma 333"])
    d = fitz.open(str(p))
    try:
        assert C.page_count(p) == d.page_count == 3
        assert C.page_texts(p, [0, 1, 2]) == [d[i].get_text() for i in range(3)]
        assert C.page_text(p, 1) == d[1].get_text()
        assert C.page_words(p, 2) == tuple(d[2].get_text("words"))
        assert C.page_words_many(p, [2, 0]) == [tuple(d[2].get_text("words")),
                                                tuple(d[0].get_text("words"))]
    finally:
        d.close()


def test_second_read_does_not_reopen(tmp_path):
    p = tmp_path / "a.pdf"
    _make_pdf(p, ["alpha", "beta"])
    C.page_texts(p, [0, 1])
    C.page_words_many(p, [0, 1])
    opens = C.STATS["open"]
    C.page_texts(p, [0, 1])
    C.page_text(p, 0)
    C.page_words_many(p, [1, 0])
    C.page_count(p)
    assert C.STATS["open"] == opens, "캐시 적중인데 PDF 를 다시 열었다"


def test_changed_file_invalidates_size_changes(tmp_path):
    p = tmp_path / "a.pdf"
    _make_pdf(p, ["OLD CONTENT ONLY"])
    assert "OLD CONTENT" in C.page_texts(p, [0])[0]
    _make_pdf(p, ["NEW CONTENT", "second page"])           # 같은 경로, 다른 내용·쪽수
    assert C.page_count(p) == 2
    t = C.page_texts(p, [0])[0]
    assert "NEW CONTENT" in t and "OLD CONTENT" not in t, "stale 텍스트를 돌려줬다"


def test_changed_file_invalidates_same_size_new_mtime(tmp_path):
    """바이트 길이가 같아도 mtime_ns 가 다르면 새로 읽는다."""
    p = tmp_path / "a.pdf"
    _make_pdf(p, ["AAAAAAAAAA"])
    size = p.stat().st_size
    assert "AAAAAAAAAA" in C.page_texts(p, [0])[0]
    _make_pdf(p, ["BBBBBBBBBB"])
    assert p.stat().st_size == size, "시험 전제: 같은 크기여야 한다"
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    t = C.page_texts(p, [0])[0]
    assert "BBBBBBBBBB" in t and "AAAAAAAAAA" not in t


def test_stale_entry_is_dropped_not_leaked(tmp_path):
    p = tmp_path / "a.pdf"
    _make_pdf(p, ["one"])
    C.page_texts(p, [0])
    _make_pdf(p, ["two two two"])
    C.page_texts(p, [0])
    same_path = [k for k in C._ENTRIES if k[0] == os.path.abspath(p)]
    assert len(same_path) == 1, "같은 경로의 옛 상태가 캐시에 남았다"


def test_memory_cap_evicts_oldest_file(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "MAX_BYTES", 1)          # 어떤 파일이든 상한 초과
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    _make_pdf(a, ["alpha text"])
    _make_pdf(b, ["beta text"])
    C.page_texts(a, [0])
    C.page_texts(b, [0])
    assert len(C._ENTRIES) == 1
    assert next(iter(C._ENTRIES))[0] == os.path.abspath(b), "방금 쓴 파일이 지켜져야 한다"
    assert "alpha" in C.page_texts(a, [0])[0], "버린 뒤에도 다시 읽으면 값이 맞아야 한다"


def test_open_failure_propagates_and_is_not_cached(tmp_path):
    p = tmp_path / "broken.pdf"
    p.write_bytes(b"not a pdf at all")
    with pytest.raises(Exception):
        C.page_count(p)
    assert not C._ENTRIES
    with pytest.raises(FileNotFoundError):
        C.page_count(tmp_path / "missing.pdf")


def test_gate_verdict_follows_file_changes(tmp_path):
    """게이트 함수 수준: 인용 PDF 를 바꾸면 같은 spec 의 판정이 바뀐다 (캐시가 판정을 굳히지 않는다)."""
    import validate_kics_disclosure as gate
    p = tmp_path / "cited.pdf"
    spec = {"file": str(p), "absent_markers": ["SECRETTABLE"]}
    _make_pdf(p, ["nothing relevant here"])
    contradicted, _why = gate._verify_absent_markers(spec)
    assert contradicted is False
    _make_pdf(p, ["a SECRETTABLE appears"])
    contradicted, why = gate._verify_absent_markers(spec)
    assert contradicted is True and "SECRETTABLE" in why
    _make_pdf(p, ["gone again"])
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 7_000_000_000))
    assert gate._verify_absent_markers(spec)[0] is False


def test_gate_row_anchor_follows_file_changes(tmp_path):
    import validate_kics_disclosure as gate
    p = tmp_path / "rows.pdf"
    doc = fitz.open()
    pg = doc.new_page()
    pg.insert_text((72, 100), "ROWLABEL")
    pg.insert_text((300, 100), "12345")        # 같은 행(y 동일)
    doc.save(str(p))
    doc.close()
    ok, d = gate._row_anchor_check(p, [1], "ROWLABEL", "12345")
    assert ok is True and d is not None
    doc = fitz.open()
    pg = doc.new_page()
    pg.insert_text((72, 100), "ROWLABEL")
    pg.insert_text((300, 400), "12345")        # 다른 행으로 이동
    doc.save(str(p))
    doc.close()
    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 9_000_000_000))
    ok2, d2 = gate._row_anchor_check(p, [1], "ROWLABEL", "12345")
    assert ok2 is False
