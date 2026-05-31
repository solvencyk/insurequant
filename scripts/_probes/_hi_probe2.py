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
    d.get('https://www.hi.co.kr/bin/CI/CI/CICI8123G.jsp'); time.sleep(8)
    print('iframes:', len(d.find_elements(By.TAG_NAME,'iframe')))
    for fr in d.find_elements(By.TAG_NAME,'iframe'):
        print('  iframe src=', fr.get_attribute('src'))
    print('frames:', len(d.find_elements(By.TAG_NAME,'frame')))
    for fr in d.find_elements(By.TAG_NAME,'frame'):
        print('  frame src=', fr.get_attribute('src'))
    html=d.page_source
    print('html len', len(html))
    # show any CICI links / 실적 keyword positions in source
    import re
    for m in re.finditer(r'CICI\d+[A-Z]\.jsp', html):
        pass
    found=sorted(set(re.findall(r'CICI\d+[A-Z]\.jsp', html)))
    print('CICI pages in source:', found[:40])
    # current url after redirects
    print('current_url', d.current_url)
finally:
    d.quit()
