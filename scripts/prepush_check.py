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
import os
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

    # 3) inbox 위생 (owner 2026-08-21). 생명주기 계약(inbox/README.md §64-71)은 문서로만 있고
    #    검사하는 것이 없어서 지켜지지 않았다 — 끝난 스레드가 활성 폴더에 남아 매 세션 다시 읽히고,
    #    status 에 스키마 밖 값('done')이 들어가고, sender 가 answered 를 재확인하지 않은 채 46일이
    #    지났다. 스키마·폴더 불일치만 push 를 막는다(항상 기계적으로 고칠 수 있다). 방치 스레드는
    #    보고만 — 진행 중인 스레드 하나가 배포를 막으면 안 된다.
    print("\n" + "=" * 72)
    print("INBOX HYGIENE (inbox/README.md §64-71)")
    import check_inbox_hygiene as hyg           # noqa: E402
    n_hyg = hyg.main(["--mechanical-only"])

    # 4) 오프라인 테스트 묶음 (owner 2026-08-21). 골든과 룰-커버리지 매니페스트가 여기 있는데
    #    **pytest 를 자동으로 돌리는 것이 아무것도 없었다** — 게이트를 훅에 걸어놓고 정작 테스트는
    #    또 honor-system 으로 남기면 같은 실수의 반복이다. 느린 것(ifrs17_bs ~2분,
    #    pl_breakdown ~95초 opt-in)은 뺀다. 이 묶음 ~19초.
    print("\n" + "=" * 72)
    print("OFFLINE TESTS (goldens + 룰 커버리지 매니페스트)")
    import subprocess                              # noqa: E402
    fast = ["tests/test_kics_rules_golden.py", "tests/test_master_tables_golden.py",
            "tests/test_post_transition_golden.py", "tests/test_deploy_assets.py",
            "tests/test_rule_coverage_manifest.py",
            # 동어반복 탐지기는 **자기 자신이 동어반복이 되기 가장 쉬운 룰**이라(임계를 조금만
            # 올리면 영원히 0건) 변이시험이 매 push 마다 돌아야 한다. 여기 안 넣으면 "게이트에
            # 배선했다"가 또 honor-system 이 된다 — 이 훅이 생긴 이유 그 자체. <1초.
            "tests/test_identity_tautology.py",
            "tests/unit/"]
    # 커버리지 매니페스트는 훅에서만 **전수(48칸 × 게이트 1회)** 로 돌린다. 로컬 pytest 기본값은
    # 선언된 사각만 셀 단위 + 나머지 묶음(42초)인데, 묶음은 "44칸이 통째로 죽는 것"만 잡고
    # **한 칸이 조용히 사각이 되는 것**은 못 잡는다 — 그게 이 테스트의 존재 이유다.
    # 대가: 이 묶음이 ~40초에서 ~4분으로 늘어난다. push 는 드물고 되돌리기 어려운 동작이라 감수한다.
    env = dict(os.environ, FULL_COVERAGE_SWEEP="1")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *fast],
                          cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", env=env)
    tail = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()][-6:]
    print("\n".join(tail) or (proc.stderr or "")[-800:])
    n_test = proc.returncode

    print("\n" + "#" * 72)
    blocked = n_red or n_hyg or n_test
    print(f"PRE-PUSH VERDICT: gate RED={n_red} · inbox 기계적위반={'있음' if n_hyg else '0'}"
          f" · offline tests={'FAIL' if n_test else 'pass'}"
          f" → {'BLOCKED (fix or owner-escalate)' if blocked else 'gate-clear'}"
          f"  |  anomaly review queue={len(skeptic_input)}")
    print("#" * 72)
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
