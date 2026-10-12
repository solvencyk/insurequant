"""lib.py (parser-kics, ticket 20261012T1030Z) -- shared helpers for the cell-level plan / simulate / apply / proof scripts.
Nothing here writes the repo master; only apply_plan.py does (guarded, single writer).

Master format facts verified by round-trip (rt_check in apply_plan.py): kics_disclosure.json = JSON list of 9-key row dicts,
json.dumps(ensure_ascii=False, indent=2), CRLF line endings, trailing CRLF, no BOM.  Values are strings ('2043', '156.63') -- some
rows hold floats, which json.dumps reproduces unchanged.
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
EVID = REPO / "data" / "_derived" / "kics_followups_20261012"
PLANS = EVID / "plans"
BACKUP = EVID / "backup"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
ROW_KEYS = ["원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값", "값_적용후"]


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


def apply_to_rows(rows, plan):
    """In-place on `rows` (caller passes a deep copy when simulating). Edits first (guard: current == old), then inserts (guard:
    key absent; anchor row must exist).  Returns (n_edit_cells, n_inserted_rows)."""
    idx = index_rows(rows)
    ne = 0
    for e in plan["edits"]:
        k = (e["code"], e["q"], e["item"])
        if k not in idx:
            raise RuntimeError(f"edit target row missing: {k}")
        r = rows[idx[k]]
        cur = r.get(e["field"], "<nokey>")
        if cur != e["old"]:
            raise RuntimeError(f"GUARD FAIL {k} {e['field']}: current {cur!r} != expected old {e['old']!r}")
        r[e["field"]] = e["new"]
        ne += 1
    ni = 0
    for ins in plan["inserts"]:
        row = ins["row"]
        k = key(row)
        idx = index_rows(rows)
        if k in idx:
            raise RuntimeError(f"insert target already exists: {k}")
        anchor = tuple(ins["after"])
        if anchor not in idx:
            raise RuntimeError(f"insert anchor missing: {anchor}")
        rows.insert(idx[anchor] + 1, {kk: row[kk] for kk in ROW_KEYS if kk in row})
        ni += 1
    return ne, ni


def load_plan(name):
    return read_json(PLANS / f"{name}.json")


def merge_plans(names):
    plans = [load_plan(n) for n in names]
    seen = {}
    for p in plans:
        for e in p["edits"]:
            k = (e["code"], e["q"], e["item"], e["field"])
            if k in seen:
                raise RuntimeError(f"cell edited by two plans: {k}")
            seen[k] = p["name"]
    return {
        "name": "+".join(p["name"] for p in plans),
        "edits": [e for p in plans for e in p["edits"]],
        "inserts": [i for p in plans for i in p["inserts"]],
    }
