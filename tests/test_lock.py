exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# The Little ones lock + the swipes between the rooms + a tap with a finger resting on the edge (the owner, Oct 2026: "the swipe back from Little ones
# doesn't work in Brave"; "a lock at the top in Little ones: locked, no way back; unlocked, as before"; the QA sweep: with a holding finger on the
# screen's edge the browser fires no click, so the house and the stickers were dead). Real touches through CDP (scroll-snap, multi-touch).
# Screenshots: tests/out/lock_*.png

async def touches(page):
    cdp = await page.context.new_cdp_session(page)
    async def send(kind, pts): await cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': pts})
    async def swipe(x0, x1, y, steps=8):
        await send('touchStart', [{'x': x0, 'y': y}])
        for k in range(1, steps + 1): await send('touchMove', [{'x': x0 + (x1 - x0) * k / steps, 'y': y}]); await asyncio.sleep(0.016)
        await send('touchEnd', [])
    return send, swipe

ST = "({ room: mb.room, lock: $('lockBtn').getAttribute('aria-pressed'), shown: getComputedStyle($('lockBtn')).display !== 'none', sl: Math.round($('mbRooms').scrollLeft), big: $('bigBtn').getAttribute('aria-pressed') })"

async def rooms(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNavGuard = true; window.__graspNoAutoFs = true;")
    await page.wait_for_timeout(800); send, swipe = await touches(page)
    s = await page.evaluate(ST)
    check(tag + ': Big kids: the lock is not shown', s['room'] == 'big' and not s['shown'], s)
    await page.tap('#littleBtn'); ok = await wait(page, "mb.room === 'little' && !mb.swiping", 4000); await page.wait_for_timeout(300)
    s = await page.evaluate(ST)
    check(tag + ': Little ones: the lock shows at the top, open', ok and s['shown'] and s['lock'] == 'false', s)
    x0, x1 = (300, 60) if he else (90, 330)  # (a swipe toward Big kids: the finger moves to the start side's opposite)
    await swipe(x0, x1, 500); ok = await wait(page, "mb.room === 'big'", 3000); await page.wait_for_timeout(500)
    check(tag + ': a swipe back on the Little ones pager\'s first page: Big kids (the switch follows)', ok and (await page.evaluate(ST))['big'] == 'true', await page.evaluate(ST))
    # the rooms follow the finger (the owner: "the swipe still isn't smooth"): mid-drag they have moved and the background is half way; a short drag goes back
    await page.tap('#littleBtn'); await wait(page, "mb.room === 'little' && !mb.swiping", 4000); await page.wait_for_timeout(400)
    w = await page.evaluate("$('mbRooms').clientWidth"); mid = (x0 + x1) / 2
    await send('touchStart', [{'x': x0, 'y': 500}])
    for k in range(1, 7): await send('touchMove', [{'x': x0 + (mid - x0) * k / 6, 'y': 500}]); await asyncio.sleep(0.03)
    m = await page.evaluate("({ sl: Math.abs($('mbRooms').scrollLeft), bg: $('start').style.backgroundColor, room: mb.room })")
    check(tag + ': mid-drag: the rooms moved with the finger (no wait for the lift), the background between the two colours', w * 0.25 < m['sl'] < w * 0.85 and m['bg'].startswith('rgb(') and m['room'] == 'little', m)
    await asyncio.sleep(0.4)  # (a slow finger: no flick)
    for k in range(1, 5): await send('touchMove', [{'x': mid + (x0 - mid) * k / 4 * 0.8, 'y': 500}]); await asyncio.sleep(0.05)
    await asyncio.sleep(0.3); await send('touchEnd', [])
    ok = await wait(page, "mb.room === 'little' && Math.abs(Math.abs($('mbRooms').scrollLeft) - $('mbRooms').clientWidth) < 2 && !$('start').style.backgroundColor", 3000)
    check(tag + ': a drag let go short of half way slides back to Little ones (its own colour)', ok, await page.evaluate("[mb.room, $('mbRooms').scrollLeft, $('start').style.backgroundColor]"))
    await page.tap('#lockBtn'); await page.wait_for_timeout(200)
    s = await page.evaluate(ST)
    check(tag + ': one tap locks (the padlock shut, Big kids greyed)', s['lock'] == 'true' and await page.evaluate("$('start').classList.contains('locked') && $('bigBtn').getAttribute('aria-disabled') === 'true'"), s)
    await page.screenshot(path=OUT + 'lock_on_%s.png' % tag.lower())
    await swipe(x0, x1, 500); await page.wait_for_timeout(900)
    check(tag + ': locked: a swipe stays in Little ones', (await page.evaluate(ST))['room'] == 'little', await page.evaluate(ST))
    await page.tap('#bigBtn', force=True); await page.wait_for_timeout(600)
    check(tag + ': locked: the Big kids switch stays in Little ones (the lock nudges)', (await page.evaluate(ST))['room'] == 'little' and 'lock:nudge' in await page.evaluate("mb.log"), await page.evaluate(ST))
    await page.go_back(); await page.wait_for_timeout(700)
    check(tag + ': locked: Back stays in Little ones (on the site)', await page.evaluate("typeof mb !== 'undefined' && mb.room === 'little'"))
    await page.reload(); await page.wait_for_function("typeof mb !== 'undefined'", timeout=15000); await page.wait_for_timeout(1000)
    check(tag + ': the lock is remembered (a reload: Little ones, locked)', (await page.evaluate(ST))['room'] == 'little' and (await page.evaluate(ST))['lock'] == 'true', await page.evaluate(ST))
    await page.tap('#lockBtn'); await page.wait_for_timeout(200); await page.tap('#bigBtn'); ok = await wait(page, "mb.room === 'big'", 3000)
    check(tag + ': one tap unlocks: Big kids again; the lock hides there', ok and not (await page.evaluate(ST))['shown'], await page.evaluate(ST))
    check(tag + ': rooms: no page errors', not errs, errs); await ctx.close()

async def resting(b):
    ctx, page, errs = await page_for(b, '/animals', True, init="window.__graspNoAutoFs = true; window.__graspTapGuard = true;")
    await wait(page, "gameMode === 'animals' && mode === 'mouse'", 10000); await page.wait_for_timeout(800); send, swipe = await touches(page)
    r = await page.evaluate("(() => { const q = $('pauseBtn').getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; })()")
    edge = {'x': 4, 'y': 600, 'id': 1}; tp = {'x': r[0], 'y': r[1], 'id': 2}
    await send('touchStart', [edge]); await page.wait_for_timeout(300); await send('touchStart', [edge, tp]); await page.wait_for_timeout(90); await send('touchEnd', [tp]); await page.wait_for_timeout(500)
    check('a finger resting on the edge: a tap on the house still goes home', await page.evaluate("mode === 'none' && !$('start').hidden"), await page.evaluate("[mode, __graspMtTap.log]"))
    await send('touchEnd', [edge]); await page.wait_for_timeout(2300)
    await page.evaluate("mbRoom('little')"); await wait(page, "mb.room === 'little' && !mb.swiping", 4000); await page.wait_for_timeout(300)
    r = await page.evaluate("(() => { const q = document.querySelector('#mbPager .stk:not([hidden])').getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; })()")
    edge = {'x': 4, 'y': 760, 'id': 3}; tp = {'x': r[0], 'y': r[1], 'id': 4}
    await send('touchStart', [edge]); await page.wait_for_timeout(300); await send('touchStart', [edge, tp]); await page.wait_for_timeout(90); await send('touchEnd', [tp]); await page.wait_for_timeout(1500)
    check('a finger resting on the edge: a Little ones sticker still starts its game', await page.evaluate("mode !== 'none' || gameMode === 'busy'"), await page.evaluate("[mode, gameMode]"))
    await send('touchEnd', [edge]); await page.evaluate("goHome()"); await page.wait_for_timeout(2300)
    n0 = await page.evaluate("__graspMtTap.log.length"); await page.tap('#settingsBtn'); await page.wait_for_timeout(300)
    check('a plain one-finger tap: one click only (no extra one made)', await page.evaluate("__graspMtTap.log.length") == n0 and await page.evaluate("!$('moreSheet').hidden"))
    check('resting: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (True, False): await rooms(b, he)
        await resting(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
