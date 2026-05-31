# -*- coding: utf-8 -*-
"""현대해상 실적발표자료: inspect exact DOM of each row (발표자료 / Factsheet buttons)
and the 연도 선택 year filter, to learn the download click mechanism."""
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
    d.execute_script("goMenu('101641');"); time.sleep(8)
    print('url', d.current_url, 'title', repr(d.title))
    # Find elements whose text is exactly Factsheet or 발표자료, print outerHTML of self + ancestors
    for label in ['Factsheet', '발표자료']:
        els = d.find_elements(By.XPATH, f"//*[normalize-space(text())='{label}']")
        print(f'\n=== label {label}: {len(els)} elements ===')
        if els:
            e = els[0]
            print(' tag', e.tag_name, '| onclick=', e.get_attribute('onclick'),
                  '| href=', e.get_attribute('href'))
            print(' self outerHTML:', (e.get_attribute('outerHTML') or '')[:300])
            # walk up 3 ancestors
            node = e
            for i in range(3):
                node = node.find_element(By.XPATH, '..')
                print(f'  anc{i} <{node.tag_name}> onclick={node.get_attribute("onclick")} html={ (node.get_attribute("outerHTML") or "")[:260] }')
    # The year filter (연도 선택) – find the select / list options
    print('\n=== year filter ===')
    sels = d.find_elements(By.TAG_NAME, 'select')
    print('selects:', len(sels))
    for s in sels:
        print('  select outerHTML', (s.get_attribute('outerHTML') or '')[:200])
    # look for any element with onclick referencing a year (2023) or goPage/search
    for el in d.find_elements(By.XPATH, "//*[@onclick]"):
        oc = el.get_attribute('onclick') or ''
        if re.search(r'2023|goYear|search|fnSearch|year', oc, re.I):
            print('  YR-OC', repr((el.text or '').strip()[:25]), '|', oc[:90])
finally:
    d.quit()
