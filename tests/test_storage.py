exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Saving blocked (the owner's Brave, Oct 2026: "Frenzy and Daily change nothing"; the ?taps log showed the pick arrive and the card read back
# Stage 1: Shields blocked the site's data, so every localStorage read and write threw; the progress and the pet were lost the same way).
# Here every touch of localStorage / sessionStorage throws a SecurityError, as in a browser that blocks the site's data: the page runs, Strike's
# picks stick for the visit, the lock works, Settings says saving is blocked. A normal browser: no note. Screenshot: tests/out/storage_settings_he.png

BLOCK = """(() => { for (const n of ['localStorage', 'sessionStorage']) Object.defineProperty(window, n, { configurable: true, get() { throw new DOMException('The document is sandboxed and lacks the allow-same-origin flag.', 'SecurityError'); } }); })();"""

async def blocked(b, he):
    tag = 'HE' if he else 'EN'
    ctx = await b.new_context(viewport={'width': 412, 'height': 915}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(BLOCK + "window.__graspLang = '" + ('he' if he else 'en') + "'; window.__graspNoAutoFs = true;")
    await page.goto(BASE + '/'); await page.wait_for_function("typeof engine !== 'undefined' && typeof mb !== 'undefined'", timeout=15000); await page.wait_for_timeout(800)
    check(tag + ': storage blocked: the page runs (no page errors), LS_ERR names it', not errs and await page.evaluate("LS_ERR") == 'SecurityError', [errs, await page.evaluate("LS_ERR")])
    if he: await page.evaluate("setLang('he')"); await page.wait_for_timeout(200)
    for chip, sub in (('#frenzyChip', 'frenzy'), ('#dailyBtn', 'dailyShort')):
        await page.tap(chip); await page.wait_for_timeout(400)
        s = await page.evaluate("({ on: [...document.querySelectorAll('#heroModes [aria-pressed=\"true\"]')].map(e => e.id), sub: $('heroSub').textContent, picked: $('hero').classList.contains('picked') })")
        check(tag + ': blocked: a tap on %s picks it (pressed, the card says so, Play calls)' % chip, s['on'] == [chip[1:]] and s['sub'] == await page.evaluate("t('%s')" % sub) and s['picked'], s)
    await page.tap('#heroPlay'); ok = await wait(page, "typeof daily !== 'undefined' && daily.on && mode !== 'none'", 8000)
    check(tag + ': blocked: Play plays the picked one (the Daily)', ok, await page.evaluate("[mode, gameMode, daily.on]"))
    await page.evaluate("goHome()"); await page.wait_for_timeout(800)
    check(tag + ': blocked: back Home, the Daily is still picked (kept for the visit)', await page.evaluate("heroModeGet()") == 'daily')
    await page.tap('#settingsBtn'); await page.wait_for_timeout(500)
    n = await page.evaluate("(() => { const e = $('lsNote'), r = e.getBoundingClientRect(); return { shown: !e.hidden && r.height > 0, text: e.textContent }; })()")
    check(tag + ': Settings says saving is blocked, in one line', n['shown'] and n['text'] == await page.evaluate("t('lsBlocked')"), n)
    await page.screenshot(path=OUT + 'storage_settings_%s.png' % tag.lower())
    await page.evaluate("h2More(false)"); await page.wait_for_timeout(300)
    await page.evaluate("mbRoom('little')"); await wait(page, "mb.room === 'little' && !mb.swiping", 4000); await page.tap('#lockBtn'); await page.wait_for_timeout(200)
    check(tag + ': blocked: the Little ones lock locks (for the visit)', await page.evaluate("mbLocked() && $('lockBtn').getAttribute('aria-pressed') === 'true'"))
    check(tag + ': blocked: still no page errors', not errs, errs); await ctx.close()

async def normal(b):
    ctx, page, errs = await page_for(b, '/', False, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(600)
    check('a normal browser: LS_ERR empty, no note in Settings, the real localStorage', await page.evaluate("LS_ERR === '' && $('lsNote').hidden && localStorage instanceof Storage"))
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        await normal(b)
        for he in (True, False): await blocked(b, he)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
