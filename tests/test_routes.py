exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Direct links: /strike (the Adventure map), /smash, /slice, /busy, /shapes, /sandbox open that game at once with the remembered input (touch until the
# camera is picked; the camera too); a trailing slash works; served through tests/serve.py, which applies vercel.json's rewrites. Entering a game from
# the start screen pushes its path, Home goes back to '/', the browser's Back from a game returns to the start screen (the round ended as Home ends it),
# Forward re-enters; any other path is the start screen. At a sub-path the page's own files still load (guest art, the Tremorti link). EN / HE.
# Hooks: __grasp.route { modes, of(path), now, log }.
URL = 'http://localhost:8765'
GAMES = ['strike', 'smash', 'slice', 'busy', 'shapes', 'sandbox']
STATE = """({ path: location.pathname, mode, game: gameMode, start: !$('start').hidden, map: advMapOpen(), now: __grasp.route.now, pause: pause.on, menu: menu.open, hl: history.length })"""

async def fresh(b, he=False, init='', mobile=True):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs = []; bad = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('response', lambda r: bad.append(r.url + ' ' + str(r.status)) if r.status >= 400 and r.url.startswith(URL) and not re.search(r'/favicon\.ico$|/assets/guests/monkey_', r.url) else None)  # (the monkey art is pending: drawn in code until it arrives)
    await page.add_init_script(INIT + HAND_JS + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    return ctx, page, errs, bad

async def st(page): return await page.evaluate(STATE)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- each game's path opens it at once (touch by default); Strike opens the Adventure map ----
        for g in GAMES:
            for he in ((False, True) if g in ('strike', 'shapes') else (False,)):
                tag = f'/{g} ' + ('he' if he else 'en')
                ctx, page, errs, bad = await fresh(b, he)
                await page.goto(f'{URL}/{g}')
                if g == 'strike': await page.wait_for_function("advMapOpen() && gameMode === 'strike'", timeout=10000)
                elif g == 'smash': await page.wait_for_function("smashMapOpen() && gameMode === 'smash'", timeout=10000)
                else: await page.wait_for_function(f"mode === 'mouse' && gameMode === '{g}' && $('start').hidden", timeout=10000)
                s = await st(page)
                title = await page.evaluate("$('advTitle').textContent") if g == 'strike' else ''
                ok = s['path'] == f'/{g}' and s['now'] == g and (s['map'] and s['mode'] == 'none' if g == 'strike' else s['mode'] == 'none' and await page.evaluate("smashMapOpen()") if g == 'smash' else s['mode'] == 'mouse' and not s['start'])
                check(tag + (': the Adventure map opens (no start screen in between)' if g == 'strike' else ': the Smash map opens (Free play or a stage)' if g == 'smash' else ': the game starts at once with touch'), ok, s)
                if g == 'smash':
                    await page.screenshot(path='tests/out/route_smash_map.png')
                    await page.tap('#smashFree'); await page.wait_for_function("mode === 'mouse' && gameMode === 'smash' && $('start').hidden && location.pathname === '/smash'", timeout=10000)
                    check(tag + ': Free play from the map: in play with touch, still /smash', True)
                if g == 'strike':
                    check(tag + ': the map in the UI language', bool(re.search('[֐-׿]', title)) if he else title == 'Adventure', title)
                    await page.screenshot(path=f"tests/out/route_strike_{'he' if he else 'en'}.png")
                    await page.click('#advEndless') if not he else await page.tap('#advEndless')
                    await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.walls.length", timeout=10000)
                    await page.wait_for_function("['in', 'happy', 'dizzy', 'squash'].every(f => { const a = GUEST_ART['cow_' + f]; return a && a.state !== 'loading'; })", timeout=10000)
                    art = await page.evaluate("({ cow: ['in', 'happy', 'dizzy', 'squash'].map(f => GUEST_ART['cow_' + f].state), src: GUEST_ART.cow_in.img.src, tremorti: document.querySelector('a[href*=tremorti]').href, path: location.pathname })")
                    check(tag + ': at the sub-path the page\'s own files load (the cow art from /assets/guests/; the Tremorti link points at /tremorti/); the path stays /strike in play', art['cow'] == ['img'] * 4 and art['src'] == f'{URL}/assets/guests/cow_in.png' and art['tremorti'] == f'{URL}/tremorti/' and art['path'] == '/strike', art)
                check(tag + ': no 404s (besides the pending monkey art) and no page errors', not bad and not errs, [bad, errs])
                await ctx.close()

        # ---- a trailing slash; the camera when it is the remembered input ----
        ctx, page, errs, bad = await fresh(b, init="localStorage.setItem('inputPref','camera'); window.__handFor = () => handAt(180, 400, 0.8);")
        await page.goto(f'{URL}/slice/')
        await page.wait_for_function("mode === 'camera' && gameMode === 'slice'", timeout=20000)
        s = await st(page)
        check('/slice/ (trailing slash) with the camera remembered: Slice starts on the camera; the path is tidied to /slice', s['path'] == '/slice' and s['mode'] == 'camera', s)
        check('/slice/ camera: no 404s, no page errors', not bad and not errs, [bad, errs]); await ctx.close()

        # ---- the start screen: entering pushes the path, Home goes back to '/', Back / Forward ----
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs, bad = await fresh(b, he)
            await page.goto(f'{URL}/'); await page.wait_for_timeout(600)
            s0 = await st(page)
            check(tag + ': / is the start screen', s0['start'] and s0['mode'] == 'none' and s0['path'] == '/' and s0['now'] is None, s0)
            await page.tap('.modes button[data-mode=smash]'); await page.wait_for_function("smashMapOpen()", timeout=8000)
            await page.tap('#smashFree'); await page.wait_for_function("mode === 'mouse' && gameMode === 'smash'", timeout=8000)
            s1 = await st(page)
            check(tag + ': a tap on Smash pushes /smash (a new history entry)', s1['path'] == '/smash' and s1['hl'] == s0['hl'] + 1 and 'push:smash' in await page.evaluate("__grasp.route.log"), [s0, s1])
            await menu_click(page, '#homeBtn', tap=True); await page.wait_for_function("mode === 'none' && location.pathname === '/'", timeout=5000)
            s2 = await st(page)
            check(tag + ': Home: the start screen at / (the entry popped, not a new one)', s2['start'] and s2['path'] == '/' and s2['hl'] == s1['hl'], s2)
            await page.tap('.modes button[data-mode=slice]'); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice' && location.pathname === '/slice'", timeout=8000)
            await page.go_back(); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
            s3 = await st(page)
            check(tag + ': the browser Back from Slice: the start screen at / (the round ended, nothing paused or open)', s3['path'] == '/' and s3['start'] and s3['mode'] == 'none' and not s3['pause'] and not s3['menu'], s3)
            await page.go_forward(); await page.wait_for_function("mode === 'mouse' && gameMode === 'slice' && $('start').hidden", timeout=8000)
            s4 = await st(page)
            check(tag + ': Forward re-enters Slice', s4['path'] == '/slice' and s4['now'] == 'slice', s4)
            await page.go_back(); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
            # Strike: the tile opens the map (/strike); Back closes it
            await page.tap('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen() && location.pathname === '/strike'", timeout=8000)
            await page.go_back(); await page.wait_for_function("!advMapOpen() && location.pathname === '/'", timeout=5000)
            s5 = await st(page)
            check(tag + ': Strike tile: the map at /strike; Back closes it to the start screen', s5['start'] and s5['mode'] == 'none' and not s5['map'], s5)
            # Strike: map -> Endless -> in play -> Back: home, the round ended cleanly
            n0 = await page.evaluate("__grasp.route.log.length")
            await page.tap('.modes button[data-mode=strike]'); await page.wait_for_function("advMapOpen()", timeout=8000)
            await page.tap('#advEndless'); await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.walls.length", timeout=10000)
            s6 = await st(page); lg = await page.evaluate(f"__grasp.route.log.slice({n0})")
            check(tag + ': Strike Endless from the map: still /strike (one entry for the map and the round: one push)', s6['path'] == '/strike' and s6['now'] == 'strike' and lg == ['push:strike'], [s6, lg])
            await page.evaluate("__grasp.strike.playerServe('medium')"); await page.wait_for_timeout(200)
            await page.go_back(); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=5000)
            s7 = await st(page); await page.wait_for_timeout(300)
            check(tag + ': Back from a Strike round: the start screen, the map closed, the round over (no music, nothing paused)', s7['path'] == '/' and not s7['map'] and not s7['pause'] and not s7['menu'] and not await page.evaluate("musicWant()"), s7)
            await page.screenshot(path=f'tests/out/route_back_home_{tag}.png')
            check(tag + ': history: no 404s, no page errors', not bad and not errs, [bad, errs]); await ctx.close()

        # ---- a deep link, then Home: '/', and Back does not leave a dead entry; unknown paths: the start screen ----
        ctx, page, errs, bad = await fresh(b)
        await page.goto(f'{URL}/busy'); await page.wait_for_function("mode === 'mouse' && gameMode === 'busy'", timeout=10000)
        hl = await page.evaluate("history.length")
        await menu_click(page, '#homeBtn', tap=True); await page.wait_for_function("mode === 'none'", timeout=5000)
        d = await st(page)
        check('deep link /busy, then Home: the start screen at / (the entry replaced)', d['path'] == '/' and d['start'] and d['hl'] == hl, d)
        await page.evaluate("history.pushState(null, '', '/nope'); history.pushState(null, '', '/strikes'); history.back()"); await page.wait_for_timeout(400)
        u = await st(page)
        check('a popstate onto an unknown path (/nope): the start screen stays', u['start'] and u['mode'] == 'none' and not u['map'], u)
        check('route.of: only the six games (with or without a trailing slash)', await page.evaluate("['/strike', '/smash/', '/slice', '/busy', '/shapes', '/sandbox', '/', '/nope', '/index.html', '/strike/x', '/tremorti/'].map(__grasp.route.of)") == ['strike', 'smash', 'slice', 'busy', 'shapes', 'sandbox', None, None, None, None, None])
        check('deep link + unknown path: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs, bad = await fresh(b)
        await page.goto(f'{URL}/index.html'); await page.wait_for_timeout(700)
        s = await st(page)
        check('/index.html: the start screen (not a game path)', s['start'] and s['mode'] == 'none' and not s['map'] and s['path'] == '/index.html', s)
        r = await page.request.get(f'{URL}/nope')
        check('the test server mirrors vercel.json: an unknown path is a 404 (only the game paths are rewritten); /tremorti/ is served as before', r.status == 404 and (await page.request.get(f'{URL}/tremorti/')).status == 200 and (await page.request.get(f'{URL}/strike/')).status == 200)
        check('/index.html: no 404s, no page errors', not bad and not errs, [bad, errs]); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
