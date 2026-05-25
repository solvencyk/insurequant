"""Non-life Insurance Association (손해보험협회) bulk downloader.

The association site (https://kpub.knia.or.kr/managementDisc/regularly/regularlyDisclosure.do)
exposes a table where each row is one non-life insurer. The first column (TH) is the
company name, and the first TD contains the 2025 Q4 disclosure link.

Handler:
1. Opens the disclosure page with Selenium
2. Extracts company names + download links from table rows
3. Downloads PDFs with proper headers (referer, user-agent)
4. Maps company names to codes via nonlife_insurer_registry.yaml
5. Yields candidates with prefetched_path for the engine to move
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

_REGISTRY_FILE = Path(__file__).resolve().parents[1] / "nonlife_insurer_registry.yaml"


def handle_nonlife_insurance_association(
    ctx: DownloadContext,
) -> Iterable[DownloadCandidate]:
    """Download non-life insurance disclosures from KNIA.

    1. Scrape company names and download link URLs
    2. Download PDFs with proper headers
    3. Map names to codes via registry
    4. Yield candidates with prefetched_path
    """
    profile = ctx.profile
    fiscal_year = profile["fiscal_year"]
    quarter = profile["quarter"]
    period = profile.get("period") or _period_from(fiscal_year, quarter)

    base_url = profile["disclosure_url"]

    insurers = _load_registry(_REGISTRY_FILE)

    # Scrape company names and download URLs
    company_links = _scrape_company_links(base_url)
    if not company_links:
        logger.error("failed to scrape companies from %s", base_url)
        return []

    # Work in temp directory and download PDFs
    workdir = Path(tempfile.mkdtemp(prefix="kics_nonlife_"))
    download_dir = workdir / "downloads"
    download_dir.mkdir()

    # Download PDFs with proper headers
    company_pdf_pairs = _download_pdfs_with_headers(company_links, download_dir, base_url)

    # Extract ZIPs and collect actual PDF files
    company_pdf_pairs = _extract_zips_and_collect_pdfs(company_pdf_pairs, download_dir)

    unmatched_dir = settings.disclosure_dir / "_unmatched" / period
    unmatched_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[DownloadCandidate] = []
    for company_name, pdf_path in company_pdf_pairs:
        insurer = _match_insurer(company_name, insurers)
        if insurer is None:
            # Copy unmatched to _unmatched directory
            target = unmatched_dir / pdf_path.name
            shutil.copy2(pdf_path, target)
            logger.warning("unmatched_company: %s -> %s", company_name, target)
            continue

        candidates.append(
            DownloadCandidate(
                company_code=insurer["code"],
                company_dirname=insurer["dirname"],
                period=period,
                title=company_name,
                fiscal_year=fiscal_year,
                quarter=quarter,
                disclosure_date=profile.get("disclosure_date"),
                source_url=f"{base_url}#{insurer['code']}_Q4",
                prefetched_path=pdf_path,
            )
        )

    gc.collect()
    return candidates


def _scrape_company_links(url: str) -> list[tuple[str, str]]:
    """Scrape company names and 2025 Q4 download link URLs from KNIA page.

    Returns list of (company_name, relative_url) tuples.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(15)
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//table/tbody/tr"))
        )

        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
        logger.info("found %d company rows", len(rows))

        result = []
        for row in rows:
            try:
                # <th scope="row">회사명</th>
                th = row.find_element(By.XPATH, "./th[@scope='row']")
                company_name = th.text.strip()

                # <td[1]> = 2025 (first data column)
                td1 = row.find_element(By.XPATH, "./td[1]")
                link = td1.find_element(By.TAG_NAME, "a")
                href = link.get_attribute("href")

                if company_name and href:
                    result.append((company_name, href))
                    logger.debug("found: %s -> %s", company_name, href)
            except Exception as e:
                logger.debug("error extracting row: %s", e)

        return result

    except Exception as e:
        logger.error("error scraping: %s", e)
        return []

    finally:
        driver.quit()


def _download_pdfs_with_headers(
    company_links: list[tuple[str, str]], download_dir: Path, referer_url: str
) -> list[tuple[str, Path]]:
    """Download PDFs using requests with proper headers.

    Args:
        company_links: List of (company_name, relative_url) tuples
        download_dir: Where to save PDFs
        referer_url: Base URL to use as Referer header

    Returns list of (company_name, pdf_path) tuples.
    """
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": referer_url,
    }

    result = []
    for company_name, relative_url in company_links:
        try:
            # Build absolute URL
            if relative_url.startswith("http"):
                url = relative_url
            else:
                url = f"https://kpub.knia.or.kr{relative_url}"

            logger.debug("downloading %s from %s", company_name, url)

            resp = requests.get(url, headers=headers, timeout=30, stream=True)
            resp.raise_for_status()

            # Extract filename from Content-Disposition or URL
            filename = None
            if "Content-Disposition" in resp.headers:
                import re as regex

                m = regex.search(
                    r'filename=["\']?([^"\']+)["\']?', resp.headers["Content-Disposition"]
                )
                if m:
                    filename = m.group(1)

            if not filename:
                # Use generic filename based on company name
                filename = f"{company_name}_2025Q4.pdf"

            filepath = download_dir / filename

            # Save file
            with filepath.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info("downloaded %s -> %s", company_name, filename)
            result.append((company_name, filepath))

        except Exception as e:
            logger.warning("failed to download %s: %s", company_name, e)
            continue

    return result


