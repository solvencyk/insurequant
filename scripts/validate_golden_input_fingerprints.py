#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빌더를 **돌리지 않고** "마스터가 자기 입력보다 낡았는가" 만 판정한다 (owner 승인 2026-08-28,
`inbox/validation/20260829T0300Z`).

## 왜 있나 (실제로 터진 사고)

```
2026-08-21  0c04537   ifrs17_bs 골든 fixture + IFRS17_BS.json 마지막 동시 갱신
2026-08-26  8c1666b   삼성생명 OFS 캐시 정정 — BS 마스터는 재빌드 안 됨
2026-08-28  발견       골든 실패. 삼성생명 2024년 4개 분기가 연결 기준 잔재로 남아 있었다
```

`tests/test_ifrs17_bs_golden.py` 는 빌더를 통째로 재실행해서 **실측 492·514초** 가 걸린다.
`scripts/prepush_check.py` 의 예산이 ~5분이라 훅의 오프라인 묶음에서 빠져 있었고, 그래서
이틀간 아무도 몰랐다. `CLAUDE.md` 가 못박은 **"배선했다 ≠ 강제된다"** 의 교과서 사례다 —
골든은 존재했고 룰도 옳았는데 **훅이 안 돌려서** 무력했다.

## 무엇을 검사하나 — 3축

빌더가 결정론적·오프라인이라면(대상 6종 전부 그렇다. 각 골든 docstring 이 근거를 적고 있다)

    입력 불변 ∧ 코드 불변 ∧ 산출 불변  ⟹  지금 다시 빌드해도 같은 바이트가 나온다

이므로, 세 축이 전부 붙어 있는 동안은 무거운 골든이 **증명적으로 잉여**다. 하나라도 어긋나면
"마스터가 낡았을 수 있다 — 전체 골든을 돌려라" 로 push 를 막는다.

  1. `inputs`  — 빌더가 **실제로 읽는** 파일 전부의 내용해시.
     경로는 추정이 아니라 **런타임 관측**으로 확정했다
     (`scripts/_probes/probe_20260829_trace_builder_reads.py`, 감사훅이 첫 쓰기에서
     프로세스를 죽여 트리를 안 건드리고 읽기 집합만 뜬다). 정적 문자열 census 는
     `DART.glob(f"FY*_Q*")` · `__import__(f"scripts.reserve_extract.{name}")` 같은 동적
     조립을 양방향으로 놓친다 — 2026-08-25 에 같은 이유로 검사기 6개가 무검사였다.
     **패턴은 일부러 넉넉히 잡는다.** 과대포함은 헛RED(안전한 방향)이고 과소포함은
     그대로 false-green 이다.
  2. `code`    — 빌더 스크립트 + 그것이 import 하는 **프로젝트 모듈 전부**(AST 폐포).
     입력이 그대로여도 빌더가 바뀌면 마스터는 낡는다. 이 축을 빠뜨리기 쉽다.
     패키지를 import 하면 그 패키지의 `*.py` 를 통째로 넣는다 —
     `scripts/reserve_extract/__init__.py` 가 `__import__(f"...{name}")` 로 서브모듈을
     동적으로 끌어오기 때문에 AST 만으로는 안 보인다.
  3. `output`  — 골든 fixture 가 박제한 산출 바이트 = 지금 디스크의 산출 바이트.
     공짜다(수 MB 해시 1회). 빌더를 돌린 뒤 fixture 를 `--update` 안 한 경우와
     마스터를 손으로 고친 경우를 잡는다.
  (+) `fixture` — fixture 자체의 해시. fixture 를 재생성했는데 이 지문을 `--update` 안 하면
     RED. 둘의 짝을 기계가 강제한다.

## 이건 무거운 골든의 **대체가 아니라 층**이다

지문은 "재료가 바뀌었나" 만 본다. 산출이 실제로 맞는지는 여전히 전체 골든이 판정한다.
무거운 골든을 지우거나 약화시키지 마라(티켓 §3).

## 산출이 정당하게 바뀌었을 때

    <full golden 을 돌려서 통과시킨 뒤>
    python scripts/validate_golden_input_fingerprints.py --update
    (커밋 메시지에 왜 움직였는지 남길 것)

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
     scripts/validate_golden_input_fingerprints.py [--update] [--verbose]
exit 0 = 전 축 일치 · 2 = 하나 이상 어긋남(push 차단)
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "tests" / "fixtures" / "builder_input_fingerprints.json"

