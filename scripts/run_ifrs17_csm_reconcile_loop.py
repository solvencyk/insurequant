#!/usr/bin/env python3
"""Re-parse / rebuild loop until CSM waterfall (incl. mandatory NB CSM) validates.

Gate order (hard blockers first):
  1. new_business CSM present + non-zero for every IFRS17 entity in scope
  2. rollforward identity (opening + … ≈ closing)
  3. (optional) NB CSM multiple vs IR

Each iteration:
  1. Re-extract measurement tables from cached DART XML
  2. Rebuild csm_waterfall.json
  3. validate_csm_waterfall.py — exit 1 triggers another iteration
  4. validate_nb_csm_multiple.py (unless --waterfall-only)
  5. Refresh bubble / KPI JSON

While new_business_failed > 0 the loop never stops early — keeps re-parsing
until data appears or --max-iter exhausted.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
LOG_PATH = ARTIFACTS / "ifrs17_csm_reconcile_loop.log"
WF_VAL_PATH = ROOT / "data" / "dart" / "viz" / "csm_waterfall_validation.json"
NB_VAL_PATH = ROOT / "data" / "_derived" / "nb_csm_validation.json"

SCRIPTS = {
    "measurement": ROOT / "scripts" / "ifrs17_batch_measurement.py",
    "waterfall": ROOT / "scripts" / "viz_build_csm_waterfall.py",
    "wf_validate": ROOT / "scripts" / "validate_csm_waterfall.py",
    "nb_validate": ROOT / "scripts" / "validate_nb_csm_multiple.py",
    "bubble": ROOT / "scripts" / "viz_build_csm_bubble.py",
    "kpis": ROOT / "scripts" / "viz_build_ifrs17_kpis.py",
    "premium_crawl": ROOT / "scripts" / "crawl_assoc_nb_premium.py",
}


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}"
    print(line)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def run_step(name: str, path: Path, extra: list[str] | None = None) -> int:
    cmd = [PY, str(path)] + (extra or [])
    log(f"RUN {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    log(f"EXIT {name} code={proc.returncode}")
    return proc.returncode


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validation_state() -> dict:
    wf: dict = load_json(WF_VAL_PATH) if WF_VAL_PATH.is_file() else {}
    nb: dict = load_json(NB_VAL_PATH) if NB_VAL_PATH.is_file() else {}
    wf_meta = wf.get("_meta") or {}
    nb_meta = nb.get("_meta") or {}
    nb_failed = wf.get("new_business_failed") or [
        r for r in wf.get("results") or [] if not r.get("new_business_ok")
    ]
    return {
        "wf_fail": len(wf.get("failed") or []),
        "nb_csm_fail": len(nb_failed),
        "nb_csm_companies": [r.get("company") for r in nb_failed if r.get("company")],
        "wf_fail_companies": [r.get("company") for r in wf.get("failed") or [] if r.get("company")],
        "nb_mult_fail": nb_meta.get("cohort_fail", 0),
        "needs_reparse_nb": bool(wf_meta.get("needs_reparse_for_new_business")),
        "wf_pass": wf_meta.get("companies_fail", 1) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="IFRS17 CSM waterfall + NB CSM reconcile loop")
    parser.add_argument("--max-iter", type=int, default=5, help="max iterations (default 5; docs/agents/claude-agent-validation.md §3)")
    parser.add_argument(
        "--skip-measurement",
        action="store_true",
        help="skip DART re-extract (waterfall rebuild only)",
    )
    parser.add_argument(
        "--waterfall-only",
        action="store_true",
        help="stop when waterfall/NB CSM gate passes; ignore IR multiple validation",
    )
    parser.add_argument("--refresh-premium", action="store_true", help="re-crawl premium each iter")
    args = parser.parse_args()

    log("=== IFRS17 CSM reconcile loop start ===")
    log("Hard gate: new_business CSM mandatory for all IFRS17 entities in scope")
    prev = None

    for iteration in range(1, args.max_iter + 1):
        log(f"--- iteration {iteration}/{args.max_iter} ---")

        if args.refresh_premium and SCRIPTS["premium_crawl"].is_file():
            run_step("premium_crawl", SCRIPTS["premium_crawl"])

        state_before = validation_state()
        if not args.skip_measurement and SCRIPTS["measurement"].is_file():
            if state_before["needs_reparse_nb"] or iteration == 1:
                run_step("measurement", SCRIPTS["measurement"])
            else:
                log("SKIP measurement (no NB reparse needed)")

        run_step("waterfall", SCRIPTS["waterfall"])
        rc_wf = run_step("wf_validate", SCRIPTS["wf_validate"])

        rc_nb = 0
        if not args.waterfall_only and SCRIPTS["nb_validate"].is_file():
            rc_nb = run_step("nb_validate", SCRIPTS["nb_validate"])

        if SCRIPTS["kpis"].is_file():
            run_step("kpis", SCRIPTS["kpis"])
        if SCRIPTS["bubble"].is_file():
            run_step("bubble", SCRIPTS["bubble"])

        st = validation_state()
        log(
            f"wf_fail={st['wf_fail']} nb_csm_fail={st['nb_csm_fail']} "
            f"nb_mult_fail={st['nb_mult_fail']}"
        )
        if st["nb_csm_companies"]:
            log(f"  NB CSM missing/zero: {', '.join(st['nb_csm_companies'])}")
        if st["wf_fail_companies"] and not st["nb_csm_companies"]:
            log(f"  waterfall fails: {', '.join(st['wf_fail_companies'])}")

        wf_ok = rc_wf == 0 and st["nb_csm_fail"] == 0
        all_ok = wf_ok and (args.waterfall_only or rc_nb == 0)

        if all_ok:
            log("=== ALL PASS ===")
            return 0

        if wf_ok and args.waterfall_only:
            log("=== WATERFALL + NB CSM GATE PASS (--waterfall-only) ===")
            return 0

        # Never stop early while 신계약 CSM still missing — user rule.
        if st["needs_reparse_nb"]:
            log("NB CSM gate open → continue reparse loop")
            prev = (st["wf_fail"], st["nb_csm_fail"], st["nb_mult_fail"])
            continue

        snap = (st["wf_fail"], st["nb_csm_fail"], st["nb_mult_fail"])
        if prev is not None and snap == prev and iteration > 1:
            log("no improvement vs previous iteration; stopping")
            break
        prev = snap

    log("=== LOOP ENDED WITH FAILURES ===")
    st = validation_state()
    if st["nb_csm_fail"]:
        log(f"BLOCKED: {st['nb_csm_fail']} companies still missing new_business CSM")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
