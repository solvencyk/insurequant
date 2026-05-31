# -*- coding: utf-8 -*-
import sys, time, re, json
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
    # IR자료 dedicated list (data room). Try the IR materials list URL pattern.
    d.get('https://m.irgo.co.kr/IR-ROOM/001450'); time.sleep(7)
    # click the first 더보기 (IR자료) link
    mores = d.find_elements(By.XPATH, "//*[normalize-space(text())='더보기']")
    print('더보기 count', len(mores))
    if mores:
        d.execute_script("arguments[0].click();", mores[0]); time.sleep(6)
    print('url now', d.current_url, 'htmllen', len(d.page_source))
    # collect all links + onclicks that look like IR detail
    rows=[]
    for a in d.find_elements(By.XPATH, "//a | //li | //div[@onclick]"):
        t=(a.text or '').strip()
        h=a.get_attribute('href') or ''
        oc=a.get_attribute('onclick') or ''
        if '경영실적' in t and ('현대해상' in t or '20' in t):
            rows.append((t[:60], h[:120], oc[:120]))
    seen=set(); 
    for t,h,oc in rows:
        if t in seen: continue
        seen.add(t)
        print('ROW', repr(t),'| href',h,'| onclick',oc)
finally:
    d.quit()