# ---------------------------------------------------------------------------
# 대상 명세. `inputs` 는 런타임 트레이스로 확정했고, 그 근거를 `evidence` 에 적는다.
# 새 골든이 빌더를 재실행하게 만들면 `tests/test_golden_input_fingerprint.py` 가
# 여기에 등재를 강제한다(등재 안 하면 테스트가 막는다).
# ---------------------------------------------------------------------------
SPECS: dict[str, dict] = {
    "ifrs17_bs": {
        "golden": "tests/test_ifrs17_bs_golden.py",
        "fixture": "tests/fixtures/ifrs17_bs_golden.json",
        "why": "빌더 재실행 492·514초 — 훅 예산(~5분) 초과라 오프라인 묶음에서 빠져 있다",
        "code_entries": ["scripts/build_ifrs17_bs.py"],
        "inputs": [
            "data/dart/_fs_api_cache/*.json",
            "data/dart/FY*_Q*/raw/**/*.xml",
            "kics_disclosure.json",
            "data/dart/viz/bs_manual_overrides.json",
            # build_equity_composition_tier2 → src.ifrs17.csm_extractor → scoring 이 읽는다.
            # **빌더 소스만 읽었으면 놓쳤을 입력**이다(import 두 단계 아래, lru_cache).
            "data/ifrs17/table_scoring_keywords.yaml",
        ],
        # fixture 의 이 키 -> 그 해시가 가리키는 산출 파일
        "outputs": {"sha256": "IFRS17_BS.json"},
        "evidence": "probe_20260829_trace_builder_reads.py scripts/build_ifrs17_bs.py",
    },
    "pl_breakdown": {
        "golden": "tests/test_pl_breakdown_golden.py",
        "fixture": "tests/fixtures/pl_breakdown_golden.json",
        "why": "빌더 재실행 ~95초 + RUN_PL_GOLDEN=1 opt-in — 평소 아무도 안 돌린다",
        "code_entries": ["scripts/build_pl_breakdown.py"],
        "inputs": [
            "data/dart/_fs_api_cache/*.json",
            "data/dart/FY*_Q*/raw/**/*.xml",
            # src/ifrs17/scoring.py 의 표-선택 키워드. 빌더 소스만 읽어서는 안 보이는 입력이다
            # (import 두 단계 아래에서 lru_cache 로 읽는다) — 트레이스가 아니었으면 놓쳤다.
            "data/ifrs17/table_scoring_keywords.yaml",
            "kics_disclosure.json",
        ],
        # 트레이스에 `.env` 도 나오지만(OpenDART 키) **일부러 뺐다**: 오프라인 빌드에서는
        # 산출을 결정하지 않고, 비밀값 파일을 해시해 fixture 에 남기는 것도 옳지 않다.
        "outputs": {
            "sha256_master": "data/dart/viz/pl_breakdown_master.json",
            "sha256_coverage": "data/_derived/pl_breakdown_coverage.json",
        },
        "evidence": "probe_20260829_trace_builder_reads.py scripts/build_pl_breakdown.py",
    },
    "viz_csm_waterfall": {
        "golden": "tests/test_viz_csm_waterfall_golden.py",
        "fixture": "tests/fixtures/viz_csm_waterfall_golden.json",
        "why": "빌더 재실행 ~1.5초 — 싸지만 훅의 오프라인 묶음에 없다(산출을 인플레이스로 덮어씀)",
        "code_entries": ["scripts/viz_build_csm_waterfall.py"],
        "inputs": ["data/dart/extracted/*.json"],
        "outputs": {"sha256": "data/dart/viz/csm_waterfall.json"},
        "evidence": "probe_20260829_trace_builder_reads.py scripts/viz_build_csm_waterfall.py "
                    "(관측 47개 = *_measurement.json; 패턴은 넉넉히 extracted/*.json 전체)",
    },
    "viz_ifrs17_panels": {
        "golden": "tests/test_viz_ifrs17_panels_golden.py",
        "fixture": "tests/fixtures/viz_ifrs17_panels_golden.json",
        "why": "빌더 재실행 ~1.5초 — 싸지만 훅의 오프라인 묶음에 없다(산출 4개를 인플레이스로 덮어씀)",
        "code_entries": ["scripts/viz_build_ifrs17_panels.py"],
        "inputs": [
            "data/dart/extracted/*.json",
            "CSM_waterfall.json",
            "data/dart/viz/sensitivity_overrides.json",
        ],
        # 이 골든의 fixture 는 `files` 밑에 파일별로 sha256 을 넣는다(중첩) — 아래 _output_pairs 참조
        "outputs_nested": ("files", "sha256", "data/dart/viz"),
        "evidence": "probe_20260829_trace_builder_reads.py scripts/viz_build_ifrs17_panels.py "
                    "— 트레이스는 첫 패널 쓰기에서 멈추므로 나머지 3패널의 glob "
                    "(*_insurance_pl_mvp/*_bs_snapshot_mvp/*_sensitivity)은 main() 의 "
                    "outputs 표에서 확인해 extracted/*.json 로 통합했다",
    },
    "dividend": {
        "golden": "tests/test_dividend_golden.py",
        "fixture": "tests/fixtures/dividend_golden.json",
        "why": "빌더 재실행 <1초 — 싸지만 훅의 오프라인 묶음에 없다(루트 마스터를 덮어씀)",
        "code_entries": ["scripts/build_dividend.py"],
        "inputs": [
            "data/dart/_alotmatter_cache/*.json",
            "data/_derived/alotmatter_fetch_census.json",
            "kics_disclosure.json",
        ],
        "outputs": {"sha256": "dividend.json"},
        "evidence": "probe_20260829_trace_builder_reads.py scripts/build_dividend.py "
                    "(관측 627개 = census 1 + 캐시 624 + kics_disclosure 1)",
    },
    "post_transition": {
        "golden": "tests/test_post_transition_golden.py",
        "fixture": "tests/fixtures/post_transition_golden.json",
        "why": "훅의 오프라인 묶음에 이미 있다(~8초). 지문은 중복 방어이자 "
               "'입력이 움직였는데 fixture 가 안 움직였다'를 축별로 지목해 준다",
        "code_entries": ["scripts/fill_post_transition_to_disclosure.py"],
        "inputs": ["md_inbox/FY*_Q?/*.md", "kics_disclosure.json"],
        # 이 골든은 파생값 해시만 박제하고 파일을 쓰지 않는다 — 산출 축 없음.
        "outputs": {},
        "evidence": "probe_20260829_trace_builder_reads.py --call "
                    "tests/test_post_transition_golden.py:_derive (관측 499 = MD 498 + kics 1)",
    },
}


