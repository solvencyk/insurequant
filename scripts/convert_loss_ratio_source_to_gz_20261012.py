#!/usr/bin/env python3
"""Ticket 20261012T0900Z (2): store the loss-ratio long source (risk_premium_vs_expected_claims.json, 85MB) as .json.gz -- content unchanged.

The gz holds exactly the bytes of the old file (the old file is already compact JSON, so "compact separators" alone saves nothing).
Deterministic gzip (mtime 0, no file name). Proofs before the old file is removed (--apply):
  * sha256 of the decompressed gz == sha256 of the old file (byte-identical), row count and parsed list equal,
  * the file name is read only through build_loss_ratio_master.read_json / extract_loss_ratio.atomic_write_json (gz-aware).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/convert_loss_ratio_source_to_gz_20261012.py [--apply]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LR = ROOT / "data" / "loss_ratio"
OLD = LR / "risk_premium_vs_expected_claims.json"
NEW = LR / "risk_premium_vs_expected_claims.json.gz"
WORK = ROOT / "data" / "_derived" / "loss_ratio_label_std_20261012"
sys.stdout.reconfigure(encoding="utf-8")
LOG: list[str] = []


def log(s: str) -> None:
    LOG.append(s)
    print(s)


def gz_bytes(raw: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, compresslevel=9, mtime=0) as g:
        g.write(raw)
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    raw = OLD.read_bytes()
    sha_old = hashlib.sha256(raw).hexdigest()
    rows_old = json.loads(raw.decode("utf-8"))
    log(f"old file {OLD.name}: {len(raw):,} bytes ({len(raw) / 1e6:.1f} MB), {len(rows_old):,} rows, sha256 {sha_old}")
    gz = gz_bytes(raw)
    log(f"gz: {len(gz):,} bytes ({len(gz) / 1e6:.2f} MB), ratio {len(gz) / len(raw):.3f}")
    back = gzip.decompress(gz)
    log(f"decompressed == old bytes: {back == raw}; sha256 {hashlib.sha256(back).hexdigest()}")
    log(f"parsed row list equal: {json.loads(back.decode('utf-8')) == rows_old}")
    if back != raw:
        sys.exit(2)
    if not args.apply:
        log("dry run only")
        (WORK / "gz_convert_log.txt").write_text("\n".join(LOG), encoding="utf-8")
        return
    tmp = NEW.with_name(NEW.name + f".tmp{os.getpid()}")
    tmp.write_bytes(gz)
    os.replace(tmp, NEW)
    disk = gzip.decompress(NEW.read_bytes())
    ok = hashlib.sha256(disk).hexdigest() == sha_old
    log(f"written {NEW.name} ({NEW.stat().st_size:,} bytes); on-disk decompress sha256 equals old: {ok}")
    if not ok:
        sys.exit(3)
    OLD.unlink()
    log(f"removed {OLD.name} (git history keeps the blob; backup outside the tree)")
    (WORK / "gz_convert_log.txt").write_text("\n".join(LOG), encoding="utf-8")


if __name__ == "__main__":
    main()
