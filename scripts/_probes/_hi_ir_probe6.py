# -*- coding: utf-8 -*-
"""현대해상: navigate to 실적발표자료 via goMenu('101641') and capture the
rendered earnings-materials list + per-row download mechanism."""
import sys, time, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,6000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
try:
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M'); time.sleep(7)
    # invoke the menu navigation used by the 실적발표자료 link
    try:
        d.execute_script("goMenu('101641');")
    except Exception as e:
        print('goMenu err', e)
    time.sleep(8)
    print('url now', d.current_url, 'title', repr(d.title), 'len', len(d.page_source))
    body = d.find_element(By.TAG_NAME,'body').text
    print('--- BODY (first 2200) ---')
    print(body[:2200])
    print('--- iframes ---')
    for fr in d.find_elements(By.TAG_NAME,'iframe'):
        print('  iframe', fr.get_attribute('src'))
    print('--- anchors / onclick (실적/분기/다운/pdf/xls/file) ---')
    for el in d.find_elements(By.XPATH, "//a | //button | //*[@onclick]"):
        t=(el.text or '').strip(); h=el.get_attribute('href') or ''; oc=el.get_attribute('onclick') or ''
        blob=(h+oc)
        if any(k in t for k in ['실적','경영','분기','상반기','결산','다운','자료','발표','반기']) \
           or '.pdf' in blob.lower() or '.xls' in blob.lower() or 'download' in blob.lower() \
           or 'fileDown' in blob or 'fnDown' in blob:
            if t or '.pdf' in blob.lower() or '.xls' in blob.lower() or 'ile' in oc:
                print('  EL', repr(t[:50]),'| h=',h[:70],'| oc=',oc[:100])
finally:
    d.quit()
