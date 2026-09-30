exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Start screen: live mode previews on the cards, best-score badges, the gesture hint row, the phone snap row, camera memory, entrance.
PV = "(() => { const cs = [...document.querySelectorAll('.modes button canvas.pvc')]; return { n: cs.length, sized: cs.every(c => c.width > 0 && c.height > 0 && c.getBoundingClientRect().width > 40), shots: cs.map(c => c.toDataURL()), frames: __grasp.previews.frames, running: __grasp.previews.running }; })()"
FIT = """(() => { const st = $('start'), a = document.querySelector('#start a.link').getBoundingClientRect(), cam = $('camBtn').getBoundingClientRect(), mo = $('mouseBtn').getBoundingClientRect(), d = $('modeCard').getBoundingClientRect(), h1 = document.querySelector('.panel h1').getBoundingClientRect();
  return { H: innerHeight, W: innerWidth, bodyScroll: document.documentElement.scrollHeight <= innerHeight && scrollY === 0, startScroll: st.scrollHeight <= st.clientHeight + 1, top: h1.top, link: a.bottom, cam: [cam.top, cam.bottom], mouse: [mo.top, mo.bottom], desc: [d.top, d.bottom], dl: d.left, dr: d.right }; })()"""
ROW = """(() => { const m = document.querySelector('.modes'), r = m.getBoundingClientRect(), cs = getComputedStyle(m), bs = [...m.querySelectorAll('button')], sel = m.querySelector('[aria-pressed=true]').getBoundingClientRect();
  const dots = [...document.querySelectorAll('#modeDots i')]; return { snap: cs.scrollSnapType, scrollable: m.scrollWidth > m.clientWidth + 1, rowIn: r.left >= 0 && r.right <= innerWidth, rows: new Set(bs.map(b => Math.round(b.getBoundingClientRect().top / 20))).size,
  widths: bs.map(b => Math.round(b.getBoundingClientRect().width)), fit: bs.every(b => b.scrollWidth <= b.clientWidth + 1), selIn: sel.left >= 0 && sel.right <= innerWidth, selMid: sel.left + sel.width / 2, dots: dots.length, dotsShown: dots.length && getComputedStyle($('modeDots')).display !== 'none', on: dots.findIndex(d => d.classList.contains('on')), sl: m.scrollLeft, W: innerWidth }; })()"""
HINTS = "(() => { const li = [...document.querySelectorAll('#modeHints li')]; return { g: li.map(l => l.dataset.g), t: li.map(l => l.textContent.trim()), icons: li.every(l => l.querySelector('svg') && l.querySelector('svg').getBoundingClientRect().width > 12), rtl: li.map(l => l.querySelector('svg').getBoundingClientRect().left > l.querySelector('span').getBoundingClientRect().left) }; })()"
BESTS = "(() => { const o = {}; for (const m of ['sandbox', 'slice', 'smash', 'busy', 'strike']) { const b = document.querySelector('.modes button[data-mode=' + m + '] .best'); o[m] = b ? (b.hidden ? null : b.textContent) : 'none'; } return o; })()"
CAM = "({ label: $('camBtn').textContent.trim(), hint: $('camHint').hidden ? null : $('camHint').textContent, hintIn: (() => { const r = $('camHint').getBoundingClientRect(), b = $('camBtn').getBoundingClientRect(); return r.right <= innerWidth && r.left >= 0 && r.top < b.top + 4; })() })"

