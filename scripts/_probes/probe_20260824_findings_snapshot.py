"""룰엔진 findings 스냅샷 dump / diff — 룰 수정 전후를 전 버킷으로 대조한다.

사용:
  ... probe_20260824_findings_snapshot.py dump  artifacts/validation/f_before.json
  (룰 수정)
  ... probe_20260824_findings_snapshot.py dump  artifacts/validation/f_after.json
  ... probe_20260824_findings_snapshot.py diff  before.json after.json

게이트가 실제로 쓰는 입력(`_load_tfi_applicability`)을 그대로 쓴다 — 다른 입력으로 재면
"게이트가 검사하는 것 = 내가 잰 것" 이 깨진다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def _dump(out: Path) -> None:
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res
    snap = {
        f"{f['원보험사코드']}|{f['공시분기']}|{f['rule']}": [
            f["status"], f.get("diff"), f.get("detail", "")
        ]
        for f in findings
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {out}  ({len(snap)} findings)")
    print("status 집계:", dict(Counter(v[0] for v in snap.values())))


def _branch_of(detail: str) -> str:
    i = detail.find("branch=")
    if i < 0:
        return ""
    return detail[i + 7:].split()[0].rstrip(",—")


def _diff(a: Path, b: Path) -> None:
    A = json.loads(a.read_text(encoding="utf-8"))
    B = json.loads(b.read_text(encoding="utf-8"))
    only_a, only_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    print(f"before {len(A)} findings · after {len(B)} findings")
    print(f"before 에만 있는 finding {len(only_a)}: {only_a[:20]}")
    print(f"after  에만 있는 finding {len(only_b)}: {only_b[:20]}")
    print("status 집계 before:", dict(Counter(v[0] for v in A.values())))
    print("status 집계 after :", dict(Counter(v[0] for v in B.values())))

    trans, diffchg, branchchg = Counter(), Counter(), Counter()
    fixes, breaks, others = [], [], []
    for k in sorted(set(A) & set(B)):
        (s0, d0, t0), (s1, d1, t1) = A[k], B[k]
        rule = k.split("|")[2]
        if s0 != s1:
            trans[(rule, s0, s1)] += 1
            line = f"  {k:<48} {s0:>6} -> {s1:<6} diff {d0} -> {d1}"
            (fixes if s1 == "GREEN" else breaks if s0 == "GREEN" else others).append(line)
        elif (d0 if d0 is not None else 0) != (d1 if d1 is not None else 0):
            diffchg[(rule, s0)] += 1
            others.append(f"  {k:<48} {s0:>6} (동일) diff {d0} -> {d1}")
        bb0, bb1 = _branch_of(t0), _branch_of(t1)
        if bb0 != bb1:
            branchchg[(rule, bb0, bb1)] += 1

    print(f"\n=== status 전이 {sum(trans.values())} 건 ===")
    for (rule, s0, s1), n in sorted(trans.items()):
        print(f"  {rule:<32} {s0:>6} -> {s1:<6} {n}")
    print(f"\n=== status 동일인데 diff 가 바뀐 셀 {sum(diffchg.values())} 건 ===")
    for (rule, s0), n in sorted(diffchg.items()):
        print(f"  {rule:<32} {s0:>6} {n}")
    print(f"\n=== 갈래(branch) 이름이 바뀐 셀 {sum(branchchg.values())} 건 ===")
    for (rule, b0, b1), n in sorted(branchchg.items()):
        print(f"  {rule:<32} {b0 or '-':<22} -> {b1 or '-':<22} {n}")
    print(f"\n=== 새로 GREEN {len(fixes)} ===")
    print("\n".join(fixes) or "  (없음)")
    print(f"\n=== GREEN 이 깨짐 {len(breaks)} ===")
    print("\n".join(breaks) or "  (없음)")
    print(f"\n=== 그 밖의 변화 {len(others)} ===")
    print("\n".join(others[:200]) or "  (없음)")


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        _dump(Path(sys.argv[2]))
    else:
        _diff(Path(sys.argv[2]), Path(sys.argv[3]))
