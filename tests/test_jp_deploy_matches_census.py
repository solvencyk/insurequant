# -*- coding: utf-8 -*-
"""불변식 1번의 jp 레인판 — **배포 JSON = census 를 지금 재빌드한 결과**여야 한다.

왜 (UH-19, 2026-09-13)
----------------------
census 를 고치고 `jp/jesr_esr.json` 을 재생성하지 않은 채 커밋한 라운드가 실제로 있었다
(커밋 `62eed63`: 2사 `basis` 정정과 SOMPO 목표레인지 정정이 census 에만 들어가고 배포본은
옛 값 `unconfirmed` · `high_pct=270` 그대로였다). jp 레인의 게이트는 **빌더를 돌릴 때만** 도는데
빌더를 안 돌리면 게이트도 안 돌므로, 그 상태는 어떤 검사에도 안 걸렸다.

그래서 "빌더를 돌렸는가" 자체를 게이트가 검사한다. 이 테스트는 네트워크를 쓰지 않는다 —
빌더가 완전 오프라인이라 그대로 재실행해 바이트 비교만 한다(`generated_at` 만 제외).

이 테스트가 깨지면 고치는 법은 하나다: `python3 J-ESR/build_jesr_page_json.py` 를 돌리고
그 산출을 같이 커밋한다. 테스트의 기대값을 손으로 맞추지 말 것.

`docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md` §5 / UH-19.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JESR = ROOT / "J-ESR"
DEPLOY = ROOT / "jp" / "jesr_esr.json"
MASTER = JESR / "jesr_master.json"

pytestmark = pytest.mark.skipif(
    not (JESR / "build_jesr_page_json.py").exists() or not DEPLOY.exists(),
    reason="jp 레인 파일이 없는 slim 트리(main 등)",
)


def _strip_volatile(payload: dict) -> dict:
    meta = dict(payload.get("_meta", {}))
    meta.pop("generated_at", None)
    return {**payload, "_meta": meta}


def _rebuild(tmp_path: Path) -> tuple[dict, dict]:
    sys.path.insert(0, str(JESR))
    import build_jesr_page_json as builder  # noqa: E402

    master_out = tmp_path / "jesr_master.json"
    deploy_out = tmp_path / "jesr_esr.json"
    orig = (builder.MASTER_OUT, builder.DEPLOY_OUT)
    builder.MASTER_OUT, builder.DEPLOY_OUT = master_out, deploy_out
    try:
        rc = builder.main()
    finally:
        builder.MASTER_OUT, builder.DEPLOY_OUT = orig
    assert rc == 0, "빌더 self-check 가 실패했다 — 출처 게이트(RED) 메시지를 stderr 에서 확인해라"
    return (
        json.loads(master_out.read_text(encoding="utf-8")),
        json.loads(deploy_out.read_text(encoding="utf-8")),
    )


def test_deploy_json_is_current_rebuild_of_census(tmp_path):
    """`jp/jesr_esr.json` 이 커밋된 census 를 재빌드한 결과와 같아야 한다."""
    _, fresh_deploy = _rebuild(tmp_path)
    committed = json.loads(DEPLOY.read_text(encoding="utf-8"))
    a, b = _strip_volatile(committed), _strip_volatile(fresh_deploy)
    if a != b:
        diffs = []
        for rec_a, rec_b in zip(a.get("records", []), b.get("records", [])):
            for key in set(rec_a) | set(rec_b):
                if rec_a.get(key) != rec_b.get(key):
                    diffs.append(f"{rec_a.get('company_jp')}.{key}: 배포본={rec_a.get(key)!r} 재빌드={rec_b.get(key)!r}")
        meta_keys = [k for k in set(a["_meta"]) | set(b["_meta"]) if a["_meta"].get(k) != b["_meta"].get(k)]
        pytest.fail(
            "jp/jesr_esr.json 이 census 재빌드 결과와 다르다 — census 를 고치고 빌더를 안 돌렸다.\n"
            "  python3 J-ESR/build_jesr_page_json.py  를 돌리고 산출을 같이 커밋해라.\n"
            + ("\n".join(f"  - {d}" for d in diffs[:15]) or "")
            + (f"\n  _meta 차이: {meta_keys}" if meta_keys else "")
        )


def test_master_json_is_current_rebuild_of_census(tmp_path):
    """`J-ESR/jesr_master.json`(누가 posted 인가의 정본)도 같은 조건이다."""
    fresh_master, _ = _rebuild(tmp_path)
    committed = json.loads(MASTER.read_text(encoding="utf-8"))
    assert _strip_volatile(committed) == _strip_volatile(fresh_master), (
        "J-ESR/jesr_master.json 이 census 재빌드 결과와 다르다 — "
        "python3 J-ESR/build_jesr_page_json.py 를 돌리고 같이 커밋해라"
    )
