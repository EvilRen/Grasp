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
MOTION6 = """window.__mi = setInterval(() => { const t = performance.now(), A = 0.8 * Math.pow(2*Math.PI*6, 2) / 1000;
    const a = { x: A * Math.sin(2*Math.PI*6*t/1000) + (Math.random()-0.5)*0.05, y: (Math.random()-0.5)*0.05, z: (Math.random()-0.5)*0.05 };
    window.dispatchEvent(new DeviceMotionEvent('devicemotion', { acceleration: a, accelerationIncludingGravity: { x: a.x, y: a.y, z: a.z + 9.81 }, interval: 16 })); }, 16);"""
SEED = """(n) => { const h = []; for (let i = 0; i < n; i++) h.push({ ts: Date.now() - (n - i) * 864e5, sensor: 'motion', limb: 'hand', posture: 'rest', side: i % 2 ? 'right' : 'left',
    f: +(5 + Math.sin(i / 3)).toFixed(2), strength: ['clear','weak','none'][i % 3], pp: +(1 + i / 20).toFixed(2), fs: 60, med: i % 4 ? '' : 'yes', medText: '', note: i === 3 ? 'walk' : '', tod: 'morning' });
    localStorage.setItem('tremor.history.v1', JSON.stringify(h.reverse())); }"""
PIX = """(() => { const cv = $('trend'), c = cv.getContext('2d'), d = c.getImageData(0, 0, cv.width, cv.height).data; let sky = 0;
    for (let i = 0; i < d.length; i += 4) if (d[i] < 120 && d[i+1] > 150 && d[i+2] > 190) sky++; return { pts: __tremor.trend.pts.length, sky, hidden: cv.hidden, w: cv.width }; })()"""
