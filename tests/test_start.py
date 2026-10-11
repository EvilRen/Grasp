exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Start screen: live mode previews on the cards, best-score badges, the gesture hint row, the phone snap row, camera memory, entrance.
PV = "(() => { const all = [...document.querySelectorAll('#start canvas.pvc, #littlePick canvas.pvc')], cs = all.filter(c => c.offsetParent); return { n: all.length, vis: cs.length, sized: cs.every(c => c.width > 0 && c.height > 0 && c.getBoundingClientRect().width > 40), shots: cs.map(c => c.toDataURL()), frames: __grasp.previews.frames, t: performance.now(), running: __grasp.previews.running }; })()"  # home2: 6 previews (the hero's Strike, Smash, Slice; the Little ones picker's 3), the visible ones drawn
FIT = """(() => { const st = $('start'), a = document.querySelector('#start a.link').getBoundingClientRect(), cam = $('camBtn').getBoundingClientRect(), mo = $('mouseBtn').getBoundingClientRect(), d = $('modeCard').getBoundingClientRect(), h1 = document.querySelector('.panel h1').getBoundingClientRect();
  return { H: innerHeight, W: innerWidth, bodyScroll: document.documentElement.scrollHeight <= innerHeight && scrollY === 0, startScroll: st.scrollHeight <= st.clientHeight + 1, top: h1.top, link: a.bottom, cam: [cam.top, cam.bottom], mouse: [mo.top, mo.bottom], desc: [d.top, d.bottom], dl: d.left, dr: d.right }; })()"""
ROW = """(() => { const m = document.querySelector('.modes'), r = m.getBoundingClientRect(), cs = getComputedStyle(m), bs = [...m.querySelectorAll('button')], sel = m.querySelector('[aria-pressed=true]').getBoundingClientRect();
  const dots = [...document.querySelectorAll('#modeDots i')]; return { snap: cs.scrollSnapType, scrollable: m.scrollWidth > m.clientWidth + 1, rowIn: r.left >= 0 && r.right <= innerWidth, rows: new Set(bs.map(b => Math.round(b.getBoundingClientRect().top / 20))).size,
  widths: bs.map(b => Math.round(b.getBoundingClientRect().width)), fit: bs.every(b => b.scrollWidth <= b.clientWidth + 1), selIn: sel.left >= 0 && sel.right <= innerWidth, selMid: sel.left + sel.width / 2, dots: dots.length, dotsShown: dots.length && getComputedStyle($('modeDots')).display !== 'none', on: dots.findIndex(d => d.classList.contains('on')), sl: m.scrollLeft, W: innerWidth }; })()"""
