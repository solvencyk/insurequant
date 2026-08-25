# -*- coding: utf-8 -*-
"""빌더 산출물 output/tier{1,2}_utilization/*_<quarter>.json → 배포본 루트
kics_tier{1,2}_utilization.json 조립(sync).

**왜 필요한가 (2026-08-25).** 이 두 배포본에는 조립 단계가 아예 없었다. 루트 파일은
2026-07-22 `a629e34`(K-ICS.html 인라인 JSON 분리) 때 한 번 복사된 스냅샷이고, 그 뒤
`wire_capital_securities_to_utilization.py` 가 빌더 산출물을 갱신해도(2026-08-03 DART
per-bond 소스 24사→39사) 루트는 따라가지 않았다. 결과: K-ICS.html 자본증권 도넛이 4사를
"발행 없음(0%)"으로 그렸다. `CLAUDE.md` 불변식 1번 위반.
포스트모템: `docs/postmortems/PM-2026-08-25_gate_read_the_wrong_file.md`
게이트: `scripts/validate_live_artifacts.py` (`TIER_DEPLOYED_VALUE_DIFFERS`)

기본은 **dry-run**(필드 단위 전건 열거만). 실제로 쓰려면 `--apply`.
배포본 포맷(indent=1 · ensure_ascii=False · CRLF · BOM 없음)을 그대로 유지한다.

용례:
  python scripts/sync_tier_utilization_to_deploy.py                 # 진단만
  python scripts/sync_tier_utilization_to_deploy.py --apply         # 반영
"""
import argparse
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

PAIRS = (
    ("tier1", ROOT / "kics_tier1_utilization.json", ROOT / "output" / "tier1_utilization"),
    ("tier2", ROOT / "kics_tier2_utilization.json", ROOT / "output" / "tier2_utilization"),
)
# K-ICS.html 이 실제로 그리는 필드 (updateDonutPanel: L906-917)
SCREEN_FIELDS = {
    "tier1": ("utilization_pct", "tier1_hybrid_issued_eok", "tier1_hybrid_limit_eok"),
    "tier2": ("utilization_pct", "numerator_eok", "tier2_limit_eok"),
}


def latest_builder(dirpath: Path, tier: str) -> Path:
    cands = sorted(dirpath.glob(f"{tier}_utilization_*.json"))
    cands = [p for p in cands if not p.name.endswith(".bak")]
    if not cands:
        raise SystemExit(f"[FATAL] 빌더 산출물 없음: {dirpath}")
    return cands[-1]  # 파일명이 <tier>_utilization_YYYYNQ.json 이라 사전순 = 분기순


def field_diffs(dep: dict, bld: dict):
    """(code, company, field, deployed_value, builder_value) 전건. 결측은 '<MISSING>'."""
    D = {r["code"]: r for r in dep.get("results", [])}
    B = {r["code"]: r for r in bld.get("results", [])}
    out, only_dep, only_bld = [], sorted(set(D) - set(B)), sorted(set(B) - set(D))
    for code in sorted(set(D) & set(B)):
        d, b = D[code], B[code]
        for k in sorted(set(d) | set(b)):
            dv, bv = d.get(k, "<MISSING>"), b.get(k, "<MISSING>")
            if dv != bv:
                out.append((code, d.get("company") or b.get("company"), k, dv, bv))
    return out, only_dep, only_bld


def write_deploy(path: Path, doc: dict) -> None:
    txt = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(txt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="배포본에 실제로 쓴다(기본은 진단만)")
    args = ap.parse_args()

    total = 0
    for tier, dep_path, bld_dir in PAIRS:
        bld_path = latest_builder(bld_dir, tier)
        dep = json.loads(dep_path.read_text("utf-8"))
        bld = json.loads(bld_path.read_text("utf-8"))
        print(f"\n===== {tier}: {dep_path.name} ← {bld_path.relative_to(ROOT)}")
        print(f"  배포본 quarter={dep.get('quarter')} n={len(dep.get('results', []))} | "
              f"빌더 quarter={bld.get('quarter')} n={len(bld.get('results', []))}")
        diffs, only_dep, only_bld = field_diffs(dep, bld)
        if only_dep or only_bld:
            print(f"  [WARN] 배포본에만 있는 회사={only_dep} · 빌더에만 있는 회사={only_bld}")
        if not diffs:
            print("  차이 없음 (in sync)")
            continue
        total += len(diffs)
        for code, company, field, dv, bv in diffs:
            mark = " *SCREEN*" if field in SCREEN_FIELDS[tier] else ""
            print(f"  {code} {company:<12} {field:<34} {dv!r:>12} -> {bv!r:>12}{mark}")
        if args.apply:
            out = dict(bld)  # 빌더가 정본: 값·정의 블록 전부
            write_deploy(dep_path, out)
            print(f"  [wrote] {dep_path.relative_to(ROOT)} ({len(diffs)} field(s))")

    if not args.apply and total:
        print(f"\n총 {total}개 필드가 어긋나 있다. 반영하려면 --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
