exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Pocket pet (/tama, the Little ones): a retro egg device with a pixel screen and four big picture buttons (food, play, bath, sleep). First play:
# an egg that cracks with each tap and hatches; the pet walks, shows what it wants (a thought bubble, the voice, the button pulses); feeding,
# a ball game, a bath that washes the poop away, sleep and waking; a tap on the pet: a hop and a heart; no real time (each visit starts the
# same, nothing lost); cares grow it: a baby, a child at 15, grown up at 40 (kept). Screenshots: tests/out/tama_*.png
S = '__grasp.tama'

async def tama_page(b, he=False, w=390, h=844, init=''):
    ctx, page, errs = await page_for(b, '/tama', he, init=init)
    if (w, h) != (390, 844): await page.set_viewport_size({'width': w, 'height': h})
    await wait(page, f"gameMode === 'tama' && mode === 'mouse' && !!{S}.ta", 10000); await page.wait_for_timeout(400)
    return ctx, page, errs

async def st(page): return await page.evaluate(f"(() => {{ const t = {S}.ta; return {{ stage: t.stage, cares: t.cares, need: Object.assign({{}}, t.need), room: t.room, want: t.want, mood: t.mood, crack: t.crack, foods: t.foods.length, foam: t.foam.length, dirt: t.dirt.length, lights: t.lights, hat: t.hat, col: t.col }}; }})()")
async def btn(page, id):
    x, y = await page.evaluate(f"(() => {{ const b = {S}.layout().btns.find(q => q.id === '{id}'); return [b.x, b.y]; }})()")
    await tap(page, x, y); await page.wait_for_timeout(250)

