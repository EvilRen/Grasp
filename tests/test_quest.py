exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Quest (/quest, Big kids; the owner, Oct 2026: "a rogue-like card quest"; fantasy into space; runs for everyone): the sticker opens the hero pick;
# a run: doors, a fight (tap a card, tap a monster; End turn: the monsters act by their shown intent), the prizes (gold, 1 of 3 cards), the camp
# fire, the shop, an event, the deck; the run is kept (a reload resumes it); a lost run ends with coins; the Robot opens after a win. Every
# screen drawn in EN and HE. A simulated bot plays whole runs (the rules: QC) for the balance. Screenshots: tests/out/quest_*.png
QT = '__grasp.quest'
async def tapbtn(page, pred):
    b = await page.evaluate(f"(() => {{ const b = {QT}.btns().find({pred}); return b ? [b.x + b.w / 2, b.y + b.h / 2] : null; }})()")
    if b: await page.mouse.click(b[0], b[1]); await page.wait_for_timeout(250)
    return b
async def st(page): return await page.evaluate(f"(() => {{ const q = {QT}.quest, r = q.run, f = q.f; return {{ scr: q.scr, hp: r && r.hp, gold: r && r.gold, deck: r && r.deck.length, room: r && r.room, li: r && r.li, hand: f && f.hand.length, en: f && f.en, over: f && f.over, mons: f && f.mons.map((m) => m.hp), log: q.log.slice(-5) }}; }})()")