async def fresh(b, mobile, he=False, init=''):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- previews: five canvases, animating while the start screen shows, frozen once a game starts or the tab hides ----
        ctx, page, errs = await fresh(b, False)
        check('intro class on first show', await page.evaluate("$('start').classList.contains('intro')"))
        a = await page.evaluate(PV); await page.wait_for_timeout(400); c = await page.evaluate(PV)
        check('5 preview canvases, sized, one shared loop running', a['n'] == 5 and a['sized'] and a['running'], a['n'])
        check('previews animate: every canvas changes between frames', c['frames'] > a['frames'] and all(x != y for x, y in zip(a['shots'], c['shots'])), [a['frames'], c['frames']])
        fps = (c['frames'] - a['frames']) / 0.4
        check('previews throttled to about 12 fps', 6 <= fps <= 14, fps)
        await page.evaluate("Object.defineProperty(document, 'hidden', { get: () => true, configurable: true }); document.dispatchEvent(new Event('visibilitychange'))"); await page.wait_for_timeout(50)
        d = await page.evaluate(PV); await page.wait_for_timeout(300); e = await page.evaluate(PV)
        check('tab hidden: previews stop', not d['running'] and e['frames'] == d['frames'] and d['shots'] == e['shots'])
        await page.evaluate("Object.defineProperty(document, 'hidden', { get: () => false, configurable: true }); document.dispatchEvent(new Event('visibilitychange'))"); await page.wait_for_timeout(300)
        f = await page.evaluate(PV)
        check('tab back: previews run again', f['running'] and f['frames'] > e['frames'])
        await page.wait_for_timeout(1400)
        check('intro class dropped after the entrance', not await page.evaluate("$('start').classList.contains('intro')"))
        await page.click('#mouseBtn'); await page.wait_for_timeout(100)
        g = await page.evaluate(PV); await page.wait_for_timeout(400); h = await page.evaluate(PV)
        check('game started: previews stop and the canvases keep their last frame', not g['running'] and h['frames'] == g['frames'] and g['shots'] == h['shots'])
        await page.click('#homeBtn'); await page.wait_for_timeout(350)
        i = await page.evaluate(PV)
        check('home: previews run again, no intro replay', i['running'] and i['frames'] > h['frames'] and not await page.evaluate("$('start').classList.contains('intro')"))
        check('previews: no page errors', not errs, errs); await ctx.close()

        # ---- best badges ----
        ctx, page, errs = await fresh(b, False)
        bs = await page.evaluate(BESTS)
        check('no scores yet: every badge hidden', all(v is None for v in bs.values()) and len(bs) == 5, bs)
        await page.evaluate("localStorage.setItem('sliceBest', '480'); localStorage.setItem('strikeBest', '12')")
        await page.click('#mouseBtn'); await page.wait_for_timeout(100); await page.click('#homeBtn'); await page.wait_for_timeout(100)
        bs = await page.evaluate(BESTS)
        check('home refreshes the badges from localStorage', bs['slice'] == '★ 480' and bs['strike'] == '★ 12' and bs['smash'] is None, bs)
        vis = await page.evaluate("(() => { const b = document.querySelector('.modes button[data-mode=slice] .best').getBoundingClientRect(), c = document.querySelector('.modes button[data-mode=slice] .pv').getBoundingClientRect(); return b.width > 20 && b.top >= c.top && b.right <= c.right + 1 && b.bottom < c.top + c.height / 2; })()")
        check('badge sits in the top corner of the preview', vis)
        await page.reload(); await page.wait_for_timeout(600)
        check('badges read on load', (await page.evaluate(BESTS))['slice'] == '★ 480')
        check('badges: no page errors', not errs, errs); await ctx.close()

        # ---- hint row + camera memory + layout, both languages, phone and desktop ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, mobile, he, "localStorage.setItem('smashBest', '7');")
                await page.wait_for_timeout(1300)  # entrance done
                hs = await page.evaluate(HINTS)
                check(tag + ': sandbox hint row = pinch Grab, open Throw, point Poke', hs['g'] == ['pinch', 'open', 'point'] and hs['icons'] and hs['t'] == (['תפיסה', 'זריקה', 'דחיפה'] if he else ['Grab', 'Throw', 'Poke']), hs)
                check(tag + ': hint icon at the start edge of its label', all(hs['rtl']) if he else not any(hs['rtl']), hs['rtl'])
                cam = await page.evaluate(CAM)
                check(tag + ': first visit: Enable camera, no hint', cam['label'] == ('הפעלת מצלמה' if he else 'Enable camera') and cam['hint'] is None, cam)
                fit = await page.evaluate(FIT)
                check(tag + ': start screen inside the viewport, no scroll', fit['bodyScroll'] and fit['startScroll'] and fit['top'] >= 0 and fit['link'] <= fit['H'] and fit['mouse'][1] <= fit['H'] and fit['dl'] >= 0 and fit['dr'] <= fit['W'], fit)
                row = await page.evaluate(ROW)
                if mobile:
                    check(tag + ': snap row: one scrollable row of 136 px cards, 5 dots, first dot on', row['snap'].startswith('x') and row['scrollable'] and row['rowIn'] and row['rows'] == 1 and all(w == 136 for w in row['widths']) and row['fit'] and row['dots'] == 5 and row['dotsShown'] and row['on'] == 0, row)
                    check(tag + ': selected (first) card centred', row['selIn'] and abs(row['selMid'] - row['W'] / 2) < 3, row)
                else:
                    check(tag + ': desktop: 5-up grid in one row, dots hidden', row['rows'] == 1 and not row['scrollable'] and row['fit'] and all(w > 90 for w in row['widths']) and not row['dotsShown'], row)
                worst = None
                for m, g, n in (('slice', ['point'], 1), ('smash', ['fist', 'open'], 2), ('busy', ['point', 'pinch', 'open'], 3), ('strike', ['open'], 1)):
                    if mobile: await page.tap('.modes button[data-mode=' + m + ']')
                    else: await page.click('.modes button[data-mode=' + m + ']')
                    await page.wait_for_timeout(600)
                    hs = await page.evaluate(HINTS); fit = await page.evaluate(FIT); row = await page.evaluate(ROW)
                    check(tag + ': ' + m + ' hint row updates (' + str(n) + ')', hs['g'] == g and len(hs['t']) == n and all(hs['t']), hs)
                    ok = fit['bodyScroll'] and fit['startScroll'] and fit['link'] <= fit['H'] and fit['top'] >= 0 and fit['desc'][0] > 0
                    if not ok: worst = (m, fit)
                    if mobile: check(tag + ': ' + m + ' card scrolled into view and centred, its dot on', row['selIn'] and abs(row['selMid'] - row['W'] / 2) < 3 and row['on'] == ['sandbox', 'slice', 'smash', 'busy', 'strike'].index(m), row)
                    if m == 'smash': await page.screenshot(path='tests/out/start_' + ('phone_' if mobile else 'desktop_') + ('he' if he else 'en') + '_smash.png')
                check(tag + ': every mode fits (description card, both buttons, link visible)', worst is None, worst)
                check(tag + ': strike pill shows and still fits', await page.evaluate("!$('strikeDiff').hidden && $('strikeDiff').getBoundingClientRect().bottom < $('camBtn').getBoundingClientRect().top"))
                check(tag + ': smash best badge', (await page.evaluate(BESTS))['smash'] == '★ 7')
                if mobile: # a swipe on the row scrolls it; the dots follow
                    await page.evaluate("document.querySelector('.modes').scrollBy({ left: " + ('' if he else '-') + "600, behavior: 'instant' })"); await page.wait_for_timeout(250)
                    row2 = await page.evaluate(ROW)
                    check(tag + ': row scrolls; the dot follows the card in view', row2['sl'] != row['sl'] and row2['on'] != row['on'], [row['sl'], row2['sl'], row['on'], row2['on']])
                    await page.tap('.modes button[data-mode=sandbox]'); await page.wait_for_timeout(600)
                    check(tag + ': tapping a card selects and centres it', await page.evaluate("gameMode") == 'sandbox' and (await page.evaluate(ROW))['on'] == 0)
                else: await page.click('.modes button[data-mode=sandbox]')
                await page.wait_for_timeout(200)
                await page.screenshot(path='tests/out/start_' + ('phone_' if mobile else 'desktop_') + ('he' if he else 'en') + '.png')
                # camera worked once: the button says so next time
                await page.evaluate("localStorage.setItem('camOk', '1')"); await page.reload(); await page.wait_for_timeout(700)
                cam = await page.evaluate(CAM)
                check(tag + ': camera remembered: Play with camera + last used tag', cam['label'] == ('משחק עם מצלמה' if he else 'Play with camera') and cam['hint'] == ('בפעם הקודמת' if he else 'last used') and cam['hintIn'], cam)
                await page.screenshot(path='tests/out/start_' + ('phone_' if mobile else 'desktop_') + ('he' if he else 'en') + '_camok.png')
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- a real camera run sets camOk; reduced motion skips the entrance ----
        ctx = await b.new_context(viewport={'width':1280,'height':800}, permissions=['camera'], reduced_motion='reduce'); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(300)
        an = await page.evaluate("[getComputedStyle(document.querySelector('.panel h1')).animationName, getComputedStyle(document.querySelector('.modes button')).animationName, $('start').classList.contains('intro')]")
        check('reduced motion: no entrance animation', an[0] == 'none' and an[1] == 'none' and an[2], an)
        check('camOk unset before the camera ran', await page.evaluate("localStorage.getItem('camOk')") is None)
        await page.click('#camBtn'); await page.wait_for_function("mode === 'camera'", timeout=15000); await page.wait_for_timeout(200)
        check('camera started: camOk saved', await page.evaluate("localStorage.getItem('camOk')") == '1')
        await page.click('#homeBtn'); await page.wait_for_timeout(200)
        cam = await page.evaluate(CAM)
        check('home after a camera game: Play with camera', cam['label'] == 'Play with camera' and cam['hint'] == 'last used', cam)
        check('camera run: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
