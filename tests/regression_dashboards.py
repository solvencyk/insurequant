#!/usr/bin/env python
"""InsureQuant dashboard regression harness (Playwright).

Encodes the cumulative owner/QA glitches (round1~3 + DS1) as automated asserts so
they stop being eyeball-only. Runs headless Chromium (Playwright's own bundle —
this machine's Edge/Chrome --dump-dom returns 0 bytes, Playwright works).

Run (server lifecycle auto-managed, no zombie ports):
  PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
  $PY .claude/skills/webapp-testing/scripts/with_server.py \
      --server "$PY -m http.server 8899" --port 8899 -- \
      $PY tests/regression_dashboards.py --port 8899

Exit 0 = all green, 1 = at least one regression.
"""
import argparse, re, sys
from playwright.sync_api import sync_playwright

try:  # keep Korean check names readable even on a cp949 (Windows) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = []
def check(name, cond, detail=""):
    RESULTS.append((bool(cond), name, detail))
    print(("PASS" if cond else "FAIL"), name, ("" if cond else f"-> {detail}"))

def attach_console(page, errbox):
    page.on("console", lambda m: errbox.append(f"console.error: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errbox.append(f"pageerror: {e}"))

def common_css_loaded(page):
    return page.evaluate("() => [...document.styleSheets].some(s => (s.href||'').endsWith('common.css'))")

def test_index(page, base):
    errs = []
    attach_console(page, errs)
    page.goto(f"{base}/index.html", wait_until="networkidle")
    page.wait_for_function("() => document.getElementById('kpiPeriod') && document.getElementById('kpiPeriod').textContent !== '—'", timeout=25000)
    check("index: common.css loaded", common_css_loaded(page))
    kpi = page.evaluate("() => ({csm:kpiCsm.textContent, ratio:kpiRatio.textContent, count:kpiCount.textContent, period:kpiPeriod.textContent, dl:document.getElementById('coJumpList').options.length})")
    check("index: KPI 총CSM 조단위", kpi["csm"].endswith("조"), kpi["csm"])
    check("index: KPI 중위값 %", kpi["ratio"].endswith("%"), kpi["ratio"])
    check("index: KPI 수록사 社", kpi["count"].endswith("社"), kpi["count"])
    check("index: KPI 기준분기 YYYY.nQ", bool(re.match(r"^\d{4}\.\dQ$", kpi["period"])), kpi["period"])
    check("index: typeahead datalist 채움", kpi["dl"] > 0, f"options={kpi['dl']}")
    cells = page.eval_on_selector_all(".cell", "els => els.length")
    check("index: 트리맵 셀 렌더(데스크탑)", cells > 0, f"cells={cells}")
    check("index: 콘솔 에러 0", not errs, "; ".join(errs[:3]))
    # typeahead jump navigates to IFRS17
    page.fill("#coJump", "삼성생명")
    page.press("#coJump", "Enter")
    page.wait_for_url("**/IFRS17.html?company=*", timeout=8000)
    check("index: typeahead → IFRS17 점프", "IFRS17.html" in page.url, page.url)

def test_kics(page, base):
    errs = []
    attach_console(page, errs)
    page.goto(f"{base}/K-ICS.html", wait_until="networkidle")
    page.wait_for_function("() => document.getElementById('company') && document.getElementById('company').options.length > 1", timeout=25000)
    check("kics: common.css loaded", common_css_loaded(page))
    nopt = page.eval_on_selector("#company", "el => el.options.length")
    check("kics: 회사 드롭다운 >=40", nopt >= 40, f"options={nopt}")
    # KB 2026.1Q solvency point present (label-variant fix)
    page.select_option("#company", "KB손해보험")
    page.select_option("#period", "quarter")
    page.wait_for_timeout(500)
    kb = page.evaluate(r"""() => {
      const cv=[...document.querySelectorAll('canvas')].find(c=>{const ch=Chart.getChart(c);return ch&&(ch.data.labels||[]).some(l=>/\d{4}\.\dQ/.test(String(l)));});
      if(!cv) return null; const ch=Chart.getChart(cv);
      const i=ch.data.labels.indexOf('2026.1Q');
      const sol=ch.data.datasets.find(d=>/지급여력비율/.test(d.label||''));
      return {labels:ch.data.labels, idx:i, val:(sol&&i>=0)?sol.data[i]:null};
    }""")
    check("kics: KB 분기차트 2026.1Q 존재", bool(kb) and kb["idx"] >= 0, str(kb and kb["labels"]))
    check("kics: KB 2026.1Q 지급여력비율 ~185.87", bool(kb) and kb["val"] is not None and abs(kb["val"] - 185.87) < 0.5, str(kb and kb["val"]))
    # 순자산(4→5~11)·기타요구자본(23→24~26) +토글 — 현대해상 = 둘 다 자식 보유
    page.select_option("#company", "현대해상")
    page.wait_for_timeout(500)
    check("kics: 순자산 +토글 존재", page.evaluate("() => !!document.querySelector('.subtoggle[data-group=netasset]')"))
    check("kics: 기타요구자본 +토글 존재", page.evaluate("() => !!document.querySelector('.subtoggle[data-group=othercap]')"))
    check("kics: 순자산 자식 기본 숨김", page.evaluate("() => { const r=[...document.querySelectorAll('tr.subrow-netasset')]; return r.length>0 && r.every(t=>getComputedStyle(t).display==='none'); }"))
    check("kics: 생명장기/시장 +토글 유지", page.evaluate("() => !!document.querySelector('.subtoggle[data-group=life]') && !!document.querySelector('.subtoggle[data-group=mkt]')"))
    bp = page.evaluate("""() => [...document.querySelectorAll('#table-container tbody tr')].filter(tr=>{const td=tr.querySelector('td');return td&&td.textContent.trim()==='1. 보통주';}).map(tr=>tr.className)""")
    check("kics: 보통주(item5) 단독행 중복 없음", len(bp) == 1 and 'subrow-netasset' in bp[0], str(bp))
    page.click(".subtoggle[data-group=netasset]"); page.wait_for_timeout(150)
    check("kics: 순자산 +클릭 펼침", page.evaluate("() => [...document.querySelectorAll('tr.subrow-netasset')].some(t=>getComputedStyle(t).display!=='none')"))
    check("kics: 콘솔 에러 0", not errs, "; ".join(errs[:3]))

def test_ifrs17(page, base):
    errs = []
    attach_console(page, errs)
    page.goto(f"{base}/IFRS17.html?company=%EC%82%BC%EC%84%B1%EC%83%9D%EB%AA%85", wait_until="networkidle")  # 삼성생명
    page.wait_for_function("() => document.querySelectorAll('#senTable table tbody tr').length > 0", timeout=25000)
    check("ifrs: common.css loaded", common_css_loaded(page))
    sen = page.evaluate("""() => {
      const cap=document.getElementById('senCap').textContent;
      const rows=[...document.querySelectorAll('#senTable table tbody tr')].map(tr=>[...tr.children].map(td=>td.textContent));
      return {cap, rows};
    }""")
    check("ifrs: 민감도 as-of 캡션", ("기준:" in sen["cap"]) and bool(re.search(r"\d{4}-\d{2}-\d{2}", sen["cap"])), sen["cap"])
    # G1: 재보험 + 토글이 K-ICS .subtoggle 양식(common.css) — 18px inline-flex
    sub = page.evaluate("() => { const b=document.querySelector('button.subtoggle'); if(!b) return null; const cs=getComputedStyle(b); return {w:cs.width, display:cs.display, radius:cs.borderTopLeftRadius}; }")
    check("ifrs: 재보험 +버튼 .subtoggle 양식", bool(sub) and sub["w"] == "18px" and sub["display"] == "inline-flex", str(sub))
    # G2: 점선 시리즈가 legend에 '신계약 CSM 시계열'로 식별
    hl = page.evaluate("() => { const c=document.getElementById('canvasHist'); const ch=c&&Chart.getChart(c); return ch?ch.data.datasets.map(d=>d.label):null; }")
    check("ifrs: 점선 legend '신계약 CSM 시계열'", isinstance(hl, list) and any("신계약 CSM 시계열" in (l or "") for l in hl), str(hl))
    flat = [c for r in sen["rows"] for c in r]
    check("ifrs: shock ↑/↓ 표준화", any(("↑" in c or "↓" in c) for c in flat), str(sen["rows"][:1]))
    check("ifrs: 음수 △(세모)", any("△" in c for c in flat), str(sen["rows"][:2]))
    # axis windowing (desktop viewport): year = [2023,2024,2025,2026.1Q]
    page.select_option("#company", "KR0069")  # 삼성생명
    page.select_option("#wfPeriod", "year")
    page.wait_for_timeout(500)
    yl = page.evaluate("() => { const c=document.getElementById('canvasHist'); const ch=c&&Chart.getChart(c); return ch?ch.data.labels:null; }")
    check("ifrs: 연도 윈도잉 [2023,2024,2025,2026.1Q]", yl == ["2023", "2024", "2025", "2026.1Q"], str(yl))
    page.select_option("#wfPeriod", "quarter")
    page.wait_for_timeout(500)
    ql = page.evaluate("() => { const c=document.getElementById('canvasHist'); const ch=c&&Chart.getChart(c); return ch?ch.data.labels:null; }")
    check("ifrs: 분기 윈도잉 직전5분기", isinstance(ql, list) and len(ql) == 5 and ql[-1] == "2026.1Q", str(ql))
    # 미제공사 (4Q-only) quarter mode → stub message
    page.select_option("#company", "KR0076")  # 아이엠라이프 (4Q-only)
    page.select_option("#wfPeriod", "quarter")
    page.wait_for_timeout(400)
    stub = page.evaluate("""() => { const s=document.querySelector('#wfStub'); return s?{disp:getComputedStyle(s).display, txt:s.textContent}:null; }""")
    check("ifrs: 분기 미제공사 메시지", bool(stub) and stub["disp"] != "none" and ("분기 공시 미제공" in stub["txt"]), str(stub))
    # 기간 윈도잉 (owner 2026-06-16): CSM waterfall(P1) + PL table(P4) = 분기 5 / 연도 [2023,2024,2025,2026.1Q]
    page.select_option("#company", "KR0069"); page.select_option("#wfPeriod", "year"); page.wait_for_timeout(500)
    wfy = page.evaluate("() => [...document.querySelectorAll('#wfTable thead th')].map(t=>t.textContent)")
    check("ifrs: CSM waterfall 연도 [2023,2024,2025,2026.1Q]", wfy[1:] == ["2023", "2024", "2025", "2026.1Q"], str(wfy))
    ply = page.evaluate("() => [...document.querySelectorAll('#plTable thead th')].map(t=>t.textContent)")
    check("ifrs: PL table 연도 [2023,2024,2025,2026.1Q]", [h for h in ply if h in ("2023", "2024", "2025", "2026.1Q")] == ["2023", "2024", "2025", "2026.1Q"], str(ply))
    page.select_option("#wfPeriod", "quarter"); page.wait_for_timeout(500)
    wfq = page.evaluate("() => [...document.querySelectorAll('#wfTable thead th')].map(t=>t.textContent)")
    check("ifrs: CSM waterfall 분기 5버킷", len(wfq) - 1 == 5 and wfq[-1] == "2026.1Q", str(wfq))
    plq = page.evaluate("() => [...document.querySelectorAll('#plTable thead th')].map(t=>t.textContent)")
    check("ifrs: PL table 분기 5열", len([h for h in plq if re.match(r"\d{4}\.\dQ", h)]) == 5, str(plq))
    # 롯데손보 투자손익 zero-crossing: 보험손익(+) → 투자손익이 0선 아래로 (y0>0>y1)
    page.select_option("#company", "KR0003"); page.select_option("#wfPeriod", "quarter"); page.wait_for_timeout(600)
    lotte = page.evaluate("""() => {
      const el=document.getElementById('chartPl'); const ec=window.echarts&&echarts.getInstanceByDom(el); if(!ec) return null;
      const opt=ec.getOption(); const xs=(opt.xAxis[0]||{}).data||[]; const data=(opt.series[0]||{}).data||[];
      const i=xs.indexOf('투자손익'); return i<0 ? {xs} : {i, geo:data[i]};
    }""")
    ok_lotte = bool(lotte) and isinstance(lotte.get("geo"), list) and lotte["geo"][0] > 0 and lotte["geo"][1] < 0
    check("ifrs: 롯데 투자손익 0선 아래로(y0>0>y1)", ok_lotte, str(lotte))
    check("ifrs: 콘솔 에러 0", not errs, "; ".join(errs[:3]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    args = ap.parse_args()
    base = f"http://localhost:{args.port}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1366, "height": 900})
        for fn in (test_index, test_kics, test_ifrs17):
            page = ctx.new_page()
            try:
                fn(page, base)
            except Exception as e:
                check(f"{fn.__name__}: 실행", False, repr(e))
            finally:
                page.close()
        browser.close()
    npass = sum(1 for ok, *_ in RESULTS if ok)
    nfail = len(RESULTS) - npass
    print(f"\n==== {npass} passed, {nfail} failed ====")
    sys.exit(1 if nfail else 0)

if __name__ == "__main__":
    main()
