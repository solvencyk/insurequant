# -*- coding: utf-8 -*-
"""현대해상: iterate the 연도 선택 dropdown (2023..2026), read each ir_detail row's
title/date + doBizFileDownload paths, and verify the /data/.. URL is downloadable."""
import sys, time, re, json
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import requests

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,6000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
PATH_RE = re.compile(r"doBizFileDownload\('([^']+)'\)")

def read_rows():
    rows=[]
    for det in d.find_elements(By.CSS_SELECTOR, 'div.ir_detail'):
        txt = det.text.strip().split('\n')
        title = txt[0] if txt else ''
        date = ''
        for ln in txt:
            if re.match(r'\d{4}-\d{2}-\d{2}', ln):
                date=ln; break
        files={}
        for a in det.find_elements(By.CSS_SELECTOR, 'a.btn'):
            label=a.text.strip()
            oc=a.get_attribute('onclick') or ''
            m=PATH_RE.search(oc)
            if m: files[label]=m.group(1)
        rows.append({'title':title,'date':date,'files':files})
    return rows

try:
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M'); time.sleep(7)
    d.execute_script("goMenu('101641');"); time.sleep(8)
    result={}
    for yr in ['2026','2025','2024','2023']:
        sel = Select(d.find_element(By.ID,'rstbzYear'))
        sel.select_by_value(yr)
        # onchange fnSearchRstbzData should fire; give it time
        time.sleep(5)
        rows=read_rows()
        result[yr]=rows
        print(f'\n=== YEAR {yr}: {len(rows)} rows ===')
        for r in rows:
            print(' ', r['title'],'|',r['date'],'|', {k:v.split("/")[-1] for k,v in r['files'].items()})
    # verify one download via requests
    print('\n--- verify download ---')
    samp=None
    for yr in result:
        for r in result[yr]:
            if 'Factsheet' in r['files']:
                samp=r['files']['Factsheet']; break
        if samp: break
    if samp:
        url='https://www.hi.co.kr'+samp
        hh={'User-Agent':'Mozilla/5.0','Referer':'https://www.hi.co.kr/serviceAction.do'}
        rr=requests.get(url,headers=hh,timeout=60)
        print('GET',url,'->',rr.status_code,'bytes',len(rr.content),'ctype',rr.headers.get('Content-Type'))
finally:
    d.quit()
