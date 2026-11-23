"""Browser acceptance checks against a disposable, explicitly seeded database.

Requires CHECK_USERNAME/CHECK_PASSWORD. Never point this at a real store:
the checkout checks intentionally create classroom sales.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--output', type=Path, help='Optional directory for screenshots and the check report.')
    args = parser.parse_args()
    if not args.base_url.startswith('http://127.0.0.1:'):
        raise SystemExit('Browser write checks are restricted to a local preview.')
    username, password = os.environ['CHECK_USERNAME'], os.environ['CHECK_PASSWORD']
    output = args.output or Path(__file__).resolve().parents[2] / '.cache' / 'ui-check'
    output.mkdir(parents=True, exist_ok=True)
    report, errors = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1366, 'height': 900}, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.base_url+'/login/')
        page.locator('[name="identifier"]').fill(username)
        page.locator('[name="password"]').fill(password)
        page.locator('#login-submit-btn').click()
        page.wait_for_url('**/home/')
        routes = {'overview': '/home/', 'customers': '/utang/', 'inventory': '/inventory/',
                  'new-product': '/inventory/register/', 'new-customer': '/utang/register/',
                  'expiry': '/expiry/', 'reports': '/reports/', 'reminders': '/reminders/',
                  'profile': '/profile/', 'settings': '/settings/', 'pos': '/pos/'}
        page.goto(args.base_url+'/inventory/')
        routes['product-detail'] = page.locator('.record-link').first.get_attribute('href')
        page.goto(args.base_url+'/utang/')
        routes['customer-detail'] = page.locator('.customer-table .record-link').first.get_attribute('href')
        for width, height, label in [(1366, 900, 'desktop'), (820, 1100, 'tablet'), (390, 844, 'mobile')]:
            page.set_viewport_size({'width': width, 'height': height})
            for name, route in routes.items():
                response = page.goto(args.base_url+route)
                assert response.status == 200, (route, response.status)
                page.locator('.workspace-content h1').wait_for()
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
                assert not overflow, f'Page overflows at {width}px: {name}'
                missing_labels = page.locator('.workspace input:visible:not([type=hidden]):not([type=checkbox]):not([type=radio]), .workspace select:visible, .workspace textarea:visible').evaluate_all('elements => elements.filter(el => !el.labels?.length && !el.getAttribute("aria-label")).map(el => el.id)')
                assert not missing_labels, (name, missing_labels)
                page.screenshot(path=str(output/f'{label}-{name}.png'), full_page=True)
                report.append({'screen': name, 'width': width, 'status': response.status})
        page.goto(args.base_url+'/home/')
        page.keyboard.press('Control+k')
        search = page.locator('#search-modal')
        assert search.is_visible()
        page.locator('#global-search-input').fill('Pancit')
        page.locator('#global-search-results a').first.wait_for()
        for _ in range(8):
            page.keyboard.press('Tab')
            assert page.evaluate('document.activeElement.closest("dialog")?.id') == 'search-modal'
        page.keyboard.press('Escape')
        assert not search.is_visible()
        page.get_by_role('button', name='More', exact=True).click()
        assert page.locator('#more-modal').is_visible()
        page.locator('#more-modal').get_by_role('link', name='Financial reports', exact=True).click()
        page.wait_for_url('**/reports/')
        page.goto(args.base_url+'/pos/')
        page.get_by_role('button', name='Add Pancit Canton', exact=False).click()
        page.locator('#pos-search').fill('water')
        assert page.locator('#basket-count').inner_text() == '1'
        page.locator('#open-basket').click()
        assert page.locator('#basket-dialog').evaluate('el => el.matches(":modal")')
        page.locator('#cash-tendered').fill('100')
        page.screenshot(path=str(output/'mobile-basket.png'), full_page=True)
        page.locator('#checkout-button').click()
        page.wait_for_url('**/pos/receipts/*/')
        assert 'Sukli: ₱85.00' in page.locator('.receipt-paper').inner_text()
        page.goto(args.base_url+'/pos/')
        assert page.locator('#basket-count').inner_text() == '0', 'Successful checkout must clear saved basket'
        page.set_viewport_size({'width': 1366, 'height': 900})
        page.locator('#pos-search').fill('water')
        page.get_by_role('button', name='Add Bottled water', exact=False).click()
        page.locator('[name="payment_method"][value="Utang"]').check()
        customer_id = page.locator('#pos-customer option').nth(1).get_attribute('value')
        page.locator('#pos-customer').select_option(customer_id)
        due = datetime.now(ZoneInfo('Asia/Manila')).date()+timedelta(days=7)
        page.locator('#pos-due-date').fill(due.isoformat())
        page.locator('#checkout-button').click()
        page.wait_for_url('**/pos/receipts/*/')
        assert 'Recorded in' in page.locator('.receipt-paper').inner_text()
        page.goto(args.base_url+'/pos/')
        page.get_by_role('button', name='Add Bottled water', exact=False).click()
        page.locator('#cash-tendered').fill('20')
        page.route('**/pos/checkout/', lambda route: route.abort(), times=1)
        page.locator('#checkout-button').click()
        page.get_by_role('button', name='Retry checkout', exact=True).wait_for()
        assert page.locator('#cash-tendered').is_disabled()
        page.reload()
        page.get_by_role('button', name='Retry checkout', exact=True).wait_for()
        page.locator('#checkout-button').click()
        page.wait_for_url('**/pos/receipts/*/')
        assert not errors, errors
        browser.close()
    (output/'report.json').write_text(json.dumps({'screens': report, 'javascript_errors': errors,
        'flows': ['search and focus containment', 'mobile More navigation', 'cash checkout', 'utang checkout', 'interrupted checkout retry']}, indent=2), encoding='utf-8')
    print(f'Browser checks passed: {len(report)} screen/viewport combinations and 5 interaction flows.')
    print(f'Screenshots: {output}')


if __name__ == '__main__':
    main()
