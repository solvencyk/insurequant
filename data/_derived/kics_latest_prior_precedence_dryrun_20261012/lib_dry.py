"""lib_dry.py (parser-kics, ticket 20261012T1900Z) -- shared helpers for the READ-ONLY latest-prior-column precedence dry run.

Nothing in this module writes the repo master, registries, goldens, xlsx or HTML.  Everything it writes stays under
data/_derived/kics_latest_prior_precedence_dryrun_20261012/ .
"""
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = REPO / "data" / "_derived" / "kics_latest_prior_precedence_dryrun_20261012"
TMP = OUT / "_tmp"                      # candidate masters / bulky scratch -- deleted at the end of the run
CACHE = OUT / "cache"                   # small JSON caches (core-table extraction per filing)
MASTER = REPO / "kics_disclosure.json"
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
DISC = REPO / "data" / "disclosure"
ROW_KEYS = ["원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값", "값_적용후"]

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))


_UTF8_WRAPPED = False


def utf8_stdout():
    """wrap stdout once (a second wrap would close the first wrapper's buffer when it is garbage collected)"""
    global _UTF8_WRAPPED
    if _UTF8_WRAPPED:
        return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    _UTF8_WRAPPED = True


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p) -> str:
    return sha_bytes(Path(p).read_bytes())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_lf(path, obj, indent=1):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, default=str)
        f.write("\n")


def read_rows(p=MASTER):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def dump_master_bytes(rows) -> bytes:
    """Same serialisation as the repo master (CRLF, indent 2, ensure_ascii False, trailing CRLF)."""
    s = json.dumps(rows, ensure_ascii=False, indent=2)
    return (s.replace("\n", "\r\n") + "\r\n").encode("utf-8")


QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]   # 2023.1Q .. 2026.2Q


def qidx(q: str) -> int:
    return (int(q[:4]) - 2023) * 4 + int(q[5]) - 1


def qadd(q: str, n: int):
    i = qidx(q) + n
    if i < 0 or i >= len(QUARTERS):
        return None
    return QUARTERS[i]


def period_of(q: str) -> str:
    return f"FY{q[:4]}_Q{q[5]}"


def quarter_of(period: str) -> str:
    m = re.match(r"FY(\d{4})_Q(\d)", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def is_even(q: str) -> bool:
    return int(q[5]) % 2 == 0


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def master_index(rows):
    """{(code, quarter): {item: (값, 값_적용후, row_index)}} plus {code: name}."""
    idx, names = {}, {}
    for i, r in enumerate(rows):
        it = r.get("항목번호")
        if not isinstance(it, int):
            continue
        idx.setdefault((r["원보험사코드"], r["공시분기"]), {})[it] = (r.get("값"), r.get("값_적용후"), i)
        names.setdefault(r["원보험사코드"], r.get("원수사명"))
    return idx, names
