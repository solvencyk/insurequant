"""Minimal OpenDART API client (PoC).

Surface intentionally small: this layer just wraps the few endpoints we
need for the IFRS17 pipeline. Everything else (table parsing, mapping) is
in higher-level modules so this stays mock-friendly for tests.

Endpoints used:
    /api/list.json         - filing list (search by corp_code + date range)
    /api/document.xml      - filing main document (HTML/XBRL inline)
    /api/corpCode.xml      - master corp_code dump (zipped XML)

Reference: https://opendart.fss.or.kr/guide/main.do
"""

from __future__ import annotations

import io
import json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from .config import settings


# Filing report codes (reprt_code on /api/list.json):
#   11013: 1Q, 11012: Half (반기), 11014: 3Q, 11011: Annual (사업)
REPRT_CODES = {
    "Q1": "11013",
    "H1": "11012",
    "Q3": "11014",
    "ANNUAL": "11011",
}


class OpenDARTError(RuntimeError):
    """Raised on non-success status codes or DART business errors."""


@dataclass
class OpenDARTClient:
    api_key: str
    base_url: str = "https://opendart.fss.or.kr"
    request_interval_s: float = 0.4  # gentle rate limit
    timeout_s: float = 15.0

    @classmethod
    def from_settings(cls) -> "OpenDARTClient":
        # Do NOT log the key or even its source — user rule.
        return cls(api_key=settings.resolve_api_key())

    # ------------------------------------------------------------------
    # Low-level
    # ------------------------------------------------------------------
    def _get(self, path: str, params: dict[str, Any]) -> requests.Response:
        params = {"crtfc_key": self.api_key, **params}
        url = f"{self.base_url}{path}?{urlencode(params)}"
        time.sleep(self.request_interval_s)
        # Two-shot: a single read timeout on a big document.xml is not a
        # signal to give up. Bigger filings (>5MB) routinely take 20-30s.
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                r = requests.get(url, timeout=(10, 60))
                if r.status_code != 200:
                    raise OpenDARTError(f"HTTP {r.status_code} for {path}")
                return r
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                time.sleep(1.5 * (attempt + 1))
        raise OpenDARTError(f"network timeout for {path}: {last_exc}")

    # ------------------------------------------------------------------
    # High-level: smoke-test key validity
    # ------------------------------------------------------------------
    def ping(self) -> dict[str, Any]:
        """Cheapest call that exercises auth: list filings for one known corp.

        Uses Samsung Fire (00139214) for the most recent year. Returns the
        raw DART status/message so callers can decide whether to proceed.
        Status meanings (selected):
            000: OK
            010: insufficient privilege (revoked/wrong tier)
            011: revoked key
            020: rate limit
            900: no result
        """
        r = self._get(
            "/api/list.json",
            {"corp_code": "00139214", "bgn_de": "20240101", "end_de": "20241231",
             "page_count": "1"},
        )
        try:
            data = r.json()
        except json.JSONDecodeError as exc:
            raise OpenDARTError(f"non-JSON ping response: {exc}: {r.text[:200]}")
        return {"status": data.get("status"), "message": data.get("message"),
                "sample_count": len(data.get("list", []))}

    # ------------------------------------------------------------------
    # Company-name search (per user rule: no permanent KR<->corp_code map)
    # ------------------------------------------------------------------
    def find_corp_codes_by_name(
        self, query: str, master_xml: Path | None = None
    ) -> list[dict[str, str]]:
        """Return matching corp_code records from the master XML.

        If ``master_xml`` is None, downloads it to ``settings.raw_dir/CORPCODE.xml``
        on first call (one-time cost per session, ~25MB cached).

        Match is substring on ``corp_name``. Returns dicts with keys:
            corp_code, corp_name, stock_code, modify_date
        """
        from lxml import etree as _etree  # local import to keep import light
        if master_xml is None:
            master_xml = settings.raw_dir / "CORPCODE.xml"
            if not master_xml.is_file():
                self.download_corp_code_xml(master_xml)
        tree = _etree.parse(str(master_xml))
        out = []
        for el in tree.iter("list"):
            name = (el.findtext("corp_name") or "").strip()
            if query in name:
                out.append({
                    "corp_code": (el.findtext("corp_code") or "").strip(),
                    "corp_name": name,
                    "stock_code": (el.findtext("stock_code") or "").strip(),
                    "modify_date": (el.findtext("modify_date") or "").strip(),
                })
        return out

    # ------------------------------------------------------------------
    # corp_code master list (zip download)
    # ------------------------------------------------------------------
    def download_corp_code_xml(self, dest: Path) -> Path:
        """Fetch the zipped master XML; writes the unzipped XML to ``dest``.

        DART returns a binary zip with one file named ``CORPCODE.xml`` inside.
        """
        r = self._get("/api/corpCode.xml", {})
        if not r.content.startswith(b"PK"):
            # Not a zip - DART returned an error JSON wrapped as bytes.
            try:
                err = r.json()
                raise OpenDARTError(
                    f"corpCode.xml returned error: status={err.get('status')} "
                    f"message={err.get('message')}"
                )
            except json.JSONDecodeError:
                raise OpenDARTError(
                    f"corpCode.xml returned non-zip payload: {r.content[:200]!r}"
                )
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            name = zf.namelist()[0]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
        return dest

    # ------------------------------------------------------------------
    # Filing list
    # ------------------------------------------------------------------
    def list_filings(
        self,
        corp_code: str,
        bgn_de: str,
        end_de: str,
        pblntf_ty: str | None = "A",  # A = 정기공시 (사업/반기/분기)
        pblntf_detail_ty: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return filings for one corp in a date range (YYYYMMDD).

        ``pblntf_ty=A`` filters to all periodic disclosures (사업/반기/분기).
        Use ``pblntf_detail_ty`` (e.g. ``A001`` 사업보고서) for finer filtering;
        leave both ``None`` to fetch everything.
        """
        params = {
            "corp_code": corp_code,
            "bgn_de": bgn_de,
            "end_de": end_de,
            "page_count": "100",
        }
        if pblntf_ty:
            params["pblntf_ty"] = pblntf_ty
        if pblntf_detail_ty:
            params["pblntf_detail_ty"] = pblntf_detail_ty
        r = self._get("/api/list.json", params)
        data = r.json()
        if data.get("status") not in ("000", "013"):
            raise OpenDARTError(
                f"list.json status={data.get('status')} message={data.get('message')}"
            )
        return data.get("list", [])

    # ------------------------------------------------------------------
    # Main document (HTML/XBRL inline) for a filing
    # ------------------------------------------------------------------
    def fetch_document_xml(self, rcept_no: str, dest: Path) -> Path:
        """Download the filing's main document (zipped XML)."""
        r = self._get("/api/document.xml", {"rcept_no": rcept_no})
        if not r.content.startswith(b"PK"):
            try:
                err = r.json()
                raise OpenDARTError(
                    f"document.xml returned error: status={err.get('status')} "
                    f"message={err.get('message')}"
                )
            except json.JSONDecodeError:
                raise OpenDARTError(
                    f"document.xml returned non-zip payload: {r.content[:200]!r}"
                )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return dest