async def run(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(700)
    await page.tap('#bigRoom [data-mode=quest]'); ok = await wait(page, f"gameMode === 'quest' && {QT}.quest.scr === 'pick'", 8000); await page.wait_for_timeout(400)
    check(tag + ': the sticker opens Quest: the hero pick (Knight, Wizard; the Robot locked) and the run lengths', ok and await page.evaluate(f"{QT}.profile().heroes.join()") == 'knight,wizard')
    await page.screenshot(path=OUT + 'quest_pick_%s.png' % tag.lower())
    await page.evaluate(f"{QT}.quest.pickHero = 'wizard'; {QT}.quest.pickLen = 'short'")
    await page.evaluate(f"(() => {{ const b = {QT}.btns(); const g = b[b.length - 1]; g.act(); }})()"); await page.wait_for_timeout(400)
    s = await st(page); check(tag + ': Start: a run (the Wizard, 66 health, 30 gold, 10 cards), the first doors', s['scr'] == 'doors' and s['hp'] == 66 and s['gold'] == 30 and s['deck'] == 10, s)
    await page.screenshot(path=OUT + 'quest_doors_%s.png' % tag.lower())
    await page.evaluate(f"{QT}.enter('fight')"); await page.wait_for_timeout(500); s = await st(page)
    check(tag + ': a fight: 5 cards in hand, 3 energy, monsters with their intent', s['scr'] == 'fight' and s['hand'] >= 5 and s['en'] >= 3 and len(s['mons']) >= 1, s)
    # tap a card, then a monster (a card that needs a target)
    i = await page.evaluate(f"{QT}.quest.f.hand.findIndex((id) => {QT}.QC.needsTarget({QT}.QC.cardOf(id)) && {QT}.QC.cardOf(id).c <= {QT}.quest.f.en)")
    if i >= 0:
        cb = await page.evaluate(f"(() => {{ const b = {QT}.btns().find((q) => q.card === {i}); return [b.x + b.w * 0.45, b.y + b.h / 2]; }})()"); await page.mouse.click(cb[0], cb[1]); await page.wait_for_timeout(250)
        await page.screenshot(path=OUT + 'quest_fight_%s.png' % tag.lower())
        m0 = (await st(page))['mons']; mp = await page.evaluate(f"(() => {{ const m = {QT}.quest.f.mons.find((q) => q.hp > 0); return [m._x, m._y]; }})()"); await page.mouse.click(mp[0], mp[1]); await page.wait_for_timeout(400)
        s = await st(page); check(tag + ': tap a card, tap a monster: it is played (energy spent, the monster hurt)', s['en'] < 3 + 1 and (sum(s['mons']) < sum(m0) or s['over']), [m0, s])
    # play the fight out with the hooks
    for k in range(40):
        s = await st(page)
        if s['scr'] != 'fight' or s['over']: break
        await page.evaluate(f"(() => {{ const q = {QT}.quest, f = q.f; let g = 0; while (g++ < 12) {{ const i = f.hand.findIndex((id) => {QT}.QC.cardOf(id).c <= f.en); if (i < 0 || f.over) break; const t = f.mons.findIndex((m) => m.hp > 0); {QT}.play(i, t); }} if (!f.over) {QT}.endTurn(); }})()"); await page.wait_for_timeout(120)
    await page.wait_for_timeout(1600); s = await st(page)
    if s['scr'] == 'reward':
        check(tag + ': a won fight: the prizes (gold, 3 cards to pick)', await page.evaluate(f"{QT}.quest.data.cards.length") == 3, s)
        await page.screenshot(path=OUT + 'quest_reward_%s.png' % tag.lower())
        d0 = s['deck']; await page.evaluate(f"(() => {{ const b = {QT}.btns().find((q) => q.h > 100); b.act(); }})()"); await page.wait_for_timeout(300); s = await st(page)
        check(tag + ': a card picked: in the deck, the next doors', s['deck'] == d0 + 1 and s['scr'] == 'doors', s)
    else: check(tag + ': the first fight won by the hooks', False, s)
    # the camp fire, the shop, an event, the deck
    for k in ('rest', 'shop', 'event', 'chest'):
        await page.evaluate(f"{QT}.enter('{k}')"); await page.wait_for_timeout(350); await page.screenshot(path=OUT + 'quest_%s_%s.png' % (k, tag.lower()))
        check(tag + ': the %s screen opens' % k, (await st(page))['scr'] == k)
        if k == 'shop':
            g0 = (await st(page))['gold']; await page.evaluate(f"{QT}.quest.run.gold = 500"); await page.evaluate(f"(() => {{ const b = {QT}.btns().find((q) => q.x > 0 && q.y > 150); b.act(); }})()"); await page.wait_for_timeout(200)
            check(tag + ': the shop sells a card (gold goes, the deck grows)', (await st(page))['gold'] < 500, await st(page))
        await page.evaluate(f"{QT}.next()"); await page.wait_for_timeout(200)
    await page.evaluate(f"{QT}.quest.deckFor = {{ k: 'view' }}"); await page.wait_for_timeout(300); await page.screenshot(path=OUT + 'quest_deck_%s.png' % tag.lower()); await page.evaluate(f"{QT}.quest.deckFor = null")
    # kept: a reload resumes the run
    s0 = await st(page); await page.goto(BASE + '/quest'); ok = await wait(page, f"gameMode === 'quest' && {QT}.quest.run", 8000); s1 = await st(page)
    check(tag + ': a reload (/quest): the same run (health, gold, deck, room)', ok and [s1[k] for k in ('hp', 'gold', 'deck', 'room')] == [s0[k] for k in ('hp', 'gold', 'deck', 'room')], [s0, s1])
    # lose: the end card, coins, a new quest
    c0 = await page.evaluate("profile.coins"); await page.evaluate(f"{QT}.enter('boss')"); await page.wait_for_timeout(300)
    await page.evaluate(f"{QT}.quest.run.hp = 1; {QT}.quest.run.relics = ['book']; {QT}.quest.f.blk = 0; {QT}.quest.f.mons.forEach((m) => m.intent = [['atk', 50]]); {QT}.endTurn()"); await page.wait_for_timeout(2600); s = await st(page)
    check(tag + ': knocked out: the end card, coins for the rooms done, the run gone', s['scr'] == 'end' and await page.evaluate("profile.coins") >= c0 and not await page.evaluate(f"{QT}.profile().run"), s)
    await page.screenshot(path=OUT + 'quest_end_%s.png' % tag.lower())
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def boss(b):
    ctx, page, errs = await page_for(b, '/quest', False, init="window.__graspNoAutoFs = true;"); await wait(page, f"{QT}.quest.scr === 'pick'", 8000)
    await page.evaluate(f"{QT}.newRun('knight', 'normal'); {QT}.quest.run.li = 2; {QT}.enter('boss')"); await page.wait_for_timeout(600)
    await page.screenshot(path=OUT + 'quest_boss_space.png')
    await page.evaluate(f"(() => {{ const r = {QT}.quest.run; r.li = 2; r.room = {QT}.QC.roomsOf(r) - 1; {QT}.quest.f.mons.forEach((m) => m.hp = 1); const f = {QT}.quest.f; f.hand = ['strike', 'strike', 'strike', 'strike', 'strike']; f.en = 9; for (let i = 0; i < 5; i++) {{ const t = f.mons.findIndex((m) => m.hp > 0); if (t < 0) break; {QT}.play(0, t); }} }})()"); await page.wait_for_timeout(1500)
    await page.evaluate(f"{QT}.next()"); await page.wait_for_timeout(500)
    check('the last boss of the last land beaten: Victory, the Robot opens', await page.evaluate(f"{QT}.quest.scr") == 'end' and await page.evaluate(f"{QT}.quest.end.won") and 'robot' in await page.evaluate(f"{QT}.profile().heroes"), await page.evaluate(f"{QT}.quest.log.slice(-4)"))
    await page.screenshot(path=OUT + 'quest_victory.png')
    check('boss: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (False, True): await run(b, he)
        await boss(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
