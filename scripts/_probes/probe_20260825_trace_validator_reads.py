# -*- coding: utf-8 -*-
"""검사기가 런타임에 **실제로 여는** 파일을 추적한다 (정적분석 오탐/누락 제거).

정적 census 는 양방향으로 틀린다:
  · 문자열 리터럴만 세면 `VIZ / 'x.json'` 조립을 놓쳐 **UNREAD 오탐**
  · AST 로 상수를 풀어도 헬퍼 인자로 흘러가는 경로를 놓쳐 **UNREAD 오탐**
그래서 여기서는 `builtins.open` / `Path.read_*` / `Path.open` 을 감싸고 검사기를 실제로 돌려
열린 경로를 기록한다. 이것이 "그 게이트가 그 파일을 검사하는가" 의 정본 증거다.

산출물을 덮어쓰는 검사기가 있으므로 워킹트리를 더럽히지 않게 **쓰기는 전부 차단**하고
(no-op) 원본 바이트를 보존한다.

사용: python scripts/_probes/probe_20260825_trace_validator_reads.py [validator_stem ...]
"""
from __future__ import annotations

import builtins
import io
import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OPENED_READ: set[str] = set()
OPENED_WRITE: set[str] = set()

_real_open = builtins.open
_real_path_open = Path.open
_real_read_text = Path.read_text
_real_read_bytes = Path.read_bytes
_real_write_text = Path.write_text
_real_write_bytes = Path.write_bytes
_real_replace = os.replace


def _rel(p) -> str | None:
    try:
        rp = Path(p).resolve()
    except Exception:
        return None
    try:
        return rp.relative_to(ROOT).as_posix()
    except ValueError:
        return None


def _note(p, mode: str):
    r = _rel(p)
    if not r:
        return
    if any(w in mode for w in ("w", "a", "x", "+")):
        OPENED_WRITE.add(r)
    else:
        OPENED_READ.add(r)


def open_hook(file, mode="r", *a, **k):
    _note(file, mode)
    if any(w in mode for w in ("w", "a", "x")):
        return io.StringIO() if "b" not in mode else io.BytesIO()
    return _real_open(file, mode, *a, **k)


def path_open_hook(self, mode="r", *a, **k):
    _note(self, mode)
    if any(w in mode for w in ("w", "a", "x")):
        return io.StringIO() if "b" not in mode else io.BytesIO()
    return _real_path_open(self, mode, *a, **k)


def rt_hook(self, *a, **k):
    _note(self, "r")
    return _real_read_text(self, *a, **k)


def rb_hook(self, *a, **k):
    _note(self, "r")
    return _real_read_bytes(self, *a, **k)


def wt_hook(self, data, *a, **k):
    _note(self, "w")
    return len(data)


def wb_hook(self, data, *a, **k):
    _note(self, "w")
    return len(data)


def replace_hook(src, dst, *a, **k):
    _note(dst, "w")
    return None


def install():
    builtins.open = open_hook
    Path.open = path_open_hook
    Path.read_text = rt_hook
    Path.read_bytes = rb_hook
    Path.write_text = wt_hook
    Path.write_bytes = wb_hook
    os.replace = replace_hook


def restore():
    builtins.open = _real_open
    Path.open = _real_path_open
    Path.read_text = _real_read_text
    Path.read_bytes = _real_read_bytes
    Path.write_text = _real_write_text
    Path.write_bytes = _real_write_bytes
    os.replace = _real_replace


def trace(stem: str) -> dict:
    OPENED_READ.clear()
    OPENED_WRITE.clear()
    script = ROOT / "scripts" / f"{stem}.py"
    argv = sys.argv[:]
    sys.argv = [str(script)]
    if stem == "validate_master_tables":
        sys.argv.append("--no-build")  # 파괴적 재빌드 진입점 차단
    cwd = os.getcwd()
    os.chdir(ROOT)
    install()
    err = None
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit:
        pass
    except BaseException as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {e}"
    finally:
        restore()
        os.chdir(cwd)
        sys.argv = argv
    return {"reads": sorted(OPENED_READ), "writes": sorted(OPENED_WRITE), "error": err}


def main() -> int:
    stems = sys.argv[1:] or [p.stem for p in sorted((ROOT / "scripts").glob("validate_*.py"))]
    out: dict[str, dict] = {}
    for s in stems:
        r = trace(s)
        out[s] = r
        j = [x for x in r["reads"] if x.endswith(".json")]
        print(f"\n[{s}] err={r['error']}")
        print(f"   READ json ({len(j)}): {j}")
    dest = ROOT / "scripts" / "_probes" / "_trace_validator_reads_out.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