CMP = """(() => { const L = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0)), R = __tremor.analyze(syn(6.5, 60, 20, 0.5, 0.05, 0));
    Object.assign(L, {sensor:'motion', limb:'hand', posture:'rest', side:'left', ts: Date.now(), plannedS:20}); Object.assign(R, {sensor:'motion', limb:'hand', posture:'rest', side:'right', ts: Date.now(), plannedS:20});
    R.compare = { left: L, right: { ...R } }; renderResult(R); })()"""
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
        e = await page.evaluate("JSON.parse(localStorage.getItem('tremor.history.v1'))[0]")
        check('history entry carries side, medication, note, time of day', e['side']=='left' and e['med']=='yes' and e['medText']=='levodopa' and e['note']=='after coffee' and e['tod'] in ('morning','afternoon','evening','night'), e)
        ht = await page.evaluate("$('histList').textContent")
        check('history list shows the notes', 'levodopa' in ht and 'after coffee' in ht and 'left' in ht, ht[:120])
        check('result shows side and notes', 'left side' in await page.evaluate("$('resSub').textContent") and 'levodopa' in await page.evaluate("$('resNotes').textContent"))

        # ---- compare sides flow ----
        await page.evaluate("__tremor.CONFIG.COMPARE_GAP_S = 1")
        await page.tap('#setupBtn'); await page.tap('#compareBtn')
        await page.wait_for_function("$('recSide').textContent.includes('Left')", timeout=3000)
        check('compare: left side prompt during first countdown', True)
        await page.wait_for_function("$('recStatus').textContent.includes('right side')", timeout=15000)
        check('compare: right-side prompt + countdown between measurements', await page.evaluate("$('recNote').textContent.includes('right') && $('count').textContent !== ''"))
        await page.wait_for_function("!$('compareCard').hidden", timeout=20000)
        cmp = await page.evaluate("(() => { const c = __tremor.last.compare; return { l: c.left.side, r: c.right.side, lf: c.left.f0, rf: c.right.f0, cells: $('cmpGrid').children.length, diff: $('cmpDiff').textContent }; })()")
        check('compare card: two results, left then right, ~6 Hz each', cmp['l']=='left' and cmp['r']=='right' and abs(cmp['lf']-6) < 0.3 and abs(cmp['rf']-6) < 0.3 and cmp['cells']==12 and 'Difference' in cmp['diff'], cmp)
        sides = await page.evaluate("JSON.parse(localStorage.getItem('tremor.history.v1')).slice(0,2).map(e => e.side)")
        check('compare: both measurements saved with sides', sides == ['right', 'left'], sides)
        await page.evaluate("clearInterval(window.__mi)")
        await page.screenshot(path='tests/out/out_compare.png', full_page=True)

        # ---- trend chart ----
        await page.evaluate("localStorage.setItem('tremor.history.v1', '[]')"); await page.evaluate("show('setup'); renderHistory()")
        check('trend: hidden with no history', await page.evaluate("$('historyWrap').hidden"))
        await page.evaluate(SEED, 1); await page.evaluate("show('setup'); renderHistory()"); await page.wait_for_timeout(150)
        check('trend: empty state with 1 point', await page.evaluate("!$('trendEmpty').hidden && $('trend').hidden"))
        await page.evaluate(SEED, 6); await page.evaluate("show('setup'); renderHistory()"); await page.wait_for_timeout(150)
        drawn = await page.evaluate(PIX)
        check('trend: 6 seeded points drawn (sky-coloured line pixels present)', drawn['pts']==6 and drawn['sky'] > 200 and not drawn['hidden'], drawn)
        await page.tap('[data-key=trendSide] [data-v=left]'); await page.wait_for_timeout(150)
        check('trend: side filter -> 3 left points', await page.evaluate("__tremor.trend.pts.length === 3 && __tremor.trend.pts.every(p => p.side === 'left')"))
        await page.tap('[data-key=limb] [data-v=leg]'); await page.evaluate("renderHistory()"); await page.wait_for_timeout(150)
        check('trend: filtered by current setup (leg -> empty)', await page.evaluate("!$('trendEmpty').hidden"))
        await page.tap('[data-key=limb] [data-v=hand]'); await page.tap('[data-key=trendSide] [data-v=both]'); await page.wait_for_timeout(150)
        box = await page.evaluate("(() => { const r = $('trend').getBoundingClientRect(); return { x: r.left + __tremor.trend.xs[2], y: r.top + 60 }; })()")
        await page.mouse.click(box['x'], box['y']); await page.wait_for_timeout(100)
        info = await page.evaluate("$('trendInfo').textContent")
        check('trend: tap a point -> highlighted with details', await page.evaluate("__tremor.trend.sel === 2") and 'Hz' in info and 'mm' in info, info)
        await page.evaluate(SEED, 50); await page.evaluate("renderHistory()"); await page.wait_for_timeout(150)
        check('trend: handles 50 points', await page.evaluate("__tremor.trend.pts.length === 50 && __tremor.trend.xs.length === 50"))

        # ---- export CSV ----
        async with page.expect_download() as dl:
            await page.tap('#exportBtn')
        d = await dl.value; csv = open(await d.path(), encoding='utf-8-sig').read().splitlines()
        check('export: CSV download with header row + 50 rows', csv[0] == 'date,sensor,limb,posture,side,freq_hz,amplitude,strength,medication,note' and len(csv) == 51 and d.suggested_filename.endswith('.csv'), [csv[0], len(csv)])
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
        await pg.evaluate(SEED, 8); await pg.evaluate("show('setup'); renderHistory()"); await pg.wait_for_timeout(200)
        check('he: RTL + Hebrew brand', await pg.evaluate("document.documentElement.dir === 'rtl' && document.querySelector('.brand').textContent.includes('טרימורטי')"))
        check('he: no horizontal overflow on setup', await pg.evaluate("document.documentElement.scrollWidth <= 360"))
        await pg.screenshot(path='tests/out/he_setup.png', full_page=True)
        await pg.evaluate("(() => { const r = __tremor.analyze(syn(5, 60, 20, 1, 0.05, 0)); Object.assign(r, {sensor:'motion', limb:'hand', posture:'rest', side:'left', notes:{med:'yes', medText:'לבודופה', note:'אחרי קפה'}, ts: Date.now(), plannedS:20}); renderResult(r); })()")
        await pg.wait_for_timeout(200); await pg.screenshot(path='tests/out/he_result.png', full_page=True)
        await pg.evaluate(CMP)
        await pg.wait_for_timeout(200)
        check('he: compare card rendered', await pg.evaluate("!$('compareCard').hidden && $('cmpDiff').textContent.includes('הפרש')"))
        await pg.evaluate("$('compareCard').scrollIntoView()"); await pg.screenshot(path='tests/out/he_compare.png', full_page=True)
        await pg.evaluate("show('setup'); renderHistory(); $('historyWrap').scrollIntoView()"); await pg.wait_for_timeout(200)
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
        check('edge: 3.0 Hz @60/s -> low-edge warning says below 3 Hz is not measured', 'bottom of the measured range (3 Hz)' in i['warn'] and 'Below 3 Hz is not measured' in i['warn'], i['warn'][:120])
        check('safety note visible (EN): not a diagnosis, neurologist, repeat 3–4 times both hands', all(k in i['safety'] for k in ['Not a diagnosis', 'neurologist', 'Take your measurements', '3–4 times', 'both hands', 'held out']) and await pi.evaluate("$('safety').getBoundingClientRect().height > 40"), i['safety'][:80])
        check('phone 360: no horizontal scroll on result with interpretation', i['sw'] <= 360, i['sw'])
        await pi.screenshot(path='tests/out/interp_rest_en.png', full_page=True)
        await pi.evaluate("$('interpCard').scrollIntoView()"); await pi.screenshot(path='tests/out/interp_rest_en_panel.png')
        # edge cases: drift below the band, top edge, no edge
        r = await pi.evaluate("(() => { const r = __tremor.analyze(syn(2.4, 60, 20, 6, 0.05, 0)); return { e: r.edge, o: r.edgeOut, s: r.strength }; })()")
        check('edge: power still rising below 3 Hz -> flagged as outside (edgeOut)', r['e'] == 'lo' and r['o'], r)
        await pi.evaluate(RENDER, [[2.4, 60, 20, 6, 0.05, 0], {'sensor':'motion','limb':'hand','posture':'rest'}])
        w = await pi.evaluate("$('resWarn').textContent")
        check('edge: drift warning explains below 3 Hz is not measured + caveat on matches', 'keeps rising below it' in w and 'Below 3 Hz is not measured' in w and await pi.evaluate("!$('interpCaveat').hidden && $('interpCaveat').textContent.includes('drifting')"), w[:120])
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
        check('he: age comparison + edge warning translated', 'לגיל 75 ומעלה' in he['norm'] and 'מתחת ל־' in he['warn'] and 'לא נמדד' in he['warn'], [he['norm'][:80], he['warn'][:80]])
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
        await b.close()
    print('FAILURES:', fails)
asyncio.run(main()); srv.terminate()
sys.exit(1 if fails else 0)
