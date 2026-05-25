"""Paths and credentials for FSC bond APIs."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_dotenv_var(dotenv_path: Path, key: str) -> str | None:
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
class BondSettings:
    repo_root: Path
    data_dir: Path
    raw_dir: Path

    @classmethod
    def load(cls) -> "BondSettings":
        root = _repo_root()
        data_dir = root / "data" / "bonds"
        return cls(repo_root=root, data_dir=data_dir, raw_dir=data_dir / "raw")

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.raw_dir):
            d.mkdir(parents=True, exist_ok=True)

    def resolve_key(self, env_name: str) -> str:
        key = os.environ.get(env_name)
        if key:
            return key.strip()
        key = _read_dotenv_var(self.repo_root / ".env", env_name)
        if key:
            return key
        raise RuntimeError(
            f"{env_name} not set. Add it to .env at repo root. See .env.example."
        )


settings = BondSettings.load()
