exec(open('tests/test_phase1.py').read().split('async def main')[0])
# Game feel (expert 7's quick wins):
#  1  no stage-5 cliff: world 1's walls stages all keep the aim help and 2 weak spots; the kid sim clears stage 5 in about a minute
#  2  the first-time finger goes when the round ends (never over an end card); while Slice's swipe demo is up a missed fruit costs no heart
#  3  the cards say less: no Best that repeats the score (or is 0), no '+0', no row of zeros, no 'Tap Next…' by touch, the stars line only under 3
#  4  Smash's stage banner is short (1.4 s: the clock runs under it); the run-power pick between stages is icon + name only
#  5  perf: the start screen idles: no frame() loop (a game / the home camera wake it), the dots move by transform, the audio suspends after 5 s of silence
#  6  toddlers: a tap on nothing in Sandbox, Busy Board, Shapes and Calm bubbles answers with the Little ones games' twinkle
SIM = open('tests/strike_sim.js').read() + "\n;0"
DRAWN = "(() => { window.__drawn = new Set(); for (const f of ['textSprite', 'bigTextSprite']) { const o = window[f]; window[f] = function (txt, ...a) { __drawn.add(String(txt)); return o.call(this, txt, ...a); }; } })()"
DROP = """window.dropFruit = () => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12; // a fruit already below the screen, still falling: a miss on the next tick
  f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); };"""
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])  # (the home camera check needs a camera)

        # ===== 1. the stage-5 cliff =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(7), 'unlocked': 8}))
        pl = await page.evaluate("[1, 2, 3, 4, 5, 6, 7, 8, 9, 16].map(n => { const P = advPlan(n); return [n, P.assist, P.weak]; })")
        check('1 world 1\'s walls stages 1-7: the aim help and 2 weak spots a wall; the boss stage 8 and world 2+ without', pl == [[n, True, 2] for n in range(1, 8)] + [[8, False, 1], [9, False, 1], [16, False, 1]], pl)
        await page.evaluate(SIM)
        ts = []
        for seed in (1, 2):
            await page.evaluate(f"{A}.start(5, 'mouse')"); await page.wait_for_function("adv.on && adv.n === 5 && adv.phase === 'play'", timeout=10000); await page.wait_for_timeout(200)
            ts.append(await page.evaluate(f"advSim({{ player: 'kid', seed: {seed}, maxS: 200 }}).t")); await page.evaluate("goHome()"); await page.wait_for_timeout(200)
        check('1 the kid sim clears stage 5 in about a minute (was 100-200 s)', all(t is not None and t <= 75 for t in ts), ts)
        check('1 no page errors', not errs, errs); await ctx.close()

        # ===== 2. the finger demo ends with the round; Slice's first lesson is free =====
        ctx, page, errs = await fresh(b, init="window.__graspFd = true;" + DROP)
        await page.tap('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && fd.ui && fd.ui.id === 'slice' && fdActive('slice')", timeout=10000)
        l0 = await page.evaluate("slice.lives")
        for _ in range(3): await page.evaluate("dropFruit()"); await page.wait_for_timeout(150)
        s1 = await page.evaluate("({ lives: slice.lives, missed: slice.missed, over: slice.over, fd: fdActive('slice') })")
        check('2 Slice\'s first round: while the swipe demo is up, missed fruit cost no heart (counted as missed)', s1['lives'] == l0 and s1['missed'] >= 3 and not s1['over'] and s1['fd'], [l0, s1])
        await page.evaluate("slice.lives = 1; sliceLoseLife(performance.now())"); await page.evaluate(FRAMES)
        s2 = await page.evaluate("({ over: slice.over, on: fd.on, ui: fd.ui, log: fd.log.slice(), tip: profile.tips.includes('fd_slice') })")
        check('2 the round ends (a bomb): the finger and its words go at once, not over the card; not marked learnt', s2['over'] and s2['on'] is None and s2['ui'] is None and 'over:slice' in s2['log'] and not s2['tip'], s2)
        await page.wait_for_function("slice.ui.buttons && performance.now() - slice.overAt > 700", timeout=5000); await page.evaluate(FRAMES)
        check('2 ...and it stays gone while the card is up', await page.evaluate("fd.on === null && fd.ui === null"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(400)
        await page.evaluate("profile.tips = profile.tips.concat(['fd_slice']); slice.score = 0")  # (Slice learnt: a miss costs a heart again)
        await page.evaluate("setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse' && !slice.over", timeout=8000)
        l1 = await page.evaluate("slice.lives"); await page.evaluate("dropFruit()"); await page.wait_for_timeout(200)
        check('2 once the swipe is learnt, a missed fruit costs a heart', await page.evaluate("slice.lives") == l1 - 1, l1)
        await page.evaluate("goHome()"); await page.wait_for_timeout(400)
        await page.evaluate("setGameMode('smash'); smashStageStart(1, 'mouse')"); await page.wait_for_function("smash.banner", timeout=12000)
        await page.evaluate("window.__bt = smash.banner.t; (function w() { if (smash.banner) requestAnimationFrame(w); else window.__bgone = performance.now(); })()")
        await page.wait_for_function("gameMode === 'smash' && fd.ui && fd.ui.id === 'smash' && !smash.banner && window.__bgone", timeout=12000)
        bt = await page.evaluate("__bgone - __bt")
        check('4 Smash\'s stage banner is short (1.4 s, was 2.6 s), then the finger', await page.evaluate("SMASH_BANNER_MS") == 1400 and 1300 < bt < 1800, round(bt))
        await page.evaluate("smash.endAt = performance.now() + 200"); await page.wait_for_function("smash.over", timeout=5000); await page.evaluate(FRAMES)
        check('2 Smash: the clock runs out with no tap: the finger goes with the round', await page.evaluate("fd.on === null && fd.ui === null && fd.log.includes('over:smash')"))
        check('2 no page errors', not errs, errs); await ctx.close()

        # ===== 3. the cards say less =====
        for he in (False, True):
            tg = 'HE' if he else 'EN'
            ctx, page, errs = await fresh(b, he=he, init=DROP + prof(adv={'stars': {}, 'unlocked': 8}))
            await stage_card(page, 4, 0, score=300); await page.wait_for_timeout(1700)
            c = await page.evaluate("({ chip: strike.ui.advBestChip, rec: adv.result.record, hint: strike.ui.advStarHint, line: strike.ui.againLine, stars: adv.result.stars })")
            check(tg + ': a 3-star first clear: no "Best" under the score, no stars line, no "Tap Next…" by touch', c['stars'] == 3 and c['chip'] is None and c['hint']['hidden'] and c['hint']['a'] == 0 and c['line'] is None, c)
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
            await stage_card(page, 4, 1, score=100); await page.wait_for_timeout(1700)
            c = await page.evaluate("({ chip: strike.ui.advBestChip, hint: strike.ui.advStarHint, stars: adv.result.stars, best: adv.result.bestScore })")
            check(tg + ': a lower 2-star replay: the best chip (300) and the line on how to get 3', c['stars'] == 2 and c['chip'] and '300' in c['chip']['text'] and not c['hint']['hidden'] and c['hint']['a'] > 0.9, c)
            await page.screenshot(path='tests/out/feel_adv_card_%s.png' % ('he' if he else 'en'))
            await page.evaluate("goHome()"); await page.wait_for_timeout(300)
            await page.evaluate("localStorage.removeItem('sliceBest'); setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000)
            for _ in range(3): await page.evaluate("dropFruit()"); await page.wait_for_timeout(150)
            await page.wait_for_function("slice.over && slice.ui.buttons && performance.now() - slice.overAt > 1200", timeout=5000)
            s = await page.evaluate("({ score: slice.score, chip: slice.ui.bestChip, line: slice.ui.bestLine, coin: slice.ui.coinBox, rc: meta.roundCoins, zeros: slice.ui.statsHidden, again: slice.ui.againLine, keys: Object.keys(slice.ui.buttons) })")
            check(tg + ': a Slice round of 0: no "Best 0", no "+0", no row of zeros, no "Tap Play again"; the buttons unchanged', s['score'] == 0 and s['chip'] is None and s['line'] is None and (s['coin'] is None) == (s['rc'] == 0) and s['zeros'] and s['again'] is None and 'again' in s['keys'] and 'home' in s['keys'], s)
            await page.screenshot(path='tests/out/feel_slice_card_%s.png' % ('he' if he else 'en'))
            check(tg + ': cards: no page errors', not errs, errs); await ctx.close()

        # ===== 4. the run-power pick: icon + name =====
        ctx, page, errs = await fresh(b, w=360, h=740, init=prof(adv={'stars': stars(9), 'unlocked': 11}))
        await stage_card(page, 9, 0)
        await page.evaluate(DRAWN)
        await card_tap(page, 'strike', 'next'); await page.wait_for_function("strike.perkOffer && strike.perkMode === 'run' && strike.ui.perkCards && performance.now() - strike.perkOfferAt > 700", timeout=8000)
        await page.evaluate("__drawn.clear()"); await page.evaluate(FRAMES)
        r = await page.evaluate("({ o: strike.perkOffer, cards: strike.ui.perkCards, names: strike.perkOffer.map(id => __drawn.has(t('pk_' + id))), desc: strike.perkOffer.some(id => [...__drawn].some(s => s && t('pkd_' + id).startsWith(s.slice(0, 12)) && s.length > 6)), sub: __drawn.has(t('rpSub')), title: __drawn.has(t('runPowTitle')) })")
        check('4 the run pick (world 2): the title and the 3 names, no description lines, no subtitle; the cards still big targets (>= 44 px)', r['title'] and all(r['names']) and not r['desc'] and not r['sub'] and all(c['h'] >= 44 and c['w'] >= 44 for c in r['cards']), r)
        await page.screenshot(path='tests/out/feel_runpick.png')
        check('4 no page errors', not errs, errs); await ctx.close()

        # ===== 5. perf: the start screen idles (no game loop, the dots on the compositor, the audio asleep after 5 s of silence) =====
        ctx, page, errs = await fresh(b)
        await page.wait_for_timeout(1200)
        bg = await page.evaluate("(() => { const st = getComputedStyle($('start')), be = getComputedStyle($('start'), '::before'); return { st: st.animationName, be: be.animationName, img: be.backgroundImage.split('radial-gradient').length - 1, stImg: st.backgroundImage }; })()")
        check('5 the start screen\'s dots: a ::before layer animated by transform (two dot layers), none on #start itself', bg['be'] == 'mbBg' and bg['img'] == 2 and bg['st'] == 'none' and bg['stImg'] == 'none', bg)
        f0 = await page.evaluate("fxp.frame"); await page.wait_for_timeout(1000); f1 = await page.evaluate("fxp.frame")
        check('5 idle start screen (fresh): no frame() over 1 s', f1 == f0 and not await page.evaluate("running"), [f0, f1])
        await page.tap('#start button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000)
        f0 = await page.evaluate("fxp.frame"); await page.wait_for_timeout(600); f1 = await page.evaluate("fxp.frame")
        check('5 a game starts and animates (the loop woke up)', f1 > f0 + 5 and await page.evaluate("running"), [f0, f1])
        await page.evaluate("audioInit(); goHome()"); await page.wait_for_function("mode === 'none' && !xf.on", timeout=5000); await page.wait_for_timeout(300)
        f0 = await page.evaluate("fxp.frame"); await page.wait_for_timeout(1000); f1 = await page.evaluate("fxp.frame")
        check('5 back home after a game: the game loop stops (no frame() over 1 s)', f1 == f0 and not await page.evaluate("running"), [f0, f1])
        await page.evaluate("setGameMode('slice'); strikeStart('mouse')"); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000)
        f0 = await page.evaluate("fxp.frame"); await page.wait_for_timeout(500)
        check('5 ...and the next game runs again', await page.evaluate("fxp.frame") > f0 + 5)
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none'", timeout=5000)
        await page.evaluate("AUDIO_IDLE_MS; audioIdle.last = performance.now() - 6000; clearTimeout(audioIdle.t); audioIdle.t = 0; audioIdleCheck()"); await page.wait_for_timeout(200)
        a1 = await page.evaluate("({ st: audio && audio.state, sus: audioIdle.sus, n: audioIdle.n })")
        await page.tap('#bubuBtn'); await page.wait_for_timeout(300)
        a2 = await page.evaluate("({ st: audio && audio.state, sus: audioIdle.sus })")
        check('5 home after 5 s of silence: the AudioContext suspends; the next touch resumes it', a1['sus'] and a1['n'] >= 1 and a1['st'] == 'suspended' and not a2['sus'] and a2['st'] == 'running', [a1, a2])
        check('5 no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=False, w=1280, h=800, camera=True, init="localStorage.setItem('inputPref','camera');")
        await page.click('#start button[data-mode=strike]'); await page.wait_for_function("!$('advMap').hidden", timeout=5000)
        await page.wait_for_function("__grasp.panelfix.homeCam.on", timeout=15000)
        await page.evaluate("$('advBack').click()"); await page.wait_for_timeout(300)
        r = await page.evaluate("(() => { const q = $('littleBtn').getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2]; })()")
        await page.evaluate(f"window.__handFor = () => handAt({r[0]}, {r[1]}, 0.8)")
        await page.wait_for_function("!$('littlePick').hidden", timeout=8000)
        check('5 the home camera keeps the loop running: the hand held over "Little ones" still opens it', 'littleBtn' in await page.evaluate("__grasp.panelfix.homeCam.clicks") and await page.evaluate("running"))
        check('5 camera: no page errors', not errs, errs); await ctx.close()

        # ===== 6. toddlers: a tap on nothing still answers (Sandbox, Busy Board, Shapes, Calm bubbles: the Little ones games' twinkle) =====
        FREE = """((hit) => { const y0 = Math.max(chromeRow.bottom + 40, 120); for (let y = y0; y < innerHeight - 60; y += 7) for (let x = 12; x < innerWidth - 12; x += 7) if (!hit({ x, y })) return [x, y]; return null; })"""
        games = [('sandbox', "setGameMode('sandbox'); strikeStart('mouse')", "gameMode === 'sandbox' && mode === 'mouse'", "(p) => bodies.some(q => Math.hypot(p.x - q.position.x, p.y - q.position.y) - q.plugin.r < CONFIG.GRAB_RADIUS + 30)", 3500),
                 ('busy', "setGameMode('busy'); strikeStart('mouse')", "gameMode === 'busy' && mode === 'mouse'", "(p) => busy.widgets.some(w => w.hit(p) || w.hit({ x: p.x + 4, y: p.y }) || w.hit({ x: p.x - 4, y: p.y }) || w.hit({ x: p.x, y: p.y + 4 }) || w.hit({ x: p.x, y: p.y - 4 }))", 600),
                 ('shapes', "setGameMode('shapes'); strikeStart('mouse')", "gameMode === 'shapes' && mode === 'mouse' && shapes.phase === 'play'", "(p) => shapeAt(p) >= 0 || shapeAt({ x: p.x + 20, y: p.y }) >= 0 || shapeAt({ x: p.x - 20, y: p.y }) >= 0 || shapeAt({ x: p.x, y: p.y + 20 }) >= 0 || shapeAt({ x: p.x, y: p.y - 20 }) >= 0", 900),
                 ('bubbles', "cgStart('bubbles', 'mouse')", "gameMode === 'bubbles' && mode === 'mouse' && bubbles.calm", "(p) => bubbles.list.some(q => Math.hypot(p.x - q.x, p.y - q.y) < q.r + 90)", 900)]
        for g, start, ready, hit, wait in games:
            ctx, page, errs = await fresh(b, init="localStorage.setItem('cgTouchOk', '1'); localStorage.setItem('bubblesCalm', '1');")
            await page.evaluate(start); await page.wait_for_function(ready, timeout=10000); await page.wait_for_timeout(wait)
            n0 = await page.evaluate("tg.twinkles || 0"); xy = await page.evaluate(FREE + "(" + hit + ")")
            if xy: await page.touchscreen.tap(xy[0], xy[1]); await page.wait_for_timeout(400)
            n1 = await page.evaluate("tg.twinkles || 0")
            check(f'6 {g}: a tap on empty space answers (a note and sparkles)', xy and n1 > n0, [g, xy, n0, n1])
            check(f'6 {g}: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
