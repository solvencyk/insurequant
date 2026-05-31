# -*- coding: utf-8 -*-
"""Inspect doBizFileDownload JS body + try a real headless click download."""
import sys, re, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

STAGE = Path('artifacts/ir_research/_tmp/hi_dl').resolve()
STAGE.mkdir(parents=True, exist_ok=True)

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,6000')
opts.add_argument('--lang=ko-KR')
opts.add_experimental_option('prefs', {
    'download.default_directory': str(STAGE),
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True,
    'plugins.always_open_pdf_externally': True,
})
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
try:
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M')
    WebDriverWait(d,25).until(lambda x: x.execute_script("return typeof goMenu==='function';"))
    d.execute_script("goMenu('101641');")
    WebDriverWait(d,25).until(lambda x: len(x.find_elements(By.CSS_SELECTOR,'div.ir_item'))>0)
    # function body
    body = d.execute_script("return typeof doBizFileDownload==='function' ? doBizFileDownload.toString() : 'NOFN';")
    print('=== doBizFileDownload ===')
    print(body[:900])
    # enable CDP download
    d.execute_cdp_cmd('Page.setDownloadBehavior', {'behavior':'allow','downloadPath':str(STAGE)})
    Select(d.find_element(By.ID,'rstbzYear')).select_by_value('2025'); time.sleep(4)
    item = d.find_elements(By.CSS_SELECTOR,'div.ir_item')[0]
    btn = item.find_element(By.XPATH, ".//a[.//span[normalize-space(text())='Factsheet']]")
    before={f.name for f in STAGE.glob('*')}
    print('clicking Factsheet of', item.find_element(By.CSS_SELECTOR,'div.ir_title').text)
    d.execute_script("arguments[0].click();", btn)
    got=None
    for _ in range(40):
        time.sleep(1)
        if any(f.name.endswith('.crdownload') for f in STAGE.glob('*')):
            continue
        new=[f for f in STAGE.glob('*') if f.name not in before and not f.name.endswith('.crdownload')]
        if new:
            got=max(new,key=lambda p:p.stat().st_mtime); break
    if got:
        print('DOWNLOADED', got.name, got.stat().st_size,'bytes')
    else:
        print('NO DOWNLOAD; staging dir:', [f.name for f in STAGE.glob('*')])
        # check for new tabs / current url
        print('windows', len(d.window_handles), 'url', d.current_url)
finally:
    d.quit()
