#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빌더가 **실제로 읽는** 파일과 **실제로 import 하는** 프로젝트 모듈을 런타임으로 뜬다.

`inbox/validation/20260829T0300Z` (골든 입력지문 게이트)의 근거 수집기다. 티켓이 못박듯
지문에서 입력을 하나라도 빠뜨리면 그대로 false-green 이 되므로, 소스를 눈으로 읽어 만든
열거를 **런타임 관측으로 대조**한다. 2026-08-25 에 같은 이유로
`probe_20260825_trace_validator_reads.py` 를 썼다 — 정적 문자열 census 는 동적 경로 조립
(`DART.glob(f"FY*_Q*")`, `__import__(f"scripts.reserve_extract.{name}")`)을 양방향으로 놓친다.

**트리를 절대 바꾸지 않는다.** 감사훅이 쓰기 의도의 open 을 처음 만나는 순간 트레이스를
덤프하고 `os._exit` 로 죽는다(except 로 못 잡는다). 이 저장소의 빌더 6종은 전부 main() 끝에서
한 번에 쓰므로 읽기 단계는 그 시점에 이미 끝나 있다(`grep -n write_text` 로 확인).

사용:
  python scripts/_probes/probe_20260829_trace_builder_reads.py scripts/build_dividend.py
  python scripts/_probes/probe_20260829_trace_builder_reads.py --call tests/test_post_transition_golden.py:_derive
출력: data/_derived/_probe_builder_reads/<name>.json  (읽은 파일 · import 한 프로젝트 모듈)
"""
from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "data" / "_derived" / "_probe_builder_reads"

_reads: set[str] = set()
_target_name = "unknown"
_dying = False          # 덤프 자체가 파일을 열어 훅에 재진입하는 것을 막는다


_ROOT_S = os.path.normcase(str(ROOT))


def _rel(p: str) -> str | None:
    """ROOT 기준 상대경로. **순수 문자열 연산만 쓴다** — `Path.resolve()` 는 윈도우에서
    `nt._getfinalpathname` 이 파일을 열어 `open` 감사이벤트를 다시 쏘고, 이 훅이 그걸 또
    받아 무한재귀로 죽는다(실측 RecursionError)."""
    try:
        ap = os.path.normcase(os.path.abspath(p))
    except Exception:
        return None
    if not ap.startswith(_ROOT_S):
        return None                             # 트리 밖(venv/stdlib)은 지문 대상이 아니다
    return os.path.abspath(p)[len(str(ROOT)):].lstrip("\\/").replace("\\", "/")


def _dump_and_die(trigger: str) -> None:
    global _dying
    _dying = True
    mods = sorted({m for m in (
        _rel(getattr(mod, "__file__", "") or "") for mod in list(sys.modules.values())
    ) if m and m.endswith(".py")})
    OUTDIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": _target_name,
        "stopped_at_write": trigger,
        "reads": sorted(_reads),
        "project_modules": mods,
    }
    (OUTDIR / f"{_target_name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.stderr.write(f"[probe] {_target_name}: reads={len(_reads)} modules={len(mods)} "
                     f"stop={trigger}\n")
    sys.stderr.flush()
    os._exit(0)


def _hook(event: str, args) -> None:
    if _dying or event != "open":
        return
    path, mode, flags = args[0], args[1], args[2]
    if not isinstance(path, str):
        return
    rel = _rel(path)
    if rel is None:
        return
    writing = bool(mode and set(str(mode)) & set("wax+"))
    if not writing and isinstance(flags, int):
        writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND))
    if writing:
        _dump_and_die(rel)
    _reads.add(rel)


def main(argv: list[str]) -> int:
    global _target_name
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--call":
        modpath, func = argv[1].split(":")
        _target_name = Path(modpath).stem + "." + func
        sys.path.insert(0, str(ROOT))
        sys.addaudithook(_hook)
        ns = runpy.run_path(str(ROOT / modpath), run_name="_probe_target")
        ns[func]()
    else:
        script = argv[0]
        _target_name = Path(script).stem
        sys.path.insert(0, str(ROOT))
        sys.argv = [str(ROOT / script)] + argv[1:]
        sys.addaudithook(_hook)
        runpy.run_path(str(ROOT / script), run_name="__main__")
    _dump_and_die("(no write observed — builder finished without writing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
