"""공유 스크린샷 회귀 (2026-10-11, designer).

2026-10-08 공통 공유 메뉴가 `scrollHeight <= 6000` 일 때만 전체를 찍고 그보다 길면 현재 화면만 찍게 막아 두었다.
K-ICS·IFRS17·모바일은 거의 다 6000px 을 넘어 사실상 늘 현재 화면만 찍혔다(owner 2026-10-11 지적, 이 파일이 막는 회귀).

- 정적 검사(항상 실행, 오프라인): 높이로 전체/현재 화면을 가르는 분기가 없고, 캔버스 한도 계획(shPlan)이 있고,
  세 페이지의 섹션 마크업(data-share-section)이 빠지지 않았다.
- 브라우저 검사(RUN_SHARE_SHOT=1 일 때만): `scripts/check_share_screenshot.py` 가 실제로 이미지를 만들어
  전체 이미지 높이 > 뷰포트 높이를 단정한다(데스크톱 1280 · 모바일 375, 전체 + 섹션 3~4곳 + 클릭 경로 + 캔버스 한도).
  Playwright·망(jsdelivr)이 없으면 스크립트가 SKIP 으로 끝난다 — 안 돌렸다는 통과가 아니므로 기본 게이트에는 넣지 않았다.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_no_height_gate_on_full_capture():
    js = _read("theme.js")
    assert not re.search(r"scrollHeight\s*<=?\s*\d{3,}", js), "높이 임계값으로 전체/현재 화면을 가르면 긴 페이지가 현재 화면만 찍힌다"
    # 현재 화면 크롭(window.scrollY/innerHeight 로 x,y,width,height 지정)이 되살아나지 않았는지
    assert "opt.y = window.scrollY" not in js
    assert "opt.windowHeight = window.innerHeight" not in js


def test_canvas_limit_plan_present():
    js = _read("theme.js")
    assert "function shPlan(" in js and "SH_MAX_DIM" in js and "SH_MIN_SCALE" in js
    assert re.search(r"SH_MAX_DIM\s*=\s*1[0-6]\d{3}\s*;", js), "캔버스 한 변 상한은 16,384 안쪽이어야 한다"


def test_share_menu_label_and_section_api():
    js = _read("theme.js")
    assert "페이지 전체 스크린샷" in js and "현재 페이지 스크린샷" not in js
    assert "mountSectionShare" in js and "iq-sec-share" in js and "이 섹션 스크린샷 공유" in js
    css = _read("common.css")
    assert ".iq-sec-share" in css and "width:44px" in css.replace(" ", "")


@pytest.mark.parametrize("page,want", [("K-ICS.html", 4), ("IFRS17.html", 9)])
def test_section_markup_complete(page, want):
    html = _read(page)
    assert len(re.findall(r'<div class="panel" id="[^"]+"[^>]*data-share-section="', html)) == want
    # 섹션 네비의 앵커 수와 같아야 한다(빠진 섹션 없음)
    nav = re.search(r'<nav class="section-nav".*?</nav>', html, re.S).group(0)
    assert len(re.findall(r'href="#', nav)) == want


def test_compare_cards_marked():
    html = _read("compare.html")
    assert "card.setAttribute('data-share-section', title)" in html


@pytest.mark.skipif(os.environ.get("RUN_SHARE_SHOT") != "1", reason="브라우저 검사: RUN_SHARE_SHOT=1 로 실행")
def test_full_page_image_taller_than_viewport():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_share_screenshot.py")],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", timeout=900,
    )
    out = proc.stdout + proc.stderr
    if "SKIP:" in out:
        pytest.skip(out.strip().splitlines()[-1])
    assert proc.returncode == 0, out[-3000:]