# ---------------------------------------------------------------------------
# 해싱
# ---------------------------------------------------------------------------
def _sha_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            n += len(b)
            h.update(b)
    return h.hexdigest(), n


_MEMO: dict[Path, tuple[str, int]] = {}


def _witness(item: tuple[Path, bool]) -> tuple[str, int]:
    """파일 하나의 증언. `stat_only` 면 크기만, 아니면 내용해시.

    같은 파일을 두 명세가 공유한다(ifrs17_bs · pl_breakdown 이 둘 다 raw XML 트리를 읽는다).
    메모가 없으면 같은 바이트를 두 번 읽는다 — 메모 전 8.8초, 후 실측 그대로."""
    path, stat_only = item
    hit = _MEMO.get(path)
    if hit is None:
        if stat_only:
            hit = (f"size:{path.stat().st_size}", path.stat().st_size)
        else:
            hit = _sha_file(path)
        _MEMO[path] = hit
    return hit


def _digest(files: list[tuple[Path, bool]]) -> tuple[str, int, int]:
    """(집합해시, 파일수, 바이트). 경로+증언을 같이 넣어 **파일이 사라진 것**도 잡는다."""
    if not files:
        return hashlib.sha256(b"").hexdigest(), 0, 0
    # I/O 바운드 + hashlib 은 GIL 을 푼다. 실측(2.08GB/3,469파일 전량 내용해시):
    # 1스레드 11.8초 · 4스레드 4.6초 · 16스레드 3.3초. 16 이상은 더 안 빨라진다.
    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(_witness, files))
    acc = hashlib.sha256()
    total = 0
    for (path, _), (token, nbytes) in zip(files, results):
        rel = path.relative_to(ROOT).as_posix()
        acc.update(rel.encode("utf-8"))
        acc.update(b"\0")
        acc.update(token.encode("ascii"))
        acc.update(b"\n")
        total += nbytes
    return acc.hexdigest(), len(files), total


def _match(pattern: str) -> list[Path]:
    return sorted(p for p in ROOT.glob(pattern) if p.is_file())


