# -*- coding: utf-8 -*-
"""7_post 신설 전/후 전 버킷 시뮬레이션 (읽기전용, 마스터 불변).

BEFORE = git HEAD 버전 kics_json_rules.py(세션 시작 시점, 내 편집 전).
AFTER  = 현재 워킹트리(7_post 신설 반영).

둘 다 임시 파일에서 importlib 로 직접 로드한다(패키지 임포트 경로를 안 건드리므로
워킹트리·sys.modules 캐시 오염이 없다). 같은 마스터 JSON · 같은 tfi_applicability 를
두 버전에 물려 findings 시그니처를 대조한다:
  1) 7_post 를 제외한 모든 (회사,분기,rule) 조합의 status 가 바이트단위로 동일한가(회귀 0 증명)
  2) 7_post 자체의 상태분포 + RED 전건 나열(발행사 모순 vs 추출오류 판정용)
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
MASTER = ROOT / "kics_disclosure.json"
BEFORE_PATH = Path(
    r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant"
    r"\2e98dd9e-be51-411e-a455-ce573b8bf95c\scratchpad\kics_json_rules_BEFORE.py"
)
AFTER_PATH = ROOT / "src" / "solvency" / "validation" / "kics_json_rules.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass(frozen=True) needs cls.__module__ resolvable
    spec.loader.exec_module(mod)
    return mod


def sig(findings):
    return {(f["원보험사코드"], f["공시분기"], f["rule"]): f for f in findings}


def main():
    from validate_kics_disclosure import _load_tfi_applicability
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    tfi = _load_tfi_applicability()

    before_mod = load_module(BEFORE_PATH, "kics_rules_before")
    after_mod = load_module(AFTER_PATH, "kics_rules_after")

    before = sig(before_mod.run_validation(rows, tfi_applicability=tfi)["findings"])
    after = sig(after_mod.run_validation(rows, tfi_applicability=tfi)["findings"])

    before_keys = set(before)
    after_keys = set(after)
    new_keys = after_keys - before_keys
    removed_keys = before_keys - after_keys
    common = before_keys & after_keys

    changed_common = [k for k in common if before[k]["status"] != after[k]["status"]]
    non_7post_new = [k for k in new_keys if k[2] != "7_post"]
    non_7post_removed = [k for k in removed_keys if k[2] != "7_post"]

    print("=== 1) 7_post 이외 회귀 여부 ===")
    print(f"공통 (회사,분기,rule) 키 {len(common)}개 중 status 변경 {len(changed_common)}건")
    for k in changed_common[:20]:
        print(f"  REGRESSION {k}: {before[k]['status']} -> {after[k]['status']}")
    print(f"7_post 가 아닌데 새로 생긴 finding key: {len(non_7post_new)}건 {non_7post_new[:10]}")
    print(f"7_post 가 아닌데 사라진 finding key: {len(non_7post_removed)}건 {non_7post_removed[:10]}")

    print("\n=== 2) 7_post 상태분포 ===")
    from collections import Counter
    c = Counter(after[k]["status"] for k in new_keys if k[2] == "7_post")
    print(dict(c))

    print("\n=== 3) 7_post RED 전건 ===")
    reds = [k for k in new_keys if k[2] == "7_post" and after[k]["status"] == "RED"]
    print(f"RED {len(reds)}건")
    for k in sorted(reds):
        f = after[k]
        print(f"  {k[0]} {k[1]}: expected={f.get('expected')} actual={f.get('actual')} "
              f"diff={f.get('diff')} detail={f.get('detail')}")

    print("\n=== 4) 7_post YELLOW 표본(최대 5) ===")
    yellows = [k for k in new_keys if k[2] == "7_post" and after[k]["status"] == "YELLOW"]
    for k in sorted(yellows)[:5]:
        f = after[k]
        print(f"  {k[0]} {k[1]}: expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")

    print("\n=== 5) 안전장치: 8_post 도 같이 안 흔들렸는지(구조 복붙이라 자기참조 실수 없는지) ===")
    b8 = {k: v["status"] for k, v in before.items() if k[2] == "8_post"}
    a8 = {k: v["status"] for k, v in after.items() if k[2] == "8_post"}
    diff8 = [k for k in b8 if b8[k] != a8.get(k)]
    print(f"8_post 변경 {len(diff8)}건 (0 이어야 정상)")


if __name__ == "__main__":
    main()
