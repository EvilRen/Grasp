exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# Smash, rebuilt: five scenes of breakable Matter things (the revealing brick wall, a room, a city, toy towers, a fruit market); the Smash tile opens
# its map (Free play + 20 stages); mouse / touch: a tap is a punch at that point, a swipe a sweeping hit (strength by speed); the camera: any contact.
# This suite: the map, each scene's build, every thing's own break sound, debris (cap, fade, pool), chain reactions, the meter -> next scene in
# free play, the pause sheet, mouse / touch / camera punches. Stages, stars, the profile, voice and the screenshots: test_smash2.py.
FIST_JS = """
window.mkFist = (cx, cy) => { // all four fingertips curled back toward the wrist, thumb away from the index tip (no pinch)
  const L = Array.from({length:21}, () => ({x: cx, y: cy + 0.10, z: 0}));
  L[0] = {x: cx, y: cy + 0.30, z:0}; L[9] = {x: cx, y: cy + 0.10, z:0}; L[4] = {x: cx - 0.14, y: cy + 0.16, z:0};
  for (const [tip, pip] of [[8,6],[12,10],[16,14],[20,18]]) { L[pip] = {x: cx + 0.02, y: cy + 0.02, z:0}; L[tip] = {x: cx + 0.02, y: cy + 0.14, z:0}; }
  return L;
};
window.fistAt = (X, Y) => { const B = __grasp.CONFIG.MAP_BOX, m = (1 - B) / 2; return mkFist(1 - (m + X / innerWidth * B), m + Y / innerHeight * B); };
window.sweep = (fn, x0, y0, x1, y1, ms) => { const t0 = performance.now(); window.__handFor = () => { const k = Math.min(1, (performance.now() - t0) / ms); return fn(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k); }; };
"""
GEST_JS = """window.__gest = (keys, o) => new Promise(res => { o = o || {}; const type = o.type || 'mouse', id = type === 'touch' ? 11 : 1; let t0 = null, k = 0;
  const fire = (kind, x, y, tg) => (tg || window).dispatchEvent(new PointerEvent(kind, { clientX: x, clientY: y, pointerType: type, pointerId: id, isPrimary: true, bubbles: true, cancelable: true, button: kind === 'pointermove' ? -1 : 0, buttons: o.down ? 1 : 0 }));
  if (o.down) fire('pointerdown', keys[0][1], keys[0][2], canvas);
  const step = (ts) => { if (t0 === null) t0 = ts; const t = ts - t0; while (k < keys.length - 1 && keys[k + 1][0] <= t) k++;
    let x, y; if (k >= keys.length - 1) { x = keys[keys.length - 1][1]; y = keys[keys.length - 1][2]; } else { const a = keys[k], b = keys[k + 1], q = (t - a[0]) / (b[0] - a[0]); x = a[1] + (b[1] - a[1]) * q; y = a[2] + (b[2] - a[2]) * q; }
    fire('pointermove', x, y);
    if (t >= keys[keys.length - 1][0]) { if (o.up) fire('pointerup', x, y, canvas); res(); return; } requestAnimationFrame(step); };
  requestAnimationFrame(step); });"""
# the speech stub (as in test_grippy): records every utterance
SPEECH = ("window.__spoken = []; try { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang }); setTimeout(() => { try { u.onend && u.onend(); } catch (e) {} }, 300); }, cancel() {}, getVoices() { return [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]; } };"
          " Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ss }); } catch (e) {}")