# 내용해시 대신 (경로, 바이트수) 로만 증언하는 층. **이 목록에 뭘 넣을지는 신중하게.**
#
# 왜 예외를 두나: DART 본문 XML 은 1.95GB 이고 분기마다 커진다. 전량 내용해시는 실측
# 3.3초(16스레드)로 이 검사 전체 시간의 8할이고, 저장소가 커지면 그대로 늘어난다.
# 왜 그래도 안전한가: DART 필링은 rcept_no 단위로 **불변**이다 — 정정공시는 새 rcept_no
# = 새 경로로 들어오고, 같은 rcept 를 다시 받으면 같은 바이트다. 그래서 이 트리에서
# 실제로 일어나는 변화는 (a) 파일 추가 (b) 파일 소실 (c) 다른 필링으로 교체 셋뿐이고,
# 셋 다 (경로, 바이트수) 집합이 바뀐다. 같은 경로·같은 크기인데 내용만 다른 경우만
# 못 잡는데, 그건 손으로 바이트를 맞춰 고쳐 넣어야 나온다.
# 보조 방어: raw 소실은 `scripts/check_dart_raw_coverage.py` 가 high-water mark 로 따로 본다
# (2026-05~08 에 KB손해보험 등 8개사 raw 가 조용히 사라진 사고의 탐지기).
# **FS API 캐시·extracted·alotmatter·MD·YAML·루트 마스터는 전부 내용해시다** — 2026-08-26
# 드리프트의 진원지가 `data/dart/_fs_api_cache` 였으므로 거기를 약하게 만들면 안 된다.
STAT_ONLY = {"data/dart/FY*_Q*/raw/**/*.xml"}


# ---------------------------------------------------------------------------
# 코드 폐포 (AST)
# ---------------------------------------------------------------------------
_BASES = (ROOT, ROOT / "scripts", ROOT / "src")
# 동적 import 를 쓰는 패키지는 AST 로 서브모듈이 안 보인다 → 그 패키지만 통째로 넣는다.
# `scripts/reserve_extract/__init__.py` 의 `__import__(f"scripts.reserve_extract.{_name}")`
# 가 실제 사례다(회사별 준비금 핸들러 7모듈이 전부 이 경로로만 들어온다).
_DYNAMIC = ("__import__(", "importlib.import_module", "spec_from_file_location")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _files_for(base: Path, parts: list[str]) -> list[Path]:
    """`base` 밑 dotted 경로 -> .py 들. 경유하는 패키지의 `__init__.py` 도 전부 넣는다
    (안 넣으면 `src/__init__.py` 처럼 실제로 실행되는 파일이 지문에서 빠진다 — 런타임
    트레이스 대조로 확인한 실제 누락이다)."""
    out: list[Path] = []
    cur = base
    for part in parts:
        nxt = cur / part
        if nxt.is_dir():
            init = nxt / "__init__.py"
            if init.is_file():
                out.append(init)
                if any(t in _read(init) for t in _DYNAMIC):
                    out += sorted(nxt.rglob("*.py"))
            cur = nxt
            continue
        mod = nxt.with_suffix(".py")
        if mod.is_file():
            out.append(mod)
        return out                      # 더 깊은 조각은 모듈이 아니라 속성명이다
    return out


def _resolve(parts: list[str], extra_base: Path | None = None) -> list[Path]:
    for base in ((extra_base,) if extra_base else _BASES):
        hits = _files_for(base, parts)
        if hits:
            return hits
    return []


def _code_closure(entries: list[str]) -> list[Path]:
    seen: set[Path] = set()
    queue = [ROOT / e for e in entries]
    while queue:
        path = queue.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            tree = ast.parse(_read(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):            # 함수 안 지연 import 도 포함해야 한다
            if isinstance(node, ast.Import):
                for a in node.names:
                    queue += _resolve(a.name.split("."))
            elif isinstance(node, ast.ImportFrom):
                if node.level:                 # 상대 import: 그 파일의 패키지 기준
                    base = path.parent
                    for _ in range(node.level - 1):
                        base = base.parent
                    head = node.module.split(".") if node.module else []
                    queue += _resolve(head, extra_base=base) if head else []
                    for a in node.names:       # `from . import x` / `from .pkg import mod`
                        queue += _resolve(head + [a.name], extra_base=base)
                    continue
                if node.module:
                    head = node.module.split(".")
                    queue += _resolve(head)
                    # `from scripts import reserve_extract` — 모듈명이 alias 쪽에 있다
                    for a in node.names:
                        queue += _resolve(head + [a.name])
    return sorted(seen)


# ---------------------------------------------------------------------------
# 지문 계산
# ---------------------------------------------------------------------------
def _output_pairs(spec: dict, fixture: dict) -> list[tuple[tuple[str, ...], Path]]:
    """(fixture 안의 해시 키경로, 그 해시가 가리키는 산출 파일).

    키경로는 **튜플**이다 — 점으로 이어붙이면 `files.csm_amort_schedule.json.sha256` 처럼
    이름 안의 점에서 쪼개져 조회가 항상 None 이 되고, 그 None 이 그대로 OUTPUT_DRIFT 4건으로
    나온다(실제로 그렇게 오탐이 났다)."""
    pairs: list[tuple[tuple[str, ...], Path]] = []
    for key, rel in (spec.get("outputs") or {}).items():
        pairs.append(((key,), ROOT / rel))
    nested = spec.get("outputs_nested")
    if nested:
        container, key, dirrel = nested
        for fname in sorted(fixture.get(container, {})):
            pairs.append(((container, fname, key), ROOT / dirrel / fname))
    return pairs


def _fixture_hash_for(fixture: dict, keypath: tuple[str, ...]) -> str | None:
    node: object = fixture
    for part in keypath:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, str) else None


