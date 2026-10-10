# The replay clip: the round's best moment as a slow-motion replay to watch, save or send.
# Covers: the rolling capture (a fixed ring of small frames: <= 360 px wide, <= 72k px, 120 frames = 6 s at 20 fps, < 40 MB; nothing captured while
# the pause sheet / a card / the replay is up or the tab is hidden; a slow-frame gate), the moment scoring (SUPER blast, PERFECT streak, boss down,
# wall cleared, stage clear / record, Frenzy speed step; Smash: boss, big collapse; Slice: combo; the best wins), the clip window (3 s before,
# 1.5 s after, encoded to JPEGs), the 'Replay' pill on the cards (Endless, Adventure clear / fail, the boss victory, Frenzy, Smash, Slice), the
# replay sheet (frames advance, the slow-motion part, the caption, EN / HE), the video (MediaRecorder in headless Chromium: a non-empty webm /
# mp4), Share (navigator.share with the file + the challenge line when canShare says yes; else a download), Save (a download), the still PNG when
# MediaRecorder is missing, the feature off when the APIs are missing, the 3D renderer's capture. Screenshots tests/out/replay_*.png.
exec(open('tests/test_challenge.py').read().split('async def main')[0])
R = "__grasp.replay"; F = "__grasp.frenzy"; SMH = "__grasp.smash"; SMK = "__grasp.sm"
ST = f"{R}.state"
STUB = """window.__shared = []; window.__clip = []; try { navigator.clipboard.writeText = async (x) => { __clip.push(x); }; } catch (e) {}
window.stubShare = (can, abort) => { Object.defineProperty(navigator, 'canShare', { configurable: true, value: (d) => can && !!(d && d.files && d.files.length) });
  Object.defineProperty(navigator, 'share', { configurable: true, value: async (d) => { if (abort) { const e = new Error('x'); e.name = 'AbortError'; throw e; } __shared.push({ title: d.title, text: d.text, files: (d.files || []).map(f => [f.name, f.type, f.size]) }); } }); };"""
DROP = """window.dropFruit = () => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12; f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };"""

async def caps(page, n, timeout=30000):  # the ring has captured n more frames
    c0 = await page.evaluate(f"{ST}.caps"); await page.wait_for_function(f"{ST}.caps >= {c0 + n}", timeout=timeout)

async def clip_of(page, kind, timeout=12000):
    await page.wait_for_function(f"{ST}.clip && {ST}.clip.kind === '{kind}' && !{ST}.pend && !{ST}.enc", timeout=timeout)
    return await page.evaluate(f"{ST}.clip")

async def pill(page, E, timeout=15000):  # the card's Replay pill is up (the card fully in)
    await page.wait_for_function(f"{E}.over && {E}.ui.rpBtn && performance.now() - {E}.overAt > 900", timeout=timeout)
    return await page.evaluate(f"({{ p: {E}.ui.rpBtn, card: {E}.ui.card, btn: {E}.ui.buttons, H: innerHeight, W: innerWidth }})")

def overlaps(a, b): return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']

def pill_ok(tag, q):
    p, c = q['p'], q['card']
    inside = p['x'] >= 0 and p['y'] >= 0 and p['x'] + p['w'] <= q['W'] and p['y'] + p['h'] <= q['H']
    clear = not any(overlaps(p, r) for r in q['btn'].values())
    check(f'{tag}: the "Replay" pill on the card ({"its bottom edge" if not p["corner"] else "the top corner"}), on screen, clear of the card\'s buttons',
          inside and clear and (p['corner'] or (p['y'] <= c['y'] + c['h'] and p['y'] + p['h'] > c['y'] + c['h'])), q)

async def tap_pill(page, E, mobile):
    p = await page.evaluate(f"{E}.ui.rpBtn"); x, y = p['x'] + p['w'] / 2, p['y'] + p['h'] / 2
    if mobile: await page.tap('#stage', position={'x': x, 'y': y})
    else: await page.mouse.click(x, y)
    await page.wait_for_function(f"{ST}.open && {ST}.play && {ST}.play.drawn > 3", timeout=8000)

async def play_checks(page, tag, shot=None):  # frames advance, the slow-motion part shows up, the caption
    a = await page.evaluate(f"{ST}.play"); await page.wait_for_timeout(700); b2 = await page.evaluate(f"{ST}.play")
    if shot:
        await page.wait_for_function(f"{ST}.play && {ST}.play.tc > -150 && {ST}.play.tc < 250", timeout=12000, polling=16)
        await page.screenshot(path=shot)
    await page.wait_for_function(f"{ST}.play && ({ST}.play.loops >= 1 || {ST}.play.tc > 900)", timeout=15000)
    c = await page.evaluate(f"{ST}.play")
    idx = c['idx']
    check(f'{tag}: the replay plays: frames advance in order (drawn {a["drawn"]} -> {b2["drawn"]}, {len(set(idx))} distinct frames)', b2['drawn'] > a['drawn'] and len(set(idx)) >= 20 and sum(1 for i in range(1, len(idx)) if idx[i] > idx[i - 1]) >= len(idx) * 0.8, idx[:12])
    check(f'{tag}: a slow-motion part around the moment (x0.35), the whole clip 4-7 s', abs(c['minSpeed'] - 0.35) < 1e-6 and c['slowFrames'] > 3 and 4000 <= c['dur'] <= 7000, {k: c[k] for k in ('minSpeed', 'slowFrames', 'dur')})
    return c

