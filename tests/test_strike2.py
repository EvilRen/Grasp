exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike step 2 (the roguelite run): perk cards between levels, the NEXT-wall telegraph, the hit streak, 'Close one!'.
# Timing-independent: the ball is parked (speed 0) between checks, every wait is a condition or a frame count.
S = "__grasp.strike"
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
PIX = "((x, y) => __grasp.strike.pixel(x, y))"  # the composited pixel: the WebGL layer (3D mode) under the 2D canvas; in 2D mode the 2D canvas pixel
TOUCH_JS = """
window.touchAt = (t, x, y) => document.getElementById('stage').dispatchEvent(new PointerEvent(t, { pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }));
"""
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
HELP_JS = """
window.park = (z = 2300, x = 30, y = 30) => { const s = __grasp.strike; s.setBallZ(z, x, y); s.ball.speed = 0; s.lives = 40; };  // the ball frozen far away, plenty of lives
window.forceOffer = (ids) => { const s = __grasp.strike; s.offerPerks(); s.perkOffer = ids.slice(); return s.perkOffer; };  // an offer of these perks (the cards redraw from strike.perkOffer every frame)
window.hpLeft = () => { const s = __grasp.strike, w = s.walls.find(q => q.left > 1 && q.z < __grasp.CONFIG.STRIKE_Z_FAR); return w ? { id: w.id, hp: w.bricks.filter(k => k.alive).reduce((a, k) => a + k.hp, 0) } : null; };
"""
PERK_IDS = ['wide', 'heavy', 'magnet', 'skin', 'lucky', 'spark', 'slow', 'coins']

async def new_page(b, mobile=False):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e))); await page.add_init_script(INIT + TOUCH_JS)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    return ctx, page, errs

async def play_strike(page, tap=False):
    if tap: await page.tap('.modes button[data-mode=strike]'); await page.tap('#mouseBtn')
    else: await page.click('.modes button[data-mode=strike]'); await page.click('#mouseBtn')
    await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.ball", timeout=8000)
    await page.evaluate(SFX_JS + ";\n" + HELP_JS + "\n__grasp.CONFIG.STRIKE_PU_RATE = 0; park()")

async def frames(page, n=1):
    for _ in range(n): await page.evaluate(FRAMES)

async def hit(page, x, y):  # an incoming ball parked at HIT_Z under the (still) cursor: hit on the next frame; then the returning ball is frozen
    h0 = await page.evaluate(f"{S}.hits")
    await page.evaluate(f"{S}.setBallZ(__grasp.CONFIG.STRIKE_HIT_Z, {x}, {y})")
    await page.wait_for_function(f"{S}.hits > {h0}", timeout=4000)
    await page.evaluate(f"{S}.ball.speed = 0")

async def wait_offer(page, first=None):  # the cards are up, drawn, and past the input guard
    cond = f"{S}.perkOffer && {S}.ui.perkCards && performance.now() - {S}.perkOfferAt > 520" + (f" && {S}.ui.perkCards[0].id === '{first}'" if first else '')
    await page.wait_for_function(cond, timeout=6000)

