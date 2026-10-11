#!/usr/bin/env python3
"""정기경영공시 raw PDF 의 디스크 위치를 푸는 단일 헬퍼.

**왜 있나 (2026-09-01).** 이 저장소는 13분기 동안 `data/disclosure/<period>/raw/` 에 회사별
PDF 를 떨궈 왔는데, **2026.2Q 부터 다운로더가 `<period>/pdf/` 로 바꿨다**(`src/solvency/config.py`
의 `disclosure_pdf_path()` 가 원래 선언한 정본 위치가 `pdf/` 다 — 즉 13분기 쪽이 관행이었고
2026.2Q 가 선언과 맞다). 실측 census:

    FY2023_Q1..FY2026_Q1   raw=38~40   pdf=0
    FY2026_Q1              raw=39      pdf=1
    FY2026_Q2              raw=1       pdf=39      <- 뒤집혔다

`raw/` 만 glob 하는 코드는 **2026.2Q 39사를 조용히 스킵한다.** 예외도 로그도 안 남기고
"원천이 없다" 로 흘러가 게이트에서 `UNMEASURED`/`NO_RAW_PDF` 로 찍힌다 —
`값이 틀리다` 가 아니라 `판정 근거가 통째로 비었다` 라서 눈에 안 띈다. 이 저장소에서 같은
버그가 최소 세 번 났다:

  1. `scripts/rebuild_combined_transition_after.py::_pdf()`  (수정됨)
  2. `scripts/fill_market_subitems_to_disclosure.py`         (수정됨, raw-first 폴백)
  3. `scripts/build_kics_source_textlayer.py` +
     `scripts/extract_transition_applicability.py::pdf_fallback` +
     `scripts/validate_kics_disclosure.py::_source_readability` (2026-09-01, 이 모듈로 수정)

**탐색 순서는 raw/ 우선, 없을 때만 pdf/ 다.** 과거 13분기의 해석을 한 칸도 바꾸지 않기 위한
것이다(raw/ 에 매치가 있으면 pdf/ 는 아예 안 본다). 새 분기처럼 raw/ 가 비어 있을 때만
pdf/ 로 떨어진다.

이 모듈은 stdlib 만 쓰고 부작용이 없다 — 게이트에서 import 해도 안전하다.

**2026-09-12 추가 (`save_versioned_pdf`)**: 같은 (분기,회사) 로 새 게시물이 오면 기존 raw 를
조용히 덮어쓰던 문제의 수정. 실측(`data/disclosure/*/raw/*_amended*.pdf` 110개 census) —
원본+정정본이 실제로 병존하는 건 1건뿐이고 그나마 바이트가 같았다. 나머지 109개는 애초에
원본이 저장된 적이 없는 "정정본만 단독 저장" 상태였다(과거 백필 스크립트들이 최신본 하나만
받아 `_amended` 로 이름 붙인 것 — 병존 매커니즘 자체가 없었다). 이 함수는 **호출 시점부터**
저장 직전에 기존 파일과 새 바이트를 비교해 다르면 원본을 그대로 둔 채 `_v<날짜>` 로 병존
저장한다. 과거분 소급 복원은 하지 않는다.

**2026-10-11 추가 (`latest_disclosure_pdfs` · `prefer_latest_edition` · `manifest_latest_name`)**: 병존 판이 생긴 뒤 `disclosure_pdfs()[0]` 이 옛 판을 고르는 문제의 수정.
실측(2026-10-11 census): (분기, 회사) 645조합 중 PDF 가 둘 이상인 곳은 4곳 — 뮌헨 2023.1Q·2Q(주 파일 = K-ICS 정정본, 옛 원본이 `_v20230101`), 스위스리 2023.4Q(옛 60쪽 `공시 예정` 판 대
새 85쪽 K-ICS 완성본 `_v20240510`), DB손보 2025.3Q(바이트 동일 `_amended2`). 어느 판이 최신인지는 이름순이나 파일 크기가 아니라 **다운로더 매니페스트**
(`data/disclosure/_meta/reinsurer_<code>_manifest.json` 의 `latest` > `versions` 마지막 > `file`)가 정한다. 한 판만 읽는 도구는 이 함수를 쓴다. 매니페스트가 없는 회사는 종전과 같다.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCLOSURE = ROOT / "data" / "disclosure"

# 탐색 순서. raw/ 가 먼저인 것이 계약이다 — 뒤집으면 과거 분기 해석이 바뀐다.
SUBDIRS = ("raw", "pdf")


def period_of(quarter: str) -> str:
    """'2026.2Q' -> 'FY2026_Q2'."""
    return f"FY{quarter[:4]}_Q{quarter[5]}"


def disclosure_pdfs(period: str, code: str, root: Path | None = None) -> list[Path]:
    """(period, 회사코드) -> 매칭되는 PDF 목록. raw/ 에 있으면 그것만, 없으면 pdf/ 를 본다.

    period 는 'FY2026_Q2' 형식. code 는 'KR0069' 같은 회사코드.
    반환은 정렬된 리스트이며, 못 찾으면 빈 리스트다.
    """
    base = (root or DISCLOSURE)
    for sub in SUBDIRS:
        d = base / period / sub
        if not d.is_dir():
            continue
        hits = sorted(d.glob(f"{code}_*.pdf"))
        if hits:
            return hits
    return []


def _period_label(period: str) -> str:
    """'FY2023_Q4' -> '2023.4Q' (the `period` key of a downloader manifest entry)."""
    return f"{period[2:6]}.{period[-1]}Q"


def manifest_latest_name(period: str, code: str, root: Path | None = None) -> str | None:
    """다운로더 매니페스트(`<disclosure>/_meta/reinsurer_<code>_manifest.json`)가 이 (분기, 회사)의 **쓸 판**이라고 적은 파일명(basename). 없으면 None.

    규칙(2026-10-11, 같은 분기에 raw PDF 가 둘일 때 도구가 옛 파일을 고르던 문제 — 스위스리 2023.4Q 60쪽 대 85쪽):
      그 분기 항목의 ``latest``(문자열 또는 ``{"file": ...}``) > ``versions`` 의 마지막 항목(다운로더가 새 판을 뒤에 덧붙인다 = 옛 `file` 을 대체하는 새 판)
      > ``file``(주 파일). ``alternates``(원본 등 비주 판)는 보지 않는다 — 뮌헨 2023.1Q·2Q 는 K-ICS 정정본이 주 파일(`file`)이고 옛 원본이 `_v` 로 병존한다.
    매니페스트가 없는 회사(기존 39사)는 항상 None 이라 종전 동작이 그대로다.
    """
    mf = (root or DISCLOSURE) / "_meta" / f"reinsurer_{code}_manifest.json"
    if not mf.is_file():
        return None
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    label = _period_label(period)
    for ent in data.get("periods", []):
        if not isinstance(ent, dict) or ent.get("period") != label:
            continue
        latest = ent.get("latest")
        if isinstance(latest, dict):
            latest = latest.get("file")
        if not latest:
            vers = [v for v in (ent.get("versions") or []) if isinstance(v, dict) and v.get("file")]
            latest = vers[-1]["file"] if vers else ent.get("file")
        return Path(str(latest).replace("\\", "/")).name if latest else None
    return None


def prefer_latest_edition(period: str, code: str, candidates, root: Path | None = None) -> list[Path]:
    """후보 파일들(PDF 든 md_inbox 의 MD 든) 중 매니페스트가 정한 최신 판의 짝만 남긴다. 후보가 1개 이하이거나 매니페스트가 판정하지 않으면 후보를 그대로 돌려준다.

    MD 는 docling 이 PDF 이름을 따라 짓기 때문에(`KR1102_스위스리아시아_v20240510.md`) stem 이 같은 것을 짝으로 본다.
    """
    cands = list(candidates)
    if len(cands) < 2:
        return cands
    name = manifest_latest_name(period, code, root)
    if not name:
        return cands
    stem = Path(name).stem
    hit = [c for c in cands if Path(c).stem == stem]
    return hit or cands


def latest_disclosure_pdfs(period: str, code: str, root: Path | None = None) -> list[Path]:
    """`disclosure_pdfs()` 와 같되, 같은 (분기, 회사)에 판이 둘 이상이면 **매니페스트가 정한 최신 판 하나**만 돌려준다(`manifest_latest_name`).

    "한 판만 읽는" 도구(`pdfs[0]` · `pdfs[-1]` · 정정본/최대크기 고르기)는 `disclosure_pdfs()` 대신 이것을 쓴다 — `disclosure_pdfs()` 는 모든 판을 이름순으로 줘서
    `[0]` 이 옛 판일 수 있다(스위스리 2023.4Q: 옛 60쪽 `…아시아.pdf` 가 새 85쪽 `…_v20240510.pdf` 보다 앞선다). 매니페스트가 판정하지 않는 (분기, 회사)는
    종전 목록 그대로라 기존 도구의 선택이 바뀌지 않는다.
    """
    return prefer_latest_edition(period, code, disclosure_pdfs(period, code, root), root)


def disclosure_pdf_dirs(period: str, root: Path | None = None) -> list[Path]:
    """(period) -> 존재하는 PDF 디렉토리들. raw/ 먼저, 그다음 pdf/."""
    base = (root or DISCLOSURE)
    return [base / period / sub for sub in SUBDIRS if (base / period / sub).is_dir()]


def save_versioned_pdf(
    dest: Path,
    content: bytes,
    *,
    title: str = "",
    url: str = "",
    posted: str | None = None,
) -> tuple[Path, str]:
    """``dest`` 에 ``content`` 를 저장하되 기존 파일을 절대 덮어쓰지 않는다.

    - ``dest`` 가 없으면 그냥 새로 쓴다 -> ``(dest, "new")``.
    - ``dest`` 가 있고 새 바이트의 sha256 이 기존과 같으면 아무것도 안 한다(로그 1줄만) ->
      ``(dest, "unchanged")``.
    - ``dest`` 가 있고 sha256 이 다르면(정정본 추정) 기존 파일은 그대로 두고
      ``<stem>_v<YYYYMMDD><ext>`` 로 병존 저장 + 같은 폴더 ``_versions.json`` 사이드카에
      ``{기본파일명: [{file, sha256, posted, title, url, fetched_at}, ...]}`` 형태로 append
      한다 -> ``(versioned_path, "versioned")``. 날짜는 ``posted``(YYYYMMDD 문자열, 게시일)가
      있으면 그걸 쓰고 없으면 다운로드 시각(UTC) 날짜를 쓴다. 같은 날짜로 이미 병존시킨
      바이트와 또 같으면(같은 정정본 재실행) 그 파일도 다시 쓰지 않는다(idempotent).

    stdlib(hashlib/json/datetime)만 쓴다 — 새 의존성 없음. 소급 복원은 하지 않는다 — 이미
    덮어써진 과거분은 이 함수로 되살릴 수 없다.
    """
    new_sha = hashlib.sha256(content).hexdigest()
    dest.parent.mkdir(parents=True, exist_ok=True)

    if not dest.exists():
        dest.write_bytes(content)
        return dest, "new"

    old_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    if old_sha == new_sha:
        print(f"  [disclosure_pdf_paths] UNCHANGED {dest.name} (sha256 동일 — 재저장 skip)")
        return dest, "unchanged"

    date_str = posted or datetime.now(timezone.utc).strftime("%Y%m%d")
    versioned = dest.with_name(f"{dest.stem}_v{date_str}{dest.suffix}")
    n = 2
    while versioned.exists():
        if hashlib.sha256(versioned.read_bytes()).hexdigest() == new_sha:
            return versioned, "unchanged"  # 이미 이 버전을 받아 둔 상태
        versioned = dest.with_name(f"{dest.stem}_v{date_str}_{n}{dest.suffix}")
        n += 1
    versioned.write_bytes(content)

    sidecar = dest.parent / "_versions.json"
    registry: dict = {}
    if sidecar.exists():
        try:
            registry = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            registry = {}
    registry.setdefault(dest.name, []).append({
        "file": versioned.name,
        "sha256": new_sha,
        "posted": posted,
        "title": title,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    sidecar.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  [disclosure_pdf_paths] VERSIONED {dest.name}: 새 바이트가 기존과 다름 -> "
          f"{versioned.name} 로 병존 저장(원본 유지)")
    return versioned, "versioned"


def find_disclosure_pdf(period: str, filename: str, root: Path | None = None) -> Path | None:
    """이미 알고 있는 파일명을 raw/ · pdf/ 어느 쪽에 있든 찾아 준다.

    사이드카가 기록한 파일명을 디스크와 대조(freshness 검사)할 때 쓴다 — 한쪽 디렉토리만
    보면 파일이 멀쩡히 있는데도 'stale' 로 강등되어 그 칸이 통째로 판정 불가가 된다.
    """
    base = (root or DISCLOSURE)
    for sub in SUBDIRS:
        p = base / period / sub / filename
        if p.exists():
            return p
    return None
