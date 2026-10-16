exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
import os
# The pet's 3D dragon (pet3d): the room renders the dragon (WebGL pixels) in EN / HE; a tap = Yes then Fast_Flying; Feed = Headbutt (chomp) with
# the snack box / food as before; a refused feed = No; the stage swaps the model (Flying_Dragon -> Flying_Dragon_Evolved at Grown-up) and the
# scale; the wearables sit on the Head / Neck bones; the egg cracks per tap and hatches into the baby dragon; an old profile keeps its pet (name,
# stage, snacks, colour, wearables); no WebGL / a model that cannot load = the 2D pet, no page errors; petSnapshot in Feed the animal, on an end
# card and through the API; nothing of the pet's 3D loads when a game opens by its link.
# Screenshots: tests/out/pet3d_{room_kid,room_adult,feed,egg,fallback}_{en,he}.png (390 x 844).
PORT = int(os.environ.get('GRASP_PORT', '8765')); BASE = 'http://localhost:%d' % PORT
if PORT != 8765: srv.terminate()  # (another server, e.g. a dev one)
OUT = 'tests/out/'
P = '__grasp.pet'; Q = '__grasp.pet3d'; T = '__grasp.tg'
P3 = "window.__graspPet3d = { pr: 1, lowFps: 0 };"  # (the shared INIT turns the 3D pet off for the other suites; here it is on, at pixel ratio 1, never held still)
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
NOGL = "(() => { const g = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (t, o) { return /webgl/i.test(t) ? null : g.call(this, t, o); }; })();"
INFO = Q + '.info'

def hatched(food=0, pantry=0, **kw):
    d = dict(hatched=True, food=food, pantry=pantry, born='2026-10-01', last='2026-10-01', egg=True, eggSeen=True, asked=True); d.update(kw)
    return d

async def fresh(b, he=False, pet=None, init='', path='/index.html', p3=True):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = await ctx.new_page(); await routes(page); errs = []; reqs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('request', lambda r: reqs.append(r.url) if ('.glb' in r.url or 'GLTFLoader' in r.url or 'three' in r.url) else None)
    seed = ''
    if pet is not None:
        seed = "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps({'v': 1, 'coins': 0, 'xp': 0, 'pet': pet})) + "); sessionStorage.setItem('__seeded', '1'); }"
    await page.add_init_script(INIT + (P3 if p3 else '') + "localStorage.setItem('lang','" + ('he' if he else 'en') + "'); sessionStorage.setItem('grasp.testDate','2026-10-02');" + seed + init)
    await page.goto(BASE + path); await page.wait_for_function("window.__grasp && __grasp.pet && __grasp.pet3d && document.readyState === 'complete'", timeout=15000)
    await page.wait_for_timeout(300); await page.evaluate(SFX_JS)
    return ctx, page, errs, reqs

async def wait(page, cond, timeout=15000):
    try: await page.wait_for_function(cond, timeout=timeout, polling=50); return True
    except Exception: return False

async def info(page): return await page.evaluate(INFO)

async def open_room(page):
    await page.evaluate(P + ".open(true)")
    return await wait(page, INFO + ".shown && " + Q + ".pixels() > 0.01", 40000)

def bone(i, slot): return (i['wear'].get(slot) or {}).get('bone')