async def mechanics(b):
    ctx, page, errs = await tama_page(b)
    await page.evaluate("tgDemoDone()")
    s0 = await st(page); L = await page.evaluate(f"{S}.layout()")
    check('first play: a big egg; five big buttons (>= 58 px) along the bottom', s0['stage'] == 'egg' and len(L['btns']) == 5 and min(q['r'] for q in L['btns']) * 2 >= 58, [s0, [q['r'] for q in L['btns']]])
    await page.screenshot(path=OUT + 'tama_egg.png')
    P = await page.evaluate(f"{S}.pet()")
    for i in range(5): await tap(page, P['x'], P['y']); await page.wait_for_timeout(450)
    await page.wait_for_timeout(600); s = await st(page)
    check('each tap cracks the egg; the fifth hatches a big cartoon creature ("Hello!")', s['stage'] == 'baby' and 'Hello!' in await said(page), s)
    await page.wait_for_timeout(900); await page.screenshot(path=OUT + 'tama_baby.png')
    # a poke: it jiggles and giggles; a rub tickles it
    P = await page.evaluate(f"{S}.pet()"); await tap(page, P['x'], P['y'] + 10); s = await st(page)
    check('a tap on it: a jiggle (the spring) and a happy face', s['mood'] in ('happy', 'wow') and abs(await page.evaluate(f"{S}.ta.sqv")) > 0.001, s)
    await page.wait_for_timeout(800)
    await drag(page, P['x'] - 40, P['y'], P['x'] + 40, P['y'], steps=12); check('a rub tickles it (laughs, giggle)', 'tickle' in await page.evaluate(f"{S}.ta.log.join()") and 'giggle' in await snd(page))
    # the kitchen
    await page.evaluate(f"{S}.ta.need.food = 1; {S}.ta.want = null"); await page.wait_for_timeout(300); s = await st(page)
    check('hungry: the bubble over its head and "I\'m hungry!"; the 🍎 button glows', s['want'] == 'food' and "I’m hungry!" in await said(page), s)
    await page.screenshot(path=OUT + 'tama_hungry.png')
    await btn(page, 'kitchen'); await page.wait_for_timeout(400); s = await st(page)
    check('🍎: the kitchen, three foods on the table', s['room'] == 'kitchen' and s['foods'] == 3, s)
    await page.evaluate(f"{S}.ta.foods.forEach(f => {{ f.yuck = false; f.e = '🍎'; }})")
    f = await page.evaluate(f"[{S}.ta.foods[1].x, {S}.ta.foods[1].y]"); m = await page.evaluate(f"{S}.mouth()")
    await page.evaluate(f"fing('pointerdown', 1, {f[0]}, {f[1]})"); await page.wait_for_timeout(60)
    for k in range(1, 11): await page.evaluate(f"fing('pointermove', 1, {f[0] + (m['x'] - f[0]) * k / 10}, {f[1] + (m['y'] - f[1]) * k / 10})"); await page.wait_for_timeout(25)
    op = await page.evaluate(f"{S}.ta.mouth"); await page.screenshot(path=OUT + 'tama_feed.png')
    await page.evaluate(f"fing('pointerup', 1, {m['x']}, {m['y']})"); await page.wait_for_timeout(300); s = await st(page)
    check('dragging food to it: the mouth opens wide as it comes (%.2f), it chews (munch), hunger +1, "Yummy!"' % op, op > 0.6 and 'munch' in await snd(page) and s['need']['food'] == 2 and 'Yummy!' in await said(page), [op, s['need']])
    await page.evaluate(f"{S}.ta.foods[0].yuck = true; {S}.ta.foods[0].e = '🥦'"); await page.evaluate(f"{S}.eat(0)"); s = await st(page)
    check('broccoli: a yuck face, spat out, "Yuck!"', s['mood'] == 'yuck' and 'Yuck!' in await said(page) and 'yuck' in await snd(page), s)
    await page.wait_for_timeout(1700)
    # the park
    await btn(page, 'park'); await page.wait_for_timeout(300)
    await page.evaluate(f"(() => {{ const B = {S}.ta.ball, p = {S}.pet(); B.x = p.x; B.y = p.y - p.R * 2.5; B.vx = 0; B.vy = 0.3; }})()"); await page.wait_for_timeout(900)
    await page.screenshot(path=OUT + 'tama_park.png'); bonks = await page.evaluate(f"{S}.ta.bonks")
    check('⚽: the park; a ball falling on it is headed up (it jumps, counts "One")', bonks >= 1 and 'One' in await said(page), [bonks, (await said(page))[-3:]])
    # the bath
    await btn(page, 'bath'); await page.wait_for_timeout(300); s = await st(page)
    check('🛁: the bath; it is muddy', s['room'] == 'bath' and s['dirt'] >= 3, s)
    P = await page.evaluate(f"{S}.pet()")
    for y in (-0.5, -0.2, 0.1, 0.4):
        await drag(page, P['x'] - P['R'] * 0.8, P['y'] + P['R'] * y, P['x'] + P['R'] * 0.8, P['y'] + P['R'] * y, steps=10)
    s = await st(page); await page.screenshot(path=OUT + 'tama_foam.png')
    check('rubbing it with a finger: foam (%d bubbles), the mud gone' % s['foam'], s['foam'] >= 15 and s['dirt'] == 0 and 'bubble' in ' '.join(await snd(page)), s)
    sh = await page.evaluate(f"(() => {{ const L = {S}.ta.L; return [L.shower.x, L.shower.y]; }})()"); await tap(page, sh[0], sh[1]); await page.wait_for_timeout(700); await page.screenshot(path=OUT + 'tama_shower.png')
    await page.evaluate(f"{S}.age(2500)"); await page.wait_for_timeout(500); s = await st(page)
    check('the shower rinses the foam away: clean, "All clean!"', s['foam'] == 0 and s['need']['clean'] == 4 and 'All clean!' in await said(page), s)
    # the bedroom
    await btn(page, 'bed'); await page.wait_for_timeout(300); lp = await page.evaluate(f"(() => {{ const L = {S}.ta.L; return [L.lamp.x, L.lamp.y]; }})()")
    await tap(page, lp[0], lp[1]); await page.wait_for_timeout(1200); s = await st(page); await page.screenshot(path=OUT + 'tama_sleep.png')
    check('🌙: tap the lamp: lights out, it sleeps (Zzz), "Good night"', not s['lights'] and 'Good night' in await said(page), s)
    await page.evaluate(f"{S}.age(8000)"); await page.wait_for_timeout(400); s = await st(page)
    check('...it wakes up rested by itself ("Good morning!")', s['lights'] and s['need']['sleep'] == 4 and 'Good morning!' in await said(page), s)
    # the wardrobe
    await btn(page, 'dress'); await page.wait_for_timeout(300); its = await page.evaluate(f"{S}.dress()")
    hat = [q for q in its if q['kind'] == 'hat'][0]; col = [q for q in its if q['kind'] == 'col'][2]
    await tap(page, hat['x'], hat['y']); await tap(page, col['x'], col['y']); await page.wait_for_timeout(400); s = await st(page); await page.screenshot(path=OUT + 'tama_dress.png')
    check('👒: a hat on, a new colour ("Wow!"), kept', s['hat'] == hat['v'] and s['col'] == col['v'] and await page.evaluate("JSON.parse(localStorage.getItem('grasp.tama')).hat") == hat['v'], s)
    # growing
    await page.evaluate(f"{S}.ta.cares = 14"); await btn(page, 'kitchen'); await page.wait_for_timeout(300); await page.evaluate(f"{S}.ta.foods[0].yuck = false; {S}.ta.need.food = 1; {S}.eat(0)"); await page.wait_for_timeout(2000); s = await st(page)
    check('cares grow it: a child at 15 (ears; "I grew!")', s['stage'] == 'child' and 'I grew!' in await said(page), s); await page.screenshot(path=OUT + 'tama_child.png')
    await page.evaluate(f"{S}.ta.cares = 39; {S}.ta.foods[0].yuck = false; {S}.ta.need.food = 1; {S}.eat(0)"); await page.wait_for_timeout(1800); s = await st(page)
    check('...grown up at 40 (antennae, a tail)', s['stage'] == 'adult', s); await btn(page, 'kitchen'); await page.wait_for_timeout(500); await page.screenshot(path=OUT + 'tama_adult.png')
    await page.tap('#pauseBtn'); await wait(page, "mode === 'none'", 4000)
    await page.evaluate("__grasp.setGameMode('tama'); strikeStart('mouse')"); await wait(page, "gameMode === 'tama' && mode === 'mouse'", 8000); await page.wait_for_timeout(300)
    s = await st(page); check('home and back: the same grown-up pet in its hat, a fresh visit at home', s['stage'] == 'adult' and s['room'] == 'home' and s['hat'] == hat['v'], s)
    check('mechanics: no page errors', not errs, errs); await ctx.close()

