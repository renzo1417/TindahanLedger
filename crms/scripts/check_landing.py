"""Browser acceptance checks and screenshots for the fictional landing demos.

Run with the project's Python environment after installing Playwright browsers:
    python scripts/check_landing.py --capture-overview
    python scripts/check_landing.py

Only local pages and fictional, browser-local state are exercised.
"""
import argparse
import base64
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'test-results' / 'landing'
if (ROOT / 'test-results' / 'browsers').is_dir():
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(ROOT / 'test-results' / 'browsers'))


@contextmanager
def local_server():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    address = f'http://127.0.0.1:{port}'
    environment = dict(os.environ, USE_LOCAL_DB='true')
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(
            [sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload'],
            cwd=ROOT, env=environment, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        try:
            for _ in range(100):
                try:
                    with urlopen(address + '/welcome/', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    if process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read().decode(errors='replace'))
                    time.sleep(0.1)
            else:
                raise RuntimeError('Local Django server did not start within 10 seconds')
            yield address
        finally:
            process.terminate()
            process.wait(timeout=10)


def capture_overview(browser, address):
    page = browser.new_page(viewport={'width': 1530, 'height': 1120}, device_scale_factor=1)
    page.goto(address + '/home/', wait_until='networkidle')
    # Anonymous /home/ is the app's existing sample-data view. Crop the actual
    # content, excluding account details, navigation and contact information.
    page.add_style_tag(content='* { animation:none !important; transition:none !important; } [class*="anim-"] { opacity:1 !important; transform:none !important; } .section-header { display:none !important; }')
    content = page.locator('.container-app-fluid')
    expect(content).to_be_visible()
    image = page.screenshot(clip={**content.bounding_box(), 'height': 860, 'width': 1180}, type='png')
    destination = ROOT / 'static/images/landing/overview.webp'
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = page.evaluate('''async (encoded) => {
        const image = new Image();
        image.src = 'data:image/png;base64,' + encoded;
        await image.decode();
        const canvas = document.createElement('canvas');
        canvas.width = image.width; canvas.height = image.height;
        canvas.getContext('2d').drawImage(image, 0, 0);
        return canvas.toDataURL('image/webp', 0.86).split(',')[1];
    }''', base64.b64encode(image).decode())
    destination.write_bytes(base64.b64decode(encoded))
    print(f'Captured real sample overview: {destination.name} ({destination.stat().st_size} bytes)', flush=True)
    page.close()


def ready(page, address, suffix=''):
    page.goto(address + '/' + suffix, wait_until='networkidle')
    expect(page.locator('body')).to_have_attribute('data-motion-ready', 'true')


def check_interactions(browser, address):
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: print(f'Browser {message.type}: {message.text}', flush=True) if message.type in ('error', 'warning') else None)
    ready(page, address)
    expect(page.locator('.pin-spacer')).to_have_count(0)
    page.get_by_role('link', name='Try the ledger').click()
    page.wait_for_function("Math.abs(document.getElementById('ledger-demo').getBoundingClientRect().top - (document.querySelector('.lp-header').offsetHeight + 24)) < 6")
    stages = page.get_by_role('group', name='Ledger stages')
    expect(stages.get_by_role('button', name=re.compile('^Utang'))).to_have_attribute('aria-pressed', 'true')
    page.mouse.wheel(0, 350)
    expect(stages.get_by_role('button', name=re.compile('^Bayad'))).to_have_attribute('aria-pressed', 'true')
    page.mouse.wheel(0, 350)
    expect(stages.get_by_role('button', name=re.compile('^Balanse'))).to_have_attribute('aria-pressed', 'true')
    page.get_by_role('link', name='Try the ledger').click()
    page.wait_for_function("Math.abs(document.getElementById('ledger-demo').getBoundingClientRect().top - (document.querySelector('.lp-header').offsetHeight + 24)) < 6")
    stages.get_by_role('button', name=re.compile('^Utang')).click()
    expect(page.get_by_text('Wala pang naitalang bayad.', exact=False)).to_be_visible()
    record = page.get_by_role('button', name=re.compile('^Record sample'))
    record.click()
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    expect(page.locator('#demo-payment-empty')).to_be_hidden()
    expect(page.get_by_role('button', name='Sample payment recorded ✓')).to_be_disabled()
    # Repeated activation of the DOM button cannot duplicate a payment.
    page.get_by_role('button', name='Sample payment recorded ✓').evaluate('(button) => { for(let i=0;i<5;i++) button.click(); }')
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    page.evaluate('window.scrollBy(0, 260)')
    expect(stages.get_by_role('button', name=re.compile('^Bayad'))).to_have_attribute('aria-pressed', 'true')
    page.get_by_role('button', name='Reset', exact=True).click()
    expect(page.locator('#demo-balance')).to_have_text('₱350.00')
    page.get_by_role('button', name=re.compile(r'^Itlog')).click()
    expect(page.locator('#demo-balance')).to_have_text('₱398.00')
    stages.get_by_role('button', name=re.compile('^Balanse')).click()
    expect(page.locator('#demo-balance')).to_have_text('₱248.00')
    page.get_by_role('button', name='Reset', exact=True).click()
    expect(page.locator('#demo-balance')).to_have_text('₱350.00')
    stages.get_by_role('button', name=re.compile('^Balanse')).click()
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    page.get_by_role('navigation', name='Sections', exact=True).get_by_role('link', name='Ang stock').click()
    page.get_by_role('button', name='Arrival order', exact=True).click()
    expect(page.get_by_role('list', name='Sellable sample batches').get_by_role('listitem').first).to_contain_text('BT-2026-072')
    page.get_by_role('button', name='Expiry priority', exact=True).click()
    expect(page.get_by_role('list', name='Sellable sample batches').get_by_role('listitem').first).to_contain_text('BT-2026-081')
    expect(page.get_by_role('group', name='Expired sample stock')).to_contain_text('Huwag ibenta')
    page.locator('#stock-days').fill('3')
    page.locator('#stock-days').dispatch_event('input')
    expect(page.get_by_role('group', name='Expired sample stock')).to_contain_text('BT-2026-081')
    page.locator('#stock-days').fill('0')
    page.locator('#stock-days').dispatch_event('input')
    expect(page.get_by_role('list', name='Sellable sample batches').get_by_role('listitem').first).to_contain_text('BT-2026-081')
    page.get_by_role('button', name='Arrival order', exact=True).focus()
    page.keyboard.press('Enter')
    expect(page.get_by_role('button', name='Arrival order', exact=True)).to_have_attribute('aria-pressed', 'true')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('body')).to_have_attribute('data-motion', 'reduced')
    expect(page.locator('.pin-spacer')).to_have_count(0)
    page.emulate_media(reduced_motion='no-preference')
    expect(page.locator('body')).to_have_attribute('data-motion', 'full')
    page.set_viewport_size({'width': 390, 'height': 844})
    expect(page.locator('.pin-spacer')).to_have_count(0)
    page.set_viewport_size({'width': 1366, 'height': 700})
    expect(page.locator('.pin-spacer')).to_have_count(0)
    page.set_viewport_size({'width': 390, 'height': 844})
    expect(page.locator('.pin-spacer')).to_have_count(0)
    page.get_by_role('navigation', name='Sections', exact=True).get_by_role('link', name='Mga tanong').click()
    question = page.locator('summary').filter(has_text='Totoong customer data ba ang demo?')
    question.focus()
    page.keyboard.press('Enter')
    expect(page.get_by_text('Hindi. Sample data lang ito;', exact=False)).to_be_visible()
    assert not errors, errors
    page.close()