_TARGET_KEYWORD = "경영공시"
_EXCLUDE_KEYWORDS = [
    "감사보고서",
    "감사",
    "별도재무제표",
    "재무제표",
    "외부검증",
    "검증보고서",
    "공문",
    "제출의 건",
]


def _select_target_pdf(pdf_files: list[Path]) -> Path | None:
    """Select the 경영공시 PDF.

    Strategy: pick the PDF whose filename contains '경영공시' but does NOT
    contain any audit/verification-report keywords. If multiple, pick largest.
    Falls back to non-audit largest if no '경영공시' match (defensive).
    """
    if not pdf_files:
        return None

    def is_excluded(name: str) -> bool:
        return any(kw in name for kw in _EXCLUDE_KEYWORDS)

    # Primary: 경영공시 in filename AND not excluded
    primary = [
        p for p in pdf_files
        if _TARGET_KEYWORD in p.name and not is_excluded(p.name)
    ]
    if primary:
        return max(primary, key=lambda p: p.stat().st_size)

    # Fallback: any non-excluded PDF (largest)
    non_excluded = [p for p in pdf_files if not is_excluded(p.name)]
    if non_excluded:
        return max(non_excluded, key=lambda p: p.stat().st_size)

    return None


def _verify_pdf(pdf_path: Path) -> bool:
    """Verify file is a valid PDF by checking magic bytes (%PDF-)."""
    if not pdf_path.exists() or pdf_path.stat().st_size < 100:
        return False
    try:
        with pdf_path.open("rb") as f:
            magic = f.read(5)
        return magic == b"%PDF-"
    except Exception:
        return False


def _extract_zips_and_collect_pdfs(
    company_file_pairs: list[tuple[str, Path]], work_dir: Path
) -> list[tuple[str, Path]]:
    """Extract ZIP files and select the 경영공시 PDF (excluding 감사보고서).

    For each (company_name, file_path) pair:
    - If file is a ZIP: extract, then select the 경영공시 PDF
    - If file is already a PDF: verify and keep as is
    Skips files that fail PDF magic-byte verification.
    """
    result = []

    for company_name, file_path in company_file_pairs:
        # Check if it's a ZIP file (regardless of extension)
        is_zip = file_path.exists() and zipfile.is_zipfile(file_path)

        if is_zip:
            try:
                extract_dir = work_dir / f"{company_name}_extracted"
                extract_dir.mkdir(parents=True, exist_ok=True)

                # Extract with cp437 → cp949 fallback for Korean filenames
                with zipfile.ZipFile(file_path, "r") as zf:
                    for info in zf.infolist():
                        if not info.flag_bits & 0x800:
                            try:
                                info.filename = info.filename.encode(
                                    "cp437"
                                ).decode("cp949")
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                pass
                        zf.extract(info, extract_dir)

                logger.debug("extracted %s to %s", file_path.name, extract_dir)

                pdf_files = list(extract_dir.rglob("*.pdf"))
                logger.info(
                    "%s: %d PDFs in zip: %s",
                    company_name,
                    len(pdf_files),
                    [p.name for p in pdf_files],
                )

                target_pdf = _select_target_pdf(pdf_files)
                if target_pdf is None:
                    logger.warning("no target PDF in %s zip", company_name)
                    continue

                if not _verify_pdf(target_pdf):
                    logger.warning(
                        "PDF verification failed for %s: %s",
                        company_name,
                        target_pdf.name,
                    )
                    continue

                result.append((company_name, target_pdf))
                logger.info("selected for %s: %s", company_name, target_pdf.name)

            except Exception as e:
                logger.warning("failed to extract %s: %s", file_path.name, e)

        elif _verify_pdf(file_path):
            # Already a verified PDF
            result.append((company_name, file_path))
            logger.info("direct PDF for %s: %s", company_name, file_path.name)

        else:
            logger.warning(
                "invalid file for %s: %s (not zip, not valid PDF)",
                company_name,
                file_path.name,
            )

    return result


def _load_registry(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    insurers = data.get("insurers", [])
    for entry in insurers:
        # match longest aliases first to avoid prefix collisions
        entry["aliases"] = sorted(entry["aliases"], key=len, reverse=True)
    return insurers


def _match_insurer(company_name: str, insurers: list[dict]) -> dict | None:
    haystack = _normalise(company_name)
    for entry in insurers:
        for alias in entry["aliases"]:
            if _normalise(alias) in haystack:
                return entry
    return None


def _normalise(s: str) -> str:
    # strip whitespace + punctuation; handle "손해보험", "손보", abbreviations, etc.
    return re.sub(r"[\s\-_().,/㈜·]+", "", s).lower()


def _period_from(fiscal_year: str, quarter: str) -> str:
    year_digits = re.sub(r"\D", "", fiscal_year)
    if len(year_digits) == 2:
        year_digits = f"20{year_digits}"
    return f"FY{year_digits}_{quarter}"
