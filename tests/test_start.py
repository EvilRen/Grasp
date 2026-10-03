exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Start screen: live mode previews on the cards, best-score badges, the gesture hint row, the phone snap row, camera memory, entrance.
PV = "(() => { const cs = [...document.querySelectorAll('.modes button canvas.pvc')]; return { n: cs.length, sized: cs.every(c => c.width > 0 && c.height > 0 && c.getBoundingClientRect().width > 40), shots: cs.map(c => c.toDataURL()), frames: __grasp.previews.frames, running: __grasp.previews.running }; })()"
FIT = """(() => { const st = $('start'), a = document.querySelector('#start a.link').getBoundingClientRect(), cam = $('camBtn').getBoundingClientRect(), mo = $('mouseBtn').getBoundingClientRect(), d = $('modeCard').getBoundingClientRect(), h1 = document.querySelector('.panel h1').getBoundingClientRect();
  return { H: innerHeight, W: innerWidth, bodyScroll: document.documentElement.scrollHeight <= innerHeight && scrollY === 0, startScroll: st.scrollHeight <= st.clientHeight + 1, top: h1.top, link: a.bottom, cam: [cam.top, cam.bottom], mouse: [mo.top, mo.bottom], desc: [d.top, d.bottom], dl: d.left, dr: d.right }; })()"""
ROW = """(() => { const m = document.querySelector('.modes'), r = m.getBoundingClientRect(), cs = getComputedStyle(m), bs = [...m.querySelectorAll('button')], sel = m.querySelector('[aria-pressed=true]').getBoundingClientRect();
  const dots = [...document.querySelectorAll('#modeDots i')]; return { snap: cs.scrollSnapType, scrollable: m.scrollWidth > m.clientWidth + 1, rowIn: r.left >= 0 && r.right <= innerWidth, rows: new Set(bs.map(b => Math.round(b.getBoundingClientRect().top / 20))).size,
  widths: bs.map(b => Math.round(b.getBoundingClientRect().width)), fit: bs.every(b => b.scrollWidth <= b.clientWidth + 1), selIn: sel.left >= 0 && sel.right <= innerWidth, selMid: sel.left + sel.width / 2, dots: dots.length, dotsShown: dots.length && getComputedStyle($('modeDots')).display !== 'none', on: dots.findIndex(d => d.classList.contains('on')), sl: m.scrollLeft, W: innerWidth }; })()"""
