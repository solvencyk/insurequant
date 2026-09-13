# -*- coding: utf-8 -*-
"""J-ESR 공용 HTTP 헬퍼 — 브라우저 기본 헤더 + 정적/JS(SPA) 판별.

왜 있나 (2026-09-13 리허설)
---------------------------
기게시 15사의 1차 출처 URL 을 전수 확인했더니 5건이 실패했는데 원인이 둘로 갈렸다.

- **403 2건**(MS&AD·ソニーFG): URL 은 멀쩡하고 기본 fetcher 가 봇으로 차단된 것.
  브라우저 헤더(UA·Accept-Language·Referer)를 붙이면 200 이 돌아온다.
- **404 3건**(東京海上HD·T&D·日本生命): 진짜 이동.

헤더 없이 훑으면 10/31 재census 가 멀쩡한 출처를 `not_found` 로 잘못 적재한다.
그래서 jp 레인의 수집·점검 스크립트는 전부 이 모듈의 :func:`get` / :func:`probe` 를 쓴다.
직접 ``requests.get`` 을 부르지 말 것 — 헤더 기본값이 한 군데 있어야 다음 라운드에
또 같은 오탐을 만들지 않는다.

두 번째 함정. 東京海上HD IR 페이지는 200 이지만 HTML 364바이트 · ``<a>`` 0개 ·
``<script>`` 1개인 **SPA 셸**이라 정적 fetch 로는 자료 링크를 못 딴다. :func:`probe` 가
이걸 ``spa_shell`` 로 따로 분류해 "죽은 URL" 과 섞이지 않게 한다 — 재census 전
정적/JS 판별 단계가 이 분류다.

세 번째. ``release.tdnet.info``(TDnet 적시개시)는 게시 후 일정 기간이 지나면 문서를
내린다. 지금 200 이어도 영구 인용 출처로 쓰면 반드시 썩으므로 :func:`probe` 가
``expiring_host`` 플래그를 세운다(도메인 문서 §4c 규칙).

SSL: 기본 검증 ON. 회사망 SSL 인스펙션 때문에 꺼야 하는 PC 에서만 ``JESR_INSECURE_SSL=1``.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from urllib.parse import urljoin, urlsplit

import requests

__all__ = [
    "UA_BROWSER",
    "browser_headers",
    "verify_setting",
    "get",
    "probe",
    "looks_like_spa",
    "EXPIRING_HOSTS",
]

UA_BROWSER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
ACCEPT_DEFAULT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "application/pdf;q=0.9,image/avif,image/webp,*/*;q=0.8"
)
ACCEPT_LANGUAGE = "ja,en-US;q=0.9,en;q=0.8,ko;q=0.7"

#: 영구 인용 출처로 쓰면 안 되는 호스트(게시 후 일정 기간이 지나면 문서를 내린다).
#: 1차 출처는 회사 자체 IR/디스클로저의 영구 경로를 쓴다.
EXPIRING_HOSTS = ("release.tdnet.info", "www.release.tdnet.info", "kabutan.jp")

#: 연속 요청에 간헐적으로 403(Akamai Access Denied)을 내는 호스트 — 죽은 게 아니라
#: 속도제한이다(2026-09-13 실측: 같은 URL 이 5회 중 4회 200, 1회 403).
#: 수집기는 이 호스트에 요청 간격을 5초 이상 둔다.
RATE_LIMITED_HOSTS = ("www.tokiomarine-nichido.co.jp",)

_ANCHOR_RE = re.compile(rb"<a\b[^>]*href=", re.I)
_SCRIPT_RE = re.compile(rb"<script\b", re.I)
#: <meta http-equiv="refresh" content="0;URL=/ir/event/presentation/2026/">
#: 東京海上HD IR 이 이걸 쓴다. 이 한 줄을 안 보면 "364바이트 SPA 셸" 로 오진한다
#: (2026-09-13 리허설의 실제 오진). requests 도 curl -L 도 meta refresh 는 안 따라간다.
_META_REFRESH_RE = re.compile(
    rb"""<meta[^>]+http-equiv=["']?refresh["']?[^>]+content=["']?\s*\d+\s*;\s*url=([^"'>\s]+)""",
    re.I,
)


def verify_setting():
    """requests 의 ``verify`` 인자. 기본 True, 사설 CA 번들이 있으면 그 경로."""
    flag = os.environ.get("JESR_INSECURE_SSL", "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return False
    bundle = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if bundle and os.path.exists(bundle):
        return bundle
    return True


def browser_headers(url: str, referer: str | None = None, accept: str = ACCEPT_DEFAULT) -> dict:
    """실제 브라우저가 보내는 최소 헤더 묶음. Referer 는 같은 사이트 루트로 기본 세팅."""
    parts = urlsplit(url)
    if referer is None and parts.scheme and parts.netloc:
        referer = f"{parts.scheme}://{parts.netloc}/"
    headers = {
        "User-Agent": UA_BROWSER,
        "Accept": accept,
        "Accept-Language": ACCEPT_LANGUAGE,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin" if referer else "none",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def get(
    url: str,
    *,
    timeout: int = 45,
    referer: str | None = None,
    headers: dict | None = None,
    stream: bool = False,
    allow_redirects: bool = True,
    retries: int = 2,
    backoff: float = 2.0,
    session: requests.Session | None = None,
) -> requests.Response:
    """브라우저 헤더를 붙인 GET. 네트워크 예외만 재시도하고 4xx/5xx 는 그대로 돌려준다."""
    hdrs = browser_headers(url, referer=referer)
    if headers:
        hdrs.update(headers)
    caller = session or requests
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return caller.get(
                url,
                headers=hdrs,
                timeout=timeout,
                stream=stream,
                allow_redirects=allow_redirects,
                verify=verify_setting(),
            )
        except requests.RequestException as exc:  # 연결 실패·타임아웃만 재시도
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def meta_refresh_target(body: bytes, base_url: str) -> str | None:
    """meta refresh 리다이렉트 대상(절대 URL). 없으면 None."""
    m = _META_REFRESH_RE.search(body)
    if not m:
        return None
    return urljoin(base_url, m.group(1).decode("utf-8", errors="replace").strip())


def curl_status(url: str, timeout: int = 45) -> int | None:
    """파이썬 TLS 로 악수 실패한 URL 을 curl 로 한 번 더 확인한다.

    www.sonylife.co.jp 처럼 requests 는 SSLV3_ALERT_HANDSHAKE_FAILURE 인데 curl 은
    200 인 사이트가 있다. 클라이언트 사정으로 죽은 링크를 만들어 내지 않기 위한 대조.
    """
    if not shutil.which("curl"):
        return None
    try:
        out = subprocess.run(
            ["curl", "-sS", "-o", os.devnull, "-w", "%{http_code}", "-L", "--max-time",
             str(timeout), "-A", UA_BROWSER, url],
            capture_output=True, text=True, timeout=timeout + 10,
        )
        code = (out.stdout or "").strip()[-3:]
        # curl 은 연결 자체가 실패하면 "000" 을 찍는다 — 상태코드 0 으로 넘기면
        # 호출부에서 "응답은 받았는데 0" 처럼 읽히므로 None 으로 정규화한다.
        return int(code) if (code.isdigit() and int(code) > 0) else None
    except Exception:
        return None


def looks_like_spa(body: bytes, content_type: str) -> tuple[bool, dict]:
    """정적 fetch 로 링크를 딸 수 없는 JS 렌더링 셸인지. (판정, 근거수치)"""
    detail = {"bytes": len(body), "anchors": 0, "scripts": 0}
    if "html" not in (content_type or "").lower():
        return False, detail
    detail["anchors"] = len(_ANCHOR_RE.findall(body))
    detail["scripts"] = len(_SCRIPT_RE.findall(body))
    is_spa = detail["anchors"] == 0 and detail["scripts"] >= 1
    return is_spa, detail


def probe(url: str, *, timeout: int = 45, compare_bare: bool = True, max_body: int = 400_000,
          hard_cap: int = 4_000_000, _depth: int = 0) -> dict:
    """URL 1건 생존 점검. classification 5종으로 분류해 dict 반환.

    - ``ok``                : 브라우저 헤더로 200, 정적으로 읽힘
    - ``ok_requires_headers``: 브라우저 헤더로 200 인데 기본 fetcher(헤더 없음)는 4xx —
      **URL 은 살아 있다.** census 에 not_found 로 적지 말 것
    - ``spa_shell``         : 200 이지만 JS 렌더링 셸이라 정적 링크 수집 불가
    - ``dead``              : 404/410 — 진짜 이동, 대체 URL 필요
    - ``blocked``           : 그 외 4xx(400·403·429 …) — WAF/봇룰. 브라우저에선 열릴 수
      있다. **죽음으로 적지 말 것**
    - ``tls_client_issue``  : 파이썬은 악수 실패인데 curl 은 200 — 우리 쪽 TLS 문제
    - ``error``             : 5xx·타임아웃 등 나머지

    meta refresh(``<meta http-equiv="refresh">``)는 최대 2홉 따라간다 — 안 따라가면
    리다이렉트 안내 페이지를 "링크 0개 SPA" 로 오진한다.
    """
    out: dict = {
        "url": url,
        "status": None,
        "bare_status": None,
        "final_url": None,
        "content_type": None,
        "classification": "error",
        "error": None,
        "expiring_host": any(urlsplit(url).netloc.lower() == h for h in EXPIRING_HOSTS),
    }
    try:
        resp = get(url, timeout=timeout, stream=True)
        body = resp.raw.read(max_body, decode_content=True) or b""
        truncated = len(body) >= max_body
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if truncated and "html" in ctype and not _ANCHOR_RE.search(body):
            # 앞부분이 인라인 base64 이미지·거대 인라인 CSS 로 채워져 있으면 400KB 안에
            # <a> 가 한 개도 없을 수 있다 — 그걸 SPA 로 읽으면 멀쩡한 정적 페이지가
            # "정적 수집 불가" 로 분류된다(2026-09-13 アクサ生命 3행 오탐). 그때만
            # 나머지를 더 읽는다(상한 hard_cap).
            body += resp.raw.read(hard_cap - max_body, decode_content=True) or b""
        resp.close()
        out["status"] = resp.status_code
        out["final_url"] = resp.url
        out["content_type"] = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
        if resp.status_code == 200:
            is_spa, detail = looks_like_spa(body, out["content_type"])
            out.update(detail)
            out["classification"] = "spa_shell" if is_spa else "ok"
        elif resp.status_code in (404, 410):
            out["classification"] = "dead"
        elif 400 <= resp.status_code < 500:
            out["classification"] = "blocked"
            out["error"] = f"HTTP {resp.status_code}"
        else:
            out["classification"] = "error"
            out["error"] = f"HTTP {resp.status_code}"
    except requests.exceptions.SSLError as exc:
        out["error"] = f"SSLError: {str(exc)[:160]}"
        code = curl_status(url, timeout=timeout)
        out["curl_status"] = code
        if code and code < 400:
            out["classification"] = "tls_client_issue"
        elif code in (404, 410):
            out["classification"] = "dead"
        return out
    except requests.RequestException as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out

    if out["status"] == 200 and _depth < 2:
        target = meta_refresh_target(body, resp.url)
        if target and target.rstrip("/") != resp.url.rstrip("/"):
            hop = probe(target, timeout=timeout, compare_bare=compare_bare,
                        max_body=max_body, hard_cap=hard_cap, _depth=_depth + 1)
            hop["meta_refresh_from"] = url
            hop.setdefault("meta_refresh_chain", []).insert(0, url)
            hop["url"] = url  # 보고는 원래 URL 기준으로
            hop["resolved_url"] = target
            return hop

    if compare_bare and out["status"] == 200:
        # 헤더 없는 기본 fetcher 와 비교 — 403/401/429 면 "봇차단이지 죽은 URL 아님"
        try:
            bare = requests.get(
                url,
                headers={"User-Agent": "python-requests"},
                timeout=timeout,
                stream=True,
                verify=verify_setting(),
            )
            bare.close()
            out["bare_status"] = bare.status_code
            if bare.status_code in (401, 403, 406, 429) and out["classification"] == "ok":
                out["classification"] = "ok_requires_headers"
        except requests.RequestException as exc:
            out["bare_status"] = f"{type(exc).__name__}"
    return out
