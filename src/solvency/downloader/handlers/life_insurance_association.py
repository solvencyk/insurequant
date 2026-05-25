"""Life Insurance Association bulk-ZIP handler.

The association site exposes a single ZIP per (year, quarter) that bundles
every life insurer's quarterly disclosure PDF. The handler:

1. opens ``search_stdYear=<YYYY>`` filtered list page,
2. clicks the per-quarter download cell (td[2]=Q1 ... td[5]=Q4),
3. unpacks the ZIP into a tempdir,
4. resolves each PDF filename to a company via ``life_insurer_registry.yaml``,
5. yields one ``DownloadCandidate`` per resolved PDF with ``prefetched_path``
   set so the engine handles sha256 + manifest in the canonical layout.
"""

from __future__ import annotations

import gc
import logging
import re
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Iterable

import yaml

from solvency.config import settings

from ..base import DownloadCandidate, DownloadContext

logger = logging.getLogger(__name__)


_QUARTER_TO_TD: dict[str, int] = {"Q1": 2, "Q2": 3, "Q3": 4, "Q4": 5}
_REGISTRY_FILE = Path(__file__).resolve().parents[1] / "life_insurer_registry.yaml"


def handle_life_insurance_association(ctx: DownloadContext) -> Iterable[DownloadCandidate]:
    profile = ctx.profile
    fiscal_year = profile["fiscal_year"]
    quarter = profile["quarter"]
    period = profile.get("period") or _period_from(fiscal_year, quarter)

    base_url = profile["disclosure_url"]
    search_year = profile.get("search_year") or _year_from_fy(fiscal_year)
    target_url = _with_year(base_url, search_year)

    button_xpath = profile["selectors"]["download_button_template"].format(
        td=_QUARTER_TO_TD[quarter]
    )

    insurers = _load_registry(_REGISTRY_FILE)

    workdir = Path(tempfile.mkdtemp(prefix="kics_life_"))
    zip_path = _download_zip(target_url, button_xpath, workdir)
    if zip_path is None:
        shutil.rmtree(workdir, ignore_errors=True)
        return []

    extract_dir = workdir / "extracted"
    extract_dir.mkdir()
    _extract_zip_korean_safe(zip_path, extract_dir)

    unmatched_dir = settings.disclosure_dir / "_unmatched" / period
    unmatched_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[DownloadCandidate] = []
    for pdf in sorted(extract_dir.rglob("*.pdf")):
        insurer = _match_insurer(pdf.name, insurers)
        if insurer is None:
            target = unmatched_dir / pdf.name
            shutil.copy2(pdf, target)
            logger.warning("unmatched_pdf -> %s", target)
            continue
        candidates.append(
            DownloadCandidate(
                company_code=insurer["code"],
                company_dirname=insurer["dirname"],
                period=period,
                title=pdf.stem,
                fiscal_year=fiscal_year,
                quarter=quarter,
                disclosure_date=profile.get("disclosure_date"),
                source_url=f"{target_url}#{insurer['code']}_{quarter}",
                prefetched_path=pdf,
            )
        )
    # Workdir cleanup is the engine's job (it moves prefetched files out);
    # cleaning here would yank the files before _move_prefetched runs.
    gc.collect()
    return candidates


def _extract_zip_korean_safe(zip_path: Path, extract_dir: Path) -> None:
    """Extract ZIP, re-decoding cp437 filenames as cp949.

    Korean ZIP archives often omit the UTF-8 filename flag; Python's
    zipfile then falls back to cp437, mangling Hangul. We detect that
    flag and re-encode to cp949 before extraction.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if not info.flag_bits & 0x800:
                try:
                    info.filename = info.filename.encode("cp437").decode("cp949")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
            zf.extract(info, extract_dir)


def _load_registry(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    insurers = data.get("insurers", [])
    for entry in insurers:
        # match longest aliases first to avoid "신한"-style prefix collisions.
        entry["aliases"] = sorted(entry["aliases"], key=len, reverse=True)
    return insurers


def _match_insurer(filename: str, insurers: list[dict]) -> dict | None:
    haystack = _normalise(filename)
    for entry in insurers:
        for alias in entry["aliases"]:
            if _normalise(alias) in haystack:
                return entry
    return None


def _normalise(s: str) -> str:
    # strip whitespace + punctuation; the association mixes "ABL", "에이비엘",
    # "(주)" and various separators across years.
    return re.sub(r"[\s\-_().,/㈜·]+", "", s).lower()


def _period_from(fiscal_year: str, quarter: str) -> str:
    year_digits = re.sub(r"\D", "", fiscal_year)
    if len(year_digits) == 2:
        year_digits = f"20{year_digits}"
    return f"FY{year_digits}_{quarter}"


def _year_from_fy(fiscal_year: str) -> str:
    digits = re.sub(r"\D", "", fiscal_year)
    if len(digits) == 2:
        digits = f"20{digits}"
    return digits


def _with_year(url: str, year: str) -> str:
    if "search_stdYear=" in url:
        return re.sub(r"search_stdYear=\d+", f"search_stdYear={year}", url)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}search_stdYear={year}"


def _download_zip(url: str, button_xpath: str, workdir: Path) -> Path | None:
    """Drive a headless Chrome to the disclosure page and click the button.

    Selenium imports are local so the rest of the package stays importable
    without a Selenium install (the harness doesn't need it).
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    download_dir = workdir / "downloads"
    download_dir.mkdir()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, button_xpath))
        )
        button.click()
        return _wait_for_zip(download_dir, timeout=120)
    finally:
        driver.quit()
        del driver


def _wait_for_zip(download_dir: Path, timeout: int) -> Path | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Chrome writes ".crdownload" while in flight and renames on completion.
        zips = [p for p in download_dir.iterdir() if p.suffix.lower() == ".zip"]
        in_flight = list(download_dir.glob("*.crdownload"))
        if zips and not in_flight:
            return zips[0]
        time.sleep(1)
    logger.error("zip download timed out after %ds", timeout)
    return None