def check_layouts(browser, address, name):
    for width, height in [(360, 800), (390, 844), (768, 1024), (1024, 768), (1366, 768), (1440, 900)]:
        page = browser.new_page(viewport={'width': width, 'height': height})
        ready(page, address)
        page.evaluate('''() => {
            gsap.globalTimeline.getChildren().filter(animation => !animation.scrollTrigger).forEach(animation => animation.progress(1));
            ScrollTrigger.getAll().filter(trigger => trigger.vars.once).forEach(trigger => trigger.animation && trigger.animation.progress(1));
        }''')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{name}: overflow at {width}'
        assert page.locator('.lp-product-preview .lp-preview-image-wrap img').evaluate('(img) => img.complete && img.naturalWidth > 0'), 'Missing overview capture'
        assert page.evaluate("document.fonts.check('600 24px \"Plus Jakarta Sans\"')"), 'Font did not load'
        heading = page.get_by_role('heading', level=1)
        assert ' '.join(heading.inner_text().split()) == 'Bawat galaw. Malinaw.'
        if width == 1366:
            actions = page.locator('.lp-hero-actions').bounding_box()
            assert actions['y'] + actions['height'] < height, 'Hero CTA is below the fold'
            assert page.evaluate('document.documentElement.scrollHeight <= 5300'), 'The denser story grew longer than the baseline'
        page.locator('img').evaluate_all("images => Promise.all(images.map(img => { img.loading = 'eager'; return img.decode(); }))")
        page.screenshot(path=str(ARTIFACTS / f'{name}-{width}.png'), full_page=True)
        page.close()


