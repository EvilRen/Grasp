exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Spot the difference (/spot, Big kids): the Big kids sticker and the link open it (touch); two pictures (stacked on a phone, side by side when
# wide, the original first in reading order); a tap on a difference in either picture rings it in both; a tap beside it is a miss (a red cross,
# counted, no fail); a tap on one already found does nothing; the bulb glows round one difference (then cools down); the last one found: the
# shared card (stars by misses and hints, coins, Next / Home); Next plays the next puzzle (level 1 of every scene, then 2, then 3: 3, 5, 7
# differences); the solved ones are kept in the profile; the pause sheet's Restart replays the same one. Screenshots: tests/out/spot_*.png
SP = '__grasp.spot'

async def spot_page(b, he=False, w=390, h=844, path='/spot', init=''):
    ctx, page, errs = await page_for(b, path, he, init=init, mobile=w < 600)
    if (w, h) != ((390, 844) if w < 600 else (1280, 800)): await page.set_viewport_size({'width': w, 'height': h})
    ok = await wait(page, f"gameMode === 'spot' && mode === 'mouse' && {SP}.spot.ready", 15000); await page.wait_for_timeout(300)
    return ctx, page, errs, ok

async def tapat(page, x, y): await tap(page, x, y, hold=50)
async def diff_pt(page, i, which='A'):
    return await page.evaluate(f"(() => {{ const L = {SP}.layout(), R = L.{which}, d = {SP}.diffs()[{i}]; return [R.x + d.x * R.w, R.y + d.y * R.h]; }})()")

async def play(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs, ok = await spot_page(b, he)
    check(tag + ': /spot opens spot the difference at once (touch), the pictures loaded', ok, await page.evaluate("[gameMode, mode]"))
    L = await page.evaluate(f"{SP}.layout()"); D = await page.evaluate(f"{SP}.diffs()"); st = await page.evaluate(f"({{ key: {SP}.spot.key, lvl: {SP}.spot.lvl }})")
    check(tag + ': the first puzzle: level 1 of the first scene, 3 differences', st['lvl'] == 1 and len(D) == 3, [st, len(D)])
    A, B = L['A'], L['B']
    check(tag + ': a phone: the original above the changed one, both the same size, inside the screen and under the pause button', abs(A['w'] - B['w']) < 1 and B['y'] >= A['y'] + A['h'] and A['y'] >= await page.evaluate("$('pauseBtn').getBoundingClientRect().bottom") - 2 and B['y'] + B['h'] <= 844 - 60, [A, B])
    check(tag + ': the banner "' + ('מצאו 3 הבדלים!' if he else 'Find 3 differences!') + '"', await page.evaluate("t('spFind', { n: 3 })") == ('מצאו 3 הבדלים!' if he else 'Find 3 differences!'))
    await page.screenshot(path=OUT + 'spot_start_%s.png' % tag.lower())
    # a miss: a corner far from every difference
    far = await page.evaluate(f"""(() => {{ const L = {SP}.layout(), R = L.A, D = {SP}.diffs(); let best = null, bd = -1; for (let u = 0.04; u < 1; u += 0.04) for (let v = 0.04; v < 1; v += 0.04) {{ const m = Math.min(...D.map((d) => Math.hypot(u - d.x, (v - d.y) * R.h / R.w) - d.r)); if (m > bd) {{ bd = m; best = [R.x + u * R.w, R.y + v * R.h]; }} }} return best; }})()""")
    await tapat(page, *far)
    check(tag + ': a tap away from every difference: a miss (a red cross), nothing found, no fail', await page.evaluate(f"{SP}.spot.miss") == 1 and await page.evaluate(f"{SP}.spot.found.length") == 0 and await page.evaluate(f"{SP}.spot.crosses.length") == 1 and not await page.evaluate(f"{SP}.spot.over"))
    # found in the original, then in the changed one
    await tapat(page, *(await diff_pt(page, 0, 'A')))
    check(tag + ': a tap on a difference in the original: found (a ring in both pictures, a chime)', await page.evaluate(f"{SP}.spot.found.join()") == '0')
    await tapat(page, *(await diff_pt(page, 0, 'B'))); await tapat(page, *(await diff_pt(page, 0, 'A')))
    check(tag + ': ...a tap on it again (either picture): nothing (no miss, not twice)', await page.evaluate(f"{SP}.spot.miss") == 1 and await page.evaluate(f"{SP}.spot.found.length") == 1)
    p = await diff_pt(page, 1, 'B'); r = await page.evaluate(f"{SP}.diffs()[1].r * {SP}.layout().B.w"); await tapat(page, p[0] + r * 0.7, p[1])
    check(tag + ': a tap on a difference in the changed picture, a little off its middle (inside its circle): found', await page.evaluate(f"{SP}.spot.found.length") == 2)
    # the bulb
    await tapat(page, L['hint']['x'], L['hint']['y'])
    h = await page.evaluate(f"(() => {{ const H = {SP}.spot.hint, d = H && {SP}.diffs()[H.i]; return H ? {{ i: H.i, found: {SP}.spot.found.includes(H.i), dist: Math.hypot(H.x - d.x, H.y - d.y), r: H.r, dr: d.r }} : null; }})()")
    check(tag + ': the bulb: a glow round one difference still to find (near it, not on it), counted', h and not h['found'] and h['dist'] > 0 and h['r'] > h['dr'] * 2 and await page.evaluate(f"{SP}.spot.hints") == 1, h)
    await tapat(page, L['hint']['x'], L['hint']['y'])
    check(tag + ': ...again at once: it is cooling down (no second hint)', await page.evaluate(f"{SP}.spot.hints") == 1)
    await page.screenshot(path=OUT + 'spot_mid_%s.png' % tag.lower())
    # the last one: the card
    await tapat(page, *(await diff_pt(page, 2, 'A'))); ok = await wait(page, f"{SP}.spot.over", 4000); await page.wait_for_timeout(700)
    c = await page.evaluate(f"({{ stars: {SP}.spot.starsN, coins: {SP}.spot.coins, round: meta.roundCoins, btns: Object.keys({SP}.spot.ui.buttons || {{}}), lb: {SP}.spot.ui.labels, solved: {SP}.profile().solved, saved: JSON.parse(localStorage.getItem('grasp.profile') || localStorage.getItem('profile') || '{{}}').spot }})")
    check(tag + ': all found: the card: 2 stars (a miss and a hint), +4 coins, Next + Home ("' + ('הבא' if he else 'Next') + '")', ok and c['stars'] == 2 and c['coins'] == 4 and c['round'] == 4 and c['btns'] == ['again', 'home'] and c['lb']['again'] == ('הבא' if he else 'Next'), c)
    check(tag + ': ...the puzzle is kept as solved (2 stars)', c['solved'].get(st['key']) == 2, c['solved'])
    await page.screenshot(path=OUT + 'spot_end_%s.png' % tag.lower())
    b0 = c and await page.evaluate(f"(() => {{ const r = {SP}.spot.ui.buttons.again; return [r.x + r.w / 2, r.y + r.h / 2]; }})()")
    await tapat(page, *b0); ok = await wait(page, f"{SP}.spot.ready && !{SP}.spot.over && {SP}.spot.key !== '{st['key']}'", 8000)
    k2 = await page.evaluate(f"{SP}.spot.key"); n2 = len(await page.evaluate(f"{SP}.diffs()")); nsc = await page.evaluate(f"{SP}.spot.data.scenes.length")
    check(tag + ': Next: the next puzzle (%s, %d differences)' % (k2, n2), ok and ((nsc > 1 and k2.endswith(':1') and n2 == 3) or (nsc == 1 and k2.endswith(':2') and n2 == 5)), [k2, n2, nsc])
    # Restart (the pause sheet): the same puzzle again, nothing found
    await tapat(page, *(await diff_pt(page, 0, 'A'))); await page.tap('#pauseBtn'); await wait(page, "menu.open", 3000)
    await page.click('#resetBtn'); ok = await wait(page, f"{SP}.spot.ready && {SP}.spot.found.length === 0 && {SP}.spot.key === '{k2}'", 6000)
    check(tag + ': the pause sheet\'s Restart: the same puzzle again, from the start', ok)
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def levels(b):
    # every level of the first scene: 3, 5, 7 differences, each findable in both pictures
    ctx, page, errs, ok = await spot_page(b)
    sid = await page.evaluate(f"{SP}.spot.data.scenes[0].id")
    for l, n in ((1, 3), (2, 5), (3, 7)):
        await page.evaluate(f"{SP}.start('{sid}', {l})"); await wait(page, f"{SP}.spot.ready && {SP}.spot.lvl === {l}", 8000); await page.wait_for_timeout(200)
        D = await page.evaluate(f"{SP}.diffs()")
        for i in range(len(D)): await tapat(page, *(await diff_pt(page, i, 'B' if i % 2 else 'A')))
        done = await wait(page, f"{SP}.spot.over", 4000)
        check('level %d: %d differences, all found by a tap on each (in either picture), no misses: 3 stars' % (l, n), len(D) == n and done and await page.evaluate(f"{SP}.spot.miss") == 0 and await page.evaluate(f"{SP}.spot.starsN") == 3, [len(D), await page.evaluate(f"{SP}.spot.log.slice(-3)")])
        if l == 3: await page.screenshot(path=OUT + 'spot_level3.png')
    # the circles never overlap (two differences under one tap would be unfair)
    bad = await page.evaluate(f"""(() => {{ const out = []; for (const s of {SP}.spot.data.scenes) for (const L of s.levels) L.diffs.forEach((a, i) => L.diffs.forEach((c, j) => {{ if (j > i && Math.hypot(a.x - c.x, (a.y - c.y) * s.h / s.w) < a.r + c.r) out.push(s.id + ':' + L.img + ':' + i + '/' + j); }})); return out; }})()""")
    check('the answer key: no two difference circles overlap (every scene, every level)', not bad, bad)
    check('levels: no page errors', not errs, errs); await ctx.close()

async def wide(b):
    ctx, page, errs, ok = await spot_page(b, True, 1280, 800)
    L = await page.evaluate(f"{SP}.layout()"); A, B = L['A'], L['B']
    check('HE wide (1280 x 800): side by side, the original on the right (reading order), the same height', ok and L['wide'] and A['x'] > B['x'] and abs(A['y'] - B['y']) < 1 and A['w'] > 500, L)
    await page.screenshot(path=OUT + 'spot_wide_he.png')
    check('wide: no page errors', not errs, errs); await ctx.close()

async def sticker(b):
    ctx, page, errs = await page_for(b, '/', True)
    await page.wait_for_timeout(600); lb = await page.evaluate("document.querySelector('#bigRoom [data-mode=spot] .lb').textContent")
    r = await page.evaluate("(() => [...document.querySelectorAll('#bigRoom .mbGrid > .stk')].map((b) => { const q = b.getBoundingClientRect(), l = b.querySelector('.lb').getBoundingClientRect(); return { w: q.width, h: q.height, lh: l.height, top: q.top }; }))()")
    check('HE: Big kids: four stickers in one row (Smash, Slice, Pop It, "' + lb + '"), each label on one line', len(r) == 4 and max(q['top'] for q in r) - min(q['top'] for q in r) < 4 and all(q['lh'] < 34 for q in r) and lb == 'הבדלים', r)
    await page.tap('#bigRoom [data-mode=spot]'); ok = await wait(page, "gameMode === 'spot' && mode === 'mouse' && __grasp.spot.spot.ready", 15000)
    check('HE: the sticker opens it in one tap', ok)
    check('sticker: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await play(b, he)
        await levels(b); await wide(b); await sticker(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
