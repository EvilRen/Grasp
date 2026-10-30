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

async def st(page): return await page.evaluate(f"(() => {{ const t = {S}.ta; return {{ stage: t.stage, cares: t.cares, hunger: t.hunger, fun: t.fun, poops: t.poops.length, asleep: t.asleep, want: t.want, act: t.act && t.act.kind, crack: t.crack }}; }})()")
async def btn(page, id):
    x, y = await page.evaluate(f"(() => {{ const b = {S}.layout().btns.find(q => q.id === '{id}'); return [b.x, b.y]; }})()")
    await tap(page, x, y); await page.wait_for_timeout(150)
async def finish(page): await page.evaluate(f"{S}.age(4000)"); await page.wait_for_timeout(250)

async def mechanics(b):
    ctx, page, errs = await tama_page(b)
    await page.evaluate("tgDemoDone()")
    s0 = await st(page); L = await page.evaluate(f"{S}.layout()")
    check('first play: an egg on the pixel screen, four big buttons (>= 72 px) under the device', s0['stage'] == 'egg' and len(L['btns']) == 4 and min(q['r'] for q in L['btns']) * 2 >= 72 and L['btns'][0]['y'] > L['lcd']['y'] + L['lcd']['h'], [s0, [q['r'] for q in L['btns']]])
    await page.screenshot(path=OUT + 'tama_egg.png')
    cx = L['lcd']['x'] + L['lcd']['w'] / 2; cy = L['lcd']['y'] + L['lcd']['h'] / 2
    for i in range(5): await tap(page, cx, cy); await page.wait_for_timeout(450)
    s1 = await st(page); await page.wait_for_timeout(1500); s2 = await st(page); sd = await said(page)
    check('each tap cracks the egg; the fifth hatches it (a party, "Hello!")', s1['crack'] == 5 and s2['stage'] == 'baby' and 'Hello!' in sd, [s1, s2, sd[-2:]])
    check('...kept: the hatched pet is saved', await page.evaluate("JSON.parse(localStorage.getItem('grasp.tama')).stage") == 'baby')
    await page.screenshot(path=OUT + 'tama_baby.png')
    # hunger: the bubble, the voice, the pulsing button
    await page.evaluate(f"{S}.ta.poops = []; {S}.ta.hunger = 1; {S}.ta.fun = 3; {S}.ta.want = null"); await page.wait_for_timeout(300)
    s = await st(page); sd = await said(page)
    check('hungry: it wants food (the bubble, "I\'m hungry!")', s['want'] == 'feed' and "I’m hungry!" in sd, [s, sd[-2:]])
    await page.screenshot(path=OUT + 'tama_hungry.png')
    c0 = s['stage'] and (await st(page))['cares']
    await btn(page, 'feed'); a = (await st(page))['act']; snd0 = await snd(page); await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'tama_eat.png'); await finish(page)
    s = await st(page); sd = await said(page)
    check('🍎: it eats (munch), hunger +2, a care, "Yummy!"', a == 'eat' and 'munch' in snd0 and s['hunger'] == 3 and s['cares'] == c0 + 1 and 'Yummy!' in sd, [a, s, sd[-2:]])
    await page.evaluate(f"{S}.ta.hunger = 4"); await btn(page, 'feed'); a = (await st(page))['act']; await finish(page)
    check('...full: it shakes its head, "I\'m full!" (no harm done)', a == 'no' and "I’m full!" in await said(page))
    await btn(page, 'play'); a = (await st(page))['act']; await page.wait_for_timeout(800); await page.screenshot(path=OUT + 'tama_play.png'); await finish(page)
    s = await st(page); check('⚽: a ball bounces over the screen, it jumps, fun +2, "Fun!"', a == 'ball' and s['fun'] >= 4 and 'Fun!' in await said(page), [a, s])
    await page.evaluate(f"{S}.age(43000)"); await page.wait_for_timeout(300); s = await st(page)
    check('in time it poops (a fart), and wants a bath', s['poops'] >= 1 and s['want'] == 'bath' and 'fart' in await snd(page), s)
    await page.screenshot(path=OUT + 'tama_poop.png')
    await btn(page, 'bath'); a = (await st(page))['act']; await page.wait_for_timeout(700); await page.screenshot(path=OUT + 'tama_bath.png'); await finish(page)
    s = await st(page); check('🛁: a wave washes the poop away, "All clean!"', a == 'bath' and s['poops'] == 0 and 'All clean!' in await said(page), [a, s])
    await btn(page, 'sleep'); s = await st(page); await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'tama_sleep.png')
    check('🌙: lights out, Zzz, "Good night"', s['asleep'] and 'Good night' in await said(page), s)
    await btn(page, 'sleep'); s = await st(page); check('...☀️ wakes it ("Good morning!"); it also wakes by itself', not s['asleep'] and 'Good morning!' in await said(page), s)
    await page.evaluate(f"{S}.pet()"); s = await st(page); check('a tap on the pet: a hop, a giggle, a heart', s['act'] == 'hop' and 'giggle' in await snd(page), s)
    await finish(page)
    # growing
    await page.evaluate(f"{S}.ta.cares = 14; {S}.ta.hunger = 1"); await btn(page, 'feed'); await finish(page); s = await st(page)
    check('cares grow it: a child at 15 ("I grew!", kept)', s['stage'] == 'child' and await page.evaluate("JSON.parse(localStorage.getItem('grasp.tama')).stage") == 'child', s)
    await page.wait_for_timeout(2600); await page.screenshot(path=OUT + 'tama_child.png')
    await page.evaluate(f"{S}.ta.cares = 39; {S}.ta.fun = 0"); await btn(page, 'play'); await finish(page); await page.wait_for_timeout(2600); s = await st(page)
    check('...grown up at 40', s['stage'] == 'adult', s); await page.screenshot(path=OUT + 'tama_adult.png')
    # no real time: home and back, the same pet, a fresh visit
    await page.tap('#pauseBtn'); await wait(page, "mode === 'none'", 4000)
    await page.evaluate("__grasp.setGameMode('tama'); strikeStart('mouse')"); await wait(page, "gameMode === 'tama' && mode === 'mouse'", 8000); await page.wait_for_timeout(300)
    s = await st(page); check('home and back: the same grown-up pet, a fresh visit (a little hungry and bored, never sick)', s['stage'] == 'adult' and s['hunger'] == 2 and s['fun'] == 2 and not s['asleep'], s)
    check('mechanics: no page errors', not errs, errs); await ctx.close()

