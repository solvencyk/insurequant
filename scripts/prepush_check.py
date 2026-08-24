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

    # 1b) K-ICS 룰 게이트 (owner 2026-08-21 2차). `CLAUDE.md` 의 "K-ICS validation gate (mandatory)"
    #     는 push 전에 이것을 돌리라고 **명시**하는데, 이 훅도 CI 도 그것을 부르지 않았다. 실제로
    #     `validate_data_contract.py` L305 에 "(prepush_check.py 는 validate_kics_disclosure.py 를
    #     호출하지 않는다) 여기서 같이 건다" 라는 주석과 함께 **룰 하나만 베껴 놓은 흔적**이 있다 —
    #     빠진 게이트를 눈치챌 때마다 룰을 한 개씩 옮겨 심는 것은 배선이 아니다. 5.9초짜리를
    #     안 돌려서 생긴 구멍이다. exit 2 = 룰엔진 blocking RED · census RED · 동어반복
    #     (IDENTITY_TAUTOLOGY) · 미평가축 · 근거 없는 면제 중 하나 이상.
    print("\n" + "=" * 72)
    print("K-ICS RULE GATE (CLAUDE.md 'mandatory' — scripts/validate_kics_disclosure.py)")
    import subprocess                              # noqa: E402
    kp = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_kics_disclosure.py")],
                        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
    klines = [ln for ln in (kp.stdout or "").splitlines() if ln.strip()]
    keep = [ln for ln in klines
            if any(t in ln for t in ("Status counts:", "blocking RED", "Coverage census:",
                                     "RED failures by rule", "(blocking)", "documented exception"))]
    print("\n".join(keep[:14]) or (kp.stderr or "")[-600:])
    n_kics = kp.returncode
    print(f"  → K-ICS gate exit={n_kics} ({'BLOCK' if n_kics else 'clear'})")

    # 1c) 나머지 도메인 게이트 (owner 2026-08-21 2차). `scripts/validate_*.py` 8개 중 훅이 부르던
    #     것은 data-contract 하나뿐이었다. 1b 로 K-ICS 룰게이트를 넣으면서 전수 확인했더니
    #     **통과하고 있으면서 아무도 안 부르는 게이트가 3개** 더 있었다(각 2~3초). 통과하는
    #     게이트를 안 부르는 것은 공짜로 검증을 버리는 것이다 — 지금 넣는다.
    #     어떤 게이트가 배선됐고 어떤 게 왜 빠졌는지는 `tests/test_push_gate_wiring.py` 가
    #     매니페스트로 강제한다(새 validate_* 를 추가하면 거기서 막힌다).
    #     **이 세 스크립트는 자기 산출 JSON 을 덮어쓴다**(`built_at` 타임스탬프만 바뀌어도
    #     diff 가 난다). 게이트는 **검사만 하고 트리를 바꾸지 않는다**는 계약이라, 실행 전
    #     바이트를 떠 두고 끝나면 되돌린다 — 안 그러면 push 할 때마다 워킹트리가 더러워지고
    #     다음 세션이 "이 diff 는 뭐지"로 시간을 쓴다(2026-08-21 실측).
    print("\n" + "=" * 72)
    print("DOMAIN GATES (csm_continuity · kics_rate_sensitivity · nb_csm_multiple · csm_waterfall)")
    _dom_outputs = [ROOT / "data" / "dart" / "viz" / "csm_waterfall_validation.json",
                    ROOT / "data" / "dart" / "viz" / "csm_continuity_validation.json",
                    ROOT / "data" / "_derived" / "kics_rate_sensitivity_validation.json",
                    ROOT / "data" / "_derived" / "nb_csm_validation.json"]
    _before = {f: f.read_bytes() for f in _dom_outputs if f.exists()}
    n_dom = 0
    for _name in ("validate_csm_continuity", "validate_kics_rate_sensitivity",
                  "validate_nb_csm_multiple", "validate_csm_waterfall"):
        # 자식 스크립트 일부가 stdout 을 utf-8 로 reconfigure 하지 않아 한글이 깨진 채 올라온다
        # (`validate_nb_csm_multiple` 실측). 훅이 그 출력을 사람에게 보여주므로 여기서 강제한다.
        _p = subprocess.run([sys.executable, str(ROOT / "scripts" / (_name + ".py"))],
                            cwd=str(ROOT), capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        _tail = [ln for ln in (_p.stdout or "").splitlines() if ln.strip()][-2:]
        print(f"  {_name}: exit={_p.returncode}")
        for _ln in _tail:
            print("      " + _ln)
        n_dom |= _p.returncode
    for _f, _bytes in _before.items():          # 검사만 하고 트리는 원래대로
        if _f.read_bytes() != _bytes:
            _f.write_bytes(_bytes)

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
    fast = ["tests/test_kics_rules_golden.py", "tests/test_master_tables_golden.py",
            "tests/test_post_transition_golden.py", "tests/test_deploy_assets.py",
            "tests/test_rule_coverage_manifest.py",
            # 동어반복 탐지기는 **자기 자신이 동어반복이 되기 가장 쉬운 룰**이라(임계를 조금만
            # 올리면 영원히 0건) 변이시험이 매 push 마다 돌아야 한다. 여기 안 넣으면 "게이트에
            # 배선했다"가 또 honor-system 이 된다 — 이 훅이 생긴 이유 그 자체. <1초.
            "tests/test_identity_tautology.py",
            # 게이트가 훅에 실제로 걸려 있는지를 검사하는 매니페스트. 이게 없으면 "새 게이트를
            # 만들고 훅에 안 거는" 사고가 조용히 반복된다(2026-08-21 에 5개가 호출처 0 이었다).
            "tests/test_push_gate_wiring.py",
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
    blocked = n_red or n_hyg or n_test or n_kics or n_dom
    print(f"PRE-PUSH VERDICT: gate RED={n_red} · K-ICS rule gate={'BLOCK' if n_kics else 'clear'}"
          f" · domain gates={'FAIL' if n_dom else 'pass'}"
          f" · inbox 기계적위반={'있음' if n_hyg else '0'}"
          f" · offline tests={'FAIL' if n_test else 'pass'}"
          f" → {'BLOCKED (fix or owner-escalate)' if blocked else 'gate-clear'}"
          f"  |  anomaly review queue={len(skeptic_input)}")
    print("#" * 72)
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