def center(r): return r['x'] + r['w'] / 2, r['y'] + r['h'] / 2

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== desktop, mouse: perks =====
        ctx, page, errs = await new_page(b); await play_strike(page)
        await page.mouse.move(640, 600); await page.wait_for_timeout(100)
        hk = await page.evaluate(f"(() => {{ const s = {S}; return {{ perks: s.perks, offer: s.perkOffer, pick: typeof s.pickPerk, streak: s.streak, next: s.next, close: s.closeOnes, timeout: typeof s.setPerkTimeout }}; }})()")
        check('hooks: perks {}, perkOffer null, pickPerk, streak 0, next (a wall kind), closeOnes 0, setPerkTimeout', hk['perks'] == {} and hk['offer'] is None and hk['pick'] == 'function' and hk['streak'] == 0 and hk['next'] == 'brick' and hk['close'] == 0 and hk['timeout'] == 'function', hk)
        i18n = await page.evaluate("(() => { const ids = " + str(PERK_IDS) + "; return ['en', 'he'].every(l => ids.every(id => I18N[l]['pk_' + id] && I18N[l]['pkd_' + id]) && ['perkTitle', 'next', 'nk_boss', 'streak5', 'streak10', 'streakLost', 'closeOne', 'ms_close'].every(k => I18N[l][k])); })()")
        check('I18N: every perk has an EN + HE name and one-line description; NEXT / BOSS / streak / Close one strings in both', i18n)
        # level-up -> the burst first, then the cards; everything waits
        await page.evaluate(f"__sfx.length = 0; park(); {S}.setLevel(3); {S}.setCleared(15)")  # level 3 done (perk picks come after levels 3, 5, 7 ...)
        lu = await page.evaluate(f"({{ level: {S}.level, offer: {S}.perkOffer, at: {S}.perkAt - performance.now(), up: !!{S}.ui.levelUp }})")
        check('level 3 cleared: level 4 with the Level up! burst; the perk cards wait for the calm release beat (2.5 s)', lu['level'] == 4 and lu['offer'] is None and 2000 < lu['at'] <= 2500 and lu['up'], lu)
        await page.evaluate(f"(() => {{ const s = {S}; s.setBallZ(2000, 640, 400); s.lives = 40; }})()")  # a moving ball, to see the freeze
        await page.wait_for_function(f"{S}.perkOffer", timeout=5000)
        of = await page.evaluate(f"({{ offer: {S}.perkOffer, z: {S}.ball.z, held: {S}.ui.levelBanner && {S}.ui.levelBanner.held, sfx: __sfx }})")
        await frames(page, 3); z1 = await page.evaluate(f"{S}.ball.z")
        check('the perk offer: 3 different perks from the pool', len(of['offer']) == 3 and len(set(of['offer'])) == 3 and all(i in PERK_IDS for i in of['offer']), of['offer'])
        check('while the cards are up the game is frozen (the ball does not move) and the level banner waits', z1 == of['z'] and of['held'] and 'cards' in of['sfx'], [of, z1])
        await wait_offer(page)
        pc = await page.evaluate(f"{S}.ui.perkCards")
        check('desktop: three cards side by side, inside the screen, below the HUD', len(pc) == 3 and all(c['x'] >= 0 and c['x'] + c['w'] <= 1280 and c['y'] + c['h'] <= 800 for c in pc) and pc[0]['x'] < pc[1]['x'] < pc[2]['x'] and abs(pc[0]['y'] - pc[2]['y']) < 1 and pc[0]['y'] > await page.evaluate(f"{S}.ui.hud.y + {S}.ui.hud.h"), pc)
        px = [0, 0, 0]  # the brightest of a small grid around the icon (icons differ per perk; one point can land on a dark glyph stroke)
        for dx in (-12, 0, 12):
            for dy in (-10, 0, 10):
                q = await page.evaluate(PIX + f"({pc[1]['x'] + pc[1]['w'] / 2 + dx}, {pc[1]['y'] + pc[1]['h'] * 0.27 + dy})")
                if max(q) > max(px): px = q
        check('the card icon is drawn in colour (bright pixel at the icon)', max(px) > 150, px)
        hr = await page.evaluate(f"({{ row: {S}.ui.heartsRow, hud: {S}.ui.hud }})")
        check('desktop: 40 lives = one heart + ×40, the row inside the HUD card', hr['row']['compact'] and hr['row']['x'] >= hr['hud']['x'] and hr['row']['x'] + hr['row']['w'] <= hr['hud']['x'] + hr['hud']['w'], hr)
        await page.evaluate(f"{S}.lives = {S}.maxLives"); await frames(page, 2)
        hr = await page.evaluate(f"({{ row: {S}.ui.heartsRow, hud: {S}.ui.hud }})")
        check('desktop: 5 lives = five hearts, inside the card', not hr['row']['compact'] and hr['row']['x'] >= hr['hud']['x'] and hr['row']['x'] + hr['row']['w'] <= hr['hud']['x'] + hr['hud']['w'], hr)
        await page.screenshot(path='tests/out/strike6_perks_desktop.png'); await page.evaluate(f"{S}.lives = 40")
        # pick by click: Wider Hands -> reach x1.2
        await page.evaluate("forceOffer(['wide', 'magnet', 'skin'])"); await wait_offer(page, 'wide')
        st0 = await page.evaluate(f"{S}.perkStats()")
        c = (await page.evaluate(f"{S}.ui.perkCards"))[0]; x, y = center(c)
        await page.mouse.click(x, y); await page.wait_for_timeout(60); await page.evaluate("park()")
        st = await page.evaluate(f"({{ perks: {S}.perks, offer: {S}.perkOffer, stats: {S}.perkStats(), bn: {S}.ui.levelBanner, now: performance.now(), tag: {S}.ui.tag }})")
        check('click on a card picks it: Wider Hands stacked once, reach x1.0 -> x1.2, the cards close', st['perks'] == {'wide': 1} and st['offer'] is None and abs(st0['reach'] - 1) < 1e-9 and abs(st['stats']['reach'] - 1.2) < 1e-9, [st0, st])
        check('after the pick the level banner slides in and the perk name shows as a tag under the HUD', st['bn'] and not st['bn'].get('held') and st['bn']['t'] >= st['now'] - 100 and st['tag'] and st['tag']['kind'] == 'wide' and st['tag'].get('perk'), [st['bn'], st['tag']])
        await frames(page, 2); pi = await page.evaluate(f"({{ icons: {S}.ui.perkIcons, hud: {S}.ui.hud }})")
        check('the active perk shows as a tiny icon inside the HUD card', len(pi['icons']) == 1 and pi['icons'][0]['id'] == 'wide' and pi['hud']['y'] < pi['icons'][0]['y'] < pi['hud']['y'] + pi['hud']['h'] and pi['hud']['x'] < pi['icons'][0]['x'] < pi['hud']['x'] + pi['hud']['w'], pi)
        # the other effects (picked through the hook)
        await page.evaluate("forceOffer(['magnet'])"); await page.evaluate(f"{S}.pickPerk(0)")
        await page.evaluate("forceOffer(['skin'])"); lv0 = await page.evaluate(f"[{S}.lives, {S}.maxLives]"); await page.evaluate(f"{S}.lives = 3; {S}.pickPerk(0)")
        await page.evaluate("forceOffer(['lucky'])"); await page.evaluate(f"{S}.pickPerk(0)")
        st = await page.evaluate(f"({{ s: {S}.perkStats(), base: __grasp.CONFIG.STRIKE_PU_RATE }})")
        check('Sticky Magnet: the magnet +0.15 (level 4: 0.325 -> 0.475)', abs(st0['magnet'] - 0.325) < 1e-9 and abs(st['s']['magnet'] - st0['magnet'] - 0.15) < 1e-9, [st0['magnet'], st['s']['magnet']])
        check('Thick Skin: +1 max life (4 -> 5) and one heart back (3 -> 4)', lv0[1] == 4 and st['s']['maxLives'] == 5 and st['s']['lives'] == 4, [lv0, st['s']])
        await page.evaluate("__grasp.CONFIG.STRIKE_PU_RATE = 1 / 12"); r, L = await page.evaluate(f"[{S}.perkStats().puRate, {S}.level]"); await page.evaluate("__grasp.CONFIG.STRIKE_PU_RATE = 0")
        check(f'Lucky: power-up rate x1.5 (level {L}: 1/3 a wall -> 1/2)', abs(r - min(1 / 3 + max(0, L - 4) / 24, 0.5) * 1.5) < 1e-9, [r, L])
        await page.evaluate("forceOffer(['heavy'])"); await page.evaluate(f"{S}.pickPerk(0)")
        await page.evaluate(f"park(); {S}.setLevel(1)")  # 1-hp bricks
        w = await page.evaluate(f"(() => {{ const w = {S}.smashTest('soft'); return {{ id: w.id, left: w.left }}; }})()"); await page.wait_for_function(f"{S}.ball.dir === 1", timeout=4000)
        left = await page.evaluate(f"{S}.walls.find(w => w.id === {w['id']}).left"); await page.evaluate("park()")
        check('Heavy Ball: a soft hit takes 2 bricks instead of 1 (footprint 2)', w['left'] - left == 2 and await page.evaluate(f"{S}.perkStats().footprint") == 2, [w, left])
        await page.evaluate("forceOffer(['slow'])"); await page.evaluate(f"{S}.pickPerk(0)")
        sv = await page.evaluate(f"(() => {{ const s = {S}; s.serve(); const r = {{ speed: s.ball.speed, pace: s.pace }}; park(); return r; }})()")
        check('Slow Start: a serve comes in 15% slower', abs(sv['speed'] - sv['pace'] * 0.85) < 1e-9, sv)
        await page.evaluate("forceOffer(['coins'])"); await page.evaluate(f"{S}.pickPerk(0)")
        c0 = await page.evaluate("__grasp.profile.coins"); await page.evaluate("__grasp.addCoins(10)"); c1 = await page.evaluate("__grasp.profile.coins")
        check('Coin Magnet: +50% coins this run (10 -> 15)', c1 - c0 == 15, [c0, c1])
        await page.evaluate("forceOffer(['spark'])"); await page.evaluate(f"{S}.pickPerk(0)")
        await page.mouse.move(640, 400); await page.wait_for_timeout(250)
        h0 = await page.evaluate("hpLeft()"); await page.evaluate("__sfx.length = 0"); await hit(page, 640, 400); h1 = await page.evaluate(f"(() => {{ const w = {S}.walls.find(q => q.id === {h0['id']}); return w.bricks.filter(k => k.alive).reduce((a, k) => a + k.hp, 0); }})()")
        check('Spark Trail: a return zaps one brick on the next wall (-1 hp), with a bolt and a zap', h0['hp'] - h1 == 1 and 'zap' in await page.evaluate("__sfx"), [h0, h1])
        await page.evaluate("park()")
        # dwell pick: a point held 600 ms on a card
        await page.evaluate("forceOffer(['wide', 'magnet', 'spark'])"); await wait_offer(page, 'wide')
        c = (await page.evaluate(f"{S}.ui.perkCards"))[1]; x, y = center(c)
        await page.mouse.move(x, y); await page.wait_for_timeout(100); await page.mouse.down(button='right')
        await page.wait_for_function(f"{S}.ui.perkDwell && {S}.ui.perkDwell.i === 1", timeout=3000)
        d0 = await page.evaluate(f"{S}.ui.perkDwell.t"); await frames(page, 2)
        mid = await page.evaluate(f"({{ open: !!{S}.perkOffer, age: performance.now() - {d0} }})")
        await page.wait_for_function(f"!{S}.perkOffer", timeout=4000); lp = await page.evaluate(f"{S}.lastPick"); await page.mouse.up(button='right')
        check('dwell: a point held on a card fills the ring and picks it after 600 ms (not before)', (mid['open'] or mid['age'] >= 590) and lp['id'] == 'magnet' and not lp['auto'] and lp['at'] - d0 >= 590 and await page.evaluate(f"{S}.perks.magnet") == 2, [mid, lp, d0])
        # auto-pick when nothing is chosen (shortened through the test hook)
        await page.mouse.move(640, 760); await page.wait_for_timeout(100)
        await page.evaluate(f"{S}.setPerkTimeout(300)"); off = await page.evaluate("forceOffer(['lucky', 'coins', 'spark'])")
        await page.wait_for_function(f"!{S}.perkOffer", timeout=5000); lp = await page.evaluate(f"{S}.lastPick"); await page.evaluate(f"{S}.setPerkTimeout(0)")
        check('no choice: the first card is picked automatically when the clock runs out', lp['auto'] and lp['id'] == off[0] and await page.evaluate(f"{S}.perks.lucky") == 2, lp)
        check('the real auto-pick time is 12 s', await page.evaluate("PERK_AUTO_MS") == 12000 and await page.evaluate(f"{S}.perkAutoMs") is None)
        # stacks cap at 3; a maxed perk is never offered again
        await page.evaluate("for (let i = 0; i < 3; i++) { forceOffer(['wide']); __grasp.strike.pickPerk(0); }")
        cap = await page.evaluate(f"({{ n: {S}.perks.wide, reach: {S}.perkStats().reach }})")
        offers = await page.evaluate("(() => { const out = []; for (let i = 0; i < 30; i++) { __grasp.strike.offerPerks(); out.push(__grasp.strike.perkOffer.slice()); __grasp.strike.perkOffer = null; } return out; })()")
        check('stacks cap at 3 (reach x1.6), and a maxed perk never comes up again', cap['n'] == 3 and abs(cap['reach'] - 1.6) < 1e-9 and all('wide' not in o and len(set(o)) == len(o) == 3 for o in offers), [cap, offers[:3]])
        await page.evaluate("forceOffer(['wide', 'heavy', 'magnet'])"); await wait_offer(page, 'wide')
        pips = await page.evaluate(PIX + f"({S}.ui.perkCards[0].x + {S}.ui.perkCards[0].w / 2 - 15, {S}.ui.perkCards[0].y + {S}.ui.perkCards[0].h - 20)")
        check('stack pips on the card: a full Wider Hands shows its first pip filled (green)', pips[1] > 150 and pips[1] > pips[2], pips)
        await page.screenshot(path='tests/out/strike6_perks_stacks.png'); await page.evaluate(f"{S}.pickPerk(1)")
        # a new round starts clean
        await page.click('#resetBtn'); await page.wait_for_timeout(100)
        rs = await page.evaluate(f"({{ perks: {S}.perks, offer: {S}.perkOffer, streak: {S}.streak, close: {S}.closeOnes, max: {S}.maxLives, stats: {S}.perkStats() }})")
        check('reset: perks cleared each round (reach x1, magnet 0.5, 4 lives), no offer, streak 0', rs['perks'] == {} and rs['offer'] is None and rs['streak'] == 0 and rs['close'] == 0 and rs['max'] == 4 and rs['stats']['reach'] == 1 and abs(rs['stats']['magnet'] - 0.5) < 1e-9, rs)
        check('perks: no page errors', not errs, errs)

        # ===== the NEXT card =====
        await page.evaluate("park()"); await frames(page, 2)
        nc = await page.evaluate(f"({{ next: {S}.next, card: {S}.ui.nextCard, v: vanish() }})")
        check('NEXT card: level 1 telegraphs a brick wall, centred above the vanishing point', nc['next'] == 'brick' and nc['card'] and nc['card']['kind'] == 'brick' and nc['card']['y'] + nc['card']['h'] <= nc['v']['y'] and abs(nc['card']['x'] + nc['card']['w'] / 2 - 640) < 2, nc)
        await page.evaluate(f"__sfx.length = 0; park(); {S}.setLevel(2); {S}.setCleared(9)"); await frames(page, 2)  # level 2 done: level 3 unlocks glass
        nc = await page.evaluate(f"({{ next: {S}.next, card: {S}.ui.nextCard, at: performance.now() - {S}.ui.nextAt }})")
        check('level 3: the next wall is the new kind (glass), and the card pulses as it changes', nc['next'] == 'glass' and nc['card']['kind'] == 'glass' and nc['at'] < 600 and nc['card']['pulse'] > 0, nc)
        check('no perk pick after level 2', await page.evaluate(f"!{S}.perkAt && !{S}.perkOffer")); await page.evaluate("park()")
        ids0 = await page.evaluate(f"{S}.walls.map(w => w.id)")
        await page.evaluate(f"{S}.smashTest('super')"); await page.wait_for_timeout(80); await page.evaluate("park()")
        nw = await page.evaluate(f"(() => {{ const w = {S}.walls.filter(q => !{ids0}.includes(q.id)); return w.map(q => q.kind); }})()")
        check('the telegraph tells the truth: the wall that spawned next is glass', nw[:1] == ['glass'], nw)
        await page.evaluate(f"{S}.setCleared(7)"); await frames(page, 2)  # 7 walls down on Easy: the 8th brings the boss
        nc = await page.evaluate(f"({{ next: {S}.next, card: {S}.ui.nextCard, boss: {S}.boss }})")
        check('the next wall cleared brings the boss: the card says BOSS', nc['next'] == 'boss' and nc['card'] and nc['card']['kind'] == 'boss' and not nc['boss'] and await page.evaluate("t('nk_boss')") == 'BOSS', nc)
        await page.wait_for_timeout(300); await page.screenshot(path='tests/out/strike6_next_boss_desktop.png')
        await page.evaluate(f"{S}.setCleared(8)"); await frames(page, 2)
        check('while the boss is in view the card steps aside', await page.evaluate(f"!!{S}.boss && {S}.ui.nextCard === null"))
        check('next card: no page errors', not errs, errs); await ctx.close()

        # ===== hit streak + Close one =====
        ctx, page, errs = await new_page(b); await play_strike(page)
        await page.evaluate("__grasp.CONFIG.STRIKE_MAGNET = 0")  # no magnet pull: the ball stays where it is parked (edge-of-reach checks)
        await page.evaluate("__grasp.profile.missions.list[0] = { id: 'close', progress: 0, goal: 3, reward: 30, done: false, claimed: false }")
        await page.mouse.move(640, 400); await page.wait_for_timeout(250)
        for i in range(1, 4): await hit(page, 640, 400)
        st = await page.evaluate(f"({{ streak: {S}.streak, hits: {S}.hits, mul: {S}.streakMul }})")
        check('every return without a miss adds to the streak (3 hits -> 3, multiplier x1.3)', st['streak'] == 3 and st['hits'] == 3 and abs(st['mul'] - 1.3) < 1e-9, st)
        await frames(page, 2); sb = await page.evaluate(f"({{ box: {S}.ui.streakBox, hud: {S}.ui.hud }})")
        check('streak chip (flame + ×3) in the middle under the HUD card', sb['box'] and sb['box']['n'] == 3 and sb['box']['y'] >= sb['hud']['y'] + sb['hud']['h'] and abs(sb['box']['x'] + sb['box']['w'] / 2 - 640) < 2, sb)
        await page.evaluate(f"{S}.streak = 10"); s0 = await page.evaluate(f"{S}.score"); await hit(page, 640, 400)
        sc = await page.evaluate(f"({{ ds: {S}.score - {s0}, power: {S}.power, fl: {S}.floaters.map(f => f.text) }})")
        check('streak 10: score multiplier x2 (a soft hit worth 1 scores 2)', sc['power'] == 'soft' and sc['ds'] == 2 and '+2' in sc['fl'], sc)
        s0 = await page.evaluate(f"{S}.score"); await page.evaluate(f"{S}.setLevel(1); {S}.smashTest('soft')"); await page.wait_for_function(f"{S}.ball.dir === 1", timeout=4000); await page.evaluate("park()")
        check('the multiplier applies to bricks too (1 brick -> +2 at x2)', await page.evaluate(f"{S}.score") - s0 == 2)
        check('the multiplier caps at x2 (streak 11 -> x2)', await page.evaluate(f"{S}.streakMul") == 2)
        await page.evaluate(f"{S}.streak = 4; __sfx.length = 0"); await hit(page, 640, 400)
        tt = await page.evaluate(f"({{ streak: {S}.streak, toast: {S}.ui.streakToast, sfx: __sfx }})")
        check('streak 5: "On fire!" milestone toast + sound', tt['streak'] == 5 and tt['toast'] and tt['toast']['key'] == 'streak5' and 'streak' in tt['sfx'] and await page.evaluate("t('streak5')") == 'On fire!' and await page.evaluate("t('streak10')") == 'Unstoppable!', tt)
        await page.wait_for_timeout(150); await page.screenshot(path='tests/out/strike6_streak_desktop.png')
        await page.evaluate(f"{S}.streak = 9"); await hit(page, 640, 400)
        check('streak 10: "Unstoppable!"', await page.evaluate(f"{S}.ui.streakToast && {S}.ui.streakToast.key") == 'streak10')
        # a miss ends it
        m0 = await page.evaluate(f"{S}.misses"); await page.mouse.move(100, 100); await page.wait_for_timeout(250)
        await page.evaluate(f"__sfx.length = 0; cursor.history.length = 0; {S}.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.7, 640, 400)")
        await page.wait_for_function(f"{S}.misses > {m0}", timeout=4000)
        ms = await page.evaluate(f"({{ streak: {S}.streak, lost: {S}.ui.streakLost, sfx: __sfx }})")
        check('a miss resets the streak with a "streak lost" fizzle', ms['streak'] == 0 and ms['lost'] and ms['lost']['n'] == 10 and 'fizzle' in ms['sfx'] and await page.evaluate("t('streakLost')") == 'Streak lost', ms)
        await page.wait_for_function(f"{S}.ball", timeout=4000); await page.evaluate("park()")
        # Close one: a late hit (the last 15% of the hit window)
        await page.mouse.move(640, 400); await page.wait_for_timeout(250)
        c0 = await page.evaluate("__grasp.profile.coins"); e0 = await page.evaluate("__grasp.events.length")
        await page.evaluate(f"__sfx.length = 0; {S}.setBallZ(-100, 640, 400)")  # Easy window: +330 .. -150, so -100 sits in its last 15% (<= -78)
        await page.wait_for_function(f"{S}.closeOnes === 1", timeout=4000); await page.evaluate(f"{S}.ball.speed = 0")
        co = await page.evaluate(f"({{ why: {S}.lastClose, coins: __grasp.profile.coins - {c0}, ev: __grasp.events.slice({e0}), slow: {S}.slowUntil - {S}.ui.closeAt, fl: {S}.floaters.map(f => f.text), sfx: __sfx, hits: {S}.hits, m: __grasp.profile.missions.list[0] }})")
        check('late hit: "Close one!" floater, +2 coins, track(close), the close sound', co['why'] == 'late' and co['coins'] == 2 and ['close', 1] in co['ev'] and 'Close one!' in co['fl'] and 'close' in co['sfx'], co)
        check('Close one: a slow-motion moment (x0.4 for 250 ms)', co['slow'] == 250 and await page.evaluate("CLOSE_SLOW") == 0.4, co['slow'])
        check('the "Close one ×3" mission counts it', co['m']['id'] == 'close' and co['m']['progress'] == 1 and any(m['id'] == 'close' and m['goals'] == [3] for m in await page.evaluate("__grasp.missionPool")) and await page.evaluate("t('ms_close', { n: 3 })") == 'Get 3 "Close one!" hits', co['m'])
        await page.wait_for_timeout(150); await page.screenshot(path='tests/out/strike6_close_desktop.png')
        # a plain hit in the middle of the window, dead centre: no Close one
        await hit(page, 640, 400)
        check('a hit mid-window on the ball centre is not a Close one', await page.evaluate(f"{S}.closeOnes") == 1)
        # edge of the reach: the ball parked 93% of the reach away from the cursor
        rc = await page.evaluate(f"(() => {{ const s = 520 / (520 + __grasp.CONFIG.STRIKE_HIT_Z), r = ballR() * s; return Math.max(r * __grasp.CONFIG.STRIKE_HIT_RADIUS, __grasp.CONFIG.STRIKE_HIT_NEAR * strikeScale()); }})()")
        await page.evaluate(f"{S}.setBallZ(__grasp.CONFIG.STRIKE_HIT_Z, {640 + rc * 0.93}, 400)")
        await page.wait_for_function(f"{S}.closeOnes === 2", timeout=4000); await page.evaluate(f"{S}.ball.speed = 0")
        check('a hit at the edge of the reach (> 80%) is a Close one too', await page.evaluate(f"{S}.lastClose") == 'edge' and await page.evaluate("__grasp.profile.missions.list[0].progress") == 2)
        check('streak + close: no page errors', not errs, errs); await ctx.close()

        # ===== phone, EN + HE: cards stacked, NEXT card, streak chip; a tap picks =====
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await new_page(b, mobile=True)
            if he: await page.tap('#startLang'); await page.wait_for_timeout(100)
            await play_strike(page, tap=True)
            await page.evaluate(f"park(); {S}.setLevel(3); {S}.setCleared(15)"); await page.wait_for_function(f"{S}.perkOffer", timeout=8000)  # level 3 done: a perk pick after the release
            await page.evaluate("forceOffer(['spark', 'skin', 'coins'])"); await wait_offer(page, 'spark')
            await page.evaluate("showHint()"); await frames(page, 2)
            hn = await page.evaluate("({ show: hintEl.classList.contains('show'), op: hintEl.style.opacity || '0' })")
            check(tag + ' phone: the hint toast is hidden while the perk cards are up (and showHint does not reopen it)', not hn['show'] and float(hn['op']) < 0.05, hn)
            hr = await page.evaluate(f"({{ row: {S}.ui.heartsRow, hud: {S}.ui.hud, lives: {S}.lives }})")
            check(tag + ' phone: with 40 lives the hearts row is one heart + ×40, inside the HUD card', hr['lives'] == 40 and hr['row']['compact'] and hr['row']['x'] >= hr['hud']['x'] and hr['row']['x'] + hr['row']['w'] <= hr['hud']['x'] + hr['hud']['w'], hr)
            pc = await page.evaluate(f"{S}.ui.perkCards")
            check(tag + ' phone: three perk cards stacked as rows inside 360 px, above the power meter', len(pc) == 3 and all(c['x'] >= 8 and c['x'] + c['w'] <= 352 and c['h'] >= 90 for c in pc) and pc[0]['y'] + pc[0]['h'] < pc[1]['y'] < pc[2]['y'] and pc[2]['y'] + pc[2]['h'] < await page.evaluate(f"{S}.ui.meterTop"), pc)
            nm = await page.evaluate("[t('pk_spark'), t('pkd_spark'), t('perkTitle')]")
            check(tag + ' phone: perk names in the language', nm == (['שובל ניצוצות', 'כל מכה מזפזפת לבנה בקיר הבא', 'בחרו כוח!'] if he else ['Spark Trail', 'Each hit zaps a brick on the next wall', 'Pick a power!']), nm)
            await page.evaluate(f"{S}.lives = {S}.maxLives"); await frames(page, 2); await page.screenshot(path='tests/out/strike6_perks_' + tag + '.png')
            x, y = center(pc[1])
            await page.evaluate(f"touchAt('pointerdown', {x}, {y})"); await page.evaluate(f"touchAt('pointerup', {x}, {y})"); await page.wait_for_timeout(60)
            tp = await page.evaluate(f"({{ offer: {S}.perkOffer, perks: {S}.perks, max: {S}.maxLives }})")
            check(tag + ' phone: a tap on a card picks it (Thick Skin: 5 hearts)', tp['offer'] is None and tp['perks'] == {'skin': 1} and tp['max'] == 5, tp)
            await page.evaluate("forceOffer(['spark']); __grasp.strike.pickPerk(0); forceOffer(['coins']); __grasp.strike.pickPerk(0); park()")
            # streak chip + NEXT card on the phone
            await page.evaluate("touchAt('pointerdown', 180, 380)"); await page.wait_for_timeout(250)
            for _ in range(3): await hit(page, 180, 380)
            await page.evaluate("touchAt('pointerup', 180, 380)")
            await page.evaluate(f"park(); {S}.setCleared(7)"); await page.wait_for_timeout(450); await frames(page, 2)
            ui = await page.evaluate(f"({{ next: {S}.ui.nextCard, streak: {S}.ui.streakBox, icons: {S}.ui.perkIcons, hud: {S}.ui.hud, v: vanish(), coin: __grasp.coinUi.box }})")
            check(tag + ' phone: NEXT card (BOSS) inside the screen above the vanishing point, below the HUD', ui['next'] and ui['next']['kind'] == 'boss' and ui['next']['x'] >= 8 and ui['next']['x'] + ui['next']['w'] <= 352 and ui['next']['y'] + ui['next']['h'] <= ui['v']['y'] and ui['next']['y'] > ui['hud']['y'] + ui['hud']['h'], ui['next'])
            check(tag + ' phone: streak chip ×3 under the HUD card, clear of the coin pill', ui['streak'] and ui['streak']['n'] == 3 and ui['streak']['y'] >= ui['hud']['y'] + ui['hud']['h'] and (ui['streak']['x'] + ui['streak']['w'] <= ui['coin']['x'] or ui['streak']['x'] >= ui['coin']['x'] + ui['coin']['w']), [ui['streak'], ui['coin']])
            ic = ui['icons']
            check(tag + ' phone: 3 perk icons inside the HUD card' + (' (right to left)' if he else ''), len(ic) == 3 and all(ui['hud']['x'] < i['x'] - i['r'] and i['x'] + i['r'] < ui['hud']['x'] + ui['hud']['w'] and i['y'] + i['r'] <= ui['hud']['y'] + ui['hud']['h'] for i in ic) and ((ic[0]['x'] > ic[2]['x']) == he), ic)
            await page.evaluate(f"{S}.lives = {S}.maxLives; {S}.ui.levelBanner = {S}.ui.levelUp = {S}.ui.tag = null"); await frames(page, 2); await page.screenshot(path='tests/out/strike6_next_' + tag + '.png'); await page.evaluate("park()")
            await page.evaluate(f"{S}.streak = 4"); await page.evaluate("touchAt('pointerdown', 180, 380)"); await page.wait_for_timeout(250); await hit(page, 180, 380); await page.evaluate("touchAt('pointerup', 180, 380)")
            tk = await page.evaluate(f"({{ key: {S}.ui.streakToast && {S}.ui.streakToast.key, streak: {S}.streak }})")
            check(tag + ' phone: "' + ('בוערים!' if he else 'On fire!') + '" at streak 5', tk['key'] == 'streak5' and tk['streak'] == 5 and await page.evaluate("t('streak5')") == ('בוערים!' if he else 'On fire!'), tk)
            await page.evaluate(f"{S}.lives = 40; {S}.ui.streakToast = {{ t: performance.now() - 200, key: 'streak5', n: 5 }}"); await page.screenshot(path='tests/out/strike6_streak_' + tag + '.png')
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
