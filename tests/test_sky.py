exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Sky tower (/sky, the Little ones): blocks with faces float down; a finger steers one, letting go drops it; build a wobbly tower up to the moon.
# Its link and sticker open it (EN / HE, no page errors, the demo finger + <= 3 words, the house in the corner is the way out); a block steered
# over the platform lands (a note, the count said); one let go over nothing tips off ("Oops!") and nothing is lost; left alone a block sinks and
# lands by itself; a block on the block's edge is pulled a little to the middle; the tower stands while its weight sits over each block and a
# staircase too far = BOOM (every block flies off, "Boom! Again!", the camera back down, a fresh tower); as it rises the camera follows and the
# sky stages are named (clouds ... the moon); the best height is kept; the layout fits a small phone and landscape. Screenshots: tests/out/sky_*.png
S = '__grasp.sky'

async def sky_page(b, he=False, w=390, h=844):
    ctx, page, errs = await page_for(b, '/sky', he)
    if (w, h) != (390, 844): await page.set_viewport_size({'width': w, 'height': h})
    await wait(page, "gameMode === 'sky' && mode === 'mouse' && !!__grasp.sky.sk.hand", 10000); await page.wait_for_timeout(400)
    return ctx, page, errs

async def hand(page): return await page.evaluate(f"(() => {{ const h = {S}.sk.hand; return h ? {{ x: innerWidth / 2 + h.x, y: h.sy, w: h.w, h: h.h }} : null; }})()")
async def landed(page): return await page.evaluate(f"{S}.sk.blocks.length")
async def wait_hand(page): return await wait(page, f"!!{S}.sk.hand && !{S}.sk.fall", 5000)

