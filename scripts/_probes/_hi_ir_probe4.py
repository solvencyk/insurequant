# -*- coding: utf-8 -*-
"""Probe 현대해상 own IR site: navigate to IR 자료실 > 실적발표자료 and discover
the rendered list page URL + per-row download buttons. Start from the IR overview."""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,4000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)

def dump(tag):
    print(f'=== {tag} === url={d.current_url} title={d.title!r} len={len(d.page_source)}')
    try:
        body=d.find_element(By.TAG_NAME,'body').text
    except Exception as e:
        body=f'(no body: {e})'
    print(body[:1200])

try:
    # candidate IR landing pages observed in search
    for url in [
        'https://www.hi.co.kr/serviceAction.do?view=bin/KC/IR/KCIR05000M',
        'https://www.hi.co.kr/serviceAction.do?view=bin/KC/IR/KCIR01000M',
        'https://www.hi.co.kr/bin/KC/IR/KCIR05000M.jsp',
    ]:
        try:
            d.get(url); time.sleep(6)
            dump(url)
        except Exception as e:
            print('ERR', url, e)
    # from the main IR overview try to find earnings-materials link
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M'); time.sleep(7)
    dump('MAIN HHKC00000M')
    print('--- anchors mentioning 실적/경영/자료 ---')
    for a in d.find_elements(By.TAG_NAME,'a'):
        t=(a.text or '').strip(); h=a.get_attribute('href') or ''; oc=a.get_attribute('onclick') or ''
        if any(k in t for k in ['실적','경영실적','자료실','IR','발표']) or 'KCIR' in (h+oc) or 'serviceAction' in h:
            if t:
                print('  A', repr(t[:40]),'| href=',h[:80],'| oc=',oc[:80])
finally:
    d.quit()
