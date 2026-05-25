"""CLI entry point for the unified downloader.

Usage:

    python -m solvency.downloader.runner --company KR0001
    python -m solvency.downloader.runner --profile path/to/profile.yaml

The runner loads a YAML profile, dispatches by ``site_type``, and
delegates all heavy lifting to ``DownloaderEngine``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Iterable

from solvency.config import settings

from .base import DownloadCandidate, DownloadContext, DownloaderEngine, SiteHandler
from .handlers.life_insurance_association import handle_life_insurance_association
from .handlers.nonlife_insurance_association import handle_nonlife_insurance_association

logger = logging.getLogger(__name__)


def _profile_dir() -> Path:
    return Path(__file__).resolve().parent / "profiles"


def _load_profile(company: str | None, profile_path: str | None) -> dict[str, Any]:
    import yaml  # local import keeps the package importable without pyyaml

    if profile_path:
        path = Path(profile_path).expanduser().resolve()
    elif company:
        path = _profile_dir() / f"{company}.yaml"
    else:
        raise SystemExit("either --company or --profile is required")

    if not path.exists():
        raise SystemExit(f"profile not found: {path}")

    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _placeholder_handler(label: str) -> SiteHandler:
    """Return a handler that just logs that nothing is wired up yet."""

    def _run(_ctx: DownloadContext) -> Iterable[DownloadCandidate]:
        logger.warning(
            "site_type=%s handler is a skeleton. Wire up Selenium / requests "
            "actions before using it in production.",
            label,
        )
        return ()

    return _run


SITE_HANDLERS: dict[str, SiteHandler] = {
    "life_insurance_association": handle_life_insurance_association,
    "nonlife_insurance_association": handle_nonlife_insurance_association,
    "case_a_direct_pdf": _placeholder_handler("case_a_direct_pdf"),
    "case_b_button_click": _placeholder_handler("case_b_button_click"),
    "case_c_zip_attachment": _placeholder_handler("case_c_zip_attachment"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", help="Company code, e.g. KR0001")
    parser.add_argument("--profile", help="Path to a profile YAML")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(name)s: %(message)s")

    settings.ensure_dirs()
    profile = _load_profile(args.company, args.profile)
    engine = DownloaderEngine(profile=profile, site_handlers=SITE_HANDLERS)
    results = engine.run()

    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    logger.info("done company=%s counts=%s", profile.get("company_code"), counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
