exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Mix (/mix, Big kids; the owner, Oct 2026: "350 things you join into one", the merge board and the discovery game in one, for the family):
# the sticker opens it; the first time two things wait with a finger; drag one onto the other: a recipe makes a new thing in the target's
# cell (the New! card, a coin, the book), two that make nothing wobble and stay; a tap on a source drops one on the board; orders take a found
# thing for coins; the bulb names a pair; dragged onto the bulb (a bin) a thing goes; the book lists every category; a full board says so;
# all of it is kept (a reload); Hebrew mirrors the board. Screenshots: tests/out/mix_*.png
MX = '__grasp.mix'

async def drag(page, a, b, steps=8):
    await page.mouse.move(a[0], a[1]); await page.mouse.down(); await page.wait_for_timeout(40)
    for k in range(1, steps + 1): await page.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); await page.wait_for_timeout(16)
    await page.wait_for_timeout(60); await page.mouse.up(); await page.wait_for_timeout(250)
async def cell(page, i): q = await page.evaluate(f"{MX}.cellXY({i})"); return [q['x'], q['y']]
async def state(page): return await page.evaluate(f"(() => {{ const m = {MX}.mix; return {{ board: m.board.slice(), found: [...m.found], orders: m.orders.map((o) => o.id), coins: profile.coins, card: m.newCard && m.newCard.id, log: m.log.slice(-6) }}; }})()")

