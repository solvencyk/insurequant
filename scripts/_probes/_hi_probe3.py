# -*- coding: utf-8 -*-
import sys, time, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,4000')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
try:
    d.get('https://m.irgo.co.kr/IR-ROOM/001450'); time.sleep(8)
    print('TITLE', d.title, 'url', d.current_url, 'htmllen', len(d.page_source))
    body=d.find_element(By.TAG_NAME,'body').text
    print('--- BODY (first 1500) ---')
    print(body[:1500])
    print('--- anchors with 경영실적/발표/pdf ---')
    for a in d.find_elements(By.TAG_NAME,'a'):
        t=(a.text or '').strip(); h=a.get_attribute('href') or ''
        if ('경영실적' in t) or ('발표' in t) or h.endswith('.pdf') or 'IR-DETAIL' in h or 'detail' in h.lower():
            print('  A', repr(t[:50]),'->',h[:110])
finally:
    d.quit()
