# -*- coding: utf-8 -*-
"""`validate_data_contract.py --selftest`(변이 회귀 suite, 90여 케이스)를 pytest 로 감싼다.

이 suite 는 UH-4(2026-07-21)에 만들어졌는데 **푸시 훅이 한 번도 돌리지 않았다**(호출처 0 -- `--selftest` 를 부르는 것이
문서뿐이었다). 케이스를 추가해도(예: 2026-10-11 Q9 주석 계보·Q10 원천부재) 사람이 손으로 돌리지 않으면 룰이 죽어도
아무도 모른다. 그래서 여기서 한 번에 돌리고, 한 케이스라도 FAIL/ERROR 면 실패시킨다. ~16초.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import _data_contract_selftest as ST  # noqa: E402


def test_data_contract_selftest_suite_passes():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ST.run_selftest()
    out = buf.getvalue()
    bad = [ln for ln in out.splitlines() if ln.lstrip().startswith(("FAIL", "ERROR"))]
    assert rc == 0 and not bad, "data-contract selftest 실패:\n" + "\n".join(bad[:20])
    # 케이스 수가 조용히 줄어드는 것도 막는다(룰/케이스 삭제) -- 2026-10-11 기준 92
    assert "SELF-TEST: " in out
    passed = int(out.split("SELF-TEST: ")[1].split("/")[0])
    assert passed >= 92, f"selftest 케이스가 줄었다: {passed} < 92"
