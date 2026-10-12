"""K-ICS Forward Outlook 노트·차트의 거짓 개선 회귀 (2026-10-12, designer; 검증 감사 티켓 20261012T2236Z).

`kics_forward_capital.json` 은 가용자본(기본자본) <= 0 인 해의 비율을 0.0 으로 자르고 `*_exhausted` 를 true 로 둔다.
예전 화면은 자르지 않은 기준선에서 잘린 2030 값을 빼 예별 「+41.8%p」·롯데 「+5.4%p」를 인쇄했다.

- 오프라인(항상): ① JSON 계약 — 잘린 해 <=> 금액 <= 0, 안 잘린 해의 비율 = 금액/SCR(반올림 허용). 노트가 기대하는 「자본/SCR 기준 변화」가
  전 회사에서 정의된다. ② HTML 정적 — 잘린 해를 null 로 그리는 경로·△ 포맷터·안내 줄이 있고, 옛 ASCII 마이너스 눈금·`.toFixed(1) : '-'}%` 가 없다.
- 브라우저(RUN_KICS_FORWARD=1): `scripts/check_kics_forward_note.py` 가 47사 노트를 실제로 그려 변화 = 자본/SCR 기준 변화 또는 「—」,
  `+41.8%p`·ASCII 마이너스 0, 도넛 툴팁 375px 폭을 단정한다. `scripts/check_kics_callcell.py` 는 콜일 칸의 null/표식 내구성.
  Playwright·망이 없으면 스크립트가 SKIP — 안 돌렸다 != 통과했다.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _rows():
    return json.loads((ROOT / "kics_forward_capital.json").read_text(encoding="utf-8"))


def _ok_rows():
    return [r for r in _rows() if r.get("status") == "ok" and r.get("projections")]


def test_forward_json_flags_match_amounts():
    rows = _ok_rows()
    assert len(rows) >= 40
    for r in rows:
        for p in r["projections"]:
            assert p["capacity_exhausted"] == (p["capital_eok"] <= 0), (r["insurer_code"], p["year"])
            assert p["basic_capacity_exhausted"] == (p["basic_capital_eok"] <= 0), (r["insurer_code"], p["year"])
            if p["capacity_exhausted"]:
                assert p["ratio_pct"] == 0.0
            else:
                tol = 0.06 + 100 * 0.1 / p["scr_eok"]   # 금액은 소수 1자리 반올림
                assert abs(p["ratio_pct"] - p["capital_eok"] / p["scr_eok"] * 100) <= tol, (r["insurer_code"], p["year"])
            if p["basic_capacity_exhausted"]:
                assert p["basic_ratio_pct"] == 0.0


def test_note_change_is_capital_over_scr_or_dash_for_every_company():
    """노트의 「2030 변화」가 무엇이 되어야 하는지(기대값)가 전 회사에서 JSON 금액만으로 정의되고, 잘린 지표는 「—」다.
    예별·롯데의 옛 거짓값(+41.8%p, +5.4%p)은 기대값이 될 수 없다."""
    fake = {"KR0004": {"+41.8%p"}, "KR0003": {"+5.4%p"}}
    n_dash = 0
    for r in _ok_rows():
        base = r.get("baseline") or r.get("baseline_2025_4Q") or {}
        last = r["projections"][-1]
        for flag, amt, base_amt in (("capacity_exhausted", "capital_eok", "capital_eok"),
                                    ("basic_capacity_exhausted", "basic_capital_eok", "basic_capital_eok")):
            if last[flag]:
                n_dash += 1
                continue
            chg = last[amt] / last["scr_eok"] * 100 - base[base_amt] / base["scr_post_eok"] * 100
            printed = ("△" if chg < 0 else "+") + f"{abs(chg):.1f}%p"
            assert printed not in fake.get(r["insurer_code"], set())
    assert n_dash >= 3   # 예별 지급여력·기본자본 + 롯데 기본자본


def test_kics_html_forward_static():
    html = (ROOT / "K-ICS.html").read_text(encoding="utf-8")
    assert "function fwExhausted(" in html and "function fmtTriPct(" in html
    assert "(exR[i] || p.ratio_pct == null) ? null" in html and "(exB[i] || p.basic_ratio_pct == null) ? null" in html
    assert "id=\"forward-clip-note\"" in html and "지급여력비율: 자본잠식" in html and "기본자본비율: 자본잠식" in html
    # 옛 ASCII 마이너스 경로가 되살아나지 않았다
    assert "ticks: {callback: v => v.toFixed(0) + '%'" not in html
    assert ".basic_ratio_post_pct.toFixed(1) : '-'}%" not in html
    assert not re.search(r"ratio_post_pct != null \? baseline\.ratio_post_pct\.toFixed", html)
    # 도넛 툴팁: 긴 한 줄을 두 줄로, 「보완자본형이면」은 표시값과 다를 때만
    assert "' · ' + opt.overNote" not in html
    assert "t1UnconfDiffers" in html
    # 발행현황 막대: 추정 행(estimated: true)이 있는 해의 툴팁 꼬리
    assert "b.estimated === true" in html and "추정(원장 미갱신)" in html


@pytest.mark.skipif(os.environ.get("RUN_KICS_FORWARD") != "1", reason="브라우저 검사 — RUN_KICS_FORWARD=1 일 때만")
@pytest.mark.parametrize("script,args", [("check_kics_forward_note.py", ["--mobile"]), ("check_kics_callcell.py", []),
                                         ("check_kics_donuts.py", ["--mobile"]), ("check_kics_capsec_cells.py", ["--mobile"])])
def test_browser_checks(script, args):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=900)
    assert r.returncode == 0, (r.stdout[-3000:], r.stderr[-1500:])
