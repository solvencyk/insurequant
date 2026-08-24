# -*- coding: utf-8 -*-
"""항목번호 등록부(`data/_gold/kics_item_registry.json`) 강제.

## 왜 이 파일이 있나 — 2026-08-24 번호 충돌

항목번호는 **parser-kics 레인과 validation 레인이 공유하는 이름공간**인데 등록부가 없었다.
2026-08-24 에 두 레인이 52 번을 동시에 잡았다:

  · parser  — TFI 표 메모행 `(기발행 신종자본증권)` 을 표 인쇄 순서대로 51 다음 정수에 배정
  · validation — `50_tfi_tier_split_post` 를 범위검사에서 등식으로 승격시킬 comparand
                 (`지급여력금액(TFI표)`) 로 **예약**. 예약은 룰 코드 주석과 TODO 산문에만 있었다.

parser 가 게이트를 돌리다 **게이트 출력 문구에서 우연히** 눈치채고 되돌렸다. 다음엔 못 잡는다.
산문에 적힌 예약은 기계가 못 읽는다 — 이 테스트가 그 예약을 기계가 읽는 자리로 옮긴다.

## 무엇을 막나

  1. 마스터에 있는데 등록부에 없는 번호 (= 누가 말없이 새 번호를 잡았다)
  2. 등록부에 있는데 마스터에 없는 번호 (= dangling 예약 / 삭제된 항목이 등록부에 남음)
  3. `reserved` 로 예약된 번호에 데이터가 들어옴 (= 예약을 채운 레인이 등록부를 안 고쳤다)
  4. 존재하지 않는 룰 id 를 `wired_rules` 에 적음 (= 룰 개명·삭제 후 등록부가 stale)

`tests/test_rule_coverage_manifest.py` 와 역할이 다르다 — 저쪽은 "이 항목이 **검사되나**",
여기는 "이 번호가 **누구 것인가**" 다. 커버리지가 0 이어도(메모행처럼) 번호는 등록돼야 한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "_gold" / "kics_item_registry.json"
MASTER = ROOT / "kics_disclosure.json"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def registry():
    assert REGISTRY.exists(), (
        f"항목번호 등록부가 없다: {REGISTRY}. 이 파일이 없으면 두 레인이 같은 번호를 "
        "다시 잡아도 아무도 모른다(2026-08-24 item52 충돌).")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def _master_items(rows) -> set[int]:
    out = set()
    for r in rows:
        try:
            out.add(int(r["항목번호"]))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _unregistered(registry) -> set[int]:
    out: set[int] = set()
    for rng in registry.get("unregistered_ranges", []):
        out |= set(range(int(rng["from"]), int(rng["to"]) + 1))
    return out


def test_every_master_item_number_is_registered(registry, rows):
    """마스터에 실린 번호는 전부 등록부에 있거나 미등재 범위로 **선언**돼 있어야 한다."""
    declared = {int(k) for k in registry["items"]} | _unregistered(registry)
    unknown = sorted(_master_items(rows) - declared)
    assert not unknown, (
        f"마스터에 있는데 등록부에 없는 항목번호: {unknown}.\n"
        f"{REGISTRY.name} 의 `items` 에 label·source_table·owner_lane·wired_rules 를 붙여 "
        "등재하라. 룰을 아직 안 걸었어도 등재는 해야 한다 — 등재의 목적은 커버리지가 아니라 "
        "**다음 번호 충돌을 막는 것**이다.")


def test_registry_has_no_dangling_entries(registry, rows):
    """등록부에만 있고 마스터에 없는 번호는 `status`=`reserved` 여야 한다."""
    master = _master_items(rows)
    dangling = sorted(
        int(k) for k, v in registry["items"].items()
        if int(k) not in master and v.get("status") != "reserved")
    assert not dangling, (
        f"등록부에 있는데 마스터에 한 셀도 없는 항목: {dangling}. 아직 적재 전이면 "
        '`"status": "reserved"` 로 두고, 폐기됐으면 등록부에서 지워라 — 어느 쪽도 아니면 '
        "다음 세션이 있지도 않은 항목에 룰을 건다.")


def test_reserved_items_have_no_data_yet(registry, rows):
    """예약 번호에 데이터가 들어오면 **막는다** — 채운 레인이 등록부를 같이 고쳐야 한다.

    이게 없으면 예약이 조용히 오염된다. 2026-08-24 의 item52 가 정확히 그 경로였다."""
    master = _master_items(rows)
    filled = sorted(
        int(k) for k, v in registry["items"].items()
        if v.get("status") == "reserved" and int(k) in master)
    assert not filled, (
        f"예약(reserved)된 항목번호에 데이터가 들어와 있다: {filled}. 예약을 채웠으면 "
        f'{REGISTRY.name} 에서 status 를 "loaded" 로 바꾸고 owner_lane·wired_rules 를 갱신하라. '
        "예약한 쪽이 그 번호를 무엇에 쓰려 했는지 확인하지 않으면 조용히 덮어쓰는 것이다.")


def test_wired_rules_actually_exist(registry, rows):
    """`wired_rules` 의 룰 id 가 실제로 엔진에서 나오는지 — 개명·삭제 후 stale 차단."""
    from solvency.validation.kics_json_rules import run_validation
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_kics_disclosure import _load_tfi_applicability
    emitted = {f["rule"] for f in
               run_validation(rows, tfi_applicability=_load_tfi_applicability())["findings"]}
    bad = {}
    for k, v in registry["items"].items():
        miss = sorted(set(v.get("wired_rules", [])) - emitted)
        if miss:
            bad[k] = miss
    assert not bad, (
        f"등록부가 존재하지 않는 룰 id 를 가리킨다: {bad}. 룰을 개명·삭제했으면 등록부도 "
        "같이 고쳐라 — 안 그러면 '이 항목은 검사된다' 는 선언이 거짓말이 된다.")


def test_registry_declares_owner_lane_for_every_item(registry):
    """소유 레인 없는 등재는 충돌 예방에 쓸모가 없다."""
    lanes = set(registry["_owner_lanes"])
    bad = sorted(k for k, v in registry["items"].items() if v.get("owner_lane") not in lanes)
    assert not bad, (
        f"owner_lane 이 없거나 선언되지 않은 값인 항목: {bad}. 허용값 {sorted(lanes)}")
