# -*- coding: utf-8 -*-
"""Probe 현대해상 IR JSP pages (CICI8xxx) for the 실적발표자료/경영실적 list."""
import sys, time, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,5000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)

def probe(url):
    d.get(url); time.sleep(6)
    body = d.find_element(By.TAG_NAME,'body').text
    print(f'\n##### {url}\n title={d.title!r} len={len(d.page_source)}')
    # is it an IR/실적 list? show body slice
    print(body[:900])
    # collect CICI page codes referenced + IR-ish anchors
    src = d.page_source
    codes = sorted(set(re.findall(r'CICI\d+[A-Z]?\.jsp', src)))
    print(' CICI codes in src:', codes)
    for a in d.find_elements(By.TAG_NAME,'a'):
        t=(a.text or '').strip(); h=a.get_attribute('href') or ''; oc=a.get_attribute('onclick') or ''
        blob=(h+oc)
        if any(k in t for k in ['실적','경영실적','자료','발표','분기','상반기','결산','다운']) or '.pdf' in blob.lower() or '.xls' in blob.lower() or 'download' in blob.lower() or 'fileDown' in blob:
            if t or '.pdf' in blob.lower() or '.xls' in blob.lower():
                print('  A', repr(t[:45]),'| h=',h[:75],'| oc=',oc[:85])

try:
    for u in [
        'https://www.hi.co.kr/bin/CI/CI/CICI8037G.jsp',
        'https://www.hi.co.kr/bin/CI/CI/CICI8123G.jsp',
        'https://www.hi.co.kr/bin/CI/CI/CICI8000G.jsp',
    ]:
        try:
            probe(u)
        except Exception as e:
            print('ERR', u, e)
finally:
    d.quit()
