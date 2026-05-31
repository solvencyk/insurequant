# -*- coding: utf-8 -*-
"""Probe DB손해보험 IR 리포트 list page to discover earnings-report rows + download links."""
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
try:
    d.get('https://www.idbins.com/pc/bizxpress/contentTemplet/cmy/inv/ir/list.jsp'); time.sleep(8)
    print('TITLE', d.title, 'url', d.current_url, 'htmllen', len(d.page_source))
    print('iframes:', len(d.find_elements(By.TAG_NAME,'iframe')))
    for fr in d.find_elements(By.TAG_NAME,'iframe'):
        print('  iframe src=', fr.get_attribute('src'))
    body = d.find_element(By.TAG_NAME,'body').text
    print('--- BODY (first 2500) ---')
    print(body[:2500])
    print('--- anchors / onclick rows ---')
    for el in d.find_elements(By.XPATH, "//a | //*[@onclick]"):
        t=(el.text or '').strip(); h=el.get_attribute('href') or ''
        oc=el.get_attribute('onclick') or ''
        if any(k in t for k in ['실적','경영','분기','상반기','결산','IR','발표','다운']) or 'download' in (h+oc).lower() or '.pdf' in (h+oc).lower() or '.xls' in (h+oc).lower():
            print('  EL', repr(t[:50]),'| href=',h[:90],'| oc=',oc[:90])
finally:
    d.quit()
