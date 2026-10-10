import asyncio, subprocess, time, sys, math, json, base64, os
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
// slow drift (sum of sines up to `top` Hz, falling 1/k), optional tremor on x; accelerometer units
window.drift = (fs, secs, amp, top, seed, tremF, tremMm) => { let s = seed || 1; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const comps = Array.from({ length: 8 }, (_, i) => [0.1 + (top - 0.1) * i / 7 * (0.85 + 0.3 * rnd()), 1 / (1 + i), rnd() * 6.28]); const out = []; let t = 1000;
  for (let i = 0; i < fs * secs; i++) { const tt = t / 1000; let d = 0; for (const [f, a, ph] of comps) d += amp * a * Math.sin(2 * Math.PI * f * tt + ph);
    const v = [d + (rnd() - 0.5) * 0.1, (rnd() - 0.5) * 0.1, (rnd() - 0.5) * 0.1];
    if (tremF) v[0] += tremMm / 1000 * Math.pow(2 * Math.PI * tremF, 2) * Math.sin(2 * Math.PI * tremF * tt);
    out.push({ t, v }); t += 1000 / fs; } return out; };
"""
MOTION6 = """window.__mi = setInterval(() => { const t = performance.now(), A = 0.8 * Math.pow(2*Math.PI*6, 2) / 1000;
    const a = { x: A * Math.sin(2*Math.PI*6*t/1000) + (Math.random()-0.5)*0.05, y: (Math.random()-0.5)*0.05, z: (Math.random()-0.5)*0.05 };
    window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: a, accelerationIncludingGravity: { x: a.x, y: a.y, z: a.z + 9.81 }, interval: 16 })); }, 16);"""
# old v1 summary history (migrated into the v2 journal on first load)
SEED = """(n) => { const h = []; for (let i = 0; i < n; i++) h.push({ ts: Date.now() - (n - i) * 864e5, sensor: 'motion', limb: 'hand', posture: 'rest', side: i % 2 ? 'right' : 'left',
    f: +(5 + Math.sin(i / 3)).toFixed(2), strength: ['clear','weak','none'][i % 3], pp: +(1 + i / 20).toFixed(2), fs: 60, med: i % 4 ? '' : 'yes', medText: '', note: i === 3 ? 'walk' : '', tod: 'morning' });
    localStorage.removeItem('tremor.journal.v2'); localStorage.setItem('tremor.history.v1', JSON.stringify(h.reverse())); return __tremor.journal.reload().length; }"""
PIX = """(() => { const cv = $('trend'), c = cv.getContext('2d'), d = c.getImageData(0, 0, cv.width, cv.height).data; let sky = 0, coral = 0;
    for (let i = 0; i < d.length; i += 4) { if (d[i] < 120 && d[i+1] > 150 && d[i+2] > 190) sky++; if (d[i] > 230 && d[i+1] > 90 && d[i+1] < 130 && d[i+2] < 110) coral++; }
    return { pts: __tremor.trend.pts.length, sky, coral, hidden: cv.hidden, w: cv.width }; })()"""
JN = "JSON.parse(localStorage.getItem('tremor.journal.v2') || '[]')"
CMP = """(() => { const L = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0)), R = __tremor.analyze(syn(6.5, 60, 20, 0.5, 0.05, 0));
    Object.assign(L, {sensor:'motion', limb:'hand', posture:'rest', side:'left', ts: Date.now(), plannedS:20}); Object.assign(R, {sensor:'motion', limb:'hand', posture:'rest', side:'right', ts: Date.now(), plannedS:20});
    R.compare = { left: L, right: { ...R } }; renderResult(R); })()"""
V2 = """
window.mkE = (o) => Object.assign({ id: 'e' + Math.random().toString(36).slice(2, 10), ts: Date.now(), kind: 'tremor', sensor: 'motion', limb: 'hand', posture: 'rest', f: 5, pp: 1, strength: 'clear',
  ratio: 30, fs: 60, nyq: 30, dur: 20, n: 1200, side: '', med: '', tags: [], q: { s: 90, lv: 'good', r: [] } }, o);
window.seedJ = (arr) => { localStorage.setItem('tremor.journal.v2', JSON.stringify(arr)); return __tremor.journal.reload().length; };
window.spiralPts = (o) => { const pts = [], n = Math.round(o.secs * o.fs);
  for (let i = 0; i < n; i++) { const u = i / (n - 1), th = u * o.turns * 2 * Math.PI, t = 1000 + i * 1000 / o.fs;
    const r = o.b * th + (o.wobPx || 0) * Math.sin(2 * Math.PI * (o.wobHz || 0) * t / 1000) + (Math.random() - 0.5) * (o.noisePx || 0);
    pts.push({ t, x: o.cx + r * Math.cos(th), y: o.cy + r * Math.sin(th) }); } return pts; };
window.drawSpiralLive = (secs, wobHz, wobPx) => new Promise((done) => { // real-time pointer events on the canvas (timestamps are real)
  const cv = document.getElementById('spCanvas'); cv.scrollIntoView({ block: 'center' }); const r = cv.getBoundingClientRect(), g = __tremor.spiralGeom(), t0 = performance.now(), T = secs * 1000;
  const ev = (type, p) => cv.dispatchEvent(new PointerEvent(type, { clientX: r.left + p[0], clientY: r.top + p[1], pointerId: 7, pointerType: 'touch', isPrimary: true, bubbles: true, cancelable: true }));
  const pos = (now) => { const u = Math.min(1, (now - t0) / T), th = u * 2.6 * 2 * Math.PI, rr = g.b * th + wobPx * Math.sin(2 * Math.PI * wobHz * (now - t0) / 1000); return [g.cx + rr * Math.cos(th), g.cy + rr * Math.sin(th)]; };
  ev('pointerdown', pos(t0));
  const id = setInterval(() => { const now = performance.now(); ev('pointermove', pos(now)); if (now - t0 >= T) { clearInterval(id); ev('pointerup', pos(now)); done(); } }, 16); });
window.noisy = () => { const s = syn(5, 60, 20, 0.3, 0.6, 0, 1.4);
  const out = s.filter((p, i) => !((i > 200 && i < 270) || (i > 600 && i < 670) || (i > 900 && i < 970)));
  for (const k of [60, 170, 330, 480, 560, 720, 800, 900]) { const j = Math.min(out.length - 8, k); for (let m = 0; m < 6; m++) out[j + m].v[0] += 15 * (m % 2 ? -1 : 1); }
  return out; };
