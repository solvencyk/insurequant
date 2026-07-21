"""Resolve each insurer's stock ticker from OpenDART (corpCode.xml) and patch the
티커 field across all root master tables. Unlisted (no DART stock_code) -> 'X'.

DART's stock_code is the source of truth (per owner instruction). Resolved live at
runtime — no permanent KR<->corp mapping file is written. Re-run after any master
rebuild to re-apply. Idempotent.

Usage: PYTHONIOENCODING=utf-8 python scripts/update_tickers_from_dart.py [--dry-run]
"""
from __future__ import annotations
import argparse, io, json, re, sys, zipfile, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MASTERS = ["kics_disclosure.json", "kics_rate_sensitivity.json", "CSM_waterfall.json",
           "CSM_amortization.json", "NB_CSM_multiple.json", "PL_breakdown.json"]


def norm(s):
    return re.sub(r"\s+", "", s or "")


def read_key():
    for ln in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        if ln.strip().startswith("OPENDART_API_KEY"):
            return ln.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("OPENDART_API_KEY not in .env")


def fetch_corps(key):
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={key}"
    data = urllib.request.urlopen(url, timeout=120).read()
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(data)).read(
        zipfile.ZipFile(io.BytesIO(data)).namelist()[0]))
    idx = {}
    for el in root.iter("list"):
        nm = norm(el.findtext("corp_name"))
        sc = (el.findtext("stock_code") or "").strip()
        idx.setdefault(nm, []).append(sc)
    return idx


# conservative suffix strips: 삼성생명보험->삼성생명, 미래에셋생명보험->미래에셋생명,
# 코리안리재보험->코리안리. NOT 생명보험/해상보험 (those leave a 2-char stem like
# 흥국/DB that false-matches unrelated listed corps).
SUFFIXES = ["", "보험", "재보험"]


def resolve(name, idx):
    n = norm(name)
    cands = [n]
    for suf in SUFFIXES[1:]:
        s = norm(suf)
        if n.endswith(s) and len(n) > len(s):
            cands.append(n[:-len(s)])
    matched = False
    for c in cands:
        if c in idx:
            matched = True
            for sc in idx[c]:
                if sc:
                    return sc.zfill(6), True  # listed -> 6-digit code
    return "X", matched  # exact corp found but unlisted, or no corp match -> X


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    # union of (code -> name) across masters
    code2name = {}
    for fn in MASTERS:
        for r in json.loads((REPO / fn).read_text(encoding="utf-8")):
            code2name.setdefault(r["원보험사코드"], r["원수사명"])

    idx = fetch_corps(read_key())
    print(f"DART corps indexed: {len(idx)} unique names\n")

    ticker, report = {}, []
    for code, name in sorted(code2name.items(), key=lambda kv: str(kv[0])):
        if code is None:
            continue
        tk, matched = resolve(name, idx)
        ticker[code] = tk
        report.append((code, name, tk, "" if matched or tk != "X" else "(no DART corp match)"))

    listed = sum(1 for _c, _n, t, _w in report if t != "X")
    print(f"resolved: {listed} listed / {len(report) - listed} unlisted(X)")
    for code, name, tk, warn in report:
        print(f"  {code} {name:22s} -> {tk}  {warn}")

    if args.dry_run:
        print("\n(dry-run; masters unchanged)")
        return 0

    for fn in MASTERS:
        rows = json.loads((REPO / fn).read_text(encoding="utf-8"))
        ch = 0
        for r in rows:
            new = ticker.get(r["원보험사코드"])
            if new is not None and r.get("티커") != new:
                r["티커"] = new; ch += 1
        (REPO / fn).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  patched {fn}: {ch} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
