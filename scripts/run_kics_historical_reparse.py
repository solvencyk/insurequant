"""Batch K-ICS historical quarter re-parse + fill scripts.

Logs per-period output under artifacts/kics_reparse_<period>.log and a
running summary at artifacts/kics_reparse_master.log.

Usage:
    .venv\\Scripts\\python.exe scripts/run_kics_historical_reparse.py
    .venv\\Scripts\\python.exe scripts/run_kics_historical_reparse.py --start-period FY2023_Q2
    .venv\\Scripts\\python.exe scripts/run_kics_historical_reparse.py --reverse --skip-done
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
HARNESS = REPO / "scripts" / "run_harness.py"
FILL_PERIOD = REPO / "scripts" / "fill_period_to_disclosure.py"
FILL_SUB = REPO / "scripts" / "fill_subitems_to_disclosure.py"
FILL_POST = REPO / "scripts" / "fill_post_transition_to_disclosure.py"
RECALC_RATIO = REPO / "scripts" / "recalc_basic_capital_ratio_post.py"
ARTIFACTS = REPO / "artifacts"
MASTER = ARTIFACTS / "kics_reparse_master.log"

ALL_PERIODS = [
    "FY2023_Q1",
    "FY2023_Q2",
    "FY2023_Q3",
    "FY2023_Q4",
    "FY2024_Q1",
    "FY2024_Q2",
    "FY2024_Q3",
    "FY2024_Q4",
    "FY2025_Q1",
    "FY2025_Q2",
    "FY2025_Q3",
    "FY2025_Q4",
]

REVERSE_DEFAULT_START = "FY2025_Q3"
FORWARD_DEFAULT_START = "FY2023_Q2"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_master(line: str) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with MASTER.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")


def _done_periods_from_master() -> set[str]:
    """Periods with PERIOD_DONE in master log (parse+fill attempted)."""
    if not MASTER.is_file():
        return set()
    done: set[str] = set()
    for line in MASTER.read_text(encoding="utf-8").splitlines():
        m = re.match(r"PERIOD_DONE (\S+)", line)
        if m:
            done.add(m.group(1))
    return done


def _parse_summary_from_log(log_path: Path) -> dict[str, str]:
    """Extract harness parse + fill stats from period log tail."""
    if not log_path.is_file():
        return {}
    text = log_path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}

    m = re.search(r"inputs=(\d+)\s+ok=(\d+)\s+skip=(\d+)\s+fail=(\d+)", text)
    if m:
        out["parse"] = f"{m.group(2)}/{m.group(1)} ok, {m.group(4)} fail"

    m = re.search(r"new rows queued:\s+(\d+)", text)
    if m:
        out["fill_subitems"] = f"+{m.group(1)} rows"

    m = re.search(r"값_적용후.*?(\d+)\s+rows", text)
    if not m:
        m = re.search(r"applied.*?(\d+)", text, re.I)
    if m:
        out["fill_post"] = m.group(1)

    return out


def _run(cmd: list[str], log_path: Path) -> tuple[int, float]:
    t0 = time.perf_counter()
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n=== {' '.join(cmd)} @ {_now()} ===\n")
        fh.flush()
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            stdout=fh,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    elapsed = time.perf_counter() - t0
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"EXIT_CODE={proc.returncode} ELAPSED_S={elapsed:.1f}\n")
    return proc.returncode, elapsed


def _resolve_periods(args: argparse.Namespace) -> list[str]:
    if args.reverse:
        start = args.start_period or REVERSE_DEFAULT_START
        end = args.end_period or "FY2023_Q1"
        try:
            si = ALL_PERIODS.index(start)
            ei = ALL_PERIODS.index(end)
        except ValueError as exc:
            raise SystemExit(f"unknown period in range: {exc}") from exc
        if si < ei:
            raise SystemExit(
                f"reverse range invalid: {start} must be >= {end} chronologically"
            )
        periods = list(reversed(ALL_PERIODS[ei : si + 1]))
    else:
        start = args.start_period or FORWARD_DEFAULT_START
        try:
            start_idx = ALL_PERIODS.index(start)
        except ValueError:
            raise SystemExit(f"unknown period: {start}") from None
        end_idx = len(ALL_PERIODS)
        if args.end_period:
            try:
                end_idx = ALL_PERIODS.index(args.end_period) + 1
            except ValueError:
                raise SystemExit(f"unknown period: {args.end_period}") from None
        periods = ALL_PERIODS[start_idx:end_idx]

    if args.skip_done:
        done = _done_periods_from_master()
        skipped = [p for p in periods if p in done]
        periods = [p for p in periods if p not in done]
        if skipped:
            _append_master(
                f"BATCH_SKIP {_now()} skipped_done={','.join(skipped)}"
            )

    return periods


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start-period",
        default=None,
        help=(
            "first period to process "
            f"(default forward: {FORWARD_DEFAULT_START}; "
            f"reverse: {REVERSE_DEFAULT_START})"
        ),
    )
    parser.add_argument(
        "--end-period",
        default=None,
        help="last period inclusive (reverse: FY2023_Q1; forward: FY2025_Q4)",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="process newest-to-oldest (FY2025_Q3 down to FY2023_Q1 by default)",
    )
    parser.add_argument(
        "--skip-done",
        action="store_true",
        help="skip periods already marked PERIOD_DONE in kics_reparse_master.log",
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--max-hit-pages", type=int, default=16)
    args = parser.parse_args(argv)

    if not PYTHON.is_file():
        print(f"venv python not found: {PYTHON}", file=sys.stderr)
        return 2

    periods = _resolve_periods(args)
    if not periods:
        print("no periods to process (all skipped or empty range)")
        _append_master(f"BATCH_END {_now()} failures=none note=empty_queue")
        return 0

    direction = "reverse" if args.reverse else "forward"
    _append_master(
        f"BATCH_START {_now()} direction={direction} periods={','.join(periods)}"
    )

    failures: list[str] = []
    for period in periods:
        log_path = ARTIFACTS / f"kics_reparse_{period}.log"
        log_path.write_text(f"PERIOD={period} START={_now()}\n", encoding="utf-8")
        _append_master(f"PERIOD_START {period} {_now()}")

        parse_cmd = [
            str(PYTHON),
            str(HARNESS),
            "--stage",
            "parse",
            "--period",
            period,
            "--workers",
            str(args.workers),
            "--max-hit-pages",
            str(args.max_hit_pages),
        ]
        rc, elapsed = _run(parse_cmd, log_path)
        status = "ok" if rc == 0 else "parse_fail"
        if rc != 0:
            failures.append(f"{period}:parse")

        fill_period_cmd = [
            str(PYTHON),
            str(FILL_PERIOD),
            "--period",
            period,
            "--refresh",
        ]
        fprc, _ = _run(fill_period_cmd, log_path)
        if fprc != 0:
            failures.append(f"{period}:fill_period")
            status = "fill_fail" if status == "ok" else status

        for label, script in (("fill_subitems", FILL_SUB), ("fill_post", FILL_POST)):
            fill_cmd = [str(PYTHON), str(script), "--period", period]
            frc, _felapsed = _run(fill_cmd, log_path)
            if frc != 0:
                failures.append(f"{period}:{label}")
                status = "fill_fail" if status == "ok" else status

        recalc_cmd = [str(PYTHON), str(RECALC_RATIO)]
        rrc, _ = _run(recalc_cmd, log_path)
        if rrc != 0:
            failures.append(f"{period}:recalc_ratio")

        md_count = len(list((REPO / "md_inbox" / period).glob("*.md")))
        stats = _parse_summary_from_log(log_path)
        stats_str = " ".join(f"{k}={v}" for k, v in stats.items()) if stats else ""
        _append_master(
            f"PERIOD_DONE {period} status={status} md_inbox={md_count} "
            f"parse_s={elapsed:.0f} {stats_str} {_now()}"
        )

    _append_master(f"BATCH_END {_now()} failures={failures or 'none'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
