# Strike Adventure worlds 6-8 (Space, Under the Sea, Candy Land). Covers: the map (64 stops, 8 world bands with their signs, ★ n / 192), world 6 opens
# after the Lava Dragon (an old profile that beat stage 40 finds 41 open, nothing else changes), the plans of stages 41-64 (deterministic, ramping
# past world 5, each new kind brought in with the 'New!' spotlight), every new wall kind's rule (asteroid: drifting, turning rocks with gaps; force
# field: blocks while on, breaks while off, switches by itself; coral: grows back unless finished; jelly: soft hits absorbed, medium+ break; gummy:
# 2 hits each; chocolate: splits into two halves first), world 6's floaty serve, world 7's bubble trail, world 8's sparkles, the ambient life; the bosses
# on 48 / 56 / 64 (Alien Mothership: tractor beam + laser sweep; Giant Octopus: ink that hides the aim ring + tentacles that block lanes; Candy King:
# lollipops + the sugar rush) with the shared framework (bar, phases, weak point, shield, intro, victory); travel 5 -> 6 -> 7 -> 8; stickers 41-64 and
# album pages 6-8 with their bonus; the star chests (130 / 160 / 192); the music per world (scheduler stub); guests per world; a theme still gets the
# worlds' life; EN / HE. Screenshots tests/out/world{6,7,8}_*.png and tests/out/boss_w{6,7,8}_*.png (2D + 3D).
exec(open('tests/test_challenge.py').read().split('async def main')[0])
B = "__grasp.boss"; W2 = "__grasp.worlds2"; P = "__grasp.profile"; MU = "__grasp.music"; AL = "__grasp.album"
OUT = 'tests/out/'
BOSSES2 = {48: ('mothership', 'Alien Mothership', 'ספינת האם של החייזרים', 6), 56: ('octopus', 'Giant Octopus', 'התמנון הענק', 7), 64: ('candyking', 'Candy King', 'מלך הממתקים', 8)}

def prof(**kw):
    d = dict(v=1, coins=0, xp=0); d.update(kw)
    return "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(d)) + "); sessionStorage.setItem('__seeded', '1'); }"
def stars(a, b2, v=3): return {str(n): v for n in range(a, b2 + 1)}

async def frames(page, n=2):
    for _ in range(n): await page.evaluate("new Promise(r => requestAnimationFrame(() => r()))")

async def stage64(page, n, walls=True):  # Adventure stage n (all 64 open) with the mouse
    await page.evaluate("profile.adv.unlocked = 64; saveProfile(); setInputPref('mouse')")
    if await page.evaluate("mode === 'none'"):
        await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.click(f'.anode[data-n="{n}"]')
    else: await page.evaluate(f"{A}.start({n})")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && mode === 'mouse'" + (f" && {S}.walls.length > 0" if walls else f" && {B}.b"), timeout=12000)
    await page.evaluate(f"{S}.noRally = true; {S}.noTiming = true; __grasp.CONFIG.STRIKE_PU_RATE = 0; {S}.guestEvery = 0")

async def boss64(page, n):
    await stage64(page, n, walls=False)
    await page.evaluate(f"{B}.enter(); {B}.calm(true); park(); {B}.weak(false)")

