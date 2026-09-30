import asyncio, subprocess, time, sys
from playwright.async_api import async_playwright
# In-game chrome: icon toolbar, hint toast, no-hand card, camera preview, and every mode's top UI clearing the top row.
srv = subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
MATTER = open('tests/vendor/matter.min.js').read(); FAKE = open('tests/fake_vision.mjs').read()
async def routes(page):
    async def h(route):
        u = route.request.url
        if 'matter' in u: return await route.fulfill(status=200, content_type='application/javascript', body=MATTER)
        if 'vision_bundle.mjs' in u: return await route.fulfill(status=200, content_type='text/javascript', body=FAKE, headers={'Access-Control-Allow-Origin':'*'})
        if '.wasm' in u or 'hand_landmarker.task' in u: return await route.fulfill(status=200, body=b'x'*2048, headers={'Access-Control-Allow-Origin':'*'})
        if 'fonts.g' in u: return await route.fulfill(status=200, body='')
        if '/_blob/probe' in u: return await route.fulfill(status=200, body='')
        return await route.continue_()
    await page.route('**/*', h)
INIT = "window.__created=[];window.__inputs=[];window.__closed=[];window.__handFor=null;"
HAND_JS = """
window.mkHand = (ax, ay, pd) => {
  const L = Array.from({length:21}, () => ({x: ax, y: ay + 0.12, z: 0}));
  const dx = pd * 72 / 640 / 2;
  L[0] = {x: ax, y: ay + 0.27, z:0}; L[9] = {x: ax, y: ay + 0.12, z:0};
  L[4] = {x: ax - dx, y: ay, z:0}; L[8] = {x: ax + dx, y: ay, z:0}; L[6] = {x: ax, y: ay + 0.07, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[tip] = {x: ax, y: ay - 0.05, z:0}; L[pip] = {x: ax, y: ay + 0.05, z:0}; }
  return L;
};
window.handAt = (X, Y, pd) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkHand(1 - (m + X / innerWidth * B), m + Y / innerHeight * B, pd); };
"""
HAND_ON = "window.__handFor = () => handAt(innerWidth*0.5, innerHeight*0.3, 0.8)"
def check(name, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + name + (('  | ' + str(extra)) if extra != '' else ''))
    if not cond: check.fails += 1
check.fails = 0

async def boot(b, mobile, he=False):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(permissions=['camera'], **opts)
    page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    if he: await page.click('#startLang'); await page.wait_for_timeout(100)
    await page.evaluate(HAND_ON)  # a hand is in view from the start, so the game (not the no-hand card) shows
    await page.click('#camBtn')
    await page.wait_for_function("mode === 'camera'", timeout=15000); await page.wait_for_timeout(700)
    return ctx, page, errs

TOOLBAR = """(() => { const c = document.querySelector('.chrome').getBoundingClientRect(), r = [...document.querySelectorAll('.chrome .chip')].map(b => b.getBoundingClientRect()), p = preview.getBoundingClientRect();
  return { n: r.length, oneRow: r.every(x => Math.abs(x.top - r[0].top) < 1 && Math.abs(x.bottom - r[0].bottom) < 1), minW: Math.min(...r.map(x => x.width)), minH: Math.min(...r.map(x => x.height)),
    left: c.left, right: c.right, top: c.top, bottom: c.bottom, height: c.height, prevLeft: p.left, prevRight: p.right, prevBottom: p.bottom, W: innerWidth }; })()"""
HINT = """(() => { const h = $('hint'), r = h.getBoundingClientRect(), ic = h.querySelector('.ic').getBoundingClientRect(), tx = h.querySelector('.tx').getBoundingClientRect();
  return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, H: innerHeight, W: innerWidth, op: getComputedStyle(h).opacity, show: h.classList.contains('show'),
    icon: !!h.querySelector('.ic svg'), icLeft: ic.left, txLeft: tx.left, text: h.textContent.trim() }; })()"""
CARD = """(() => { const s = statusEl.getBoundingClientRect(), b = $('swapBtn').getBoundingClientRect(), p = preview.getBoundingClientRect(), g = document.querySelector('#status .handGuide svg');
  return { shown: !statusEl.hidden, big: preview.classList.contains('big'), inCard: statusEl.contains(preview), card: [s.top, s.bottom, s.left, s.right], btn: [b.top, b.bottom, b.left, b.right], prev: [p.top, p.bottom, p.width],
    tips: document.querySelectorAll('#status .tips li svg').length, guide: g && g.getBoundingClientRect().width > 20 && getComputedStyle(g).opacity !== '0', dot: $('liveDot').hidden, H: innerHeight, W: innerWidth }; })()"""

