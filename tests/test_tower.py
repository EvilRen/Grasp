exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Smash is the Tower now (the owner, Oct 2026: Smash "isn't fun, it isn't clear what to do"; from the smash lab he picked the tower): knock every block
# off the table, a tap = a blast where the finger lands. The sticker starts the next tower at once (no map); the count of what is left; glass
# shatters, TNT goes off; the card: stars by taps, coins, Next tower; profile.tower; Restart = the same tower; Home; the pause sheet has no Map.
# Screenshots: tests/out/tower_*.png

TW = '__grasp.tower'
LOWEST = """(() => { if (smash.over) return 'over'; const T = tower.table; const l = tower.blocks.filter(b => !b.tw.gone && b.position.y < T.y + 4 && Math.abs(b.position.x - T.x) < T.w / 2 + 10);
  if (!l.length) return 'wait'; l.sort((a, c) => c.position.y - a.position.y); const b = l[0]; return [b.position.x + (b.position.x < T.x ? 6 : -6), b.position.y]; })()"""

async def clear(page, maxtaps=16):
    taps = 0
    while taps < maxtaps:
        T = await page.evaluate(LOWEST)
        if T == 'over': return True
        if T == 'wait': await page.wait_for_timeout(250); continue
        await page.touchscreen.tap(T[0], T[1]); taps += 1; await page.wait_for_timeout(1200)
    return await wait(page, "smash.over", 3000)

