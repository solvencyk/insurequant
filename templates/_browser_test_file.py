from playwright.sync_api import sync_playwright

file_url = 'file:///' + r'c:/Users/sangwook.cho/Desktop/insurequant/templates/index.html'.replace('\\', '/')
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on('pageerror', lambda e: errors.append('pageerror:' + str(e)))
    page.on('console', lambda msg: errors.append(f'console:{msg.type}:{msg.text}') if msg.type in ('error','warning') else None)
    page.goto(file_url, wait_until='load')
    page.wait_for_timeout(2000)
    header = page.locator('header').count()
    body_text = page.locator('body').inner_text()[:200]
    cells = page.locator('#map .cell').count()
    print('file_url', file_url)
    print('header_count', header)
    print('body_preview', body_text.replace(chr(10),' | '))
    print('cells', cells)
    print('errors', errors[:15])
    browser.close()