S = "__grasp.smash"; SM = "__grasp.sm"
# the front tile wall's cell at a screen point (index, alive) and how many cells are out
CELL = "((x, y) => { const T = __grasp.sm.tiles.find(q => q.layer === 0); const r = Math.floor((y - T.y0) / T.ch), off = T.stagger && r % 2 ? T.cw / 2 : 0, c = Math.floor((x - T.x0 + off) / T.cw), i = r * T.nc + c; return { i, alive: T.cells[i] === 1, out: T.total - T.alive }; })"
TOTAL = "(() => { let n = 0; for (const T of __grasp.sm.tiles) n += T.total - T.alive; return n + __grasp.sm.objs.filter(o => !o.alive).length; })()"  # everything smashed so far (tiles + things)
OUT0 = "(() => { const T = __grasp.sm.tiles.find(q => q.layer === 0); return T ? T.total - T.alive : -1; })()"
SOUNDS = {'window': 'glass', 'frame': 'glass', 'jar': 'glass', 'bottle': 'glass', 'plate': 'clink', 'cup': 'clink', 'vase': 'clink', 'clock': 'clink', 'plant': 'clink', 'tv': 'spark', 'ceilLamp': 'pop', 'floorLamp': 'pop',
          'shelf': 'wood', 'table': 'wood', 'cabinet': 'wood', 'book': 'swish', 'floor': 'crunch', 'car': 'car', 'streetLamp': 'pop', 'tree': 'wood', 'towerLegs': 'clang', 'tank': 'splash', 'hydrant': 'splash',
          'block': 'clack', 'balloon': 'pop', 'gift': 'confetti', 'watermelon': 'splat', 'tomato': 'splat', 'egg': 'splat', 'pumpkin': 'splat', 'orange': 'splat', 'apple': 'splat', 'crate': 'wood',
          'chest': 'confetti', 'gem': 'clink', 'trophy': 'clang'}
NEED = {'wall': ['chest', 'gem', 'trophy', 'gift', 'table', 'plate', 'cup', 'tv', 'cabinet', 'vase', 'floorLamp'],
        'room': ['window', 'frame', 'clock', 'ceilLamp', 'shelf', 'jar', 'plant', 'book', 'table', 'plate', 'cup', 'vase', 'tv', 'cabinet', 'floorLamp'],
        'city': ['floor', 'car', 'tree', 'towerLegs', 'tank', 'streetLamp', 'hydrant'], 'blocks': ['block', 'balloon', 'gift'],
        'food': ['watermelon', 'tomato', 'egg', 'pumpkin', 'crate', 'shelf', 'bottle', 'orange', 'apple']}
REST = "(() => { const o = __grasp.sm.objs; return { n: o.length, alive: o.every(q => q.alive), moving: o.filter(q => q.alive && !q.stat && q.body.speed > 0.6).map(q => q.kind + ':' + q.body.speed.toFixed(2)) }; })()"

