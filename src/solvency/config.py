"""Central configuration for the solvency pipeline.

All paths are resolved relative to the repository root so the project is
portable. Environment variables can override individual paths when needed
(useful for CI, Docker, or alternative storage layouts).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if raw:
        return Path(raw).expanduser().resolve()
    return default


@dataclass(frozen=True)
class Settings:
    """Resolved filesystem layout used across the pipeline.

    Layout for ``disclosure_dir`` follows the *quarter-first* convention:

        data/disclosure/<period>/<kind>/<companyCode>_<companyName>.<ext>

    where ``<period>`` is something like ``FY2025_Q4``, ``<kind>`` is
    ``pdf`` or ``parsed``, and the file stem matches the legacy company
    folder name (so the company stays trivially identifiable).
    """

    repo_root: Path
    data_dir: Path
    disclosure_dir: Path
    md_inbox_dir: Path
    artifacts_dir: Path
    review_queue_dir: Path

    def disclosure_pdf_path(
        self, period: str, company_dirname: str, ext: str = ".pdf"
    ) -> Path:
        """Resolve the canonical PDF path for one (period, company).

        정본은 `raw/` 다 (owner 2026-09-02 "폴더 통일"). 이 함수는 원래 `pdf/` 를 돌려줬고
        13개 분기는 `raw/` 에 쌓여 있어서 2026.2Q 부터 디렉터리가 갈렸다 — `raw/` 만 glob 하는
        코드가 39사를 **예외도 로그도 없이** 스킵했고, 같은 버그가 최소 네 번 났다
        (`scripts/_disclosure_pdf_paths.py` 의 사고 목록 참조). 2026-09-02 에 `pdf/` 를
        `raw/` 로 합치면서 이 선언도 맞췄다. 읽기는 계속 그 헬퍼(`disclosure_pdfs()`)를 써라 —
        과거 워크트리에 남아 있을 `pdf/` 를 폴백으로 본다.
        """
        return self.disclosure_dir / period / "raw" / f"{company_dirname}{ext}"

    def disclosure_parsed_path(
        self, period: str, company_dirname: str, ext: str = ".xlsx"
    ) -> Path:
        """Resolve the canonical parsed-output path."""
        return self.disclosure_dir / period / "parsed" / f"{company_dirname}{ext}"

    def disclosure_period_dir(self, period: str) -> Path:
        return self.disclosure_dir / period

    @classmethod
    def load(cls) -> "Settings":
        root = _env_path("SOLVENCY_REPO_ROOT", _repo_root())
        data_dir = _env_path("SOLVENCY_DATA_DIR", root / "data")
        artifacts_dir = _env_path("SOLVENCY_ARTIFACTS_DIR", root / "artifacts")
        return cls(
            repo_root=root,
            data_dir=data_dir,
            disclosure_dir=_env_path(
                "SOLVENCY_DISCLOSURE_DIR", data_dir / "disclosure"
            ),
            md_inbox_dir=_env_path("SOLVENCY_MD_INBOX_DIR", root / "md_inbox"),
            artifacts_dir=artifacts_dir,
            review_queue_dir=_env_path(
                "SOLVENCY_REVIEW_QUEUE_DIR", artifacts_dir / "review_queue"
            ),
        )

    def ensure_dirs(self) -> None:
        """Create runtime directories that downstream stages rely on."""
        for directory in (
            self.md_inbox_dir,
            self.artifacts_dir,
            self.review_queue_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings.load()