async def run(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true; window.__mxAutoMs = 1e9;"); await page.wait_for_timeout(700)
    await page.tap('#bigRoom [data-mode=mix]'); ok = await wait(page, f"gameMode === 'mix' && {MX}.mix.ready", 8000); await page.wait_for_timeout(500)
    s = await state(page); n0 = await page.evaluate(f"{MX}.mix.data.items.length")
    check(tag + ': the sticker opens Mix; the first time: the base four found, two things on the board, the finger', ok and len(s['found']) == 4 and sum(1 for x in s['board'] if x) == 2 and await page.evaluate(f"{MX}.mix.coach"), s)
    await page.screenshot(path=OUT + 'mix_first_%s.png' % tag.lower())
    i, j = [k for k, x in enumerate(s['board']) if x]
    c = await page.evaluate(f"{MX}.combine('{s['board'][i]}', '{s['board'][j]}')")
    await drag(page, await cell(page, i), await cell(page, j)); s2 = await state(page)
    check(tag + ': dragged one onto the other: they make %s in the target\'s cell, a New! card, +1 coin' % c, c and s2['board'][j] == c and not s2['board'][i] and c in s2['found'] and s2['card'] == c and s2['coins'] == s['coins'] + 1, s2)
    await page.wait_for_timeout(500); await page.screenshot(path=OUT + 'mix_new_%s.png' % tag.lower())
    await page.mouse.click(30, 300); await page.wait_for_timeout(200)
    check(tag + ': a tap closes the New! card; an order asks for it', not (await state(page))['card'] and c in (await state(page))['orders'])
    # no sources to tap any more (the board fills by itself): a tap on "next" drops nothing
    L = await page.evaluate(f"{MX}.layout()"); n0 = sum(1 for x in s2['board'] if x)
    await page.mouse.click(L['next']['x'], L['next']['y']); await page.wait_for_timeout(400); s3 = await state(page)
    check(tag + ': the bar: the book, "next", the bulb; a tap on "next" drops nothing', sum(1 for x in s3['board'] if x) == n0, s3['log'])
    # an order: drag the thing onto it
    k = s3['orders'].index(c); o = L['orders'][k]; coins = s3['coins']
    await drag(page, await cell(page, j), [o['x'] + o['w'] / 2, o['y'] + o['h'] / 2]); s4 = await state(page)
    check(tag + ': dragged onto its order: it goes, coins come', not s4['board'][j] and s4['coins'] > coins and any(x.startswith('order:') for x in s4['log']), s4)
    # two that make nothing: they wobble and stay
    pair = await page.evaluate(f"(() => {{ const m = {MX}.mix, F = [...m.found]; for (const a of F) for (const b of F) if (!{MX}.combine(a, b)) return [a, b]; return null; }})()")
    if pair:
        await page.evaluate(f"(() => {{ const m = {MX}.mix; m.board.fill(''); m.board[0] = '{pair[0]}'; m.board[1] = '{pair[1]}'; }})()")
        await drag(page, await cell(page, 0), await cell(page, 1)); s5 = await state(page)
        check(tag + ': two that make nothing (%s + %s): both stay, nothing lost' % tuple(pair), s5['board'][0] == pair[0] and s5['board'][1] == pair[1] and any(x.startswith('no:') for x in s5['log']), s5['log'])
    # the bin
    await drag(page, await cell(page, 0), [L['bulb']['x'], L['bulb']['y']])
    check(tag + ': dragged onto the bulb (a bin while dragging): gone', not (await state(page))['board'][0])
    # the bulb
    h = await page.evaluate(f"{MX}.hint()")
    check(tag + ': the bulb names two found things that make one not found', h and await page.evaluate(f"(() => {{ const m = {MX}.mix; return m.found.has('{h['a']}') && m.found.has('{h['b']}') && !m.found.has('{h['c']}'); }})()"), h)
    await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'mix_hint_%s.png' % tag.lower())
    # the book
    await page.evaluate(f"{MX}.mix.hint = null"); await page.mouse.click(L['book']['x'], L['book']['y']); await page.wait_for_timeout(400)
    bk = await page.evaluate("({ open: !$('mixBook').hidden, tabs: $('mxTabs').children.length, cats: __grasp.mix.mix.cats.length, found: document.querySelectorAll('#mxGrid .mxCell:not(.no)').length, n: $('mxBookN').textContent })")
    check(tag + ': the book: every category a tab, the found ones by name, the count', bk['open'] and bk['tabs'] == bk['cats'] and bk['found'] >= 1, bk)
    await page.screenshot(path=OUT + 'mix_book_%s.png' % tag.lower())
    await page.click('#mxBookX'); await page.wait_for_timeout(200); check(tag + ': the book closes', await page.evaluate("$('mixBook').hidden"))
    # a full board
    await page.evaluate(f"{MX}.mix.board.fill('water'); {MX}.mix.autoAt = 1"); await page.wait_for_timeout(300)
    check(tag + ': a full board: it says so (nothing lost)', 'full' in (await state(page))['log'])
    await page.screenshot(path=OUT + 'mix_full_%s.png' % tag.lower())
    # kept: a reload
    await page.evaluate(f"(() => {{ const m = {MX}.mix; m.board.fill(''); m.board[5] = '{c}'; }})()"); await page.evaluate("goHome()"); await page.wait_for_timeout(500)
    await page.goto(BASE + '/mix'); ok = await wait(page, f"gameMode === 'mix' && {MX}.mix.ready", 8000); s6 = await state(page)
    check(tag + ': a reload (/mix): the found things and the board are kept', ok and c in s6['found'] and s6['board'][5] == c, s6)
    if he:
        q0, q5 = await cell(page, 0), await cell(page, 5)
        check('HE: the board reads right to left (cell 0 on the right)', q0[0] > q5[0], [q0, q5])
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def auto(b):
    # the owner: "the game should make the things by itself": a basic thing lands on the board every 3 s (here 0.3 s) until it is full
    ctx, page, errs = await page_for(b, '/mix', True, init="window.__graspNoAutoFs = true; window.__mxAutoMs = 300;"); await wait(page, f"{MX}.mix.ready", 8000)
    n0 = sum(1 for x in (await state(page))['board'] if x); await page.wait_for_timeout(2000); s = await state(page); n1 = sum(1 for x in s['board'] if x)
    base = await page.evaluate(f"{MX}.mix.data.base")
    check('by itself: new basic things land on the board, nothing tapped; "next" shows the one on its way', n1 >= n0 + 3 and any(l.startswith('auto:') for l in s['log']) and await page.evaluate(f"!!{MX}.mix.nextId"), [n0, n1, s['log']])
    await page.screenshot(path=OUT + 'mix_auto.png')
    await page.evaluate(f"(() => {{ const m = {MX}.mix; for (let i = 0; i < m.board.length; i++) if (!m.board[i]) m.board[i] = 'water'; }})()"); await page.wait_for_timeout(900)
    check('a full board: nothing more lands, nothing lost', all((await state(page))['board']))
    check('auto: no page errors', not errs, errs); await ctx.close()

async def content(b):
    ctx, page, errs = await page_for(b, '/mix', False, init="window.__graspNoAutoFs = true;"); await wait(page, f"{MX}.mix.ready", 8000)
    r = await page.evaluate(f"""(() => {{ const m = {MX}.mix, d = m.data, reach = new Set(d.base); let more = true;
      while (more) {{ more = false; for (const [a, b, c] of d.r) if (reach.has(a) && reach.has(b) && !reach.has(c)) {{ reach.add(c); more = true; }} }}
      return {{ n: d.items.length, cats: d.cats.length, reach: reach.size, merges: d.r.filter(([a, b]) => a === b).length, he: d.items.every((it) => it.he && it.en && it.e) }}; }})()""")
    check('the content: every thing can be made from the base four, names in both languages', r['reach'] == r['n'] and r['he'], r)
    check('the content: 340+ things, 60+ merges of two of the same', r['n'] >= 340 and r['merges'] >= 60, r)
    check('content: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await run(b, he)
        await auto(b)
        await content(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