HINTS = "(() => { const li = [...document.querySelectorAll('#modeHints li')]; return { g: li.map(l => l.dataset.g), t: li.map(l => l.textContent.trim()), icons: li.every(l => l.querySelector('svg') && l.querySelector('svg').getBoundingClientRect().width > 12), rtl: li.map(l => l.querySelector('svg').getBoundingClientRect().left > l.querySelector('span').getBoundingClientRect().left) }; })()"
BESTS = "(() => { const o = {}; for (const m of ['sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes']) { const b = document.querySelector('.modes button[data-mode=' + m + '] .best'); o[m] = b ? (b.hidden ? null : b.textContent) : 'none'; } return o; })()"
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

        # ---- previews: six canvases, animating while the start screen shows, frozen once a game starts or the tab hides ----
        ctx, page, errs = await fresh(b, False)
        check('intro class on first show', await page.evaluate("$('start').classList.contains('intro')"))
        a = await page.evaluate(PV); await page.wait_for_timeout(400); c = await page.evaluate(PV)
        check('6 preview canvases, sized, one shared loop running', a['n'] == 6 and a['sized'] and a['running'], a['n'])
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
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(100)
        g = await page.evaluate(PV); await page.wait_for_timeout(400); h = await page.evaluate(PV)
        check('game started: previews stop and the canvases keep their last frame', not g['running'] and h['frames'] == g['frames'] and g['shots'] == h['shots'])
        await page.click('#homeBtn'); await page.wait_for_timeout(350)
        i = await page.evaluate(PV)
        check('home: previews run again, no intro replay', i['running'] and i['frames'] > h['frames'] and not await page.evaluate("$('start').classList.contains('intro')"))
        check('previews: no page errors', not errs, errs); await ctx.close()

        # ---- best badges ----
        ctx, page, errs = await fresh(b, False)
        bs = await page.evaluate(BESTS)
        check('no scores yet: every badge hidden', all(v is None for v in bs.values()) and len(bs) == 6, bs)
        await page.evaluate("localStorage.setItem('sliceBest', '480'); localStorage.setItem('strikeBest', '12')")
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(100); await page.click('#homeBtn'); await page.wait_for_timeout(100)
        bs = await page.evaluate(BESTS)
        check('home refreshes the badges from localStorage', bs['slice'] == '★ 480' and bs['strike'] == '★ 12' and bs['smash'] is None, bs)
        vis = await page.evaluate("(() => { const b = document.querySelector('.modes button[data-mode=slice] .best').getBoundingClientRect(), c = document.querySelector('.modes button[data-mode=slice] .pv').getBoundingClientRect(); return b.width > 20 && b.top >= c.top && b.right <= c.right + 1 && b.bottom < c.top + c.height / 2; })()")
        check('badge sits in the top corner of the preview', vis)
        await page.reload(); await page.wait_for_timeout(600)
        check('badges read on load', (await page.evaluate(BESTS))['slice'] == '★ 480')
        check('badges: no page errors', not errs, errs); await ctx.close()

        # ---- the start screen v2, phone + desktop, EN + HE: everything on one screen (no scroll), 6 game tiles, a labelled icon row, the Camera | Touch toggle; a tap on a tile starts that game ----
        LAY = """(() => { const tiles = [...document.querySelectorAll('.modes > button[data-mode]')].map(b => { const r = b.getBoundingClientRect(); return { m: b.dataset.mode, in: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, w: r.width, h: r.height, name: b.querySelector('[data-i18n]').textContent }; });
          const icons = [...document.querySelectorAll('.metaRow > button')].map(b => { const r = b.getBoundingClientRect(), l = b.querySelector('.dTx b, :scope > span[data-i18n]').getBoundingClientRect(); return { id: b.id, in: r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, label: l.width > 10 && l.left >= r.left - 1 && l.right <= r.right + 1, text: b.querySelector('.dTx b, :scope > span[data-i18n]').textContent }; });
          const st = $('start'), a = document.querySelector('#start a.link').getBoundingClientRect(), sd = $('strikeDiff').getBoundingClientRect(), stk = document.querySelector('.modes button[data-mode=strike]').getBoundingClientRect(), cam = $('camBtn').getBoundingClientRect(), mo = $('mouseBtn').getBoundingClientRect();
          return { noScroll: document.documentElement.scrollHeight <= innerHeight && st.scrollHeight <= st.clientHeight + 1, link: a.bottom <= innerHeight && a.height > 0, tiles, icons, diffOnTile: !$('strikeDiff').hidden && sd.left >= stk.left - 1 && sd.right <= stk.right + 1 && sd.top >= stk.top && sd.bottom <= stk.bottom,
            seg: [cam.bottom <= innerHeight && cam.width > 60, mo.bottom <= innerHeight && mo.width > 60], segText: [$('camBtn').textContent.trim(), $('mouseBtn').textContent.trim()], pressed: [$('camBtn').getAttribute('aria-pressed'), $('mouseBtn').getAttribute('aria-pressed')], h1: document.querySelector('.panel h1').getBoundingClientRect().height }; })()"""
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); W = 360 if mobile else 1280
                ctx, page, errs = await fresh(b, mobile, he, "localStorage.setItem('smashBest', '7'); if (!sessionStorage.getItem('pv')) { sessionStorage.setItem('pv', '1'); localStorage.removeItem('inputPref'); }")
                await page.wait_for_timeout(1300)  # entrance done
                L = await page.evaluate(LAY)
                check(tag + ': no scrolling at all; the Tremorti link visible; a small wordmark', L['noScroll'] and L['link'] and L['h1'] <= 40, L)
                check(tag + ': all 6 game tiles fully on screen, named', len(L['tiles']) == 6 and all(t['in'] and t['w'] > 80 and t['name'] for t in L['tiles']), L['tiles'])
                check(tag + ': one icon row, every button labelled on screen (Daily, Missions, Road, Shop)', [i['id'] for i in L['icons']] == ['dailyBtn', 'missionsBtn', 'roadBtn', 'collectionBtn'] and all(i['in'] and i['label'] for i in L['icons']) and [i['text'] for i in L['icons']] == (['יומי', 'משימות', 'הדרך', 'חנות'] if he else ['Daily', 'Missions', 'Road', 'Shop']), L['icons'])
                check(tag + ': the Easy / Normal toggle sits on the Strike tile', L['diffOnTile'], L)
                check(tag + ': the Camera | Touch toggle on screen, translated; on a first visit Touch is the default', all(L['seg']) and L['segText'] == (['מצלמה', 'מגע'] if he else ['Camera', 'Touch']) and L['pressed'] == ['false', 'true'], L)
                check(tag + ': smash best badge', (await page.evaluate(BESTS))['smash'] == '★ 7')
                await page.screenshot(path='tests/out/start2_' + ('phone_' if mobile else 'desktop_') + ('he' if he else 'en') + '.png')
                if mobile: await page.tap('#mouseBtn')
                else: await page.click('#mouseBtn')
                await page.reload(); await page.wait_for_timeout(700)
                check(tag + ': the toggle persists (Touch after a reload)', (await page.evaluate(LAY))['pressed'] == ['false', 'true'])
                started = {}
                for m in ('sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes'):
                    if mobile: await page.tap('.modes button[data-mode=' + m + ']')
                    else: await page.click('.modes button[data-mode=' + m + ']')
                    if m == 'strike':  # (Strike: the tile opens the Adventure map; its current stop starts the stage)
                        await page.wait_for_function("!$('advMap').hidden", timeout=4000)
                        if mobile: await page.tap('#advPath .anode.cur')
                        else: await page.click('#advPath .anode.cur')
                    await page.wait_for_function("mode !== 'none'", timeout=8000); started[m] = await page.evaluate("[gameMode, mode, $('start').hidden]")
                    await page.evaluate("goHome()"); await page.wait_for_timeout(250)
                check(tag + ': a tap on each tile starts that game at once (Strike: via its map), with touch', all(v == [m, 'mouse', True] for m, v in started.items()), started)
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- a real camera run sets camOk; reduced motion skips the entrance ----
        ctx = await b.new_context(viewport={'width':1280,'height':800}, permissions=['camera'], reduced_motion='reduce'); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(300)
        an = await page.evaluate("[getComputedStyle(document.querySelector('.panel h1')).animationName, getComputedStyle(document.querySelector('.modes button')).animationName, $('start').classList.contains('intro')]")
        check('reduced motion: no entrance animation', an[0] == 'none' and an[1] == 'none' and an[2], an)
        check('camOk unset before the camera ran', await page.evaluate("localStorage.getItem('camOk')") is None)  # (the toggle: Camera, then a tap on the selected tile)
        await page.click('#camBtn'); await page.click('.modes > button[aria-pressed=true]'); await page.wait_for_function("mode === 'camera'", timeout=15000); await page.wait_for_timeout(200)
        check('camera started: camOk saved', await page.evaluate("localStorage.getItem('camOk')") == '1')
        await page.click('#homeBtn'); await page.wait_for_timeout(200)
        check('home after a camera game: the toggle says Camera', await page.evaluate("$('camBtn').getAttribute('aria-pressed')") == 'true')
        check('camera run: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