async def mode_ui_checks(page, tag):
    # every mode's own top UI starts below the toolbar / preview row; the hint toast sits above Strike's power meter
    row = await page.evaluate("__grasp.chromeRowBottom()")
    for m in ('slice', 'smash'):
        await page.evaluate(f"__grasp.setGameMode('{m}')"); await page.wait_for_timeout(120)
        sy = await page.evaluate("__grasp.scoreY()")
        check(tag + f' {m}: score starts below the top row', sy - 37 >= row, [sy, row])
    await page.evaluate("__grasp.setGameMode('strike')"); await page.wait_for_timeout(400)
    hud = await page.evaluate("__grasp.strike.ui.hud"); mt = await page.evaluate("__grasp.strike.ui.meterTop"); h = await page.evaluate(HINT)
    check(tag + ' strike: HUD card under the top row', hud and hud['y'] >= row, [hud, row])
    check(tag + ' strike: hint toast sits above the power meter', h['show'] and mt > 0 and h['bottom'] <= mt and h['top'] > h['H'] * 0.5, [h, mt])
    await page.evaluate("__grasp.setGameMode('busy')"); await page.wait_for_timeout(200)
    check(tag + ' busy: board starts below the top row', await page.evaluate("__grasp.busy.board.y") >= row)
    await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(100)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await boot(b, True, he)
            tb = await page.evaluate(TOOLBAR)
            check(tag + ' phone: toolbar is one row of 5 icon buttons, each >= 40 px', tb['n'] == 5 and tb['oneRow'] and tb['minW'] >= 40 and tb['minH'] >= 40 and tb['height'] < 60, tb)
            check(tag + ' phone: toolbar fits next to the 96 px preview at 360 px', tb['prevRight'] - tb['prevLeft'] == 96 and tb['left'] >= tb['prevRight'] + 4 and tb['right'] <= tb['W'] and abs(tb['top'] - 12) < 1, tb)
            titles = await page.evaluate("[...document.querySelectorAll('.chrome .chip')].map(b => b.title || b.getAttribute('aria-label'))")
            check(tag + ' phone: every button has a tooltip in the current language', all(titles) and (('בית' in titles) if he else ('Home' in titles)) and (('השתקת צלילים' in titles) if he else ('Mute sound' in titles)), titles)
            check(tag + ' phone: live dot on the small preview', await page.evaluate("!$('liveDot').hidden && getComputedStyle($('liveDot')).display !== 'none'"))
            h = await page.evaluate(HINT)
            check(tag + ' phone: hint toast at the bottom, inside the screen, with the mode icon at the start edge',
                  h['show'] and h['op'] == '1' and h['icon'] and h['top'] > h['H'] * 0.55 and h['bottom'] <= h['H'] - 8 and h['left'] >= 0 and h['right'] <= h['W'] and ((h['icLeft'] > h['txLeft']) if he else (h['icLeft'] < h['txLeft'])) and len(h['text']) > 10, h)
            await page.screenshot(path='tests/out/chrome_phone_' + tag + '.png')
            await page.click('#hudBtn'); await page.wait_for_timeout(300)
            st = await page.evaluate("({p: $('hudBtn').getAttribute('aria-pressed'), bg: getComputedStyle($('hudBtn')).backgroundColor, hud: !hudEl.hidden})")
            check(tag + ' phone: HUD button highlighted while the HUD shows', st['p'] == 'true' and st['hud'] and st['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent'), st)
            await page.click('#hudBtn'); await page.wait_for_timeout(100)
            check(tag + ' phone: HUD button back to normal', await page.evaluate("$('hudBtn').getAttribute('aria-pressed') === 'false' && hudEl.hidden"))
            await page.wait_for_function("$('hint').style.opacity === '0'", timeout=6000); await page.wait_for_timeout(700)
            check(tag + ' phone: hint toast faded after ~4 s', float(await page.evaluate("getComputedStyle($('hint')).opacity")) < 0.05 and not await page.evaluate("$('hint').classList.contains('show')"))
            await page.tap('#preview'); await page.wait_for_timeout(400)
            w1 = await page.evaluate("preview.getBoundingClientRect().width")
            await page.wait_for_timeout(2300)
            w2 = await page.evaluate("preview.getBoundingClientRect().width")
            check(tag + ' phone: a tap on the preview enlarges it for a look, then it shrinks back', w1 > 150 and abs(w2 - 96) < 1 and await page.evaluate("!preview.classList.contains('peek')"), [w1, w2])
            if not he:
                check('camera maps the central 86% of the frame', await page.evaluate("__grasp.CONFIG.MAP_BOX === 0.86"))
                await page.evaluate("window.__handFor = () => mkHand(1 - 0.12, 0.5, 0.8)"); await page.wait_for_timeout(700)  # a hand 12% into the frame lands ~5.8% into the screen
                cx = await page.evaluate("cursor.x")
                check('hand at 12% of the frame maps near the screen edge (~21 px)', abs(cx - 360 * (0.12 - 0.07) / 0.86) < 4, cx)
                await page.evaluate("window.__handFor = () => handAt(-300, innerHeight / 2, 0.8)"); await page.wait_for_timeout(700)
                lx = await page.evaluate("[cursor.x, cursor.present]")
                await page.evaluate("window.__handFor = () => handAt(innerWidth + 300, innerHeight + 300, 0.8)"); await page.wait_for_timeout(700)
                rx = await page.evaluate("[cursor.x, cursor.y, cursor.present]")
                check('cursor clamped to the screen with an 8 px margin', lx[0] == 8 and lx[1] and rx[0] == 352 and rx[1] == 732 and rx[2], [lx, rx])
                await page.evaluate(HAND_ON); await page.wait_for_timeout(300)
            await mode_ui_checks(page, tag + ' phone')
            await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(1000)
            c = await page.evaluate(CARD)
            check(tag + ' phone: no-hand card with the enlarged preview, 3 tips, hand guide; switch button inside the viewport below the preview',
                  c['shown'] and c['big'] and c['inCard'] and c['tips'] == 3 and c['guide'] and c['dot'] and c['prev'][2] > 200
                  and c['card'][0] >= 0 and c['card'][1] <= c['H'] and c['btn'][0] > c['prev'][1] and c['btn'][1] <= c['H'] and c['btn'][2] >= 0 and c['btn'][3] <= c['W'], c)
            await page.screenshot(path='tests/out/chrome_phone_nohand_' + tag + '.png')
            await page.evaluate(HAND_ON); await page.wait_for_timeout(800)
            check(tag + ' phone: hand back -> card hides, preview back in the corner', await page.evaluate("statusEl.hidden && preview.parentNode === document.body && Math.abs(preview.getBoundingClientRect().width - 96) < 1 && !$('liveDot').hidden"))
            if not he:
                await page.click('#muteBtn'); await page.wait_for_timeout(100)
                st = await page.evaluate("({m: __grasp.muted, p: $('muteBtn').getAttribute('aria-pressed'), ls: localStorage.getItem('muted'), t: $('muteBtn').title})")
                check('mute button mutes and persists', st['m'] and st['p'] == 'true' and st['ls'] == '1' and st['t'] == 'Unmute sound', st)
                await page.reload(); await page.wait_for_timeout(700)
                check('mute survives a reload', await page.evaluate("__grasp.muted && $('muteBtn').getAttribute('aria-pressed') === 'true'"))
                await page.evaluate("__grasp.muted = false")
                check('unmute via the test hook clears it', await page.evaluate("!__grasp.muted && localStorage.getItem('muted') === '0' && $('muteBtn').getAttribute('aria-pressed') === 'false'"))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()

        # ---- start screen: Strike difficulty pill, saved across reloads ----
        ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        check('difficulty pill hidden unless Strike is selected', await page.evaluate("$('strikeDiff').hidden"))
        await page.tap('.modes button[data-mode=strike]'); await page.wait_for_timeout(100)
        d = await page.evaluate("(() => { const r = $('strikeDiff').getBoundingClientRect(), a = document.querySelector('#start a.link').getBoundingClientRect(); return { hidden: $('strikeDiff').hidden, diff: __grasp.strike.diff, pressed: $('strikeDiff').querySelector('[aria-pressed=true]').dataset.diff, top: r.top, fits: a.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth }; })()")
        check('Strike selected: Easy / Normal pill shows, Easy by default, start screen still fits', not d['hidden'] and d['diff'] == 'easy' and d['pressed'] == 'easy' and d['fits'], d)
        await page.tap('#strikeDiff button[data-diff=normal]'); await page.wait_for_timeout(100)
        check('tap Normal: selected and saved', await page.evaluate("__grasp.strike.diff === 'normal' && $('strikeDiff').querySelector('[aria-pressed=true]').dataset.diff === 'normal' && localStorage.getItem('strikeDiff') === 'normal'"))
        await page.reload(); await page.wait_for_timeout(600); await page.tap('.modes button[data-mode=strike]'); await page.wait_for_timeout(100)
        check('difficulty persists across a reload', await page.evaluate("__grasp.strike.diff === 'normal' && $('strikeDiff').querySelector('[aria-pressed=true]').dataset.diff === 'normal'"))
        await page.tap('#mouseBtn'); await page.wait_for_timeout(300)
        check('Normal round starts with 3 lives', await page.evaluate("__grasp.strike.lives === 3 && __grasp.strikeParams().speed === 1.1"))
        await page.screenshot(path='tests/out/chrome_phone_strike_normal.png')
        check('difficulty: no page errors', not errs, errs); await ctx.close()

        # ---- desktop 1280x800, camera ----
        ctx, page, errs = await boot(b, False)
        tb = await page.evaluate(TOOLBAR)
        check('desktop: toolbar one row, top-right, clear of the preview', tb['n'] == 5 and tb['oneRow'] and tb['left'] > tb['prevRight'] and tb['right'] <= tb['W'], tb)
        await page.screenshot(path='tests/out/chrome_desktop.png')
        await mode_ui_checks(page, 'desktop')
        await page.evaluate("__grasp.setGameMode('strike')"); await page.wait_for_timeout(300)
        await page.screenshot(path='tests/out/chrome_desktop_strike.png')
        await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(1000)
        c = await page.evaluate(CARD)
        check('desktop: no-hand card centred and inside the viewport', c['shown'] and c['inCard'] and c['card'][0] > 40 and c['card'][1] < c['H'] - 40 and c['btn'][1] <= c['H'], c)
        await page.screenshot(path='tests/out/chrome_desktop_nohand.png')
        check('desktop: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