def compute(name: str, spec: dict) -> dict:
    per_pattern = {}
    all_inputs: list[tuple[Path, bool]] = []
    for pat in spec["inputs"]:
        files = _match(pat)
        per_pattern[pat] = len(files)
        all_inputs += [(f, pat in STAT_ONLY) for f in files]
    all_inputs = sorted(set(all_inputs))
    in_dig, in_n, in_bytes = _digest(all_inputs)

    code_files = _code_closure(spec["code_entries"])
    code_dig, code_n, _ = _digest([(f, False) for f in code_files])

    fx_path = ROOT / spec["fixture"]
    fixture = json.loads(fx_path.read_text(encoding="utf-8")) if fx_path.is_file() else {}
    fx_dig = _sha_file(fx_path)[0] if fx_path.is_file() else None

    outputs = {}
    for keypath, out_path in _output_pairs(spec, fixture):
        outputs[" / ".join(keypath)] = {
            "path": out_path.relative_to(ROOT).as_posix(),
            "fixture_sha256": _fixture_hash_for(fixture, keypath),
            "ondisk_sha256": _sha_file(out_path)[0] if out_path.is_file() else None,
        }

    return {
        "inputs_sha256": in_dig,
        "input_files": in_n,
        "input_bytes": in_bytes,
        "input_files_per_pattern": per_pattern,
        "code_sha256": code_dig,
        "code_files": [p.relative_to(ROOT).as_posix() for p in code_files],
        "fixture_sha256": fx_dig,
        "outputs": outputs,
    }


# ---------------------------------------------------------------------------
# 대조
# ---------------------------------------------------------------------------
_HINT = ("→ 전체 골든을 돌려서 산출이 정말 안 움직였는지 확인한 뒤, 움직였으면 골든을 "
         "--update 하고, 그다음 `python scripts/validate_golden_input_fingerprints.py --update`")


def check(name: str, spec: dict, stored: dict | None, actual: dict) -> list[str]:
    reds: list[str] = []
    if stored is None:
        return [f"[{name}] 등재가 없다 — 이 골든의 지문이 한 번도 기록된 적이 없다. --update 로 만들어라"]

    # 축 1: 입력
    if stored.get("inputs_sha256") != actual["inputs_sha256"]:
        reds.append(
            f"[{name}] INPUTS_MOVED — 빌더 입력이 바뀌었는데 골든 fixture 는 그대로다. "
            f"마스터가 낡았을 수 있다 (파일 {stored.get('input_files')}→{actual['input_files']}개, "
            f"{stored.get('input_bytes')}→{actual['input_bytes']} bytes). {_HINT}")
    # 패턴이 0건이 되는 것은 따로 지목한다 — 디렉터리가 옮겨지면 지문은 '안정적으로 빈' 값이 되어
    # 조용히 false-green 이 된다. 이 저장소가 반복해서 당한 형태다.
    for pat, n_now in actual["input_files_per_pattern"].items():
        n_was = (stored.get("input_files_per_pattern") or {}).get(pat)
        if n_was and not n_now:
            reds.append(f"[{name}] INPUT_PATTERN_EMPTY — 패턴 '{pat}' 이 {n_was}→0건. "
                        f"경로가 옮겨졌거나 데이터가 사라졌다(지문은 '안정적으로 빈' 값이 된다)")
    # 축 2: 코드
    if stored.get("code_sha256") != actual["code_sha256"]:
        was, now = set(stored.get("code_files") or []), set(actual["code_files"])
        delta = ""
        if was != now:
            delta = f" (추가 {sorted(now - was)} · 삭제 {sorted(was - now)})"
        reds.append(
            f"[{name}] CODE_MOVED — 빌더 코드/의존 모듈이 바뀌었는데 골든 fixture 는 그대로다"
            f"{delta}. {_HINT}")
    # 축 (+): fixture 자체
    if stored.get("fixture_sha256") != actual["fixture_sha256"]:
        reds.append(
            f"[{name}] FIXTURE_MOVED — 골든 fixture 가 재생성됐는데 이 지문이 --update 되지 "
            f"않았다. 둘은 항상 같이 움직여야 한다")
    # 축 3: 산출
    for keypath, info in actual["outputs"].items():
        if info["ondisk_sha256"] is None:
            reds.append(f"[{name}] OUTPUT_MISSING — {info['path']} 이 없다")
        elif info["fixture_sha256"] != info["ondisk_sha256"]:
            reds.append(
                f"[{name}] OUTPUT_DRIFT — {info['path']} 의 지금 바이트가 골든 fixture 의 "
                f"박제({keypath})와 다르다. 빌더를 돌리고 --update 를 안 했거나 마스터를 손으로 "
                f"고쳤다. {_HINT}")
    return reds


