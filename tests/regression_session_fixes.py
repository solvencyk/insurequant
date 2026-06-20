#!/usr/bin/env python
"""Verify this session's 3 fixes:
 1) K-ICS forward outlook: 신뢰도(confidence) 요소·배지 완전 제거
 2) IFRS17 Panel5 NB CSM 배수: 연도→연누계 1계열, 분기→당분기 1계열
 3) index 모바일: 더보기 펼친 뒤 높이-only resize(스크롤) → 펼침 유지
Run: PY tests/_verify_session_fixes.py --port 8899
"""
import argparse, sys
from playwright.sync_api import sync_playwright
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

R = []
def chk(n, c, d=""):
    R.append((bool(c), n, d)); print(("PASS" if c else "FAIL"), n, ("" if c else f"-> {d}"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8899)
    base = f"http://localhost:{ap.parse_args().port}"
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)

        # ===== 1) K-ICS forward 신뢰도 제거 =====
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        pg = ctx.new_page(); kerr = []
        pg.on("console", lambda m: kerr.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: kerr.append(str(e)))
        pg.goto(f"{base}/K-ICS.html", wait_until="networkidle")
        pg.wait_for_function("() => document.getElementById('company') && document.getElementById('company').options.length > 1", timeout=25000)
        chk("kics: forward-confidence-wrap DOM 제거", pg.evaluate("() => !document.getElementById('forward-confidence-wrap')"))
        chk("kics: forward-confidence CSS 클래스 미사용", pg.evaluate("() => !document.querySelector('.forward-confidence-wrap, .forward-confidence-badge')"))
        chk("kics: '모델 신뢰도' 텍스트 부재", pg.evaluate("() => !/모델 신뢰도|Face vs/.test(document.body.innerText)"))
        # forward 패널 정상 렌더 (cohort 회사 선택) — 신뢰도 없이도 차트 뜸
        pg.select_option("#company", "삼성생명보험"); pg.wait_for_timeout(700)
        chk("kics: 콘솔 에러 0(신뢰도 제거 후)", not kerr, "; ".join(kerr[:3]))
        ctx.close()

        # ===== 2) IFRS17 Panel5 기준별 단일 계열 =====
        ctx2 = b.new_context(viewport={"width": 1366, "height": 900})
        pg2 = ctx2.new_page(); ferr = []
        pg2.on("console", lambda m: ferr.append(m.text) if m.type == "error" else None)
        pg2.on("pageerror", lambda e: ferr.append(str(e)))
        pg2.goto(f"{base}/IFRS17.html", wait_until="networkidle")
        pg2.wait_for_function("() => document.getElementById('company') && document.getElementById('company').options.length > 1", timeout=25000)
        pg2.select_option("#company", "KR0069")  # 삼성생명
        pg2.select_option("#wfPeriod", "year"); pg2.wait_for_timeout(600)
        yr = pg2.evaluate("() => { const c=document.getElementById('canvasNb'); const ch=c&&Chart.getChart(c); return ch?ch.data.datasets.map(d=>d.label):null; }")
        chk("ifrs Panel5: 연도→연누계 1계열", yr == ["연누계 배수"], str(yr))
        pg2.select_option("#wfPeriod", "quarter"); pg2.wait_for_timeout(600)
        qr = pg2.evaluate("() => { const c=document.getElementById('canvasNb'); const ch=c&&Chart.getChart(c); return ch?ch.data.datasets.map(d=>d.label):null; }")
        chk("ifrs Panel5: 분기→당분기 1계열", qr == ["당분기 배수"], str(qr))
        chk("ifrs: 콘솔 에러 0(Panel5)", not ferr, "; ".join(ferr[:3]))
        ctx2.close()

        # ===== 3) index 모바일 더보기 펼침 유지(높이-only resize) =====
        ctx3 = b.new_context(viewport={"width": 390, "height": 840})
        pg3 = ctx3.new_page(); ierr = []
        pg3.on("console", lambda m: ierr.append(m.text) if m.type == "error" else None)
        pg3.on("pageerror", lambda e: ierr.append(str(e)))
        pg3.goto(f"{base}/index.html", wait_until="networkidle")
        pg3.wait_for_function("() => document.querySelectorAll('#map-list .li-more-btn').length > 0", timeout=25000)
        # 생보 더보기 클릭 → 펼침
        pg3.evaluate("() => document.querySelectorAll('#map-list .li-more-btn')[0].click()")
        pg3.wait_for_timeout(150)
        before = pg3.evaluate("() => document.querySelectorAll('#map-list .li-row').length")
        # 높이만 줄여 resize 발생(URL바 노출 시뮬) — 폭은 동일 390
        pg3.set_viewport_size({"width": 390, "height": 720})
        pg3.wait_for_timeout(200)
        after = pg3.evaluate("() => document.querySelectorAll('#map-list .li-row').length")
        chk("idx모바일: 높이-only resize 후 펼침 유지", after == before and after > 10, f"before={before} after={after}")
        # '접기' 버튼(reroll) → 다시 5개로 접힘
        pg3.evaluate("() => { const b=[...document.querySelectorAll('#map-list .li-more-btn')].find(x=>x.textContent.trim()==='접기'); if(b) b.click(); }")
        pg3.wait_for_timeout(150)
        fold = pg3.evaluate("() => { const k=[...document.getElementById('map-list').children]; let c=0; for(const x of k){ if(x.classList.contains('li-row')) c++; if(x.classList.contains('li-more-btn')) break;} return c; }")
        chk("idx모바일: '접기' 클릭 → 5개로 접힘", fold <= 5, f"firstblock={fold}")
        # 폭 변화(회전)는 정상적으로 접힘 리셋
        pg3.set_viewport_size({"width": 380, "height": 720})
        pg3.wait_for_timeout(200)
        rot = pg3.evaluate("() => { const k=[...document.getElementById('map-list').children]; const i=k.findIndex(x=>x.classList.contains('li-more-btn')); let c=0; for(const x of k){ if(x.classList.contains('li-row')) c++; if(x.classList.contains('li-more-btn')) break;} return c; }")
        chk("idx모바일: 폭 변화 시 접힘 리셋(≤5)", rot <= 5, f"firstblock={rot}")
        chk("idx모바일: 콘솔 에러 0", not ierr, "; ".join(ierr[:3]))
        ctx3.close()
        b.close()

    npass = sum(1 for ok, *_ in R if ok); nfail = len(R) - npass
    print(f"\n==== {npass} passed, {nfail} failed ====")
    sys.exit(1 if nfail else 0)

if __name__ == "__main__":
    main()
