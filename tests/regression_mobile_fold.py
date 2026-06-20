#!/usr/bin/env python
"""Ad-hoc verification for: K-ICS 순자산/기타요구자본 +토글 + index 모바일 생보/손보 fold.
Run: PY tests/_verify_toggles_mobile.py --port 8899  (server must be up)
"""
import argparse, sys
from playwright.sync_api import sync_playwright
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

R = []
def chk(n, c, d=""):
    R.append((bool(c), n, d)); print(("PASS" if c else "FAIL"), n, ("" if c else f"-> {d}"))

def first_block_rows(seq):
    """count 'R' between first 'H:' header and the next header/MORE."""
    try: i0 = next(i for i, x in enumerate(seq) if x.startswith('H:'))
    except StopIteration: return -1
    cnt = 0
    for x in seq[i0+1:]:
        if x == 'R': cnt += 1
        elif x == 'MORE' or x.startswith('H:'): break
    return cnt

SEQ_JS = r"""(id) => {
  const host=document.getElementById(id); if(!host) return null;
  return [...host.children].map(k=>
    k.classList.contains('li-sector') ? ('H:'+k.textContent)
    : k.classList.contains('li-more-btn') ? 'MORE'
    : k.classList.contains('li-row') ? 'R' : '?');
}"""

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8899)
    base = f"http://localhost:{ap.parse_args().port}"
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)

        # ===== K-ICS 토글 (테이블은 뷰포트 무관 동일) =====
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        pg = ctx.new_page(); kerr = []
        pg.on("console", lambda m: kerr.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: kerr.append(str(e)))
        pg.goto(f"{base}/K-ICS.html", wait_until="networkidle")
        pg.wait_for_function("() => document.getElementById('company') && document.getElementById('company').options.length > 1", timeout=25000)
        pg.select_option("#company", "현대해상")
        pg.select_option("#period", "quarter")
        pg.wait_for_timeout(700)
        chk("kics: 순자산 +버튼 존재", pg.evaluate("() => !!document.querySelector('.subtoggle[data-group=netasset]')"))
        chk("kics: 기타요구자본 +버튼 존재", pg.evaluate("() => !!document.querySelector('.subtoggle[data-group=othercap]')"))
        na_cnt = pg.evaluate("() => document.querySelectorAll('tr.subrow-netasset').length")
        na_hid = pg.evaluate("() => [...document.querySelectorAll('tr.subrow-netasset')].every(t=>getComputedStyle(t).display==='none')")
        chk("kics: 순자산 자식 7개 기본 숨김", na_cnt == 7 and na_hid, f"count={na_cnt} hidden={na_hid}")
        oc_cnt = pg.evaluate("() => document.querySelectorAll('tr.subrow-othercap').length")
        oc_hid = pg.evaluate("() => [...document.querySelectorAll('tr.subrow-othercap')].every(t=>getComputedStyle(t).display==='none')")
        chk("kics: 기타요구자본 자식 3개 기본 숨김", oc_cnt == 3 and oc_hid, f"count={oc_cnt} hidden={oc_hid}")
        # 중복 없음: '1. 보통주'(item5)는 subrow로만 정확히 1회 (메인 루프 단독 렌더 방지 확인)
        bp = pg.evaluate("""() => [...document.querySelectorAll('#table-container tbody tr')]
          .filter(tr => { const td=tr.querySelector('td'); return td && td.textContent.trim()==='1. 보통주'; })
          .map(tr=>tr.className)""")
        chk("kics: 보통주(item5) 중복 없음(subrow만 1)", len(bp) == 1 and 'subrow-netasset' in bp[0], str(bp))
        # 클릭 → 펼침
        pg.click(".subtoggle[data-group=netasset]"); pg.wait_for_timeout(200)
        chk("kics: 순자산 +클릭→펼침", pg.evaluate("() => [...document.querySelectorAll('tr.subrow-netasset')].some(t=>getComputedStyle(t).display!=='none')"))
        pg.click(".subtoggle[data-group=othercap]"); pg.wait_for_timeout(200)
        chk("kics: 기타요구자본 +클릭→펼침", pg.evaluate("() => [...document.querySelectorAll('tr.subrow-othercap')].some(t=>getComputedStyle(t).display!=='none')"))
        # 기존 생명장기/시장 토글 유지
        chk("kics: 생명장기/시장 토글 유지", pg.evaluate("() => !!document.querySelector('.subtoggle[data-group=life]') && !!document.querySelector('.subtoggle[data-group=mkt]')"))
        chk("kics: 콘솔 에러 0", not kerr, "; ".join(kerr[:3]))
        ctx.close()

        # ===== index 모바일 (390px) 생보/손보 fold =====
        ctx2 = b.new_context(viewport={"width": 390, "height": 840})
        pg2 = ctx2.new_page(); ierr = []
        pg2.on("console", lambda m: ierr.append(m.text) if m.type == "error" else None)
        pg2.on("pageerror", lambda e: ierr.append(str(e)))
        pg2.goto(f"{base}/index.html", wait_until="networkidle")
        pg2.wait_for_function("() => document.querySelectorAll('#map-list .li-row').length > 0", timeout=25000)
        # K-ICS 리스트
        seq = pg2.evaluate(SEQ_JS, "map-list")
        heads = [x[2:] for x in seq if x.startswith('H:')]
        chk("idx모바일 K-ICS: 생보→손보 순서", heads[:2] == ['생명보험', '손해보험'], str(heads))
        chk("idx모바일 K-ICS: 생보 top5(첫블록≤5)", 0 < first_block_rows(seq) <= 5, str(seq[:14]))
        chk("idx모바일 K-ICS: 더보기 2개(생보+손보)", seq.count('MORE') == 2, f"MORE={seq.count('MORE')} seq={seq}")
        # 버블 CSM 리스트
        pg2.wait_for_function("() => document.querySelectorAll('#bubble-list .li-row').length > 0", timeout=25000)
        bseq = pg2.evaluate(SEQ_JS, "bubble-list")
        bheads = [x[2:] for x in bseq if x.startswith('H:')]
        chk("idx모바일 CSM버블: 생보→손보 순서", bheads[:2] == ['생명보험', '손해보험'], str(bheads))
        chk("idx모바일 CSM버블: 생보 top5(첫블록≤5)", 0 < first_block_rows(bseq) <= 5, str(bseq[:14]))
        chk("idx모바일 CSM버블: 더보기 존재", bseq.count('MORE') >= 1, f"MORE={bseq.count('MORE')} seq={bseq}")
        # 더보기 클릭 → 펼침
        pg2.evaluate("() => { const btns=document.querySelectorAll('#map-list .li-more-btn'); if(btns[0]) btns[0].click(); }")
        pg2.wait_for_timeout(200)
        seq2 = pg2.evaluate(SEQ_JS, "map-list")
        chk("idx모바일 K-ICS: 생보 더보기→확장", first_block_rows(seq2) > 5, str(seq2[:14]))
        chk("idx모바일: 콘솔 에러 0", not ierr, "; ".join(ierr[:3]))
        ctx2.close()
        b.close()

    npass = sum(1 for ok, *_ in R if ok); nfail = len(R) - npass
    print(f"\n==== {npass} passed, {nfail} failed ====")
    sys.exit(1 if nfail else 0)

if __name__ == "__main__":
    main()
