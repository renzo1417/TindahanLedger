"""Capture reproducible intermediate frames for the landing's connected scenes."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from check_landing import ARTIFACTS, local_server, ready


def settle_scroll(page, scene, fraction):
    page.evaluate('''({scene, fraction}) => {
        const trigger = ScrollTrigger.getById(scene);
        const target = Math.max(0, Math.min(document.documentElement.scrollHeight - innerHeight,
            trigger.vars.once ? trigger.start + 40 : trigger.start + (trigger.end - trigger.start) * fraction));
        scrollTo(0, target);
        ScrollTrigger.update();
        if (trigger.getTween()) trigger.getTween().progress(1);
        if (trigger.animation) {
            if (trigger.vars.once) trigger.animation.pause();
            trigger.animation.progress(fraction);
        }
        ScrollTrigger.getAll().filter(item => item !== trigger && item.vars.once && scrollY >= item.start)
            .forEach(item => item.animation && item.animation.progress(1));
    }''', {'scene': scene, 'fraction': fraction})
    page.wait_for_function('''({scene, fraction}) => {
        const trigger = ScrollTrigger.getById(scene);
        const progress = trigger.vars.once ? trigger.animation.progress() : trigger.progress;
        return Math.abs(progress - fraction) < 0.015;
    }''', arg={'scene': scene, 'fraction': fraction})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--mobile', action='store_true')
    args = parser.parse_args()
    output = ARTIFACTS / 'connected'
    output.mkdir(parents=True, exist_ok=True)
    with local_server() as address, sync_playwright() as playwright:
        browser_type = getattr(playwright, args.browser)
        browser = browser_type.launch(channel='chrome') if args.browser == 'chromium' and not Path(browser_type.executable_path).exists() else browser_type.launch()
        page = browser.new_page(viewport={'width': 390, 'height': 844} if args.mobile else {'width': 1366, 'height': 768})
        prefix = args.browser + ('-mobile' if args.mobile else '')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: print(message.text, flush=True) if message.type in ('warning', 'error') else None)
        ready(page, address)
        page.wait_for_function("performance.now() > 1400 && document.fonts.status === 'loaded'")
        page.screenshot(path=str(output / f'{prefix}-hero.png'))
        print(json.dumps(page.evaluate('''() => ({height:document.documentElement.scrollHeight,
            motion:document.body.dataset.motion, proxies:document.querySelectorAll('.lp-handoff-proxy').length,
            triggers:ScrollTrigger.getAll().map(t=>({id:t.vars.id,start:t.start,end:t.end,enabled:t.enabled}))})''')), flush=True)
        scenes = ['landing-ledger-entry'] if args.mobile else ['landing-ledger']
        scenes += ['landing-stock-backdrop', 'landing-daily', 'landing-closing']
        for scene in scenes:
            if not page.evaluate('(id) => !!ScrollTrigger.getById(id)', scene):
                raise AssertionError(f'Missing scene: {scene}')
            for fraction in [0, 0.25, 0.5, 0.75, 1]:
                settle_scroll(page, scene, fraction)
                page.screenshot(path=str(output / f'{prefix}-{scene}-{int(fraction*100):03}.png'))
        if not args.mobile:
            settle_scroll(page, 'landing-ledger', 1)
            page.locator('[data-item="itlog"]').click()
            page.locator('[data-item="kape"]').click()
            page.locator('#ledger-demo .lp-ledger').scroll_into_view_if_needed()
            page.evaluate("window.scrollBy(0, 60)")
            page.wait_for_timeout(450)
            page.screenshot(path=str(output / f'{prefix}-interactive-ledger.png'))
            settle_scroll(page, 'landing-stock-backdrop', 0.65)
            page.locator('#stock-days').fill('3')
            page.locator('#stock-days').dispatch_event('input')
            page.wait_for_timeout(500)
            page.screenshot(path=str(output / f'{prefix}-interactive-stock.png'))
            settle_scroll(page, 'landing-daily', 1)
            page.locator('#daily-overview .lp-day-flow').scroll_into_view_if_needed()
            page.locator('.lp-tape-row').first.focus()
            page.wait_for_timeout(250)
            page.screenshot(path=str(output / f'{prefix}-interactive-daily.png'))
        assert not errors, errors
        page.close()
        browser.close()


if __name__ == '__main__':
    main()
