"""Base downloader engine.

The pipeline ships a single downloader engine. Per-company behaviour is
expressed as a YAML "profile" loaded at runtime instead of forking a
new ``*_downloader.py`` script. The engine implements the parts that
all sites share: Chrome setup, download directory, manifest writing,
retries, idempotent skip-if-already-downloaded.

Site-specific actions (login flow, table selectors, pagination, file
URL extraction) are described declaratively in the profile and dispatched
by ``site_type`` (case A / B / C). Each site_type maps to a small handler
module in this package.
"""

from __future__ import annotations

import csv
import dataclasses
import gc
import hashlib
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from solvency.config import settings
from solvency.verification import (
    VerificationLevel,
    normalize_file_acl,
    verify_pdf,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class DownloadCandidate:
    """One PDF that the engine has discovered and may download.

    ``period`` is the canonical bucket the file lands in on disk (e.g.
    ``FY2025_Q4``). The filename stem is the company directory name so
    the resulting layout is::

        data/disclosure/<period>/pdf/<company_dirname>.pdf
    """

    company_code: str
    company_dirname: str
    period: str
    title: str
    fiscal_year: str | None
    quarter: str | None
    disclosure_date: str | None
    source_url: str
    is_supplement: bool = False
    # Optional: handler may pre-fetch the file (e.g. ZIP-extracted PDF) and
    # hand the path off so the engine performs verification + manifest write
    # instead of issuing a fresh HTTP GET against ``source_url``.
    prefetched_path: Path | None = None


@dataclasses.dataclass
class DownloadResult:
    """Outcome of a single download attempt."""

    candidate: DownloadCandidate
    local_path: Path | None
    sha256: str | None
    status: str
    error_message: str | None = None
    bytes_downloaded: int = 0
    verification_level: str = ""
    verification_reasons: str = ""


SiteHandler = Callable[["DownloadContext"], Iterable[DownloadCandidate]]


@dataclasses.dataclass
class DownloadContext:
    """Runtime context handed to a site-specific handler.

    Handlers receive the parsed profile + an idempotency cache and yield
    ``DownloadCandidate`` objects. The base engine takes care of actually
    fetching the URL, verifying it, and writing the manifest entry.
    """

    company_code: str
    profile: dict[str, Any]
    download_dir: Path
    cache: "DownloadCache"


class DownloadCache:
    """Persistent record of (company, source_url) pairs already fetched.

    Used to enforce the idempotency gate: rerunning the engine on the same
    profile must not redownload PDFs that already live on disk and match
    the recorded checksum.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._known: dict[str, str] = {}
        if path.exists():
            with path.open("r", encoding="utf-8", newline="") as fp:
                for row in csv.DictReader(fp):
                    self._known[row["source_url"]] = row["sha256"]

    def is_known(self, source_url: str) -> bool:
        return source_url in self._known

    def record(self, source_url: str, sha256_hex: str) -> None:
        self._known[source_url] = sha256_hex

    def flush(self, rows: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists()
        with self.path.open("a", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=[
                    "run_id",
                    "company_code",
                    "company_dirname",
                    "period",
                    "title",
                    "fiscal_year",
                    "quarter",
                    "disclosure_date",
                    "source_url",
                    "local_path",
                    "sha256",
                    "status",
                    "verification_level",
                    "verification_reasons",
                    "error_message",
                ],
            )
            if write_header:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)


@contextmanager
def _timed(label: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("[%s] elapsed=%.2fs", label, time.perf_counter() - start)


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class DownloaderEngine:
    """Single entry point: ``DownloaderEngine(profile).run()``.

    The engine is intentionally site-handler agnostic. Adding a new
    insurer means dropping a YAML file under ``profiles/`` and (only if
    the site has a fundamentally new pattern) a small handler under this
    package.
    """

    def __init__(
        self,
        profile: dict[str, Any],
        site_handlers: dict[str, SiteHandler],
        max_retries: int = 2,
    ) -> None:
        self.profile = profile
        self.site_handlers = site_handlers
        self.run_id = _make_run_id()
        self.max_retries = max_retries

    def run(self) -> list[DownloadResult]:
        company_code = self.profile["company_code"]
        site_type = self.profile["site_type"]
        if site_type not in self.site_handlers:
            raise KeyError(
                f"No handler registered for site_type={site_type!r}. "
                f"Known: {sorted(self.site_handlers)}"
            )

        # Per-run cache lives at the disclosure root - it spans periods
        # because the same source URL can correspond to different
        # quarters, so keying by URL only would be ambiguous if scoped
        # to a single period directory.
        cache = DownloadCache(
            settings.disclosure_dir / "_meta" / f"{company_code}_download_cache.csv"
        )
        context = DownloadContext(
            company_code=company_code,
            profile=self.profile,
            download_dir=settings.disclosure_dir,  # period is decided per-candidate
            cache=cache,
        )

        results: list[DownloadResult] = []
        manifest_rows: list[dict[str, Any]] = []
        try:
            with _timed(f"discover:{company_code}"):
                candidates = list(self.site_handlers[site_type](context))

            for candidate in candidates:
                result = self._fetch_with_retry(candidate, cache)
                results.append(result)
                manifest_rows.append(self._manifest_row(result))
                gc.collect()
        finally:
            cache.flush(manifest_rows)

        return results

    def _fetch_with_retry(
        self, candidate: DownloadCandidate, cache: DownloadCache
    ) -> DownloadResult:
        """Run ``_fetch_one`` and retry verification failures.

        ``downloaded_basic`` and ``skipped`` are accepted on the first
        try - only ``failed`` triggers a retry. Each retry forgets the
        cache entry so the next ``_fetch_one`` re-pulls from source.
        """
        last_result: DownloadResult | None = None
        for attempt in range(self.max_retries + 1):
            result = self._fetch_one(candidate, cache)
            last_result = result
            if result.status != "failed":
                return result
            logger.warning(
                "fetch failed (attempt %d/%d) for %s: %s",
                attempt + 1,
                self.max_retries + 1,
                candidate.company_code,
                result.error_message,
            )
            cache._known.pop(candidate.source_url, None)
            if result.local_path and result.local_path.exists():
                try:
                    result.local_path.unlink()
                except OSError:
                    pass
        assert last_result is not None
        return last_result

    def _fetch_one(
        self,
        candidate: DownloadCandidate,
        cache: DownloadCache,
    ) -> DownloadResult:
        target = self._target_path(candidate)
        if cache.is_known(candidate.source_url) and target.exists():
            # Even on a cache hit we run the full verification chain so a
            # cached entry that became user-unreadable since last run
            # surfaces as ``failed`` (and gets retried).
            normalize_file_acl(target)
            verification = verify_pdf(target)
            if verification.ok:
                logger.info("skip(idempotent): %s", candidate.source_url)
                return DownloadResult(
                    candidate=candidate,
                    local_path=target,
                    sha256=_sha256_of(target),
                    status="skipped",
                    verification_level=verification.level.value,
                    verification_reasons="; ".join(verification.reasons),
                )
            logger.warning(
                "cache hit but verification failed (%s); will redownload",
                target.name,
            )

        try:
            if candidate.prefetched_path is not None:
                self._move_prefetched(candidate.prefetched_path, target)
            else:
                self._download_url(candidate.source_url, target)
        except Exception as exc:
            return DownloadResult(
                candidate=candidate,
                local_path=None,
                sha256=None,
                status="failed",
                error_message=str(exc),
            )

        normalize_file_acl(target)
        verification = verify_pdf(target)
        if not verification.ok:
            logger.warning(
                "verification FAILED for %s: %s",
                target.name,
                "; ".join(verification.reasons),
            )
            return DownloadResult(
                candidate=candidate,
                local_path=target,
                sha256=_sha256_of(target),
                status="failed",
                error_message="verification: " + "; ".join(verification.reasons),
                bytes_downloaded=target.stat().st_size,
                verification_level=verification.level.value,
                verification_reasons="; ".join(verification.reasons),
            )

        sha = _sha256_of(target)
        cache.record(candidate.source_url, sha)
        if verification.level is VerificationLevel.VERIFIED_FULL:
            status = "downloaded"
        else:
            status = "downloaded_basic"
        return DownloadResult(
            candidate=candidate,
            local_path=target,
            sha256=sha,
            status=status,
            bytes_downloaded=target.stat().st_size,
            verification_level=verification.level.value,
            verification_reasons="; ".join(verification.reasons),
        )

    @staticmethod
    def _target_path(candidate: DownloadCandidate) -> Path:
        suffix = "_amended" if candidate.is_supplement else ""
        target = settings.disclosure_pdf_path(
            period=candidate.period,
            company_dirname=f"{candidate.company_dirname}{suffix}",
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def _move_prefetched(src: Path, dest: Path) -> None:
        """Move a handler-prefetched file into the canonical location.

        Used when ``site_type`` cannot be expressed as a direct GET (e.g.
        the file lives inside a ZIP that a Selenium handler already fetched
        and unpacked). The engine still owns sha256 + manifest writing
        and (after the move) ACL normalisation via
        ``solvency.verification.acl.normalize_file_acl`` in ``_fetch_one``.
        """
        import shutil

        if not src.exists():
            raise FileNotFoundError(f"prefetched file missing: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))

    def _download_url(self, url: str, dest: Path) -> None:
        """Default URL fetcher.

        For sites that expose direct PDF URLs (case A), the simple
        ``requests`` path is enough. Sites that need JavaScript rendering
        or click-driven downloads should set ``site_type`` accordingly and
        provide a Selenium-aware handler that performs the actual file
        write itself, leaving this method unused.
        """
        import requests

        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as fp:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fp.write(chunk)

    def _manifest_row(self, result: DownloadResult) -> dict[str, Any]:
        cand = result.candidate
        return {
            "run_id": self.run_id,
            "company_code": cand.company_code,
            "company_dirname": cand.company_dirname,
            "period": cand.period,
            "title": cand.title,
            "fiscal_year": cand.fiscal_year,
            "quarter": cand.quarter,
            "disclosure_date": cand.disclosure_date,
            "source_url": cand.source_url,
            "local_path": str(result.local_path) if result.local_path else "",
            "sha256": result.sha256 or "",
            "status": result.status,
            "verification_level": result.verification_level,
            "verification_reasons": result.verification_reasons,
            "error_message": result.error_message or "",
        }
