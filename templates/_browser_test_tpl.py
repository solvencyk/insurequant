import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for url in ['http://127.0.0.1:8766/index.html', 'http://127.0.0.1:8765/templates/index.html']:
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on('pageerror', lambda e: errors.append('pageerror:' + str(e)))
        page.on('console', lambda msg: errors.append(f'console:{msg.type}:{msg.text}') if msg.type=='error' else None)
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(1500)
        print('URL', url)
        print('  cells', page.locator('#map .cell').count())
        print('  eq_len', len(page.locator('#eq-chart').inner_html()))
        print('  errors', errors[:5])
        browser.close()