async def fresh(b, mobile=False, he=False, init='', camera=False):
    opts = dict(viewport={'width':360,'height':740}, device_scale_factor=3, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width':1280,'height':800})
    ctx = await b.new_context(**({'permissions': ['camera']} if camera else {}), **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + FIST_JS + GEST_JS + SPEECH + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_timeout(600)
    return ctx, page, errs
async def free(page, tap=False):  # the Smash tile, then the map's Free play
    await (page.tap if tap else page.click)('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
    await (page.tap if tap else page.click)('#smashFree'); await page.wait_for_function("mode !== 'none' && __grasp.smash.run === 'free' && __grasp.sm.objs.length > 0", timeout=15000)
async def settle(page, ms=1300): await page.wait_for_timeout(ms)
async def drag(page, x0, x1, y, step=64, wait=16):
    await page.mouse.move(x0, y); await page.wait_for_timeout(120); await page.mouse.down()
    n = max(1, int(abs(x1 - x0) / step))
    for i in range(1, n + 1): await page.mouse.move(x0 + (x1 - x0) * i / n, y); await page.wait_for_timeout(wait)
    await page.mouse.up(); await page.wait_for_timeout(150)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
        # ---------------- desktop, mouse ----------------
        ctx, page, errs = await fresh(b)
        await page.click('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
        mp = await page.evaluate("""(() => { const n = [...document.querySelectorAll('#smList .smNode')]; return { path: location.pathname, mode, title: $('smTitle').textContent, free: $('smashFree').getBoundingClientRect().height > 60, nodes: n.length,
          cur: n.filter(b => b.classList.contains('cur')).map(b => b.dataset.n), locked: n.filter(b => b.classList.contains('locked')).length, scenes: [...document.querySelectorAll('#smList .smScene')].map(s => s.dataset.scene), total: $('smStarTotal').textContent.trim() }; })()""")
        check('the Smash tile opens its map at /smash: Free play on top, 20 stages in 5 scene groups (stage 1 current, the rest locked), no game running yet', mp['path'] == '/smash' and mp['mode'] == 'none' and mp['title'] == 'Smash' and mp['free'] and mp['nodes'] == 20 and mp['cur'] == ['1'] and mp['locked'] == 19 and mp['scenes'] == ['wall', 'room', 'city', 'blocks', 'food'] and mp['total'].startswith('0'), mp)
        await page.click('#smList .smNode[data-n="5"]', force=True); await page.wait_for_timeout(300)
        check('a locked stage does not start (the map stays)', await page.evaluate("__grasp.sm.mapOpen && mode === 'none'"))
        await page.keyboard.press('Escape'); await page.wait_for_function("!__grasp.sm.mapOpen && !location.pathname.startsWith('/smash')", timeout=4000)
        check('Escape closes the map back to the start screen at /', await page.evaluate("!__grasp.sm.mapOpen && !$('start').hidden && !location.pathname.startsWith('/smash')"))
        await free(page)
        st = await page.evaluate("""(() => { const v = [...document.querySelectorAll('.chrome > *')].filter(e => e.getBoundingClientRect().width > 0); return { run: __grasp.smash.run, scene: __grasp.smash.scene, phase: __grasp.smash.phase, path: location.pathname, chrome: v.map(e => e.id), tiles: __grasp.sm.tiles.map(t => [t.kind, t.layer, t.alive]), bodies: bodies.length, sleeping: engine.enableSleeping }; })()""")
        check('Free play starts on the brick wall (a full-screen brick wall in front of a tiled room wall), sandbox objects gone, resting bodies sleep', st['run'] == 'free' and st['scene'] == 'wall' and st['phase'] == 'play' and st['path'] == '/smash' and [t[:2] for t in st['tiles']] == [['tile', 1], ['brick', 0]] and st['tiles'][1][2] > 100 and st['bodies'] == 0 and st['sleeping'], st)
        check('in play the toolbar is one pause button', st['chrome'] == ['pauseBtn'], st)
        await page.wait_for_timeout(500); hud = await page.evaluate(S + ".ui.hud")
        check('the HUD is one slim pill: the destruction meter only (free play: no clock, no score, no coin pill)', hud and hud['parts'] == ['meter'] and hud['h'] <= 32 and await page.evaluate("__grasp.coinUi.box") is None, hud)
        wall = await page.evaluate("(() => { const T = __grasp.sm.tiles.find(q => q.layer === 0); return { x0: T.x0, y0: T.y0, w: T.w, h: T.h }; })()")
        check('the brick wall covers the whole screen', wall['x0'] == 0 and wall['y0'] == 0 and wall['w'] == 1280 and wall['h'] == 800, wall)
        # a click is a punch right there
        c0 = await page.evaluate(CELL + "(640, 420)")
        await page.mouse.click(640, 420); await page.wait_for_function(f"!{CELL}(640, 420).alive", timeout=3000)
        c1 = await page.evaluate(CELL + "(640, 420)")
        check('mouse: a click knocks the brick under it out (and a few around it)', c0['alive'] and not c1['alive'] and c1['out'] >= 2, [c0, c1])
        check('a brick breaks with its crunch', any(s['o'] == 'brick' and s['k'] == 'crunch' for s in await page.evaluate(SM + ".snd")))
        o0 = await page.evaluate(OUT0); await drag(page, 200, 1080, 250, step=8, wait=60)
        check('mouse: a slow drag smashes nothing along its way (only the press itself punches where it lands)', await page.evaluate(OUT0) - o0 <= 10 and (await page.evaluate(CELL + "(640, 250)"))['alive'] and (await page.evaluate(CELL + "(1000, 250)"))['alive'], [o0, await page.evaluate(OUT0)])
        await drag(page, 100, 1180, 250)
        o1 = await page.evaluate(OUT0)
        check('mouse: a fast swipe sweeps a band of bricks out along its path', o1 - o0 >= 8 and not (await page.evaluate(CELL + "(400, 250)"))['alive'] and not (await page.evaluate(CELL + "(900, 250)"))['alive'], [o0, o1])
        pc = await page.evaluate("({ n: __grasp.smash.pieces.length, dyn: __grasp.smash.pieces.every(p => !p.isStatic), moving: __grasp.smash.pieces.some(p => p.speed > 0.5), meter: __grasp.sm.meter })")
        check('knocked-out bricks fly as dynamic debris; the meter rises', pc['n'] > 0 and pc['dyn'] and pc['moving'] and 0 < pc['meter'] < 0.5, pc)
        # ---- each scene builds, rests, and holds what it should ----
        for sc in ['wall', 'room', 'city', 'blocks', 'food']:
            n = await page.evaluate(f"{SM}.build('{sc}', 2)"); await settle(page)
            k = await page.evaluate(SM + ".kinds()"); r = await page.evaluate(REST)
            miss = [q for q in NEED[sc] if not k.get(q)]
            check(f'desktop {sc}: builds with {n} things of every kind it should have', n >= 16 and not miss, [n, miss, k])
            check(f'desktop {sc}: everything rests after the build (nothing breaks by itself, nothing still moving)', r['alive'] and not r['moving'], r)
        lay = await page.evaluate(f"(() => {{ {SM}.build('wall', 1); return [...new Set({SM}.objs.map(o => o.kind + ':' + o.layer))]; }})()")
        check('the wall scene: the room\'s things behind the bricks (layer 1), the treasure behind the room\'s wall (layer 2)', 'chest:2' in lay and 'gem:2' in lay and 'tv:1' in lay and 'table:1' in lay, lay)
        # the front-most first: a punch on the wall breaks bricks, not the TV behind them
        tv = await page.evaluate(f"(() => {{ const o = {SM}.alive('tv')[0]; return {{ x: o.body.position.x, y: o.body.position.y }}; }})()")
        await page.evaluate(f"{SM}.punch({tv['x']}, {tv['y']}, 0.4)")
        check('front first: a punch where the TV stands behind the wall knocks bricks out, the TV is untouched', await page.evaluate(f"{SM}.alive('tv')[0].hp === {SM}.alive('tv')[0].maxHp") and await page.evaluate(OUT0) > 0)
        for _ in range(6): await page.evaluate(f"{SM}.punch({tv['x']}, {tv['y']}, 1)")
        check('...and once the bricks there are gone, the TV takes the hits and breaks', await page.evaluate(f"{SM}.alive('tv').length") == 0, await page.evaluate(f"{SM}.alive('tv').map(o => o.hp)"))
        # ---- every thing breaks with its own sound ----
        heard, bad = {}, []
        for sc in ['wall', 'room', 'city', 'blocks', 'food']:
            await page.evaluate(f"{SM}.build('{sc}', 3)"); await settle(page, 900)
            for kind, want in SOUNDS.items():
                got = await page.evaluate(f"(() => {{ const o = {SM}.alive('{kind}')[0]; if (!o) return null; {SM}.snd.length = 0; {SM}.breakObj(o); const s = {SM}.snd.find(q => q.o === '{kind}'); return s ? s.k : 'none'; }})()")
                if got is None: continue
                heard[kind] = got
                if got != want: bad.append((kind, got, want))
        check('every kind of thing breaks with its own sound (glass shatter, china clink, TV spark, bulb / balloon pop, splat, confetti, crunch...)', not bad and set(heard) >= set(SOUNDS), [bad, sorted(set(SOUNDS) - set(heard))])
        # ---- chain reactions: a shelf goes, its jars fall and break; a building's ground floor goes, the floors above collapse one by one; the water tower's legs go, the tank bursts ----
        await page.evaluate(f"{SM}.build('room', 1)"); await settle(page)
        jar0 = await page.evaluate(f"(() => {{ const s = {SM}.alive('shelf')[0], b = s.body.bounds, on = {SM}.objs.filter(o => o.alive && o !== s && o.body.position.y < s.body.position.y && o.body.position.x > b.min.x && o.body.position.x < b.max.x && s.body.position.y - o.body.position.y < 80); window.__on = on; {SM}.breakObj(s); return on.length; }})()")
        await page.wait_for_function("__on.filter(o => !o.alive).length >= 2", timeout=6000)
        check('chain: a broken shelf drops its jars and they smash on the floor by themselves', jar0 >= 3 and await page.evaluate("__on.filter(o => !o.alive).length") >= 2, [jar0, await page.evaluate("__on.map(o => o.kind + (o.alive ? '' : '!'))")])
        await page.evaluate(f"{SM}.build('city', 2)"); await settle(page)
        g = await page.evaluate(f"(() => {{ const fl = {SM}.alive('floor'), by = {{}}; for (const o of fl) (by[o.group] = by[o.group] || []).push(o); const g = Object.keys(by).sort((a, b) => by[b].length - by[a].length)[0]; window.__bl = by[g]; const low = by[g].reduce((a, o) => o.body.position.y > a.body.position.y ? o : a); window.__c0 = {SM}.heard.crunch || 0; {SM}.breakObj(low); return by[g].length; }})()")
        await page.wait_for_function("__bl.filter(o => !o.alive).length >= 4", timeout=8000)
        cl = await page.evaluate("({ down: __bl.filter(o => !o.alive).length, crunch: (__grasp.sm.heard.crunch || 0) - __c0 })")
        check('chain: knock out a building\'s ground floor and the floors above crash down floor by floor', g >= 5 and cl['down'] >= 4 and cl['crunch'] >= 4, [g, cl])
        await page.evaluate(f"(() => {{ window.__tank = {SM}.alive('tank')[0]; {SM}.breakObj({SM}.alive('towerLegs')[0]); }})()")
        await page.wait_for_function("!__tank.alive", timeout=5000)
        check('chain: the water tower\'s legs go, the tank falls and bursts with a splash', await page.evaluate("__grasp.sm.snd.some(s => s.o === 'tank' && s.k === 'splash')"))
        # ---- debris: capped, faded, pooled ----
        await page.evaluate(f"(() => {{ {SM}.build('food', 4); window.__pmax = 0; window.__pOn = true; (function r() {{ if (!__pOn) return; __pmax = Math.max(__pmax, __grasp.smash.pieces.length); requestAnimationFrame(r); }})(); }})()"); await settle(page, 800)
        for sc in ['food', 'blocks', 'room']:
            await page.evaluate(f"(() => {{ {SM}.build('{sc}', 4); for (const o of {SM}.alive()) {SM}.breakObj(o, 1); }})()"); await page.wait_for_timeout(250)
        await page.wait_for_timeout(400); cap = await page.evaluate(SM + ".cap"); pm = await page.evaluate("__pOn = false; __pmax"); now_n = await page.evaluate(SM + ".pieces")
        check('debris is capped (140 on a desktop; never far over it, back under it within a moment)', cap == 140 and pm <= cap * 1.25 + 1 and now_n <= cap, [cap, pm, now_n])
        await page.evaluate("__grasp.CONFIG.SMASH_PIECE_MS = 150")
        await page.wait_for_function("__grasp.sm.pieces === 0", timeout=5000)
        pool = await page.evaluate(SM + ".pool")
        check('debris fades out and goes back to its pool (no bodies left in the world)', pool > 20 and await page.evaluate("engine.world.bodies.filter(b => b.label === 'debris').length") == 0, pool)
        await page.evaluate("__grasp.CONFIG.SMASH_PIECE_MS = 3500"); await page.evaluate(f"(() => {{ {SM}.build('blocks', 1); for (const o of {SM}.alive('block').slice(0, 6)) {SM}.breakObj(o); }})()")
        check('new debris reuses pooled bodies', await page.evaluate(SM + ".pool") < pool and await page.evaluate(SM + ".pieces") > 0, [pool, await page.evaluate(SM + ".pool")])
        # ---- free play: the meter fills -> 'Smashed!' (the rest goes up), coins, then the next scene slides in ----
        await page.evaluate(f"{SM}.build('wall', 1)"); await settle(page, 600)
        c0 = await page.evaluate("__grasp.profile.coins"); await page.evaluate("__grasp.grippy.cool()")
        await page.evaluate(f"{SM}.breakTo(0.85)"); await page.wait_for_function(S + ".ui.meterBox && " + S + ".ui.meterBox.pct >= 90", timeout=3000)
        check('below the clear (85%): still playing; the meter shows 85/90', await page.evaluate(S + ".phase") == 'play' and 90 <= await page.evaluate(S + ".ui.meterBox.pct") <= 95, await page.evaluate(S + ".ui.meterBox"))
        await page.evaluate(f"{SM}.breakTo(0.91)"); await page.wait_for_function(S + ".phase === 'clear'", timeout=3000)
        await page.wait_for_function(SM + ".alive().length === 0 && " + S + ".ui.meterBox.pct === 100", timeout=4000)
        cl = await page.evaluate(f"({{ coins: __grasp.profile.coins, box: {S}.ui.clearBox, said: __grasp.grippy.last && __grasp.grippy.last.event, meter: {SM}.meter, alive: {SM}.alive().length, pct: {S}.ui.meterBox.pct }})")
        check('at 90%: "Smashed!", the meter full, everything left goes up, +6 coins, the voice cheers (smashClear)', cl['box'] and cl['box']['text'] == 'Smashed!' and cl['pct'] == 100 and cl['coins'] - c0 == 6 and cl['said'] == 'smashClear' and cl['alive'] == 0 and cl['meter'] == 1, [c0, cl])
        await page.screenshot(path='tests/out/smash2_clear_desktop_en.png')
        await page.wait_for_function(S + ".phase === 'in'", timeout=5000)
        sl = await page.evaluate(f"({{ scene: {S}.scene, slide: {S}.slide, tag: {S}.ui.tagBox }})")
        await page.wait_for_function(S + ".phase === 'play'", timeout=5000)
        nx = await page.evaluate(f"({{ scene: {S}.scene, meter: {SM}.meter, slide: {S}.slide, said: __grasp.grippy.said.map(s => s.event).slice(-2), spoken: __spoken.length }})")
        check('then the next scene (the room) slides in from the side with its name, and the voice says so (smashScene)', sl['scene'] == 'room' and sl['slide'] > 0 and nx['scene'] == 'room' and nx['meter'] < 0.05 and nx['slide'] == 0 and nx['said'] == ['smashClear', 'smashScene'], [sl, nx])
        check('free play order: wall, room, city, blocks, food, then round again', await page.evaluate("(() => { const out = []; for (let i = 0; i < 6; i++) { smFreeNext(performance.now()); out.push(__grasp.smash.scene); } return out; })()") == ['city', 'blocks', 'food', 'wall', 'room', 'city'])
        ev = await page.evaluate("__grasp.events.map(e => e[0])"); pr = await page.evaluate("__grasp.profile.stats")
        check('smashing counts for the stats and missions: bricks (bricks, tiles, blocks, floors), cars, walls (a wall or a building all the way down), things smashed', all(k in ev for k in ['brick', 'car', 'wall', 'smash']) and pr['smashed'] > 0 and pr['bricks'] > 0 and pr['cars'] > 0 and pr['walls'] > 0, [sorted(set(ev)), pr])
        # ---- the pause sheet: everything waits ----
        await page.evaluate(f"{SM}.build('blocks', 1)"); await settle(page, 600)
        await page.click('#pauseBtn'); await page.wait_for_function("menu.open && __grasp.pause.on", timeout=3000)
        sh = await page.evaluate("[...document.querySelectorAll('.chrome.open button')].filter(b => b.getBoundingClientRect().width > 0).map(b => b.id)")
        check('the pause button opens the sheet: Resume, Restart, Sound, Language, Stats, Home', all(i in sh for i in ['resumeBtn', 'resetBtn', 'muteBtn', 'hudBtn', 'homeBtn']) and len(sh) >= 6, sh)
        await page.evaluate(f"(() => {{ for (const o of {SM}.alive('block').slice(0, 3)) {SM}.breakObj(o); }})()")
        y0 = await page.evaluate("__grasp.smash.pieces.map(p => p.position.y).join()"); await page.wait_for_timeout(400); y1 = await page.evaluate("__grasp.smash.pieces.map(p => p.position.y).join()")
        check('paused: the debris hangs still (physics waits)', y0 == y1 and len(y0) > 0)
        await page.screenshot(path='tests/out/smash2_pause_desktop_en.png')
        await page.click('#resumeBtn'); await page.wait_for_function("!menu.open && !__grasp.pause.on", timeout=3000)
        await page.wait_for_timeout(200)
        check('Resume: play goes on (the debris falls again)', await page.evaluate("__grasp.smash.pieces.map(p => p.position.y).join()") != y1)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        check('Escape opens the sheet too (and again closes it)', await page.evaluate("menu.open") and (await page.keyboard.press('Escape') or True) and not await page.evaluate("menu.open"))
        await page.evaluate(f"{SM}.breakTo(0.3)"); await menu_click(page, '#resetBtn'); await page.wait_for_timeout(300)
        check('Restart (free play): the same scene afresh', await page.evaluate(f"!menu.open && {S}.scene === 'blocks' && {SM}.meter < 0.05 && {S}.run === 'free'"))
        await menu_click(page, '#homeBtn'); await page.wait_for_function("mode === 'none' && !location.pathname.startsWith('/smash')", timeout=4000)
        check('Home: the start screen at /', await page.evaluate("mode === 'none' && !$('start').hidden && !location.pathname.startsWith('/smash')"))
        await page.evaluate("__grasp.setGameMode('sandbox')"); await page.wait_for_timeout(200)
        check('leaving Smash for another game clears its things and stops the sleeping', await page.evaluate("__grasp.sm.objs.length === 0 && !engine.enableSleeping && !document.body.classList.contains('minChrome')"))
        check('desktop: no page errors', not errs, errs); await ctx.close()

        # ---------------- camera ----------------
        ctx, page, errs = await fresh(b, camera=True)
        await page.click('#camBtn'); await page.click('.modes button[data-mode=smash]'); await page.wait_for_function("__grasp.sm.mapOpen", timeout=5000)
        await page.click('#smashFree'); await page.wait_for_function("mode === 'camera' && __grasp.sm.objs.length > 0", timeout=15000)
        await page.evaluate("window.__handFor = () => fistAt(200, 300)"); await page.wait_for_timeout(700)
        check('camera: a closed fist is recognised', await page.evaluate("gesture") == 'fist', await page.evaluate("[gesture, hand.pinchD]"))
        await page.wait_for_function("!__grasp.pause.on", timeout=8000)
        o0 = await page.evaluate(OUT0); cy = await page.evaluate("cursor.y")
        await page.evaluate("sweep(fistAt, 150, 300, 1130, 300, 260)"); await page.wait_for_timeout(700)
        o1 = await page.evaluate(OUT0)
        check('camera: a fist swept across the wall knocks a band of bricks out', o1 - o0 >= 8 and not (await page.evaluate(CELL + f"(640, {cy})"))['alive'], [o0, o1, cy])
        await page.evaluate("window.__handFor = () => handAt(150, 680, 0.8)"); await page.wait_for_timeout(600)
        check('camera: an open hand punches too (kid-friendly)', await page.evaluate("gesture === 'open' && __grasp.punchGesture()"))
        o2 = await page.evaluate(TOTAL); await page.evaluate("sweep((x, y) => handAt(x, y, 0.8), 150, 680, 1130, 680, 260)"); await page.wait_for_timeout(700)
        check('camera: a fast open-hand wave smashes too', await page.evaluate(TOTAL) - o2 >= 8, [o2, await page.evaluate(TOTAL)])
        await page.evaluate("window.__handFor = () => handAt(640, 120, 0.8)"); await page.wait_for_timeout(500)
        kn = await page.evaluate("new Promise(res => { const seen = new Set(), t0 = performance.now(); let fr = 0; (function r() { fr++; seen.add(__grasp.smash.camAt); if (performance.now() - t0 < 1000) requestAnimationFrame(r); else res({ knocks: seen.size - 1, frames: fr }); })(); })")
        check('camera: a hand resting on things keeps knocking, a few times a second (not every frame)', 2 <= kn['knocks'] <= 6 and kn['frames'] > kn['knocks'] * 2, kn)
        await page.evaluate("window.__handFor = () => handAt(1000, 120, 0.1)"); await page.wait_for_timeout(500)
        o5 = await page.evaluate(TOTAL); await page.wait_for_timeout(800)
        check('camera: a pinch does not punch', await page.evaluate("gesture") == 'pinch' and await page.evaluate(TOTAL) == o5, [o5, await page.evaluate(TOTAL)])
        hint = await page.evaluate("hintText()"); hhe = await page.evaluate("(() => { setLang('he'); const h = hintText(); setLang('en'); return h; })()")
        check('camera hint (EN + HE): punch or touch things, fill the meter', hint.startswith('Punch or touch things with your hand to smash them') and hhe.startswith('תנו אגרוף או געו בדברים'), [hint, hhe])
        check('smash constants: PUNCH_SPEED 0.55 (touch 0.35), FIST_RADIUS 40, clear at 90%', await page.evaluate("__grasp.CONFIG.PUNCH_SPEED === 0.55 && __grasp.CONFIG.PUNCH_SPEED_TOUCH === 0.35 && __grasp.CONFIG.FIST_RADIUS === 40 && __grasp.CONFIG.SMASH_CLEAR === 0.9"))
        check('camera: no page errors', not errs, errs); await ctx.close()

        # ---------------- phone, touch (EN + HE) ----------------
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile=True, he=he)
            await free(page, tap=True)
            check(tag + ' phone: Free play on touch', await page.evaluate("mode === 'mouse' && __grasp.smash.scene === 'wall'"))
            await page.wait_for_timeout(400)
            c0 = await page.evaluate(CELL + "(180, 420)")
            await page.tap('#stage', position={'x': 180, 'y': 420}); await page.wait_for_function(f"!{CELL}(180, 420).alive", timeout=3000)
            check(tag + ' phone: a tap is a punch right where the finger lands', c0['alive'] and not (await page.evaluate(CELL + "(180, 420)"))['alive'])
            o0 = await page.evaluate(OUT0)
            await page.evaluate("__gest([[0, 20, 600], [60, 20, 600], [260, 340, 600], [300, 340, 600]], { type: 'touch', down: true, up: true })"); await page.wait_for_timeout(250)
            o1 = await page.evaluate(OUT0)
            check(tag + ' phone: a fast touch swipe sweeps the bricks along it', o1 - o0 >= 5 and not (await page.evaluate(CELL + "(100, 600)"))['alive'] and not (await page.evaluate(CELL + "(260, 600)"))['alive'], [o0, o1])
            await page.evaluate("__gest([[0, 30, 250], [100, 30, 250], [3600, 330, 250], [3700, 330, 250]], { type: 'touch', down: true, up: true })"); await page.wait_for_timeout(200)
            o2 = await page.evaluate(OUT0)
            check(tag + ' phone: a slow finger drag smashes nothing along its way (only where it first lands)', o2 - o1 <= 10 and (await page.evaluate(CELL + "(200, 250)"))['alive'] and (await page.evaluate(CELL + "(310, 250)"))['alive'], [o1, o2])
            check(tag + ' phone: debris capped lower on a phone (80)', await page.evaluate(SM + ".cap") == 80)
            hud = await page.evaluate(S + ".ui.hud"); pb = await page.evaluate("(() => { const r = $('pauseBtn').getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom }; })()")
            check(tag + ' phone: the meter pill sits beside the pause button on the top row, on screen', hud and hud['x'] >= 0 and hud['x'] + hud['w'] <= pb['l'] and hud['y'] < pb['b'] and hud['y'] + hud['h'] > pb['t'], [hud, pb])
            await menu_click(page, '#homeBtn', tap=True); await page.wait_for_timeout(300)
            check(tag + ' phone: Home from the sheet', await page.evaluate("mode === 'none' && !$('start').hidden"))
            check(tag + ' phone: no page errors', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