async def run(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(800)
    await page.tap('#start button[data-mode="smash"]'); ok = await wait(page, "mode !== 'none' && gameMode === 'smash' && smash.run === 'tower' && !!tower.table", 8000)
    s = await page.evaluate(f"({{ map: !$('smashMap').hidden, left: {TW}.left(), n: tower.plan.n, mats: tower.plan.mats, king: !!tower.blocks.find(b => b.tw.mat === 'king') }})")
    check(tag + ': the Smash sticker starts tower 1 at once (no map): blocks on the table, a king on top', ok and not s['map'] and s['n'] == 1 and s['left'] >= 6 and s['king'], s)
    await page.wait_for_timeout(900); await page.screenshot(path=OUT + 'tower_start_%s.png' % tag.lower())
    l0 = s['left']; T = await page.evaluate(LOWEST); await page.touchscreen.tap(T[0], T[1]); await page.wait_for_timeout(1300)
    l1 = await page.evaluate(f"{TW}.left()")
    check(tag + ': one tap blasts blocks off the table (the count drops)', l1 < l0, [l0, l1])
    c0 = await page.evaluate("profile.coins")
    done = await clear(page); await page.wait_for_timeout(900)
    r = await page.evaluate("({ res: smash.result, coins: profile.coins, prof: { ...profile.tower }, btns: Object.keys(smash.ui.buttons || {}) })")
    check(tag + ': the table cleared: the card (stars by taps, coins), the next tower saved', done and r['res'] and r['res']['tower'] and 1 <= r['res']['stars'] <= 3 and r['coins'] > c0 and r['prof']['n'] == 2, r)
    check(tag + ': the card has Next tower and Home (no Map)', 'again' in r['btns'] and 'home' in r['btns'] and 'map' not in r['btns'], r['btns'])
    await page.screenshot(path=OUT + 'tower_card_%s.png' % tag.lower())
    B = await page.evaluate("(() => { const q = smash.ui.buttons.again; return [q.x + q.w / 2, q.y + q.h / 2]; })()"); await page.touchscreen.tap(B[0], B[1])
    ok = await wait(page, "!smash.over && tower.plan && tower.plan.n === 2", 4000)
    check(tag + ': Next tower: tower 2 (planks join)', ok and 'plank' in await page.evaluate("tower.plan.mats"), await page.evaluate("[smash.over, tower.plan && tower.plan.n]"))
    await page.evaluate("openMenu()"); await page.wait_for_timeout(400)
    check(tag + ': the pause sheet: no Map row for the tower', await page.evaluate("$('menuMap').hidden || getComputedStyle($('menuMap')).display === 'none'"))
    await page.evaluate("$('restartBtn') ? $('restartBtn').click() : $('resetBtn').click()"); await page.wait_for_timeout(900)
    check(tag + ': Restart: the same tower again, from the start', await page.evaluate("!menu.open && tower.plan.n === 2 && tower.taps === 0 && !smash.over"))
    await page.evaluate("goHome()"); ok = await wait(page, "mode === 'none' && !$('start').hidden", 4000)
    ok = ok and await wait(page, "document.querySelector('#start button[data-mode=\"smash\"] .best').textContent.includes('1')", 3000)
    check(tag + ': Home: the start screen, the sticker shows the tower reached', ok, await page.evaluate("document.querySelector('#start button[data-mode=\"smash\"] .best').textContent"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def materials(b):
    ctx, page, errs = await page_for(b, '/', False, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(600)
    await page.tap('#start button[data-mode="smash"]'); await wait(page, "!!tower.table", 8000)
    P = await page.evaluate("[1, 2, 3, 5, 7].map((n) => twPlan(n).mats.join('+'))")
    check('materials join with the towers: box; +plank (2); +glass (3); +TNT (5); +stone (7)', P == ['box', 'box+plank', 'box+plank+glass', 'box+plank+glass+tnt', 'box+plank+glass+tnt+stone'], P)
    K = await page.evaluate("[1, 2, 3, 4, 5, 6].map((n) => twPlan(n).king.id)")
    check('a different king each tower (five, round and round)', len(set(K[:5])) == 5 and K[5] == K[0], K)
    await page.evaluate("profile.tower.n = 6; towerNext()"); await page.wait_for_timeout(900)
    tnt = await page.evaluate("tower.blocks.find(b => b.tw.mat === 'tnt')")
    if tnt is not None:
        await page.evaluate("(() => { const b = tower.blocks.find(q => q.tw.mat === 'tnt'); towerTap(b.position.x, b.position.y, performance.now()); })()"); await page.wait_for_timeout(500)
        check('TNT in a blast goes off (its own bigger blast)', 'tnt' in await page.evaluate("tower.log"), await page.evaluate("tower.log.slice(-5)"))
    gl = await page.evaluate("tower.blocks.some(b => b.tw.mat === 'glass' && !b.tw.gone)")
    if gl:
        await page.evaluate("(() => { const b = tower.blocks.find(q => q.tw.mat === 'glass' && !q.tw.gone); towerTap(b.position.x, b.position.y, performance.now()); })()"); await page.wait_for_timeout(300)
        check('glass in a blast shatters', 'glass' in await page.evaluate("tower.log"))
    await page.screenshot(path=OUT + 'tower_tnt.png')
    check('materials: no page errors', not errs, errs); await ctx.close()

async def zoo(b):
    # the owner: "funny animals to blow up", off by default (Settings: "Tower: animals"): 2-4 on the top blocks; "I wanted animals that break into
    # pieces": blasted, an animal breaks into chunks of its drawing that fly, spin, fall and fade
    ctx, page, errs = await page_for(b, '/', True, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(600)
    await page.tap('#start button[data-mode="smash"]'); await wait(page, "!!tower.table", 8000)
    check('zoo: off by default: no animals on the tower', await page.evaluate("tower.blocks.filter(b => b.tw.mat === 'animal').length") == 0)
    await page.evaluate("goHome()"); await page.wait_for_timeout(500)
    await page.tap('#settingsBtn'); await page.wait_for_timeout(300); await page.tap('#moreZoo'); await page.wait_for_timeout(200)
    check('zoo: Settings has "🐷 מגדל: חיות", a tap turns it on (kept)', await page.evaluate("$('moreZoo').getAttribute('aria-pressed') === 'true' && localStorage.getItem('grasp.fun.towerZoo') === '1'"))
    await page.evaluate("document.querySelector('#moreSheet .xBtn').click()"); await page.wait_for_timeout(300)
    await page.tap('#start button[data-mode="smash"]'); await wait(page, "!!tower.table && tower.blocks.some(b => b.tw.mat === 'animal')", 8000)
    A = await page.evaluate("tower.blocks.filter(b => b.tw.mat === 'animal').map(b => [b.tw.kind, b.tw.poof])")
    check('zoo: 2-4 cartoon animals sit on the top blocks', 2 <= len(A) <= 4, A); await page.wait_for_timeout(700); await page.screenshot(path=OUT + 'tower_zoo.png')
    await page.evaluate("(() => { const b = tower.blocks.filter(q => q.tw.mat === 'animal')[0]; towerTap(b.position.x, b.position.y + 4, performance.now()); })()"); await page.wait_for_timeout(250)
    await page.screenshot(path=OUT + 'tower_zoo_break.png')
    k = await page.evaluate("[tower.log.filter(x => x.startsWith('animal:')), (tower.bits || []).length, tg.snd.filter(x => x.startsWith('an_')).length]")
    check('zoo: a blasted animal breaks into 6-7 chunks of its drawing that fly off, with its voice', 'animal:break' in k[0] and 6 <= k[1] <= 14 and k[2] >= 1, k)
    await page.wait_for_timeout(2800); check('zoo: the chunks fall and fade away', await page.evaluate("(tower.bits || []).length") == 0)
    check('zoo: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (True, False): await run(b, he)
        await materials(b); await zoo(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
