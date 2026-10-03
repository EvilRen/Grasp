exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Strike Adventure: 40 fixed stages (5 worlds x 8, the 8th of each a boss stage) on a saga map. A stage's plan comes from its number alone; the goal is
# to break every wall (no more come once the plan's are out); 3 lives, 1-3 stars; coins on a first clear and for stars added on a replay; the fail
# card's Try again; the map (phone / desktop, EN / HE: nodes, stars, locks, the pulsing current stop, the star total, no sideways scroll); the Strike
# tile opens it, Endless plays the old run; the trip to the next world after a boss stage (state and pixels, 2D and 3D); the profile and the old-profile
# migration. Hooks: __grasp.adventure (plan / start / finishTest / failTest / travel / openMap ...). Timing-independent: state changes are polled.
A = "__grasp.adventure"; S = "__grasp.strike"; P = "__grasp.profile"
TOASTS = "__grasp.toasts.map(t => t.text)"
MAP = """(() => { const M = $('advMap'), sc = $('advScroll'), r = sc.getBoundingClientRect(), nodes = [...M.querySelectorAll('.anode')].map(b => { const q = b.getBoundingClientRect(), d = b.querySelector('.disc').getBoundingClientRect();
    return { n: +b.dataset.n, stars: +b.dataset.stars, on: b.querySelectorAll('.st svg.on').length, locked: b.classList.contains('locked'), lock: !!b.querySelector('.disc svg rect'), cur: b.classList.contains('cur'), boss: b.classList.contains('boss'),
      crown: !!b.querySelector('.mark'), hand: !!b.querySelector('canvas.hand'), anim: getComputedStyle(b.querySelector('.disc')).animationName, x: q.left + q.width / 2, y: q.top + q.height / 2, dw: d.width, l: q.left, rt: q.right, text: b.querySelector('.disc').textContent }; });
  const cur = nodes.find(n => n.cur), bands = [...M.querySelectorAll('.aband')].map(e => ({ w: +e.dataset.world, name: e.querySelector('.asign b').textContent }));
  return { shown: !M.hidden, nodes, bands, cur: cur ? cur.n : 0, curIn: !!cur && cur.y > r.top && cur.y < r.bottom, total: $('advStarTotal').textContent.replace(/\\s+/g, ' ').trim(), title: $('advTitle').textContent, endless: $('advEndless').textContent,
    noX: sc.scrollWidth <= sc.clientWidth + 1 && document.documentElement.scrollWidth <= innerWidth + 1 && nodes.every(n => n.l >= -1 && n.rt <= innerWidth + 1), dir: document.documentElement.dir,
    back: (() => { const b = $('advBack').getBoundingClientRect(); return { w: b.width, x: b.left + b.width / 2 }; })(), endBtn: (() => { const b = $('advEndless').getBoundingClientRect(); return b.bottom <= innerHeight + 1 && b.height >= 44; })() }; })()"""
# one stage's opening: the plan's kinds, the walls spawned at the start and their brick layouts (power-up bricks, TNT, holes)
OPENING = """(n => { __grasp.adventure.start(n); const s = __grasp.strike; return { kinds: s.walls.map(w => w.kind), lay: s.walls.map(w => w.bricks.map(k => k.tnt ? 't' : k.hole ? 'h' : k.pu ? k.pu[0] : '.').join('')), spawned: __grasp.adventure.spawned, guest: s.guestNext && [s.guestNext.at, s.guestNext.kind] }; })"""
DAILY_SEQ = """(() => { const g = __grasp, s = g.strike; g.startDaily(); s.setLevel(6); const kinds = s.walls.map(w => w.kind); while (kinds.length < 10) kinds.push(s.spawnWall().kind); const r = [g.strikeRand('serve'), g.strikeRand('guest')]; return { kinds, r }; })()"""
DOWN = "(() => { const s = __grasp.strike, w = s.walls.slice().sort((a, b) => a.z - b.z)[0]; if (w) wallDown(w, performance.now()); return s.walls.length; })()"  # the nearest wall knocked out at once