HITS = """((tier, x, y, perf) => { const r = __grasp.boss.ball(tier, x, y, perf); park(); return r; })"""
CENTER = "(() => { const s = __grasp.boss.state(); return [s.x, s.y + s.hh * 0.2]; })()"
KWALL = """((kind, z = 900) => { const s = __grasp.strike; s.walls.length = 0; s.noSpecials = true; const w = s.spawnWall(kind, z); for (const k of w.bricks) { k.weak = k.key = k.gold = k.turret = k.armor = false; k.pu = null; if (k.alive && kind !== 'gummy') k.hp = k.max = 1; } return w; })"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', '--autoplay-policy=no-user-gesture-required'])

        # ===== M1: the map (64 stops, 8 bands, ★ / 192), world 6 after the Lava Dragon (an old profile), the plans =====
        for mobile, he in ((False, False), (True, False), (True, True)):
            tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en')
            ctx, page, errs = await fresh(b, mobile, he, init=prof(adv={'stars': stars(1, 40), 'unlocked': 40}, album={'got': list(range(1, 41)), 'fresh': [], 'pages': [1, 2, 3, 4, 5]}, habit={'starChests': [10, 25, 45, 70, 100]}))
            await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(300)
            m = await page.evaluate("""(() => { const n = [...document.querySelectorAll('.anode')].map(e => ({ n: +e.dataset.n, locked: e.classList.contains('locked'), boss: e.classList.contains('boss') }));
              const bands = [...document.querySelectorAll('.aband')].map(e => ({ w: +e.dataset.world, name: e.querySelector('.asign b').textContent, bg: getComputedStyle(e, '::before').backgroundImage.length }));
              return { n, bands, total: $('advStarTotal').textContent.replace(/\\s/g, ''), album: $('advAlbumBtn').querySelector('.pr').textContent, sw: $('advScroll').scrollWidth <= $('advScroll').clientWidth + 1 }; })()""")
            nd = {x['n']: x for x in m['n']}
            names = [x['name'] for x in m['bands']]
            want = ['Space', 'Under the Sea', 'Candy Land'] if not he else ['החלל', 'מתחת לים', 'ארץ הממתקים']
            check(tag + ': the map has 64 stops in 8 world bands; bands 6-8 named ' + str(names[5:]) + ' with their own backdrop', len(m['n']) == 64 and [x['w'] for x in m['bands']] == list(range(1, 9)) and names[5:] == want and all(x['bg'] > 20 for x in m['bands'][5:]) and m['sw'], m['bands'])
            check(tag + ': boss stops 48 / 56 / 64 with a crown', all(nd[k]['boss'] for k in (8, 16, 24, 32, 40, 48, 56, 64)))
            check(tag + ': the star total reads 120/192, the album 40/64', m['total'] == '120/192' and m['album'] == '40/64', [m['total'], m['album']])
            check(tag + ': an old profile that beat the Lava Dragon finds world 6 open (41), the rest of it locked; nothing else changed', not nd[41]['locked'] and all(nd[k]['locked'] for k in range(42, 65)) and await page.evaluate(P + ".adv.unlocked") == 41 and len(await page.evaluate(P + ".adv.stars")) == 40 and await page.evaluate(P + ".album.got.length") == 40, await page.evaluate(P + ".adv.unlocked"))
            if not mobile:
                await page.evaluate("document.querySelector('.anode[data-n=\"41\"]').scrollIntoView({ block: 'center' })"); await page.wait_for_timeout(250)
                await page.screenshot(path=OUT + 'world6_map_desktop.png')
            else:
                for n0, nm in ((44, 'world6'), (52, 'world7'), (60, 'world8')):
                    await page.evaluate(f"document.querySelector('.anode[data-n=\"{n0}\"]').scrollIntoView({{ block: 'center' }})"); await page.wait_for_timeout(250)
                    await page.screenshot(path=OUT + nm + '_map_phone_' + ('he' if he else 'en') + '.png')
            check(tag + ': no page errors (map)', not errs, errs); await ctx.close()

        ctx, page, errs = await fresh(b)
        check('a new player: stage 41 is locked', not await page.evaluate(f"{A}.playable(41)"))
        await page.evaluate("profile.adv.stars[40] = 3; profile.adv.unlocked = 40; saveProfile()")
        await page.reload(); await page.wait_for_timeout(700)
        check('a profile whose stage 40 is cleared opens 41 on load (the old last stage), not 42', await page.evaluate(f"{A}.playable(41) && !{A}.playable(42)"))
        pl = await page.evaluate(f"(() => {{ const o = []; for (let n = 33; n <= 64; n++) {{ const a = JSON.stringify({A}.plan(n)), b = JSON.stringify({A}.plan(n)); o.push(Object.assign({A}.plan(n), {{ same: a === b }})); }} return o; }})()")
        P_ = {x['n']: x for x in pl}
        check('stages 41-64: plans are deterministic (the same object every call), worlds 6 / 7 / 8, bosses on 48 / 56 / 64 with no walls', all(x['same'] for x in pl) and [P_[n]['world'] for n in (41, 48, 49, 56, 57, 64)] == [6, 6, 7, 7, 8, 8] and all(P_[n]['boss'] and P_[n]['walls'] == 0 for n in (48, 56, 64)) and not any(P_[n]['boss'] for n in range(41, 64) if n % 8))
        intro = {41: 'asteroid', 43: 'force', 49: 'coral', 51: 'jelly', 57: 'gummy', 59: 'choco'}
        check('each new kind comes in second on its stage (its spotlight): 41 asteroid, 43 force, 49 coral, 51 jelly, 57 gummy, 59 choco; none before its stage', all(P_[n]['kinds'][1] == k for n, k in intro.items()) and all(k not in P_[m_]['kinds'] for n, k in intro.items() for m_ in range(33, n)), {n: P_[n]['kinds'] for n in intro})
        avg = lambda w, key: sum(P_[n][key] for n in range(w * 8 - 7, w * 8)) / 7
        check('the curve keeps climbing past world 5, gently (pace up, reach and gaps down, walls at least as many); 3 lives a stage', all(avg(w, 'paceK') < avg(w + 1, 'paceK') for w in (5, 6, 7)) and all(avg(w + 1, 'reachK') <= avg(w, 'reachK') and avg(w + 1, 'gapK') < avg(w, 'gapK') and avg(w + 1, 'walls') >= avg(w, 'walls') for w in (5, 6, 7)) and avg(8, 'paceK') < 1.5 and await page.evaluate(A + ".lives") == 3, [avg(w, 'paceK') for w in (5, 6, 7, 8)])
        check('world 6 floats the serve (low gravity), the others do not', all(P_[n]['float'] for n in range(41, 49)) and not any(P_[n]['float'] for n in range(49, 65)) and not P_[40]['float'])
        check('M1: no page errors', not errs, errs); await ctx.close()

        # ===== K: each new wall kind's rule (Endless, plain walls; the hooks spawn a kind) =====
        ctx, page, errs = await fresh(b); await endless(page)
        a1 = await page.evaluate(f"""(() => {{ const w = {KWALL}('asteroid'), ox0 = w.ox, rot0 = w.bricks.filter(k => k.alive).map(k => k.rot), holes = w.bricks.filter(k => k.hole).length, g = wallGrid();
          for (let i = 0; i < 30; i++) {W2}.tick(w, 50); return {{ cols: w.cols, gcols: g.cols, holes, n: w.bricks.length, dox: Math.abs(w.ox - ox0), drot: Math.min(...w.bricks.filter(k => k.alive).map((k, i) => Math.abs(k.rot - rot0[i]))) }}; }})()""")
        check('asteroid: a drifting wall (one brick short, its offset moves), irregular (a fifth of the cells are empty space), every rock turns', a1['cols'] == a1['gcols'] - 1 and a1['dox'] > 1 and a1['holes'] >= round(a1['n'] * 0.2) - 1 and a1['holes'] >= 1 and a1['drot'] > 0.01, a1)
        f1 = await page.evaluate(f"""(() => {{ const w = {KWALL}('force'), on = {W2}.field(w, true), b = ballAt(w, 1, 2, 'super'), n0 = w.left, out = smashWall(w, b, performance.now()); const r = {{ on, out, lost: n0 - w.left, blocks: w.fieldBlocks, sfx: __sfx.slice(-6) }};
          {W2}.field(w, false); const b2 = ballAt(w, 1, 2, 'medium'), n1 = w.left; r.out2 = smashWall(w, b2, performance.now()); r.lost2 = n1 - w.left; r.off = !w.field;
          const t0 = w.fieldT, seq = []; for (let i = 0; i < 90; i++) {{ {W2}.tick(w, 50); seq.push(w.field ? 1 : 0); }} r.flips = seq.filter((v, i) => i && v !== seq[i - 1]).length; return r; }})()""")
        check('force field on: a SUPER hit is blocked (bounces back, no brick lost, "Field on!")', f1['on'] and f1['out'] == 'bounce' and f1['lost'] == 0 and f1['blocks'] == 1, f1)
        check('force field off: the same wall breaks (medium: 2 bricks)', f1['off'] and f1['out2'] == 'bounce' and f1['lost2'] == 2, f1)
        check('the field switches on and off by itself (2 s on, 2 s off: 2+ flips in 4.5 s)', f1['flips'] >= 2, f1['flips'])
        c1 = await page.evaluate(f"""(() => {{ strike.waiting = false; const w = {KWALL}('coral'), k = w.bricks.find(q => q.alive), n0 = w.left; hurtBrick(w, k, 1, {{ x: 0, y: 0 }}, 'soft', performance.now()); const n1 = w.left;
          {W2}.tick(w, 1500); const n2 = w.left; {W2}.tick(w, 2000); const n3 = w.left; return {{ n0, n1, n2, n3, back: k.alive, regrown: w.regrown }}; }})()""")
        check('coral: a broken piece grows back after ~3 s (not at 1.5 s)', c1['n1'] == c1['n0'] - 1 and c1['n2'] == c1['n1'] and c1['n3'] == c1['n0'] and c1['back'] and c1['regrown'] == 1, c1)
        c2 = await page.evaluate(f"""(() => {{ strike.waiting = false; const w = {KWALL}('coral'); let t = 0; while (w.left > 0 && t < 40) {{ const k = w.bricks.find(q => q.alive); hurtBrick(w, k, 1, {{ x: 0, y: 0 }}, 'soft', performance.now()); maybeCollapse(w, performance.now()); if (w.left <= 0) wallDown(w, performance.now()); {W2}.tick(w, 400); t++; }}
          const gone = !strike.walls.includes(w); return {{ gone, regrown: w.regrown, left: w.left }}; }})()""")
        check('coral finished quickly (a break every 0.4 s): it never grows back, the wall comes down', c2['gone'] and c2['regrown'] == 0, c2)
        j1 = await page.evaluate(f"""(() => {{ const w = {KWALL}('jelly'), b = ballAt(w, 1, 2, 'soft'), n0 = w.left, out = smashWall(w, b, performance.now()); const r = {{ out, lost: n0 - w.left, abs: strike.jellyAbsorbs || 0 }};
          const b2 = ballAt(w, 1, 2, 'medium'), n1 = w.left; r.out2 = smashWall(w, b2, performance.now()); r.lost2 = n1 - w.left; return r; }})()""")
        check('jelly: a soft hit only wobbles it (absorbed, "Too soft!"), a medium one breaks it', j1['out'] == 'bounce' and j1['lost'] == 0 and j1['abs'] >= 1 and j1['lost2'] == 2, j1)
        g1 = await page.evaluate(f"""(() => {{ const w = {KWALL}('gummy'), hp = w.bricks.filter(k => k.alive).every(k => k.hp === 2), b = ballAt(w, 1, 2, 'super'), n0 = w.left; smashWall(w, b, performance.now()); const lost1 = n0 - w.left, wob = !!w.bricks.find(k => k.col === 1 && k.row === 2).hitAt;
          const b2 = ballAt(w, 1, 2, 'super'); smashWall(w, b2, performance.now()); return {{ hp, lost1, lost2: n0 - w.left, wob }}; }})()""")
        check('gummy: every gummy has 2 hp; a SUPER hit takes one off each (none breaks, they wobble); the second hit breaks the 3x3', g1['hp'] and g1['lost1'] == 0 and g1['wob'] and g1['lost2'] == 9, g1)
        h1 = await page.evaluate(f"""(() => {{ const w = {KWALL}('choco'), k = w.bricks.find(q => q.col === 1 && q.row === 2), n0 = w.left, r = {{}};
          let b = ballAt(w, 1, 2, 'soft'); smashWall(w, b, performance.now()); r.s1 = [k.alive, k.split, k.hp, n0 - w.left];
          b = ballAt(w, 1, 2, 'soft'); smashWall(w, b, performance.now()); r.s2 = [k.alive, k.hp, n0 - w.left];
          b = ballAt(w, 1, 2, 'soft'); smashWall(w, b, performance.now()); r.s3 = [k.alive, n0 - w.left]; r.splits = strike.chocoSplits; return r; }})()""")
        check('chocolate: the first hit splits a block into two halves (still there, 2 halves), the next hits break one half each', h1['s1'] == [True, True, 2, 0] and h1['s2'] == [True, 1, 0] and h1['s3'] == [False, 1] and h1['splits'] >= 1, h1)
        check('K: no page errors', not errs, errs); await ctx.close()

        # ===== S: the stages in their worlds (the spotlight, the life, the floaty serve, the bubble trail, sparkles, guests, music), 2D screenshots =====
        for mobile in (True, False):
            ctx, page, errs = await fresh(b, mobile, init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}))
            for n, kind, wi in ((41, 'asteroid', 6), (43, 'force', 6), (49, 'coral', 7), (51, 'jelly', 7), (57, 'gummy', 8), (59, 'choco', 8)):
                await stage64(page, n)
                await page.wait_for_function(f"{S}.ui.spot && {S}.ui.spot.id === '{kind}'", timeout=15000)
                sp = await page.evaluate(f"({{ spot: {S}.ui.spot, seen: {P}.adv.seen.includes('{kind}'), world: {A}.world, amb: {W2}.amb }})")
                check(f'stage {n} ({"phone" if mobile else "desktop"}): world {wi}, the "New! ..." spotlight for {kind} ({sp["spot"]["text"]}), remembered; the world\'s life on screen', sp['world'] == wi and sp['spot']['text'].startswith('New!') and sp['seen'] and sp['amb'] and sp['amb']['n'] > 5 and sp['amb']['kind'] == ['stars', 'bubbles', 'sprinkles'][wi - 6], sp)
                await page.evaluate(f"(() => {{ const s = {S}; const keep = s.walls.filter(w => w.kind === '{kind}'); s.walls.length = 0; s.walls.push(...keep.slice(0, 1)); for (const w of s.walls) {{ w.z = w.pz = 720; for (const k of w.bricks) if (k.alive) {{ k.weak = k.turret = k.gold = k.key = false; }} }} park(); }})()")
                if kind == 'choco': await page.evaluate(f"(() => {{ const w = {S}.walls[0]; for (const k of w.bricks.filter(q => q.alive).slice(0, 4)) {{ k.split = true; k.hp = 2; }} }})()")
                await page.wait_for_timeout(2700)
                if kind == 'force': await page.evaluate(f"{W2}.field({S}.walls[0], true)"); await frames(page, 3)
                await page.screenshot(path=OUT + f'world{wi}_{kind}_{"phone" if mobile else "desktop"}.png')
            if mobile:
                await stage64(page, 41); await page.evaluate(f"{S}.waiting = false")
                fl = await page.evaluate(f"(() => {{ serveBall(performance.now()); const b = {S}.balls[0], Z = __grasp.CONFIG.STRIKE_Z_FAR, ys = []; for (const q of [0.25, 0.5, 0.75]) {{ const k = q; ys.push(b.y0 + (b.ty - b.y0) * k - (b.float ? b.float * Math.sin(Math.PI * k) : 0) - (b.y0 + (b.ty - b.y0) * k)); }} return {{ float: b.float, ys }}; }})()")
                check('world 6: the serve floats up in an arc (low gravity) and still lands on its target', fl['float'] > 0 and fl['ys'][1] < fl['ys'][0] < 0 and abs(fl['ys'][0] - fl['ys'][2]) < 1e-6, fl)
                await stage64(page, 49); await page.wait_for_timeout(1500)
                await page.evaluate(f"(() => {{ {S}.waiting = false; serveBall(performance.now()); }})()"); await page.wait_for_timeout(700)
                check('world 7: the ball leaves a trail of bubbles', await page.evaluate(f"{W2}.trail") >= 3, await page.evaluate(f"{W2}.trail"))
                await stage64(page, 57); await page.wait_for_timeout(500)
                sk = await page.evaluate(f"(() => {{ const w = {S}.walls[0], k = w.bricks.find(q => q.alive), n0 = __grasp.gfx.fxp.made + __grasp.gfx.fxp.recycled; breakBrick(w, k, {{ x: 0, y: 0 }}, 'medium', performance.now()); return __grasp.gfx.fxp.made + __grasp.gfx.fxp.recycled - n0; }})()")
                check('world 8: a broken brick bursts in sweet sparkles', sk >= 2, sk)
                gl = await page.evaluate(f"(() => {{ const o = {{}}; for (const n of [41, 49, 57, 1]) {{ adv.world = advWorldOf(n); o[n] = [{W2}.guestLook('cow'), {W2}.guestLook('monkey')]; }} adv.world = 8; return o; }})()")
                check('guests per world: an alien + a space monkey, a fish + a turtle, a gummy bear + a donut (worlds 1-5 keep the cow / monkey)', gl == {'41': ['alien', 'astro'], '49': ['fish', 'turtle'], '57': ['gummybear', 'donut'], '1': ['cow', 'monkey']}, gl)
                gp = await page.evaluate("""(() => ['alien', 'astro', 'fish', 'turtle', 'gummybear', 'donut'].map(k => { const sp = guestSprite(k, 'in'), d = sp.c.getContext('2d').getImageData(0, 0, sp.c.width, sp.c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 200) n++; return [k, n / (d.length / 4), t('say_' + k)]; }))()""")
                check('each new guest is drawn (a filled head) and has its bubble line', all(x[1] > 0.12 and x[2] and not x[2].startswith('say_') for x in gp), gp)
                await stage64(page, 57); await page.evaluate(f"(() => {{ {S}.waiting = false; const b = (serveBall(performance.now()), {S}.balls[0]); makeGuest(b, 'cow', performance.now()); b.z = 900; }})()"); await page.wait_for_timeout(300)
                await page.screenshot(path=OUT + 'world8_guest_phone.png')
            check(f'S ({"phone" if mobile else "desktop"}): no page errors', not errs, errs); await ctx.close()

        # ===== T: a theme still gets the worlds' life (fainter); HE spotlight / tag =====
        ctx, page, errs = await fresh(b, True, True, init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}, themes=['classic', 'gym'], theme='gym'))
        await stage64(page, 49); await page.wait_for_timeout(1200)
        am = await page.evaluate(f"{W2}.amb")
        check('a theme on (gym): the arena is the theme\'s, but under the sea the bubbles / kelp still show, fainter', am and am['kind'] == 'bubbles' and am['faint'] and await page.evaluate("themeNow()") == 'gym', am)
        await page.wait_for_function(f"{S}.ui.spot", timeout=15000)
        check('HE: the spotlight reads "חדש! קירות אלמוגים"-style in Hebrew', 'קירות' in (await page.evaluate(f"{S}.ui.spot.text")), await page.evaluate(f"{S}.ui.spot.text"))
        await page.wait_for_timeout(600); await page.screenshot(path=OUT + 'world7_theme_gym_he.png')
        miss = await page.evaluate("""(() => { const ks = ['wn_6', 'wn_7', 'wn_8', 'bn_mothership', 'bn_octopus', 'bn_candyking', 'fieldBlocked', 'jellySoft', 'tipField', 'tipJelly', 'tipChoco', 'bossAbduct', 'bossInk', 'bossSugar'].concat(...['asteroid', 'force', 'coral', 'jelly', 'gummy', 'choco'].map(k => ['wk_' + k, 'nk_' + k, 'rd_' + k, 'rdd_' + k])).concat(STICKERS.slice(40).map(s => 'st_' + s));
          return ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k])).map(k => l + ':' + k)); })()""")
        check('I18N: every new line in EN and HE', not miss, miss)
        check('T: no page errors', not errs, errs); await ctx.close()

        # ===== B: the bosses on 48 / 56 / 64 =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}))
        for n, (kind, name, name_he, wi) in BOSSES2.items():
            await stage64(page, n, walls=False)
            pl = await page.evaluate(f"({{ walls: {S}.walls.length, banner: !!({S}.ui.levelBanner && {S}.ui.levelBanner.boss) }})")
            await page.wait_for_function(f"{B}.state().entered && {S}.ui.rbIntroBox", timeout=10000)
            intro = await page.evaluate(f"({{ name: {S}.ui.rbIntroBox.name, bar: {S}.ui.bossBar, s: {B}.state(), col: WORLDS[{wi - 1}].accent }})")
            check(f'W{wi}: stage {n} is the {name} fight: no walls, the stage banner, it comes in with its name banner, the health bar in the world\'s colour', pl['walls'] == 0 and pl['banner'] and intro['name'] == name and intro['bar'] and intro['bar']['name'] == name and intro['bar']['col'] == intro['col'] and intro['s']['kind'] == kind, intro['name'])
            await page.wait_for_timeout(900); await page.evaluate(f"{B}.calm(true); park(); {B}.weak(false)")
            await page.screenshot(path=OUT + f'boss_w{wi}_2d.png')
            s0 = await page.evaluate(f"{B}.state()")
            c = await page.evaluate(CENTER)
            r1 = await page.evaluate(f"{HITS}('medium', {c[0]}, {c[1]})")
            check(f'W{wi}: hp {s0["maxHp"]} (harder than the Lava Dragon), a medium hit on the body does 2 and comes back', s0['maxHp'] > 490 and r1['hit'] and r1['dmg'] == 2 and r1['dir'] == 1, [s0['maxHp'], r1])
            wk = await page.evaluate(f"(() => {{ const p = {B}.weak(true); return {HITS}('medium', p.x, p.y); }})()")
            check(f'W{wi}: its weak point while it glows: x3', wk['dmg'] == 6, wk)
            sh = await page.evaluate(f"(() => {{ {B}.fire('shield'); const c = {CENTER}, a = {HITS}('hard', c[0], c[1]), b2 = {HITS}('super', c[0], c[1]); return {{ a: a.dmg, b: b2.dmg, sh: {B}.state().shield }}; }})()")
            check(f'W{wi}: the shield blocks a hard hit, a SUPER breaks it', sh['a'] == 0 and sh['b'] == 4 and not sh['sh'], sh)
            # its own attacks
            if kind == 'mothership':
                ab = await page.evaluate(f"""(() => {{ for (const w of {S}.walls.slice()) if (w.summon) wallDown(w, performance.now()); const s1 = {B}.fire('abduct'); const ws = {S}.walls.filter(w => w.summon), n1 = ws.reduce((a, w) => a + w.left, 0);
                  const w = ws[0]; let broke = 0; for (const k of w.bricks.filter(q => q.alive).slice(0, 3)) {{ hurtBrick(w, k, 1, {{ x: 0, y: 0 }}, 'soft', performance.now()); broke++; }} const n2 = w.left; {B}.b.beam = null; {B}.fire('abduct'); return {{ walls: ws.length, n1, n2, n3: w.left, beam: {B}.state().beam, abducted: {B}.state().abducted }}; }})()""")
                check('Mothership tractor beam: no mini-wall up: it beams one down; broken bricks of it are beamed back into the wall', ab['walls'] >= 1 and ab['n1'] > 0 and ab['n2'] == ab['n3'] - 3 and ab['beam'] and ab['abducted'] >= ab['n1'] + 3, ab)
                await page.evaluate(f"(() => {{ for (const w of {S}.walls.slice()) if (w.summon) wallDown(w, performance.now()); {S}.shots.length = 0; }})()")
                await page.evaluate(f"{B}.calm(true); {B}.fire('laser')")
                await page.wait_for_function(f"{S}.shots.filter(q => q.boss && q.kind === 'laser').length >= 3", timeout=6000)
                ls = await page.evaluate(f"(() => {{ const q = {S}.shots.filter(q => q.boss && q.kind === 'laser'); return {{ n: q.length, tx: q.map(x => x.tx) }}; }})()")
                mono = ls['tx'] == sorted(ls['tx']) or ls['tx'] == sorted(ls['tx'], reverse=True)
                check('Mothership laser sweep: 3 laser shots one after the other across the lanes', ls['n'] >= 3 and mono and max(ls['tx']) - min(ls['tx']) > 100, ls)
                hp0 = await page.evaluate(f"{B}.state().hp")
                await page.evaluate(f"(() => {{ for (const q of {S}.shots.filter(q => q.boss && q.dir > 0)) deflectShot(q, performance.now()); }})()")
                await page.wait_for_function(f"{B}.state().returned >= 3", timeout=8000)
                check('...each slapped away flies back and hurts it (-3 each)', await page.evaluate(f"{B}.state().hp") == hp0 - 9)
                await page.evaluate(f"{S}.shots.length = 0; {B}.fire('abduct')"); await frames(page, 3); await page.screenshot(path=OUT + 'boss_w6_beam.png')
                await page.evaluate(f"(() => {{ for (const w of {S}.walls.slice()) if (w.summon) wallDown(w, performance.now()); }})()")
            if kind == 'octopus':
                ink = await page.evaluate(f"""(() => {{ {B}.fire('ink'); const b = {S}.balls[0] || (serveBall(performance.now()), {S}.balls[0]); b.dir = -1; b.z = 300; b.aim = {{ x: 0, y: 0, z: 700, wall: 1, t: performance.now(), ms: 400 }}; return {{ on: {W2}.inkOn() }}; }})()""")
                await frames(page, 3)
                ik = await page.evaluate(f"({{ marks: {S}.ui.aimMarks.length, ring: {S}.ui.timingRing, ink: {S}.ui.ink, inks: {B}.state().inks }})")
                check('Octopus ink: an ink cloud over the screen, the aim ring and the timing ring hidden while it lasts', ink['on'] and ik['marks'] == 0 and ik['ring'] is None and ik['ink'] and ik['inks'] == 1, ik)
                await page.screenshot(path=OUT + 'boss_w7_ink.png'); park_ = await page.evaluate("park()")
                await page.wait_for_function(f"!{W2}.inkOn()", timeout=6000)
                check('...it clears by itself after a few seconds', True)
                tn = await page.evaluate(f"""(() => {{ {B}.fire('tentacle'); {B}.b.tent.at -= 400; const s = {B}.state(), segs = {B}.arm(); const sg = segs[0], x = sg.x0, y = (sg.y0 + sg.y1) / 2; const hp0 = s.hp; const r = {HITS}('hard', x, y);
                  const lanes = s.tent, free = [-72, -24, 24, 72].find(l => !lanes.includes(l)), G = {B}.b.g, r2 = {HITS}('hard', G.x + free * G.k, G.y - G.hh * 0.6); return {{ lanes, n: segs.length, r, r2, hp: {B}.state().hp - hp0 }}; }})()""")
                check('Octopus tentacles: two lanes blocked (a ball meeting one is thrown back, no damage); the free lanes still reach it', tn['n'] == 2 and len(tn['lanes']) == 2 and tn['r']['hit'] and tn['r']['dmg'] == 0 and tn['r']['dir'] == 1 and tn['r2']['dmg'] > 0, tn)
                await frames(page, 3); await page.screenshot(path=OUT + 'boss_w7_tentacles.png')
            if kind == 'candyking':
                lo = await page.evaluate(f"(() => {{ {S}.shots.length = 0; {B}.fire('shot'); const q = {S}.shots.find(q => q.boss); return q && q.kind; }})()")
                check('Candy King throws lollipops', lo == 'lolly', lo)
                await page.evaluate(f"{S}.shots.length = 0")
                sg = await page.evaluate(f"(() => {{ const k0 = speedMul(); const b = {B}.b; b.hp = Math.floor(b.maxHp / 3) + 2; {B}.hit('medium'); const st = {B}.state(); return {{ k0, k1: speedMul(), sugar: st.sugar, phase: st.phase }}; }})()")
                check('Candy King\'s last phase is the sugar rush: everything faster (the ball x1.2)', sg['phase'] == 3 and sg['sugar'] and abs(sg['k1'] / sg['k0'] - 1.2) < 1e-6, sg)
                await frames(page, 4); await page.screenshot(path=OUT + 'boss_w8_sugar.png')
            # phases + the victory + the trip on
            ph = await page.evaluate(f"(() => {{ const b = {B}.b, out = []; b.shield = null; b.tent = null; while (b.hp > 0 && out.length < 400) {{ {B}.hit('super'); out.push(b.phase); if (b.phase === 3 && !window.__p3) {{ window.__p3 = 1; return {{ p3: true, hp: b.hp }}; }} }} return {{ p3: false }}; }})()")
            await frames(page, 3); await page.evaluate(f"{B}.calm(true)"); await page.wait_for_timeout(300)
            await page.screenshot(path=OUT + f'boss_w{wi}_2d_phase3.png'); await page.evaluate("window.__p3 = 0")
            await page.evaluate(f"(() => {{ const b = {B}.b; while (b && b.hp > 0) {{ b.shield = null; {B}.hit('super'); }} }})()")
            await page.wait_for_function(f"{A}.phase === 'clear' || {A}.phase === 'card'", timeout=6000)
            res = await page.evaluate(f"({{ r: {A}.result, travel: adv.travel && {{ from: adv.travel.from, to: adv.travel.to }} }})")
            check(f'W{wi}: phase 3 reached on the way down; beaten: the stage clear, "{name} defeated!"' + (f', then the trip to world {wi + 1}' if wi < 8 else ' (the last world: no trip, the map next)'), ph['p3'] and res['r']['clear'] and res['r']['boss'] and res['r']['rb']['kind'] == kind and ((res['travel'] == {'from': wi, 'to': wi + 1}) if wi < 8 else res['travel'] is None), res)
            if wi < 8:
                await page.wait_for_function(f"{A}.phase === 'card'", timeout=8000)
                check(f'...the corridor is world {wi + 1}\'s after the trip', await page.evaluate(f"{A}.world") == wi + 1)
            else:
                await page.wait_for_function(f"{A}.phase === 'card' && {S}.ui.buttons && {S}.ui.buttons.next", timeout=8000)
                await page.evaluate("advNext()"); await page.wait_for_timeout(400)
                check('after the Candy King, Next opens the map', await page.evaluate("!$('advMap').hidden"))
        nm = await page.evaluate("(() => ['mothership', 'octopus', 'candyking'].map(k => [I18N.en['bn_' + k], I18N.he['bn_' + k]]))()")
        check('every new boss has its name in EN and HE', [tuple(x) for x in nm] == [(v[1], v[2]) for v in BOSSES2.values()], nm)
        check('B: no page errors', not errs, errs); await ctx.close()

        # ===== B5: the time to beat each new boss (the simulated good player, phone, Easy, the rally on): a little longer than the Lava Dragon (~115-125 s) =====
        ctx, page, errs = await fresh(b, mobile=True, init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}))
        await stage64(page, 48, walls=False); await page.evaluate(f"{S}.noRally = false; {S}.noTiming = false")
        for n, (kind, name, _, wi) in BOSSES2.items():
            await page.evaluate(f"{A}.start({n})"); await page.wait_for_function(f"{A}.stage === {n} && {A}.phase === 'play' && {B}.b", timeout=10000)
            r = await page.evaluate(f"{B}.sim({{ player: 'good', seed: 1, maxS: 600 }})")
            print(f'  measured: stage {n} ({name}) good player: {r["t"]} s, hearts lost per phase {r["segLost"]}, fired {r["fired"]}')
            check(f'W{wi}: a good player beats the {name} in ~1.5-2.5 minutes ({r["t"]} s), using its own attacks', r['t'] and 95 <= r['t'] <= 160 and all(k in r['fired'] for k in {'mothership': ('abduct', 'laser'), 'octopus': ('ink', 'tentacle'), 'candyking': ('shot',)}[kind]), r['fired'])
        check('B5: no page errors', not errs, errs); await ctx.close()

        # ===== B3D: the bosses and worlds in 3D (phone, light settings) =====
        ctx, page, errs = await fresh(b, mobile=True, gfx="{ pr: 0.35, shadows: false, auto: false }", init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}))
        g3 = False
        for n, kind, wi in ((41, 'asteroid', 6), (51, 'jelly', 7), (59, 'choco', 8)):
            await stage64(page, n)
            if not g3:
                try: await page.wait_for_function(f"{S}.gfx === '3d'", timeout=30000); g3 = True
                except Exception: pass
            await page.evaluate(f"(() => {{ const s = {S}; const keep = s.walls.filter(w => w.kind === '{kind}'); s.walls.length = 0; s.walls.push(...keep.slice(0, 1)); for (const w of s.walls) w.z = w.pz = 720; park(); }})()")
            if kind == 'choco': await page.evaluate(f"(() => {{ for (const k of {S}.walls[0].bricks.filter(q => q.alive).slice(0, 5)) {{ k.split = true; k.hp = 2; }} }})()")
            await page.wait_for_timeout(2800); await page.screenshot(path=OUT + f'world{wi}_3d.png')
        if g3:
            mats = await page.evaluate("Object.keys(G3.mats).filter(k => k.startsWith('w2:'))")
            check('3D: the new kinds get their own materials (asteroid, jelly, chocolate + halves)', all(k in mats for k in ('w2:asteroid', 'w2:jelly', 'w2:choco', 'w2:chocoH')), mats)
            await stage64(page, 43); await page.evaluate(f"(() => {{ const s = {S}; const keep = s.walls.filter(w => w.kind === 'force'); s.walls.length = 0; s.walls.push(...keep.slice(0, 1)); for (const w of s.walls) w.z = w.pz = 720; park(); }})()")
            await page.wait_for_timeout(1200); await page.evaluate(f"{W2}.field({S}.walls[0], true)"); await frames(page, 3)
            fv = await page.evaluate(f"(() => {{ const e = G3.walls.get({S}.walls[0].id); return !!(e && e.field && e.field.visible && e.field.material.opacity > 0.3); }})()")
            check('3D: the force field is a glowing plane in front of its wall while on', fv); await page.screenshot(path=OUT + 'world6_force_3d.png')
            for n, (kind, name, _, wi) in BOSSES2.items():
                await boss64(page, n); await page.wait_for_function(f"!{S}.ui.levelBanner && !{S}.ui.rbIntro", timeout=8000); await page.wait_for_timeout(300)
                if kind == 'octopus': await page.evaluate(f"(() => {{ {B}.fire('tentacle'); {B}.b.tent.at -= 400; }})()")
                await page.wait_for_timeout(300)
                ok = await page.evaluate("!!(G3.rb && G3.rb.visible)")
                check(f'3D: the {name} is on its billboard', ok)
                await page.screenshot(path=OUT + f'boss_w{wi}_3d.png')
        else: print('  (WebGL not available here: the 3D screenshots are skipped)')
        check('B3D: no page errors', not errs, errs); await ctx.close()

        # ===== A: stickers 41-64, album pages 6-8, star chests, music =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(1, 40), 'unlocked': 64}, album={'got': list(range(1, 41)), 'fresh': [], 'pages': [1, 2, 3, 4, 5]}))
        st = await page.evaluate("""(() => { const out = []; for (let n = 41; n <= 64; n++) { const sp = stickerSprite(n, false, 40), d = sp.c.getContext('2d').getImageData(0, 0, sp.c.width, sp.c.height).data; let ink = 0, col = new Set();
          for (let i = 0; i < d.length; i += 16) if (d[i + 3] > 200) { ink++; col.add((d[i] >> 5) + ',' + (d[i + 1] >> 5) + ',' + (d[i + 2] >> 5)); } out.push([n, STICKERS[n - 1], col.size, t('st_' + STICKERS[n - 1])]); } return out; })()""")
        check('stickers 41-64: 24 new ones (64 in all, all different), each drawn in colour with a name', await page.evaluate("STICKERS.length") == 64 and len(set(await page.evaluate("STICKERS"))) == 64 and all(x[2] >= 8 and not x[3].startswith('st_') for x in st), [(x[1], x[2]) for x in st])
        c0 = await page.evaluate(P + ".coins")
        r6 = [await page.evaluate(f"{AL}.award({n})") for n in range(41, 49)]
        check('album page 6: 8 stickers fill it, the page bonus is paid once (30)', all(r6) and r6[-1]['page'] and await page.evaluate(P + ".coins") == c0 + 30 and 6 in await page.evaluate(P + ".album.pages"), r6[-1])
        await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(200); await page.click('#advAlbumBtn'); await page.wait_for_timeout(300)
        tabs = await page.evaluate("[...document.querySelectorAll('.albTab')].map(b => b.querySelector('b').textContent)")
        check('the album has 8 world tabs', tabs == [str(i) for i in range(1, 9)], tabs)
        for w in (6, 7, 8):
            await page.evaluate(f"{AL}.setPage({w})"); await page.wait_for_timeout(250)
            await page.screenshot(path=OUT + f'world{w}_album.png')
        check('album pages 6-8 show their world\'s name', (await page.evaluate("$('albumPageTitle').textContent")).endswith('Candy Land'))
        ch = await page.evaluate("__grasp.habit.starChests")
        check('star chests: 10 / 25 / 45 / 70 / 100 / 130 / 160 / 192 paying 15 / 25 / 35 / 50 / 80 / 60 / 70 / 100 (100 and 192 also a look)', [c['stars'] for c in ch] == [10, 25, 45, 70, 100, 130, 160, 192] and [c['coins'] for c in ch] == [15, 25, 35, 50, 80, 60, 70, 100] and [c['last'] for c in ch] == [False, False, False, False, True, False, False, True], ch)
        await page.evaluate("(() => { for (let n = 1; n <= 64; n++) profile.adv.stars[n] = 3; saveProfile(); })()")
        c1 = await page.evaluate(P + ".coins"); r = await page.evaluate("__grasp.habit.claimStar(7)")
        check('192 stars: the last chest pays 100 coins and a look', r and r['coins'] == 100 and r['item'] and await page.evaluate(P + ".coins") == c1 + 100, r)
        await page.evaluate("closeAlbum && closeAlbum()"); await page.evaluate(f"{A}.openMap()"); await page.wait_for_timeout(300)
        pos = await page.evaluate("[...document.querySelectorAll('.achest')].map(b => +b.dataset.stars)")
        check('the 8 chests sit on the map', pos == [10, 25, 45, 70, 100, 130, 160, 192], pos)
        tr = await page.evaluate(MU + ".tracks")
        check('music: 8 tracks; worlds 6-8 have their own tempo / key / lead (space synth, bubbly sea, candy chiptune)', len(tr) == 8 and len({(x['bpm'], x['root'], x['lead']) for x in tr}) == 8 and [x['lead'] for x in tr[5:]] == ['synth', 'bubbly', 'chip'], [x.get('name') for x in tr])
        await page.evaluate("window.__leads = []; const _ml = mLead; mLead = (k, ...a) => { __leads.push(k); return _ml(k, ...a); }; 0")
        for n, wi, lead in ((41, 6, 'synth'), (49, 7, 'bubbly'), (57, 8, 'chip')):
            await page.evaluate(f"{A}.start({n}, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play'", timeout=8000)
            await page.evaluate("__leads.length = 0")
            try: await page.wait_for_function(f"{MU}.on && {MU}.world === {wi} && __leads.length >= 3", timeout=8000); got = await page.evaluate("[...new Set(__leads)]")
            except Exception: got = await page.evaluate(f"({{ on: {MU}.on, w: {MU}.world, l: __leads.slice(0, 5), a: audio && audio.state }})")
            check(f'music: stage {n} plays world {wi}\'s loop (its lead voice "{lead}" scheduled)', got == [lead], got)
        check('A: no page errors', not errs, errs); await ctx.close()

        # ===== V: the travel 5 -> 6 (the Lava Dragon's portal leads to Space) =====
        ctx, page, errs = await fresh(b, init=prof(adv={'stars': stars(1, 39), 'unlocked': 40}))
        await page.evaluate("profile.adv.unlocked = 40; saveProfile(); setInputPref('mouse')"); await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.click('.anode[data-n="40"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 40 && {B}.b", timeout=10000)
        await page.evaluate(f"{B}.enter(); {B}.calm(true); park(); (() => {{ const b = {B}.b; while (b && b.hp > 0) {{ b.shield = null; {B}.hit('super'); }} }})()")
        await page.wait_for_function("adv.travel && adv.travel.q > 0.6", timeout=8000)
        tv = await page.evaluate("({ from: adv.travel.from, to: adv.travel.to, world: adv.world, acc: WORLDS[5].accent })")
        await page.screenshot(path=OUT + 'world6_travel.png')
        check('the Lava Dragon beaten: the portal opens to world 6 (Space), the corridor becomes world 6', tv['from'] == 5 and tv['to'] == 6 and tv['world'] == 6, tv)
        await page.wait_for_function(f"{A}.phase === 'card'", timeout=8000)
        check('...and stage 41 is open now', await page.evaluate(f"{A}.playable(41)"))
        check('V: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)

asyncio.run(main())
