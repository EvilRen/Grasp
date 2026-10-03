exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Step 4: Grippy, now a cheering VOICE (no hand, no bubble): short lines (1-3 words) spoken with speechSynthesis in the UI language at the big moments
# only (start, last heart, boss, new best, stage clear / fail, world, level up, a rare close save), an 8 s cooldown, music ducked while he talks,
# muted / off / no speech / no voice for the language = silence; onboarding tips as a one-time hint toast. speechSynthesis is stubbed (window.__spoken).
# Also: the end card's "One more?" teaser (nearest goal for crafted profiles) and its pulsing Play again, and toasts that never cover a round-over card.
# Timing-independent: rounds end by parking the ball behind the player (or dropping fruit / calling the life loss) and polling for the state.
G = "__grasp.grippy"; S = "__grasp.strike"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
DATE = '2026-10-02'
# the speech stub: records every utterance (text, lang, voice lang); voices: 'both' (EN + HE), 'en' (EN only), 'none' (no speechSynthesis at all)
def speech(voices='both'):
    if voices == 'none': return "try { delete window.speechSynthesis; Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: undefined }); } catch (e) {} window.__spoken = [];"
    vs = "[{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]" if voices == 'both' else "[{ lang: 'en-GB', name: 'E' }]"
    return ("window.__spoken = []; window.__cancels = 0; try { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang, rate: u.rate, t: performance.now() }); setTimeout(() => { try { u.onend && u.onend(); } catch (e) {} }, 600); }, cancel() { __cancels++; }, getVoices() { return " + vs + "; } };"
            " Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ss }); } catch (e) { window.__speechStubFailed = String(e); }")
ALL_CHEAP = ['ball_beach', 'ball_soccer', 'hand_mint', 'hand_sky', 'hand_lilac', 'hand_robot', 'blade_neon', 'blade_rainbow', 'trail_sparkle', 'trail_fire']

def prof(coins=0, xp=0, unlocked=(), missions=None):
    p = {'v': 1, 'xpv': 2, 'coins': coins, 'xp': xp, 'unlocked': list(unlocked)}
    if missions is not None: p['missions'] = {'date': DATE, 'list': [dict(id=i, progress=pr, goal=g, reward=20, done=False, claimed=False) for i, pr, g in missions]}
    return "localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(p)) + ");"

async def fresh(b, mobile=False, he=False, init='', voices='both'):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "'); sessionStorage.setItem('grasp.testDate','" + DATE + "');" + speech(voices) + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs
async def play(page, m, mobile=False):
    await page.evaluate("__grasp.setGameMode('" + m + "')")
    if mobile: await page.evaluate(START_MOUSE)
    else: await page.evaluate(START_MOUSE)
    await page.wait_for_function("mode === 'mouse'", timeout=8000); await page.evaluate(SFX_JS)
async def end_strike(page, score=0, lives=1):
    await page.evaluate(f"(() => {{ const s = {S}; s.score = {score}; s.lives = {lives}; s.setBallZ(-500); }})()")
    await page.wait_for_function(f"{S}.over && {S}.ui.card && performance.now() - {S}.overAt > 450", timeout=8000)
