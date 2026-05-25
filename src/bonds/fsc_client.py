"""FSC data.go.kr bond API client (issuance, early exercise, rights schedule)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "http://apis.data.go.kr/1160100"

ENDPOINTS = {
    "issuance": {
        "path": "GetBondTradInfoService_V2/getIssuIssuItemStat_V2",
        "key_env": "DATA_GO_KR_BOND_ISSUANCE_KEY",
        "data_id": "15043421",
    },
    "early_exercise": {
        "path": "GetBondRedeInfoService_V2/getEarlExerOpti_V2",
        "key_env": "DATA_GO_KR_BOND_REDE_KEY",
        "data_id": "15059595",
    },
    "schedule": {
        "path": "GetBondRighScheInfoService_V2/getBondRighExerSche_V2",
        "key_env": "DATA_GO_KR_BOND_REDE_KEY",
        "data_id": "15059611",
    },
}


class FscBondError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApiPage:
    endpoint: str
    page_no: int
    num_of_rows: int
    result_code: str | None
    result_msg: str | None
    total_count: int | None
    items: list[dict[str, Any]]
    http_status: int | None = None
    error: str | None = None


def _walk_header(payload: object) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        if "resultCode" in payload:
            return payload
        for value in payload.values():
            found = _walk_header(value)
            if found:
                return found
    return None


def _find_items(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "item":
                if isinstance(value, list):
                    return [dict(x) for x in value if isinstance(x, dict)]
                if isinstance(value, dict):
                    return [dict(value)]
            found = _find_items(value)
            if found:
                return found
    return []


class FscBondClient:
    def __init__(
        self,
        issuance_key: str,
        rede_key: str,
        *,
        timeout: float = 90.0,
        pause_sec: float = 0.2,
    ) -> None:
        self._keys = {
            "DATA_GO_KR_BOND_ISSUANCE_KEY": issuance_key,
            "DATA_GO_KR_BOND_REDE_KEY": rede_key,
        }
        self.timeout = timeout
        self.pause_sec = pause_sec

    @classmethod
    def from_settings(cls) -> "FscBondClient":
        from src.bonds.config import settings

        return cls(
            issuance_key=settings.resolve_key("DATA_GO_KR_BOND_ISSUANCE_KEY"),
            rede_key=settings.resolve_key("DATA_GO_KR_BOND_REDE_KEY"),
        )

    def fetch_page(
        self,
        endpoint: str,
        *,
        page_no: int = 1,
        num_of_rows: int = 100,
        extra_params: dict[str, str] | None = None,
    ) -> ApiPage:
        if endpoint not in ENDPOINTS:
            raise ValueError(f"unknown endpoint: {endpoint}")
        meta = ENDPOINTS[endpoint]
        service_key = self._keys[meta["key_env"]]
        params: dict[str, str] = {
            "serviceKey": service_key,
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows),
            "resultType": "json",
        }
        if extra_params:
            params.update(extra_params)
        url = f"{BASE_URL}/{meta['path']}?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                status = resp.status
        except TimeoutError as exc:
            return ApiPage(
                endpoint=endpoint,
                page_no=page_no,
                num_of_rows=num_of_rows,
                result_code=None,
                result_msg=str(exc),
                total_count=None,
                items=[],
                error=f"timeout after {self.timeout}s",
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            return ApiPage(
                endpoint=endpoint,
                page_no=page_no,
                num_of_rows=num_of_rows,
                result_code=None,
                result_msg=detail or exc.reason,
                total_count=None,
                items=[],
                http_status=exc.code,
                error=f"HTTP {exc.code}: {exc.reason}",
            )
        except urllib.error.URLError as exc:
            return ApiPage(
                endpoint=endpoint,
                page_no=page_no,
                num_of_rows=num_of_rows,
                result_code=None,
                result_msg=str(exc.reason),
                total_count=None,
                items=[],
                error=str(exc.reason),
            )

        payload = json.loads(body)
        header = _walk_header(payload) or {}
        items = _find_items(payload)
        total_raw = header.get("totalCount")
        total_count = int(total_raw) if total_raw not in (None, "") else None
        if self.pause_sec:
            time.sleep(self.pause_sec)
        return ApiPage(
            endpoint=endpoint,
            page_no=page_no,
            num_of_rows=num_of_rows,
            result_code=str(header.get("resultCode")) if header.get("resultCode") is not None else None,
            result_msg=str(header.get("resultMsg")) if header.get("resultMsg") is not None else None,
            total_count=total_count,
            items=items,
            http_status=status,
        )

    def smoke_test(self) -> dict[str, ApiPage]:
        return {name: self.fetch_page(name, page_no=1, num_of_rows=1) for name in ENDPOINTS}

    def fetch_all_pages(
        self,
        endpoint: str,
        *,
        num_of_rows: int = 100,
        max_pages: int = 50,
        extra_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for page_no in range(1, max_pages + 1):
            page = self.fetch_page(
                endpoint,
                page_no=page_no,
                num_of_rows=num_of_rows,
                extra_params=extra_params,
            )
            if page.error:
                if page_no == 1:
                    raise FscBondError(f"{endpoint} page {page_no}: {page.error}")
                break
            if page.result_code and page.result_code != "00":
                raise FscBondError(
                    f"{endpoint} page {page_no}: resultCode={page.result_code} msg={page.result_msg!r}"
                )
            if not page.items:
                break
            rows.extend(page.items)
            if len(page.items) < num_of_rows:
                break
        return rows