async def fresh(b, mobile=False, he=False, init='', gfx=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + (f"window.__graspGfx = {gfx};" if gfx else '') + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(700)
    return ctx, page, errs

async def tap(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

async def press(page, key):  # press a card button (a tap on the canvas at its centre) once the card is up and armed
    await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.{key} && performance.now() - {S}.overAt > 600", timeout=10000)
    r = await page.evaluate(f"{S}.ui.buttons.{key}")
    await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)

async def play_stage(page, n):  # start stage n in a running game (the mouse), wait for its walls
    await page.evaluate(f"{A}.start({n})")
    await page.wait_for_function(f"{A}.on && {A}.stage === {n} && {A}.phase === 'play' && {S}.walls.length > 0", timeout=8000)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the plans: 40 stages, deterministic, ramping; each world brings its kinds in; boss stages ----
        ctx, page, errs = await fresh(b)
        plans = await page.evaluate(f"Array.from({{ length: {A}.count }}, (_, i) => {A}.plan(i + 1))")
        again = await page.evaluate(f"(() => {{ Math.random = () => 0.5; return Array.from({{ length: 40 }}, (_, i) => {A}.plan(i + 1)); }})()")
        check('40 stages (5 worlds x 8), 3 lives a stage', len(plans) == 40 and await page.evaluate(A + ".perWorld") == 8 and await page.evaluate(A + ".lives") == 3)
        check('plan(n) is deterministic (the same with Math.random poisoned)', plans == again)
        walls = [q['walls'] for q in plans]
        check('stage 1: 4 walls, all brick, 1 hp', plans[0]['walls'] == 4 and plans[0]['kinds'] == ['brick'] * 4 and plans[0]['hp'] == 1, plans[0])
        check('walls ramp: never fewer within a world (boss stages aside), 10 at most, ~10 by world 5', all(walls[i] <= walls[i + 1] for w in range(5) for i in range(w * 8, w * 8 + 6)) and max(walls) == 10 and min(walls[32:39]) >= 8 and walls[0] == 4, walls)
        bosses = [q['n'] for q in plans if q['boss']]
        check('the 8th stage of each world is its boss stage (fewer walls, then the boss)', bosses == [8, 16, 24, 32, 40] and all(plans[n - 1]['walls'] < plans[n - 2]['walls'] for n in bosses), bosses)
        intro = {}
        for q in plans:
            for i, k in enumerate(q['kinds']):
                if k not in intro: intro[k] = (q['n'], i)
        check('kinds by world: brick from 1; glass at stage 9, steel 17, holed 25, moving 27, TNT 33, each as its stage\'s second wall', intro == {'brick': (1, 0), 'glass': (9, 1), 'steel': (17, 1), 'holed': (25, 1), 'moving': (27, 1), 'tnt': (33, 1)}, intro)
        allowed = {1: {'brick'}, 2: {'brick', 'glass'}, 3: {'brick', 'glass', 'steel'}, 4: {'brick', 'glass', 'steel', 'holed', 'moving'}, 5: {'brick', 'glass', 'steel', 'holed', 'moving', 'tnt'}}
        check('a stage only uses what its world has', all(set(q['kinds']) <= allowed[q['world']] and len(q['kinds']) == q['walls'] for q in plans))
        lv = [q['level'] for q in plans]; hp = [q['hp'] for q in plans]
        check('difficulty ramps: the tuning level climbs (world 1: 1..6, the boss stage at 6; world 5 up to 30), brick hp 1 -> 4', lv == sorted(lv) and lv[0] == 1 and lv[7] == 6 and lv[39] == 30 and hp == sorted(hp) and hp[0] == 1 and hp[39] == 4, [lv, hp])
        check('power-up bricks from stage 3 (rare), the cow from stage 2, the monkey and bending serves from world 2, S-wobbles from world 4',
              [q['pu'] > 0 for q in plans[:3]] == [False, False, True] and all(0 < q['pu'] <= 0.4 for q in plans[2:]) and [q['guests'] for q in plans[:2]] == [False, True]
              and [q['monkey'] for q in plans[7:9]] == [False, True] and plans[8]['curve'] and not plans[7]['curve'] and plans[24]['wobble'] and not plans[23]['wobble'])
        await page.reload(); await page.wait_for_timeout(500)
        check('...and the same after a reload', await page.evaluate(f"Array.from({{ length: 40 }}, (_, i) => {A}.plan(i + 1))") == plans)
        check('plans: no page errors', not errs, errs); await ctx.close()

        # ---- a stage plays its plan: seeded (a retry is the same), the daily's sequence untouched; the road does not gate it; no perks ----
        ctx, page, errs = await fresh(b)
        d0 = await page.evaluate(DAILY_SEQ)
        await page.evaluate("goHome()"); await page.evaluate(f"{P}.adv.unlocked = 40; __grasp.setPlayerLevel(1)")
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen")
        await page.click('.anode[data-n="25"]'); await page.wait_for_function(f"{A}.on && {A}.stage === 25 && mode === 'mouse' && {S}.walls.length", timeout=8000)
        o1 = await page.evaluate(OPENING + "(25)")
        await page.evaluate("Math.random = () => 0.5")
        o2 = await page.evaluate(OPENING + "(25)")
        plan25 = await page.evaluate(A + ".plan(25)")
        check('a stage opens on its plan\'s first 4 walls (stage 25: brick, then the new holed wall) even at player level 1 (the road does not gate it)', o1['kinds'] == plan25['kinds'][:4] and o1['spawned'] == 4 and o1['kinds'][1] == 'holed', o1)
        check('a retry replays the same bricks, power-ups and guest schedule (seeded per stage; Math.random poisoned changes nothing)', o1 == o2, [o1, o2])
        o3 = await page.evaluate(OPENING + "(24)")
        check('another stage: another layout', o3['lay'] != o1['lay'])
        pc = await page.evaluate(f"({{ perks: {S}.pacing.perks, offer: {S}.offerPerks(), guests: {S}.pacing.guests }})")
        check('no perk picks in a stage (none open, an offer gives nothing); world 3+: both flying guests', pc['perks'] == [] and not pc['offer'] and sorted(pc['guests']) == ['cow', 'monkey'], pc)
        await page.evaluate("goHome()")
        d1 = await page.evaluate(DAILY_SEQ)
        check('the daily\'s seeded sequence is the same before and after Adventure stages (its channels untouched)', d0 == d1, [d0, d1])
        check('seeding: no page errors', not errs, errs); await ctx.close()

        # ---- the goal: break every wall; no more come; HUD pips; the stars rule; coins (first clear vs replay); fail + Try again; Next; Map ----
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate("__grasp.setPlayerLevel(60)")  # (no level-up coins in the way of the coin checks)
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen")
        mp = await page.evaluate(MAP)
        check('fresh profile: stage 1 is the current stop, everything else locked', mp['cur'] == 1 and [n['n'] for n in mp['nodes'] if not n['locked']] == [1], mp['cur'])
        await page.click('#advPath .anode[data-n="2"]', force=True)  # (aria-disabled: Playwright would wait for it to be enabled)
        check('a locked stop: a toast, the map stays, nothing starts', await page.evaluate(A + ".mapOpen") and await page.evaluate("mode") == 'none' and any('Clear stage 1 first' in x for x in await page.evaluate(TOASTS)))
        await page.click('#advPath .anode[data-n="1"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 1 && mode === 'mouse' && {S}.walls.length === 4", timeout=8000)
        await page.wait_for_function(f"{S}.ui.advPill", timeout=4000)
        h0 = await page.evaluate(f"({{ pill: {S}.ui.advPill.text, pips: {S}.ui.advPips || null, parts: {S}.ui.hudParts, goal: {S}.goal, lives: {S}.lives, banner: !!{S}.ui.levelBanner && {S}.ui.levelBanner.stage, map: {A}.mapOpen }})")
        check('a stop on the map starts its stage: the map goes, 3 hearts, HUD "0/4" pill (minimal HUD: hearts + pill, no wall pips), the "Stage 1" banner', h0['pill'].endswith('0/4') and h0['pips'] is None and h0['parts'] == ['hearts', 'walls'] and h0['goal'] == 4 and h0['lives'] == 3 and h0['banner'] == 1 and not h0['map'], h0)
        await page.evaluate(f"{S}.balls.length = 0; {S}.waiting = false; {S}.serveAt = performance.now() + 60000")
        await page.evaluate("loseLife(performance.now())")
        c0 = await page.evaluate(P + ".coins")
        await page.evaluate(DOWN)
        await page.wait_for_function(f"{S}.ui.advPill.text.endsWith('1/4')", timeout=4000)
        st1 = await page.evaluate(f"({{ walls: {S}.walls.length, spawned: {A}.spawned }})")
        check('a wall down: 3 walls left, no replacement spawns (4 of 4 out), the pill counts it (1/4)', st1['walls'] == 3 and st1['spawned'] == 4, st1)
        await page.evaluate(DOWN); await page.evaluate(DOWN)
        mid = await page.evaluate(f"({{ walls: {S}.walls.length, prog: {S}.progress, phase: {A}.phase, spawned: {A}.spawned, coins: {P}.coins }})")
        check('walls down pay no coins in a stage; the last one standing is all that is left', mid['walls'] == 1 and mid['prog'] == 3 and mid['phase'] == 'play' and mid['spawned'] == 4 and mid['coins'] == c0, mid)
        await page.evaluate(f"(() => {{ const s = {S}; s.serveAt = 0; s.smashTest('super'); }})()")  # the last wall: a real SUPER smash in play
        await page.wait_for_function(f"{A}.phase !== 'play'", timeout=6000)
        r = await page.evaluate(A + ".result")
        check('the last wall clears the stage: one life lost = 2 stars; a first clear pays 3 + 2 coins', await page.evaluate(A + ".phase") == 'clear' and r['clear'] and r['stars'] == 2 and r['first'] and r['coins'] == 5 and await page.evaluate(P + ".coins") == c0 + 5, r)
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.advStars && {S}.ui.advStars.shown === 2", timeout=8000)
        card = await page.evaluate(f"({{ b: Object.keys({S}.ui.buttons), stars: {A}.stars, unl: {A}.unlocked, nw: {S}.walls.length }})")
        check('the clear card: the 2 stars flew in; Next / Try again / Map; stage 2 unlocked, stars saved; still no wall spawned', card['b'] == ['next', 'retry', 'map'] and card['stars'] == {'1': 2} and card['unl'] == 2 and card['nw'] == 0, card)
        await page.screenshot(path='tests/out/adv_clear_card.png')
        # replays: only the stars added pay (1 each); stars never go down
        res = []
        for lost in (0, 0, 2):
            await press(page, 'retry'); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 1 && !{S}.over", timeout=6000)
            c = await page.evaluate(P + ".coins"); rr = await page.evaluate(f"{A}.finishTest({lost})")
            res.append((rr['stars'], rr['coins'], await page.evaluate(P + ".coins") - c, await page.evaluate(A + ".stars")['1'] if False else await page.evaluate(f"{A}.stars[1]")))
        check('Try again replays the stage; replays pay only the stars added (2 -> 3 stars: +1; 3 again: 0; 1 star: 0) and the best stays 3', res == [(3, 1, 1, 3), (3, 0, 0, 3), (1, 0, 0, 3)], res)
        await press(page, 'next'); await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 2 && {S}.walls.length", timeout=6000)
        check('Next plays the next stage at once', await page.evaluate(f"{A}.stage") == 2)
        # fail: So close + Try again
        await page.evaluate(f"{S}.balls.length = 0; {S}.waiting = false; {S}.serveAt = performance.now() + 60000")
        await page.evaluate(DOWN); await page.evaluate(DOWN)
        kinds0 = await page.evaluate(f"{A}.plan(2).kinds")
        fr = await page.evaluate(A + ".failTest()")
        await page.wait_for_function(f"{S}.over && {S}.ui.advWalls && {S}.ui.buttons && {S}.ui.buttons.retry", timeout=6000)
        fc = await page.evaluate(f"({{ b: Object.keys({S}.ui.buttons), walls: {S}.ui.advWalls, txt: [I18N.en.soClose, I18N.en.wallsOf], unl: {A}.unlocked, st: {A}.stars[2] || 0 }})")
        check('losing the 3 lives: the fail card ("So close!", 2 of 4 walls lit), Try again (big) and Map; nothing unlocked, no stars', not fr['clear'] and fr['cleared'] == 2 and fr['walls'] == 4 and fc['b'] == ['retry', 'map'] and fc['walls']['cleared'] == 2 and sum(1 for q in fc['walls']['pips'] if q['on']) == 2 and fc['unl'] == 2 and fc['st'] == 0, [fr, fc])
        await page.screenshot(path='tests/out/adv_fail_card.png')
        rb = await page.evaluate(f"{S}.ui.buttons.retry"); nb = await page.evaluate(f"{S}.ui.buttons.map")
        check('fail card: Try again is the big one', rb['w'] > nb['w'] * 0.99 and rb['h'] > nb['h'], [rb, nb])
        await press(page, 'retry')
        await page.wait_for_function(f"{A}.phase === 'play' && {A}.stage === 2 && !{S}.over && {S}.walls.length === 4", timeout=6000)
        rs = await page.evaluate(f"({{ lives: {S}.lives, prog: {S}.progress, lost: {A}.lost, kinds: {S}.walls.map(w => w.kind) }})")
        check('Try again: the same stage at once, 3 hearts, nothing broken yet', rs['lives'] == 3 and rs['prog'] == 0 and rs['lost'] == 0 and rs['kinds'] == kinds0[:4], rs)
        await page.evaluate(A + ".failTest()"); await press(page, 'map')
        await page.wait_for_function(A + ".mapOpen", timeout=4000)
        mm = await page.evaluate(MAP)
        check('the card\'s Map: the map over the game, stage 2 current (stage 1 with its 3 stars)', mm['cur'] == 2 and mm['nodes'][0]['on'] == 3 and await page.evaluate("mode") == 'mouse', mm['cur'])
        await page.click('#advBack'); await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000)
        check('Back from the map in a game: home', not await page.evaluate(A + ".mapOpen") and not await page.evaluate(A + ".on"))
        check('stages: no page errors', not errs, errs); await ctx.close()

        # ---- the map on phones and a desktop, EN and HE ----
        for mobile, he, name in ((True, False, 'phone_en'), (True, True, 'phone_he'), (False, False, 'desktop')):
            stars = "{1:3,2:3,3:2,4:1,5:3,6:2,7:3,8:3,9:2,10:1,11:3}"
            ctx, page, errs = await fresh(b, mobile, he, init=f"if (!sessionStorage.getItem('s')) {{ sessionStorage.setItem('s', '1'); localStorage.setItem('grasp.profile', JSON.stringify({{ v: 1, coins: 0, xp: 0, adv: {{ stars: {stars}, unlocked: 12 }} }})); }}")
            await tap(page, mobile, '.modes button[data-mode=strike]')
            await page.wait_for_function(A + ".mapOpen"); await page.wait_for_timeout(500)
            m = await page.evaluate(MAP)
            nd = {n['n']: n for n in m['nodes']}
            check(name + ': the Strike tile opens the map (40 stops, 5 world bands named, the game not started)', m['shown'] and len(m['nodes']) == 40 and [x['w'] for x in m['bands']] == [1, 2, 3, 4, 5] and await page.evaluate("mode") == 'none', len(m['nodes']))
            check(name + ': stars under each stop as saved, numbers on the open ones, locks on the rest', [nd[n]['on'] for n in range(1, 13)] == [3, 3, 2, 1, 3, 2, 3, 3, 2, 1, 3, 0] and nd[5]['text'] == '5' and all(nd[n]['locked'] and nd[n]['lock'] for n in range(13, 41)) and not any(nd[n]['locked'] for n in range(1, 13)))
            check(name + ': the current stop (12) pulses, with the hand on it, scrolled into view', m['cur'] == 12 and nd[12]['hand'] and nd[12]['anim'] == 'apulse' and m['curIn'], [m['cur'], nd[12]['anim'], m['curIn']])
            check(name + ': boss stops (8, 16 ...) are bigger, with a crown', all(nd[n]['boss'] and nd[n]['crown'] for n in (8, 16, 24, 32, 40)) and nd[8]['dw'] > nd[7]['dw'] * 1.15, [nd[8]['dw'], nd[7]['dw']])
            check(name + ': the star total in the header (26 / 120)', m['total'].replace(' ', '') == '26/120', m['total'])
            check(name + ': no sideways scroll, every stop inside the screen, Back and Endless reachable', m['noX'] and m['back']['w'] >= 44 and m['endBtn'], m['noX'])
            check(name + ': the path winds (stops left and right of the middle) and climbs (stage 2 above stage 1)', nd[2]['y'] < nd[1]['y'] and max(n['x'] for n in m['nodes']) - min(n['x'] for n in m['nodes']) > (120 if mobile else 300))
            if he: check(name + ': RTL, Hebrew title / names / Endless; the path mirrored', m['dir'] == 'rtl' and m['title'] == 'הרפתקה' and m['bands'][1]['name'] == 'גן הזכוכית' and 'אינסופי' in m['endless'] and nd[2]['x'] < 180, [m['title'], nd[2]['x']])
            else: check(name + ': English title and names', m['title'] == 'Adventure' and m['bands'][1]['name'] == 'Glass Garden' and 'Endless' in m['endless'] and (nd[2]['x'] > 180 if mobile else nd[2]['x'] > 640))
            await page.screenshot(path='tests/out/adv_map_' + name + '.png')
            if name == 'phone_en':
                await page.evaluate("$('advScroll').scrollTop = 0"); await page.wait_for_timeout(150); await page.screenshot(path='tests/out/adv_map_phone_top.png')
            if name == 'desktop':  # a 2-star stage's replay from the map; Escape closes it
                await page.evaluate(f"{A}.openMap()"); await page.click('#advPath .anode[data-n="3"]')
                await page.wait_for_function(f"{A}.on && {A}.stage === 3 && mode === 'mouse'", timeout=8000)
                check(name + ': an open (played) stop replays its stage', await page.evaluate(f"{A}.stage") == 3)
                await page.evaluate(f"goHome(); {A}.openMap()"); await page.keyboard.press('Escape')
                check(name + ': Escape closes the map', not await page.evaluate(A + ".mapOpen"))
            check(name + ': no page errors', not errs, errs); await ctx.close()

        # ---- Endless: the old run, exactly as before ----
        ctx, page, errs = await fresh(b)
        await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless')
        await page.wait_for_function(f"mode === 'mouse' && gameMode === 'strike' && {S}.walls.length === 4", timeout=8000)
        en = await page.evaluate(f"({{ on: {A}.on, level: {S}.level, goal: {S}.goal, lives: {S}.lives, gate: {S}.gate, map: {A}.mapOpen, pill: {S}.ui.advPill }})")
        await page.evaluate(DOWN); await page.wait_for_timeout(100)
        en['after'] = await page.evaluate(f"({{ walls: {S}.walls.length, prog: {S}.progress }})")
        check('Endless: the old run (level 1, goal 4 walls of the level, the world-1 gate, the walls pill not the stage pill), and a broken wall is replaced', not en['on'] and en['level'] == 1 and en['goal'] == 4 and en['gate'] == 6 and not en['map'] and en['pill'] is None and en['after'] == {'walls': 4, 'prog': 1}, en)
        await page.evaluate(f"goHome(); __grasp.worlds.unlocked = 2")
        await page.click('.modes button[data-mode=strike]'); await page.click('#advEndless'); await page.wait_for_timeout(200)
        check('Endless with a second world open: the old world map, as before', await page.evaluate("!$('worldMap').hidden && mode === 'none'") and not await page.evaluate(A + ".mapOpen"))
        await page.click('#wmap .wnode[data-world="2"]'); await page.wait_for_function(f"mode === 'mouse' && {S}.walls.length", timeout=8000)
        check('...and its world 2 checkpoint start', await page.evaluate(f"{S}.level") == 7 and not await page.evaluate(A + ".on"))
        mg = await page.evaluate(f"({{ unl: {A}.unlocked, open: {A}.open, play9: {A}.playable(9) }})")
        check('a world open in Endless keeps its first stage open on the map', mg['play9'] and mg['open'] == [9], mg)
        check('endless: no page errors', not errs, errs); await ctx.close()

        # ---- world travel after a boss stage: 2D (state + pixels), then the map rising to the new world's first stop ----
        ctx, page, errs = await fresh(b, True)
        await page.evaluate(f"{P}.adv.unlocked = 8"); await tap(page, True, '.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen")
        await tap(page, True, '#advPath .anode[data-n="8"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 8 && {S}.walls.length", timeout=8000)
        bs = await page.evaluate(f"(() => {{ const s = {S}; s.balls.length = 0; s.waiting = false; s.serveAt = performance.now() + 60000; const n = {A}.plan(8).walls; for (let i = 0; i < n; i++) {{ const w = s.walls.slice().sort((a, b) => a.z - b.z)[0]; if (w) wallDown(w, performance.now()); }} return {{ boss: !!s.boss, phase: {A}.phase, walls: s.walls.length, spawned: {A}.spawned, next: s.next }}; }})()")
        check('a boss stage: its last wall brings the boss (no walls behind it), the stage not clear yet', bs['boss'] and bs['phase'] == 'play' and bs['walls'] == 0, bs)
        await page.evaluate(f"(() => {{ const b = {S}.boss; b.hp = 1; {S}.bossHit('hard'); }})()")
        tr = await page.evaluate(f"({{ phase: {A}.phase, travel: {A}.travel, r: {A}.result, world: {S}.world }})")
        check('the boss down clears the stage and sets off the trip to world 2', tr['phase'] == 'clear' and tr['travel'] and tr['travel']['from'] == 1 and tr['travel']['to'] == 2 and tr['r']['boss'] and tr['world'] == 1, tr)
        await page.wait_for_function(f"{A}.travel && {A}.travel.q > 0.2 && {A}.travel.q < 0.4", timeout=8000, polling=30)
        v = await page.evaluate("vanish()"); px = await page.evaluate(f"[0, 1, 2, 3, 4, 5, 6, 7].map(i => {S}.pixel({v['x']} + 62 * Math.cos(i * 0.785 + 0.3), {v['y']} + 62 * Math.sin(i * 0.785 + 0.3)))")
        await page.screenshot(path='tests/out/adv_travel_portal.png')
        check('the portal: the far end glows in the next world\'s mint (bright, green over red, round the centre)', sum(1 for q in px if sum(q) > 330 and q[1] > q[0] + 20) >= 5, px)
        await page.wait_for_function(f"{A}.travel && {A}.travel.switched && {A}.travel.q > 0.62", timeout=8000, polling=30)
        await page.screenshot(path='tests/out/adv_travel_banner.png')
        check('past the midpoint: the corridor is world 2\'s', await page.evaluate(S + ".world") == 2 and bool(await page.evaluate(f"{S}.ui.travelBox")))
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card'", timeout=8000)
        await page.wait_for_timeout(300)
        fl = await page.evaluate("(() => { const c = document.createElement('canvas'); c.width = innerWidth; c.height = innerHeight; drawCorridor(c.getContext('2d'), 2); const d1 = c.getContext('2d').getImageData(20, innerHeight - 30, 1, 1).data; drawCorridor(c.getContext('2d'), 1); const d2 = c.getContext('2d').getImageData(20, innerHeight - 30, 1, 1).data; return [[...d1].slice(0, 3), [...d2].slice(0, 3)]; })()")
        lt = await page.evaluate(A + ".lastTravel")
        check('after the trip: the card, world 2 for good (its floor is not world 1\'s)', lt and lt['from'] == 1 and lt['to'] == 2 and await page.evaluate(S + ".world") == 2 and fl[0] != fl[1], [lt, fl])
        await page.screenshot(path='tests/out/adv_travel_card.png')
        await press(page, 'next')
        await page.wait_for_function(f"{A}.mapOpen && document.querySelector('#advPath .anode[data-n=\"9\"].pop')", timeout=8000, polling=50)
        pop = await page.evaluate("(() => { const sc = $('advScroll').getBoundingClientRect(), b = document.querySelector('#advPath .anode[data-n=\"9\"]').getBoundingClientRect(); return { inView: b.top > sc.top && b.bottom < sc.bottom, cur: document.querySelector('#advPath .anode.cur').dataset.n }; })()")
        check('Next after a world\'s boss: the map rises to the new world\'s first stop, which pops open (and is the current one)', pop['inView'] and pop['cur'] == '9', pop)
        await page.wait_for_timeout(500); await page.screenshot(path='tests/out/adv_map_after_travel.png')
        await tap(page, True, '#advPath .anode[data-n="9"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 9 && {S}.walls.length", timeout=8000)
        await page.wait_for_function(f"{A}.seen.includes('glass')", timeout=15000)
        sp = await page.evaluate(f"({{ world: {S}.world, banner: {S}.ui.levelBanner && {S}.ui.levelBanner.world, spot: {S}.lastSpot && {S}.lastSpot.id, road: __grasp.road.unlocked('glass') }})")
        check('stage 9 in world 2 ("World 2" banner); its glass wall gets the spotlight the first time (not unlocked on the road)', sp['world'] == 2 and sp['spot'] == 'glass' and not sp['road'], sp)
        check('travel 2D: no page errors', not errs, errs); await ctx.close()

        # ---- world travel on the WebGL renderer: the 3D corridor re-themes, no errors ----
        ctx, page, errs = await fresh(b, gfx="{ pr: 0.12, shadows: false, auto: false }")
        await page.evaluate(f"{P}.adv.unlocked = 16"); await page.click('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen")
        await page.click('#advPath .anode[data-n="16"]')
        try: await page.wait_for_function(f"{S}.gfx === '3d' && {A}.stage === 16 && {S}.walls.length", timeout=25000); g3 = True
        except Exception: g3 = False
        check('3D: the renderer is up for a stage', g3, await page.evaluate(f"{S}.gfxInfo"))
        if g3:
            await page.evaluate(f"{A}.finishTest(0)")
            await page.wait_for_function(f"{A}.travel && {A}.travel.switched", timeout=10000)
            await page.wait_for_timeout(200)
            th = await page.evaluate(f"({{ shown: G3.worldShown, world: {S}.world, gfx: {S}.gfx }})")
            await page.screenshot(path='tests/out/adv_travel_3d.png')
            check('3D: past the midpoint the WebGL corridor shows world 3', th == {'shown': 3, 'world': 3, 'gfx': '3d'}, th)
            await page.wait_for_function(f"{S}.over && {A}.phase === 'card'", timeout=10000)
            check('3D: the card after the trip', await page.evaluate(f"{S}.gfx") == '3d')
        check('travel 3D: no page errors', not errs, errs); await ctx.close()

        # ---- persistence: the stars and the frontier survive a reload; an old profile keeps its worlds; broken data is cleaned ----
        ctx, page, errs = await fresh(b)
        await page.evaluate(f"{P}.adv.unlocked = 3"); await page.click('.modes button[data-mode=strike]'); await page.click('#advPath .anode[data-n="3"]')
        await page.wait_for_function(f"{A}.on && {A}.stage === 3", timeout=8000); await page.evaluate(f"{A}.finishTest(1)")
        await page.reload(); await page.wait_for_timeout(500)
        pr = await page.evaluate(f"({{ stars: {A}.stars, unl: {A}.unlocked, total: {A}.total, raw: JSON.parse(localStorage.getItem('grasp.profile')).adv }})")
        check('the stars and the unlocked stage are saved in the profile and survive a reload', pr['stars'] == {'3': 2} and pr['unl'] == 4 and pr['total'] == 2 and pr['raw']['stars'] == {'3': 2} and pr['raw']['unlocked'] == 4, pr)
        check('persistence: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, True, init="if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 70, xp: 900, worlds: { unlocked: 3, last: 3 } })); }")
        old = await page.evaluate(f"({{ unl: {A}.unlocked, open: {A}.open, p: [1, 2, 9, 10, 17, 18].map(n => {A}.playable(n)), cur: {A}.current, coins: {P}.coins, worlds: {P}.worlds.unlocked }})")
        check('an old profile with worlds 1-3 open (no Adventure data): stages 1, 9 and 17 open, the furthest (17) current; nothing else lost', old['unl'] == 1 and old['open'] == [9, 17] and old['p'] == [True, False, True, False, True, False] and old['cur'] == 17 and old['coins'] == 70 and old['worlds'] == 3, old)
        await tap(page, True, '.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen"); await page.wait_for_timeout(300)
        m = await page.evaluate(MAP); nd = {n['n']: n for n in m['nodes']}
        check('...and its map: stops 1, 9, 17 open, 17 current', [n for n in nd if not nd[n]['locked']] == [1, 9, 17] and m['cur'] == 17 and m['curIn'], m['cur'])
        await tap(page, True, '#advPath .anode[data-n="9"]'); await page.wait_for_function(f"{A}.on && {A}.stage === 9", timeout=8000)
        await page.evaluate(f"{A}.finishTest(0)")
        check('clearing an open stop past the gap opens the one after it', await page.evaluate(f"{A}.playable(10) && !{A}.playable(11)"))
        check('old profile: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, init="if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s', '1'); localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, adv: { stars: { 1: 3, 2: 9, abc: 2, 50: 1, 3: 1.5, 4: '2' }, unlocked: 'x', open: [5, 'q', 99], seen: ['glass', 'lava'] } })); }")
        bad = await page.evaluate(f"({{ stars: {A}.stars, unl: {A}.unlocked, open: {A}.open, seen: {A}.seen }})")
        check('broken Adventure data is cleaned on load (bad stars, stage numbers and kinds dropped)', bad == {'stars': {'1': 3}, 'unl': 1, 'open': [5], 'seen': ['glass']}, bad)
        check('broken profile: no page errors', not errs, errs); await ctx.close()

        # ---- strings: every new key in EN and HE; Grippy's new lines ----
        ctx, page, errs = await fresh(b)
        keys = ['advTitle', 'back', 'endless', 'endlessSub', 'advBoss', 'advStarsN', 'advLockedAria', 'advLocked', 'stageN', 'stageGoal', 'stageGoalBoss', 'stageClear', 'worldClear', 'soClose', 'wallsOf', 'nextBtn', 'retryBtn', 'mapBtn', 'advBest', 'advWaveNext', 'advWaveRetry']
        miss = await page.evaluate("(ks => ['en', 'he'].flatMap(l => ks.filter(k => !I18N[l][k] || (l === 'he' && I18N.he[k] === I18N.en[k])).map(k => l + ':' + k)))(" + json.dumps(keys) + ")")
        check('I18N: every Adventure string in EN and HE (HE translated)', not miss, miss)
        gl = await page.evaluate("['advClear', 'advPerfect', 'advFail'].map(e => [__grasp.grippy.lines.en[e].length, __grasp.grippy.lines.he[e].length])")
        check('Grippy: 6 lines each for a clear, a perfect clear and a fail, EN and HE', gl == [[6, 6]] * 3, gl)
        check('strings: no page errors', not errs, errs); await ctx.close()

        await b.close()
    print('FAILURES:', check.fails)
    srv.terminate()
    if check.fails: sys.exit(1)
asyncio.run(main())