HINTS = "(() => { const li = [...document.querySelectorAll('#modeHints li')]; return { g: li.map(l => l.dataset.g), t: li.map(l => l.textContent.trim()), icons: li.every(l => l.querySelector('svg') && l.querySelector('svg').getBoundingClientRect().width > 12), rtl: li.map(l => l.querySelector('svg').getBoundingClientRect().left > l.querySelector('span').getBoundingClientRect().left) }; })()"
BESTS = "(() => { const o = {}; for (const m of ['sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes']) { const b = document.querySelector('button[data-mode=' + m + '] .best'); o[m] = b ? (b.hidden ? null : b.textContent) : 'none'; } return o; })()"
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
        check('6 preview canvases (3 on the start screen: the hero, Smash, Slice), sized, one shared loop running', a['n'] == 6 and a['vis'] == 3 and a['sized'] and a['running'], a)
        check('previews animate: every visible canvas changes between frames', c['frames'] > a['frames'] and all(x != y for x, y in zip(a['shots'], c['shots'])), [a['frames'], c['frames']])
        await page.click('#littleBtn'); await page.wait_for_function("!$('littlePick').hidden", timeout=3000); await page.wait_for_timeout(500)
        a2 = await page.evaluate(PV); await page.wait_for_timeout(400); c2 = await page.evaluate(PV)
        check('the Little ones picker: its 3 previews show and animate too', a2['vis'] == 6 and a2['sized'] and all(x != y for x, y in zip(a2['shots'], c2['shots'])), a2['vis'])
        await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        fps = (c['frames'] - a['frames']) / ((c['t'] - a['t']) / 1000)  # (the page's own clock between the two reads: under load the 400 ms wait stretches)
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
        await menu_click(page, '#homeBtn'); await page.wait_for_timeout(350)
        i = await page.evaluate(PV)
        check('home: previews run again, no intro replay', i['running'] and i['frames'] > h['frames'] and not await page.evaluate("$('start').classList.contains('intro')"))
        check('previews: no page errors', not errs, errs); await ctx.close()

        # ---- best badges ----
        ctx, page, errs = await fresh(b, False)
        bs = await page.evaluate(BESTS)
        check('no scores yet: every badge hidden', all(v is None for v in bs.values()) and len(bs) == 6, bs)
        await page.evaluate("localStorage.setItem('sliceBest', '480'); localStorage.setItem('strikeBest', '12')")
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(100); await menu_click(page, '#homeBtn'); await page.wait_for_timeout(100)
        bs = await page.evaluate(BESTS)
        check('home refreshes the badges from localStorage (home2: no Endless badge on the hero\'s Map)', bs['slice'] == '★ 480' and bs['strike'] is None and bs['smash'] is None, bs)
        vis = await page.evaluate("(() => { const b = document.querySelector('.modes button[data-mode=slice] .best').getBoundingClientRect(), c = document.querySelector('.modes button[data-mode=slice] .pv').getBoundingClientRect(); return b.width > 20 && b.top >= c.top && b.right <= c.right + 1 && b.bottom < c.top + c.height / 2; })()")
        check('badge sits in the top corner of the preview', vis)
        await page.reload(); await page.wait_for_timeout(600)
        check('badges read on load', (await page.evaluate(BESTS))['slice'] == '★ 480')
        check('badges: no page errors', not errs, errs); await ctx.close()

        # ---- home2, phone + desktop, EN + HE: one screen (no scroll): the top bar (wordmark, coins pill, ⋯), the hero, Smash · Slice · Arcade, Camera games · Little ones, the tab bar; a tap plays ----
        LAY = """(() => { const r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height }; }, on = (q) => q.l >= 0 && q.t >= 0 && q.r <= innerWidth + 0.5 && q.b <= innerHeight + 0.5;
          const tiles = [...document.querySelectorAll('#start .modes button')].map(b => ({ id: b.id || b.dataset.mode, ...r(b), name: (b.querySelector('[data-i18n], b') || b).textContent.trim(), fs: Math.min(...[...b.querySelectorAll('b, span[data-i18n]')].filter(x => x.offsetParent).map(x => parseFloat(getComputedStyle(x).fontSize))) }));
          const st = $('start'), tabs = [...document.querySelectorAll('#tabBar .tab')].filter(b => !b.hidden).map(b => ({ id: b.id, ...r(b) }));
          return { noScroll: document.documentElement.scrollHeight <= innerHeight && st.scrollHeight <= st.clientHeight + 1, tiles, tabs, allOn: tiles.every(on) && tabs.every(on), more: r($('moreBtn')), pill: r($('metaPill')), h1: r(document.querySelector('#start h1')),
            gone: ['metaRow', 'habitBar', 'flameBtn', 'giftBtn', 'strikeDiff', 'camBtn', 'eventBtn'].filter(id => { const e = document.getElementById(id) || document.querySelector('#start .' + id); return e && e.closest('#start') && e.offsetParent; }), link: !!document.querySelector('#start a.link') }; })()"""
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en'); W = 360 if mobile else 1280
                ctx, page, errs = await fresh(b, mobile, he, "localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, xpv: 2, smash: { stars: { 1: 3, 2: 3, 3: 1 }, unlocked: 4 } })); if (!sessionStorage.getItem('pv')) { sessionStorage.setItem('pv', '1'); localStorage.removeItem('inputPref'); }")
                await page.wait_for_timeout(1300)  # entrance done
                L = await page.evaluate(LAY)
                check(tag + ': no scrolling at all; the hero + 6 buttons (map, Smash, Slice, Arcade, Camera games, Little ones) and the tab bar on screen, >= 44 px, text >= 14 px', L['noScroll'] and L['allOn'] and len(L['tiles']) == 7 and all(t['h'] >= 44 and t['w'] >= 44 and t['fs'] >= 14 for t in L['tiles']) and len(L['tabs']) == 3, L)
                check(tag + ': gone from the start screen: the meta row, the flame / gift chips, the Easy / Normal toggle, Camera | Touch, the event banner, the Tremorti link', not L['gone'] and not L['link'], L['gone'])
                check(tag + ': the top bar: the wordmark, the coins pill and ⋯ (>= 44 px)', L['more']['w'] >= 44 and L['more']['h'] >= 44 and L['pill']['h'] >= 44 and L['h1']['h'] <= 40, L)
                check(tag + ': smash badge: the stars of its stages', (await page.evaluate(BESTS))['smash'] == '★ 7')
                check(tag + ': on a first visit Touch is the way to play (Camera | Touch now in the More sheet)', await page.evaluate("inputPref()") == 'mouse' and await page.evaluate("$('mouseBtn').getAttribute('aria-pressed')") == 'true')
                await page.screenshot(path='tests/out/start2_' + ('phone_' if mobile else 'desktop_') + ('he' if he else 'en') + '.png')
                started = {}
                for m in ('sandbox', 'slice', 'smash', 'busy', 'strike', 'shapes'):
                    if m in ('sandbox', 'busy', 'shapes'):
                        await (page.tap('#littleBtn') if mobile else page.click('#littleBtn')); await page.wait_for_function("!$('littlePick').hidden", timeout=4000)
                        sel = '#littlePick button[data-mode=' + m + ']'
                    else: sel = '.modes button[data-mode=' + m + ']'
                    if mobile: await page.tap(sel)
                    else: await page.click(sel)
                    if m == 'smash':  # (Smash: the tile opens its map; Free play starts)
                        await page.wait_for_function("!$('smashMap').hidden", timeout=4000)
                        if mobile: await page.tap('#smashFree')
                        else: await page.click('#smashFree')
                    if m == 'strike':  # (Strike: the hero's Map opens the Adventure map; its current stop starts the stage)
                        await page.wait_for_function("!$('advMap').hidden", timeout=4000)
                        if mobile: await page.tap('#advPath .anode.cur')
                        else: await page.click('#advPath .anode.cur')
                    await page.wait_for_function("mode !== 'none'", timeout=8000); started[m] = await page.evaluate("[gameMode, mode, $('start').hidden, $('littlePick').hidden]")
                    await page.evaluate("goHome()"); await page.wait_for_timeout(250)
                check(tag + ': a tap on each game starts it at once with touch (Strike, Smash via their maps; Busy Board, Shapes, Sandbox via Little ones; the picker closes)', all(v == [m, 'mouse', True, True] for m, v in started.items()), started)
                if mobile: await page.tap('#camGamesBtn')
                else: await page.click('#camGamesBtn')
                await page.wait_for_function("!$('cgPick').hidden", timeout=4000)
                if mobile: await page.tap('#cgPick [data-cg=bubbles]')
                else: await page.click('#cgPick [data-cg=bubbles]')
                await page.wait_for_function("mode === 'mouse' && gameMode === 'bubbles' && $('start').hidden && $('cgPick').hidden", timeout=8000)
                check(tag + ': the Camera games tile opens its picker; a game there starts with touch', True)
                await page.evaluate("goHome()"); await page.wait_for_timeout(250)
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- a real camera run sets camOk; reduced motion skips the entrance ----
        ctx = await b.new_context(viewport={'width':1280,'height':800}, permissions=['camera'], reduced_motion='reduce'); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + HAND_JS)
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(300)
        an = await page.evaluate("[getComputedStyle(document.querySelector('#start h1')).animationName, getComputedStyle(document.querySelector('.modes button')).animationName, $('start').classList.contains('intro')]")
        check('reduced motion: no entrance animation', an[0] == 'none' and an[1] == 'none' and an[2], an)
        check('camOk unset before the camera ran', await page.evaluate("localStorage.getItem('camOk')") is None)  # (the toggle (More sheet): Camera, then a tap on the selected tile)
        await page.evaluate("$('camBtn').click()"); await page.evaluate("document.querySelector('button[data-mode][aria-pressed=true]').click()"); await page.wait_for_function("mode === 'camera'", timeout=15000); await page.wait_for_timeout(200)
        check('camera started: camOk saved', await page.evaluate("localStorage.getItem('camOk')") == '1')
        await menu_click(page, '#homeBtn'); await page.wait_for_timeout(200)
        check('home after a camera game: the toggle says Camera', await page.evaluate("$('camBtn').getAttribute('aria-pressed')") == 'true')
        check('camera run: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