async def room_suite(b, he):
    L = 'he' if he else 'en'
    # ---- a Kid: the dragon in its room; tap; feed; refused; the stage swap at Grown-up; wearables ----
    ctx, page, errs, reqs = await fresh(b, he=he, pet=hatched(food=12, pantry=4, color='pink', head='bow', seen=2, name='Rex'))
    ok = await open_room(page); i = await info(page); px = await page.evaluate(Q + ".pixels()")
    check(f'{L}: the room shows the 3D dragon (Kid: Flying_Dragon at 0.82, pink, the bow on the Head bone; {px * 100:.1f}% of the WebGL canvas painted)',
          ok and i['model'] == 'Flying_Dragon' and i['scale'] == 0.82 and i['color'] == 'pink' and bone(i, 'head') == 'Head' and px > 0.02, i)
    st = await page.evaluate("[document.documentElement.dir, $('petRoomT').textContent, " + Q + ".stats.first]")
    check(f'{L}: the name and stage as before, the direction ({st[0]}); first 3D frame {st[2]} ms after the room opened', st[0] == ('rtl' if he else 'ltr') and 'Rex' in st[1], st)
    await wait(page, '!__grasp.pet3d.p3.queue.length && !__grasp.pet3d.p3.pumping', 40000); await page.wait_for_timeout(200)  # (the wardrobe tiles' snapshots done)
    await page.screenshot(path=OUT + f'pet3d_room_kid_{L}.png')
    await page.evaluate(P + ".tap()"); ok1 = await wait(page, INFO + ".clip === 'Yes'", 5000)
    ok2 = await wait(page, INFO + ".running.includes('Fast_Flying')", 12000)
    check(f'{L}: a tap: Yes, then the Fast_Flying burst', ok1 and ok2, await info(page))
    await wait(page, "!" + INFO + ".busy", 15000)
    before = await page.evaluate(P + ".state")
    await page.evaluate("__sfx.length = 0; " + P + ".feedUi()")
    ok = await wait(page, INFO + ".clip === 'Headbutt'", 8000); after = await page.evaluate(P + ".state")
    await wait(page, "__sfx.filter(k => k === 'munch').length >= 2", 8000); sf = await page.evaluate("__sfx")
    check(f'{L}: Feed: the cookie flies in, Headbutt = chomp chomp (munch x2), the snack box -1 and food +1 as before',
          ok and after['pantry'] == before['pantry'] - 1 and after['food'] == before['food'] + 1 and sf.count('munch') >= 2, [before['pantry'], after['pantry'], before['food'], after['food'], sf])
    await wait(page, "!" + INFO + ".busy", 15000)
    await page.evaluate(P + ".set({ pantry: 0 }); " + P + ".feedUi()"); ok = await wait(page, INFO + ".clip === 'No'", 8000)
    check(f'{L}: a feed with an empty box: No (head shake)', ok and await page.evaluate(P + ".state.pantry") == 0, await info(page))
    await page.evaluate(P + ".equip('eyes', 'glasses') || " + P + ".set({ food: 30, seen: 3 })"); await page.evaluate(P + ".equip('eyes', 'glasses'); " + P + ".equip('neck', 'scarf')")
    ok = await wait(page, INFO + ".wear.eyes && " + INFO + ".wear.neck && !" + INFO + ".busy", 15000); i = await info(page)
    check(f'{L}: the glasses sit on the Head bone, the scarf on the Neck bone; a Teen = 0.9', ok and bone(i, 'eyes') == 'Head' and bone(i, 'neck') == 'Neck' and i['scale'] == 0.9 and i['model'] == 'Flying_Dragon', i)
    # Teen -> Grown-up by feeding: the celebration swaps to the evolved model
    await page.evaluate(P + ".set({ food: 44, pantry: 3, seen: 3, ate: { date: '', n: 0 } })"); await wait(page, "!" + INFO + ".busy", 15000)
    await page.evaluate(P + ".feedUi()")
    ok = await wait(page, INFO + ".model === 'Flying_Dragon_Evolved' && " + INFO + ".form === 4", 20000)
    await wait(page, "!__grasp.pet.ui.evo && !" + INFO + ".busy", 20000); i = await info(page)
    check(f'{L}: Teen -> Grown-up: the evolved model (Flying_Dragon_Evolved) at 1.0, the wearables moved over', ok and i['scale'] == 1 and i['model'] == 'Flying_Dragon_Evolved' and bone(i, 'eyes') == 'Head' and bone(i, 'neck') == 'Neck', i)
    await page.evaluate(P + ".equip('color', 'lilac'); " + P + ".equip('head', 'cap'); " + P + ".equip('neck', 'bowtie'); " + P + ".equip('eyes', '')")
    ok = await wait(page, INFO + ".color === 'lilac' && " + INFO + ".wear.head && " + INFO + ".wear.head.id === 'cap' && " + INFO + ".wear.neck && " + INFO + ".wear.neck.id === 'bowtie' && !" + INFO + ".wear.eyes", 6000)
    await wait(page, "!" + INFO + ".busy", 15000); await page.wait_for_timeout(300); i = await info(page)
    check(f'{L}: wardrobe in 3D: lilac tint, cap on the Head bone, bow tie under the chin, glasses off', ok and bone(i, 'head') == 'Head', i)
    await wait(page, '!__grasp.pet3d.p3.queue.length && !__grasp.pet3d.p3.pumping', 40000); await page.wait_for_timeout(200)  # (the wardrobe tiles' snapshots done)
    await page.screenshot(path=OUT + f'pet3d_room_adult_{L}.png')
    tiles = await page.evaluate("[...document.querySelectorAll('#petItems canvas')].length")
    ok = await wait(page, "(() => { const k = " + Q + ".p3.snaps; let n = 0; for (const [key, j] of k) if (j.cv && key.includes('|head|')) n++; return n >= 6; })()", 30000)
    check(f'{L}: the wardrobe tiles show the dragon wearing each item (snapshots, head framing; {tiles} tiles)', ok and tiles >= 6)
    await wait(page, "$('petTabCv').dataset.k.endsWith('|3d')", 30000); tab = await page.evaluate("$('petTabCv').dataset.k")
    check(f'{L}: the Pet tab icon is the dragon (snapshot)', tab.endswith('|3d'), tab)
    await page.evaluate(P + ".close()"); ok = await wait(page, "!" + INFO + ".canvas && !" + Q + ".p3.view", 3000)
    check(f'{L}: closing the room disposes its renderer and canvas', ok)
    check(f'{L}: no page errors (room)', not errs, errs); await ctx.close()

    # ---- the egg: cracks per tap, the hatch into the baby dragon ----
    ctx, page, errs, reqs = await fresh(b, he=he, pet=dict(hatched=False, pantry=2, egg=True, eggSeen=True, color='sky'))
    ok = await open_room(page); i = await info(page)
    check(f'{L}: an egg: the 3D egg (made in code)', ok and i['model'] == 'egg' and i['form'] == 0, i)
    for k in range(4): await page.evaluate(P + ".eggTap()"); await page.wait_for_timeout(120)
    ok = await wait(page, INFO + ".cracks === 4", 4000)
    await wait(page, "!" + INFO + ".busy", 6000); await page.wait_for_timeout(200)
    await page.screenshot(path=OUT + f'pet3d_egg_{L}.png')
    check(f'{L}: 4 taps: the egg wobbles and shows 4 cracks', ok, await info(page))
    await wait(page, "__grasp.pet3d.p3.roomI.Flying_Dragon", 20000)
    await page.evaluate(P + ".eggTap()")
    ok = await wait(page, INFO + ".model === 'Flying_Dragon' && " + INFO + ".form === 1", 10000); await wait(page, "!" + INFO + ".busy", 15000); i = await info(page)
    check(f'{L}: the 5th tap hatches it: a poof, the baby dragon (0.6) pops in', ok and await page.evaluate(P + ".state.hatched") and i['scale'] == 0.6, i)
    check(f'{L}: no page errors (egg)', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])
        for he in (False, True): await room_suite(b, he)

        # ---- an existing pet (an old profile, stored before the dragon): it keeps everything and simply becomes the dragon ----
        old = {'hatched': True, 'name': 'Pixel', 'food': 90, 'pantry': 7, 'ate': {'date': '2026-10-01', 'n': 3}, 'last': '2026-10-01', 'born': '2026-09-01', 'color': 'gold', 'head': 'crown', 'eyes': 'glasses', 'neck': 'scarf', 'seen': 5, 'earned': 120}
        ctx, page, errs, reqs = await fresh(b, pet=old)
        s = await page.evaluate(P + ".state")
        check('an old profile is accepted as it was: name, Legend, snacks, colour, wearables', [s['name'], s['stageId'], s['pantry'], s['food'], s['color'], s['head'], s['eyes'], s['neck']] == ['Pixel', 'legend', 7, 90, 'gold', 'crown', 'glasses', 'scarf'], s)
        sp = await page.evaluate("[__grasp.pet.p.species, __grasp.pet.validate({ hatched: true, species: 'unicorn' }).species, __grasp.pet.validate({ hatched: true, species: '__proto__' }).species, __grasp.pet.validate({ hatched: true, species: 'dragon' }).species, Object.keys(PET_SPECIES)]")
        check('the species: an old profile (no species) = dragon; unknown / odd ids = dragon; the table has the dragon', sp[:4] == ['dragon'] * 4 and 'dragon' in sp[4], sp)
        ok = await open_room(page); i = await info(page)
        check('... and it is the dragon: the evolved model at 1.08 (Legend), gold, crown + glasses on the Head bone, scarf on the Neck', ok and i['model'] == 'Flying_Dragon_Evolved' and i['scale'] == 1.08 and i['color'] == 'gold' and bone(i, 'head') == 'Head' and bone(i, 'eyes') == 'Head' and bone(i, 'neck') == 'Neck', i)
        await page.evaluate(P + ".close()")
        c = await page.evaluate("(async () => { const c = await petSnapshotAsync(64, 'happy', { timeout: 40000 }); if (!c) return null; const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 128) n++; return [c.width, n / (c.width * c.height), c.p3.model]; })()")
        check('petSnapshotAsync(64, "happy") (the API for the Sticker Book): a 128 px canvas with the dragon', c and c[0] == 128 and c[1] > 0.05 and c[2] == 'Flying_Dragon_Evolved', c)
        check('no page errors (old profile)', not errs, errs); await ctx.close()

        # ---- no WebGL: the 2D pet, silently; a model that cannot load: the same ----
        for he in (False, True):
            L = 'he' if he else 'en'
            ctx, page, errs, reqs = await fresh(b, he=he, pet=hatched(food=12, pantry=3, color='pink', head='bow', seen=2), init=NOGL)
            await page.evaluate(P + ".open(true)"); await wait(page, Q + ".state === 'failed'", 8000); await page.wait_for_timeout(600)
            r = await page.evaluate("(() => { const c = $('petRoomCv'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 16) if (d[i] > 200) n++; return { px: n * 4 / (c.width * c.height), state: __grasp.pet3d.state, gl: !!document.querySelector('canvas.pet3d'), tab: $('petTabCv').dataset.k, glb: __grasp.pet3d.fetched.length, snap: petSnapshot(40, 'idle') }; })()")
            check(f'{L}: no WebGL: the room draws the 2D pet ({r["px"] * 100:.0f}% painted), no 3D canvas, no model fetched, petSnapshot = null, the tab icon 2D', r['state'] == 'failed' and r['px'] > 0.03 and not r['gl'] and r['glb'] == 0 and r['snap'] is None and not r['tab'].endswith('|3d'), r)
            await page.evaluate(P + ".tap(); " + P + ".feedUi()"); await page.wait_for_timeout(500)
            await page.screenshot(path=OUT + f'pet3d_fallback_{L}.png')
            check(f'{L}: no page errors without WebGL (tap, feed)', not errs, errs); await ctx.close()
        ctx, page, errs, reqs = await fresh(b, pet=hatched(food=12, pantry=3, seen=2))
        async def abort(route): await route.abort()
        await page.route('**/*.glb', abort)
        await page.evaluate(P + ".open(true)"); await page.wait_for_timeout(3000)
        r = await page.evaluate("(() => { const c = $('petRoomCv'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 16) if (d[i] > 200) n++; return { px: n * 4 / (c.width * c.height), info: __grasp.pet3d.info }; })()")
        check('the model cannot load (offline, blocked): the 2D pet stays, no error shown', r['px'] > 0.03 and not r['info']['shown'] and not errs and await page.evaluate("!document.querySelector('.ov:not([hidden]) .err')"), r)
        await ctx.close()

        # ---- nothing of the pet's 3D loads when a game opens by its link ----
        for path in ('/strike', '/smash', '/slice', '/animals', '/feed'):
            ctx, page, errs, reqs = await fresh(b, path=path, pet=hatched(food=12, pantry=3, seen=2))
            await page.wait_for_timeout(5000)
            pet = [u for u in reqs if '.glb' in u or 'GLTFLoader' in u]; three = [u for u in reqs if 'three' in u]
            note = ' (three.js itself: Strike\'s own 3D renderer)' if path == '/strike' else ''
            check(f'{path} by its link: no GLB / GLTFLoader requested in 5 s; three.js {"loaded by Strike" if three else "not loaded"}{note}', not pet and (path == '/strike' or not three), reqs)
            check(f'{path}: no page errors', not errs, errs); await ctx.close()

        # ---- Feed the animal: the pet's turn uses the dragon's snapshots (chomp frames), the +1 snack as before ----
        for he in (False, True):
            L = 'he' if he else 'en'
            ctx, page, errs, reqs = await fresh(b, he=he, path='/feed', pet=hatched(food=30, pantry=2, seen=3, color='sky', eyes='glasses'))
            await wait(page, "typeof engine !== 'undefined' && !!engine && " + T + ".fe.geo", 15000)
            await page.wait_for_timeout(2500)
            check(f'{L} feed: nothing of the 3D pet is fetched before the first bite', not [u for u in reqs if '.glb' in u or 'GLTFLoader' in u], reqs)
            await page.evaluate(T + ".feEnter('pet')"); ok = await wait(page, T + ".fe.state === 'wait' && " + T + ".fe.pet3d && " + T + ".fe.petMouth", 40000)
            check(f'{L} feed: the pet is the dragon (petSnapshot drawn; its mouth from the snapshot)', ok, await page.evaluate(Q + ".log.slice(-6)"))
            await wait(page, "(() => { let n = 0; for (const [k, j] of " + Q + ".p3.snaps) if (j.cv && /\\|(eat|eat2)\\|/.test(k)) n++; return n >= 2; })()", 40000)
            p0 = await page.evaluate("petP().pantry")
            await page.evaluate("(() => { const F = " + T + ".fe; feFeed(F.foods.find(f => f.kind === 'snack'), performance.now()); })()")
            ok = await wait(page, T + ".fe.state === 'eat'", 4000); await page.wait_for_timeout(250)
            await page.screenshot(path=OUT + f'pet3d_feed_{L}.png')
            await page.wait_for_timeout(600); p1 = await page.evaluate("petP().pantry")
            check(f'{L} feed: it chomps its cookie (the eat frames) and gets +1 snack as before', ok and p1 == p0 + 1 and await page.evaluate(T + ".fe.pet3d"), [p0, p1])
            check(f'{L} feed: no page errors', not errs, errs); await ctx.close()

        # ---- an end card: the snack line's face is the dragon ----
        ctx, page, errs, reqs = await fresh(b, pet=hatched(food=12, pantry=0, seen=2, color='pink'))
        await page.evaluate("setInputPref('mouse'); __grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=5000)
        ok = await wait(page, "__grasp.slice.ui.petTag && __grasp.slice.ui.petTag.img", 40000)
        tag = await page.evaluate("__grasp.slice.ui.petTag")
        check('end card: "Yum! +1 snack" with the dragon\'s face (petSnapshot)', ok and tag and tag['text'] == 'Yum! +1 snack', tag)
        await page.screenshot(path=OUT + 'pet3d_card_en.png')
        check('no page errors (card)', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
