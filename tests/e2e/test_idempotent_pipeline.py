"""End-to-end idempotency gate for the downloader engine.

Covers Stage 6-3 of the validation harness: a second engine run on the
same input must skip every already-downloaded file (status="skipped"),
keep the manifest deduped on source_url, and leave checksums unchanged.

The test stubs the site handler so the network is never touched; the
gate under test is the engine's cache + prefetched_path path, which is
the new code path used by the Life Insurance Association handler.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solvency.downloader.base import (  # noqa: E402
    DownloadCandidate,
    DownloaderEngine,
)
from solvency.config import settings  # noqa: E402


@pytest.fixture
def isolated_disclosure_dir(tmp_path):
    """Redirect settings.disclosure_dir to a tempdir for this test.

    Settings is a frozen dataclass; ``monkeypatch.setattr`` raises
    ``FrozenInstanceError``. We patch via ``object.__setattr__`` and
    restore in teardown.
    """
    target = tmp_path / "disclosure"
    target.mkdir()
    original = settings.disclosure_dir
    object.__setattr__(settings, "disclosure_dir", target)
    yield target
    object.__setattr__(settings, "disclosure_dir", original)


def _make_pdf(workdir: Path, name: str, payload: bytes) -> Path:
    p = workdir / name
    p.write_bytes(payload)
    return p


def _candidate_for(source_pdf: Path, source_url: str) -> DownloadCandidate:
    return DownloadCandidate(
        company_code="KR0068",
        company_dirname="KR0068_한화생명",
        period="FY2025_Q4",
        title="한화생명_25Q4",
        fiscal_year="FY2025",
        quarter="Q4",
        disclosure_date="2026-01-15",
        source_url=source_url,
        prefetched_path=source_pdf,
    )


def test_second_run_skips_already_downloaded(isolated_disclosure_dir, tmp_path):
    """First run downloads, second run must report status='skipped'."""
    fixture_url = "https://pub.insure.or.kr/zip#KR0068_Q4"

    # Run 1: hand the engine a freshly-staged "prefetched" PDF.
    staging1 = tmp_path / "staging1"
    staging1.mkdir()
    pdf1 = _make_pdf(staging1, "한화생명.pdf", b"%PDF-1.4 fake-content")
    handler_run1 = lambda ctx: [_candidate_for(pdf1, fixture_url)]  # noqa: E731

    profile = {"company_code": "LIFE_TEST", "site_type": "stub"}
    engine = DownloaderEngine(profile, {"stub": handler_run1})
    [result1] = engine.run()
    assert result1.status == "downloaded", f"first run unexpected: {result1}"
    assert result1.local_path is not None and result1.local_path.exists()
    sha_after_run1 = result1.sha256

    # Run 2: re-stage an identical (but different path) PDF; engine should skip.
    staging2 = tmp_path / "staging2"
    staging2.mkdir()
    pdf2 = _make_pdf(staging2, "한화생명.pdf", b"%PDF-1.4 fake-content")
    handler_run2 = lambda ctx: [_candidate_for(pdf2, fixture_url)]  # noqa: E731

    engine2 = DownloaderEngine(profile, {"stub": handler_run2})
    [result2] = engine2.run()

    assert result2.status == "skipped", f"second run not idempotent: {result2}"
    assert result2.sha256 == sha_after_run1, "sha256 drifted across runs"
    # Skip path must not consume the prefetched staging file.
    assert pdf2.exists(), "engine should not move file when skipping"


def test_manifest_records_skip_on_second_run(isolated_disclosure_dir, tmp_path):
    """Manifest CSV must capture both 'downloaded' and 'skipped' rows."""
    import csv

    url = "https://pub.insure.or.kr/zip#KR0069_Q4"
    profile = {"company_code": "LIFE_TEST", "site_type": "stub"}

    staging = tmp_path / "staging"
    staging.mkdir()
    pdf = _make_pdf(staging, "삼성생명.pdf", b"%PDF-1.4 sample")

    cand = DownloadCandidate(
        company_code="KR0069",
        company_dirname="KR0069_삼성생명",
        period="FY2025_Q4",
        title="삼성생명_25Q4",
        fiscal_year="FY2025",
        quarter="Q4",
        disclosure_date="2026-01-15",
        source_url=url,
        prefetched_path=pdf,
    )

    DownloaderEngine(profile, {"stub": lambda ctx: [cand]}).run()

    # Re-stage and run again; engine should produce a 'skipped' manifest row.
    staging2 = tmp_path / "staging2"
    staging2.mkdir()
    pdf_again = _make_pdf(staging2, "삼성생명.pdf", b"%PDF-1.4 sample")
    cand2 = DownloadCandidate(**{**cand.__dict__, "prefetched_path": pdf_again})
    DownloaderEngine(profile, {"stub": lambda ctx: [cand2]}).run()

    manifest = isolated_disclosure_dir / "_meta" / "LIFE_TEST_download_cache.csv"
    assert manifest.exists()
    with manifest.open("r", encoding="utf-8", newline="") as fp:
        rows = list(csv.DictReader(fp))

    statuses = [r["status"] for r in rows if r["source_url"] == url]
    assert statuses == ["downloaded", "skipped"], f"unexpected statuses: {statuses}"


def test_failed_status_when_prefetched_file_missing(isolated_disclosure_dir, tmp_path):
    """Engine must record status='failed' (not crash) on missing prefetched file."""
    cand = DownloadCandidate(
        company_code="KR0070",
        company_dirname="KR0070_에이비엘생명보험",
        period="FY2025_Q4",
        title="ABL_25Q4",
        fiscal_year="FY2025",
        quarter="Q4",
        disclosure_date="2026-01-15",
        source_url="https://pub.insure.or.kr/zip#KR0070_Q4",
        prefetched_path=tmp_path / "does_not_exist.pdf",
    )
    [result] = DownloaderEngine(
        {"company_code": "LIFE_TEST", "site_type": "stub"},
        {"stub": lambda ctx: [cand]},
    ).run()
    assert result.status == "failed"
    assert "missing" in (result.error_message or "").lower()
