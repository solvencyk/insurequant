# -*- coding: utf-8 -*-
"""변이시험 — 라이브 아티팩트 배선 매트릭스에 이빨이 있는지 확인한다.

"테스트를 추가했다" 와 "그 테스트가 실제로 무언가를 막는다" 는 다른 말이다. 이 저장소가
반복해서 데인 자리라(honor-system 게이트 · 검사처럼 보이는 무검사), 새 매니페스트는
**변이를 넣으면 반드시 실패하는지**를 보여야 한다.

변이 4종:
  M1  선언 삭제       — LIVE_ARTIFACT_READERS 에서 NB_CSM_multiple.json 줄을 지운다
  M2  소스 되돌리기   — validate_master_tables.PL_PATH 를 중간산출물로 되돌린다
  M3  거짓 선언       — 읽지도 않는 검사기를 reader 로 선언한다
  M4  새 화면 파일    — HTML fetch 목록에 선언 없는 파일이 하나 늘어난 상황

각 변이마다 원본 바이트를 떠 두고 **반드시 되돌린다**(try/finally). 실패해야 할 테스트가
통과하면 그 테스트는 무검사다.

사용: python scripts/_probes/probe_20260825_mutate_wiring_matrix.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
TEST = "tests/test_push_gate_wiring.py"


def run(node: str) -> tuple[int, str]:
    p = subprocess.run([PY, "-m", "pytest", node, "-q", "--no-header", "-x"],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "")[-700:]


def mutate(path: Path, fn, node: str, label: str, expect_fail=True) -> bool:
    orig = path.read_bytes()
    try:
        src = orig.decode("utf-8")
        new = fn(src)
        assert new != src, f"{label}: 변이가 소스를 바꾸지 못했다(패턴 불일치)"
        path.write_bytes(new.encode("utf-8"))
        rc, out = run(node)
    finally:
        path.write_bytes(orig)
    ok = (rc != 0) if expect_fail else (rc == 0)
    verdict = "이빨 있음" if ok else "!! 무검사 !!"
    print(f"\n[{label}]  pytest exit={rc}  -> {verdict}")
    tail = [ln for ln in out.splitlines() if ln.strip()][-3:]
    for ln in tail:
        print("     " + ln)
    return ok


def main() -> int:
    tp = ROOT / "tests" / "test_push_gate_wiring.py"
    vmt = ROOT / "scripts" / "validate_master_tables.py"

    print("=" * 84)
    print("기준선 — 변이 없이 매트릭스 테스트가 통과하는가")
    print("=" * 84)
    rc, out = run(f"{TEST}")
    print(f"  exit={rc} ({'pass' if rc == 0 else 'FAIL'})")
    if rc != 0:
        print(out)
        return 1

    results = []

    # M1: 선언 삭제 -> 라이브가 fetch 하는데 선언 없음 -> FAIL 이어야 한다
    # (줄바꿈이 CRLF 라 리터럴 \n 매칭은 안 된다 — 줄 단위 정규식으로 지운다)
    results.append(mutate(
        tp,
        lambda s: re.sub(r'^[ \t]*"NB_CSM_multiple\.json":.*\r?\n', "", s,
                         count=1, flags=re.M),
        f"{TEST}::test_every_live_fetched_artifact_has_a_declared_reader",
        "M1 선언 삭제 (NB_CSM_multiple.json)"))

    # M2: 소스를 중간산출물로 되돌리기 -> 배포본/상류 짝 테스트가 FAIL 이어야 한다
    def m2(s):
        s = s.replace('PL_PATH = "PL_breakdown.json"',
                      'PL_PATH = "data/dart/viz/pl_breakdown_master.json"', 1)
        # 배포본 리터럴이 주석에 남아 있으면 소스검사를 통과해 버린다 -> 주석에서도 제거
        return re.sub(r"PL_breakdown\.json", "PL_breakdown_REDACTED.json", s)
    results.append(mutate(
        vmt, m2,
        f"{TEST}::test_gate_reads_the_deployed_artifact_not_the_upstream_copy",
        "M2 소스 되돌리기 (validate_master_tables PL_PATH -> 중간산출물)"))

    # M2b: 상수만 되돌리고 주석은 남긴 경우 — 실제 로드 줄 검출로 잡아야 한다
    results.append(mutate(
        vmt,
        lambda s: s.replace('PL_PATH = "PL_breakdown.json"',
                            'PL_PATH = "x"\nPL_PATH = json.loads((ROOT / '
                            '"data/dart/viz/pl_breakdown_master.json").read_text())', 1),
        f"{TEST}::test_gate_reads_the_deployed_artifact_not_the_upstream_copy",
        "M2b 상류를 직접 로드 (주석은 그대로 둔 채)"))

    # M3: 거짓 선언 — 읽지 않는 검사기를 reader 로 선언
    results.append(mutate(
        tp,
        lambda s: s.replace(
            '    "dividend.json": ["validate_data_contract"],',
            '    "dividend.json": ["validate_csm_continuity"],', 1),
        f"{TEST}::test_declared_reader_actually_references_the_artifact",
        "M3 거짓 선언 (dividend.json -> 읽지 않는 검사기)"))

    # M4: 화면에 새 파일이 붙은 상황 — 선언 없는 fetch 를 주입해 FAIL 을 확인
    results.append(mutate(
        tp,
        lambda s: re.sub(
            r"^([ \t]*)undeclared = sorted\(fetched - set\(LIVE_ARTIFACT_READERS\)\)",
            r'\1fetched = fetched | {"brand_new_panel.json"}   # [MUTATION]'
            "\n" r"\1undeclared = sorted(fetched - set(LIVE_ARTIFACT_READERS))",
            s, count=1, flags=re.M),
        f"{TEST}::test_every_live_fetched_artifact_has_a_declared_reader",
        "M4 화면에 새 파일이 붙음 (선언 없음)"))

    print("\n" + "=" * 84)
    ok = sum(results)
    print(f"변이 {len(results)}종 중 {ok}종에서 테스트가 발화했다.")
    print("=" * 84)
    if ok != len(results):
        print("!! 발화하지 않은 변이가 있다 — 그 축은 무검사다. 테스트를 고쳐라.")
        return 2

    # 되돌림 확인 — 워킹트리를 더럽히지 않았는가
    rc2, _ = run(TEST)
    print(f"\n복원 후 재실행 exit={rc2} ({'clean' if rc2 == 0 else '!! 복원 실패 !!'})")
    return 0 if rc2 == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