async def mechanics(b):
    ctx, page, errs = await sky_page(b)
    await page.evaluate("tgDemoDone()"); await page.evaluate("tgReset('sky')"); await page.wait_for_timeout(200)
    h = await hand(page); W = await page.evaluate("innerWidth")
    check('a fresh tower: a block with a face hovers to one side, the platform empty', h and abs(h['x'] - W / 2) > 40 and await landed(page) == 0, h)
    # steer from anywhere: the block glides under the finger, letting go drops it onto the platform
    await page.evaluate(f"fing('pointerdown', 1, {W / 2 + 120}, 600)"); await page.wait_for_timeout(60)
    for k in range(1, 9): await page.evaluate(f"fing('pointermove', 1, {W / 2 + 120 - k * 15}, 600)"); await page.wait_for_timeout(30)
    await page.wait_for_timeout(350); hx = (await hand(page))['x']
    check('a finger anywhere steers the block: it glides under the finger (%.0f -> %.0f)' % (h['x'], hx), abs(hx - W / 2) < 12, hx)
    await page.evaluate(f"fing('pointerup', 1, {W / 2}, 600)"); ok = await wait(page, f"{S}.sk.blocks.length === 1", 3000)
    n1 = await said(page)
    check('letting go drops it: it lands on the platform, a note plays and the count is said ("%s")' % (n1[-1] if n1 else ''), ok and 'xylo' in await snd(page) and n1 and n1[-1] == 'One', n1[-3:])
    # carry the block itself
    await wait_hand(page); h = await hand(page)
    await page.evaluate(f"fing('pointerdown', 1, {h['x']}, {h['y']})"); await page.wait_for_timeout(60)
    for k in range(1, 9): await page.evaluate(f"fing('pointermove', 1, {h['x'] + (W / 2 - h['x']) * k / 8}, {h['y'] + 40 * k / 8})"); await page.wait_for_timeout(30)
    await page.wait_for_timeout(300); h2 = await hand(page)
    check('the block itself can be carried (down %.0f px)' % (h2['y'] - h['y']), h2['y'] > h['y'] + 25, [h, h2])
    await page.evaluate(f"fing('pointerup', 1, {W / 2}, {h2['y']})"); ok = await wait(page, f"{S}.sk.blocks.length === 2", 3000)
    check('...and dropped onto the tower (2 blocks, "Two")', ok and (await said(page))[-1] == 'Two', await said(page))
    # a miss tips off, nothing lost
    await wait_hand(page); r = await page.evaluate(f"{S}.put(innerWidth * 0.42)")
    await page.wait_for_timeout(200); sd = await said(page)
    check('a block let go over nothing tips off ("Oops!", a boing) and the tower is untouched', r == 'tip' and await landed(page) == 2 and 'Oops!' in sd and 'boing' in await snd(page), [r, sd[-2:]])
    ok = await wait(page, f"!!{S}.sk.hand && {S}.sk.debris.length === 0", 5000)
    check('...it poofs away and the next block comes', ok)
    # left alone: it sinks and lands by itself
    await page.evaluate(f"{S}.sk.hand.x = {S}.sk.hand.tx = {S}.visX()"); ok = await wait(page, f"{S}.sk.blocks.length === 3", 15000)
    check('left alone, a block sinks slowly and lands by itself', ok)
    # the magnet
    await wait_hand(page); sup = await page.evaluate(f"(() => {{ const b = {S}.sk.blocks.at(-1); return [b.x, b.w]; }})()"); vx = await page.evaluate(f"{S}.visX()")
    await page.evaluate(f"{S}.put({sup[1] * 0.2})"); nb = await page.evaluate(f"{S}.sk.blocks.at(-1).x")
    check('a block a bit off the middle is pulled a little toward it (%.1f of %.1f off)' % (nb - sup[0], sup[1] * 0.2), 0 < nb - sup[0] < sup[1] * 0.2 * 0.8, [sup, vx, nb])
    await page.screenshot(path=OUT + 'sky_low.png')
    # the camera follows and the stages are named
    await page.evaluate("tgReset('sky')"); await page.wait_for_timeout(100)
    for i in range(26): await page.evaluate(f"{S}.put(0)")
    await page.wait_for_timeout(1400); log = await page.evaluate(f"{S}.sk.log.join()"); sd = ' | '.join(await said(page))
    alt = await page.evaluate(f"{S}.alt()"); cam = await page.evaluate(f"[{S}.sk.cam, {S}.cam0()]")
    check('a straight tower of 26 stands (%.1f blocks high) and the camera climbed with it (%.0f px)' % (alt, cam[1] - cam[0]), await landed(page) == 26 and cam[1] - cam[0] > 1000, [alt, cam])
    check('...every sky stage on the way was reached and named (clouds, birds, balloon, space, the moon)', all(('stage:' + k) in log for k in ('clouds', 'birds', 'balloon', 'space', 'moon')) and all(x in sd for x in ('The clouds!', 'Hello, birds!', 'A balloon!', 'Space!', 'We reached the moon!')), [log[-200:], sd[-200:]])
    await page.screenshot(path=OUT + 'sky_moon.png')
    best = await page.evaluate("+localStorage.getItem('grasp.skyBest')")
    check('the best height is kept (%.1f)' % best, best >= alt - 0.2, best)
    # a staircase too far = boom
    await page.evaluate("tgReset('sky')"); await page.wait_for_timeout(100); res = []
    for i in range(8):
        res.append(await page.evaluate(f"(() => {{ const s = {S}.sk; const t = s.blocks.at(-1); const w = t ? t.w : s.pw; return {S}.put(w * 0.45); }})()"))
        if res[-1] == 'boom': break
    await page.wait_for_timeout(150); sd = await said(page); deb = await page.evaluate(f"{S}.sk.debris.length")
    check('a staircase leaning too far = BOOM: every block flies off dizzy (%d), "Boom! Again!", a boom sound (%s)' % (deb, ','.join(res)), res[-1] == 'boom' and deb >= 2 and 'Boom! Again!' in sd and 'boom' in await snd(page), [res, sd[-3:]])
    await page.wait_for_timeout(250); await page.screenshot(path=OUT + 'sky_boom.png')
    ok = await wait(page, f"!{S}.sk.boom && !!{S}.sk.hand && {S}.sk.blocks.length === 0 && Math.abs({S}.sk.cam - {S}.cam0()) < 30", 6000)
    check('...then the camera is back at the ground and a fresh tower starts', ok)
    # while leaning (but standing) the blocks look worried and the tower sways
    await page.evaluate("tgReset('sky')"); await page.wait_for_timeout(100)
    for i in range(4): await page.evaluate(f"{S}.put(0)")
    for i in range(3):
        r = await page.evaluate(f"(() => {{ const t = {S}.sk.blocks.at(-1); return {S}.put(t.w * 0.3); }})()")
    lean = await page.evaluate(f"{S}.sk.lean"); await page.wait_for_timeout(300); sw = await page.evaluate(f"Math.abs({S}.sk.sway) + Math.abs({S}.sk.swayV) * 100")
    check('a leaning tower still stands (lean %.2f) and sways (%.1f)' % (lean, sw), await page.evaluate(f"!{S}.sk.boom") and lean > 0.3 and sw > 0.5, [lean, sw, r])
    check('mechanics: no page errors', not errs, errs); await ctx.close()

