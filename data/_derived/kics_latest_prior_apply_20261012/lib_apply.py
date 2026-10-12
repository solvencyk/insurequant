"""lib_apply.py (parser-kics, ticket 20261012T2200Z) -- shared helpers for the 'latest prior column' APPLY run.

Only apply_master.py (and the small ledger scripts) write repo files.  Everything else here is read-only.
Master format facts (verified by round trip in apply_master.py): kics_disclosure.json = JSON list of 9-key row dicts,
json.dumps(ensure_ascii=False, indent=2), CRLF line endings, trailing CRLF, no BOM.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MASTER = REPO / "kics_disclosure.json"
OUT = REPO / "data" / "_derived" / "kics_latest_prior_apply_20261012"
PLANS = OUT / "plans"
BACKUP = OUT / "backup"
DRY = REPO / "data" / "_derived" / "kics_latest_prior_precedence_dryrun_20261012"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
ROW_KEYS = ["원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값", "값_적용후"]

# the 16 blocks that pass every ticket criterion (see held_blocks.csv for the other 72)
APPLIED = ["KR0003_2023.4Q", "KR0003_2025.1Q", "KR0004_2023.1Q", "KR0004_2024.1Q", "KR0009_2023.1Q", "KR0009_2023.2Q",
           "KR0032_2024.3Q", "KR0049_2025.1Q", "KR0049_2026.1Q", "KR0050_2025.3Q", "KR0069_2024.2Q", "KR0071_2024.4Q",
           "KR0072_2025.2Q", "KR0080_2026.1Q", "KR0095_2024.4Q", "KR0099_2024.3Q"]


def utf8_stdout():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p) -> str:
    return sha_bytes(Path(p).read_bytes())


def key(r) -> tuple:
    return (r["원보험사코드"], r["공시분기"], r["항목번호"])


def read_rows(p=MASTER):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def head_rows():
    out = subprocess.run(["git", "show", "HEAD:kics_disclosure.json"], cwd=REPO, capture_output=True)
    assert out.returncode == 0, out.stderr[:300]
    return json.loads(out.stdout.decode("utf-8"))


def dump_master_bytes(rows) -> bytes:
    s = json.dumps(rows, ensure_ascii=False, indent=2)
    return (s.replace("\n", "\r\n") + "\r\n").encode("utf-8")


def index_rows(rows) -> dict:
    idx = {}
    for i, r in enumerate(rows):
        k = key(r)
        if k in idx:
            raise RuntimeError(f"duplicate key {k}")
        idx[k] = i
    return idx


def write_json_lf(path, obj, indent=1):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
        f.write("\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_plan(name):
    return read_json(PLANS / f"{name}.json")


def apply_to_rows(rows, edits):
    """In place on `rows` (caller passes a deep copy when simulating).  Guard per cell: current value must equal the planned old
    value (type and value) -- otherwise the whole call raises and nothing is trusted.  Returns the number of edited cells."""
    idx = index_rows(rows)
    n = 0
    for e in edits:
        k = (e["code"], e["q"], e["item"])
        if k not in idx:
            raise RuntimeError(f"edit target row missing: {k}")
        r = rows[idx[k]]
        cur = r.get(e["field"], "<nokey>")
        if cur != e["old"]:
            raise RuntimeError(f"GUARD FAIL {k} {e['field']}: current {cur!r} != planned old {e['old']!r}")
        r[e["field"]] = e["new"]
        n += 1
    return n


def merge_plans(names):
    plans = [load_plan(n) for n in names]
    seen = {}
    for p in plans:
        for e in p["edits"]:
            k = (e["code"], e["q"], e["item"], e["field"])
            if k in seen:
                raise RuntimeError(f"cell edited by two plans: {k}")
            seen[k] = p["name"]
    return {"name": "+".join(p["name"] for p in plans), "edits": [e for p in plans for e in p["edits"]]}


def atomic_replace(tmp: Path, dest: Path, tries: int = 12, wait: float = 3.0):
    """os.replace with retries (another process may hold the destination open on Windows)."""
    import time
    for attempt in range(1, tries + 1):
        try:
            os.replace(tmp, dest)
            return attempt
        except PermissionError as exc:
            print(f"  os.replace attempt {attempt} failed ({exc.__class__.__name__}); retry in {wait}s", flush=True)
            time.sleep(wait)
    raise SystemExit(f"os.replace kept failing; {dest.name} NOT written (tmp left in place: {tmp})")
