# -*- coding: utf-8 -*-
"""Ingest FSC data.go.kr bond issuance and call/early-exercise data for Korean insurers.

Usage:
    python scripts/ingest_fsc_bonds.py --smoke
    python scripts/ingest_fsc_bonds.py --full
    python scripts/ingest_fsc_bonds.py --full --max-pages 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.bonds.config import settings  # noqa: E402
from src.bonds.fsc_client import ENDPOINTS, FscBondClient, FscBondError  # noqa: E402
from src.bonds.universe import InsurerRef, load_insurer_refs, match_insurer_code  # noqa: E402


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _dedupe_rows(rows: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for row in rows:
        key = tuple(row.get(f) for f in key_fields)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _attach_meta(rows: list[dict], refs: list[InsurerRef], query_name: str | None = None) -> list[dict]:
    enriched: list[dict] = []
    for row in rows:
        item = dict(row)
        isur = str(item.get("bondIsurNm") or "")
        item["_insurer_code"] = match_insurer_code(isur, refs)
        if query_name:
            item["_query_bondIsurNm"] = query_name
        enriched.append(item)
    return enriched


def run_smoke(client: FscBondClient) -> int:
    print("=== FSC bond API smoke test ===")
    required_ok = True
    for name, page in client.smoke_test().items():
        meta = ENDPOINTS[name]
        if page.error:
            if name == "schedule" and page.http_status == 403:
                print(
                    f"[SKIP] {name} ({meta['data_id']}): HTTP 403 — "
                    "portal approval may still be propagating, or check serviceKey encoding / "
                    "data.go.kr 활용신청 status for 15059611"
                )
                continue
            print(f"[FAIL] {name} ({meta['data_id']}): {page.error}")
            required_ok = False
            continue
        rc = page.result_code or "?"
        status = "OK" if rc == "00" else "FAIL"
        print(
            f"[{status}] {name} ({meta['data_id']}): resultCode={rc} "
            f"msg={page.result_msg!r} items={len(page.items)}"
        )
        if rc != "00" and name != "schedule":
            required_ok = False
    return 0 if required_ok else 1


def pull_for_insurers(
    client: FscBondClient,
    refs: list[InsurerRef],
    *,
    max_pages: int,
    rows_per_page: int,
) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {k: [] for k in ENDPOINTS}
    schedule_probe = client.fetch_page("schedule", page_no=1, num_of_rows=1)
    schedule_blocked = bool(schedule_probe.error and schedule_probe.http_status == 403)
    if schedule_blocked:
        print(
            "[WARN] schedule API HTTP 403 — approval propagation or key encoding; "
            "re-smoke after data.go.kr shows [승인] for 15059611"
        )
    for ref in refs:
        # Try ALL aliases (was: only ref.search_names[0]). FSC bondIsurNm matching is
        # exact-string at API side, so e.g. "KB손해보험" hits but "KB손해보험주식회사" misses;
        # likewise "삼성화재" vs "삼성화재해상보험". Loop and dedupe at end.
        for name in ref.search_names:
            for endpoint in ("issuance", "schedule"):
                if endpoint == "schedule" and schedule_blocked:
                    continue
                try:
                    rows = client.fetch_all_pages(
                        endpoint,
                        num_of_rows=rows_per_page,
                        max_pages=max_pages,
                        extra_params={"bondIsurNm": name},
                    )
                except FscBondError as exc:
                    print(f"[WARN] {ref.code} {endpoint} query={name!r}: {exc}")
                    continue
                if rows:
                    out[endpoint].extend(_attach_meta(rows, refs, query_name=name))
        # early_exercise bondIsurNm filter is slow/timeouts; paginated sample covers it.
    for endpoint in out:
        if endpoint == "issuance":
            out[endpoint] = _dedupe_rows(out[endpoint], ("isinCd", "basDt", "bondIssuDt"))
        elif endpoint == "early_exercise":
            out[endpoint] = _dedupe_rows(out[endpoint], ("isinCd", "basDt", "optnExertSttgDt"))
        else:
            out[endpoint] = _dedupe_rows(out[endpoint], ("isinCd", "basDt"))
    return out


def pull_paginated_sample(
    client: FscBondClient,
    refs: list[InsurerRef],
    *,
    pages: int,
    rows_per_page: int,
) -> dict[str, list[dict]]:
    sample: dict[str, list[dict]] = {}
    for endpoint in ("issuance", "early_exercise"):
        rows: list[dict] = []
        for page_no in range(1, pages + 1):
            page = client.fetch_page(endpoint, page_no=page_no, num_of_rows=rows_per_page)
            if page.error:
                raise FscBondError(f"{endpoint} page {page_no}: {page.error}")
            if page.result_code != "00":
                raise FscBondError(f"{endpoint} page {page_no}: {page.result_code}")
            rows.extend(_attach_meta(page.items, refs))
        sample[endpoint] = rows
    return sample


def filter_insurer_hits(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("_insurer_code")]


def summarize_hits(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        code = row.get("_insurer_code")
        if code:
            counts[str(code)] += 1
    return dict(sorted(counts.items()))


def write_outputs(payload: dict, out_dir: Path) -> list[Path]:
    written: list[Path] = []
    for name, rows in payload.items():
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(path)
    summary = {
        "generated_at": _stamp(),
        "row_counts": {k: len(v) for k, v in payload.items()},
        "insurer_hits": {k: summarize_hits(v) for k, v in payload.items()},
    }
    summary_path = out_dir / "manifest.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(summary_path)
    return written


def run_full(client: FscBondClient, *, max_pages: int, sample_pages: int) -> int:
    settings.ensure_dirs()
    refs = load_insurer_refs(settings.repo_root)
    stamp = _stamp()
    out_dir = settings.data_dir / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pulling per-insurer bondIsurNm queries (max_pages={max_pages})...")
    by_insurer = pull_for_insurers(client, refs, max_pages=max_pages, rows_per_page=100)

    print(f"Pulling paginated sample (pages={sample_pages}) for issuance + early_exercise...")
    sample = pull_paginated_sample(client, refs, pages=sample_pages, rows_per_page=100)

    schedule_page = client.fetch_page("schedule", page_no=1, num_of_rows=10)
    schedule_rows: list[dict] = []
    if schedule_page.error:
        print(f"[WARN] schedule API unavailable: {schedule_page.error}")
    elif schedule_page.result_code == "00":
        schedule_rows = _attach_meta(schedule_page.items, refs)
    else:
        print(
            f"[WARN] schedule API resultCode={schedule_page.result_code} "
            f"msg={schedule_page.result_msg!r}"
        )

    payload = {
        "issuance_by_insurer": by_insurer["issuance"],
        "early_exercise_by_insurer": by_insurer["early_exercise"],
        "schedule_by_insurer": by_insurer["schedule"] or schedule_rows,
        "issuance_sample_pages": sample["issuance"],
        "early_exercise_sample_pages": sample["early_exercise"],
    }

    paths = write_outputs(payload, out_dir)
    print("\n=== ingest summary ===")
    for key, rows in payload.items():
        hits = summarize_hits(rows)
        print(f"{key}: rows={len(rows)} insurer_hits={hits}")
    print(f"Output dir: {out_dir}")
    for p in paths:
        print(f"  {p.name}: {p.stat().st_size} bytes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="FSC data.go.kr bond ingest")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true", help="1-row smoke test for all 3 APIs")
    mode.add_argument("--full", action="store_true", help="Pull insurer-filtered + paginated sample")
    parser.add_argument("--max-pages", type=int, default=2, help="Max pages per insurer query (default 2)")
    parser.add_argument("--sample-pages", type=int, default=2, help="Unfiltered paginated pages (default 2)")
    args = parser.parse_args()

    settings.ensure_dirs()
    client = FscBondClient.from_settings()
    if args.smoke:
        return run_smoke(client)
    return run_full(client, max_pages=args.max_pages, sample_pages=args.sample_pages)


if __name__ == "__main__":
    raise SystemExit(main())
