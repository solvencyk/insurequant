import hashlib
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_pdf(period: str, code: str):
    for sub in ("pdf", "raw"):
        d = ROOT / "data" / "disclosure" / period / sub
        if not d.exists():
            continue
        for p in d.glob(f"{code}_*.pdf"):
            return p
    return None


codes = ["KR0011", "KR0029", "KR0150", "KR0009", "KR0032", "KR0051"]
for code in codes:
    q1 = find_pdf("FY2026_Q1", code)
    q2 = find_pdf("FY2026_Q2", code)
    print(f"=== {code} ===")
    print("Q1:", q1)
    print("Q2:", q2)
    if q1 and q2:
        s1 = sha256_of(q1)
        s2 = sha256_of(q2)
        sz1 = q1.stat().st_size
        sz2 = q2.stat().st_size
        print(f"Q1 sha256={s1} size={sz1}")
        print(f"Q2 sha256={s2} size={sz2}")
        print("*** IDENTICAL (stale duplicate) ***" if s1 == s2 else "different content")
    print()