async def hebrew(b):
    ctx, page, errs = await sky_page(b, True)
    await page.evaluate("tgDemoDone()")
    for i in range(3): await page.evaluate(f"{S}.put(0)")
    await page.wait_for_timeout(200); sd = await said(page)
    check('HE: the count is said in Hebrew (%s)' % ' '.join(sd[-3:]), sd[-3:] == ['אחת', 'שתיים', 'שלוש'], sd)
    await page.screenshot(path=OUT + 'sky_he.png')
    check('HE: no page errors', not errs, errs); await ctx.close()

async def layouts(b):
    for he, (w, h) in ((False, (320, 568)), (False, (844, 390)), (True, (1280, 800))):
        tag = ('HE' if he else 'EN') + ' %dx%d' % (w, h); ctx, page, errs = await sky_page(b, he, w, h)
        await page.evaluate("tgDemoDone(); tgReset('sky')"); await page.wait_for_timeout(300)
        r = await page.evaluate(f"(() => {{ const s = {S}.sk, hd = s.hand, top = tgTop(); return {{ u: s.u, pw: s.pw, hy: hd.sy - hd.h / 2, top, inside: Math.abs(hd.x) + hd.w / 2 <= innerWidth / 2, ground: -s.cam }}; }})()")
        check(tag + ': the block (%d px) hovers under the corner stickers, inside the screen; the platform (%d px) on the screen' % (r['u'], r['pw']), r['hy'] >= r['top'] - 2 and r['inside'] and r['pw'] < w and r['ground'] < h - 30, r)
        for i in range(6): await page.evaluate(f"{S}.put(0)")
        await page.wait_for_timeout(900); await page.screenshot(path=OUT + 'sky_%s_%dx%d.png' % ('he' if he else 'en', w, h))
        check(tag + ': no page errors', not errs, errs); await ctx.close()

async def sticker(b):
    ctx, page, errs = await page_for(b, '/', True)
    await page.tap('#littleBtn'); await wait(page, "!$('littlePick').hidden", 3000); await page.wait_for_timeout(500)
    await page.evaluate("(() => { const b = document.querySelector('#littlePick button[data-mode=sky]'); __grasp.menub.page([...$('mbPager').querySelectorAll('.mbPg')].indexOf(b.closest('.mbPg')), true); })()"); await page.wait_for_timeout(400)
    lb = await page.evaluate("document.querySelector('#littlePick button[data-mode=sky] .lb').textContent")
    ic = await page.evaluate("document.querySelector('#littlePick button[data-mode=sky] .ic svg') !== null")
    await page.screenshot(path=OUT + 'sky_sticker.png')
    await page.tap('#littlePick button[data-mode=sky]'); ok = await wait(page, "gameMode === 'sky' && mode === 'mouse'", 8000)
    check('HE: the Little ones sticker "' + lb + '" (its own drawing) opens the sky tower in one tap', ok and ic and lb == 'מגדל לשמיים', [lb, ic])
    check('sticker: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await link_tests(b, 'sky', he)
        await mechanics(b); await hebrew(b); await layouts(b); await sticker(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