def main(argv: list[str]) -> int:
    update = "--update" in argv
    verbose = "--verbose" in argv
    record = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.is_file() else {}
    stored_specs = record.get("specs", {})

    computed = {name: compute(name, spec) for name, spec in SPECS.items()}

    if update:
        RECORD.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "_what": (
                "빌더 입력·코드·산출의 3축 지문. 무거운 골든(ifrs17_bs 8분 · pl_breakdown 95초)을 "
                "훅에서 돌릴 수 없어 생긴 사각을 메운다 — 빌더를 안 돌리고 '마스터가 자기 입력보다 "
                "낡았는가' 만 수초에 판정한다. 이 파일은 손으로 고치지 말고 "
                "scripts/validate_golden_input_fingerprints.py --update 로 재생성할 것."),
            "_contract": (
                "입력 불변 ∧ 코드 불변 ∧ 산출 불변 ⟹ 지금 다시 빌드해도 같은 바이트. 하나라도 "
                "어긋나면 전체 골든을 돌려 확인한 뒤 --update 한다. 지문은 무거운 골든의 대체가 "
                "아니라 층이다."),
            "specs": {},
        }
        for name, spec in SPECS.items():
            c = dict(computed[name])
            c["_golden"] = spec["golden"]
            c["_why_not_in_hook"] = spec["why"]
            c["_input_patterns"] = {p: ("stat(path+size)" if p in STAT_ONLY else "content-sha256")
                                    for p in spec["inputs"]}
            c["_evidence"] = spec["evidence"]
            payload["specs"][name] = c
        RECORD.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        print(f"updated {RECORD.relative_to(ROOT).as_posix()}")
        for name, c in computed.items():
            print(f"  {name}: inputs {c['input_files']}개/{c['input_bytes']/1e6:.1f}MB · "
                  f"code {len(c['code_files'])}개 · outputs {len(c['outputs'])}개")
        return 0

    print("=" * 72)
    print("GOLDEN INPUT FINGERPRINT  (빌더 미실행 — 입력·코드·산출 3축 대조)")
    print("=" * 72)
    reds: list[str] = []
    for name, spec in SPECS.items():
        c = computed[name]
        r = check(name, spec, stored_specs.get(name), c)
        reds += r
        mark = "FAIL" if r else "ok  "
        print(f"  {mark} {name:18s} inputs={c['input_files']:5d} "
              f"({c['input_bytes']/1e6:7.1f}MB) code={len(c['code_files']):3d} "
              f"outputs={len(c['outputs'])}   [{spec['golden']}]")
        if verbose:
            for pat, n in c["input_files_per_pattern"].items():
                print(f"         {n:5d}  {pat}")
    if not stored_specs:
        print("\n  등재 파일이 없다 — `--update` 로 최초 지문을 만들어라: "
              f"{RECORD.relative_to(ROOT).as_posix()}")
    for r in reds:
        print("\n  RED " + r)
    print("\n" + ("-" * 72))
    print(f"  RED={len(reds)} → {'BLOCK' if reds else 'clear'}")
    return 2 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
