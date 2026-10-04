# Strike v5 ("addictive"): perfect timing, juice, floating texts that never overlap, permanent upgrades, run powers between Adventure stages.
# Covers: the timing judge (perfect / good / early / late by ms from the ideal moment, a fast ball's wider window, the short Normal window's
# cap, the 'perfect' upgrade), the hand's contact time (an early swing caught by the path memory is early; the camera's lag), PERFECT's
# effects (+1 tier capped at SUPER, x2 points, hit-stop, flash rings, the sting, the floater, the perfect streak), a still hand is never
# PERFECT, a natural hit in play is judged, the PERFECT serve (flicked as the pulsing ring closes), the timing ring; the juice (hit-stop /
# shake / big chunks scaled to what broke, the chunks fly at the camera, the SUPER thump, the wall-down flash, the last wall's slow-motion beat
# with the camera nudge, prefers-reduced-motion); floaters (one big message at a time, PERFECT cuts in, no two texts overlap each other or the
# banners / tag / combo pop, the spotlight waits for the stage banner); upgrades (Shop rows, prices, buying, levels, MAX, validation, effects,
# none in the daily, the difficulty still climbs); run powers (offered after a clear before Next, tap / auto pick, each power's effect, one
# stage only, kept for a retry after a fail, none after a boss). Screenshots tests/out/addict_*.png (EN / HE, phone).
exec(open('tests/test_challenge.py').read().split('async def main')[0])

FLOAT_JS = """window.textRects = () => { const s = __grasp.strike, ui = s.ui; return { fl: ui.floaterRects.slice(), blocks: ui.blocks.filter(b => b.name !== 'hud').slice() }; };
window.overlaps = (R) => { const all = R.fl.map(r => ({ ...r, kind: 'fl' })).concat(R.blocks.map(r => ({ ...r, kind: r.name }))), out = [];
  for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) { const a = all[i], b = all[j]; if (a.kind !== 'fl' && b.kind !== 'fl' && !(a.kind === 'stageBanner' || b.kind === 'stageBanner' || a.kind === 'spot' || b.kind === 'spot' || a.kind === 'combo' || b.kind === 'combo' || a.kind === 'tag' || b.kind === 'tag')) continue;
    if (a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h) out.push([a.kind + ':' + (a.text || ''), b.kind + ':' + (b.text || '')]); } return out; };
0;"""
RAF = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"

