# -*- coding: utf-8 -*-
"""정정본 병존 저장(save_versioned_pdf)과 disclosure_pdfs() 의 회사-수 안전성 회귀 테스트.

배경: 2026-09-12 발주(downloader 후속 작업 1) — 같은 (분기,회사) 의 새 게시물이 기존 raw 를
조용히 덮어쓰던 문제를 고쳤다(`scripts/_disclosure_pdf_paths.py::save_versioned_pdf`). 실측
census: `data/disclosure/*/raw/*_amended*.pdf` 110개 중 원본과 병존한 건 1건뿐이고 그나마
바이트가 동일했다 — 즉 병존 매커니즘 자체가 없었다(과거 백필이 최신본 하나만 받아
`_amended` 로 이름 붙인 것).

이 테스트는 두 가지를 고정한다:
  1. `save_versioned_pdf` 의 new / unchanged / versioned / idempotent 4-분기 동작.
  2. 공유 해석기 `disclosure_pdfs()` 가 ``<code>_<name>_v<date>.pdf`` 를 별개 회사로 오인하지
     않는다(같은 KR 코드의 여러 버전으로만 잡힌다) — 발주 원문이 명시적으로 요구한 검사.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from _disclosure_pdf_paths import disclosure_pdfs, save_versioned_pdf  # noqa: E402


# ---------------------------------------------------------------------------
# save_versioned_pdf
# ---------------------------------------------------------------------------

def test_save_new_file(tmp_path):
    dest = tmp_path / "KR0150_서울보증보험.pdf"
    saved, status = save_versioned_pdf(dest, b"%PDF-1.4 original")

    assert status == "new"
    assert saved == dest
    assert dest.read_bytes() == b"%PDF-1.4 original"
    assert not (tmp_path / "_versions.json").exists()


def test_save_unchanged_bytes_is_noop(tmp_path):
    dest = tmp_path / "KR0150_서울보증보험.pdf"
    save_versioned_pdf(dest, b"%PDF-1.4 original")
    mtime_before = dest.stat().st_mtime_ns

    saved, status = save_versioned_pdf(dest, b"%PDF-1.4 original")

    assert status == "unchanged"
    assert saved == dest
    assert dest.stat().st_mtime_ns == mtime_before  # 실제로 재저장(덮어쓰기)되지 않았다
    assert not (tmp_path / "_versions.json").exists()


def test_save_different_bytes_coexists_and_preserves_original(tmp_path):
    dest = tmp_path / "KR0150_서울보증보험.pdf"
    save_versioned_pdf(dest, b"%PDF-1.4 original")

    saved, status = save_versioned_pdf(
        dest,
        b"%PDF-1.4 amended",
        posted="20260912",
        title="정정 경영공시",
        url="https://example.com/x.pdf",
    )

    assert status == "versioned"
    assert saved != dest
    assert saved.name == "KR0150_서울보증보험_v20260912.pdf"
    # 원본은 손대지 않는다
    assert dest.read_bytes() == b"%PDF-1.4 original"
    assert saved.read_bytes() == b"%PDF-1.4 amended"

    sidecar = json.loads((tmp_path / "_versions.json").read_text(encoding="utf-8"))
    entries = sidecar["KR0150_서울보증보험.pdf"]
    assert len(entries) == 1
    assert entries[0]["file"] == "KR0150_서울보증보험_v20260912.pdf"
    assert entries[0]["posted"] == "20260912"
    assert entries[0]["title"] == "정정 경영공시"
    assert entries[0]["url"] == "https://example.com/x.pdf"
    assert entries[0]["sha256"] == hashlib.sha256(b"%PDF-1.4 amended").hexdigest()


def test_save_same_version_rerun_is_idempotent(tmp_path):
    dest = tmp_path / "KR0150_서울보증보험.pdf"
    save_versioned_pdf(dest, b"%PDF-1.4 original")
    saved1, status1 = save_versioned_pdf(dest, b"%PDF-1.4 amended", posted="20260912")
    assert status1 == "versioned"

    # 같은 날 같은 정정본을 다시 받아도 재저장/중복 파일 생성이 없다
    saved2, status2 = save_versioned_pdf(dest, b"%PDF-1.4 amended", posted="20260912")
    assert status2 == "unchanged"
    assert saved2 == saved1

    versioned_files = sorted(tmp_path.glob("KR0150_서울보증보험_v*.pdf"))
    assert len(versioned_files) == 1  # _2 같은 중복 파일이 생기지 않는다


def test_save_third_distinct_version_same_day_gets_suffixed(tmp_path):
    dest = tmp_path / "KR0150_서울보증보험.pdf"
    save_versioned_pdf(dest, b"%PDF-1.4 original")
    save_versioned_pdf(dest, b"%PDF-1.4 amended-A", posted="20260912")
    saved3, status3 = save_versioned_pdf(dest, b"%PDF-1.4 amended-B", posted="20260912")

    assert status3 == "versioned"
    assert saved3.name == "KR0150_서울보증보험_v20260912_2.pdf"
    assert dest.read_bytes() == b"%PDF-1.4 original"  # 원본 불변


# ---------------------------------------------------------------------------
# disclosure_pdfs() 의 회사-수 안전성 (2026-09-12 발주 원문 명시 테스트)
# ---------------------------------------------------------------------------

def test_disclosure_pdfs_versioned_file_does_not_create_phantom_company(tmp_path):
    """KR0150 의 버전 파일이 추가돼도 그 기간의 distinct 회사 수는 늘지 않는다."""
    period = "FY2026_Q9"  # 실데이터와 안 섞이게 존재하지 않는 가짜 분기
    raw = tmp_path / period / "raw"
    raw.mkdir(parents=True)

    (raw / "KR0001_메리츠화재해상보험.pdf").write_bytes(b"%PDF-1")
    (raw / "KR0002_한화손해보험.pdf").write_bytes(b"%PDF-2")
    (raw / "KR0150_서울보증보험.pdf").write_bytes(b"%PDF-150-orig")

    codes_before = {p.stem.split("_")[0] for p in raw.glob("*.pdf")}
    assert codes_before == {"KR0001", "KR0002", "KR0150"}

    # 발주 원문과 동일한 이름의 정정본 병존 파일을 추가
    (raw / "KR0150_서울보증보험_v20260912.pdf").write_bytes(b"%PDF-150-amended")

    codes_after = {p.stem.split("_")[0] for p in raw.glob("*.pdf")}
    assert codes_after == codes_before  # 회사 수 불변(3 그대로, 4 로 늘지 않는다)

    # disclosure_pdfs() 는 KR0150 조회 시 두 버전을 다 반환하되 여전히 KR0150 소속이다
    hits = disclosure_pdfs(period, "KR0150", root=tmp_path)
    assert len(hits) == 2
    assert all(p.name.startswith("KR0150_") for p in hits)

    # 다른 회사 조회에는 절대 섞여 들어오지 않는다
    kr0001_hits = disclosure_pdfs(period, "KR0001", root=tmp_path)
    assert [p.name for p in kr0001_hits] == ["KR0001_메리츠화재해상보험.pdf"]

    # 존재하지 않는 코드는 여전히 빈 목록(prefix 오매칭 없음)
    assert disclosure_pdfs(period, "KR0015", root=tmp_path) == []
