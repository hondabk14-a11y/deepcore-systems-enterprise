"""Optional browser smoke test; Chromium + playwright required."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright
from telemetry_server import Handler

class QuietHandler(Handler):
    def log_message(self, *_): pass

server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(Path(__file__).parent)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.goto((Path(__file__).parent/'live.html').as_uri(),wait_until='load')
        assert page.locator('#connectionText').inner_text()=='DEMO'
        assert page.locator('#totalNodes').inner_text()=='1,248'
        assert page.locator('.node-circle').count()==12
        assert page.locator('#events .event').count()==6
        page.locator('#nodeSearch').fill('N-812')
        assert 'N-812' in page.locator('#selectedNode').inner_text()
        page.locator('#nav button[data-view="risk"]').click()
        assert page.locator('#viewPath').inner_text()=='RISK'
        page.locator('#eventFilter').select_option('RISK')
        assert page.locator('#events .event').count()==1
        page.screenshot(path='/mnt/data/Deepcore-Live-Preview.png',full_page=True)
        page.locator('#source').select_option('live')
        page.wait_for_function("document.querySelector('#connectionText').textContent === 'ERROR'",timeout=6000)
        assert page.locator('#totalNodes').inner_text()=='--', 'Must not preserve demo data in live failure'
        assert not errors, errors
        print('Browser smoke PASS: page renders, node search, navigation, event filter, error handling')
        browser.close()
finally:
    server.shutdown();server.server_close()