async def layouts(b):
    for he, (w, h) in ((False, (320, 568)), (True, (390, 844)), (False, (844, 390)), (True, (1280, 800))):
        tag = ('HE' if he else 'EN') + ' %dx%d' % (w, h); ctx, page, errs = await tama_page(b, he, w, h, init="localStorage.setItem('grasp.tama', JSON.stringify({ stage: 'child', cares: 20 }));")
        r = await page.evaluate(f"""(() => {{ const L = {S}.layout(), top = tgTop(); const bs = L.btns; return {{ inside: bs.every(b => b.x - b.r >= 0 && b.x + b.r <= innerWidth && b.y + b.r <= innerHeight), apart: bs.every((b, i) => !i || Math.abs(b.x - bs[i - 1].x) >= b.r * 2), dev: L.cy - L.dh / 2 >= top - 2 && (L.cy + L.dh / 2 <= Math.min(...bs.map(b => b.y - b.r)) || L.cx + L.dw / 2 <= Math.min(...bs.map(b => b.x - b.r))), lcd: L.lcd.w, d: bs[0].r * 2 }}; }})()""")
        check(tag + ': the device under the corner stickers, the four buttons (%d px) apart and on screen, the screen %d px wide' % (r['d'], r['lcd']), r['inside'] and r['apart'] and r['dev'] and r['lcd'] >= 96, r)
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
