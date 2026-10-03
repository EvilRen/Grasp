import asyncio, subprocess, time, json, sys, re
from playwright.async_api import async_playwright
import socket as _sk
class _NoSrv:
    def terminate(self): pass
if _sk.socket().connect_ex(('127.0.0.1', 8765)) == 0: srv = _NoSrv()  # shared server from run_fast.sh
else: srv = subprocess.Popen(['python3','-m','http.server','8765','--bind','127.0.0.1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
MATTER = open('tests/vendor/matter.min.js').read(); THREE = open('tests/vendor/three.min.js').read(); FAKE = open('tests/fake_vision.mjs').read()
async def routes(page):
    async def h(route):
        u = route.request.url
        if 'matter' in u: return await route.fulfill(status=200, content_type='application/javascript', body=MATTER)
        if 'three' in u and u.endswith('three.min.js'): return await route.fulfill(status=200, content_type='application/javascript', body=THREE)
        if 'vision_bundle.mjs' in u: return await route.fulfill(status=200, content_type='text/javascript', body=FAKE, headers={'Access-Control-Allow-Origin':'*'})
        if '.wasm' in u or 'hand_landmarker.task' in u: return await route.fulfill(status=200, body=b'x'*2048, headers={'Access-Control-Allow-Origin':'*'})
        if 'fonts.g' in u: return await route.fulfill(status=200, body='')
        if '/_blob/probe' in u: return await route.fulfill(status=200, body='')
        return await route.continue_()
    await page.route('**/*', h)
INIT = "window.__created=[];window.__inputs=[];window.__closed=[];window.__handFor=null;"
INIT += "try { if (!localStorage.getItem('inputPref')) localStorage.setItem('inputPref', 'mouse'); } catch (e) {}"  # the start screen's tiles start a game at once with the remembered input: the suites play with the mouse unless they pick the camera
START_MOUSE = "(() => { if (mode !== 'none') return; setInputPref('mouse'); document.querySelector('.modes > button[aria-pressed=\"true\"]').click(); if (!$('advMap').hidden) $('advEndless').click(); })()"  # 'play the selected game with the mouse' (the old Play with mouse button; Strike: the Adventure map's Endless, the old run)
# Strike's renderer in the suites: by default (GRASP_GFX=2d) the 2D canvas; GRASP_GFX=3d runs the WebGL renderer at a low fixed pixel ratio, no
# shadows and no low-fps fallback (headless Chromium's WebGL is SwiftShader, a CPU rasterizer: full resolution runs at ~2-5 fps and falls back
# to 2D; even this light setup runs ~30 fps, so the frame-timing checks of test_strike.py flake in 3D here; test_strike3d.py sets its own)
import os
GFX = os.environ.get('GRASP_GFX', '2d')
INIT += "window.__graspGfx = { mode: '2d' };" if GFX == '2d' else "window.__graspGfx = { pr: 0.12, shadows: false, auto: false };"
HAND_JS = """
window.mkHand = (ax, ay, pd) => {  // ax, ay: pinch anchor in camera coords (0..1, NOT mirrored); pd: pinch distance / hand size
  const L = Array.from({length:21}, () => ({x: ax, y: ay + 0.12, z: 0}));
  const dx = pd * 72 / 640 / 2;
  L[0] = {x: ax, y: ay + 0.27, z:0}; L[9] = {x: ax, y: ay + 0.12, z:0};
  L[4] = {x: ax - dx, y: ay, z:0}; L[8] = {x: ax + dx, y: ay, z:0}; L[6] = {x: ax, y: ay + 0.07, z:0};
  for (const [tip, pip] of [[12,10],[16,14],[20,18]]) { L[tip] = {x: ax, y: ay - 0.05, z:0}; L[pip] = {x: ax, y: ay + 0.05, z:0}; }
  return L;
};
window.handAt = (X, Y, pd) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkHand(1 - (m + X / innerWidth * B), m + Y / innerHeight * B, pd); };
"""
def check(name, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + name + (('  | ' + str(extra)) if extra != '' else ''))
    if not cond: check.fails += 1
check.fails = 0
async def menu_click(page, sel, tap=False):  # Strike: the toolbar is one pause button whose sheet holds the toolbar's own buttons; elsewhere a plain click
    if await page.evaluate("document.body.classList.contains('minChrome') && mode !== 'none' && !menu.open"):
        await (page.tap('#pauseBtn') if tap else page.click('#pauseBtn')); await page.wait_for_function("menu.open", timeout=4000)
    await (page.tap(sel) if tap else page.click(sel))

async def boot(b, mobile):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(permissions=['camera'], **opts)
    page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    await page.click('#camBtn'); await page.click('.modes > button[aria-pressed=true]')
    await page.wait_for_function("mode === 'camera'", timeout=15000)
    return ctx, page, errs

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- Desktop: GPU first, auto-switch to CPU after 5s without a hand, then hand found ----
        ctx, page, errs = await boot(b, False)
        cr = await page.evaluate("__created")
        check('desktop starts on GPU', cr[0]['d'] == 'GPU', cr)
        check('thresholds 0.25 / 0.25 / 0.25 (cheap landmark tracking)', (cr[0]['det'], cr[0]['pres'], cr[0]['trk']) == (0.25, 0.25, 0.25), cr[0])
        rows = await page.evaluate("Object.fromEntries([...document.querySelectorAll('#checks li')].map(l=>[l.dataset.k, l.dataset.s + ': ' + l.querySelector('small').textContent]))")
        check('all 5 boot rows ok', all(v.startswith('ok') for v in rows.values()), rows)
        await page.wait_for_timeout(1500)
        check('no-hand screen shown', await page.evaluate("!statusEl.hidden && preview.classList.contains('big')"))
        live = await page.inner_text('#statusLive'); check('live line shows GPU + scans/s', 'GPU' in live and 'scans/s' in live, live)
        check('tracker reads a 320 px frame from the canvas, not the video', (await page.evaluate("__inputs.at(-1)")).startswith('CANVAS:320x240'), await page.evaluate("__inputs.at(-1)"))
        await page.wait_for_timeout(4500)
        check('auto-switched to CPU after ~5s', await page.evaluate("delegateUsed") == 'CPU', await page.evaluate("[delegateUsed, __created.map(c=>c.d), __closed]"))
        await page.wait_for_timeout(6500)
        check('never switches back to GPU', await page.evaluate("delegateUsed") == 'CPU' and await page.evaluate("__created.length") == 2)
        live = await page.inner_text('#statusLive'); check('live line now CPU', 'CPU' in live, live)
        await page.evaluate("window.__handFor = () => handAt(innerWidth*0.5, innerHeight*0.25, 0.8)")
        await page.wait_for_timeout(700)
        check('hand found -> screen hides, preview back to corner', await page.evaluate("statusEl.hidden && !preview.classList.contains('big') && cursor.present"))
        hudoff = await page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--hud-offset')")
        check('HUD pushed below small preview', hudoff.strip() not in ('', '0px'), hudoff)
        # a tracker that scans only every 110 ms (a phone's CPU tracker) still gives a cursor that moves every frame: predicted from the last two samples, then eased
        await page.evaluate("(() => { const orig = trackTick; let last = -1e9; window.__slowTrack = (on) => { trackTick = on ? (now) => { if (now - last < 110) return; last = now; orig(now); } : orig; }; })()")
        await page.evaluate("__slowTrack(true); window.__rec = []; window.__recOn = true; (function r(t) { if (!__recOn) return; __rec.push([t, cursor.x, hand.lastSeen]); requestAnimationFrame(r); })(performance.now())")
        n0 = await page.evaluate("__inputs.length")
        await page.evaluate("(() => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / 1200); return handAt(200 + 800 * k, innerHeight * 0.3, 0.8); }; })()")
        await page.wait_for_timeout(1000)
        scans = await page.evaluate("__inputs.length") - n0
        rec = await page.evaluate("__recOn = false; __rec"); await page.evaluate("__slowTrack(false)")
        gaps, tots, cnt, tot, seen = [], [], 0, 0, 0
        for i in range(1, len(rec)):  # frames grouped by the sample they follow; count the frames on which the cursor moved between two samples
            if rec[i][2] != rec[i - 1][2]:
                if seen: gaps.append(cnt); tots.append(tot)
                cnt = tot = 0; seen += 1
            else:
                tot += 1
                if rec[i][1] != rec[i - 1][1]: cnt += 1
        if len(gaps) > 3: gaps, tots = gaps[1:-1], tots[1:-1]
        # under load (parallel runs) fewer frames fit between two samples: judge the share of frames that moved, not a fixed count
        share = sorted(c / t for c, t in zip(gaps, tots) if t)[len(gaps) // 2] if gaps else 0
        check('stubbed tracker throttled to ~9 scans/s', 6 <= scans <= 12, scans)
        check('cursor moves on most frames between two 110 ms samples (smooth, not jumping)', len(gaps) >= 3 and max(gaps) >= 3 and share >= 0.6, [gaps, tots])
        check('raw tracker speed recorded (px/ms between samples)', await page.evaluate("hand.rawSpeed") >= 0 and await page.evaluate("hand.samples.length") >= 2, await page.evaluate("[hand.rawSpeed, hand.samples.length]"))
        await page.click('#hudBtn'); await page.wait_for_timeout(700)
        hud = await page.inner_text('#hud')
        check('HUD shows scans/s and the cursor latency in ms', 'Scans/s' in hud and re.search(r'Cursor latency\s+\d+ ms', hud) is not None, hud)
        await page.click('#hudBtn'); await page.wait_for_timeout(100)

        # grab + throw with the camera pipeline
        await page.evaluate("for (const b of bodies) { M.Body.setStatic(b, false); } engine.gravity.y = 0; for (const b of bodies) { M.Body.setVelocity(b,{x:0,y:0}); M.Body.setAngularVelocity(b,0); }")
        tgt = await page.evaluate("(() => { const b = bodies[0]; M.Body.setPosition(b, {x: innerWidth*0.4, y: innerHeight*0.5}); return {x: b.position.x, y: b.position.y}; })()")
        await page.evaluate(f"window.__handFor = () => handAt({tgt['x']}, {tgt['y']}, 0.8)"); await page.wait_for_timeout(500)
        await page.evaluate(f"window.__handFor = () => handAt({tgt['x']}, {tgt['y']}, 0.1)"); await page.wait_for_timeout(400)
        st = await page.evaluate("__grasp.state"); check('pinch grabs object', st['held'] == 0, st)
        for i in range(1, 9):
            await page.evaluate(f"window.__handFor = () => handAt({tgt['x']} + {i*45}, {tgt['y']}, 0.1)"); await page.wait_for_timeout(35)
        await page.evaluate(f"window.__handFor = () => handAt({tgt['x']} + 380, {tgt['y']}, 0.8)"); await page.wait_for_timeout(200)
        st = await page.evaluate("__grasp.state"); check('open hand throws', st['held'] == -1 and st['lastThrow'] > 3, st)
        # hand loss while holding = drop, no throw
        await page.evaluate("lastThrow = 0; const b = bodies[1]; M.Body.setPosition(b, {x: innerWidth*0.6, y: innerHeight*0.6}); M.Body.setVelocity(b,{x:0,y:0});")
        t2 = await page.evaluate("({x: bodies[1].position.x, y: bodies[1].position.y})")
        await page.evaluate(f"window.__handFor = () => handAt({t2['x']}, {t2['y']}, 0.8)"); await page.wait_for_timeout(400)
        await page.evaluate(f"window.__handFor = () => handAt({t2['x']}, {t2['y']}, 0.1)"); await page.wait_for_timeout(400)
        held = (await page.evaluate("__grasp.state"))['held']
        await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(500)
        st = await page.evaluate("__grasp.state"); check('hand lost -> drop without throw', held == 1 and st['held'] == -1 and st['lastThrow'] == 0, [held, st])
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---- Phone: CPU first, no auto-switch, manual switch button both ways ----
        ctx, page, errs = await boot(b, True)
        check('phone starts on CPU', (await page.evaluate("__created"))[0]['d'] == 'CPU')
        await page.wait_for_timeout(1500)
        await page.screenshot(path='tests/out/phone_nohand.png')
        box = await page.evaluate("(() => { const r = $('swapBtn').getBoundingClientRect(), p = preview.getBoundingClientRect(); return {btn:[r.top,r.bottom], prev:[p.top,p.bottom], H: innerHeight}; })()")
        check('switch button visible, below preview, on screen', box['btn'][0] > box['prev'][1] and box['btn'][1] < box['H'], box)
        await page.wait_for_timeout(5000)
        check('phone on CPU is not auto-switched', await page.evaluate("delegateUsed") == 'CPU')
        await page.tap('#swapBtn'); await page.wait_for_timeout(1200)
        check('button switches CPU -> GPU', await page.evaluate("delegateUsed") == 'GPU', await page.inner_text('#statusLive'))
        await page.tap('#swapBtn'); await page.wait_for_timeout(1200)
        check('button switches GPU -> CPU', await page.evaluate("delegateUsed") == 'CPU', await page.inner_text('#statusLive'))
        await page.evaluate("window.__handFor = () => handAt(innerWidth*0.5, innerHeight*0.3, 0.8)"); await page.wait_for_timeout(600)
        check('phone: hand found hides screen + button', await page.evaluate("statusEl.hidden && getComputedStyle($('status')).opacity !== '1'"))
        await page.screenshot(path='tests/out/phone_hand.png')
        check('phone: no page errors', not errs, errs); await ctx.close()

        # ---- Mouse fallback: drag + flick throw ----
        ctx = await b.new_context(viewport={'width':1280,'height':800}); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600); await page.evaluate(START_MOUSE)
        await page.evaluate("engine.gravity.y = 0; const b = bodies[2]; M.Body.setPosition(b,{x:400,y:400}); M.Body.setVelocity(b,{x:0,y:0});"); await page.wait_for_timeout(100)
        await page.mouse.move(400, 400); await page.mouse.down(); await page.wait_for_timeout(100)
        st = await page.evaluate("__grasp.state"); check('mouse grabs', st['held'] == 2, st)
        for i in range(1, 8): await page.mouse.move(400 + i*40, 400); await page.wait_for_timeout(16)
        await page.mouse.up(); await page.wait_for_timeout(50)
        st = await page.evaluate("__grasp.state"); check('mouse throws', st['held'] == -1 and st['lastThrow'] > 3, st)
        check('mouse: status stays hidden', await page.evaluate("statusEl.hidden"))
        await page.click('#homeBtn'); await page.wait_for_timeout(100)
        check('home returns to start screen', await page.evaluate("mode === 'none' && !$('start').hidden && preview.hidden"))
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(100)
        check('can start again after home', await page.evaluate("mode === 'mouse' && $('start').hidden"))
        check('mouse: no page errors', not errs, errs); await ctx.close()

        # ---- Perf: 10 objects bouncing in the phone viewport must keep a playable frame rate (headless is slower than a phone) ----
        ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600); await page.evaluate(START_MOUSE); await page.wait_for_timeout(300)
        KICK = "engine.gravity.y = 0; for (const b of bodies) { M.Body.setVelocity(b, {x: (Math.random()-0.5)*16, y: (Math.random()-0.5)*16}); M.Body.setAngularVelocity(b, 0.1); }"
        fpss = []
        for _ in range(4):  # re-kick every half second so all 10 keep flying (walls soak up speed)
            await page.evaluate(KICK); await page.wait_for_timeout(550); fpss.append(await page.evaluate("__grasp.state.fps"))
        moving = await page.evaluate("bodies.filter(b => b.speed > 1).length")
        check('phone perf: objects in motion, >= 30 fps over 2 s', min(fpss[1:]) >= 30 and moving >= 1, {'fps': [round(f) for f in fpss], 'moving': moving})
        check('sprites cached, not rebuilt per frame', await page.evaluate("SPRITES.size") <= 16, await page.evaluate("[...SPRITES.keys()]"))
        check('perf: no page errors', not errs, errs); await ctx.close()

        # ---- Hebrew: language button, RTL, persistence, phone layout ----
        ctx = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True); page = await ctx.new_page(); await routes(page); errs=[]
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
        check('defaults to English', await page.evaluate("document.documentElement.dir") == 'ltr')
        await page.tap('#startLang'); await page.wait_for_timeout(100)
        st = await page.evaluate("({dir: document.documentElement.dir, lang: document.documentElement.lang, cam: $('camBtn').textContent, desc: $('modeDesc').textContent})")
        check('language button switches to Hebrew RTL', st['dir'] == 'rtl' and st['lang'] == 'he' and st['cam'] == 'מצלמה' and 'המצלמה' in st['desc'], st)
        await page.screenshot(path='tests/out/he_start.png')
        await page.reload(); await page.wait_for_timeout(600)
        check('Hebrew persists after reload', await page.evaluate("document.documentElement.lang") == 'he')
        await page.evaluate(START_MOUSE); await page.wait_for_timeout(200); await page.tap('#hudBtn'); await page.wait_for_timeout(700)
        check('HUD in Hebrew', 'מחווה' in await page.inner_text('#hud'))
        ov = await page.evaluate("(() => { const r = [...document.querySelectorAll('.chrome .chip')].map(b => b.getBoundingClientRect()); return {minLeft: Math.min(...r.map(x => x.left)), maxRight: Math.max(...r.map(x => x.right)), W: innerWidth}; })()")
        check('phone: top buttons fit on screen', ov['minLeft'] >= 0 and ov['maxRight'] <= ov['W'], ov)
        await page.screenshot(path='tests/out/he_game.png')
        await page.tap('.chrome .langBtn'); await page.wait_for_timeout(100)
        check('in-game button switches back to English', await page.evaluate("document.documentElement.dir === 'ltr' && $('resetBtn').title === 'Reset' && $('resetBtn').getAttribute('aria-label') === 'Reset'"))
        check('Hebrew: no page errors', not errs, errs)
        await b.close()
    print('FAILURES:', check.fails)
    if check.fails: sys.exit(1)
asyncio.run(main()); srv.terminate()