window.__said = [];
try { Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { speak: (u) => window.__said.push(u.text), cancel: () => {}, getVoices: () => [] } }); } catch (e) {}
if (typeof SpeechSynthesisUtterance === 'undefined') window.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };
window.__notes = [];
window.Notification = class { constructor(title, o) { window.__notes.push({ title, body: o && o.body }); } static requestPermission() { return Promise.resolve(window.Notification.permission); } };
window.Notification.permission = 'granted';
window.__printed = 0; window.print = () => { window.__printed++; };
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
        r = await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 0.02, 0.05, 0)); return {s: r.strength, f: r.f0, pp: r.pp}; })()")  # weak or clear
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
        await page.tap('[data-key=posture] [data-v=action]'); await page.tap('[data-key=limb] [data-v=leg]')
        check('v2: "Moving" (finger to nose) is for the hand only: leg drops it back to rest', await page.evaluate("__tremor.state.posture === 'rest' && document.querySelector('[data-key=posture] [data-v=action]').disabled"))
        await page.tap('[data-key=limb] [data-v=hand]')
        await page.screenshot(path='tests/out/out_setup.png', full_page=True)

        # ---- motion flow: no sensor ----
        await page.evaluate("__tremor.CONFIG.RECORD_OVERRIDE_S = 6; __tremor.CONFIG.COUNTDOWN_S.motion = 1; __tremor.CONFIG.COUNTDOWN_S.camera = 1;")
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
        check('result visible, saved in the journal', await page.evaluate("!$('result').hidden && " + JN + ".length === 1"))
        warn = await page.evaluate("$('resWarn').hidden ? '' : $('resWarn').textContent")
        fs = res['fs'] if res else 0
        check('standing with ~60/s: no false low-rate warning' if fs >= 36 else 'standing with low rate: warning shown', ('too slow' not in warn) if fs >= 36 else ('too slow' in warn), [round(fs), warn[:80]])
        await page.evaluate("clearInterval(window.__mi)")
        await page.screenshot(path='tests/out/out_result.png', full_page=True)

        # ---- cancel mid-recording ----
        await page.evaluate("window.__mi = setInterval(() => window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: {x:0,y:0,z:0}, interval: 16 })), 16);")
        await page.tap('#againBtn'); await page.wait_for_timeout(600); await page.tap('#cancelBtn'); await page.wait_for_timeout(8000)
        check('cancel returns to setup, no result, no new journal entry', await page.evaluate("!$('setup').hidden && $('result').hidden && " + JN + ".length === 1"))
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
        await page.evaluate("__tremor.goTab('journal')"); nj = await page.evaluate(JN + ".length"); await page.tap('#clearHist'); await page.wait_for_timeout(150)
        check('delete all asks first (in-app sheet with the count)', nj >= 2 and await page.evaluate("!$('confirm').hidden && $('confirmTxt').textContent.includes('Delete all " + str(nj) + "')"), nj)
        await page.tap('#confirmNo'); await page.wait_for_timeout(100)
        check('delete all: Cancel keeps everything', await page.evaluate("$('confirm').hidden && " + JN + ".length === " + str(nj)))
        await page.tap('#clearHist'); await page.tap('#confirmYes'); await page.wait_for_timeout(150)
        check('delete all: confirmed -> journal empty, empty-state shown', await page.evaluate(JN + ".length === 0 && !$('jEmpty').hidden"))
        await page.evaluate("__tremor.goTab('setup')")

        # ---- quality guard: both cases covered ----
        await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 0, 0.001, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', plannedS:20}); renderResult(r); })()")
        check('almost no movement -> "still" warning with advice', 'Almost no movement' in await page.evaluate("$('resWarn').textContent"))
        await page.evaluate("(() => { const r = __tremor.analyze(syn(4, 16, 20, 1, 0.05, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', plannedS:20}); renderResult(r); })()")
        check('16/s sample rate -> low-rate warning with advice', 'Low sample rate' in await page.evaluate("$('resWarn').textContent"))
        await page.evaluate("__tremor.setLang('he')")
        check('warnings translated', 'קצב דגימה נמוך' in await page.evaluate("$('resWarn').textContent"))
        await page.evaluate("__tremor.setLang('en'); show('setup')")

        # ---- notes saved with the measurement ----
        await page.tap('[data-key=sensor] [data-v=motion]'); await page.tap('[data-key=limb] [data-v=hand]'); await page.tap('[data-key=posture] [data-v=rest]')
        await page.tap('[data-key=side] [data-v=left]'); await page.tap('[data-key=med] [data-v=yes]')
        check('medication text field appears on "yes"', await page.evaluate("!$('medText').hidden"))
        await page.fill('#medText', 'levodopa'); await page.fill('#noteText', 'after coffee')
        check('notes persisted in localStorage', await page.evaluate("JSON.parse(localStorage.getItem('tremor.notes.v1')).note === 'after coffee'"))
        await page.evaluate(MOTION6)
        await page.tap('#startBtn'); await page.wait_for_function("!$('result').hidden", timeout=15000)
        e = await page.evaluate(JN + "[0]")
        check('journal entry carries side, medication, note, quality, downsampled spectrum', e['side']=='left' and e['med']=='yes' and e['medText']=='levodopa' and e['note']=='after coffee' and e['q']['lv'] in ('good','fair','low') and len(e['spec']['p']) > 50 and max(e['spec']['p']) == 1000, {k: e[k] for k in ('side','med','note','q')})
        await page.evaluate("__tremor.goTab('journal')"); await page.wait_for_timeout(100)
        ht = await page.evaluate("$('jList').textContent")
        check('journal list shows the notes', 'levodopa' in ht and 'after coffee' in ht and 'left' in ht and 'Today' in ht, ht[:160])
        await page.tap('#jList .jitem'); await page.wait_for_timeout(150)
        check('result shows side and notes', 'left side' in await page.evaluate("$('resSub').textContent") and 'levodopa' in await page.evaluate("$('resNotes').textContent"))

        # ---- compare sides flow ----
        await page.evaluate("__tremor.CONFIG.COMPARE_GAP_S = 1")
        await page.evaluate("__tremor.goTab('setup')"); await page.tap('#compareBtn')
        await page.wait_for_function("$('recSide').textContent.includes('Left')", timeout=3000)
        check('compare: left side prompt during first countdown', True)
        await page.wait_for_function("$('recStatus').textContent.includes('right side')", timeout=15000)
        check('compare: right-side prompt + countdown between measurements', await page.evaluate("$('recNote').textContent.includes('right') && $('count').textContent !== ''"))
        await page.wait_for_function("!$('compareCard').hidden", timeout=20000)
        cmp = await page.evaluate("(() => { const c = __tremor.last.compare; return { l: c.left.side, r: c.right.side, lf: c.left.f0, rf: c.right.f0, cells: $('cmpGrid').children.length, diff: $('cmpDiff').textContent }; })()")
        check('compare card: two results, left then right, ~6 Hz each', cmp['l']=='left' and cmp['r']=='right' and abs(cmp['lf']-6) < 0.3 and abs(cmp['rf']-6) < 0.3 and cmp['cells']==12 and 'Difference' in cmp['diff'], cmp)
        sides = await page.evaluate(JN + ".slice(0,2).map(e => e.side)")
        check('compare: both measurements saved with sides', sides == ['right', 'left'], sides)
        await page.evaluate("clearInterval(window.__mi)")
        await page.screenshot(path='tests/out/out_compare.png', full_page=True)

        # ---- trend chart (Trends tab) from the old v1 history, migrated into the journal ----
        n = await page.evaluate(SEED, 1); await page.evaluate("__tremor.goTab('trends')"); await page.wait_for_timeout(150)
        check('migration: 1 old v1 entry -> 1 journal entry; trend empty state', n == 1 and await page.evaluate("!$('trendEmpty').hidden && $('trend').hidden"))
        await page.tap('.chips[data-f=range] [data-v=all]')
        n = await page.evaluate(SEED, 6); await page.evaluate("__tremor.goTab('journal'); __tremor.goTab('trends')"); await page.wait_for_timeout(250)
        drawn = await page.evaluate(PIX)
        check('trend: 6 migrated points drawn (sky median line + coral dots)', n == 6 and drawn['pts']==6 and drawn['sky'] > 150 and drawn['coral'] > 20 and not drawn['hidden'], drawn)
        await page.tap('.chips[data-f=side] [data-v=left]'); await page.wait_for_timeout(150)
        check('trend: side filter -> 3 left points', await page.evaluate("__tremor.trend.pts.length === 3 && __tremor.trend.pts.every(p => p.side === 'left')"))
        await page.tap('.chips[data-f=limb] [data-v=leg]'); await page.wait_for_timeout(150)
        check('trend: body-part filter (leg -> empty)', await page.evaluate("!$('trendEmpty').hidden"))
        await page.tap('.chips[data-f=limb] [data-v=all]'); await page.tap('.chips[data-f=side] [data-v=both]'); await page.wait_for_timeout(150)
        box = await page.evaluate("(() => { const r = $('trend').getBoundingClientRect(); return { x: r.left + __tremor.trend.xs[2], y: r.top + 60 }; })()")
        await page.mouse.click(box['x'], box['y']); await page.wait_for_timeout(100)
        info = await page.evaluate("$('trendInfo').textContent")
        check('trend: tap a point -> highlighted with details + Open', await page.evaluate("__tremor.trend.sel === 2") and 'Hz' in info and 'mm' in info and 'Open' in info, info)
        await page.tap('#trendOpen'); await page.wait_for_timeout(150)
        check('trend: Open -> the saved result (no spectrum kept for old entries), Back -> Trends', await page.evaluate("!$('result').hidden && $('spectrum').hidden && !$('resBack').hidden"))
        await page.tap('#resBack'); await page.wait_for_timeout(100)
        check('trend: Back returns to Trends', await page.evaluate("!$('trends').hidden"))
        n = await page.evaluate(SEED, 50); await page.evaluate("__tremor.goTab('journal'); __tremor.goTab('trends')"); await page.wait_for_timeout(150)
        check('trend: handles 50 points', await page.evaluate("__tremor.trend.pts.length === 50 && __tremor.trend.xs.length === 50"))

        # ---- export CSV ----
        await page.evaluate("__tremor.goTab('journal')")
        async with page.expect_download() as dl:
            await page.tap('#exportBtn')
        d = await dl.value; csv = open(await d.path(), encoding='utf-8-sig').read().splitlines()
        check('export: CSV download with header row + 50 rows', csv[0] == 'date,kind,sensor,limb,posture,side,freq_hz,size_mm,strength,quality,tags,medication,note' and len(csv) == 51 and d.suggested_filename.endswith('.csv'), [csv[0], len(csv)])
        check('export: rows carry side/medication/note', any(',left,' in l and ',yes,' in l for l in csv[1:]) and any(l.endswith(',walk') for l in csv[1:]), csv[1])

        # ---- share fallback ----
        await page.evaluate("Object.defineProperty(navigator, 'share', { value: undefined, configurable: true }); navigator.clipboard.writeText = (s) => { window.__copied = s; return Promise.resolve(); };")
        await page.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', side:'left', notes:{med:'yes', medText:'levodopa'}, ts: Date.now(), plannedS:20}); renderResult(r); })()")
        await page.tap('#shareBtn'); await page.wait_for_timeout(200)
        copied = await page.evaluate("window.__copied || ''")
        check('share: no navigator.share -> clipboard copy + toast', '5.0 Hz' in copied and 'left side' in copied and 'levodopa' in copied and await page.evaluate("$('toast').classList.contains('on') && $('toast').textContent.includes('Copied')"), copied)
        check('no page errors', not errs, errs)

        # ---- Hebrew RTL screenshots at 360x740 ----
        ctx2 = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = await ctx2.new_page(); await routes(pg); errs2 = []; pg.on('pageerror', lambda e: errs2.append(str(e)))
        await pg.add_init_script(SYN); await pg.add_init_script("localStorage.setItem('lang', 'he'); localStorage.setItem('tremor.notes.v1', JSON.stringify({side:'left', med:'yes', medText:'לבודופה', note:'אחרי קפה'}))")
        await pg.goto('http://localhost:8781/index.html'); await pg.wait_for_timeout(300)
        await pg.evaluate(SEED, 8); await pg.evaluate("show('setup')"); await pg.wait_for_timeout(200)
        check('he: RTL + Hebrew brand', await pg.evaluate("document.documentElement.dir === 'rtl' && document.querySelector('.brand').textContent.includes('טרימורטי')"))
        check('he: no horizontal overflow on setup', await pg.evaluate("document.documentElement.scrollWidth <= 360"))
        await pg.screenshot(path='tests/out/he_setup.png', full_page=True)
        await pg.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', side:'left', notes:{med:'yes', medText:'לבודופה', note:'אחרי קפה'}, ts: Date.now(), plannedS:20}); renderResult(r); })()")
        await pg.wait_for_timeout(200); await pg.screenshot(path='tests/out/he_result.png', full_page=True)
        await pg.evaluate(CMP)
        await pg.wait_for_timeout(200)
        check('he: compare card rendered', await pg.evaluate("!$('compareCard').hidden && $('cmpDiff').textContent.includes('הפרש')"))
        await pg.evaluate("$('compareCard').scrollIntoView()"); await pg.screenshot(path='tests/out/he_compare.png', full_page=True)
        await pg.evaluate("__tremor.goTab('trends')"); await pg.tap('.chips[data-f=range] [data-v=all]'); await pg.wait_for_timeout(200)
        await pg.evaluate("(() => { const r = $('trend').getBoundingClientRect(); $('trend').dispatchEvent(new MouseEvent('click', { clientX: r.left + __tremor.trend.xs[4], clientY: r.top + 50, bubbles: true })); })()")
        await pg.wait_for_timeout(100)
        check('he: trend point details in Hebrew with LTR number island', '⁦' in await pg.evaluate("$('trendInfo').textContent"))
        await pg.screenshot(path='tests/out/he_history.png')
        await pg.evaluate("window.scrollTo(0,0)"); await pg.screenshot(path='tests/out/he_history_full.png', full_page=True)
        check('he: no horizontal overflow on history', await pg.evaluate("document.documentElement.scrollWidth <= 360"))
        # ---- actionable errors: blocked motion sensor (Brave), camera busy; both languages ----
        await pg.evaluate("window.scrollTo(0,0); show('setup'); __tremor.setLang('en'); navigator.brave = { isBrave: () => Promise.resolve(true) }; DeviceMotionEvent.requestPermission = () => Promise.resolve('denied');")
        await pg.tap('[data-key=sensor] [data-v=motion]'); await pg.tap('#startBtn'); await pg.wait_for_timeout(300)
        err = await pg.evaluate("$('setupError').hidden ? '' : $('setupError').textContent")
        check('motion denied -> site-settings steps, Brave named, Reload button', 'Motion sensors' in err and 'Brave' in err and 'Shields' in err and await pg.evaluate("$('errAction').textContent === 'Reload'"), err[:100])
        await pg.evaluate("__tremor.setLang('he')")
        err = await pg.evaluate("$('setupError').textContent")
        check('motion denied (he) -> translated with Brave + reload button', 'חיישני תנועה' in err and 'Brave' in err and await pg.evaluate("$('errAction').textContent === 'טעינה מחדש'"), err[:80])
        await pg.screenshot(path='tests/out/he_error.png')
        await pg.tap('[data-key=limb] [data-v=leg]')
        check('changing a setup option hides the error box', await pg.evaluate("$('setupError').hidden"))
        await pg.evaluate("__tremor.setLang('en'); navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error('busy'), { name: 'NotReadableError' })); 0")
        await pg.tap('[data-key=sensor] [data-v=camera]'); await pg.tap('#startBtn'); await pg.wait_for_timeout(400)
        err = await pg.evaluate("$('setupError').hidden ? '' : $('setupError').textContent")
        check('camera busy -> names another tab (Grasp), Try again button', 'another tab' in err and 'Grasp' in err and await pg.evaluate("$('errAction').textContent === 'Try again'"), err[:100])
        await pg.tap('#errAction'); await pg.wait_for_timeout(400)
        check('try again re-runs the camera start (fails again with the stub)', await pg.evaluate("!$('setupError').hidden && $('setupError').textContent.includes('Grasp')"))
        await pg.evaluate("__tremor.setLang('he')")
        err = await pg.evaluate("$('setupError').textContent")
        check('camera busy (he) -> translated + try-again button', 'Grasp' in err and 'לשונית' in err and await pg.evaluate("$('errAction').textContent === 'ניסיון נוסף'"), err[:80])
        check('he: no page errors', not errs2, errs2)
        # ---- interpretation panel: which tremor types match + typical values by age (phone 360x740) ----
        ctx3 = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pi = await ctx3.new_page(); await routes(pi); errs3 = []; pi.on('pageerror', lambda e: errs3.append(str(e)))
        await pi.add_init_script(SYN); await pi.add_init_script("if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.setItem('lang', 'en'); localStorage.removeItem('tremor.notes.v1'); }")
        await pi.goto('http://localhost:8781/index.html'); await pi.wait_for_timeout(300)
        RENDER = """([args, ctx]) => { const r = __tremor.analyze(syn(...args)); Object.assign(r, { plannedS: 20, ts: Date.now(), notes: {} }, ctx); renderResult(r); return r; }"""
        INFO = """(() => { const r = __tremor.last, rows = [...document.querySelectorAll('#fscale .fs-row')], mk = $('fsMark');
            return { ids: [...document.querySelectorAll('#matchList li')].map(li => li.dataset.id), rank: __tremor.interpret(r).map(m => m.id),
              rows: rows.length, top: rows.filter(x => x.classList.contains('top')).map(x => x.dataset.id), mark: mk && parseFloat(mk.style.left),
              why: $('matchList').textContent, warn: $('resWarn').hidden ? '' : $('resWarn').textContent, hidden: $('interpCard').hidden,
              safety: $('safety').textContent, sw: document.documentElement.scrollWidth, f: r.f0 }; })()"""
        # setup: one side / both sides note
        await pi.tap('[data-key=sides] [data-v=one]')
        check('setup: "one side / both sides" note saved', await pi.evaluate("JSON.parse(localStorage.getItem('tremor.notes.v1')).sides === 'one'"))
        await pi.screenshot(path='tests/out/interp_setup.png', full_page=True)
        # 3 Hz at rest, one side -> rest-tremor bands first
        await pi.evaluate(RENDER, [[3, 60, 20, 1.5, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest','side':'left','notes':{'sides':'one'}}])
        await pi.wait_for_timeout(150); i = await pi.evaluate(INFO)
        check('interp: 9 coloured bands on the scale, peak marker at 3 Hz', i['rows'] == 9 and i['mark'] is not None and abs(i['mark'] - (3-1)/19*100) < 1.0 and not i['hidden'], [i['rows'], i['mark']])
        check('interp: 3 Hz rest one-sided -> Parkinsonian rest tremor first (rest bands lead)', i['ids'][0] == 'pd' and i['rank'][0] == 'pd' and 'pd' in i['top'] and i['rank'].index('ortho') > 4 and i['rank'].index('phys') > 3, i['rank'])
        check('interp: why line names rate, posture and side', '3.0 Hz, at rest, one side' in i['why'] and '→' in i['why'], i['why'][:140])
        check('interp: careful wording (resembles, not a diagnosis, never "you have")', 'resembles' in await pi.evaluate("$('interpCard').textContent") and 'you have' not in (await pi.evaluate("$('interpCard').textContent")).lower())
        check('v2 band: 3.0 Hz is now mid-band (analysed down to 1.5 Hz) -> no edge warning', 'measured range' not in i['warn'] and abs(i['f'] - 3) < 0.1, i['warn'][:120])
        check('safety note visible (EN): not a diagnosis, neurologist, repeat 3–4 times both hands', all(k in i['safety'] for k in ['Not a diagnosis', 'neurologist', 'Take your measurements', '3–4 times', 'both hands', 'held out']) and await pi.evaluate("$('safety').getBoundingClientRect().height > 40"), i['safety'][:80])
        check('phone 360: no horizontal scroll on result with interpretation', i['sw'] <= 360, i['sw'])
        await pi.screenshot(path='tests/out/interp_rest_en.png', full_page=True)
        await pi.evaluate("$('interpCard').scrollIntoView()"); await pi.screenshot(path='tests/out/interp_rest_en_panel.png')
        # edge cases: drift below the band, top edge, no edge
        r = await pi.evaluate("(() => { const r = __tremor.analyze(syn(2.4, 60, 20, 6, 0.05, 0)); return { e: r.edge, o: r.edgeOut, s: r.strength, f: r.f0, d: r.drift }; })()")
        check('v2 band: a real 2.4 Hz rhythm (the old "edge" case) is now measured: 2.4 Hz, clear, no edge', r['e'] == '' and not r['o'] and r['s'] == 'clear' and abs(r['f'] - 2.4) < 0.15 and r['d'] == '', r)
        await pi.evaluate("""(() => { const r = __tremor.analyze(drift(60, 20, 3, 1.2, 2)); Object.assign(r, { plannedS: 20, ts: Date.now(), notes: {}, sensor:'motion', limb:'hand', posture:'rest' }); renderResult(r); })()""")
        w = await pi.evaluate("$('resWarn').textContent")
        check('drift only: no rhythm reported, warning explains slow drifting, no ranking', 'slow drifting' in w and await pi.evaluate("__tremor.last.drift === 'only' && __tremor.last.strength === 'none' && $('matchList').children.length === 0"), w[:120])
        await pi.screenshot(path='tests/out/v2_drift_warning.png', full_page=True)
        await pi.evaluate(RENDER, [[7.4, 16, 20, 1, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'hold'}])
        w = await pi.evaluate("$('resWarn').textContent")
        check('edge: peak at the top (16/s) -> "faster than 7.5 Hz is not measured"', 'top of the measured range (7.5 Hz)' in w and 'Faster than 7.5 Hz is not measured' in w, w[-120:])
        await pi.evaluate(RENDER, [[6, 60, 20, 1, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest'}])
        check('edge: 6 Hz mid-band -> no edge warning', 'measured range' not in await pi.evaluate("$('resWarn').textContent"))
        # 10 Hz held out, small -> physiological / essential first
        await pi.evaluate(RENDER, [[10, 60, 20, 0.05, 0.01, 0], {'sensor':'motion','limb':'hand','posture':'hold','notes':{'sides':'both'}}])
        await pi.wait_for_timeout(150); i = await pi.evaluate(INFO)
        check('interp: 10 Hz posture small -> physiological / essential first', i['rank'][0] in ('phys', 'et') and i['ids'][0] in ('phys', 'et') and i['rank'].index('pd') > 2 and i['rank'].index('ortho') > 2, i['rank'])
        await pi.screenshot(path='tests/out/interp_posture_en.png', full_page=True)
        # 15 Hz legs standing -> orthostatic
        await pi.evaluate(RENDER, [[15, 100, 20, 0.2, 0.05, 2], {'sensor':'motion','limb':'leg','posture':'stand','notes':{'sides':'both'}}])
        await pi.wait_for_timeout(150); i = await pi.evaluate(INFO)
        check('interp: 15 Hz leg standing -> orthostatic first', i['ids'][0] == 'ortho' and i['rank'][0] == 'ortho', i['rank'])
        check('normal values: leg -> size not compared (explained)', 'Not compared' in await pi.evaluate("$('normSize').textContent"))
        await pi.screenshot(path='tests/out/interp_ortho_en.png', full_page=True)
        # compare left/right -> sides inferred
        await pi.evaluate(CMP)
        check('interp: compare result with rhythm on both sides -> "both"', await pi.evaluate("__tremor.sidesOf(__tremor.last) === 'both' && $('matchList').textContent.includes('both sides')"))
        # no clear rhythm -> no ranking, plain explanation
        await pi.evaluate(RENDER, [[5, 60, 20, 0, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest'}])
        check('interp: no clear rhythm -> no match list, explanation shown', await pi.evaluate("$('matchList').children.length === 0 && !$('interpNone').hidden && $('normRate').textContent.includes('No clear rhythm')"))
        # error result -> panels hidden
        await pi.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 1, 1, 0.05, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', plannedS:20}); renderResult(r); })()")
        check('interp: error result -> interpretation and typical values hidden', await pi.evaluate("$('interpCard').hidden && $('normCard').hidden"))
        # typical values by age: saved, and the comparison changes with age
        await pi.evaluate(RENDER, [[7.5, 60, 20, 0.175, 0.01, 0], {'sensor':'motion','limb':'hand','posture':'hold'}])
        n0 = await pi.evaluate("$('normCard').textContent")
        check('normal values: no age -> adult values + hint to add age', 'Add an age' in n0 and 'mm' in n0, n0[:120])
        await pi.fill('#ageInput', '30'); await pi.wait_for_timeout(100)
        a30 = await pi.evaluate("({ size: $('normSize').textContent, lvl: $('normSize').dataset.level, rate: $('normRate').textContent, grp: $('normFor').textContent })")
        await pi.fill('#ageInput', '80'); await pi.wait_for_timeout(100)
        a80 = await pi.evaluate("({ size: $('normSize').textContent, lvl: $('normSize').dataset.level, rate: $('normRate').textContent, grp: $('normFor').textContent })")
        check('age saved locally', await pi.evaluate("JSON.parse(localStorage.getItem('tremor.notes.v1')).age === '80'"))
        check('age 30 vs 80: size verdict changes (above typical -> typical for age)', a30['lvl'] == '1' and 'above typical for age under 40' in a30['size'] and a80['lvl'] == '0' and 'typical for age 75 and over' in a80['size'], [a30, a80])
        check('age 30 vs 80: rate verdict changes (7.5 Hz slower than normal -> within normal)', 'slower than normal' in a30['rate'] and 'within the range of normal' in a80['rate'], [a30['rate'], a80['rate']])
        check('normal values: approximate, explained in small print', await pi.evaluate("$('normCard').textContent.includes('approximate') && $('normCard').textContent.includes('how the phone is held')"))
        await pi.evaluate("$('normCard').querySelector('details').open = true; $('normCard').scrollIntoView()"); await pi.wait_for_timeout(100)
        await pi.screenshot(path='tests/out/interp_age.png')
        check('normal values: camera -> size not compared', await pi.evaluate("(() => { const r = __tremor.analyze(syn(5, 30, 20, 1, 0.05, 0)); Object.assign(r, {sensor:'camera', limb:'hand', posture:'rest', plannedS:20, handPct:1}); renderResult(r); return $('normSize').textContent.includes('camera'); })()"))
        await pi.reload(); await pi.wait_for_timeout(300)
        await pi.evaluate(RENDER, [[7.5, 60, 20, 0.175, 0.01, 0], {'sensor':'motion','limb':'hand','posture':'hold'}])
        check('age survives a reload', await pi.evaluate("$('ageInput').value === '80' && $('normFor').textContent.includes('75')"))
        # ---- illustrative example spectra: thumbnails + overlay on the user's chart ----
        await pi.evaluate(RENDER, [[4.8, 60, 20, 1.5, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest','notes':{'sides':'one'}}])
        await pi.wait_for_timeout(250)
        th = await pi.evaluate("""(() => [...document.querySelectorAll('#exGrid .ex')].map(b => { const cv = b.querySelector('canvas'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
            let lit = 0; for (let i = 0; i < d.length; i += 4) if (d[i] + d[i+1] + d[i+2] > 330) lit++; return { id: b.dataset.id, w: cv.width, lit, label: b.textContent, aria: b.getAttribute('aria-label') }; }))()""")
        check('examples: 9 thumbnails drawn (curve pixels present), labelled', len(th) == 9 and all(x['w'] > 50 and x['lit'] > 30 for x in th) and all(x['label'] for x in th) and all('not real patient data' in x['aria'] for x in th), [(x['id'], x['lit']) for x in th])
        pk = await pi.evaluate("Object.fromEntries(['phys','et','pd','holmes','drug','ortho'].map(id => { const e = __tremor.exampleSpectrum(id); let k = 10; e.psd.forEach((v, i) => { if (e.freqs[i] >= 1 && v > e.psd[k]) k = i; }); return [id, e.freqs[k]]; }))")
        check('examples: peaks where described (pd ~4.8, ET ~7, phys/drug ~10, Holmes ~3, ortho ~15.5)', abs(pk['pd']-4.8) < 0.3 and abs(pk['et']-7) < 0.3 and abs(pk['phys']-10) < 1.2 and abs(pk['drug']-10) < 0.4 and abs(pk['holmes']-3) < 0.3 and abs(pk['ortho']-15.5) < 0.3, pk)
        same = await pi.evaluate("JSON.stringify(__tremor.exampleSpectrum('dyst').psd.slice(0, 50)) === JSON.stringify(__tremor.exampleSpectrum('dyst').psd.slice(0, 50))")
        check('examples: fixed seed (deterministic)', same)
        ct = await pi.evaluate("$('interpCard').textContent")
        check('examples: "illustrative examples, not real patient data" label', 'Illustrative examples, not real patient data' in ct, '')
        SEEN_EN = {'phys': 'overactive thyroid', 'et': 'runs in families', 'pd': "Parkinson's disease", 'holmes': 'brainstem', 'cereb': 'multiple sclerosis', 'dyst': "writer's cramp", 'drug': 'lithium', 'ortho': 'primary orthostatic tremor', 'func': 'functional neurological disorder'}
        SEEN_HE = {'phys': 'בלוטת התריס', 'et': 'עובר במשפחה', 'pd': 'מחלת פרקינסון', 'holmes': 'גזע המוח', 'cereb': 'טרשת נפוצה', 'dyst': 'עווית כותבים', 'drug': 'ליתיום', 'ortho': 'רעד אורתוסטטי ראשוני', 'func': 'הפרעה נוירולוגית תפקודית'}
        SEENQ = """(() => ({ ex: Object.fromEntries([...document.querySelectorAll('#exGrid .ex')].map(b => [b.dataset.id, b.querySelector('.ex-seen').textContent])),
            m: Object.fromEntries([...document.querySelectorAll('#matchList li')].map(li => [li.dataset.id, (li.querySelector('.m-seen') || {}).textContent || ''])) }))()"""
        sq = await pi.evaluate(SEENQ)
        check('often seen with (EN): every example card names its associated conditions', all(sq['ex'].get(k, '').startswith('Often seen with:') and v in sq['ex'][k] for k, v in SEEN_EN.items()), sq['ex'])
        check('often seen with (EN): every listed match has the line', len(sq['m']) >= 1 and all(v.startswith('Often seen with:') and SEEN_EN[k] in v for k, v in sq['m'].items()), sq['m'])
        check('often seen with: the not-a-diagnosis note sits right under the matches', await pi.evaluate("$('safety').previousElementSibling.id === 'interpTip' && $('matchList').compareDocumentPosition($('safety')) & 4"))
        await pi.evaluate("$('exGrid').scrollIntoView({block:'center'})"); await pi.wait_for_timeout(100)
        await pi.screenshot(path='tests/out/interp_examples_en.png')
        await pi.tap('#exGrid .ex[data-id=pd]'); await pi.wait_for_timeout(500)
        ov = await pi.evaluate("({ o: __tremor.overlay, d: __tremor.ovDrawn, note: $('ovNote').hidden ? '' : $('ovText').textContent, pressed: document.querySelector('#exGrid .ex[data-id=pd]').getAttribute('aria-pressed') })")
        check('examples: tap -> overlaid on the chart (dashed) with a note', ov['o'] == 'pd' and ov['d'] == 'pd' and 'Parkinsonian rest tremor' in ov['note'] and 'not real patient data' in ov['note'] and ov['pressed'] == 'true', ov)
        await pi.evaluate("window.scrollTo(0, 0)"); await pi.wait_for_timeout(100)
        await pi.screenshot(path='tests/out/interp_examples_overlay.png')
        await pi.tap('#exGrid .ex[data-id=ortho]'); await pi.wait_for_timeout(200)
        check('examples: another tap switches the overlay', await pi.evaluate("__tremor.overlay === 'ortho' && __tremor.ovDrawn === 'ortho'"))
        await pi.tap('#exGrid .ex[data-id=ortho]'); await pi.wait_for_timeout(200)
        check('examples: tap again -> overlay off', await pi.evaluate("__tremor.overlay === null && __tremor.ovDrawn === null && $('ovNote').hidden"))
        await pi.tap('#exGrid .ex[data-id=et]'); await pi.wait_for_timeout(200); await pi.tap('#ovOff'); await pi.wait_for_timeout(200)
        check('examples: "Remove example" button clears the overlay', await pi.evaluate("__tremor.overlay === null && $('ovNote').hidden"))
        await pi.tap('#exGrid .ex[data-id=et]'); await pi.wait_for_timeout(200)
        await pi.evaluate(RENDER, [[6, 60, 20, 1, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest'}])
        check('examples: a new result starts without an overlay', await pi.evaluate("__tremor.overlay === null"))
        check('examples: no horizontal scroll (360)', await pi.evaluate("document.documentElement.scrollWidth <= 360"))
        # Wilson's disease hint: only for under-40s with an irregular / mixed pattern
        await pi.evaluate(RENDER, [[5, 60, 20, 1, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'hold'}])
        w80 = await pi.evaluate("$('wilson').hidden")
        await pi.fill('#ageInput', '25'); await pi.wait_for_timeout(100)
        w25 = await pi.evaluate("({ h: $('wilson').hidden, t: $('wilson').textContent, top: [...document.querySelectorAll('#matchList li')].map(l => l.dataset.id) })")
        check("wilson: age 25 + irregular-type match -> Wilson's disease check mentioned; not at 80", w80 and not w25['h'] and "Wilson's disease" in w25['t'], w25)
        await pi.screenshot(path='tests/out/interp_wilson.png', full_page=True)
        await pi.fill('#ageInput', '80'); await pi.wait_for_timeout(100)
        # Hebrew RTL
        await pi.evaluate("__tremor.setLang('he')")
        await pi.evaluate(RENDER, [[3, 60, 20, 1.5, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest','side':'left','notes':{'sides':'one'}}])
        await pi.wait_for_timeout(150); i = await pi.evaluate(INFO)
        he = await pi.evaluate("({ dir: document.documentElement.dir, title: $('interpCard').querySelector('h2').textContent, norm: $('normCard').textContent, warn: $('resWarn').textContent, scaleDir: getComputedStyle($('fscale')).direction })")
        check('he: panel translated, RTL page, scale stays left-to-right', he['dir'] == 'rtl' and 'סוגי רעד' in he['title'] and he['scaleDir'] == 'ltr' and 'מנוחה פרקינסוני' in i['why'], he)
        check('he: safety note (neurologist, 3–4 times)', 'נוירולוג' in i['safety'] and '3–4' in i['safety'] and 'זה לא אבחון' in i['safety'])
        check('he: age comparison translated', 'לגיל 75 ומעלה' in he['norm'], he['norm'][:80])
        await pi.evaluate("""(() => { const r = __tremor.analyze(drift(60, 20, 3, 1.2, 2)); Object.assign(r, { plannedS: 20, ts: Date.now(), notes: {}, sensor:'motion', limb:'hand', posture:'rest' }); renderResult(r); })()""")
        check('he: drift warning translated', 'סחיפה איטית' in await pi.evaluate("$('resWarn').textContent"))
        await pi.evaluate(RENDER, [[3, 60, 20, 1.5, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest','side':'left','notes':{'sides':'one'}}])
        check('he: no horizontal scroll on result (360)', i['sw'] <= 360, i['sw'])
        await pi.screenshot(path='tests/out/interp_he.png', full_page=True)
        await pi.evaluate("$('interpCard').scrollIntoView()"); await pi.screenshot(path='tests/out/interp_he_panel.png')
        await pi.tap('#exGrid .ex[data-id=pd]'); await pi.wait_for_timeout(300)
        exhe = await pi.evaluate("({ title: $('interpCard').textContent, note: $('ovText').textContent, lbl: [...document.querySelectorAll('#exGrid .ex-n')].map(s => s.textContent).join('|') })")
        check('he: example labels + "not real patient data" translated', 'לא נתונים של מטופלים אמיתיים' in exhe['title'] and 'פרקינסוני' in exhe['note'] and 'אורתוסטטי' in exhe['lbl'], exhe['lbl'])
        sq = await pi.evaluate(SEENQ)
        check('often seen with (HE): every example card and match translated', all(sq['ex'].get(k, '').startswith('מופיע לעיתים קרובות עם') and v in sq['ex'][k] for k, v in SEEN_HE.items()) and all(SEEN_HE[k] in v for k, v in sq['m'].items()), sq['m'])
        await pi.evaluate("$('exGrid').scrollIntoView({block:'center'})"); await pi.wait_for_timeout(100)
        await pi.screenshot(path='tests/out/interp_examples_he.png')
        await pi.evaluate("window.scrollTo(0, 0)"); await pi.wait_for_timeout(100); await pi.screenshot(path='tests/out/interp_examples_he_overlay.png')
        await pi.evaluate("show('setup')"); await pi.screenshot(path='tests/out/interp_he_setup.png', full_page=True)
        check('he: no horizontal scroll on setup (360)', await pi.evaluate("document.documentElement.scrollWidth <= 360"))
        check('interp: no page errors', not errs3, errs3)

        # ======================= v2: journal, trends, routine, reminders, report, accuracy, quality, spiral =======================
        ctx4 = await b.new_context(viewport={'width':360,'height':740}, device_scale_factor=2, is_mobile=True, has_touch=True, accept_downloads=True)
        pv = await ctx4.new_page(); await routes(pv); errs4 = []; pv.on('pageerror', lambda e: errs4.append(str(e)))
        await pv.add_init_script(SYN); await pv.add_init_script(V2)
        await pv.add_init_script("if (!sessionStorage.getItem('v2')) { sessionStorage.setItem('v2', '1'); localStorage.clear(); localStorage.setItem('lang', 'en'); }")
        await pv.goto('http://localhost:8781/index.html'); await pv.wait_for_timeout(300)
        q = pv.evaluate
        sw = lambda: q("document.documentElement.scrollWidth")
        await pv.screenshot(path='tests/out/v2_setup_en.png', full_page=True)
        check('v2 setup (360): tabs, today card, Full check + Spiral buttons, 20/30/60 s, "Moving"; no horizontal scroll', await q("['Measure','Journal','Trends'].every((x, i) => document.querySelectorAll('#tabs button')[i].textContent.includes(x)) && !$('todayCard').hidden && $('routineBtn').textContent.includes('Full check') && document.querySelectorAll('[data-key=len] button').length === 3 && !!document.querySelector('[data-key=posture] [data-v=action]')") and await sw() <= 360, await sw())

        # ---- accuracy: Welch + interpolation, longer recordings, sub-3 Hz, drift, gravity removal ----
        acc = await q("""(() => [2.0, 4.5, 9.0].map((f) => { const r = __tremor.analyze(syn(f, 60, 20, 1, 0.05, 0, 0.3)); return [f, r.f0, r.strength, r.pp]; }))()""")
        check('v2 Welch: 2.0 / 4.5 / 9.0 Hz sines (jittery timing) within ±0.15 Hz, clear, size ~2 mm', all(abs(a[1]-a[0]) <= 0.15 and a[2]=='clear' and 1.6 < a[3] < 2.4 for a in acc), acc)
        print('     accuracy, Hz error @60/s:', [round(a[1]-a[0], 4) for a in acc], ' size mm (true 2.0):', [round(a[3], 2) for a in acc])
        acc2 = await q("""(() => [2.0, 4.5, 9.0].map((f) => { const r = __tremor.analyze(syn(f, 25, 20, 1, 0.03, 0, 0.2)); return [f, r.f0]; }))()""")
        check('v2 Welch: same at a camera-like 25/s within ±0.15 Hz', all(abs(a[1]-a[0]) <= 0.15 for a in acc2), acc2)
        print('     accuracy, Hz error @25/s:', [round(a[1]-a[0], 4) for a in acc2])
        ln = await q("""(() => [20, 30, 60].map((s) => { const r = __tremor.analyze(syn(4.5, 60, s, 1, 0.05, 0, 0.3)); return [s, r.df, r.segS, r.f0]; }))()""")
        check('v2 longer recordings: 30 / 60 s use longer segments (finer resolution), still accurate', ln[0][2] < ln[1][2] < ln[2][2] and ln[2][1] < ln[0][1] and all(abs(x[3]-4.5) < 0.05 for x in ln), ln)
        sub = await q("""(() => [1.6, 2.0, 2.5].map((f) => { const r = __tremor.analyze(syn(f, 60, 20, 2, 0.05, 0, 0.3)); return [f, r.f0, r.strength, r.edge, r.drift, r.band[0]]; }))()""")
        check('v2 sub-3 Hz: 1.6 / 2.0 / 2.5 Hz found (band now starts at 1.5 Hz), clear, no edge / drift flag', all(abs(a[1]-a[0]) <= 0.15 and a[2]=='clear' and a[3]=='' and a[4]=='' and a[5]==1.5 for a in sub), sub)
        dr = await q("""(() => [1, 2, 3, 4, 5].map((s) => { const r = __tremor.analyze(drift(60, 20, 3, 1.4, s)); return [r.strength, r.drift]; }))()""")
        check('v2 drift rejection: heavy slow drift (up to 1.4 Hz) is never reported as a rhythm', all(a[0]=='none' for a in dr) and sum(1 for a in dr if a[1]=='only') >= 3, dr)
        dt = await q("""(() => [1, 2, 3].map((s) => { const r = __tremor.analyze(drift(60, 20, 3, 1.4, s, 4, 1)); return [r.f0, r.strength]; }))()""")
        check('v2 drift rejection: a 4 Hz tremor under heavy drift is still found', all(abs(a[0]-4) < 0.15 and a[1]=='clear' for a in dt), dt)
        dt2 = await q("""(() => [1, 2, 3].map((s) => { const r = __tremor.analyze(drift(60, 20, 3, 1.4, s, 2, 2)); return [r.f0, r.strength]; }))()""")
        check('v2 drift rejection: a 2 Hz tremor under heavy drift is still found (±0.15 Hz)', all(abs(a[0]-2) <= 0.15 and a[1]=='clear' for a in dt2), dt2)
        nz = await q("""(() => Array.from({ length: 6 }, () => { const r = __tremor.analyze(syn(5, 60, 20, 0, 0.05, 0)); return [r.strength, r.drift]; }))()""")
        check('v2: pure sensor noise -> no rhythm and no drift label', all(a[0]=='none' and a[1]=='' for a in nz), nz)
        hp = await q("""(() => { const fs = 60, x = Float64Array.from({ length: 1200 }, (_, i) => 9.81 + 0.5 * Math.sin(2 * Math.PI * 6 * i / fs)); const y = __tremor.highpass(x, fs, 0.8);
            let m = 0, a = 0; for (let i = 100; i < 1100; i++) { m += y[i]; a = Math.max(a, Math.abs(y[i])); } return [m / 1000, a]; })()""")
        check('v2 gravity removal: the zero-phase high-pass removes a 9.81 offset and keeps a 6 Hz sine', abs(hp[0]) < 0.01 and 0.47 < hp[1] < 0.53, hp)

        # ---- quality score ----
        qc = await q("(() => __tremor.scoreQuality(__tremor.analyze(syn(5, 60, 20, 1, 0.05, 0, 0.1))))()")
        qn = await q("(() => __tremor.scoreQuality(__tremor.analyze(noisy())))()")
        check('v2 quality: clean synthetic signal >= 85, "good"', qc['s'] >= 85 and qc['lv'] == 'good', qc)
        check('v2 quality: noisy synthetic signal (dropouts, jitter, bumps) < 50, "low", with reasons', qn['s'] < 50 and qn['lv'] == 'low' and 'drop' in qn['r'] and 'art' in qn['r'], qn)
        print('     quality clean / noisy:', qc['s'], qn['s'])
        await q("""(() => { const r = __tremor.analyze(noisy()); Object.assign(r, { kind: 'tremor', sensor: 'motion', limb: 'hand', posture: 'rest', plannedS: 20, ts: Date.now(), notes: {}, tags: [] }); r.q = __tremor.scoreQuality(r); renderResult(r); })()""")
        qt = await q("$('resQuality').textContent")
        check('v2 quality on the result: score, "low", advice to repeat, reasons', 'Measurement quality' in qt and 'low' in qt and 'repeat this measurement' in qt and 'Why:' in qt and await q("$('resQuality').dataset.level === 'low'"), qt[:160])
        await pv.screenshot(path='tests/out/v2_result_low_quality.png', full_page=True)

        # ---- journal: validation, corrupt data, cap ----
        bad = await q("""(() => { const good = mkE({ id: 'good1', note: '<img src=x onerror=alert(1)>', tags: ['coffee', 'bogus', 'coffee'] });
          const arr = [good, mkE({ ts: 'x' }), mkE({ f: NaN }), mkE({ f: 999 }), mkE({ strength: 'huge' }), mkE({ sensor: 'touch' }), null, 42, 'str', mkE({ id: 'dup' }), mkE({ id: 'dup' }),
            mkE({ id: 'sp1', kind: 'spiral', spiral: { score: 3, turns: 2.5, img: 'javascript:alert(1)' } }), mkE({ id: 'q1', q: { s: 500, lv: 'meh' } }), mkE({ id: 'sp2', spec: { d: 0.2, top: 1, p: [1, 2, 'x', 4] } })];
          localStorage.setItem('tremor.journal.v2', JSON.stringify(arr)); const j = __tremor.journal.reload();
          const g = j.find((e) => e.id === 'good1'), s = j.find((e) => e.id === 'sp1'), qq = j.find((e) => e.id === 'q1'), s2 = j.find((e) => e.id === 'sp2');
          return { n: j.length, tags: g.tags, note: g.note, spSensor: s.sensor, spImg: 'img' in s.spiral, q: 'q' in qq, spec: 'spec' in s2 }; })()""")
        check('v2 journal validation: bad entries dropped, duplicate ids removed, tags filtered, unsafe image / bad quality / bad spectrum discarded', bad['n'] == 5 and bad['tags'] == ['coffee'] and bad['spSensor'] == 'touch' and not bad['spImg'] and not bad['q'] and not bad['spec'], bad)
        await q("__tremor.goTab('journal')")
        check('v2 journal: notes are shown as text, never as HTML', await q("!document.querySelector('#jList img') && $('jList').textContent.includes('<img src=x')"))
        await q("localStorage.setItem('tremor.journal.v2', '{not json'); __tremor.journal.reload(); __tremor.goTab('journal')")
        check('v2 journal: corrupt storage -> empty journal + empty state, no crash', await q("__tremor.journal.load().length === 0 && !$('jEmpty').hidden"))
        cap = await q("""(() => { __tremor.CONFIG.JOURNAL_MAX = 30; const arr = Array.from({ length: 45 }, (_, i) => mkE({ ts: Date.now() - i * 36e5 }));
          __tremor.journal.store(arr); const n1 = __tremor.journal.reload().length, newest = __tremor.journal.load()[0].ts;
          __tremor.CONFIG.JOURNAL_MAX = 1000; __tremor.CONFIG.JOURNAL_BYTES = 20000;
          const r = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0));
          const withSpec = Array.from({ length: 40 }, (_, i) => { const e = __tremor.journal.entryOf(Object.assign({}, r, { kind: 'tremor', sensor: 'motion', limb: 'hand', posture: 'rest', ts: Date.now() - i * 36e5, notes: {}, tags: [] })); e.id = 'c' + i; return e; });
          __tremor.journal.store(withSpec); const j = __tremor.journal.reload(), bytes = localStorage.getItem('tremor.journal.v2').length;
          const out = { n1, newestKept: newest > Date.now() - 36e5, n2: j.length, bytes, newestSpec: !!j[0].spec, oldestSpec: !!j[j.length - 1].spec };
          __tremor.CONFIG.JOURNAL_BYTES = 1500000; return out; })()""")
        check('v2 journal cap: count (30 newest kept) and size (spectra dropped oldest-first, entries kept, under the byte cap)', cap['n1'] == 30 and cap['newestKept'] and cap['n2'] == 40 and cap['bytes'] <= 20000 and cap['newestSpec'] and not cap['oldestSpec'], cap)

        # ---- a real recording: live guidance, quality, tags + note, reopen from history, delete one ----
        await q("localStorage.removeItem('tremor.journal.v2'); __tremor.journal.reload(); __tremor.CONFIG.RECORD_OVERRIDE_S = 5; __tremor.CONFIG.COUNTDOWN_S.motion = 1; __tremor.goTab('setup')")
        await q(MOTION6)
        await pv.tap('#startBtn'); await pv.wait_for_selector('#record:not([hidden])'); await pv.wait_for_timeout(800)
        g = await q("({ k: __tremor.guide.key, shown: !$('guide').hidden, txt: $('guideTxt').textContent, tabs: $('tabs').hidden })")
        check('v2 guidance: live holding check while getting into position (steady 6 Hz tremor -> "steady position"); tabs hidden while recording', g['shown'] and g['k'] == 'gOk' and 'steady' in g['txt'] and g['tabs'], g)
        await pv.screenshot(path='tests/out/v2_record_guide.png')
        await pv.wait_for_function("!$('result').hidden", timeout=15000)
        r = await q("({ q: __tremor.last.q, id: __tremor.last.id, tagShown: !$('tagCard').hidden, chips: $('tagChips').children.length, qt: $('resQuality').textContent, saved: " + JN + ".length })")
        check('v2 result: quality score shown (good), saved to the journal, tag card with 7 tags', r['q'] and r['q']['s'] >= 75 and r['id'] and r['tagShown'] and r['chips'] == 7 and 'good' in r['qt'] and r['saved'] == 1, r)
        await pv.tap('#tagChips [data-tag=beforeMed]'); await pv.tap('#tagChips [data-tag=coffee]'); await pv.tap('#tagChips [data-tag=afterMed]')
        await pv.fill('#entryNote', 'shaky morning'); await pv.wait_for_timeout(450)
        e = await q(JN + "[0]")
        check('v2 tags + note saved on the entry; "before meds" / "after meds" are exclusive', sorted(e['tags']) == ['afterMed', 'coffee'] and e['note'] == 'shaky morning', [e['tags'], e['note']])
        await q("$('tagCard').scrollIntoView({ block: 'center' })"); await pv.screenshot(path='tests/out/v2_result_tags.png')
        await q("window.scrollTo(0, 0)"); await pv.screenshot(path='tests/out/v2_result_en.png', full_page=True)
        await q("clearInterval(window.__mi)")
        await q("__tremor.goTab('journal')"); await pv.wait_for_timeout(150)
        await pv.tap('#jList .jitem'); await pv.wait_for_timeout(300)
        ro = await q("({ res: !$('result').hidden, saved: $('resSaved').textContent, spec: !$('spectrum').hidden, interp: !$('interpCard').hidden, back: !$('resBack').hidden, again: $('againBtn').hidden, f: __tremor.last.f0, tags: [...document.querySelectorAll('#tagChips [aria-pressed=true]')].map(b => b.dataset.tag) })")
        check('v2 history: tap -> reopens the full result (saved line, spectrum, interpretation, tags); Back instead of Measure again', ro['res'] and 'Saved in your journal' in ro['saved'] and ro['spec'] and ro['interp'] and ro['back'] and ro['again'] and abs(ro['f'] - 6) < 0.3 and sorted(ro['tags']) == ['afterMed', 'coffee'], ro)
        px = await q("(() => { const cv = $('spectrum'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i] < 120 && d[i+1] > 150 && d[i+2] > 190) n++; return n; })()")
        check('v2 history: the reopened spectrum is drawn from the saved (downsampled) spectrum', px > 100, px)
        await pv.screenshot(path='tests/out/v2_reopen_en.png', full_page=True)
        await pv.tap('#resBack'); await pv.wait_for_timeout(100)
        check('v2 history: Back -> journal', await q("!$('journal').hidden"))
        await pv.tap('#jList .jitem'); await pv.wait_for_timeout(200); await pv.tap('#resDelete'); await pv.wait_for_timeout(150)
        await pv.tap('#confirmNo'); await pv.wait_for_timeout(100)
        check('v2 delete one: Cancel keeps it', await q(JN + ".length === 1"))
        await pv.tap('#resDelete'); await pv.wait_for_timeout(100); await pv.tap('#confirmYes'); await pv.wait_for_timeout(200)
        check('v2 delete one: confirmed -> removed, back in the journal', await q(JN + ".length === 0 && !$('journal').hidden"))

        # ---- history grouped by day, streak + heatmap (fixed clock) ----
        NOW = "Date.parse('2026-10-10T18:00:00')"
        await q("__tremor.setNow(" + NOW + ")")
        grp = await q("""(() => { const N = """ + NOW + """, H = 36e5, D = 864e5; seedJ([mkE({ ts: N - 2 * H }), mkE({ ts: N - 3 * H, side: 'left' }), mkE({ ts: N - D }), mkE({ ts: N - 3 * D, tags: ['tired'] }), mkE({ ts: N - 3 * D - H, kind: 'spiral', spiral: { score: 2.4, turns: 3 } })]);
          __tremor.goTab('journal'); return [...document.querySelectorAll('#jList .jday')].map((d) => d.textContent); })()""")
        check('v2 history: grouped by day (Today, Yesterday, then the date)', len(grp) == 3 and grp[0] == 'Today' and grp[1] == 'Yesterday' and 'October' in grp[2], grp)
        check('v2 history: spiral row + tag chips', await q("$('jList').textContent.includes('Spiral · score 2.4/10') && $('jList').textContent.includes('tired')"))
        st = await q("""(() => { const N = """ + NOW + """, D = 864e5; seedJ([0, 1, 2, 4, 9].map((d) => mkE({ ts: N - d * D - 36e5 })).concat([mkE({ ts: N - 36e5 * 2 }), mkE({ ts: N - 36e5 * 3 }), mkE({ ts: N - 36e5 * 4 })]));
          const s = __tremor.streakInfo(__tremor.journal.load(), N), cells = __tremor.heatCells(__tremor.journal.load(), N); __tremor.goTab('journal');
          const dom = [...document.querySelectorAll('#heat i')], today = dom.find((i) => i.classList.contains('today'));
          return { s, cells: cells.length, future: cells.filter((c) => c.future).length, expFuture: 6 - new Date(N).getDay(), todayN: today && +today.dataset.n, todayCls: today && today.className,
            txt: $('jStreakTxt').textContent, num: $('jStreakNum').textContent, sub: $('jStreakSub').textContent, lit: dom.filter((i) => /l[123]/.test(i.className)).length }; })()""")
        check('v2 streak: 3 days in a row (today, yesterday, the day before), 5 of the last 14 days', st['s']['streak'] == 3 and st['s']['today'] and st['s']['last14'] == 5 and st['txt'] == '3 days in a row' and st['num'] == '3' and 'Measured on 5 of the last 14 days' in st['sub'], st)
        check('v2 heatmap: 12 weeks, 5 measured days lit, today outlined with 4 measurements (darkest), future days hidden', st['cells'] == 84 and st['lit'] == 5 and st['todayN'] == 4 and 'l3' in st['todayCls'] and 'today' in st['todayCls'] and st['future'] == st['expFuture'], st)
        await pv.screenshot(path='tests/out/v2_journal_en.png', full_page=True)
        z = await q("""(() => { const N = """ + NOW + """; seedJ([mkE({ ts: N - 5 * 864e5 })]); __tremor.goTab('setup'); return { numHidden: $('streakNum').hidden, txt: $('streakTxt').textContent, due: $('todayDue').hidden }; })()""")
        check('v2 streak: none running -> gentle wording, no number, no guilt words', z['numHidden'] and 'Start when it suits you' in z['txt'] and not any(w in z['txt'].lower() for w in ['missed', 'lost', 'broke', 'failed']), z)

        # ---- reminders (Notification stubbed) ----
        nr = await q("""(() => { const at = (h, m) => { const d = new Date(""" + NOW + """); d.setHours(h, m, 0, 0); return d.getTime(); };
          const f = (now) => { const x = __tremor.nextReminder(now, ['09:00', '19:30']); return x && new Date(x).toString().slice(0, 21); };
          return [f(at(8, 0)), f(at(10, 0)), f(at(20, 0)), __tremor.nextReminder(at(10, 0), ['25:00', 'x'])]; })()""")
        check('v2 reminders: next = today 09:00 / today 19:30 / tomorrow 09:00; invalid times ignored', nr[0].endswith('09:00') and nr[1].endswith('19:30') and nr[2].endswith('09:00') and nr[0][:10] == nr[1][:10] and nr[2][:10] != nr[1][:10] and nr[3] is None, nr)
        await q("seedJ([]); __tremor.goTab('journal')")
        await pv.tap('#remToggle'); await pv.wait_for_timeout(250)
        rm = await q("({ on: __tremor.settings.rem.on, times: __tremor.settings.rem.times, note: $('remNote').textContent, next: __tremor.remNextAt, inputs: document.querySelectorAll('#remTimes input[type=time]').length })")
        check('v2 reminders: toggle on (permission granted) -> saved, next reminder scheduled and shown', rm['on'] and rm['times'] == ['09:00'] and rm['inputs'] == 1 and 'Next reminder' in rm['note'] and bool(rm['next']), rm)
        await pv.fill('#remTimes input[type=time]', '07:15'); await pv.dispatch_event('#remTimes input[type=time]', 'change')
        await pv.tap('#remAdd'); await pv.wait_for_timeout(150)
        check('v2 reminders: change a time + add a second one (saved)', await q("JSON.stringify(JSON.parse(localStorage.getItem('tremor.settings.v1')).rem.times) === JSON.stringify(['07:15', '19:00'])"))
        await q("$('remCard').scrollIntoView({ block: 'center' })"); await pv.screenshot(path='tests/out/v2_reminders.png')
        fired = await q("(async () => { window.__notes = []; const shown = await __tremor.fireReminder(); return { shown, notes: window.__notes }; })()")
        check('v2 reminders: fires a notification when nothing is measured today', fired['shown'] and len(fired['notes']) == 1 and "today's check" in fired['notes'][0]['title'], fired)
        due = await q("(() => { __tremor.goTab('setup'); return { due: !$('todayDue').hidden, txt: $('todayDue').textContent }; })()")
        check('v2 reminders: in-app "today\'s check" prompt once the reminder time has passed', due['due'] and "Time for today's check" in due['txt'], due)
        await pv.screenshot(path='tests/out/v2_today_due.png')
        fired2 = await q("(async () => { seedJ([mkE({ ts: " + NOW + " - 36e5 })]); window.__notes = []; const shown = await __tremor.fireReminder(); __tremor.goTab('setup'); return { shown, n: window.__notes.length, txt: $('todayDue').textContent }; })()")
        check('v2 reminders: no notification once today is measured; the prompt says done', not fired2['shown'] and fired2['n'] == 0 and 'done' in fired2['txt'], fired2)
        den = await q("(() => { Notification.permission = 'denied'; __tremor.goTab('journal'); return $('remNote').textContent; })()")
        check('v2 reminders: notifications blocked -> graceful in-app explanation', 'blocked' in den and 'Measure tab' in den, den)
        noapi = await q("(() => { const N = window.Notification; window.Notification = undefined; __tremor.goTab('journal'); const t = $('remNote').textContent; window.Notification = N; Notification.permission = 'granted'; return t; })()")
        check('v2 reminders: no Notification API -> graceful in-app explanation', "can't show notifications" in noapi, noapi)

        # ---- trends: filters, rolling median, left vs right, before / after medication (synthetic) ----
        TRS = """(() => { const N = """ + NOW + """, D = 864e5, H = 36e5, out = [];
          for (let d = 0; d < 40; d++) { out.push(mkE({ ts: N - d * D - 10 * H, side: 'left', f: 5 + 0.01 * d, pp: 1.0, posture: 'rest' })); out.push(mkE({ ts: N - d * D - 9 * H, side: 'right', f: 5.2, pp: 2.0, posture: 'rest' })); }
          for (let d = 0; d < 8; d++) out.push(mkE({ ts: N - d * D - 5 * H, side: 'left', f: 7, pp: 0.3, posture: 'hold', strength: 'weak' }));
          for (let i = 0; i < 6; i++) { const t0 = N - (i + 1) * D - 3 * H;
            out.push(mkE({ ts: t0, side: 'right', posture: 'hold', f: 5.0, pp: 2.0, tags: ['beforeMed'] })); out.push(mkE({ ts: t0 + 2 * H, side: 'right', posture: 'hold', f: 4.8, pp: 1.3, tags: ['afterMed'] })); }
          out.push(mkE({ ts: N - 20 * D, side: 'right', posture: 'hold', f: 5, pp: 1, tags: ['afterMed'] }));
          out.push(mkE({ ts: N - 30 * D, limb: 'leg', posture: 'stand', f: 15, pp: 0.2 }));
          return seedJ(out); })()"""
        n = await q(TRS)
        await q("__tremor.goTab('trends')")
        for f, v in [('range', '90'), ('limb', 'all'), ('cond', 'all'), ('side', 'both')]: await pv.tap('.chips[data-f=%s] [data-v="%s"]' % (f, v))
        await pv.wait_for_timeout(150); c_all = await q("__tremor.trend.pts.length")
        await pv.tap('.chips[data-f=cond] [data-v=rest]'); await pv.wait_for_timeout(100); c_rest = await q("__tremor.trend.pts.length")
        await pv.tap('.chips[data-f=side] [data-v=left]'); await pv.wait_for_timeout(100); c_left = await q("__tremor.trend.pts.length")
        await pv.tap('.chips[data-f=range] [data-v="30"]'); await pv.wait_for_timeout(100); c_30 = await q("__tremor.trend.pts.length")
        for f, v in [('limb', 'leg'), ('cond', 'all'), ('side', 'both'), ('range', 'all')]: await pv.tap('.chips[data-f=%s] [data-v="%s"]' % (f, v))
        await pv.wait_for_timeout(100); c_leg = await q("__tremor.trend.pts.length")
        check('v2 trends filters: all 102, at rest 80, rest + left 40, last 30 days 30, leg 1', [n, c_all, c_rest, c_left, c_30, c_leg] == [102, 102, 80, 40, 30, 1], [n, c_all, c_rest, c_left, c_30, c_leg])
        check('v2 trends: filters remembered', await q("JSON.parse(localStorage.getItem('tremor.settings.v1')).tf.limb === 'leg'"))
        for f, v in [('limb', 'hand'), ('cond', 'rest'), ('range', '90')]: await pv.tap('.chips[data-f=%s] [data-v="%s"]' % (f, v))
        await pv.wait_for_timeout(250)
        drawn = await q(PIX)
        check('v2 trends: rolling-median lines + dots drawn', drawn['sky'] > 80 and drawn['coral'] > 50 and not drawn['hidden'], drawn)
        lr = await q("({ t: $('lrTxt').textContent, cells: $('lrGrid').children.length })")
        check('v2 left vs right (synthetic): right side about 2.0x the left, medians of 40 + 40', 'right side: size about 2.0×' in lr['t'] and '40 left and 40 right' in lr['t'] and lr['cells'] == 12, lr)
        await pv.screenshot(path='tests/out/v2_trends_en.png', full_page=True)
        await pv.tap('.chips[data-f=cond] [data-v=hold]'); await pv.wait_for_timeout(150)
        md = await q("({ t: $('medTxt').textContent, s: $('medSub').textContent, pairs: __tremor.medPairs(__tremor.trendFilter(__tremor.journal.load())).length })")
        check('v2 before / after medication: 6 tag pairs -> "35% smaller in 6 paired measurements" + rates + caveat; an "after" without a "before" within 6 h is not paired', md['pairs'] == 6 and 'After medication your tremor size was on average 35% smaller in 6 paired measurements' in md['t'] and '5.0 Hz before, 4.8 Hz after' in md['s'] and 'not proof' in md['s'], md)
        await q("$('medCard').scrollIntoView({ block: 'center' })"); await pv.screenshot(path='tests/out/v2_trends_med_en.png')
        mm = await q("""(() => { const N = """ + NOW + """, H = 36e5, L = [];
          for (let i = 0; i < 3; i++) { L.push(mkE({ ts: N - i * 864e5 - 8 * H, med: 'no', pp: 1.0, f: 6 })); L.push(mkE({ ts: N - i * 864e5 - 7 * H, med: 'yes', pp: 1.5, f: 6 })); }
          L.push(mkE({ ts: N - 5 * 864e5, med: 'no', pp: 1 })); L.push(mkE({ ts: N - 5 * 864e5 + 7 * H, med: 'yes', pp: 0.2 }));
          return __tremor.medSummary(__tremor.medPairs(L)); })()""")
        check('v2 before / after: also pairs "Medication taken: no / yes" within the window; larger after -> "larger"', mm['n'] == 3 and mm['dir'] == 'larger' and mm['pct'] == 50, mm)

        # ---- backup: export / import JSON ----
        await q("__tremor.goTab('journal')")
        async with pv.expect_download() as dl:
            await pv.tap('#exportJson')
        d = await dl.value; bkpath = await d.path(); bk = json.load(open(bkpath))
        check('v2 backup: JSON export (app tag, version, all 102 entries)', bk['app'] == 'tremorti' and bk['v'] == 2 and len(bk['entries']) == 102 and d.suggested_filename.endswith('.json'), [bk.get('app'), len(bk.get('entries', []))])
        await q("seedJ([])")
        await pv.set_input_files('#importFile', str(bkpath)); await pv.wait_for_timeout(500)
        imp = await q("({ n: __tremor.journal.load().length, toast: $('toast').textContent })")
        check('v2 import: restores all 102 measurements', imp['n'] == 102 and 'Imported 102 measurements (0 already there)' in imp['toast'], imp)
        await pv.set_input_files('#importFile', str(bkpath)); await pv.wait_for_timeout(500)
        imp2 = await q("({ n: __tremor.journal.load().length, toast: $('toast').textContent })")
        check('v2 import again: duplicates skipped', imp2['n'] == 102 and '(102 already there)' in imp2['toast'], imp2)
        open('tests/out/v2_bad_backup.json', 'w').write('{"hello": 1}')
        await pv.set_input_files('#importFile', 'tests/out/v2_bad_backup.json'); await pv.wait_for_timeout(400)
        check('v2 import: not a backup -> clear message, nothing changed', "isn't a Tremorti backup" in await q("$('toast').textContent") and await q("__tremor.journal.load().length === 102"))
        os.remove('tests/out/v2_bad_backup.json')

        # ---- doctor report: HTML page (print -> PDF) + PNG image ----
        await q("""(() => { const N = """ + NOW + """; const r = __tremor.analyze(syn(4.8, 60, 20, 1.5, 0.05, 0)); Object.assign(r, { kind: 'tremor', sensor: 'motion', limb: 'hand', posture: 'rest', side: 'left', ts: N - 18e5, notes: { sides: 'one' }, tags: [] });
          r.q = __tremor.scoreQuality(r); __tremor.journal.save(r);
          const list = __tremor.journal.load(); list.push(__tremor.journal.validate(mkE({ id: 'spx', ts: N - 2 * 864e5, kind: 'spiral', f: 6.1, pp: 1.8, spiral: { score: 3.4, turns: 3 } }))); __tremor.journal.store(list);
          __tremor.notes.age = '72'; __tremor.goTab('trends'); })()""")
        await pv.tap('#reportBtn'); await pv.wait_for_timeout(200)
        await pv.fill('#rpName', 'Dana Levi'); await pv.tap('.chips[data-f=rpRange] [data-v="90"]'); await pv.wait_for_timeout(500)
        rp = await q("({ txt: $('reportPaper').textContent, imgs: $('reportPaper').querySelectorAll('img').length, rows: $('reportPaper').querySelectorAll('tbody tr').length, sw: document.documentElement.scrollWidth, tabs: $('tabs').hidden })")
        need = ['Dana Levi', 'Age: 72', 'Period:', '103 measurements, 1 spiral drawings', 'Median values by condition and side', 'Hand, at rest', 'Before / after medication', '35% smaller in 6 paired', 'Left vs right', 'Latest spectrum', 'resembles', 'Parkinsonian rest tremor', 'Spiral drawings', 'score 3.4/10', 'Not a diagnosis']
        check('v2 report: name, age, period, counts, medians by condition + side, trend + spectrum images, medication, L/R, pattern match, spiral, not-a-diagnosis', all(k in rp['txt'] for k in need) and rp['imgs'] == 2 and rp['rows'] == 5 and rp['sw'] <= 360, [k for k in need if k not in rp['txt']] or rp['rows'])
        await pv.screenshot(path='tests/out/v2_report_en.png', full_page=True)
        await pv.tap('#rpPrint'); await pv.wait_for_timeout(100)
        check('v2 report: "Print / save as PDF" opens the browser print', await q("window.__printed === 1"))
        await pv.emulate_media(media='print')
        vis = await q("({ tabs: getComputedStyle($('tabs')).display, form: getComputedStyle($('reportForm')).display, paper: getComputedStyle($('reportPaper')).display, top: getComputedStyle(document.querySelector('.topbar')).display })")
        try: await pv.pdf(path='tests/out/v2_report_en.pdf', format='A4')
        except Exception as ex: print('     (pdf not saved:', ex, ')')
        await pv.emulate_media(media='screen')
        check('v2 report print layout: only the report page is printed', vis['tabs'] == 'none' and vis['form'] == 'none' and vis['top'] == 'none' and vis['paper'] != 'none', vis)
        await q("window.__shared = null; navigator.canShare = (d) => !!(d && d.files); navigator.share = (d) => { window.__shared = d; return Promise.resolve(); };")
        how = await q("__tremor.shareReportImage()")
        sh = await q("""(async () => { const f = window.__shared && window.__shared.files && window.__shared.files[0], b = __tremor.reportBlob, bmp = await createImageBitmap(b);
            return { name: f && f.name, type: f && f.type, size: b.size, w: bmp.width, h: bmp.height }; })()""")
        check('v2 report PNG: shared as an image file through the share sheet (WhatsApp etc.)', how == 'shared' and sh['type'] == 'image/png' and sh['name'].endswith('.png') and sh['size'] > 30000 and sh['w'] == 1080 and sh['h'] > 1200, sh)
        B64 = "(async () => { const buf = new Uint8Array(await __tremor.reportBlob.arrayBuffer()); let s = ''; for (let i = 0; i < buf.length; i += 8192) s += String.fromCharCode(...buf.subarray(i, i + 8192)); return btoa(s); })()"
        open('tests/out/v2_report_image_en.png', 'wb').write(base64.b64decode(await q(B64)))
        await q("navigator.canShare = () => false")
        async with pv.expect_download() as dl:
            await pv.tap('#rpImage')
        d = await dl.value
        check('v2 report PNG: no file sharing -> the PNG is downloaded', d.suggested_filename.endswith('.png'), d.suggested_filename)
        await q("__tremor.setLang('he')"); await pv.wait_for_timeout(300)
        rh = await q("({ txt: $('reportPaper').textContent, dir: $('reportPaper').getAttribute('dir'), sw: document.documentElement.scrollWidth })")
        check('v2 report (HE): translated, right-to-left', all(k in rh['txt'] for k in ['מדידות רעד', 'Dana Levi', 'גיל: 72', 'קטן בממוצע ב־35%', 'זה לא אבחון', 'רעד מנוחה פרקינסוני']) and rh['dir'] == 'rtl' and rh['sw'] <= 360, rh['txt'][:200])
        await pv.screenshot(path='tests/out/v2_report_he.png', full_page=True)
        await q("__tremor.shareReportImage()"); open('tests/out/v2_report_image_he.png', 'wb').write(base64.b64decode(await q(B64)))
        await q("__tremor.setLang('en')"); await pv.tap('#rpBack'); await pv.wait_for_timeout(100)
        check('v2 report: Back returns to where it was opened (Trends)', await q("!$('trends').hidden"))

        # ---- holding guidance: table / big movements / tilting ----
        await q("seedJ([]); __tremor.CONFIG.COUNTDOWN_S.motion = 9; __tremor.goTab('setup')")
        await q("""window.__mi = setInterval(() => window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: { x: (Math.random() - .5) * 0.004, y: (Math.random() - .5) * 0.004, z: (Math.random() - .5) * 0.004 }, accelerationIncludingGravity: { x: 0, y: 0, z: 9.81 }, interval: 16 })), 16);""")
        await pv.tap('#startBtn'); await pv.wait_for_timeout(1600)
        g1 = await q("({ k: __tremor.guide.key, t: $('guideTxt').textContent, warn: $('guide').classList.contains('warn') })")
        await q("clearInterval(window.__mi)")
        await q("""window.__mi = setInterval(() => { const t = performance.now() / 1000, a = 2.5 * Math.sin(2 * Math.PI * 0.7 * t); window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: { x: a, y: 0, z: 0 }, accelerationIncludingGravity: { x: a, y: 0, z: 9.81 }, interval: 16 })); }, 16);""")
        await pv.wait_for_timeout(2300); g2 = await q("({ k: __tremor.guide.key, t: $('guideTxt').textContent })")
        await q("clearInterval(window.__mi)")
        await q("""window.__mi = setInterval(() => { const t = performance.now() / 1000, th = 0.5 * Math.sin(2 * Math.PI * 0.25 * t); window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: { x: 0.01, y: 0, z: 0 }, accelerationIncludingGravity: { x: 9.81 * Math.sin(th), y: 0, z: 9.81 * Math.cos(th) }, interval: 16 })); }, 16);""")
        await pv.wait_for_timeout(2300); g3 = await q("({ k: __tremor.guide.key, t: $('guideTxt').textContent })")
        await pv.screenshot(path='tests/out/v2_record_guide_warn.png')
        await pv.tap('#cancelBtn'); await q("clearInterval(window.__mi); __tremor.CONFIG.COUNTDOWN_S.motion = 1")
        check('v2 guidance: phone lying still on a table -> "lying still on a surface" warning', g1['k'] == 'gTable' and 'lying still' in g1['t'] and g1['warn'], g1)
        check('v2 guidance: big slow movements -> "settle into position"', g2['k'] == 'gMoving' and 'settle into position' in g2['t'], g2)
        check('v2 guidance: tilting phone (gravity vector turning) -> "keep the phone at the same angle"', g3['k'] == 'gTilt' and 'same angle' in g3['t'], g3)

        # ---- full check (~3 min, shortened here): step cards, countdowns, voice, combined summary ----
        await q("seedJ([]); __tremor.CONFIG.RECORD_OVERRIDE_S = 4; Object.assign(__tremor.CONFIG, { ROUTINE_PREP_S: 1, ROUTINE_SWITCH_S: 1, ROUTINE_FIRST_S: 1 }); window.__said = []; __tremor.goTab('setup')")
        await q(MOTION6)
        await pv.tap('#routineBtn')
        steps = []
        for i in range(6):
            await pv.wait_for_function("!$('stepCard').hidden && $('stepK').textContent === 'Step %d of 6'" % (i + 1), timeout=25000)
            steps.append(await q("$('stepT').textContent + ' | ' + $('stepH').textContent + ' | ' + $('count').textContent"))
            if i in (0, 3): await pv.wait_for_timeout(250); await pv.screenshot(path='tests/out/v2_routine_step%d_en.png' % (i + 1))
        await pv.wait_for_function("!$('session').hidden", timeout=25000)
        names = [s.split(' | ')[0] for s in steps]
        check('v2 full check: 6 step cards in order (left: rest, held out, finger to nose; then right) with countdowns', names == ['Left hand · At rest', 'Left hand · Arm held out', 'Left hand · Finger to nose', 'Right hand · At rest', 'Right hand · Arm held out', 'Right hand · Finger to nose'] and 'Switch hands' in steps[3], steps)
        said = await q("window.__said")
        check('v2 full check: spoken prompt for every step, the hand switch and the end', len(said) == 7 and said[0].startswith('Left hand. At rest.') and 'Switch hands' in said[3] and said[-1] == 'Full check done. Well done.', said)
        ss = await q("({ cells: [...document.querySelectorAll('#sessGrid .cellbtn')].map(b => b.textContent), sum: [...document.querySelectorAll('#sessSum li')].map(l => l.textContent), j: " + JN + ".map(e => [e.session, e.step, e.posture, e.side]) })")
        check('v2 full check: 6 measurements saved with one session id (steps 0-5)', len(ss['j']) == 6 and len(set(x[0] for x in ss['j'])) == 1 and sorted(x[1] for x in ss['j']) == [0, 1, 2, 3, 4, 5], ss['j'])
        check('v2 full check: combined summary (3 positions x 2 hands at ~6 Hz) + plain-language lines with the pattern note', len(ss['cells']) == 6 and all(any(v in c for v in ('5.9 Hz', '6 Hz', '6.0 Hz', '6.1 Hz')) for c in ss['cells']) and any('Largest shaking' in s for s in ss['sum']) and any('Both hands were similar' in s for s in ss['sum']) and any('A pattern, not a diagnosis' in s for s in ss['sum']), ss)
        check('v2 full check: summary fits 360 px', await sw() <= 360, await sw())
        await pv.screenshot(path='tests/out/v2_session_en.png', full_page=True)
        await pv.tap('#sessGrid .cellbtn'); await pv.wait_for_timeout(250)
        check("v2 full check: a cell opens that step's full result", await q("!$('result').hidden && __tremor.last.posture === 'rest' && __tremor.last.side === 'left' && !$('resBack').hidden"))
        await pv.tap('#resBack'); await pv.wait_for_timeout(100)
        check('v2 full check: Back returns to the summary', await q("!$('session').hidden"))
        await q("clearInterval(window.__mi); __tremor.goTab('journal')")
        check('v2 journal: the full check is one row ("Full check · 6 steps") that reopens the summary', await q("document.querySelectorAll('#jList .jitem').length === 1 && $('jList').textContent.includes('Full check · 6 steps')"))
        await pv.tap('#jList .jitem'); await pv.wait_for_timeout(150)
        check('v2 journal: tapping the full-check row opens its summary', await q("!$('session').hidden && document.querySelectorAll('#sessGrid .cellbtn:not([disabled])').length === 6"))
        # mute: no voice (beeps also skipped)
        await q("seedJ([]); window.__said = []; __tremor.goTab('setup')"); await pv.tap('#muteBtn')
        check('v2 mute: button pressed and remembered', await q("$('muteBtn').getAttribute('aria-pressed') === 'true' && JSON.parse(localStorage.getItem('tremor.settings.v1')).mute === true"))
        await q(MOTION6); await pv.tap('#routineBtn'); await pv.wait_for_function("$('stepK').textContent === 'Step 2 of 6'", timeout=20000)
        check('v2 mute: no voice prompts while muted', await q("window.__said.length === 0 && __tremor.voice.skipped >= 2"))
        await pv.tap('#cancelBtn'); await pv.wait_for_timeout(300)
        check('v2 full check: cancel part-way -> summary of the finished step(s)', await q("!$('session').hidden && document.querySelectorAll('#sessGrid .cellbtn:not([disabled])').length >= 1"))
        await q("clearInterval(window.__mi)"); await pv.tap('#muteBtn')

        # ---- spiral drawing test ----
        sa = await q("""(() => { const mm = 0.16, o = { cx: 160, cy: 160, b: 160 * 0.44 / (3 * 2 * Math.PI), turns: 3, secs: 10, fs: 60 }, at = { cx: 160, cy: 160, mmPerPx: mm };
          const f = (r) => ({ f: r.f0, s: r.strength, pp: r.pp, score: r.spiral && r.spiral.score, turns: r.spiral && r.spiral.turns, err: r.error });
          return { wob: f(__tremor.analyzeSpiral(spiralPts({ ...o, wobHz: 6, wobPx: 1 / mm, noisePx: 0.3 }), at)), smooth: f(__tremor.analyzeSpiral(spiralPts({ ...o, noisePx: 0.3 }), at)),
            big: f(__tremor.analyzeSpiral(spiralPts({ ...o, wobHz: 4.5, wobPx: 3 / mm, noisePx: 0.3 }), at)), short: f(__tremor.analyzeSpiral(spiralPts({ ...o, turns: 1, secs: 3 }), at)) }; })()""")
        check('v2 spiral (synthetic, 6 Hz radial wobble, 2 mm back and forth): 6 Hz ±0.3, size ~2 mm, turns counted outside the centre (2.5-3 of 3)', abs(sa['wob']['f'] - 6) < 0.3 and sa['wob']['s'] == 'clear' and 1.5 < sa['wob']['pp'] < 2.6 and 2.5 <= sa['wob']['turns'] <= 3.0, sa['wob'])
        check('v2 spiral score: smooth line < 1.5 (wobble < 0.1 mm) < 2 mm wobble < 6 mm wobble', sa['smooth']['score'] < 1.5 and sa['smooth']['pp'] < 0.1 and sa['smooth']['score'] < sa['wob']['score'] < sa['big']['score'], [sa['smooth'], sa['wob']['score'], sa['big']['score']])
        print('     spiral: f=%.2f Hz pp=%.2f mm score smooth/2mm/6mm = %s/%s/%s' % (sa['wob']['f'], sa['wob']['pp'], sa['smooth']['score'], sa['wob']['score'], sa['big']['score']))
        check('v2 spiral: under 2 turns -> rejected as too short', sa['short']['err'] == 'short', sa['short'])
        await q("seedJ([]); __tremor.goTab('setup')"); await pv.tap('#spiralBtn'); await pv.wait_for_timeout(250)
        await pv.tap('[data-key=spSide] [data-v=left]')
        check('v2 spiral screen fits 360 px; Done disabled before drawing', await sw() <= 360 and await q("$('spDone').disabled"))
        await pv.screenshot(path='tests/out/v2_spiral_empty.png', full_page=True)
        mmpx = await q("__tremor.spiral.mmPerPx")
        await q("drawSpiralLive(7, 6, %f)" % (1 / mmpx))
        dd = await q("({ turns: __tremor.spiral.turns, n: __tremor.spiral.pts.length, done: !$('spDone').disabled, msg: $('spMsg').textContent })")
        check('v2 spiral UI: finger drawing tracked (pointer events), Done enabled after 2+ turns', dd['turns'] > 2.3 and dd['n'] > 150 and dd['done'] and 'tap Done' in dd['msg'], dd)
        await pv.screenshot(path='tests/out/v2_spiral_draw.png', full_page=True)
        await pv.tap('#spDone'); await pv.wait_for_timeout(350)
        sr = await q("({ res: !$('spResult').hidden, score: $('spScore').textContent, lv: $('spScoreLv').textContent, det: $('spDetails').textContent, img: $('spImg').src.slice(0, 22), e: " + JN + "[0] })")
        check('v2 spiral UI: result (score, level, ~6 Hz, size) saved to the journal with its image', sr['res'] and '/ 10' in sr['score'] and 'Hz' in sr['det'] and sr['img'] == 'data:image/png;base64,' and sr['e']['kind'] == 'spiral' and sr['e']['side'] == 'left' and sr['e']['spiral']['img'].startswith('data:image/png') and abs(sr['e']['f'] - 6) < 0.5, {k: sr[k] for k in ('score', 'lv', 'det')})
        await pv.screenshot(path='tests/out/v2_spiral_result_en.png', full_page=True)
        await q("__tremor.goTab('journal')"); await pv.tap('#jList .jitem'); await pv.wait_for_timeout(250)
        check('v2 spiral: reopened from the journal (image, score, saved line, Back)', await q("!$('spResult').hidden && !$('spImg').hidden && !$('spSaved').hidden && $('spAgain').hidden"))
        await pv.tap('#spBack'); await pv.wait_for_timeout(100)
        check('v2 spiral: Back -> journal', await q("!$('journal').hidden"))
        await q("__tremor.goTab('trends')"); await pv.tap('.chips[data-f=cond] [data-v=spiral]'); await pv.tap('.chips[data-f=side] [data-v=both]'); await pv.wait_for_timeout(100)
        check('v2 trends: "Spiral" condition shows spiral drawings', await q("__tremor.trend.pts.length === 1 && __tremor.trend.pts[0].kind === 'spiral'"))

        # ---- Hebrew + 360 px on every new screen ----
        await q(TRS); await q("__tremor.setLang('he'); Object.assign(__tremor.settings.tf, { limb: 'hand', cond: 'hold', side: 'both', range: '90' })")
        for tab in ['setup', 'journal', 'trends']:
            await q("__tremor.goTab('%s')" % tab); await pv.wait_for_timeout(200)
            check('v2 he: %s fits 360 px (no horizontal scroll)' % tab, await sw() <= 360, await sw())
            await pv.screenshot(path='tests/out/v2_%s_he.png' % tab, full_page=True)
        het = await q("({ tabs: $('tabs').textContent, journal: $('journal').textContent, trends: $('trends').textContent, dir: document.documentElement.dir })")
        check('v2 he: tabs, journal (tracking, reminder, backup) and trends (L/R, medication) translated, RTL', het['dir'] == 'rtl' and all(k in het['tabs'] for k in ['מדידה', 'יומן', 'מגמות']) and all(k in het['journal'] for k in ['המעקב שלכם', 'תזכורת יומית', 'ייצוא גיבוי']) and all(k in het['trends'] for k in ['שמאל מול ימין', 'לפני ואחרי תרופה', 'קטן בממוצע ב־35%']), het['trends'][:200])
        await q("seedJ([]); window.__said = []; __tremor.goTab('setup')"); await q(MOTION6)
        await pv.tap('#routineBtn'); await pv.wait_for_function("$('stepK').textContent === 'שלב 1 מתוך 6'", timeout=10000); await pv.wait_for_timeout(200)
        stp = await q("({ t: $('stepT').textContent, h: $('stepH').textContent, said: window.__said[0] || '' })")
        check('v2 he: full-check step card + voice prompt in Hebrew', 'יד שמאל' in stp['t'] and 'במנוחה' in stp['t'] and 'יד שמאל' in stp['said'], stp)
        await pv.screenshot(path='tests/out/v2_routine_step_he.png')
        await pv.wait_for_function("$('stepK').textContent === 'שלב 2 מתוך 6'", timeout=20000); await pv.tap('#cancelBtn'); await q("clearInterval(window.__mi)"); await pv.wait_for_timeout(200)
        check('v2 he: partial full-check summary in Hebrew, fits 360 px', await q("!$('session').hidden && $('session').textContent.includes('בדיקה מלאה')") and await sw() <= 360)
        await pv.screenshot(path='tests/out/v2_session_he.png', full_page=True)
        await q("__tremor.goTab('setup')"); await pv.tap('#spiralBtn'); await pv.wait_for_timeout(200)
        await q("drawSpiralLive(5, 5, %f)" % (1.5 / mmpx)); await pv.tap('#spDone'); await pv.wait_for_timeout(300)
        sph = await q("({ t: $('spResult').textContent, sw: document.documentElement.scrollWidth })")
        check('v2 he: spiral result translated, fits 360 px', 'תוצאת הספירלה' in sph['t'] and 'לא אבחון' in sph['t'] and sph['sw'] <= 360, sph['sw'])
        await pv.screenshot(path='tests/out/v2_spiral_result_he.png', full_page=True)
        await q("__tremor.setLang('en')")
        check('v2: no page errors', not errs4, errs4)
        await b.close()
    print('FAILURES:', fails)
asyncio.run(main()); srv.terminate()
sys.exit(1 if fails else 0)