async def end_slice(page, score=0):
    await page.evaluate(f"(() => {{ const s = __grasp.slice; s.score = {score}; s.nextSpawn = 1e12; s.fruits.length = 0; s.lives = 1; sliceLoseLife(performance.now()); }})()")
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.card && performance.now() - __grasp.slice.overAt > 450", timeout=8000)
def inter(a, b):  # overlap area of two {x, y, w, h} boxes
    return max(0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x'])) * max(0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))

# samples every frame until no toast is left: each visible toast's rect against the end card's, the toolbar's, and how many show at once
SAMPLER = """(E => new Promise((done) => { const out = { n: 0, maxOver: 0, maxBar: 0, maxAtOnce: 0, texts: new Set(), oneLine: true, inside: true, frames: 0 }, t0 = performance.now();
  const bar = document.querySelector('.chrome').getBoundingClientRect();
  (function smp() { const c = E().ui.card, live = [...document.querySelectorAll('#metaToast .mt')].filter(e => !e.classList.contains('wait') && e.getBoundingClientRect().height > 0);
    out.frames++; out.maxAtOnce = Math.max(out.maxAtOnce, live.length);
    for (const e of live) { const r = e.getBoundingClientRect(), ov = (a, b) => Math.max(0, Math.min(a.right, b.x + b.w) - Math.max(a.left, b.x)) * Math.max(0, Math.min(a.bottom, b.y + b.h) - Math.max(a.top, b.y));
      out.texts.add(e.querySelector('.tx').textContent); out.maxOver = Math.max(out.maxOver, ov(r, c)); out.maxBar = Math.max(out.maxBar, ov(r, { x: bar.left, y: bar.top, w: bar.width, h: bar.height }));
      if (r.height > 40) out.oneLine = false; if (r.left < 0 || r.right > innerWidth || r.top < 0) out.inside = false; out.card = c; out.last = { x: r.left, y: r.top, w: r.width, h: r.height }; }
    if (!document.querySelector('#metaToast .mt') || performance.now() - t0 > 20000) { out.texts = [...out.texts]; done(out); } else requestAnimationFrame(smp); })(); }))"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])

        # ---- the lines: only the big moments, 1-3 words, EN and HE ----
        ctx, page, errs = await fresh(b)
        ln = await page.evaluate(G + ".lines")
        evs = await page.evaluate(G + ".events")
        need = ['start', 'lastLife', 'boss', 'bossDown', 'newBest', 'levelUp', 'world', 'close', 'advClear', 'advPerfect', 'advFail', 'shapesLevel']
        quiet = ['firstHit', 'combo', 'streak5', 'streak10', 'super', 'pu_fire', 'pu_multi', 'miss', 'mission', 'final', 'cow', 'monkey', 'chest', 'unlock', 'shapesMatch', 'tip_serve', 'tip_pu']
        check('Grippy speaks at the big moments only: exactly ' + ', '.join(need), sorted(evs) == sorted(need) and sorted(ln['he']) == sorted(need), evs)
        bad = [e + ':' + l for e in need for l in ('en', 'he') if len(ln[l][e]) < 3 or len(set(ln[l][e])) != len(ln[l][e]) or any(not (1 <= len(x.split()) <= 3) or len(x) > 16 for x in ln[l][e])]
        check('>= 3 distinct, kid-short lines (1-3 words, <= 16 chars) per event in EN and HE', not bad, bad)
        heb = [e for e in need if not all(re.search('[\u0590-\u05ff]', x) for x in ln['he'][e])]
        check('HE lines are Hebrew', not heb, heb)
        check('the start screen: say() does nothing, nothing spoken', await page.evaluate(G + ".say('start')") is False and await page.evaluate("__spoken.length") == 0)
        check('no Grippy element anywhere (no hand, no bubble); visible / box() are false / null', not await page.evaluate("!!document.querySelector('#grippy, .nuGrip')") and not await page.evaluate(G + ".visible") and await page.evaluate(G + ".box()") is None)

        # ---- in a Strike round: spoken on round start (EN voice), quiet events, the cooldown, a rare close one ----
        await play(page, 'strike')
        await page.wait_for_function(G + ".last && " + G + ".last.event === 'start' && __spoken.length === 1", timeout=5000)
        st = await page.evaluate("({ last: __grasp.grippy.last, sp: __spoken[0], tips: __grasp.profile.tips.slice(), hint: $('hint').querySelector('.tx').textContent, how: hintText(), wait: __grasp.strike.balls.length > 0, flick: t('tipFlick') })")
        hint_ok = (st['tips'] == ['serve'] and st['hint'] == st['how']) if not st['wait'] else (st['tips'] == ['serve', 'flick'] and st['hint'] == st['flick'])  # (once the first ball waits, the one-time pull-back + flick tip replaces the start hint)
        check("round start (a fresh profile's first run): the start line spoken once in English (en-US); the serve tip is the start hint, marked seen (then the one-time flick tip once the ball waits)", st['sp']['text'] in ln['en']['start'] and st['sp']['lang'] == 'en-US' and st['last']['text'] == st['sp']['text'] and hint_ok, st)
        await page.wait_for_timeout(200); await page.screenshot(path='tests/out/voice_play_en.png')
        q = await page.evaluate("(evs => { const n0 = __spoken.length; const r = evs.map(e => { __grasp.grippy.cool(); return __grasp.grippy.say(e); }); return { r, n: __spoken.length - n0 }; })(" + json.dumps(quiet) + ")")
        check('every other event is quiet: say() false, nothing spoken (' + ', '.join(quiet) + ')', not any(q['r']) and q['n'] == 0, q)
        await page.evaluate(S + ".extrasOff = true; " + S + ".ball = null; " + S + ".balls.length = 0")
        cd = await page.evaluate("""(() => { const g = __grasp.grippy, r = {}, now = performance.now(), n0 = __spoken.length; g.cool();
          r.boss = grippySay('boss', null, now); r.duck = g.ducking && musicDucked(performance.now()); r.best = grippySay('newBest', null, now + 100); r.last = grippySay('lastLife', null, now + 7900);
          r.later = grippySay('lastLife', null, now + 8100); r.n = __spoken.length - n0; r.texts = __spoken.slice(n0).map(x => x.text); r.why = g.skipped.slice(-2).map(x => x.why); r.gap = g.gapMs; return r; })()""")
        check('cooldown: one line per moment, >= 8 s between lines (boss spoken; a new best 0.1 s later and the last heart at 7.9 s held back; at 8.1 s it speaks)',
              cd['boss'] and not cd['best'] and not cd['last'] and cd['later'] and cd['n'] == 2 and cd['texts'][0] in ln['en']['boss'] and cd['texts'][1] in ln['en']['lastLife'] and cd['why'] == ['cooldown', 'cooldown'] and cd['gap'] == 8000, cd)
        check('while he talks the world music ducks', cd['duck'], cd)
        await page.wait_for_function("!" + G + ".ducking", timeout=4000)
        check('the duck lifts when the line ends (the stub ends it after 0.6 s)', True)
        cl = await page.evaluate("""(() => { const g = __grasp.grippy, now = performance.now(); g.cool(); const a = grippySay('close', null, now), b = grippySay('close', null, now + 9000), c = grippySay('close', null, now + 46000); return { a, b, c, why: g.skipped[g.skipped.length - 1].why, gap: g.closeGapMs }; })()""")
        check('a close save is rare: at most once per 45 s', cl['a'] and not cl['b'] and cl['c'] and cl['why'] == 'rare' and cl['gap'] == 45000, cl)
        seq = await page.evaluate("(() => { const out = []; for (let i = 0; i < 30; i++) { __grasp.grippy.cool(); __grasp.grippy.say('start'); out.push(__grasp.grippy.last.i); } return out; })()")
        check('no immediate repeat (30 start lines in a row), and the lines vary', all(a != b2 for a, b2 in zip(seq, seq[1:])) and len(set(seq)) >= 3, seq)
        # real triggers: a boss, a hit (quiet), a missed ball (quiet), the last heart, a new best
        real = await page.evaluate(f"""(() => {{ const s = {S}, g = __grasp.grippy, r = {{}}, n0 = __spoken.length;
          g.cool(); s.serve(); s.setBallZ(60, innerWidth / 2, innerHeight / 2); s.hits = 0; strikeHit(s.ball, performance.now()); r.hit = __spoken.length - n0;
          g.cool(); s.ball = null; s.balls.length = 0; s.spawnBoss(); r.boss = g.last.event; r.bossText = __spoken[__spoken.length - 1].text; return r; }})()""")
        check('real triggers: a first hit is quiet; a boss is spoken', real['hit'] == 0 and real['boss'] == 'boss' and real['bossText'] in ln['en']['boss'], real)
        await page.evaluate(G + ".cool(); " + S + ".boss = null; " + S + ".lives = 3; " + S + ".ball = null; " + S + ".serve(); " + S + ".setBallZ(-500)")
        await page.wait_for_function(S + ".lives === 2", timeout=6000); await page.wait_for_timeout(100)
        check('a missed ball with hearts left is quiet', await page.evaluate(G + ".last.event") == 'boss')
        await page.wait_for_function(S + ".balls.length > 0", timeout=6000)
        await page.evaluate(S + ".setBallZ(-500)")
        await page.wait_for_function(S + ".lives === 1 && " + G + ".last.event === 'lastLife'", timeout=6000)
        check('the next miss leaves one heart -> "Last heart!" spoken', await page.evaluate("__spoken[__spoken.length - 1].text") in ln['en']['lastLife'])
        await page.evaluate(S + ".best = 0; " + G + ".cool()")
        await page.wait_for_function(S + ".balls.length > 0", timeout=6000)
        await end_strike(page, 50)
        check('a new best at the end -> spoken', await page.evaluate(G + ".last.event") == 'newBest' and await page.evaluate(S + ".ui.newBest") and await page.evaluate("__spoken[__spoken.length - 1].text") in ln['en']['newBest'])
        # muted: silence (no speak call), and the cooldown is not used up
        await page.evaluate("__grasp.muted = true; " + G + ".cool()")
        mu = await page.evaluate("(() => { const n0 = __spoken.length; const ok = __grasp.grippy.say('boss'); return { ok, n: __spoken.length - n0, why: __grasp.grippy.skipped[__grasp.grippy.skipped.length - 1].why }; })()")
        check('muted: nothing spoken', not mu['ok'] and mu['n'] == 0 and mu['why'] == 'muted', mu)
        await page.evaluate("__grasp.muted = false")
        check('unmuted: he speaks again at once (mute did not start a cooldown)', await page.evaluate(G + ".say('boss')"))
        check('no page errors (desktop)', not errs, errs); await ctx.close()

        # ---- tips: a one-time hint toast instead of a bubble ----
        ctx, page, errs = await fresh(b)
        await play(page, 'strike'); await page.wait_for_function("__grasp.strike.waiting && __grasp.grippy.tips.length === 1", timeout=8000)  # (the first serve's one-time flick tip first)
        tp = await page.evaluate("(() => { const a = tipOnce('pu'), txt = $('hint').querySelector('.tx').textContent, show = $('hint').classList.contains('show'), b = tipOnce('pu'); return { a, b, txt, show, want: t('tipPu'), shown: __grasp.grippy.tips.map(x => x.id), seen: __grasp.profile.tips.slice() }; })()")
        check('onboarding tip (gold brick): shown once as the hint toast, never again; marked in profile.tips', tp['a'] and not tp['b'] and tp['show'] and tp['txt'] == tp['want'] and tp['shown'] == ['flick', 'pu'] and 'pu' in tp['seen'], tp)
        check('no page errors (tips)', not errs, errs); await ctx.close()

        # ---- no voice for the language / no speechSynthesis: silently skipped ----
        ctx, page, errs = await fresh(b, he=True, voices='en')
        await play(page, 'strike'); await page.wait_for_timeout(400)
        nv = await page.evaluate("(() => { __grasp.grippy.cool(); const ok = __grasp.grippy.say('boss'); return { ok, n: __spoken.length, why: __grasp.grippy.skipped.map(x => x.why) }; })()")
        check('HE UI with only an English voice installed: nothing spoken (no wrong-language voice), skipped quietly', not nv['ok'] and nv['n'] == 0 and 'nospeech' in nv['why'], nv)
        check('no page errors (no HE voice)', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, voices='none')
        await play(page, 'strike'); await page.wait_for_timeout(400)
        ns = await page.evaluate("(() => { __grasp.grippy.cool(); return { has: !!window.speechSynthesis, ok: __grasp.grippy.say('boss'), said: __grasp.grippy.said.length }; })()")
        check('no speechSynthesis at all: say() false, nothing recorded, no errors', not ns['has'] and not ns['ok'] and ns['said'] == 0 and not errs, [ns, errs]); await ctx.close()

        # ---- HE phone: Hebrew voice in Slice; the Voice toggle in the Collection header (persists), off = silence ----
        ctx, page, errs = await fresh(b, True, True)
        await play(page, 'slice', True)
        await page.wait_for_function(G + ".last && " + G + ".last.event === 'start' && __spoken.length === 1", timeout=5000)
        sp = await page.evaluate("__spoken[0]")
        check('HE: the start line is spoken in Hebrew (he-IL)', sp['text'] in ln['he']['start'] and sp['lang'] == 'he-IL', sp)
        await page.wait_for_timeout(300); await page.screenshot(path='tests/out/voice_play_he.png')
        check('HE phone in play: no Grippy hand / bubble on screen', not await page.evaluate("!!document.querySelector('#grippy, .nuGrip, .bub')"))
        await menu_click(page, '#homeBtn', tap=True); await page.wait_for_timeout(300)
        await page.tap('#collectionBtn'); await page.wait_for_timeout(400)
        tb = await page.evaluate("(() => { const b = $('grippyBtn'), r = b.getBoundingClientRect(), h = b.closest('header').getBoundingClientRect(), x = b.closest('header').querySelector('.xBtn').getBoundingClientRect(); return { pressed: b.getAttribute('aria-pressed'), label: b.getAttribute('aria-label'), canvas: !!b.querySelector('canvas'), svg: !!b.querySelector('svg'), inHeader: r.top >= h.top - 1 && r.bottom <= h.bottom + 1 && r.left >= 0 && r.right <= innerWidth, noOverlap: r.right <= x.left || r.left >= x.right, w: r.width }; })()")
        check('Collection header: the Voice toggle (a speaker icon, no hand), on by default, labelled, fits beside the close button', tb['pressed'] == 'true' and 'קול' in tb['label'] and tb['svg'] and not tb['canvas'] and tb['inHeader'] and tb['noOverlap'], tb)
        await page.screenshot(path='tests/out/voice_toggle_he.png')
        await page.tap('#grippyBtn'); await page.wait_for_timeout(150)
        check('tap: off (aria-pressed false), saved in the profile', await page.evaluate("$('grippyBtn').getAttribute('aria-pressed')") == 'false' and await page.evaluate("JSON.parse(localStorage.getItem('grasp.profile')).grippy") is False)
        await page.reload(); await page.wait_for_timeout(700)
        check('off survives a reload', await page.evaluate(G + ".on") is False and await page.evaluate("$('grippyBtn').getAttribute('aria-pressed')") == 'false')
        await play(page, 'strike', True)
        await page.wait_for_timeout(600)
        off = await page.evaluate("(() => { __grasp.grippy.cool(); return { say: __grasp.grippy.say('boss'), n: __spoken.length }; })()")
        check('off: nothing spoken on round start or say()', not off['say'] and off['n'] == 0, off)
        await page.evaluate(G + ".on = true; " + G + ".cool(); " + S + ".ball = null; " + S + ".balls.length = 0")
        check('back on: he speaks again (Hebrew)', await page.evaluate(G + ".say('boss')") and await page.evaluate("__spoken[__spoken.length - 1].lang") == 'he-IL')
        check('no page errors (HE / toggle)', not errs, errs); await ctx.close()

        # ---- Adventure: a stage cleared / failed is spoken (phone EN) ----
        ctx, page, errs = await fresh(b, True)
        await page.evaluate("__grasp.adventure.start(1, 'mouse')")
        await page.wait_for_function("__grasp.adventure.on && __grasp.adventure.phase === 'play' && __grasp.grippy.last && __grasp.grippy.last.event === 'start'", timeout=8000)
        await page.evaluate(G + ".cool(); __grasp.adventure.finishTest(0)")
        await page.wait_for_function("__grasp.strike.over && __grasp.adventure.phase === 'card' && __grasp.grippy.last.event === 'advPerfect'", timeout=10000)
        check('a perfect stage clear: "Three stars!"-style line spoken', await page.evaluate("__spoken[__spoken.length - 1].text") in ln['en']['advPerfect'])
        await page.evaluate("__grasp.adventure.start(2, 'mouse')")
        await page.wait_for_function("__grasp.adventure.on && __grasp.adventure.stage === 2 && __grasp.adventure.phase === 'play'", timeout=8000)
        await page.evaluate(G + ".cool(); __grasp.strike.lives = 1; __grasp.adventure.failTest()")  # (from 2 hearts the 'Last heart!' line would take this moment)
        await page.wait_for_function("__grasp.strike.over && __grasp.grippy.last.event === 'advFail'", timeout=10000)
        check('a failed stage: "So close!"-style line spoken', await page.evaluate("__spoken[__spoken.length - 1].text") in ln['en']['advFail'])
        check('no page errors (Adventure voice)', not errs, errs); await ctx.close()

        # ---- "One more?" teaser: the nearest goal for crafted profiles; Play again dominant and pulsing ----
        cases = [
            ('coins', prof(coins=963, unlocked=ALL_CHEAP, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), 'Only 37 coins to the Disco ball!', 'רק עוד 37 מטבעות לכדור דיסקו!'),
            ('xp', prof(xp=568, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), '12 XP to Level 4', 'עוד 12 XP לרמה 4'),
            ('mission', prof(missions=[('walls', 4, 6), ('fruit', 10, 40), ('boss', 0, 1)]), '2 more walls for the mission', 'עוד 2 קירות למשימה'),
            ('buy', prof(coins=1020, unlocked=ALL_CHEAP, missions=[('walls', 0, 6), ('fruit', 0, 40), ('boss', 0, 1)]), 'You can buy the Disco ball now!', 'יש לכם מספיק מטבעות לכדור דיסקו!'),
        ]
        for kind, init, en, hetext in cases:
            for he in ((False, True) if kind in ('coins', 'mission') else (False,)):
                tag = kind + ' ' + ('he' if he else 'en')
                ctx, page, errs = await fresh(b, he, he, init)
                await play(page, 'strike', he)
                await end_strike(page, 0)
                tz = await page.evaluate(S + ".ui.teaser")
                exp = hetext if he else en
                check('teaser (' + tag + '): "' + exp + '"', tz and tz['text'] == exp and tz['kind'] == kind and (tz['item'] == 'ball_disco') == (kind in ('coins', 'buy')), tz)
                c = await page.evaluate(S + ".ui.card"); bt = await page.evaluate(S + ".ui.buttons")
                check('teaser (' + tag + '): inside the card, under the stats, above the buttons', tz and tz['x'] >= c['x'] and tz['x'] + tz['w'] <= c['x'] + c['w'] and tz['y'] > c['y'] + 200 and tz['y'] + tz['h'] < bt['again']['y'], [tz, c])
                if kind == 'coins':
                    await page.wait_for_timeout(300); await page.screenshot(path='tests/out/grippy_teaser_' + ('he' if he else 'en') + '.png')
                    p1 = await page.evaluate(S + ".ui.againPulse")
                    await page.wait_for_function(f"Math.abs({S}.ui.againPulse - {p1}) > 0.01", timeout=4000)
                    check('Play again pulses (scale changes over time, within a few %), and is wider than Home', 1 <= p1 <= 1.04 and bt['again']['w'] > bt['home']['w'] * 1.2, [p1, bt])
                if kind == 'mission' and not he:  # the same profile from the API, and a Slice card shows it too
                    q = await page.evaluate("__grasp.teaser()")
                    check('__grasp.teaser(): the same pick (walls 4/6 beats fruit 10/40)', q['kind'] == 'mission' and q['id'] == 'walls' and q['n'] == 2, q)
                check('teaser (' + tag + '): no page errors', not errs, errs); await ctx.close()

        # ---- toasts at round end never touch the end card (phone EN / HE: Strike, Slice, the daily) ----
        for he in (False, True):
            for m in ('strike', 'slice', 'daily'):
                tag = 'phone ' + ('he' if he else 'en') + ' ' + m
                ctx, page, errs = await fresh(b, True, he, prof(coins=10, xp=175, missions=[('rounds', 2, 3), ('fruit', 0, 40), ('boss', 0, 1)]))
                if m == 'daily':
                    await page.evaluate("__grasp.setGameMode('strike')"); await page.tap('#dailyBtn'); await page.wait_for_timeout(300); await page.tap('#dailyMouse')
                    await page.wait_for_function("__grasp.daily.on && mode === 'mouse'", timeout=8000)
                else: await play(page, m, True)
                await page.wait_for_timeout(300)
                await page.evaluate("__grasp.toasts.length = 0")
                if m == 'slice': await end_slice(page, 60)
                else: await end_strike(page, 60)
                E = "() => " + ("__grasp.slice" if m == 'slice' else S)
                await page.wait_for_function("document.querySelector('#metaToast .mt:not(.wait)')", timeout=4000)
                await page.wait_for_timeout(150)
                await page.screenshot(path='tests/out/grippy_endcard_' + m + '_' + ('he' if he else 'en') + '.png')
                res = await page.evaluate(SAMPLER + "(" + E + ")")
                nt = len(await page.evaluate("__grasp.toasts"))
                want = 3 if m == 'daily' else 2  # level up + mission (+ the first daily's bonus)
                check(tag + ': ' + str(nt) + ' round-end toasts, all shown one at a time, one line each, inside the screen', nt >= want and len(res['texts']) >= want and res['maxAtOnce'] == 1 and res['oneLine'] and res['inside'], {k: res[k] for k in ('texts', 'maxAtOnce', 'oneLine', 'inside', 'frames', 'last')})
                check(tag + ': no toast pixel over the end card or the toolbar (every frame)', res['maxOver'] == 0 and res['maxBar'] == 0 and res['frames'] > 5, {k: res.get(k) for k in ('maxOver', 'maxBar', 'card', 'last')})
                check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- toasts away from an end card are unchanged: stacked at the top, 3 s ----
        ctx, page, errs = await fresh(b, True)
        await play(page, 'strike', True)
        await page.evaluate("toast('claimedToast', { c: 5 }, 'coin'); toast('claimedToast', { c: 6 }, 'coin')")
        n = await page.evaluate("[...document.querySelectorAll('#metaToast .mt')].filter(e => e.getBoundingClientRect().height > 0).length")
        check('mid-round: two toasts stack as before (not compact)', n == 2 and not await page.evaluate("__grasp.toastCompact"), n)
        check('no page errors (mid-round toasts)', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
