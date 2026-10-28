exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Tachles (/tachles, adults only; the owner's party card game without its database): a long press on the copyright line opens it behind an
# 18+ gate; one phone passed round (a pass screen hides each hand), against bots, each on their own phone (a room code; here over a
# BroadcastChannel instead of PeerJS); a round: the black card, picks, the judge's choice, the point; a game played to its end; the deck ships
# without the two dropped groups. Screenshots: tests/out/tachles_*.png
TKH = '__grasp.tk'
async def click(page, sel): await page.click(sel); await page.wait_for_timeout(120)
async def view(page): return await page.evaluate(f"(() => {{ const t = {TKH}.tk; return {{ scr: t.scr, mode: t.mode, phase: t.view && t.view.phase, round: t.view && t.view.round, players: t.view && t.view.players.map((p) => p.score), log: t.log.slice(-4) }}; }})()")
async def step_local(page):
    # whatever this phone shows: a pass screen, cards to pick, submissions to judge, the reveal
    for sel in ['[data-a^="iam:"]', '[data-a="next"]']:
        if await page.locator('#tachles ' + sel).count(): await click(page, '#tachles ' + sel); return True
    if await page.locator('#tachles [data-a^="judge:"]').count(): await click(page, '#tachles [data-a^="judge:"] >> nth=0'); return True
    n = await page.locator('#tachles .tkWhite').count()
    if n:
        pick = await page.evaluate(f"{TKH}.tk.view ? (window.__grasp.tk.tk.mode === 'local' ? 1 : 1) : 1")
        need = await page.evaluate("(() => { const b = document.querySelector('#tachles .tkBlack i'); return b ? +(b.textContent.match(/\\d/) || [1])[0] : 1; })()")
        for i in range(need): await click(page, '#tachles .tkWhite >> nth=%d' % i)
        await click(page, '#tachles [data-a="send"]'); return True
    return False

async def gate_and_bots(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true; window.__tkFast = true;"); await page.wait_for_timeout(700)
    f = await page.evaluate("(() => { const r = $('footTap').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    await page.mouse.move(f[0], f[1]); await page.mouse.down(); await page.wait_for_timeout(1200); await page.mouse.up()
    ok = await wait(page, f"gameMode === 'tachles' && !$('tachles').hidden && {TKH}.tk.scr === 'gate'", 5000)
    check(tag + ': a long press on the copyright line opens Tachles behind the 18+ gate', ok, await page.evaluate(f"[gameMode, {TKH}.tk.scr]"))
    await page.screenshot(path=OUT + 'tachles_gate_%s.png' % tag.lower())
    await click(page, '#tachles [data-a="gate"]'); check(tag + ': "I\'m 18+": the menu (one phone / bots / own phones)', (await view(page))['scr'] == 'menu' and await page.locator('#tachles [data-a^="m:"]').count() == 3)
    await page.screenshot(path=OUT + 'tachles_menu_%s.png' % tag.lower())
    await page.select_option('#tachles select[data-a=target]', '3'); await click(page, '#tachles [data-a="m:bots"]'); await page.fill('#tkMe', 'Dana'); await click(page, '#tachles [data-a="goBots"]')
    v = await view(page); check(tag + ': against bots: a game (you + 2 bots), round 1, a black card and 7 white ones (or the judge\'s wait)', v['scr'] == 'game' and len(v['players']) == 3 and v['round'] == 1, v)
    await page.screenshot(path=OUT + 'tachles_hand_%s.png' % tag.lower())
    for k in range(200):
        v = await view(page)
        if v['phase'] == 'over': break
        if not await step_local(page): await page.wait_for_timeout(80)
    await page.wait_for_timeout(200); v = await view(page)
    check(tag + ': the game played to the end (3 points): the winner, Play again', v['phase'] == 'over' and max(v['players']) == 3 and await page.locator('#tachles [data-a="again"]').count() == 1, v)
    await page.screenshot(path=OUT + 'tachles_over_%s.png' % tag.lower())
    await page.evaluate("goHome()"); await page.wait_for_timeout(500)
    check(tag + ': Home: the sheet goes', await page.evaluate("$('tachles').hidden && mode === 'none'"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def pass_round(b):
    ctx, page, errs = await page_for(b, '/tachles', True, init="window.__graspNoAutoFs = true; window.__tkFast = true; sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu'", 6000)
    await click(page, '#tachles [data-a="m:local"]'); await click(page, '#tachles [data-a="bot-"]'); await click(page, '#tachles [data-a="bot-"]')
    for i, n in enumerate(['אבי', 'בתיה', 'גיל']): await page.fill('#tachles .tkIn[data-i="%d"]' % i, n)
    await click(page, '#tachles [data-a="goLocal"]')
    check('HE one phone (3 people, no bots): a pass screen first ("מעבירים ל…"), no hand on show', await page.locator('#tachles [data-a^="iam:"]').count() == 1 and await page.locator('#tachles .tkWhite').count() == 0)
    await page.screenshot(path=OUT + 'tachles_pass_he.png')
    seen = 0
    for k in range(40):
        v = await view(page)
        if v['phase'] == 'reveal': break
        if await page.locator('#tachles [data-a^="iam:"]').count(): seen += 1
        await step_local(page)
    check('HE one phone: each player gets the phone in turn (the pickers, then the judge), a point is given', (await view(page))['phase'] == 'reveal' and seen >= 3 and sum((await view(page))['players']) == 1, [seen, await view(page)])
    await page.screenshot(path=OUT + 'tachles_reveal_he.png')
    check('pass: no page errors', not errs, errs); await ctx.close()

async def online(b):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); errs = []
    pages = []
    for i in range(3):
        pg = await ctx.new_page(); await routes(pg); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("window.__graspNoAutoFs = true; window.__tkFast = true; window.__tkBus = 'bc'; sessionStorage.setItem('grasp.tk18', '1'); localStorage.setItem('lang','he');")
        await pg.goto(BASE + '/tachles'); await wait(pg, f"{TKH}.tk.scr === 'menu'", 8000); pages.append(pg)
    host, g1, g2 = pages
    await click(host, '#tachles [data-a="m:online"]'); await host.fill('#tkMe', 'המארח'); await click(host, '#tachles [data-a="create"]'); await host.wait_for_timeout(300)
    code = await host.evaluate(f"{TKH}.tk.code"); check('online: the host opens a room with a 4-letter code', len(code) == 4 and (await view(host))['scr'] == 'lobby', code)
    for pg, n in ((g1, 'אורח1'), (g2, 'אורח2')):
        await click(pg, '#tachles [data-a="m:online"]'); await pg.fill('#tkMe', n); await pg.fill('#tkCode', code); await click(pg, '#tachles [data-a="join"]'); await pg.wait_for_timeout(300)
    n = await host.evaluate(f"{TKH}.tk.lobby.length"); check('online: two phones join with the code: three in the room (the guests see the list too)', n == 3 and await g1.evaluate(f"({TKH}.tk.lobbyView || []).length") == 3, n)
    await host.screenshot(path=OUT + 'tachles_lobby_he.png')
    await click(host, '#tachles [data-a="hostGo"]'); await host.wait_for_timeout(400)
    vs = [await view(p) for p in pages]; check('online: the host starts: every phone in the game, round 1', all(v['scr'] == 'game' and v['round'] == 1 for v in vs), vs)
    hands = [await p.evaluate(f"{TKH}.tk.view.hand.join('|')") for p in pages]; check('online: each phone sees only its own hand (three different hands)', len(set(hands)) == 3, [h[:30] for h in hands])
    await g1.screenshot(path=OUT + 'tachles_guest_he.png')
    for k in range(30):
        if (await view(host))['phase'] == 'reveal': break
        for p in pages: await step_local(p)
        await host.wait_for_timeout(150)
    v = await view(host); check('online: everyone answers, the judge (on their own phone) picks: a point, every phone sees the reveal', v['phase'] == 'reveal' and sum(v['players']) == 1 and (await view(g2))['phase'] == 'reveal', [v, await view(g2)])
    await g2.screenshot(path=OUT + 'tachles_online_reveal_he.png')
    check('online: no page errors', not errs, errs); await ctx.close()

async def deck(b):
    ctx, page, errs = await page_for(b, '/tachles', True, init="sessionStorage.setItem('grasp.tk18', '1');"); await page.wait_for_timeout(1200)
    d = await page.evaluate(f"{TKH}.tk.deck")
    bad = [c for c in d['w'] + [x[0] for x in d['b']] if any(k in c for k in ('פדופיל', 'הסבא שמשפץ', 'תינוק עם זין', 'הזין של הרב עובדיה', 'יואב גלנט שמכניס'))]
    check('the deck: 100+ black and 400 white cards, without the two dropped groups', len(d['b']) >= 100 and len(d['w']) >= 400 and not bad, [len(d['b']), len(d['w']), bad])
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (True, False): await gate_and_bots(b, he)
        await pass_round(b); await online(b); await deck(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
