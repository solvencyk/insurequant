#!/usr/bin/env python3
"""PRE-PUSH check (owner 2026-06-19): the single gate publishing runs RIGHT BEFORE a push
(push-time only, not a daily cron). Chains:
  1. hard data-contract gate  (validate_data_contract) — exit 2 if any RED → push BLOCKED.
  2. generic-anomaly triage   (triage_anomaly_candidates) — writes the review queue.
Then it hands the triage residual (REAL + UNCERTAIN) to the publishing LLM-skeptic step
(see claude-agent-publishing §3): each is classified extraction/unit-error (→parser) vs real
economic event (→none) before the push is recommended.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import validate_data_contract as gate            # noqa: E402
import triage_anomaly_candidates as triage       # noqa: E402


def main() -> int:
    print("=" * 72)
    print("PRE-PUSH CHECK  (1: data-contract gate  +  2: anomaly triage → skeptic)")
    print("=" * 72)

    # 1) hard gate (blocks on RED)
    env = gate.Env()
    res = gate.run_gate(env)
    gate.print_report(res)
    n_red = len(res.red)

    # 2) discovery → precision triage  (owner-confirmed cells are suppressed, never reach skeptic)
    real, _noise, uncertain, _confirmed = triage.triage()
    out_dir = ROOT / "data" / "_derived"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "anomaly_triage.json").write_text(
        json.dumps({"real": real, "uncertain": uncertain, "noise_count": len(_noise),
                    "owner_confirmed": _confirmed}, ensure_ascii=False, indent=2), encoding="utf-8")
    skeptic_input = real + uncertain
    (out_dir / "anomaly_skeptic_input.json").write_text(
        json.dumps(skeptic_input, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"ANOMALY TRIAGE: REAL={len(real)} UNCERTAIN={len(uncertain)} "
          f"NOISE(auto-suppressed)={len(_noise)}")
    print(f"  → review queue: data/_derived/anomaly_triage.json")
    print(f"  → LLM-skeptic input ({len(skeptic_input)}): data/_derived/anomaly_skeptic_input.json")
    print("  NEXT (publishing §3): LLM-skeptic classifies each REAL/UNCERTAIN "
          "(extraction/unit-error→parser | real event→none) BEFORE recommending push.")

    print("\n" + "#" * 72)
    print(f"PRE-PUSH VERDICT: gate RED={n_red} → {'BLOCKED (fix or owner-escalate)' if n_red else 'gate-clear'}"
          f"  |  anomaly review queue={len(skeptic_input)}")
    print("#" * 72)
    return 2 if n_red else 0


if __name__ == "__main__":
    raise SystemExit(main())
