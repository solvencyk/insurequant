# -*- coding: utf-8 -*-
"""Find the title element relative to div.ir_detail (title is sibling/parent text)."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
import time

opts = Options()
opts.add_argument('--headless=new'); opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage'); opts.add_argument('--window-size=1400,6000')
opts.add_argument('--lang=ko-KR')
opts.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
d = webdriver.Chrome(options=opts)
try:
    d.get('https://www.hi.co.kr/serviceAction.do?view=bin/KC/00/HHKC00000M')
    WebDriverWait(d,25).until(lambda x: x.execute_script("return typeof goMenu==='function';"))
    d.execute_script("goMenu('101641');")
    WebDriverWait(d,25).until(lambda x: len(x.find_elements(By.CSS_SELECTOR,'div.ir_detail'))>0)
    Select(d.find_element(By.ID,'rstbzYear')).select_by_value('2025'); time.sleep(4)
    det=d.find_elements(By.CSS_SELECTOR,'div.ir_detail')[0]
    # parent
    par=det.find_element(By.XPATH,'..')
    print('PARENT tag', par.tag_name, 'class', par.get_attribute('class'))
    print('PARENT outerHTML:', (par.get_attribute('outerHTML') or '')[:600])
    print('PARENT text:', par.text.replace(chr(10),' | ')[:160])
    # preceding sibling
    try:
        prev=det.find_element(By.XPATH,'preceding-sibling::*[1]')
        print('PREV-SIB tag', prev.tag_name, 'class', prev.get_attribute('class'), 'text', repr(prev.text.strip()[:60]))
    except Exception as e:
        print('no prev sib', e)
finally:
    d.quit()
