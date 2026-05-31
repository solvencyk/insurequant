# -*- coding: utf-8 -*-
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,3000')
d = webdriver.Chrome(options=opts)
try:
    # IR 자료실 candidate pages
    for url in [
        'https://www.hi.co.kr/bin/CI/CI/CICI8123G.jsp',   # IR일정
    ]:
        d.get(url); time.sleep(6)
        print('URL', url, 'TITLE', d.title)
        # dump anchors mentioning 실적/경영/IR/자료
        for a in d.find_elements(By.TAG_NAME, 'a'):
            t=(a.text or '').strip()
            h=a.get_attribute('href') or ''
            if any(k in t for k in ['실적','경영','자료','IR','발표']) or 'CICI' in h:
                if t or 'CICI' in h:
                    print('  A', repr(t[:40]), '->', h[:90])
        # also dump nav/menu text
        print('--- body head ---')
        print((d.find_element(By.TAG_NAME,'body').text or '')[:600])
finally:
    d.quit()
