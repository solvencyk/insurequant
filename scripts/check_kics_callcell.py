#!/usr/bin/env python3
"""K-ICS.html 자본성증권 큼직한 셀의 「콜 상환 도래일」 내구성 검사 (2026-10-12, designer).

타임라인 JSON 의 잔액(outstanding_eok)이 null · 빈 문자열 · 표식 문자열(원장 미갱신)이어도 셀이 깨지지 않고 날짜만(또는 대시) 그리는지,
정상 값이면 종전처럼 날짜 + (금액억)을 그리는지 합성 JSON 으로 확인한다. JSON 파일은 읽기만 하고(라우트로 가로채 바꿈) 쓰지 않는다.
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/check_kics_callcell.py   종료코드 0 = 통과/SKIP, 1 = 위반
"""
from __future__ import annotations
import copy, json, socket, subprocess, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parents[1]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # noqa: BLE001
        print("SKIP: playwright 없음", e); return 0
    base = json.loads((ROOT / "kics_capital_securities_timeline.json").read_text(encoding="utf-8"))
    tl = {r["company"]: r for r in json.loads((ROOT / "kics_tier1_utilization.json").read_text(encoding="utf-8"))["results"]}
    code = next(k for k, v in base["securities"].items() if any(b["tier"] == "subordinated" and b.get("call_date") and b.get("outstanding_eok") for b in v))
    ref = max(b["as_of"] for v in base["securities"].values() for b in v if b.get("as_of"))
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    bad = []
    variants = {"normal": lambda b: None, "null": lambda b: b.update(outstanding_eok=None), "blank": lambda b: b.update(outstanding_eok=""),
                "marker": lambda b: b.update(outstanding_eok="원장 미갱신"), "missing": lambda b: b.pop("outstanding_eok", None),
                "datemarker": lambda b: b.update(call_date="원장 미갱신")}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(channel="msedge", headless=True)
            for vn, mut in variants.items():
                d = copy.deepcopy(base)
                for b in d["securities"][code]:
                    if b["tier"] == "subordinated" and b.get("call_date") and b["call_date"] >= ref and (b.get("outstanding_eok") or 0) > 0:
                        mut(b)
                ctx = br.new_context(viewport={"width": 375, "height": 812}); ctx.add_init_script("try{localStorage.setItem('iq_notice_seen','2026-3Q')}catch(e){}"); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
                pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
                body = json.dumps(d)
                pg.route("**/kics_capital_securities_timeline.json*", lambda route, request, body=body: route.fulfill(status=200, body=body, content_type="application/json"))
                pg.goto(f"http://127.0.0.1:{port}/K-ICS.html?iq_internal=1", wait_until="domcontentloaded")
                
                try:
                    pg.wait_for_function("() => window.Chart && document.getElementById('company').options.length > 5", timeout=30000)
                except Exception:
                    print("대기 실패", vn, errs); raise
                pg.wait_for_timeout(1500)
                n = pg.evaluate("(c) => allData.find(x => x['원보험사코드'] === c)['원수사명']", code)
                pg.evaluate("(n) => { const s = document.getElementById('company'); s.value = n; s.dispatchEvent(new Event('change')); }", n)
                pg.wait_for_timeout(500)
                txt = pg.evaluate("() => document.getElementById('capsec-cell-sub').innerText")
                print(f"[{vn}] {n}: {txt.replace(chr(10), ' / ')}")
                if errs: bad.append((vn, f"오류 {errs[:2]}"))
                ctx.close()
                if vn == "normal":
                    normal = txt
                elif vn in ("null", "blank", "marker", "missing"):
                    # 잔액을 모르는 증권은 날짜만 — 'NaN'·'undefined'·'null' 이 찍히면 안 된다
                    if any(x in txt for x in ("NaN", "undefined", "null")): bad.append((vn, "깨진 값 인쇄: " + txt))
                    if "콜 상환 도래일 : 20" not in txt: bad.append((vn, "날짜가 안 보임: " + txt))
                elif vn == "datemarker":
                    if any(x in txt for x in ("NaN", "undefined", "null", "미갱신")): bad.append((vn, "표식 인쇄: " + txt))
            br.close()
    finally:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(srv.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("violations", len(bad))
    for b in bad: print("  ", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