async def layouts(b):
    for he, (w, h) in ((False, (320, 568)), (True, (390, 844)), (False, (844, 390)), (True, (1280, 800))):
        tag = ('HE' if he else 'EN') + ' %dx%d' % (w, h); ctx, page, errs = await tama_page(b, he, w, h, init="localStorage.setItem('grasp.tama', JSON.stringify({ stage: 'child', cares: 20 }));")
        r = await page.evaluate(f"""(() => {{ const L = {S}.layout(), p = {S}.pet(), top = tgTop(); const bs = L.btns; return {{ inside: bs.every(b => b.x - b.r >= 0 && b.x + b.r <= innerWidth && b.y + b.r <= innerHeight), apart: bs.every((b, i) => !i || Math.hypot(b.x - bs[i - 1].x, b.y - bs[i - 1].y) >= b.r * 2), pet: p.y - p.R >= top + 30 && (L.floorY < bs[0].y - bs[0].r || bs.every(b => Math.abs(b.x - p.x) > p.R + b.r)), R: p.R, d: bs[0].r * 2 }}; }})()""")
        check(tag + ': the creature (%d px) between the needs and the buttons, the five buttons (%d px) apart and on screen' % (r['R'], r['d']), r['inside'] and r['apart'] and r['pet'] and r['R'] >= 40, r)
        await page.screenshot(path=OUT + 'tama_%s_%dx%d.png' % ('he' if he else 'en', w, h))
        check(tag + ': no page errors', not errs, errs); await ctx.close()

async def sticker(b):
    ctx, page, errs = await page_for(b, '/', True)
    await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.wait_for_timeout(500)
    await page.evaluate("(() => { const b = document.querySelector('#littlePick button[data-mode=tama]'); __grasp.menub.page([...$('mbPager').querySelectorAll('.mbPg')].indexOf(b.closest('.mbPg')), true); })()"); await page.wait_for_timeout(400)
    lb = await page.evaluate("document.querySelector('#littlePick button[data-mode=tama] .lb').textContent")
    await page.screenshot(path=OUT + 'tama_sticker.png')
    await page.tap('#littlePick button[data-mode=tama]'); ok = await wait(page, "gameMode === 'tama' && mode === 'mouse'", 8000)
    check('HE: the Little ones sticker "' + lb + '" opens the pocket pet in one tap', ok and lb == 'חיית כיס', lb)
    check('sticker: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await link_tests(b, 'tama', he)
        await mechanics(b); await layouts(b); await sticker(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
