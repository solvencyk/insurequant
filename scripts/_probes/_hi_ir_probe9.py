# -*- coding: utf-8 -*-
"""Debug: after selecting a year, dump exactly what read_rows sees (title + files)."""
import sys, time, re, json
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,6000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
PATH_RE = re.compile(r"doBizFileDownload\('([^']+)'\)")
try:
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M')
    WebDriverWait(d,25).until(lambda x: x.execute_script("return typeof goMenu==='function';"))
    d.execute_script("goMenu('101641');")
    WebDriverWait(d,25).until(lambda x: len(x.find_elements(By.CSS_SELECTOR,'div.ir_detail'))>0)
    for yr in ['2025','2023']:
        Select(d.find_element(By.ID,'rstbzYear')).select_by_value(yr); time.sleep(4)
        dets=d.find_elements(By.CSS_SELECTOR,'div.ir_detail')
        print(f'\n=== YEAR {yr}: {len(dets)} ir_detail ===')
        for det in dets:
            full=det.text.strip().replace(chr(10),' | ')
            print(' RAW:', full[:120])
            for a in det.find_elements(By.CSS_SELECTOR,'a.btn'):
                m=PATH_RE.search(a.get_attribute('onclick') or '')
                print('      btn', repr(a.text.strip()), '->', (m.group(1) if m else None))
finally:
    d.quit()
