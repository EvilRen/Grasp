import asyncio, subprocess, time, sys, math
from playwright.async_api import async_playwright
srv = subprocess.Popen(['python3','-m','http.server','8781','--bind','127.0.0.1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
FAKE = open('tests/fake_vision.mjs').read()
fails = 0
def check(name, cond, extra=''):
    global fails
    print(('PASS ' if cond else 'FAIL ') + name + (('  | ' + str(extra)) if extra != '' else ''))
    if not cond: fails += 1
async def routes(page):
    async def h(route):
        u = route.request.url
        if 'vision_bundle.mjs' in u: return await route.fulfill(status=200, content_type='text/javascript', body=FAKE, headers={'Access-Control-Allow-Origin':'*'})
        if 'fonts.g' in u: return await route.fulfill(status=200, body='')
        return await route.continue_()
    await page.route('**/*', h)
SYN = """
window.syn = (f, fs, secs, dispMm, noise, axis, jitter) => { // accelerometer samples for a displacement sine
  const out = [], A = dispMm / 1000 * Math.pow(2 * Math.PI * f, 2); let t = 1000;
  for (let i = 0; i < fs * secs; i++) { const v = [0,0,0].map(() => (Math.random() - 0.5) * 2 * noise);
    v[axis || 0] += A * Math.sin(2 * Math.PI * f * t / 1000); out.push({ t, v }); t += 1000 / fs * (1 + (Math.random() - 0.5) * (jitter || 0)); }
  return out; };
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True, permissions=['camera'])
        page = await ctx.new_page(); await routes(page); errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        await page.add_init_script(SYN)
        await page.goto('http://localhost:8781/index.html'); await page.wait_for_timeout(400)

        # ---- analysis unit tests ----
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0, 0.3)); return {f: r.f0, s: r.strength, pp: r.pp, fs: r.fs}; })()")
        check('5 Hz @60/s, jittery timing -> 5.0 Hz, clear', abs(r['f']-5) < 0.2 and r['s']=='clear', r)
        check('size estimate: 1 mm peak -> ~2 mm peak-to-peak', 1.7 < r['pp'] < 2.3, r['pp'])
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(15, 100, 20, 0.2, 0.05, 2)); return {f: r.f0, s: r.strength}; })()")
        check('15 Hz standing tremor @100/s, z axis -> 15 Hz', abs(r['f']-15) < 0.3 and r['s']=='clear', r)
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(8.5, 60, 20, 0.3, 0.05, 1)); return {f: r.f0}; })()")
        check('8.5 Hz on y axis -> 8.5 Hz', abs(r['f']-8.5) < 0.25, r)
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 0, 0.05, 0)); return {s: r.strength, ratio: r.ratio}; })()")
        check('noise only -> no clear rhythm', r['s']=='none', r)
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 0.02, 0.05, 0)); return {s: r.strength, f: r.f0, pp: r.pp}; })()")
        check('tiny tremor in noise -> found at 5 Hz, size reported tiny (<0.1 mm)', abs(r['f']-5) < 0.3 and r['pp'] < 0.1, r)
        await page.evaluate("(() => { const r = __tremor.analyze(syn(9, 60, 20, 0.02, 0.01, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'hold', plannedS:20}); renderResult(r); })()")
        check('tiny clear rhythm -> natural-shake note shown', 'natural shake' in await page.evaluate("$('resWarn').textContent"))
        await page.evaluate("show('setup')")
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 1, 1, 0.05, 0)); return r.error || ''; })()")
        check('1 s recording -> error, no fake result', 'short' in r or 'few' in r, r)
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(4.5, 25, 20, 1, 0.03, 0)); return {f: r.f0, nyq: r.nyq}; })()")
        check('camera-like 25/s still finds 4.5 Hz', abs(r['f']-4.5) < 0.25, r)

        # ---- setup constraints ----
        await page.tap('[data-key=sensor] [data-v=camera]')
        check('camera disables leg', await page.evaluate("document.querySelector('[data-key=limb] [data-v=leg]').disabled && __tremor.state.limb === 'hand'"))
        await page.tap('[data-key=sensor] [data-v=motion]'); await page.tap('[data-key=limb] [data-v=leg]'); await page.tap('[data-key=posture] [data-v=stand]')
        check('leg enables standing', await page.evaluate("__tremor.state.posture === 'stand'"))
        await page.tap('[data-key=limb] [data-v=hand]')
        check('hand drops standing back to rest', await page.evaluate("__tremor.state.posture === 'rest' && document.querySelector('[data-key=posture] [data-v=stand]').disabled"))
        await page.screenshot(path='tests/out/out_setup.png', full_page=True)

        # ---- motion flow: no sensor ----
        await page.evaluate("__tremor.CONFIG.RECORD_S = 6; __tremor.CONFIG.COUNTDOWN_S.motion = 1; __tremor.CONFIG.COUNTDOWN_S.camera = 1;")
        await page.tap('#startBtn'); await page.wait_for_timeout(2500)
        err = await page.evaluate("$('setupError').hidden ? '' : $('setupError').textContent")
        check('no motion events -> clear error on setup screen', 'No motion data' in err, err[:60])

        # ---- motion flow: 6 Hz leg standing via real devicemotion events ----
        await page.tap('[data-key=limb] [data-v=leg]'); await page.tap('[data-key=posture] [data-v=stand]')
        await page.evaluate("""window.__mi = setInterval(() => { const t = performance.now(), A = 0.8 * Math.pow(2*Math.PI*6, 2) / 1000;
            const a = { x: A * Math.sin(2*Math.PI*6*t/1000) + (Math.random()-0.5)*0.05, y: (Math.random()-0.5)*0.05, z: (Math.random()-0.5)*0.05 };
            window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: a, accelerationIncludingGravity: { x: a.x, y: a.y, z: a.z + 9.81 }, interval: 16 })); }, 16);""")
        await page.tap('#startBtn'); await page.wait_for_timeout(1700)
        await page.screenshot(path='tests/out/out_recording.png')
        await page.wait_for_timeout(6500)
        res = await page.evaluate("(() => { const r = __tremor.last; return r && {f: r.f0, s: r.strength, fs: r.fs, pp: r.pp, err: r.error}; })()")
        check('motion flow -> result screen with 6 Hz', bool(res) and abs(res['f']-6) < 0.3, res)
        check('result visible, history saved', await page.evaluate("!$('result').hidden && JSON.parse(localStorage.getItem('tremor.history.v1')).length === 1"))
        warn = await page.evaluate("$('resWarn').hidden ? '' : $('resWarn').textContent")
        fs = res['fs'] if res else 0
        check('standing with ~60/s: no false low-rate warning' if fs >= 36 else 'standing with low rate: warning shown', ('too slow' not in warn) if fs >= 36 else ('too slow' in warn), [round(fs), warn[:80]])
        await page.evaluate("clearInterval(window.__mi)")
        await page.screenshot(path='tests/out/out_result.png', full_page=True)

        # ---- cancel mid-recording ----
        await page.evaluate("window.__mi = setInterval(() => window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: {x:0,y:0,z:0}, interval: 16 })), 16);")
        await page.tap('#againBtn'); await page.wait_for_timeout(600); await page.tap('#cancelBtn'); await page.wait_for_timeout(8000)
        check('cancel returns to setup, no result, no new history', await page.evaluate("!$('setup').hidden && $('result').hidden && JSON.parse(localStorage.getItem('tremor.history.v1')).length === 1"))
        await page.evaluate("clearInterval(window.__mi)")

        # ---- camera flow: 4 Hz hand ----
        await page.tap('[data-key=sensor] [data-v=camera]'); await page.tap('[data-key=posture] [data-v=hold]')
        await page.evaluate("window.__camHz = 4; window.__camAmp = 0.005;")
        await page.tap('#startBtn'); await page.wait_for_timeout(9500)
        res = await page.evaluate("(() => { const r = __tremor.last; return r && {f: r.f0, s: r.strength, fs: r.fs, pp: r.pp, hand: r.handPct, sensor: r.sensor, err: r.error}; })()")
        check('camera flow -> 4 Hz, clear', res and res['sensor']=='camera' and abs(res['f']-4) < 0.3 and res['s']=='clear', res)
        check('camera size in mm plausible (~4 mm pp)', res and 3 < res['pp'] < 5.5, res and res['pp'])
        await page.screenshot(path='tests/out/out_camera_result.png', full_page=True)
        # camera: hand lost -> warning
        await page.evaluate("window.__camNoHand = true; setTimeout(() => window.__camNoHand = false, 4200)")
        await page.tap('#againBtn'); await page.wait_for_timeout(9500)
        warn = await page.evaluate("$('resWarn').textContent")
        check('hand lost for part of recording -> warning', 'lost' in warn, warn[:90])
        await page.tap('#clearHist'); 
        check('clear history', await page.evaluate("JSON.parse(localStorage.getItem('tremor.history.v1') || '[]').length === 0 && $('historyWrap').hidden"))
        check('no page errors', not errs, errs)
        await b.close()
    print('FAILURES:', fails)
asyncio.run(main()); srv.terminate()
sys.exit(1 if fails else 0)