async def frames(page, n=2):
    for _ in range(n): await page.evaluate(RAF)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== T1: the timing judge (pure, deterministic) =====
        ctx, page, errs = await fresh(b); await endless(page); await page.evaluate(FLOAT_JS)
        jt = await page.evaluate("""(() => { const J = (e, sp, w) => judgeTiming(e, sp, w); return {
          z: hitZone(), p0: J(0, 0.65, 740), p85: J(85, 0.65, 740), pm85: J(-85, 0.65, 740), g150: J(150, 0.65, 740), gm190: J(-190, 0.65, 740), e: J(300, 0.65, 740), l: J(-300, 0.65, 740),
          fast: timingWin(2.2, 0), capped: timingWin(2.2, 480 / 2.2), slow: timingWin(0.65, 740), normal: timingWin(1.1, 150 / 1.1) }; })()""")
        check('the judge: within ±90 ms of the ideal moment = PERFECT, within ±200 = Good, more = Early (+) / Late (-)', [jt[k]['grade'] for k in ('p0', 'p85', 'pm85', 'g150', 'gm190', 'e', 'l')] == ['perfect', 'perfect', 'perfect', 'good', 'good', 'early', 'late'] and jt['slow']['perf'] == 90 and jt['slow']['good'] == 200, jt)
        check('a faster ball gets a wider window (fair on phones), never more than 30% of its hit window: the short Normal window is not all PERFECT', jt['fast']['perf'] > 110 and jt['fast']['good'] > 230 and 60 <= jt['capped']['perf'] <= 70 and 40 <= jt['normal']['perf'] <= 42 and jt['normal']['good'] < 110, [jt['fast'], jt['capped'], jt['normal']])
        check('the ideal moment sits a third into the hit window (Easy: z 330 .. -150)', abs(jt['z']['zi'] - (-150 + 0.35 * 480)) < 1 and jt['z']['zo'] == 330, jt['z'])
        up = await page.evaluate("profile.upg.perfect = 2; const w = timingWin(0.65, 740); profile.upg.perfect = 0; w")
        check('the Perfect window upgrade: +15% a level (level 2: ±117 ms)', abs(up['perf'] - 117) < 0.5, up)
        # the contact time: the hand's nearest pass over the ball in the path memory
        HT = """((tt, swingAgo, cam) => { const s = __grasp.strike, b = s.ball, Z = hitZone(), now = performance.now(); b.dir = 1; b.speed = 0.65; b.z = Z.zi + tt * 0.65; b.curve = 0;
          const sc = ballScreen(b); cursor.present = true; cursor.history.length = 0; cursor.history.push({ t: now - 150, x: sc.x - 300, y: sc.y }, { t: now - swingAgo, x: sc.x, y: sc.y }, { t: now - 5, x: sc.x + (swingAgo > 20 ? 260 : 2), y: sc.y }); cursor.x = sc.x + (swingAgo > 20 ? 260 : 2); cursor.y = sc.y;
          const m0 = mode; if (cam) mode = 'camera'; const r = hitTiming(b, now); mode = m0; return r; })"""
        h = await page.evaluate(f"[{HT}(0, 5), {HT}(60, 5), {HT}(0, 120), {HT}(-150, 5), {HT}(0, 5, true)]")
        check('the hand met the ball at the ideal moment: PERFECT (err ~0); 60 ms before it: still PERFECT, +60', h[0]['grade'] == 'perfect' and abs(h[0]['err']) <= 8 and h[1]['grade'] == 'perfect' and 50 <= h[1]['err'] <= 70, h[:2])
        check('a swing that passed the ball\'s spot 120 ms ago (caught by the path memory) counts from then: Good, early (+120)', h[2]['grade'] == 'good' and 110 <= h[2]['err'] <= 130, h[2])
        check('150 ms after the ideal moment: Good, late (-150); on the camera the tracker\'s lag (50 ms) is taken off the contact time', h[3]['grade'] == 'good' and -160 <= h[3]['err'] <= -140 and 45 <= h[4]['err'] - h[0]['err'] <= 55, [h[3], h[4]])

        # ===== T2: PERFECT in play =====
        await page.evaluate("park(); __grasp.strike.noSpecials = true")
        PH = """((force, tt, swing) => { const s = __grasp.strike, now = performance.now(); s.setBallZ(400, 640, 420); const b = s.ball, Z = hitZone(); b.speed = 0.65; b.z = Z.zi + tt * 0.65;
          const sc = ballScreen(b); cursor.present = true; cursor.history.length = 0; cursor.history.push({ t: now - 60, x: sc.x - (swing ? 120 : 0), y: sc.y }, { t: now - 3, x: sc.x, y: sc.y }); cursor.x = sc.x; cursor.y = sc.y;
          __sfx.length = 0; s.heat = 0; s.stopUntil = 0; const sc0 = s.score, mul = comboMul(), tm = hitTiming(b, now); strikeHit(b, now, force, tm);
          const r = { grade: tm.grade, tier: s.lastHit.tier, ds: s.score - sc0, mul, stop: s.stopUntil - now, sfx: __sfx.slice(), fl: s.floaters.map(f => f.text), streak: s.perfStreak, best: s.bestPerf, last: s.lastTiming, rings: rings.length }; park(); s.heat = 0; s.hotUntil = 0; return r; })"""
        q1 = await page.evaluate(f"__grasp.strike.streak = 0; {PH}('medium', 0, true)")
        check('PERFECT: a medium slap goes out one tier up (hard), x2 points (3 x2), an ~90 ms hit-stop, the sting, flash rings, a "PERFECT!" floater, streak 1',
              q1['grade'] == 'perfect' and q1['tier'] == 'hard' and q1['ds'] == 2 * round(3 * q1['mul']) and q1['stop'] >= 75 and 'perfect' in q1['sfx'] and 'PERFECT!' in q1['fl'] and q1['streak'] == 1 and q1['rings'] >= 2, q1)
        q2 = await page.evaluate(f"{PH}('hard', 30, true)")
        check('a second PERFECT in a row: hard -> SUPER, the floater says "PERFECT ×2", perfect streak 2', q2['grade'] == 'perfect' and q2['tier'] == 'super' and q2['streak'] == 2 and 'PERFECT ×2' in q2['fl'], q2)
        q3 = await page.evaluate(f"{PH}('super', -20, true)")
        check('a PERFECT SUPER stays SUPER (capped: the blast stays bounded)', q3['tier'] == 'super' and q3['grade'] == 'perfect' and q3['streak'] == 3 and q3['best'] == 3, q3)
        q4 = await page.evaluate(f"{PH}('medium', 160, true)")
        check('a Good hit: no bump (medium), no x2, a small "Good" floater, the perfect streak is gone', q4['grade'] == 'good' and q4['tier'] == 'medium' and q4['streak'] == 0 and 'Good' in q4['fl'] and 'perfect' not in q4['sfx'], q4)
        q5 = await page.evaluate(f"{PH}(0.05, 0, false)")
        check('a hand held still on the ball\'s path is never PERFECT (it takes a swing): Good, soft, no label', q5['grade'] == 'good' and q5['tier'] == 'soft' and q5['last']['still'] and 'perfect' not in q5['sfx'], q5)
        q6 = await page.evaluate(f"{PH}('medium', 400, true)")
        check('a swing 400 ms early: "Early" (small)', q6['grade'] == 'early' and 'Early' in q6['fl'], q6['fl'])
        # the timing ring: closing on the ideal spot, gold inside the perfect window
        rg = []
        for tt in (450, 10):
            await page.evaluate(f"(() => {{ const s = __grasp.strike; s.setBallZ(400, 640, 420); const b = s.ball, Z = hitZone(); b.speed = 0.0001; b.z = Z.zi + {tt} * 0.65 * 1; b.speed = 0.65; s.stopUntil = performance.now() + 400; }})()")
            await frames(page); rg.append(await page.evaluate("__grasp.strike.ui.timingRing"))
        check('the timing ring: 450 ms out it is wide and white; at the ideal moment it meets the ball\'s outline in gold', rg[0] and rg[0]['r'] > rg[0]['r0'] * 1.6 and not rg[0]['hot'] and rg[1] and rg[1]['hot'] and abs(rg[1]['r'] - rg[1]['r0']) < rg[1]['r0'] * 0.1, rg)
        await page.screenshot(path='tests/out/addict_ring_en.png')
        # a natural hit in play is judged (ballTick): the mouse resting on the ball's path at the window's edge = early
        await page.evaluate("park(2300, 640, 420); __grasp.strike.ball.speed = 0.3; __grasp.strike.timings = {}")
        await page.mouse.move(640, 420)
        nat = None
        for _ in range(40):
            await page.mouse.move(640, 421); await page.mouse.move(640, 420); await page.wait_for_timeout(60)
            if await page.evaluate("__grasp.strike.ball.dir === -1 || Object.keys(__grasp.strike.timings).length > 0"): break
            await page.evaluate("(() => { const b = __grasp.strike.ball; if (b.z > 600) { b.z = 600; } })()")
        nat = await page.evaluate("({ t: __grasp.strike.timings, last: __grasp.strike.lastTiming, dir: __grasp.strike.ball && __grasp.strike.ball.dir })")
        check('a natural hit in play is judged (a still mouse on the path at the window\'s edge: early)', nat['last'] and sum(nat['t'].values()) >= 1 and nat['last']['grade'] in ('early', 'good'), nat)
        # the PERFECT serve: flicked as the pulsing ring closes
        sv = await page.evaluate("""(() => { const s = __grasp.strike, now = performance.now(); s.balls.length = 0; startWait(now); s.waitSince = now - 1000; __sfx.length = 0;
          const a = [serveTiming(now - 700, now), serveTiming(now - 350, now), serveTiming(now - 900, now), serveTiming(now - 1420, now)];
          const tier = playerServe('medium', now, 0, serveTiming(now - 700, now)); return { a, tier, last: s.lastTiming, sfx: __sfx.slice(), fl: s.floaters.map(f => f.text) }; })()""")
        check('the serve\'s ring: flicked as it closes (700 ms after the pull) = PERFECT; 350 ms in = early; 900 = good (late); the next close (1400) PERFECT', [q['grade'] for q in sv['a']] == ['perfect', 'early', 'good', 'perfect'] and sv['a'][2]['err'] < 0, sv['a'])
        check('a PERFECT serve: one tier up (medium -> hard), the sting and the floater (no points: a serve)', sv['tier'] == 'hard' and sv['last']['serve'] and 'perfect' in sv['sfx'] and any('PERFECT' in f for f in sv['fl']), sv)
        await page.evaluate("(() => { const s = __grasp.strike, now = performance.now(); s.balls.length = 0; startWait(now); s.waitSince = now - 1000; s.pull.armed = true; s.pull.armedAt = now - 650; })()")
        await frames(page); sr0 = await page.evaluate("__grasp.strike.ui.timingRing")
        sr = await (await page.wait_for_function("(() => { const r = __grasp.strike.ui.timingRing; return r && r.hot ? { ...r } : null; })()", timeout=3000, polling='raf')).json_value()
        check('the armed serve ball: a ring pulses in round it, gold as it closes on the ball', sr0 and sr0['serve'] and sr['serve'] and sr['hot'] and sr0['r'] >= sr0['r0'] and abs(sr['r'] / sr['r0'] - (1 + 1.3 * abs(sr['tt']) / 350)) < 0.02 and sr['r'] < sr['r0'] * 1.35, [sr0, sr])
        check('T: no page errors', not errs, errs); await ctx.close()

        # ===== J: juice =====
        ctx, page, errs = await fresh(b); await endless(page); await page.evaluate("__grasp.strike.noSpecials = true; __grasp.strike.reducedMotion = false")
        JB = "((tier, col, row) => { __sfx.length = 0; const s = __grasp.strike; s.stopUntil = 0; const d0 = s.debris.filter(d => d.chunk).length, now = performance.now(), r = blast(tier, col, row); return { n: r.n, j: s.juice, stop: s.stopUntil - now, chunks: s.debris.filter(d => d.chunk).length - d0, sfx: __sfx.slice(), amp: shake.amp }; })"
        js = await page.evaluate(f"[{JB}('soft', 1, 2), {JB}('hard', 1, 2), {JB}('super', 1, 2)]")
        s0, s1, s2 = js
        check('juice scales with the impact: soft (1 brick) no hit-stop, a small shake, no chunks; hard (5): a short stop, more shake, 2 chunks; SUPER (9): the longest stop (capped 110 ms), the capped shake, 4 chunks',
              s0['j']['stop'] == 0 and s0['j']['chunks'] == 0 and s1['n'] == 5 and 40 <= s1['j']['stop'] <= 60 and s1['j']['chunks'] == 2 and s2['n'] == 9 and s2['j']['stop'] == 110 and s2['j']['chunks'] == 4 and s0['j']['shake'] < s1['j']['shake'] < s2['j']['shake'] <= 3.2, [q['j'] for q in js])
        check('the hit-stop is applied (the world freezes that long) and a SUPER impact adds the bass thump', s2['stop'] >= 100 and 'thump' in s2['sfx'] and 'thump' not in s0['sfx'], [s2['stop'], s2['sfx']])
        ch = await page.evaluate("__grasp.strike.debris.filter(d => d.chunk).map(d => ({ z: d.z, s: proj(d.x, d.y, d.z).s, k: d.k, vz: d.vz }))")
        await page.wait_for_timeout(350)
        ch2 = await page.evaluate("__grasp.strike.debris.filter(d => d.chunk).map(d => ({ z: d.z, s: proj(d.x, d.y, d.z).s }))")
        check('big chunks fly at the camera: big pieces, depth falling fast, their on-screen size growing (perspective)', len(ch) >= 4 and all(c['vz'] < -1 and c['k'] >= 0.3 for c in ch) and len(ch2) >= 1 and min(c['z'] for c in ch2) < min(c['z'] for c in ch) - 200 and max(c['s'] for c in ch2) > max(c['s'] for c in ch) * 1.3, [ch[:2], ch2[:2]])
        await page.evaluate(f"{JB}('super', 1, 2)"); await page.wait_for_timeout(40); await page.screenshot(path='tests/out/addict_juice_en.png')
        wf = await page.evaluate("(() => { __sfx.length = 0; const w = plainWall(); w.left = 1; wallDown(w, performance.now()); return { f: __grasp.strike.wallFlash, sfx: __sfx.slice() }; })()")
        check('a wall down: a white flash, a wide ring and a low thump', wf['f'] and not wf['f']['rm'] and 'thump' in wf['sfx'] and 'chime' in wf['sfx'], wf)
        # reduced motion
        await page.evaluate("__grasp.strike.reducedMotion = true; shake.amp = 0; shake.t = -1e9")
        rm = await page.evaluate(f"{JB}('super', 1, 2)")
        check('prefers-reduced-motion: the same impact shakes at most 0.6 px (5x less), the juice records it', rm['j']['rm'] and rm['j']['shake'] <= 0.6 and rm['amp'] <= 0.6 and rm['j']['raw'] > 3, rm['j'])
        check('J: no page errors', not errs, errs); await ctx.close()
        # the last wall of a stage: a slow-motion beat, the camera nudged forward (and none of it with reduced motion)
        for red in (False, True):
            ctx, page, errs = await fresh(b, init="window.__rm = " + ('true' if red else 'false') + ";")
            await stage(page, 3); await page.evaluate(f"__grasp.strike.reducedMotion = {'true' if red else 'false'}; __grasp.strike.noRunPick = true")
            p0 = await page.evaluate("proj(100, 100, 600).s")
            await page.evaluate(f"{A}.finishTest(0)"); await page.wait_for_timeout(300)
            sm = await page.evaluate("({ s: __grasp.strike.lastSlowmo, push: __grasp.strike.ui.camPush, slow: __grasp.strike.slowUntil - performance.now(), p: proj(100, 100, 600).s })")
            if not red:
                check('the stage\'s last wall: a 0.6 s slow-motion beat, the camera nudged forward (things loom bigger) and back', sm['s']['ms'] == 600 and sm['s']['push'] == 130 and sm['push'] > 60 and sm['p'] > p0 * 1.1, [sm, p0])
                await page.screenshot(path='tests/out/addict_slowmo_en.png')
                await page.wait_for_timeout(900); check('... the camera is back after the beat', await page.evaluate("__grasp.strike.ui.camPush") == 0)
            else:
                check('reduced motion: a short beat (250 ms), no camera move', sm['s']['ms'] == 250 and sm['s']['push'] == 0 and sm['push'] == 0 and abs(sm['p'] - p0) < 1e-6, sm)
            check('slow-mo: no page errors', not errs, errs); await ctx.close()

        # ===== F: floating texts never overlap; one big message at a time =====
        for he in (False, True):
            tag = 'he_phone' if he else 'en_phone'
            ctx, page, errs = await fresh(b, mobile=True, he=he); await stage(page, 22); await page.evaluate(FLOAT_JS)
            await page.evaluate(f"{S}.playerServe('medium'); park(2300); {S}.walls.forEach(w => w.turretAt = 1e12)")
            # the stage banner is up: a spotlight waits for it (it used to cover 'Stage 22')
            await page.evaluate(f"{S}.spots.length = 0; {S}.spots.push({{ id: 'steel', t: 0 }}); {S}.ui.levelBanner = {{ t: performance.now() - 300, level: 9, stage: 22, goal: 6, boss: false, world: 0 }}")
            await frames(page)
            sb = await page.evaluate(f"({{ spot: {S}.ui.spot, banner: !!{S}.ui.levelBanner, R: textRects(), o: overlaps(textRects()) }})")
            check(tag + ': while the "Stage 22" banner shows, the "New! Steel walls" spotlight waits (no overlap)', sb['banner'] and sb['spot'] is None and not sb['o'], sb)
            await page.wait_for_function(f"{S}.ui.spot", timeout=5000)
            await frames(page); so = await page.evaluate("overlaps(textRects())")
            check(tag + ': the spotlight comes after the banner, clear of everything', not so, so)
            # a busy moment: a combo pop, the tag, many points, a keystone, WALL +n, gold, weak spot, PERFECT, all at once and at the same spot
            await page.evaluate(f"""(() => {{ const s = {S}, now = performance.now(), x = innerWidth / 2, y = innerHeight * 0.36; s.floaters.length = 0; s.floatLog.length = 0; s.streak = 8; streakUp(now); s.ui.tag = {{ t: now, kind: 'steel' }};
              for (let i = 0; i < 6; i++) addFloater({{ x: x + (i % 3 - 1) * 20, y: y + (i % 2) * 8, text: '+' + (3 + i), big: false, life: 1 }});
              addFloater({{ x, y, text: t('keyHit'), big: true, life: 1.2 }}); addFloater({{ x, y: y + 10, text: 'WALL +170', big: true, life: 1 }}); addFloater({{ x, y, text: t('goldPts', {{ n: 50 }}), big: true, life: 1.2 }});
              addFloater({{ x: x + 30, y: y + 40, text: t('tmGood'), small: true, life: 0.7 }}); }})()""")
            bigs = await page.evaluate(f"(() => {{ const now = performance.now(); return {{ act: {S}.floaters.filter(f => f.big && !(f.wait > now)).map(f => f.text), wait: {S}.floaters.filter(f => f.wait > now).map(f => f.text) }}; }})()")
            check(tag + ': one big message at a time: Keystone! shows, WALL +170 and GOLD wait their turn', len(bigs['act']) == 1 and len(bigs['wait']) == 2, bigs)
            await frames(page, 3)
            for _ in range(8):  # (a loaded container: the layout settles over a few frames; sample until it is clear)
                R = await page.evaluate("textRects()"); o = await page.evaluate("overlaps(textRects())")
                if not o: break
                await frames(page, 1)
            check(tag + ': busy moment: no two texts overlap (floaters, the combo pop, the tag, the spotlight): ' + str(len(R['fl'])) + ' floaters drawn', not o and len(R['fl']) >= 5, [o, R])
            await page.screenshot(path=f'tests/out/addict_busy_{tag}.png')
            await page.wait_for_function(f"{S}.floatLog.length >= 3", timeout=4000)
            lg = await page.evaluate(f"{S}.floatLog.slice(-3)"); await frames(page); o2 = await page.evaluate("overlaps(textRects())")
            check(tag + ': the big messages take turns: Keystone!, then WALL +170, then GOLD, each up >= 0.45 s before the next (still no overlap)', [q['text'] for q in lg] == [await page.evaluate("t('keyHit')"), 'WALL +170', await page.evaluate("t('goldPts', { n: 50 })")] and all(lg[i + 1]['at'] - lg[i]['at'] >= 440 for i in range(2)) and not o2, [lg, o2])
            await page.evaluate("addFloater({ x: innerWidth / 2, y: innerHeight * 0.4, text: t('perfect'), big: true, perfect: true, life: 1.1 })")
            await frames(page)
            q = await page.evaluate(f"(() => {{ const now = performance.now(); return {{ act: {S}.floaters.filter(f => f.big && !(f.wait > now) && f.life > 0).map(f => f.text), o: overlaps(textRects()) }}; }})()")
            check(tag + ': PERFECT cuts in at once (the message showing gives way)', q['act'] == [await page.evaluate("t('perfect')")] and not q['o'], q)
            await page.screenshot(path=f'tests/out/addict_perfect_{tag}.png')
            # sampled over a second of real play-like spawning: never an overlap
            bad = []
            for i in range(8):
                await page.evaluate("(() => { const x = innerWidth * (0.3 + Math.random() * 0.4), y = innerHeight * (0.3 + Math.random() * 0.3); addFloater({ x, y, text: '+' + (1 + (Math.random() * 30 | 0)), big: false, life: 1 }); if (Math.random() < 0.5) addFloater({ x, y, text: t('weakHit'), big: true, life: 1.2 }); })()")
                await page.wait_for_timeout(110); ov = await page.evaluate("overlaps(textRects())")
                if ov: bad.append(ov)
            check(tag + ': floaters spawned over a second at random spots: never an overlap', not bad, bad)
            check(tag + ': floaters: no page errors', not errs, errs); await ctx.close()

        # ===== U: permanent upgrades =====
        for he in (False, True):
            tag = 'he_phone' if he else 'en_phone'
            ctx, page, errs = await fresh(b, mobile=True, he=he)
            await page.evaluate("profile.coins = 0; saveProfile(); openPanel('collection')")
            rows = await page.evaluate("[...document.querySelectorAll('#upgs .upg')].map(b => ({ id: b.dataset.id, cls: b.className, pr: b.querySelector('.pr').textContent, pips: b.querySelectorAll('.pips i').length, on: b.querySelectorAll('.pips i.on').length, nm: b.querySelector('.nm').textContent, w: b.getBoundingClientRect().width, r: b.getBoundingClientRect().right }))")
            ids = [r['id'] for r in rows]
            check(tag + ': the Shop opens on a Power section: 6 upgrade tracks (3 levels; Extra heart 2), names, level pips, the first price', ids == ['heavy', 'heart', 'cool', 'reach', 'lucky', 'perfect'] and [r['pips'] for r in rows] == [3, 2, 3, 3, 3, 3] and all(r['on'] == 0 for r in rows) and [r['pr'] for r in rows] == ['100', '160', '80', '100', '90', '80'] and all(r['r'] <= 361 for r in rows), rows)
            check(tag + ': the first levels cost 80-160 coins (about 3-4 runs at 15-35 a run); with no coins they read as too dear', all('poor' in r['cls'] for r in rows))
            await page.click('#upgs .upg[data-id=cool]'); await page.wait_for_timeout(100)
            nt = await page.evaluate("({ lv: profile.upg.cool || 0, toast: meta.toasts.slice(-1)[0], shake: document.querySelector('#upgs .upg[data-id=cool]').className })")
            check(tag + ': a tap with too few coins: nothing bought, a "not enough" toast', nt['lv'] == 0 and nt['toast']['key'] == 'notEnough', nt)
            await page.evaluate("profile.coins = 300; saveProfile(); renderCollection()")
            await page.click('#upgs .upg[data-id=cool]'); await page.wait_for_timeout(150)
            bt = await page.evaluate("({ lv: profile.upg.cool, coins: profile.coins, row: (() => { const b = document.querySelector('#upgs .upg[data-id=cool]'); return { on: b.querySelectorAll('.pips i.on').length, pr: b.querySelector('.pr').textContent }; })(), saved: JSON.parse(localStorage.getItem(PROFILE_KEY)).upg })")
            check(tag + ': buying Cool hands: level 1 (a pip lights), 80 coins paid, the next level costs 210; saved', bt['lv'] == 1 and bt['coins'] == 220 and bt['row'] == {'on': 1, 'pr': '210'} and bt['saved'] == {'cool': 1}, bt)
            await page.evaluate("profile.upg.heart = 2; profile.upg.perfect = 1; saveProfile(); renderCollection()")
            mx = await page.evaluate("(() => { const b = document.querySelector('#upgs .upg[data-id=heart]'); return { cls: b.className, pr: b.querySelector('.pr').textContent, lv: profile.upg.heart, buy: buyUpgrade('heart') }; })()")
            check(tag + ': a maxed track says MAX and buys nothing more', 'max' in mx['cls'] and mx['pr'] == await page.evaluate("t('upMax')") and mx['lv'] == 2 and not mx['buy'], mx)
            await page.evaluate("$('metaToast').replaceChildren(); document.querySelector('#collection .sheet').scrollTop = 0"); await page.wait_for_timeout(150)
            await page.screenshot(path=f'tests/out/addict_shop_{tag}.png')
            check(tag + ': shop: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b)
        v = await page.evaluate("(() => { localStorage.setItem(PROFILE_KEY, JSON.stringify({ v: PROFILE_V, coins: 5, upg: { heavy: 9, heart: -1, cool: 'x', reach: 2.5, bogus: 3, lucky: 2, perfect: 0 } })); return loadProfile().upg; })()")
        check('the profile\'s upgrades are validated on load: clamped to each track\'s max, junk dropped', v == {'heavy': 3, 'lucky': 2}, v)
        v2 = await page.evaluate("(() => { localStorage.setItem(PROFILE_KEY, JSON.stringify({ v: PROFILE_V, coins: 5, upg: 'oops' })); return loadProfile().upg; })()")
        check('... a broken field loads as no upgrades', v2 == {}, v2)
        await page.evaluate("localStorage.removeItem(PROFILE_KEY); profile = loadProfile(); saveProfile()")
        await endless(page)
        await page.evaluate("resetStrike(performance.now())"); e0 = await page.evaluate("({ s: upgStats(), lives: (() => { const l = __grasp.strike.lives; park(); return l; })() })")
        await page.evaluate("profile.upg = { heavy: 3, heart: 2, cool: 3, reach: 3, lucky: 3, perfect: 3 }; saveProfile(); resetStrike(performance.now())")
        e1 = await page.evaluate("({ s: upgStats(), lives: (() => { const l = __grasp.strike.lives; park(); return l; })(), heat: (() => { const s = __grasp.strike; s.heat = 0; heatHit('super', performance.now()); const a = s.heat; heatHit('soft', performance.now()); return [a, s.heat]; })() })")
        check('upgrades apply in Endless: +2 hearts, reach x1.15, heat x0.55 per hard hit and cooling x2.05, gold +0.66, a wider PERFECT window (x1.45)',
              e1['lives'] == e0['lives'] + 2 and abs(e1['s']['reach'] - e0['s']['reach'] * 1.15) < 1e-6 and abs(e1['heat'][0] - 0.45 * 0.55) < 1e-6 and e1['heat'][1] == 0 and abs(e1['s']['coolK'] - 2.05) < 1e-6 and abs(e1['s']['gold'] - 1.66) < 1e-6 and abs(e1['s']['win']['perf'] - 90 * 1.45) < 0.01, [e0, e1])
        hv = await page.evaluate("""(() => { const s = __grasp.strike; s.noSpecials = true; s.heavyUps = 0; let wide = 0; for (let i = 0; i < 60; i++) { const r = blast('medium', 1, 2); if (r.n > 2) wide++; } const ups = s.heavyUps;
          const w = plainWall(), k = w.bricks.find(q => q.col === 1 && q.row === 2); k.armor = true; k.hp = k.max = 3; const b = ballAt(w, 1, 2, 'medium'); smashWall(w, b, performance.now()); return { wide, ups, armor: k.alive }; })()""")
        check('Heavier ball: a medium hit sometimes blasts a plus (36% at level 3), and level 3 breaks a 3-hp armored brick with one medium hit', 8 <= hv['wide'] <= 40 and hv['ups'] == hv['wide'] and not hv['armor'], hv)
        gd = await page.evaluate("(() => { const s = __grasp.strike, c0 = profile.coins, w = plainWall(), k = w.bricks[0]; k.gold = true; const b = ballAt(w, k.col, k.row, 'soft'); smashWall(w, b, performance.now()); return profile.coins - c0; })()")
        check('Lucky: a gold brick pays a coin too', gd == 1, gd)
        await page.evaluate("__grasp.strike.diff = 'easy'; daily.on = true")
        dl = await page.evaluate("({ lv: upgStats().lv, reach: reachMul() })"); await page.evaluate("daily.on = false")
        check('the daily ignores upgrades (a fair run, the same for everyone)', all(x == 0 for x in dl['lv'].values()), dl)
        await page.evaluate("profile.upg = { heart: 2, reach: 3 }; saveProfile()")
        await stage(page, 20)
        ad = await page.evaluate(f"({{ lives: {S}.lives, reach: reachMul() * advK('reachK'), r1: advPlan(1).reachK, r20: advPlan(20).reachK, r36: advPlan(36).reachK }})")
        check('Adventure: Extra heart 2 = 5 hearts (3 stars still means no heart lost); maxed reach never undoes the ramp: world 3+ reach (x' + str(round(ad['reach'], 3)) + ') stays under world 1\'s on-ramp (x1.08)', ad['lives'] == 5 and ad['reach'] < 1.08 and ad['r36'] * 1.15 < 1.0, ad)
        check('U: no page errors', not errs, errs); await ctx.close()

        # ===== R: run powers between stages =====
        for he in (False, True):
            tag = 'he_phone' if he else 'en_phone'
            ctx, page, errs = await fresh(b, mobile=True, he=he); await stage(page, 3)
            await page.evaluate(f"{A}.finishTest(0)")
            await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.next && performance.now() - {S}.overAt > 600", timeout=10000)
            r = await page.evaluate(f"{S}.ui.buttons.next"); await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
            await page.wait_for_function(f"{S}.perkOffer && {S}.ui.perkCards && {S}.ui.perkCards.length === 3", timeout=5000)
            await page.wait_for_timeout(500)
            of = await page.evaluate(f"({{ o: {S}.perkOffer, mode: {S}.perkMode, cards: {S}.ui.perkCards, btn: {S}.ui.buttons, stage: {A}.stage, all: RUN_POWERS, i18n: {S}.perkOffer.every(id => I18N.en['pk_' + id] && I18N.he['pk_' + id] && I18N.en['pkd_' + id] && I18N.he['pkd_' + id]) }})")
            check(tag + ': Next after a clear: 3 different run powers on big cards (EN / HE names), the card\'s buttons out of the way, the stage not started yet',
                  of['mode'] == 'run' and len(set(of['o'])) == 3 and all(x in of['all'] for x in of['o']) and of['btn'] is None and of['stage'] == 3 and of['i18n'] and all(c['h'] >= 88 and c['w'] >= 300 for c in of['cards']), of)
            await page.screenshot(path=f'tests/out/addict_runpick_{tag}.png')
            c = of['cards'][1]; await page.mouse.click(c['x'] + c['w'] / 2, c['y'] + c['h'] / 2)
            await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 4 && {S}.walls.length", timeout=6000)
            await frames(page, 3)
            pk = await page.evaluate(f"({{ p: {A}.power, pend: {A}.pendingPower, badge: {S}.ui.runBadge, last: {S}.lastPick }})")
            check(tag + ': a tap on a card picks it: stage 4 starts with that power, a small badge by the HUD pill', pk['p'] == of['o'][1] and pk['pend'] is None and pk['badge'] and pk['badge']['id'] == pk['p'] and pk['last']['run'], pk)
            await page.screenshot(path=f'tests/out/addict_runbadge_{tag}.png')
            check(tag + ': run pick: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b); await stage(page, 3)
        async def with_power(pid, n=3):
            await page.evaluate(f"{A}.pendingPower = '{pid}'; {A}.start({n})")
            await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === {n} && {S}.walls.length", timeout=6000)
            await page.evaluate("(() => { const l = __grasp.strike.lives; park(); __grasp.strike.lives = l; })()")
        await with_power('rp_shield')
        sh = await page.evaluate(f"(() => {{ const s = {S}, l0 = s.lives; loseLife(performance.now()); const a = {{ lives: s.lives, lost: {A}.lost, shield: s.shield, fl: s.floaters.map(f => f.text) }}; loseLife(performance.now()); return {{ l0, a, b: {{ lives: s.lives, lost: {A}.lost }} }}; }})()")
        check('Shield: the first lost heart is blocked (no star lost either), the next one counts', sh['a']['lives'] == sh['l0'] and sh['a']['lost'] == 0 and sh['a']['shield'] == 0 and sh['b']['lives'] == sh['l0'] - 1 and sh['b']['lost'] == 1 and 'Shield!' in sh['a']['fl'], sh)
        await with_power('rp_heart'); hl = await page.evaluate(f"{S}.lives")
        check('Extra heart: 4 hearts this stage', hl == 4, hl)
        await with_power('rp_fire'); await with_power('rp_fire'); fr = await page.evaluate("[powerOn('fire'), powerOn('slow')]")
        await with_power('rp_slow'); sl = await page.evaluate("[powerOn('fire'), powerOn('slow')]")
        check('Fire start / Slow-mo start: the stage begins with a fireball / in slow motion', fr == [True, False] and sl == [False, True], [fr, sl])
        m0 = await page.evaluate("magnetVal()"); await with_power('rp_magnet'); m1 = await page.evaluate("magnetVal()")
        check('Magnet paddle: the ball drifts to the hand much more (+0.45)', abs(m1 - m0 - 0.45) < 1e-6, [m0, m1])
        await with_power('rp_combo')
        cb = await page.evaluate(f"(() => {{ const s = {S}; s.streak = 9; const m0 = comboMul(); streakReset(performance.now()); const m1 = comboMul(); streakReset(performance.now()); return [m0, m1, comboMul(), s.comboSaves]; }})()")
        check('Combo keeper: the first miss keeps the combo (x4 stays), the next one drops it', cb == [4, 4, 1, 1], cb)
        await with_power('rp_split')
        sp = await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(140, 640, 420); strikeHit(s.ball, performance.now(), 'super'); const n = s.balls.length, sp = s.balls.filter(b => b.split).length; const l0 = s.lives; const c = s.balls.find(b => b.split); strikeMiss(c, performance.now()); return {{ n, sp, lives: s.lives - l0, left: s.balls.length }}; }})()")
        check('Split shot: a SUPER hit splits the ball in two; missing the extra one costs no heart', sp['n'] == 2 and sp['sp'] == 1 and sp['lives'] == 0 and sp['left'] == 1, sp)
        # one stage only; kept for a retry after a fail; none after a boss; auto-pick
        await with_power('rp_heart', 3)
        await page.evaluate(f"{A}.finishTest(0)"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons", timeout=10000)
        await page.evaluate(f"{A}.start(4)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 4", timeout=6000)
        ex = await page.evaluate(f"[{A}.power, {S}.lives]")
        check('a run power lasts one stage: the next stage (no pick) has none (3 hearts)', ex == [None, 3], ex)
        await with_power('rp_heart', 4); await page.evaluate(f"{A}.failTest()"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.retry", timeout=10000)
        await page.evaluate(f"{A}.start(4)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 4", timeout=6000)
        rt = await page.evaluate(f"[{A}.power, {S}.lives]")
        check('a fail keeps the power for the retry', rt == ['rp_heart', 4], rt)
        await page.evaluate(f"profile.adv.unlocked = 40; saveProfile(); {A}.start(8)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 8", timeout=6000)
        await page.evaluate(f"{A}.finishTest(0)"); await page.wait_for_function(f"{S}.over && {A}.phase === 'card'", timeout=15000)
        await page.evaluate("advNext()"); await page.wait_for_timeout(300)
        bo = await page.evaluate(f"({{ offer: {S}.perkOffer, map: {A}.mapOpen }})")
        check('after a boss stage (a new world): no pick, the map', bo['offer'] is None and bo['map'], bo)
        await page.evaluate(f"closeAdvMap(true); {A}.start(5)"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 5", timeout=6000)
        await page.evaluate(f"{S}.setPerkTimeout(400); {A}.finishTest(0)"); await page.wait_for_function(f"{S}.over && {A}.phase === 'card'", timeout=10000)
        await page.evaluate("advNext()"); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 6", timeout=6000)
        au = await page.evaluate(f"({{ p: {A}.power, last: {S}.lastPick }})")
        check('nothing picked: the first card is taken after the timer (20 s; here 0.4 s) and the next stage starts', au['p'] and au['last']['auto'] and au['last']['run'], au)
        await page.evaluate(f"{S}.setPerkTimeout(0)")
        check('R: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('FAILURES:', check.fails); sys.exit(1 if check.fails else 0)

asyncio.run(main())
