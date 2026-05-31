"""Paths and credentials for the IFRS17 DART pipeline.

User rules (from docs/claude-agent-ifrs17.md §0):
  - OpenDART API key MUST come from .env (var: OPENDART_API_KEY).
  - Do NOT hardcode the key in source.
  - Do NOT log the key value.

Key resolution order:
  1. env var OPENDART_API_KEY
  2. ``.env`` file at repo root (parsed minimally, no python-dotenv required)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_dotenv_var(dotenv_path: Path, key: str) -> str | None:
    """Tiny .env parser. Supports ``KEY=value`` lines (no quoting tricks)."""
    if not dotenv_path.is_file():
        return None
    with open(dotenv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return None


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    data_dir: Path           # data/dart/
    raw_dir: Path            # data/dart/raw/        (XBRL, attachments)
    reports_dir: Path        # data/dart/reports/    (rcept_no -> attachment PDFs)
    extracted_dir: Path      # data/dart/extracted/  (normalised JSON)

    def resolve_api_key(self) -> str:
        """Return the OpenDART API key. Raise if not found.

        Order: env var, then .env file at repo root.
        """
        key = os.environ.get("OPENDART_API_KEY")
        if key:
            return key.strip()
        key = _read_dotenv_var(self.repo_root / ".env", "OPENDART_API_KEY")
        if key:
            return key
        raise RuntimeError(
            "OPENDART_API_KEY not set. Add it to .env at repo root or export "
            "the env var. See docs/claude-agent-ifrs17.md."
        )

    @classmethod
    def load(cls) -> "Settings":
        root = _repo_root()
        data_dir = root / "data" / "dart"
        return cls(
            repo_root=root,
            data_dir=data_dir,
            raw_dir=data_dir / "raw",
            reports_dir=data_dir / "reports",
            extracted_dir=data_dir / "extracted",
        )

    def ensure_dirs(self) -> None:
        for d in (self.raw_dir, self.reports_dir, self.extracted_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings.load()