async def video_checks(page, tag):
    await page.wait_for_function(f"{ST}.video || {ST}.still", timeout=20000)
    v = await page.evaluate(f"{ST}.video")
    head = await page.evaluate(f"(async () => {{ const v = {R}.rp.video; if (!v) return null; const u = new Uint8Array(await v.blob.slice(0, 12).arrayBuffer()); return Array.from(u); }})()")
    webm = head and head[:4] == [0x1A, 0x45, 0xDF, 0xA3]; mp4 = head and bytes(head[4:8]) == b'ftyp'
    check(f'{tag}: MediaRecorder (headless Chromium) records the first loop: a non-empty {v and v["type"]} (<= 3 MB, ~4-8 s)', v and 1000 < v['size'] <= 3_000_000 and (webm or mp4) and v['type'] in ('video/webm', 'video/mp4') and 3500 <= v['ms'] <= 9000, [v, head])
    btn = await page.evaluate("[$('rpShare').disabled, $('rpSave').disabled, $('rpNote').textContent]")
    check(f'{tag}: Share and Save are on once the video is ready', btn[0] is False and btn[1] is False and btn[2] == '', btn)
    return v

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== R1: the ring: frame size, bounded count and memory, timestamps, the capture's cost, the gates =====
        ctx, page, errs = await fresh(b, init=STUB)
        sz = await page.evaluate(f"[[360, 740], [412, 915], [390, 844], [1280, 800], [740, 360], [1920, 1080], [3840, 2160]].map(([w, h]) => {R}.size(w, h))")
        cfg = await page.evaluate(f"({{ n: {R}.n(), cfg: {R}.cfg, ok: {ST}.ok, rec: {ST}.recOk }})")
        check('frame size: <= 360 px wide, <= 400 tall, <= ~72k px, even, the screen\'s shape kept (360x740 -> 188x384, 1280x800 -> 340x212)',
              sz[0] == [188, 384] and sz[3] == [340, 212] and all(w <= 360 and h <= 400 and w * h <= 72000 * 1.03 and w % 2 == 0 and h % 2 == 0 for w, h in sz)
              and all(abs(w / h - a / c) < 0.05 for (w, h), (a, c) in zip(sz, [[360, 740], [412, 915], [390, 844], [1280, 800], [740, 360], [1920, 1080], [3840, 2160]])), sz)
        check('the ring: 120 frames (6 s at 20 fps), at most 120 x 72k px x 4 B < 40 MB; capture and recording supported here', cfg['n'] == 120 and 120 * 72000 * 1.03 * 4 < 40e6 and cfg['ok'] and cfg['rec'], cfg)
        await endless(page)
        await page.evaluate(f"{R}.rp.noGate = true")
        await page.wait_for_function(f"{ST}.caps >= 135", timeout=40000)
        r1 = await page.evaluate(f"(() => {{ const s = {ST}, f = {R}.frames(-1e9, 1e9); return {{ count: s.count, ring: s.ring, fw: s.fw, fh: s.fh, bytes: {R}.bytes(), ts: f.map(q => q.t), seq: f.map(q => q.seq), cost: s.cost, caps: s.caps }}; }})()")
        d = sorted(r1['ts'][i + 1] - r1['ts'][i] for i in range(len(r1['ts']) - 1))
        check('after 135+ captures the ring holds exactly 120 frames (no growth), 120 canvases, 340x212 each: ~34.6 MB', r1['count'] == 120 and r1['ring'] == 120 and [r1['fw'], r1['fh']] == [340, 212] and r1['bytes'] == 120 * 340 * 212 * 4 and r1['bytes'] < 40e6, {k: r1[k] for k in ('count', 'ring', 'bytes', 'caps')})
        check('the ring\'s frames are the newest, oldest first, ~50 ms apart (every 3rd frame), spanning ~6 s', len(d) == 119 and all(x > 0 for x in d) and 40 <= d[len(d) // 2] <= 70 and r1['seq'] == sorted(r1['seq']) and 5000 <= r1['ts'][-1] - r1['ts'][0] <= 6500, [d[len(d) // 2], r1['ts'][-1] - r1['ts'][0]])
        print('capture cost (desktop 2D, JS time per capture, ms):', r1['cost'], flush=True)
        check('the capture is cheap on the main thread (2D: drawn at the next frame\'s start, no forced flush): avg < 3 ms', r1['cost']['avg'] < 3, r1['cost'])
        # the gates: slow frames, a hidden tab
        g = await page.evaluate(f"(async () => {{ const r = {R}.rp, c = {R}.cfg; r.noGate = false; c.gateDt = 1; await new Promise(q => setTimeout(q, 150)); const a = r.caps, k = r.skipped; await new Promise(q => setTimeout(q, 600)); const out = {{ caps: r.caps - a, skipped: r.skipped - k }}; c.gateDt = 50; r.dtEma = 16.7; r.noGate = true; return out; }})()")
        check('slow frames (the gate): no capture at all while frames are slower than the gate', g['caps'] == 0 and g['skipped'] >= 3, g)
        hd = await page.evaluate(f"(async () => {{ Object.defineProperty(document, 'hidden', {{ configurable: true, get: () => true }}); await new Promise(q => setTimeout(q, 120)); const r = {R}.rp, a = r.caps, cl = r.clock; await new Promise(q => setTimeout(q, 500)); const out = {{ caps: r.caps - a, clock: r.clock - cl, why: {R}.block() }}; delete document.hidden; return out; }})()")
        check('a hidden tab: nothing captured, the clip clock stands still', hd['caps'] == 0 and hd['clock'] == 0 and hd['why'] == 'hidden', hd)
        # the pause sheet: capture waits
        await page.evaluate("openMenu()"); await page.wait_for_timeout(200)
        a0 = await page.evaluate(f"[{ST}.caps, {ST}.clock, {ST}.paused]"); await page.wait_for_timeout(600); a1 = await page.evaluate(f"[{ST}.caps, {ST}.clock, {ST}.paused]")
        check('the pause sheet is open: capture paused (no frames, the clip clock stopped)', a0[0] == a1[0] and a0[1] == a1[1] and a1[2] == 'menu', [a0, a1])
        await page.evaluate("closeMenu()"); await caps(page, 5)
        check('the sheet closed: capture resumes', await page.evaluate(f"{ST}.paused") == '')
        check('R1: no page errors', not errs, errs)

        # ===== R2: the moments: scoring, the best one wins, the clip window =====
        await page.evaluate(f"{R}.reset(); {S}.noTiming = true"); await caps(page, 70)
        m = await page.evaluate(f"""(() => {{ const R = {R}, out = {{}};
          out.combo = !!R.moment('combo', 39, {{ n: 3 }}); out.perfLow = R.moment('perfect', 30) === null;
          const n0 = R.state.log.length; R.strikeHit('soft', false, 1, false); out.soft = R.state.log.length === n0;
          R.strikeHit('hard', false, 6, false); out.blast = R.state.log[R.state.log.length - 1]; out.pend1 = R.state.pend.kind;
          return out; }})()""")
        check('moment scoring: a soft chip is no moment; a 6-brick hard hit is (33) but not better than a x3 combo (39); a lower one never replaces the best',
              m['combo'] and m['perfLow'] and m['soft'] and m['blast']['kind'] == 'blast' and m['blast']['score'] == 33 and m['pend1'] == 'combo', m)
        sb = await page.evaluate("blast('super', 2, 2)")
        m2 = await page.evaluate(f"(() => {{ const L = {ST}.log; for (let i = 0; i < 3; i++) timingFx({{ grade: 'perfect', v: 1 }}, {{ x: 640, y: 400, r: 20 }}, performance.now()); return {{ sup: L.filter(q => q.kind === 'super').pop(), perf: {ST}.log.filter(q => q.kind === 'perfect'), pend: {ST}.pend }}; }})()")
        check(f'a real SUPER blast ({sb["n"]} bricks) is a moment (40 + 3 x bricks) and takes the lead', m2['sup'] and m2['sup']['n'] == sb['n'] and m2['sup']['score'] == 40 + 3 * sb['n'] and m2['pend']['kind'] == 'super', m2['sup'])
        check('a PERFECT streak (x3) is a moment (48) but the SUPER stays the best', len(m2['perf']) >= 1 and m2['perf'][-1]['n'] == 3 and m2['perf'][-1]['score'] == 48 and m2['pend']['kind'] == 'super', m2['perf'])
        await page.wait_for_timeout(500)
        bd = await page.evaluate(f"(() => {{ spawnBoss(1, performance.now()); const b = {S}.boss; bossDefeated(b, performance.now()); return {{ pend: {ST}.pend, t: {R}.rp.clock }}; }})()")
        check('a boss down (90) beats them all: the round\'s best moment', bd['pend'] and bd['pend']['kind'] == 'boss' and bd['pend']['score'] == 90, bd)
        await page.wait_for_timeout(500)
        mid = await page.evaluate(f"({{ clip: {ST}.clip, pend: !!{ST}.pend }})")
        check('the clip waits 1.5 s after the moment (to have the aftermath)', mid['pend'] and (mid['clip'] is None or mid['clip']['kind'] != 'boss'), mid)
        c = await clip_of(page, 'boss')
        ts = c['ts']; inwin = all(-3000 <= x <= 1500 for x in ts)
        check(f'the clip: the ring\'s window around the moment, 3 s before and 1.5 s after ({c["frames"]} frames, {c["t0"]:.0f} .. {c["t1"]:.0f} ms), oldest first, the peak frame at the moment',
              inwin and c['t0'] <= -2850 and 1350 <= c['t1'] <= 1500 and c['frames'] >= 70 and ts == sorted(ts) and abs(ts[c['peak']]) <= 30 and c['lost'] == 0, {k: c[k] for k in ('frames', 't0', 't1', 'peak', 'lost')})
        check(f'the clip is small: JPEGs, {c["bytes"] // 1024} KB (< 3 MB), and its peak thumbnail decoded', 20_000 < c['bytes'] < 3_000_000 and c['thumb'], c['bytes'])
        lo = await page.evaluate(f"{R}.moment('super', 60)")
        check('a later, weaker moment keeps the clip', lo is None and (await page.evaluate(f"{ST}.clip.kind")) == 'boss')
        # the timeline: the slow part
        tl = await page.evaluate(f"(() => {{ const T = {R}.timeline(-3000, 1500); return {{ dur: T.dur, s0: {R}.speed(0), s1: {R}.speed(-2000), s2: {R}.speed(1200), mid: {R}.speed(-325), a: {R}.clipAt(T, 0), b: {R}.clipAt(T, T.dur) }}; }})()")
        check('the playback: x0.35 around the moment, ramping back to x1 (the 4.5 s window plays in ~5.8 s)', abs(tl['s0'] - 0.35) < 1e-9 and tl['s1'] == 1 and tl['s2'] == 1 and 0.35 < tl['mid'] < 1 and 5300 <= tl['dur'] <= 6300 and tl['a'] == -3000 and tl['b'] == 1500, tl)
        check('R2: no page errors', not errs, errs)

        # ===== R3: the Endless card: the pill, the replay sheet, the video, Share / Save / the download fallback =====
        await page.evaluate(f"(() => {{ const s = {S}; s.score = 1234; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        q = await pill(page, S); pill_ok('Endless round-over card (desktop)', q)
        check('the card is up: capture paused', await page.evaluate(f"{ST}.paused") == 'card')
        await page.screenshot(path='tests/out/replay_card_endless_en.png')
        await tap_pill(page, S, False)
        o = await page.evaluate(f"({{ hidden: $('replay').hidden, title: $('rpTitle').textContent, share: $('rpShare').innerText.trim(), save: $('rpSave').innerText.trim(), cap: {ST}.play.cap, vw: {ST}.play.vw, vh: {ST}.play.vh, note: $('rpNote').textContent, ring: {ST}.ring }})")
        check('Replay opens the sheet: "Your best moment", Share / Save, the caption "Boss down!" + "Endless · 1,234"', not o['hidden'] and o['title'] == 'Your best moment' and o['share'] == 'Share' and o['save'] == 'Save' and o['cap']['kind'] == 'Boss down!' and o['cap']['line'] == 'Endless · ‎1,234', o)
        check('the video canvas: the clip x2 (680x424), even; the ring\'s memory released while it plays', [o['vw'], o['vh']] == [680, 424] and o['ring'] == 0, [o['vw'], o['vh'], o['ring']])
        check('while the video is made: "Making the video…", Share / Save wait', o['note'] == 'Making the video…' and await page.evaluate("$('rpShare').disabled"), o['note'])
        await page.mouse.move(100, 100); await page.mouse.move(1100, 700); await page.mouse.move(200, 600)
        await play_checks(page, 'desktop EN', shot='tests/out/replay_modal_slowmo_en.png')
        check('the sheet is up: the card waits (a fast mouse does not restart the round)', await page.evaluate(f"{S}.over && {ST}.open"))
        await video_checks(page, 'desktop EN')
        await page.screenshot(path='tests/out/replay_modal_en.png')
        # Share: the share sheet with the file and the challenge line
        await page.evaluate("stubShare(true, false)"); await page.click('#rpShare')
        await page.wait_for_function("__shared.length === 1", timeout=5000)
        sd = await page.evaluate("__shared[0]"); ext = (await page.evaluate(f"{ST}.video.ext"))
        check('Share (canShare says yes): navigator.share with the video file, the title and the Challenge-a-friend line + link', sd['title'] == 'Grasp' and sd['files'][0][0] == 'grasp-replay.' + ext and sd['files'][0][1].startswith('video/') and sd['files'][0][2] > 1000 and sd['text'].startswith('I scored 1234 on Grasp Endless') and '/duel?m=end' in sd['text'] and 'score=1234' in sd['text'], sd)
        await page.evaluate("stubShare(true, true)"); ab = await page.evaluate(f"{R}.share(false)")
        check('a cancelled share sheet: nothing else happens (no download)', ab == 'aborted', ab)
        await page.evaluate("stubShare(false, false)")
        async with page.expect_download(timeout=8000) as dl: await page.click('#rpShare')
        d1 = await dl.value; await page.wait_for_function("__clip.length >= 1", timeout=4000)
        sh = await page.evaluate(f"({{ last: {ST}.lastShare, clip: __clip.slice(), toasts: __grasp.toasts.map(t => t.text) }})")
        check('no file sharing here (canShare says no): the video downloads ("grasp-replay.*"), the challenge line goes to the clipboard, "Replay saved!"', d1.suggested_filename == 'grasp-replay.' + ext and sh['last'] == 'downloaded' and '/duel?m=end' in sh['clip'][-1] and 'Replay saved!' in sh['toasts'], [d1.suggested_filename, sh])
        await page.evaluate("stubShare(true, false); __shared.length = 0")
        async with page.expect_download(timeout=8000) as dl2: await page.click('#rpSave')
        d2 = await dl2.value
        check('Save always downloads (even where sharing works)', d2.suggested_filename == 'grasp-replay.' + ext and await page.evaluate("__shared.length") == 0, d2.suggested_filename)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
        es = await page.evaluate(f"({{ open: {ST}.open, hidden: $('replay').hidden, over: {S}.over, menu: menu.open, rec: {ST}.recording }})")
        check('Escape closes the sheet (not the pause menu); the card stays', not es['open'] and es['hidden'] and es['over'] and not es['menu'] and not es['rec'], es)
        await page.wait_for_timeout(700)
        await tap_pill(page, S, False); await page.wait_for_timeout(300)
        check('reopened: the same clip, the video kept (no second recording)', await page.evaluate(f"{ST}.video && !{ST}.recording && !$('rpShare').disabled"))
        await page.click('#rpClose'); await page.wait_for_timeout(200)
        check('the X closes it', await page.evaluate(f"!{ST}.open && $('replay').hidden && {S}.over"))
        await page.evaluate("endCardAction('again', performance.now())"); await page.wait_for_function(f"!{S}.over", timeout=5000)
        nr = await page.evaluate(f"({{ clip: {ST}.clip, pend: {ST}.pend, count: {ST}.count, rec: {ST}.record }})")
        check('Play again: a fresh round, no clip yet (each round its own best moment)', nr['clip'] is None and nr['pend'] is None and nr['count'] <= 3 and not nr['rec'], nr)
        check('R3: no page errors', not errs, errs); await ctx.close()

        # ===== R4: Adventure on a phone: the stage clear (a record) and the fail card; EN =====
        ctx, page, errs = await fresh(b, mobile=True, init=STUB)
        await stage(page, 3); await page.evaluate(f"{R}.rp.noGate = true; park(); {S}.noTiming = true; profile.adv.best[3] = 5; saveProfile()")
        await caps(page, 70)
        sb = await page.evaluate("blast('super', 1, 3)"); await page.evaluate(f"{S}.score = 900")
        await page.wait_for_timeout(600)
        await page.evaluate(f"{A}.finishTest(0)")
        q = await pill(page, S); pill_ok('Adventure stage clear (phone)', q)
        cl = await page.evaluate(f"({{ clip: {ST}.clip, log: {ST}.log.map(m => [m.kind, m.score]), rec: {ST}.record, res: {A}.result && {A}.result.record }})")
        check('the SUPER blast (67) was a moment, but a stage clear with a NEW RECORD (50 + 40) beats it: the clip is the last wall going, the record noted', ['super', 67] in cl['log'] and ['clear', 90] in cl['log'] and cl['clip']['kind'] == 'clear' and cl['rec'] and cl['res'], {k: cl[k] for k in ('log', 'rec', 'res')})
        await page.screenshot(path='tests/out/replay_adv_clear_phone_en.png')
        await tap_pill(page, S, True)
        cap = await page.evaluate(f"{ST}.play.cap")
        check('the caption: "Stage clear!", "NEW RECORD!", "Stage 3 · 900"', cap['kind'] == 'Stage clear!' and cap['record'] == 'NEW RECORD!' and cap['line'] == 'Stage 3 · ‎900', cap)
        await play_checks(page, 'phone EN', shot='tests/out/replay_modal_phone_en.png')
        v = await video_checks(page, 'phone EN')
        sz = await page.evaluate(f"[{ST}.play.vw, {ST}.play.vh, $('rpCanvas').getBoundingClientRect().toJSON(), $('replay').querySelector('.sheet').getBoundingClientRect().toJSON()]")
        check('phone: the video is 352x720 (portrait), the sheet fits the screen', sz[0:2] == [352, 720] and sz[3]['top'] >= 0 and sz[3]['bottom'] <= 740 and sz[2]['width'] > 150, sz)
        await page.evaluate("stubShare(true, false)"); await page.tap('#rpShare'); await page.wait_for_function("__shared.length === 1", timeout=5000)
        sd = await page.evaluate("__shared[0]")
        check('Share from a stage card: the stage challenge line + link', sd['text'].startswith('I scored 900 on Grasp stage 3') and '/duel?m=adv&s=3' in sd['text'] and sd['files'][0][2] > 1000, sd)
        await page.tap('#rpClose'); await page.wait_for_timeout(300)
        # the fail card
        await page.evaluate("endCardAction('retry', performance.now())")
        await page.wait_for_function(f"{A}.on && {A}.phase === 'play' && !{S}.over", timeout=8000)
        await page.evaluate(f"{R}.rp.noGate = true; park(); {S}.noTiming = true"); await caps(page, 50)
        await page.evaluate("blast('hard', 1, 3)"); hb = await page.evaluate(f"{ST}.pend")
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(100, 180, 420); strikeMiss(s.ball, performance.now()); }})()")
        q = await pill(page, S); pill_ok('Adventure fail card (phone)', q)
        check('the fail card: the round\'s best (a hard blast) cut at once when the round ends', hb and (await page.evaluate(f"{ST}.clip.kind")) in ('blast', 'wall'), hb)
        await page.screenshot(path='tests/out/replay_adv_fail_phone_en.png')
        check('R4: no page errors', not errs, errs); await ctx.close()

        # ===== R5: the boss victory card (world 1, desktop) =====
        ctx, page, errs = await fresh(b, init=STUB)
        await page.evaluate("profile.adv.unlocked = 40; saveProfile(); setInputPref('mouse'); openAdvMap({ how: 'mouse' })"); await page.click('.anode[data-n="8"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 8 && {A}.phase === 'play' && __grasp.boss.b && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"{S}.noRally = true; {S}.noTiming = true; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0; __grasp.boss.enter(); __grasp.boss.calm(true); park(); __grasp.boss.weak(false); {R}.rp.noGate = true")
        await caps(page, 70)
        await page.evaluate("(() => { const b = __grasp.boss.b, s = __grasp.boss.state(); b.hp = 3; __grasp.boss.ball('super', s.x, s.y + s.hh * 0.45); park(); })()")
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card'", timeout=15000)
        q = await pill(page, S); pill_ok('boss victory card', q)
        c = await page.evaluate(f"{ST}.clip")
        check('the boss victory: the clip is the boss going down (120), cut 1.5 s after it', c['kind'] == 'boss' and c['score'] == 120 and c['t1'] >= 1300, {k: c[k] for k in ('kind', 'score', 't0', 't1', 'frames')})
        await page.screenshot(path='tests/out/replay_boss_card_en.png')
        await tap_pill(page, S, False)
        await page.wait_for_function(f"{ST}.play && {ST}.play.tc > -100 && {ST}.play.tc < 300", timeout=12000, polling=16)
        await page.screenshot(path='tests/out/replay_boss_modal_en.png')
        check('its caption: "Boss down!" + "Stage 8 · ..."', (await page.evaluate(f"{ST}.play.cap.kind")) == 'Boss down!' and (await page.evaluate(f"{ST}.play.cap.line")).startswith('Stage 8 · '))
        await page.keyboard.press('Escape')
        check('R5: no page errors', not errs, errs); await ctx.close()

        # ===== R6: Frenzy on a phone in Hebrew: a speed step is the moment; the card, the sheet, the share line =====
        ctx, page, errs = await fresh(b, mobile=True, he=True, init=STUB)
        await page.evaluate("__grasp.setPlayerLevel(12); profile.frenzy = { best: 3, top: 1.2, runs: 1 }; saveProfile(); setInputPref('mouse')")
        await page.evaluate(f"{F}.start('mouse')"); await page.wait_for_function(f"{F}.on && {S}.walls.length === 4 && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"{R}.rp.noGate = true; {S}.noTiming = true; park()"); await caps(page, 70)
        fz = await page.evaluate(f"(() => {{ const s = {S}; s.hits = 20; let n = 0; while (!{ST}.pend && n < 20) {{ rallyUp(performance.now()); n++; }} return {{ pend: {ST}.pend, n }}; }})()")
        check('Frenzy: a speed step ("x1.2 SPEED") is a moment (25 + hits)', fz['pend'] and fz['pend']['kind'] == 'frenzy' and fz['pend']['score'] == 45 and fz['pend']['n'] == 20, fz)
        await page.wait_for_timeout(1700)
        await page.evaluate(f"(() => {{ const s = {S}; s.hits = 20; s.shield = 0; s.lives = 1; s.setBallZ(100, 180, 420); strikeMiss(s.ball, performance.now()); }})()")
        q = await pill(page, S); pill_ok('Frenzy card (phone HE)', q)
        check('Hebrew: the pill says "הילוך חוזר"', q['p']['label'] == 'הילוך חוזר', q['p'])
        await page.screenshot(path='tests/out/replay_frenzy_card_he.png')
        await tap_pill(page, S, True)
        he = await page.evaluate(f"({{ title: $('rpTitle').textContent, share: $('rpShare').innerText.trim(), save: $('rpSave').innerText.trim(), cap: {ST}.play.cap, dir: document.documentElement.dir }})")
        check('the sheet in Hebrew: "הרגע הכי טוב שלכם", שיתוף / שמירה, "20 ברצף!", "טירוף · 20 ברצף", "שיא חדש!" (a Frenzy record)',
              he['title'] == 'הרגע הכי טוב שלכם' and he['share'] == 'שיתוף' and he['save'] == 'שמירה' and he['cap']['kind'] == '20 ברצף!' and he['cap']['line'] == 'טירוף · 20 ברצף' and he['cap']['record'] == 'שיא חדש!' and he['dir'] == 'rtl', he)
        await play_checks(page, 'phone HE', shot='tests/out/replay_modal_he.png')
        await video_checks(page, 'phone HE')
        await page.evaluate("stubShare(true, false)"); await page.tap('#rpShare'); await page.wait_for_function("__shared.length === 1", timeout=5000)
        sd = await page.evaluate("__shared[0]")
        check('Share from the Frenzy card (HE): the Hebrew challenge line + the /duel?m=frz link', 'ברצף בטירוף של Grasp' in sd['text'] and '/duel?m=frz' in sd['text'], sd['text'])
        await page.tap('#rpClose')
        check('R6: no page errors', not errs, errs); await ctx.close()

        # ===== R7: Smash (phone EN): a big collapse, then the boss (the best); the stage card =====
        ctx, page, errs = await fresh(b, mobile=True, init=STUB)
        await page.evaluate("profile.smash.unlocked = 20; saveProfile(); setInputPref('mouse')")
        await page.evaluate(f"{SMK}.stage(1)"); await page.wait_for_function(f"{SMH}.n === 1 && {SMH}.phase === 'play' && !{SMH}.over && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"{R}.rp.noGate = true; {SMH}.banner = null"); await caps(page, 60)
        for f in (0.3, 0.45, 0.6, 0.75):  # real swipes across the wall (twice: bricks crack first)
            for _ in range(2): await page.evaluate(f"{SMK}.sweep(innerWidth * 0.05, innerHeight * {f}, innerWidth * 0.95, innerHeight * {f + 0.03}, 0.9)")
        await page.wait_for_timeout(200)
        co = await page.evaluate(f"{ST}.log.filter(m => m.kind === 'collapse').pop()")
        check('Smash: many things breaking at once is a "big collapse" moment (20 + 3 per thing, <= 100)', co and co['n'] >= 6 and co['score'] == min(100, 20 + 3 * co['n']), co)
        await page.wait_for_timeout(1700); await caps(page, 30)
        await page.evaluate(f"{SMK}.win()")
        await page.wait_for_function(f"{SMH}.over && {SMH}.result", timeout=15000)
        q = await pill(page, SMH); pill_ok('Smash stage card (phone)', q)
        c = await page.evaluate(f"{ST}.clip")
        check('the boss down (110) beats the collapse: the clip', c['kind'] == 'boss' and c['score'] == 110, c and {k: c[k] for k in ('kind', 'score', 'frames')})
        await page.screenshot(path='tests/out/replay_smash_card_en.png')
        await tap_pill(page, SMH, True)
        cap = await page.evaluate(f"{ST}.play.cap")
        check('the caption: "Boss down!", "Smash · Stage 1"', cap['kind'] == 'Boss down!' and cap['line'] == 'Smash · Stage 1', cap)
        await play_checks(page, 'Smash', shot='tests/out/replay_smash_modal_en.png')
        await page.evaluate("stubShare(true, false)"); await video_checks(page, 'Smash'); await page.tap('#rpShare'); await page.wait_for_function("__shared.length === 1", timeout=5000)
        check('Share from Smash: the plain line (no challenge link)', (await page.evaluate("__shared[0].text")) == 'My best moment in Grasp! 💥')
        await page.tap('#rpClose')
        check('R7: no page errors', not errs, errs); await ctx.close()

        # ===== R8: Slice (desktop HE): a combo; the round-over card =====
        ctx, page, errs = await fresh(b, he=True, init=STUB + DROP)
        await page.click('.modes button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"{R}.rp.noGate = true"); await caps(page, 70)
        await page.evaluate("(() => { const c = __grasp.slice.combo; c.n = 3; c.t = performance.now(); })()"); await page.wait_for_timeout(100)
        await page.evaluate("(() => { const c = __grasp.slice.combo; c.n = 5; c.t = performance.now(); })()"); await page.wait_for_timeout(100)
        sc = await page.evaluate(f"({{ log: {ST}.log.filter(m => m.kind === 'combo'), pend: {ST}.pend }})")
        check('Slice: a combo is a moment (15 + 8 x n); x5 beats x3', [m['score'] for m in sc['log']] == [39, 55] and sc['pend']['n'] == 5, sc)
        await page.wait_for_timeout(1700)
        for _ in range(3): await page.evaluate("dropFruit()"); await page.wait_for_timeout(150)
        q = await pill(page, "__grasp.slice"); pill_ok('Slice round-over card (HE)', q)
        await page.screenshot(path='tests/out/replay_slice_card_he.png')
        await tap_pill(page, "__grasp.slice", False)
        cap = await page.evaluate(f"{ST}.play.cap")
        check('the caption in Hebrew: "קומבו ×5!", "חיתוך · ..."', cap['kind'] == 'קומבו ×5!' and cap['line'].startswith('חיתוך · '), cap)
        await page.wait_for_function(f"{ST}.play && {ST}.play.tc > -100 && {ST}.play.tc < 300", timeout=12000, polling=16)
        await page.screenshot(path='tests/out/replay_slice_modal_he.png')
        await page.keyboard.press('Escape')
        check('R8: no page errors', not errs, errs); await ctx.close()

        # ===== R9: no MediaRecorder: a still PNG of the peak; no createImageBitmap: the feature is off, the game unchanged =====
        ctx, page, errs = await fresh(b, init=STUB + "try { delete window.MediaRecorder; window.MediaRecorder = undefined; } catch (e) {}")
        await endless(page); await page.evaluate(f"{R}.rp.noGate = true")
        check('no MediaRecorder: capture still on, recording off', await page.evaluate(f"{ST}.ok && !{ST}.recOk"))
        await caps(page, 70); await page.evaluate("blast('super', 2, 2)"); await clip_of(page, 'super')
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await pill(page, S); await tap_pill(page, S, False)
        await page.wait_for_function(f"{ST}.still", timeout=8000)
        st = await page.evaluate(f"({{ still: {ST}.still, video: {ST}.video, note: $('rpNote').textContent, dis: $('rpShare').disabled }})")
        check('a still PNG of the peak frame instead (Share / Save on, a note says so)', st['still']['type'] == 'image/png' and st['still']['size'] > 1000 and st['video'] is None and not st['dis'] and 'picture' in st['note'], st)
        await page.evaluate("stubShare(true, false)"); await page.click('#rpShare'); await page.wait_for_function("__shared.length === 1", timeout=5000)
        check('Share hands over "grasp-replay.png"', (await page.evaluate("__shared[0].files[0]"))[:2] == ['grasp-replay.png', 'image/png'])
        await page.keyboard.press('Escape')
        check('R9a: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init=STUB + "window.createImageBitmap = undefined;")
        await endless(page); await page.wait_for_timeout(1500); await page.evaluate("blast('super', 2, 2)"); await page.wait_for_timeout(1800)
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(100, 640, 420); strikeMiss(s.ball, performance.now()); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons", timeout=6000); await page.wait_for_timeout(1200)
        off = await page.evaluate(f"({{ ok: {ST}.ok, caps: {ST}.caps, clip: {ST}.clip, pill: {S}.ui.rpBtn, btn: Object.keys({S}.ui.buttons) }})")
        check('no createImageBitmap: the feature is silently off (nothing captured, no pill), the card as before', not off['ok'] and off['caps'] == 0 and off['clip'] is None and off['pill'] is None and 'again' in off['btn'], off)
        check('R9b: no page errors', not errs, errs); await ctx.close()

        # ===== R10: the 3D renderer: the capture reads the WebGL corridor under the overlay =====
        ctx, page, errs = await fresh(b, mobile=True, init=STUB, gfx="{ pr: 0.12, shadows: false, auto: false }")
        await endless(page)
        if await page.evaluate("gfx3dActive()"):
            await page.evaluate(f"{R}.rp.noGate = true"); await caps(page, 40)
            px = await page.evaluate(f"""(() => {{ const r = {R}.rp, N = {R}.n(), s = r.ring[(r.head - 1 + N) % N], d = s.g.getImageData(0, 0, s.c.width, s.c.height).data; let sum = 0, lit = 0;
              for (let i = 0; i < d.length; i += 4) {{ const v = d[i] + d[i + 1] + d[i + 2]; sum += v; if (v > 120) lit++; }} return {{ mean: sum / (d.length / 4) / 3, lit: lit / (d.length / 4), cost: {ST}.cost }}; }})()""")
            print('capture cost (phone 3D, SwiftShader, JS time per capture, ms):', px['cost'], flush=True)
            check('3D: the captured frame has the WebGL corridor in it (not a black / empty overlay)', px['mean'] > 12 and px['lit'] > 0.02, px)
            await page.evaluate("blast('super', 1, 3)"); await clip_of(page, 'super', 15000)
            await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(100, 180, 420); strikeMiss(s.ball, performance.now()); }})()")
            await pill(page, S); await tap_pill(page, S, True)
            await page.wait_for_function(f"{ST}.play && {ST}.play.tc > -100 && {ST}.play.tc < 300", timeout=12000, polling=16)
            await page.screenshot(path='tests/out/replay_modal_3d.png'); await page.tap('#rpClose')
        else: print('(3D renderer not ready here: skipped)')
        check('R10: no page errors', not errs, errs); await ctx.close()
        await b.close()
    srv.terminate()
    print('FAILURES:', check.fails)
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
