# -*- coding: utf-8 -*-
"""Probe DB IR list rows: get the title->detail navigation mechanism, then open one
detail page to see download (xlsx/pdf) links. Also enumerate all rows across pages."""
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
    # Inspect the table rows: find anchors / tr with onclick
    print('--- table rows ---')
    rows = d.find_elements(By.XPATH, "//table//tr")
    print('tr count', len(rows))
    for tr in rows[:25]:
        links = tr.find_elements(By.XPATH, ".//a")
        for a in links:
            t=(a.text or '').strip(); h=a.get_attribute('href') or ''; oc=a.get_attribute('onclick') or ''
            if t:
                print('  ROW', repr(t[:45]),'| href=',h[:70],'| oc=',oc[:90])
    # Click the first "Fact sheet" row to view detail download links
    print('\n--- click first Fact sheet ---')
    cand = d.find_elements(By.XPATH, "//a[contains(normalize-space(.),'Fact sheet') or contains(normalize-space(.),'경영실적')]")
    print('candidates', [(c.text.strip()[:30]) for c in cand[:6]])
    if cand:
        before = d.current_url
        d.execute_script("arguments[0].click();", cand[0]); time.sleep=getattr(time,'sleep'); time.sleep(6)
        print('after click url', d.current_url)
        print('windows', len(d.window_handles))
        # check for download links on detail
        for a in d.find_elements(By.XPATH, "//a | //*[@onclick]"):
            t=(a.text or '').strip(); h=a.get_attribute('href') or ''; oc=a.get_attribute('onclick') or ''
            blob=(h+oc).lower()
            if '.pdf' in blob or '.xls' in blob or 'download' in blob or 'filedown' in blob or '다운' in t or '첨부' in t:
                print('  DL', repr(t[:40]),'| href=',h[:100],'| oc=',oc[:120])
        body=d.find_element(By.TAG_NAME,'body').text
        print('--- detail body (first 1200) ---')
        print(body[:1200])
finally:
    d.quit()