def check_fallbacks(browser, address):
    context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
    page = context.new_page()
    page.goto(address + '/welcome/')
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    expect(page.get_by_role('group', name='Ledger stages')).to_be_hidden()
    expect(page.get_by_role('link', name='Try the ledger')).to_be_visible()
    context.close()
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    page.route('**/vendor/**', lambda route: route.abort())
    ready(page, address)
    page.get_by_role('button', name=re.compile('^Record sample')).click()
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    page.get_by_role('button', name='Arrival order', exact=True).click()
    expect(page.get_by_role('list', name='Sellable sample batches').get_by_role('listitem').first).to_contain_text('BT-2026-072')
    page.close()
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    ready(page, address, '#inventory-story')
    expect(page.get_by_role('button', name='Expiry priority', exact=True)).to_be_in_viewport()
    page.get_by_role('navigation', name='Sections', exact=True).get_by_role('link', name='Mga tanong').click()
    page.go_back(wait_until='networkidle')
    expect(page.get_by_role('button', name='Expiry priority', exact=True)).to_be_in_viewport()
    page.close()
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    pending_fonts = []
    page.route('**/fonts/landing/*.woff2', lambda route: pending_fonts.append(route))
    page.goto(address + '/welcome/', wait_until='domcontentloaded')
    expect(page.locator('body')).to_have_attribute('data-motion-ready', 'true')
    expect(page.get_by_role('heading', name='Bawat galaw. Malinaw.', exact=True)).to_be_visible()
    for route in list(pending_fonts):
        route.continue_()
    page.unroute('**/fonts/landing/*.woff2')
    page.wait_for_function("document.fonts.status === 'loaded'")
    expect(page.get_by_role('heading', name='Bawat galaw. Malinaw.', exact=True)).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    # The Windows WebKit test runtime does not expose Safari's full-keyboard
    # preference. Test skip-link focus/Enter directly there; Tab in Chrome/Firefox.
    if browser.browser_type.name == 'webkit':
        page.get_by_role('link', name='Skip to main content').focus()
    else:
        page.keyboard.press('Tab')
    expect(page.get_by_role('link', name='Skip to main content')).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('#main-content')).to_be_focused()
    page.get_by_role('group', name='Ledger stages').get_by_role('button', name=re.compile('^Utang')).click()
    page.locator('.lp-account').get_by_role('link', name='Sign in', exact=True).click()
    expect(page).to_have_url(re.compile('/login/'))
    page.go_back(wait_until='domcontentloaded')
    expect(page.locator('body')).to_have_attribute('data-motion-ready', 'true')
    page.get_by_role('button', name=re.compile('^Record sample')).click()
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    page.close()


def check_connected_motion(browser, address):
    page = browser.new_page(viewport={'width': 1366, 'height': 768})
    ready(page, address)
    expect(page.locator('.lp-handoff-proxy')).to_have_count(0)
    expect(page.locator('.pin-spacer')).to_have_count(0)
    assert page.locator('.lp-purchase').evaluate_all("rows => rows.every(row => Number(getComputedStyle(row).opacity) > 0)"), 'Purchase rows must remain visible'
    page.locator('.lp-closing-actions a').first.focus()
    expect(page.locator('.lp-closing-actions')).to_have_css('opacity', '1')
    page.close()

    options = {'viewport': {'width': 390, 'height': 844}, 'has_touch': True}
    if browser.browser_type.name != 'firefox':
        options['is_mobile'] = True
    context = browser.new_context(**options)
    page = context.new_page()
    ready(page, address)
    page.get_by_role('group', name='Ledger stages').get_by_role('button', name=re.compile('^Utang')).tap()
    page.get_by_role('button', name=re.compile('^Record sample')).tap()
    expect(page.locator('#demo-balance')).to_have_text('₱200.00')
    page.get_by_role('button', name='Arrival order', exact=True).tap()
    expect(page.get_by_role('list', name='Sellable sample batches').get_by_role('listitem').first).to_contain_text('BT-2026-072')
    expect(page.get_by_role('group', name='Expired sample stock')).to_contain_text('Huwag ibenta')
    expect(page.locator('.lp-handoff-proxy')).to_have_count(0)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-overview', action='store_true')
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit', 'all'], default='all')
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with local_server() as address, sync_playwright() as playwright:
        names = ['chromium'] if args.capture_overview else ['chromium', 'firefox', 'webkit'] if args.browser == 'all' else [args.browser]
        for name in names:
            browser_type = getattr(playwright, name)
            if name == 'chromium' and not Path(browser_type.executable_path).exists():
                browser = browser_type.launch(channel='chrome')
            else:
                browser = browser_type.launch()
            try:
                if args.capture_overview:
                    capture_overview(browser, address)
                else:
                    check_interactions(browser, address)
                    check_layouts(browser, address, name)
                    check_fallbacks(browser, address)
                    check_connected_motion(browser, address)
                    print(f'{name}: interactions, six layouts, fallbacks, connected motion, and touch passed', flush=True)
            finally:
                browser.close()


if __name__ == '__main__':
    main()
