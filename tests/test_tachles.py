exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Tachles (/tachles, adults only; the owner's party card game without its database): a long press on the copyright line opens it behind an
# 18+ gate; one phone passed round (a pass screen hides each hand), against bots, each on their own phone (a room code; here over a
# BroadcastChannel instead of PeerJS); a round: the black card, picks, the judge's choice, the point; a game played to its end; the deck ships
# without the two dropped groups. Screenshots: tests/out/tachles_*.png
TKH = '__grasp.tk'
JUDGED = []
BACKS = []
async def click(page, sel): await page.click(sel); await page.wait_for_timeout(120)
async def view(page): return await page.evaluate(f"(() => {{ const t = {TKH}.tk; return {{ scr: t.scr, mode: t.mode, phase: t.view && t.view.phase, round: t.view && t.view.round, players: t.view && t.view.players.map((p) => p.score), log: t.log.slice(-4) }}; }})()")
async def step_local(page):
    # whatever this phone shows: a pass screen, cards to pick, answers to judge (the reveal moves on by itself)
    if await page.locator('#tachles [data-a^="iam:"]').count(): await click(page, '#tachles [data-a^="iam:"]'); return True
    if await page.locator('#tachles .tkCrownB').count(): # judging, the czar: the answers in the hand, a gold background; one into the zone, then the crown
        if not JUDGED:
            JUDGED.append(1); g0 = await page.evaluate("[$('tachles').classList.contains('tkJudge'), document.querySelectorAll('#tachles .tkJC').length, !!document.querySelector('#tachles .tkCrownB[disabled]'), !!document.querySelector('#tachles .tkJudgeT')]")
            check('judging: the answers as a hand of cards, a gold background and a "judging" line, the crown off until one is chosen (the owner)', g0[0] and g0[1] >= 1 and g0[2] and g0[3], g0)
            z = await page.evaluate("(() => { const r = document.querySelector('#tachles .tkSlots').getBoundingClientRect(), c = document.querySelectorAll('#tachles .tkJC')[0]; c.scrollIntoView({ inline: 'center', block: 'nearest' }); const q = c.getBoundingClientRect(); return [q.left + q.width / 2, q.top + q.height / 2, r.left + r.width / 2, r.top + r.height / 2]; })()")
            await page.wait_for_timeout(150); await page.mouse.move(z[0], z[1]); await page.mouse.down()
            for k in range(1, 13): await page.mouse.move(z[0] + (z[2] - z[0]) * k / 12, z[1] + (z[3] - z[1]) * k / 12); await page.wait_for_timeout(20)
            await page.mouse.up(); await page.wait_for_timeout(200); await page.screenshot(path=OUT + 'tachles_judge.png')
            check('judging: the czar drags the best answer into the zone by the question; the crown button lights', await page.evaluate(f"{TKH}.tk.jsel") == 0 and await page.locator('#tachles .tkSlot.full').count() == 1 and await page.locator('#tachles .tkCrownB[disabled]').count() == 0)
        else:
            await page.evaluate("document.querySelectorAll('#tachles .tkJC')[0].scrollIntoView({ inline: 'center', block: 'nearest' })"); await page.wait_for_timeout(120); await click(page, '#tachles .tkJC >> nth=0')
            if await page.locator('#tachles .tkCrownB[disabled]').count(): await page.wait_for_timeout(500); await click(page, '#tachles .tkJC >> nth=0') # (the hand's snap may have put the other card in the middle: the first tap brings this one over, like a person tapping twice)
        await click(page, '#tachles .tkCrownB'); return True
    if await page.locator('#tachles [data-a^="judge:"]').count(): await click(page, '#tachles [data-a^="judge:"] >> nth=0'); return True
    if await page.locator('#tachles .tkJC').count(): return False
    if await page.evaluate(f"(() => {{ const t = {TKH}.tk, v = t.mode === 'local' ? null : t.view; return !!v && v.phase === 'pick' && v.me === v.judge; }})()"): return False # (the czar waits while the others choose)
    n = await page.locator('#tachles .tkHC').count()
    if n:
        need = await page.evaluate(f"{TKH}.tk.view ? (({TKH}.tk.mode === 'local' && {TKH}.tk.g) ? {TKH}.TK.view({TKH}.tk.g, 'x').pick : {TKH}.tk.view.pick) : 1")
        await page.evaluate(f"{TKH}.tk.sel = []")
        for i in range(need):
            await page.evaluate("document.querySelectorAll('#tachles .tkHC')[%d].scrollIntoView({ inline: 'center', block: 'nearest' })" % i); await page.wait_for_timeout(120); await click(page, '#tachles .tkHC >> nth=%d' % i)
            if len(await page.evaluate(f"{TKH}.tk.sel")) <= i: await page.wait_for_timeout(500); await click(page, '#tachles .tkHC >> nth=%d' % i) # (the hand's snap may have put another card in the middle: the first tap brought this one over)
        if not await page.locator('#tachles [data-a="send"]').count(): return False # (the round moved on meanwhile: look again)
        await click(page, '#tachles [data-a="send"]')
        if not BACKS and await page.locator('#tachles .tkBacks').count():
            BACKS.append(1); bk = await page.evaluate("[document.querySelectorAll('#tachles .tkBacks .tkBackC:not(.wait)').length, document.querySelectorAll('#tachles .tkScores .tkSt').length]")
            check('after answering: the answers in so far lie face down (one per answer), the players\' strip marks the judge / still choosing / done', bk[0] >= 1 and bk[1] >= 2, bk)
        return True
    return False
FAST = "window.__graspNoAutoFs = true; window.__tkFast = true; window.__tkReveal = 250;"

async def gate_and_bots(b, he):
    tag = 'HE' if he else 'EN'
    ctx, page, errs = await page_for(b, '/', he, init=FAST); await page.wait_for_timeout(700)
    f = await page.evaluate("(() => { const r = $('footTap').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    await page.mouse.move(f[0], f[1]); await page.mouse.down(); await page.wait_for_timeout(1200); await page.mouse.up()
    ok = await wait(page, f"gameMode === 'tachles' && !$('tachles').hidden && {TKH}.tk.scr === 'gate'", 5000)
    check(tag + ': a long press on the copyright line opens Tachles behind the 18+ gate (the original\'s: 🔞, the neon title)', ok and await page.locator('#tachles .tkNeon').count() == 1, await page.evaluate(f"[gameMode, {TKH}.tk.scr]"))
    await page.screenshot(path=OUT + 'tachles_gate_%s.png' % tag.lower())
    check(tag + ': no corner buttons in Tachles (the home / full-screen chips are hidden)', await page.evaluate("getComputedStyle($('pauseBtn')).display === 'none' && getComputedStyle(document.querySelector('.chrome')).display === 'none'"))
    await click(page, '#tachles [data-a="gate"]')
    check(tag + ': "I\'m 18+": the original\'s menu (create, join) and ours (bots, one phone)', (await view(page))['scr'] == 'menu' and all([await page.locator('#tachles [data-a="m:%s"]' % k).count() == 1 for k in ('create', 'join', 'bots', 'local')]))
    await page.screenshot(path=OUT + 'tachles_menu_%s.png' % tag.lower())
    await page.evaluate("localStorage.setItem('grasp.tk', JSON.stringify({ me: 'Lemonade 54' }))"); await page.evaluate(f"{TKH}.start()"); await page.wait_for_timeout(200)
    await click(page, '#tachles [data-a="m:bots"]')
    nick = await page.evaluate(f"{TKH}.tk.lobby[0].name")
    check(tag + ': against bots: straight into the room (no name screen); an old English nickname became a Hebrew snack one', (await view(page))['scr'] == 'lobby' and not nick.startswith('Lemonade') and await page.locator('#tachles .tkPl.me').count() == 1, nick)
    await click(page, '#tachles [data-a="rename"]'); check(tag + ': ✏️ on your row: the nickname box ("your nickname in the game"), its avatar, shuffle', await page.locator('#tachles .tkModal #tkMe').count() == 1 and await page.locator('#tachles .tkModal .tkNickL').count() == 1)
    await click(page, '#tachles [data-a="shuffle"]'); n2 = await page.input_value('#tkMe'); check(tag + ': shuffle: another nickname', n2 != nick, [nick, n2])
    await page.screenshot(path=OUT + 'tachles_rename_%s.png' % tag.lower())
    await page.fill('#tkMe', 'Dana'); await click(page, '#tachles [data-a="renameOk"]')
    L = await page.evaluate(f"{TKH}.tk.lobby.map((p) => p.name)")
    check(tag + ': each bot shows its taste ("אוהב …")', await page.locator('#tachles .tkPl .tkTaste').count() == 2 and 'אוהב' in await page.inner_text('#tachles .tkPl .tkTaste >> nth=0'))
    check(tag + ': a room with you and two bots ("BOT-<snack>"), avatars, Add bot, Settings, Start', (await view(page))['scr'] == 'lobby' and len(L) == 3 and all(x.startswith('BOT-') for x in L[1:]) and await page.locator('#tachles .tkPl .tkAv').count() == 3 and await page.locator('#tachles [data-a="start"]').count() == 1, L)
    for i in range(2): await click(page, '#tachles [data-a="addBot"]')
    check(tag + ': four bots at most (the button says so)', await page.evaluate(f"{TKH}.tk.lobby.length") == 5 and await page.locator('#tachles [data-a="addBot"][disabled]').count() == 1)
    await click(page, '#tachles [data-a^="kick:"] >> nth=0'); check(tag + ': a kick asks first', await page.locator('#tachles .tkModal [data-a="kickOk"]').count() == 1)
    await click(page, '#tachles [data-a="kickOk"]'); await click(page, '#tachles [data-a^="kick:"] >> nth=0'); await click(page, '#tachles [data-a="kickOk"]')
    check(tag + ': two bots kicked', await page.evaluate(f"{TKH}.tk.lobby.length") == 3)
    await click(page, '#tachles [data-a="set"]'); await page.screenshot(path=OUT + 'tachles_settings_modal_%s.png' % tag.lower())
    await click(page, '#tachles [data-a="ws-"]'); await click(page, '#tachles [data-a="ws-"]'); await click(page, '#tachles [data-a="hs-"]'); await click(page, '#tachles [data-a="tm+"]')
    S = await page.evaluate(f"{TKH}.tk.set"); check(tag + ': room settings: points to win 3, hand 6, round time 90 s', {k: S[k] for k in ('target', 'hand', 'timer')} == {'target': 3, 'hand': 6, 'timer': 90}, S)
    await click(page, '#tachles .tkMHead [data-a="mclose"]'); await page.screenshot(path=OUT + 'tachles_lobby_%s.png' % tag.lower()); await click(page, '#tachles [data-a="start"]')
    v = await view(page); check(tag + ': the game: round 1, the scores strip (avatars, a crown on the czar), the black card', v['scr'] == 'game' and len(v['players']) == 3 and v['round'] == 1 and await page.locator('#tachles .tkScores .tkAv').count() == 3 and await page.locator('#tachles .tkScores .tkCrown').count() == 1 and await page.locator('#tachles .tkBlackC').count() == 1, v)
    if await page.evaluate(f"{TKH}.tk.view.judge !== 'h'"):
        check(tag + ': a hand of 6 cards in a row, the round clock ring', await page.locator('#tachles .tkHC').count() == 6 and await page.locator('#tachles #tkTimer svg').count() == 1)
        await page.evaluate("document.querySelectorAll('#tachles .tkHC')[2].scrollIntoView({ inline: 'center', block: 'nearest' })"); await page.wait_for_timeout(300)
        check(tag + ': the hand is held: the middle card straight, the others tilted; a dot each, the middle one marked', await page.evaluate("(() => { const c = [...document.querySelectorAll('#tachles .tkHC')]; return c[2].style.transform.includes('rotate(0') && !c[0].style.transform.includes('rotate(0') && document.querySelectorAll('#tachles .tkDots i').length === c.length && document.querySelectorAll('#tachles .tkDots i')[2].classList.contains('cur'); })()"))
        q = await page.evaluate("(() => { const r = document.querySelectorAll('#tachles .tkHC')[1].getBoundingClientRect(), m = document.querySelectorAll('#tachles .tkHC')[2].getBoundingClientRect(), x = r.left < m.left ? Math.min(r.right, m.left) - 15 : Math.max(r.left, m.right) + 15; return [x, r.top + r.height / 2]; })()")
        await page.mouse.click(q[0], q[1]); await page.wait_for_timeout(600)
        check(tag + ': a tap on a side card brings it to the middle (not picked yet)', await page.evaluate(f"{TKH}.tk.sel.length") == 0 and await page.evaluate("document.querySelectorAll('#tachles .tkDots i')[1].classList.contains('cur')"))
        q = await page.evaluate("(() => { const r = document.querySelectorAll('#tachles .tkHC')[1].getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        await page.mouse.click(q[0], q[1]); await page.wait_for_timeout(200); check(tag + ': a tap on the middle card picks it', await page.evaluate(f"{TKH}.tk.sel") == [1])
        dz = await page.evaluate("(() => { const d = document.querySelector('#tachles .tkDuel'), q = d && d.querySelector('.tkBlackC').getBoundingClientRect(), z = d && d.querySelector('.tkSlots').getBoundingClientRect(); return d ? { qx: q.left + q.width / 2, zx: z.left + z.width / 2, zy: z.top + z.height / 2, full: d.querySelectorAll('.tkSlot.full').length, txt: (d.querySelector('.tkSlot.full p') || {}).textContent } : null; })()")
        hand1 = await page.evaluate(f"{TKH}.tk.view.hand[1]")
        check(tag + ': choosing: the question is a card on the right, the drop zone on the left (the owner), the picked card sits in it', dz and dz['qx'] > dz['zx'] and dz['full'] == 1 and dz['txt'] == hand1, dz)
        await click(page, '#tachles [data-a="unsel:0"]'); check(tag + ': a tap on the card in the zone takes it back', await page.evaluate(f"{TKH}.tk.sel") == [] and await page.locator('#tachles .tkSlot.empty').count() == await page.evaluate(f"{TKH}.tk.view.pick"))
        c = await page.evaluate("(() => { const r = document.querySelectorAll('#tachles .tkHC')[1].getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
        await page.mouse.move(c[0], c[1]); await page.mouse.down()
        for k in range(1, 13): await page.mouse.move(c[0] + (dz['zx'] - c[0]) * k / 12, c[1] + (dz['zy'] - c[1]) * k / 12); await page.wait_for_timeout(20)
        gh = await page.locator('#tachles .tkGhost').count(); hot = await page.locator('#tachles .tkSlots.hot').count(); await page.screenshot(path=OUT + 'tachles_drag_%s.png' % tag.lower())
        await page.mouse.up(); await page.wait_for_timeout(200)
        check(tag + ': dragging a hand card up: a ghost follows the finger, the zone lights, the drop picks it', gh == 1 and hot == 1 and await page.evaluate(f"{TKH}.tk.sel") == [1] and await page.locator('#tachles .tkGhost').count() == 0, [gh, hot, await page.evaluate(f"{TKH}.tk.sel")])
        check(tag + ': while picking, the question stays clean (the whole sentence only at the judging and the reveal)', await page.locator('#tachles .tkBlackC mark').count() == 0)
        for top in (1, 0):
            cov = await page.evaluate("((top) => { const T = $('tachles'); [T, ...T.querySelectorAll('*')].forEach((e) => { if (e.scrollHeight > e.clientHeight + 2 && !e.classList.contains('tkHandW')) e.scrollTop = top ? 0 : e.scrollHeight; }); const s = document.querySelector('#tachles [data-a=\"send\"]'), r = s.getBoundingClientRect(), x = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!(x && s.contains(x)); })(%d)" % top)
            check(tag + ': the submit button is never under the cards (scrolled to the ' + ('top' if top else 'bottom') + ')', cov)
        await page.screenshot(path=OUT + 'tachles_hand_%s.png' % tag.lower())
        h0 = await page.evaluate(f"{TKH}.tk.view.hand.join('|')")
        check(tag + ': a "החלף (3)" button next to Submit', (await page.inner_text('#tachles [data-a="swap"]')).strip() == 'החלף (3)')
        await click(page, '#tachles [data-a="swap"]'); await page.wait_for_timeout(200)
        h1 = await page.evaluate(f"{TKH}.tk.view.hand"); check(tag + ': swap: a whole new hand, the pick cleared, 2 swaps left', not set(h1) & set(h0.split('|')) and len(h1) == 6 and await page.evaluate(f"{TKH}.tk.sel") == [] and await page.evaluate(f"{TKH}.tk.view.swaps") == 2, h1)
        for _ in range(2): await click(page, '#tachles [data-a="swap"]')
        check(tag + ': after 3 swaps the button is off', await page.locator('#tachles [data-a="swap"][disabled]').count() == 1)
        seen = await page.evaluate("JSON.parse(localStorage.getItem('grasp.tkSeen') || '[]').length")
        check(tag + ': the cards shown are remembered on this phone (4 hands + the question)', seen >= 4 * 6, seen)
    else: await page.screenshot(path=OUT + 'tachles_czar_%s.png' % tag.lower())
    shot = False
    for k in range(300):
        v = await view(page)
        if v['phase'] == 'over': break
        if v['phase'] == 'reveal' and not shot:
            await page.evaluate(f"{TKH}.tk.g.revealAt = Date.now() + 4000")
            mk = await page.evaluate("[document.querySelectorAll('#tachles .tkRevHand .tkJC').length, document.querySelectorAll('#tachles .tkRevHand .tkJC mark').length, document.querySelectorAll('#tachles .tkDuel .tkSlot').length, document.querySelectorAll('#tachles .tkBlackC mark').length]")
            full = await page.evaluate(f"(() => {{ {TKH}.tk.set.full = true; {TKH}.render(); const n = document.querySelectorAll('#tachles .tkRevHand .tkJC mark').length; {TKH}.tk.set.full = false; {TKH}.render(); return n; }})()")
            fb = await page.locator('#tachles .tkTop .tkFullB').count(); await click(page, '#tachles .tkTop .tkFullB'); fb2 = [await page.evaluate(f"{TKH}.tk.set.full"), await page.locator('#tachles .tkRevHand .tkJC mark').count(), await page.locator('#tachles .tkFullB.on').count()]
            await click(page, '#tachles .tkTop .tkFullB'); fb3 = [await page.evaluate(f"{TKH}.tk.set.full"), await page.locator('#tachles .tkRevHand .tkJC mark').count()]
            check(tag + ': "📜 משפט מלא" at the top of the reveal turns the whole sentence on and off in the game', fb == 1 and fb2[0] is True and fb2[1] >= 1 and fb2[2] == 1 and fb3 == [False, 0], [fb, fb2, fb3])
            rv = await page.evaluate("(() => { const r = window.__tkReveal; delete window.__tkReveal; const ms = tkRevealMs(); window.__tkReveal = r; return ms; })()")
            await page.screenshot(path=OUT + 'tachles_reveal_%s.png' % tag.lower()); shot = True
            if tag == 'HE':
                rxs = await page.locator('#tachles .tkRxB').count(); n0 = len([x for x in await page.evaluate(f"{TKH}.tk.log") if x.startswith('fx:')]); row0 = await page.locator('#tachles .tkRx').count()
                if rxs: await page.click('#tachles .tkRxB >> nth=0'); await page.wait_for_timeout(100); rxs = rxs if row0 == 0 and await page.locator('#tachles .tkRx button').count() == 6 else 0; await page.click('#tachles .tkRx button >> nth=2'); await page.wait_for_timeout(100)
                fx = [x for x in await page.evaluate(f"{TKH}.tk.log") if x.startswith('fx:')]
                check(tag + ': live reactions: one small 😂 on each of the others\' answers (not your own) opens 😂👏💨🥴🤮🔥; a tap plays the fart and flies 💨 up', rxs >= 1 and len(fx) > n0 and fx[-1] == 'fx:fart' and await page.locator('#tachles .tkFly').count() >= 1, [rxs, fx[-3:]])
            check(tag + ': the reveal: the answers show just the answer (the owner; no sentence), the question card stays clean beside the winner\'s zone', mk[0] >= 1 and mk[1] == 0 and mk[2] == 1 and mk[3] == 0, mk)
            check(tag + ': the "whole sentence" switch (off by default) puts each answer in the sentence again', full >= mk[0], full)
            check(tag + ': the next round waits for the "Next round" button by default (from Evil Apples; was a 4.5 s clock)', rv >= 1e11, rv)
            ea = await page.evaluate("[document.querySelectorAll('#tachles .tkNextB').length, document.querySelectorAll('#tachles .tkRevHand .tkBy').length, document.querySelectorAll('#tachles .tkDuel .tkWinC, #tachles .tkDuel .tkSlot.empty').length, document.querySelectorAll('#tachles .tkRevHand .tkJC').length]")
            check(tag + ': the reveal: the winner sits in the zone by the question, every answer in the hand with who wrote it, a red "Next round ›" button', ea[0] == 1 and ea[1] >= 1 and ea[2] == 1 and ea[3] >= 2, ea)
        if not await step_local(page): await page.wait_for_timeout(80)
    await page.wait_for_timeout(200); v = await view(page)
    check(tag + ': the game played to the end (3 points), round after round on its own; the win screen (trophy, podium, New game)', v['phase'] == 'over' and max(v['players']) == 3 and await page.locator('#tachles .tkMedal').count() == 3 and await page.locator('#tachles [data-a="again"]').count() == 1, v)
    await page.screenshot(path=OUT + 'tachles_over_%s.png' % tag.lower())
    check(tag + ': the evening\'s moments: the winning sentences (the answer marked), a share button on each', await page.locator('#tachles .tkMoment').count() >= 3 and await page.locator('#tachles .tkMoment mark').count() >= 3 and await page.locator('#tachles .tkMoment [data-a^="shr:"]').count() >= 3)
    await page.evaluate("navigator.canShare = () => true; navigator.share = (d) => { const r = new FileReader(); r.onload = () => { window.__shot = r.result; }; r.readAsDataURL(d.files[0]); window.__shared = d.files[0].size; return Promise.resolve(); }; 1")
    await click(page, '#tachles .tkMoment [data-a^="shr:"] >> nth=0'); await page.wait_for_timeout(800)
    sz = await page.evaluate("window.__shared || 0"); check(tag + ': share: a picture of the sentence goes to the share sheet', sz > 20000, sz)
    if tag == 'HE':
        import base64; d64 = await page.evaluate("window.__shot || ''")
        if d64: open(OUT + 'tachles_share.png', 'wb').write(base64.b64decode(d64.split(',')[1]))
    await click(page, '#tachles [data-a="again"]'); check(tag + ': New game: back to the room, the same players', (await view(page))['scr'] == 'lobby' and await page.evaluate(f"{TKH}.tk.lobby.length") == 3)
    await page.evaluate("goHome()"); await page.wait_for_timeout(500)
    check(tag + ': Home: the sheet goes, the corner buttons are back', await page.evaluate("$('tachles').hidden && mode === 'none' && !document.body.classList.contains('tkOn')"))
    check(tag + ': no page errors', not errs, errs); await ctx.close()

async def rules(b):
    # the original's rules in the engine: two players get two decoy answers; the clock sends whoever answered to the czar; a czar's decoy pick gives no point
    ctx, page, errs = await page_for(b, '/tachles', True, init=FAST + "sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu' && {TKH}.tk.deck", 6000)
    r = await page.evaluate(f"""(() => {{ const T = {TKH}.TK, d = {TKH}.tk.deck, out = {{}};
      let g = T.newGame(d, [{{ id: 'a', name: 'A' }}, {{ id: 'b', name: 'B' }}], {{ target: 3, hand: 5 }}); const p = g.players.find((q, i) => i !== g.judge), J = g.players[g.judge];
      out.hand = p.hand.length; T.submit(g, p.id, Array.from({{ length: d.b[g.black][1] }}, (_, i) => i)); out.subs2 = g.order.length; out.phase2 = g.phase;
      const k = g.order.findIndex((id) => id[0] === '~'); T.judge(g, J.id, k); out.decoyPts = g.players.reduce((s, q) => s + q.score, 0); out.decoyName = T.view(g, 'a').last.name;
      g = T.newGame(d, [{{ id: 'a', name: 'A' }}, {{ id: 'b', name: 'B' }}, {{ id: 'c', name: 'C' }}], {{ timer: 30 }}); const q = g.players.find((x, i) => i !== g.judge);
      out.early = T.force(g); T.submit(g, q.id, Array.from({{ length: d.b[g.black][1] }}, (_, i) => i)); out.forced = T.force(g); out.phase3 = g.phase; out.subs3 = g.order.length;
      return out; }})()""")
    sf = await page.evaluate(f"""(() => {{ const T = {TKH}.TK, d = {TKH}.tk.deck, seenW = Array.from({{ length: d.w.length - 20 }}, (_, i) => i), seenB = Array.from({{ length: d.b.length - 3 }}, (_, i) => i);
      const g = T.newGame(d, [{{ id: 'a', name: 'A' }}, {{ id: 'b', name: 'B' }}], {{ target: 3, hand: 7, seenW, seenB }}); const fresh = g.players.flatMap((p) => p.hand).filter((i) => i >= d.w.length - 20).length;
      return {{ fresh, black: g.black >= d.b.length - 3 }}; }})()""")
    tz = await page.evaluate(f"""(() => {{ const T = {TKH}.TK, d = {TKH}.tk.deck, sx = d.wm.findIndex((m) => m.includes('s', 1)), pl = d.wm.findIndex((m) => m[0] !== '3' && !/[sg]/.test(m.slice(1))); let wins = 0, picks = 0;
      for (let r = 0; r < 20; r++) {{ const g = T.newGame(d, [{{ id: 'a', name: 'A' }}, {{ id: 'b', name: 'B', bot: true, taste: 'sg3' }}, {{ id: 'c', name: 'C', bot: true, taste: 'sg3' }}], {{ hand: 7 }});
        g.judge = 1; g.phase = 'judge'; g.subs = {{ a: [pl], c: [sx] }}; g.order = ['a', 'c']; g.black = d.b.findIndex((b) => b[1] === 1); T.botMove(g); if (g.last && g.last.pid === 'c') wins++;
        const h = T.newGame(d, [{{ id: 'a', name: 'A' }}, {{ id: 'b', name: 'B', bot: true, taste: 'sg3' }}], {{ hand: 7 }}); h.judge = 0; h.black = d.b.findIndex((b) => b[1] === 1); h.players[1].hand = [pl, pl, sx, pl, pl, pl, pl].map((x, i) => i === 2 ? sx : x); h.phase = 'pick'; h.subs = {{}};
        T.botMove(h); if (h.subs.b && h.subs.b[0] === sx) picks++; }}
      return {{ wins, picks }}; }})()""")
    check('bots with taste: a "סוטה ומגעיל" bot czar picks the sex answer over a plain one, and answers with it (20 of 20)', tz['wins'] == 20 and tz['picks'] == 20, tz)
    cr = await page.evaluate(f"""(() => {{ const T = {TKH}.TK, d = {TKH}.tk.deck, g = T.newGame(d, ['a', 'b', 'c', 'd'].map((id) => ({{ id, name: id.toUpperCase() }})), {{ hand: 5 }});
      g.judge = 0; g.black = d.b.findIndex((b) => b[1] === 1); g.phase = 'pick'; g.subs = {{}}; g.order = []; for (const id of ['b', 'c', 'd']) T.submit(g, id, [0]);
      const kc = g.order.indexOf('c'), kb = g.order.indexOf('b'); const own = T.react(g, 'c', kc); T.react(g, 'b', kc); T.react(g, 'd', kc); T.react(g, 'a', kb); T.judge(g, 'a', kb);
      return {{ own, b: g.players[1].score, c: g.players[2].score, crowd: g.last.crowd }}; }})()""")
    check('reactions: never on your own answer; the most-reacted answer the czar did not pick gets a crowd point (and the czar\'s pick its point)', cr == {'own': False, 'b': 1, 'c': 1, 'crowd': 'c'}, cr)
    sb = await page.evaluate("(async () => { audioInit(); tkSfxLoad(); await Promise.all(Object.values(tkSfxBuf)); const B = Object.entries(tkSfxBuf); return { n: B.length, ok: B.filter(([, b]) => b instanceof AudioBuffer).length, max: Math.max(...B.map(([, b]) => b ? b.duration : 0)) }; })()")
    check('reaction sounds: 11 real recordings (CC0) load and decode, none longer than 3 s', sb['n'] == 11 and sb['ok'] == 11 and sb['max'] < 3, sb)
    check('rules: cards not seen yet come first (14 dealt of 20 unseen: all 14 unseen; the question too)', sf['fresh'] == 14 and sf['black'], sf)
    check('rules: a hand of the set size; 2 players: the answer + 2 decoys go to the czar; a decoy pick gives no point ("nobody won")', r['hand'] == 5 and r['subs2'] == 3 and r['phase2'] == 'judge' and r['decoyPts'] == 0 and r['decoyName'] is None, r)
    check('rules: the clock: nothing to judge with no answers; with one, it goes to the czar', r['early'] is False and r['forced'] is True and r['phase3'] == 'judge' and r['subs3'] == 1, r)
    check('rules: no page errors', not errs, errs); await ctx.close()

async def pass_round(b):
    ctx, page, errs = await page_for(b, '/tachles', True, init=FAST + "sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu'", 6000)
    await click(page, '#tachles [data-a="m:local"]')
    for i, n in enumerate(['אבי', 'בתיה', 'גיל']): await page.fill('#tachles .tkIn[data-i="%d"]' % i, n)
    await page.screenshot(path=OUT + 'tachles_local_he.png')
    await click(page, '#tachles [data-a="goLocal"]')
    check('HE one phone (3 people, no bots): a pass screen first (the avatar, "מעבירים את הטלפון ל…"), no hand on show', await page.locator('#tachles [data-a^="iam:"]').count() == 1 and await page.locator('#tachles .tkHC').count() == 0)
    await page.screenshot(path=OUT + 'tachles_pass_he.png')
    seen = 0
    for k in range(40):
        v = await view(page)
        if v['phase'] == 'reveal': break
        if await page.locator('#tachles [data-a^="iam:"]').count(): seen += 1
        await step_local(page)
    v = await view(page)
    check('HE one phone: each player gets the phone in turn (the pickers, then the czar), a point is given', v['phase'] == 'reveal' and seen >= 3 and sum(v['players']) == 1, [seen, v])
    await page.wait_for_timeout(700); check('HE one phone: the next round starts on its own after the banner', (await view(page))['round'] == 2)
    check('pass: no page errors', not errs, errs); await ctx.close()

async def online(b):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); errs = []
    pages = []
    for i in range(4):
        pg = await ctx.new_page(); await routes(pg); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(FAST + "window.__tkReveal = 1500; window.__tkBus = 'bc'; sessionStorage.setItem('grasp.tk18', '1'); localStorage.setItem('lang','he');")
        await pg.goto(BASE + '/tachles'); await wait(pg, f"{TKH}.tk.scr === 'menu'", 8000); pages.append(pg)
    host, g1, g2, g3 = pages
    await click(host, '#tachles [data-a="m:create"]'); await host.fill('#tkMe', 'המארח'); await click(host, '#tachles [data-a="go:create"]'); await host.wait_for_timeout(300)
    code = await host.evaluate(f"{TKH}.tk.code"); check('online: the host opens a room: the big neon code, Copy link, Share', len(code) == 4 and (await view(host))['scr'] == 'lobby' and await host.locator('#tachles .tkCodeBig').count() == 1 and await host.locator('#tachles [data-a="copy"]').count() == 1, code)
    for pg, n in ((g1, 'אורח1'), (g2, 'אורח2'), (g3, 'טרול')):
        await click(pg, '#tachles [data-a="m:join"]'); await pg.fill('#tkMe', n); await pg.fill('#tkCode', code.lower()); await click(pg, '#tachles [data-a="go:join"]'); await pg.wait_for_timeout(300)
    n = await host.evaluate(f"{TKH}.tk.lobby.length"); check('online: three phones join with the code: four in the room; a guest sees the list, "(אתה)" and the host\'s badge', n == 4 and await g1.evaluate(f"({TKH}.tk.lobbyView || []).length") == 4 and await g1.locator('#tachles .tkPl.me').count() == 1 and await g1.locator('#tachles .tkHostB').count() == 1, n)
    await host.screenshot(path=OUT + 'tachles_lobby_online_he.png'); await g1.screenshot(path=OUT + 'tachles_lobby_guest_he.png')
    await click(host, '#tachles [data-a^="kick:"] >> nth=2'); await click(host, '#tachles [data-a="kickOk"]'); await host.wait_for_timeout(300)
    check('online: the host kicks a guest: three left, the kicked phone is back at the menu with a toast', await host.evaluate(f"{TKH}.tk.lobby.length") == 3 and (await view(g3))['scr'] == 'menu' and await g3.locator('#tachles .tkToast').count() == 1)
    await g3.screenshot(path=OUT + 'tachles_kicked_he.png')
    await click(g3, '#tachles [data-a="m:screen"]'); await g3.fill('#tkCode', code); await click(g3, '#tachles [data-a="go:screen"]'); await g3.wait_for_timeout(500)
    check('TV: the kicked phone joins as a shared screen: the big code, the players, no player added', await g3.locator('#tachles .tkTV .tkTvCode').count() == 1 and await g3.locator('#tachles .tkTvPl .tkChip').count() == 3 and await host.evaluate(f"{TKH}.tk.lobby.length") == 3 and 'מסך משותף מחובר' in await host.inner_text('#tachles .tkTvHint'))
    await g3.set_viewport_size({'width': 1280, 'height': 720}); await g3.screenshot(path=OUT + 'tachles_tv_lobby.png')
    await click(host, '#tachles [data-a="dbg"]'); dl = await host.inner_text('#tachles .tkDbgP')
    check('debug log: 🐞 in the room opens the connection log (the room made, guests\' hello, the TV)', '— create room' in dl and 'hello' in dl and 'screen' in dl and await host.locator('#tachles [data-a="dbgCopy"]').count() == 1, dl[:300])
    await click(host, '#tachles [data-a="dbgNet"]'); await host.wait_for_timeout(600)
    check('debug log: "🔬 בדיקת רשת" runs a network check into the log', any('network check' in x for x in await host.evaluate("tkDbgL")))
    await click(host, '#tachles .tkMHead [data-a="mclose"]')
    await click(host, '#tachles [data-a="set"]'); await click(host, '#tachles [data-a="fullT"]'); await host.wait_for_timeout(250)
    check('full sentence: the host turns it on for the whole room ("לכל החדר"), the guests get it', await host.evaluate(f"{TKH}.tk.set.full === true") and 'לכל החדר' in await host.inner_text('#tachles .tkModal') and await g1.evaluate("tkFullOn()") and await g2.evaluate("tkFullOn()"))
    await click(host, '#tachles .tkMHead [data-a="mclose"]')
    await click(g2, '#tachles [data-a="set"]'); m2 = await g2.inner_text('#tachles .tkModal'); await click(g2, '#tachles [data-a="fullT"]'); await g2.wait_for_timeout(200)
    check('full sentence: a guest turns it off on their own phone only ("רק בטלפון שלך"); the room and the others keep it', 'רק בטלפון שלך' in m2 and not await g2.evaluate("tkFullOn()") and await g1.evaluate("tkFullOn()") and await host.evaluate(f"{TKH}.tk.set.full === true"))
    await click(g2, '#tachles .tkMHead [data-a="mclose"]')
    await click(host, '#tachles [data-a="start"]'); await host.wait_for_timeout(400); pages = [host, g1, g2]
    check('TV: the game on the screen: the question card, the scores, the answer chips, no hand', await g3.locator('#tachles .tkTV .tkBlackC').count() == 1 and await g3.locator('#tachles .tkTV .tkScores').count() == 1 and await g3.locator('#tachles .tkHC').count() == 0)
    vs = [await view(p) for p in pages]; check('online: the host starts: every phone in the game, round 1', all(v['scr'] == 'game' and v['round'] == 1 for v in vs), vs)
    st = await g1.evaluate("(() => { const s = document.querySelector('#tachles .tkScores'), r = s.getBoundingClientRect(); return [s.scrollWidth <= s.clientWidth + 1, [...s.querySelectorAll('.tkSc')].every((c) => { const q = c.getBoundingClientRect(); return q.left >= r.left - 1 && q.right <= r.right + 1; })]; })()")
    st8 = await g1.evaluate("(() => { const d = document.createElement('div'), w = document.querySelector('#tachles .tkWrap2') || document.querySelector('#tachles .tkIn0'); d.innerHTML = tkScoresHtml({ phase: 'pick', judge: 'p0', players: ['בני', 'איתמר', 'אריאל', 'רעות', 'אורי', 'פיתה 42', 'שמשון הגיבור', 'דנה'].map((n, i) => ({ id: 'p' + i, name: n, score: i, on: true })) }, 'p0'); w.appendChild(d); const s = d.firstChild, r = s.getBoundingClientRect(), ok = [s.scrollWidth <= s.clientWidth + 1, [...s.querySelectorAll('.tkSc')].every((c) => { const q = c.getBoundingClientRect(); return q.left >= r.left - 1 && q.right <= r.right + 1 && q.width >= 36; })]; d.remove(); return ok; })()")
    check('the players\' strip: everyone fits, no scrolling (3 players, and 8: the avatar over the name)', all(st) and all(st8), [st, st8])
    hands = [await p.evaluate(f"{TKH}.tk.view.hand.join('|')") for p in pages]; check('online: each phone sees only its own hand (three different hands)', len(set(hands)) == 3, [h[:30] for h in hands])
    J = await host.evaluate(f"{TKH}.tk.view.judge"); pick = [p for p in pages if await p.evaluate(f"{TKH}.tk.view.me") != J]
    H = "(() => { const s = document.querySelector('#tachles .tkStatus'); return s ? Math.round(s.getBoundingClientRect().height) : -1; })()"; h0 = await pick[1].evaluate(H)
    await step_local(pick[0]); await host.wait_for_timeout(200); h1 = await pick[1].evaluate(H)
    check('online: one answered, one left: the status chips (a tick, a pulsing avatar) and a tease line for the last one', await pick[1].locator('#tachles .tkTick').count() == 1 and len((await pick[1].inner_text('#tachles .tkTease')).strip()) > 3)
    check('the tease line does not push the screen: its place is kept from the start of the round (the owner: a scroll appeared)', h0 > 0 and h0 == h1, [h0, h1])
    await pick[1].screenshot(path=OUT + 'tachles_guest_he.png')
    for k in range(30):
        if (await view(host))['phase'] == 'reveal': break
        for p in pages:
            if (await view(host))['phase'] == 'reveal' or (await view(host))['round'] > 1: break
            await step_local(p)
        await host.wait_for_timeout(150)
    v = await view(host); check('online: everyone answers, the czar picks: a point, every phone sees the trophy on the winning answer', v['phase'] == 'reveal' and sum(v['players']) == 1 and (await view(g2))['phase'] == 'reveal' and await g2.locator('#tachles .tkDuel .tkWinC .tkTrophy').count() == 1, [v, await view(g2)])
    await g2.screenshot(path=OUT + 'tachles_online_reveal_he.png')
    check('TV: the reveal on the screen: the winning sentence in the question card and every answer under it', await g3.locator('#tachles .tkTV .tkBlackC mark').count() >= 1 and await g3.locator('#tachles .tkTV .tkSub .tkAnsC').count() >= 2)
    await g3.screenshot(path=OUT + 'tachles_tv_reveal.png')
    await host.wait_for_timeout(1900); check('online: the next round on its own, on every phone', all([(await view(p))['round'] == 2 for p in pages]))
    await click(host, '#tachles [data-a="leave"]'); check('online: Close room asks first', await host.locator('#tachles .tkModal [data-a="leaveOk"]').count() == 1)
    await host.screenshot(path=OUT + 'tachles_leave_he.png')
    await click(host, '#tachles [data-a="leaveOk"]'); await host.wait_for_timeout(300)
    check('online: the room closes: the guests are back at the menu with a toast', (await view(g1))['scr'] == 'menu' and await g1.locator('#tachles .tkToast').count() == 1)
    check('online: no page errors', not errs, errs); await ctx.close()

async def deck(b):
    ctx, page, errs = await page_for(b, '/tachles', True, init="sessionStorage.setItem('grasp.tk18', '1');"); await page.wait_for_timeout(1200)
    d = await page.evaluate(f"{TKH}.tk.deck")
    bad = [c for c in d['w'] + [x[0] for x in d['b']] if any(k in c for k in ('פדופיל', 'הסבא שמשפץ', 'תינוק עם זין', 'הזין של הרב עובדיה', 'יואב גלנט שמכניס'))]
    check('the deck: 340+ black and 1350+ white cards, each with its level and packs, without the two dropped groups', len(d['b']) >= 340 and len(d['w']) >= 1350 and len(d['wm']) == len(d['w']) and len(d['bm']) == len(d['b']) and not bad, [len(d['b']), len(d['w']), bad])
    await ctx.close()

async def style_packs(b):
    # the evening's style (3 levels) and the topic packs: only the cards they let in are dealt
    ctx, page, errs = await page_for(b, '/tachles', True, init=FAST + "sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu' && {TKH}.tk.deck", 6000)
    await click(page, '#tachles [data-a="m:bots"]')
    check('style: the room shows "סגנון הערב" with 3 levels, 🟠 גס on by default, and a packs button', await page.locator('#tachles .tkLv').count() == 3 and await page.locator('#tachles .tkLv.on').inner_text() == '🟠\nגס' and await page.locator('#tachles [data-a="packs"]').count() == 1)
    await click(page, '#tachles [data-a="lvl:1"]'); check('style: 🟢 קליל picked, its warning line shown', await page.evaluate(f"{TKH}.tk.set.lvl") == 1 and 'ההורים' in await page.inner_text('#tachles .tkLvD'))
    await click(page, '#tachles [data-a="packs"]'); check('packs: a sheet of 13 packs, each with ⚠️ a warning and a card count, all on', await page.locator('#tachles .tkPacks .tkPk').count() == 13 and await page.locator('#tachles .tkPacks .tkPk.on').count() == 13 and await page.locator('#tachles .tkPk small:has-text("⚠️")').count() == 13)
    await page.screenshot(path=OUT + 'tachles_packs.png')
    await click(page, '#tachles [data-a="pkAll"]'); await click(page, '#tachles .tkMHead [data-a="mclose"]')
    n0 = await page.inner_text('#tachles [data-a="packs"]')
    check('packs: all off at 🟢: the button says 0 of 13 and fewer cards (the ones with no sensitive topic stay)', 'חבילות: 0 מתוך 13' in n0, n0)
    await page.evaluate(f"{TKH}.tk.deck.wm = {TKH}.tk.deck.wm.map((m) => m + 'i'); {TKH}.render()")
    check('packs: too few cards: Start is off and says why', await page.locator('#tachles [data-a="start"][disabled]').count() == 1 and 'מעט מדי' in await page.inner_text('#tachles [data-a="start"]'))
    await page.evaluate(f"{TKH}.tk.deck.wm = {TKH}.tk.deck.wm.map((m) => m.slice(0, -1))")
    await click(page, '#tachles [data-a="packs"]'); await click(page, '#tachles [data-a="pkAll"]'); await click(page, '#tachles [data-a="pk:s"]'); await click(page, '#tachles [data-a="pk:f"]'); await click(page, '#tachles .tkMHead [data-a="mclose"]')
    check('packs: sex and family off, saved', await page.evaluate(f"{TKH}.tk.set.off.slice().sort().join('')") == 'fs' and await page.evaluate("JSON.parse(localStorage.getItem('grasp.tk')).set.lvl") == 1)
    await page.screenshot(path=OUT + 'tachles_style.png')
    await click(page, '#tachles [data-a="own"]'); await page.fill('#tkOwnIn', 'המנגל של אבי ביום העצמאות'); await click(page, '#tachles [data-a="ownAdd"]')
    check('in-jokes: "🤫 הבדיחות שלנו": added, the button counts it', await page.evaluate(f"{TKH}.tk.own.h") == ['המנגל של אבי ביום העצמאות.'])
    await click(page, '#tachles .tkMHead [data-a="mclose"]'); check('in-jokes: the room shows "(1)"', 'הבדיחות שלנו (1)' in await page.inner_text('#tachles [data-a="own"]'))
    await click(page, '#tachles [data-a="start"]'); await page.wait_for_timeout(300)
    gc = await page.evaluate(f"""(() => {{ const g = {TKH}.tk.g, d = g.deck, names = g.players.map((p) => p.name), j = d.w.indexOf('המנגל של אבי ביום העצמאות.');
      const nb = d.b.map((b, i) => i).filter((i) => i >= {TKH}.tk.deck.b.length), early = g.bd.slice(-60).filter((i) => i >= {TKH}.tk.deck.b.length).length;
      const inHand = g.players.some((p) => p.hand.includes(j)), soon = inHand || g.wd.slice(-45).includes(j) || !g.wd.includes(j); /* (or already played: fast bots) */
      return {{ named: nb.length > 0 && nb.every((i) => names.some((n) => d.b[i][0].includes(n))), early, soon }}; }})()""")
    check('the group\'s cards: questions with the players\' names (those the style lets in), several among the first draws; the in-joke dealt early', gc['named'] and gc['early'] >= 2 and gc['soon'], gc)
    r = await page.evaluate(f"""(() => {{ const g = {TKH}.tk.g, d = g.deck, ws = g.players.flatMap((p) => p.hand).concat(g.wd), bs = g.bd.concat([g.black]);
      const bad = (m) => +m[0] > 1 || m.includes('s', 1) || m.includes('f', 1); return {{ n: ws.length, badW: ws.filter((i) => bad(d.wm[i])).length, badB: bs.filter((i) => bad(d.bm[i])).length }}; }})()""")
    check('style: the game at 🟢 without sex and family: every card in the hands, the pile and the questions passes', r['n'] > 50 and r['badW'] == 0 and r['badB'] == 0, r)
    check('style: no page errors', not errs, errs); await ctx.close()

async def reconnect(b):
    # the owner's log: the room's link to the broker dropped and re-dropped every few hundred ms. A fake PeerJS whose reconnects keep failing (an
    # error + a disconnect at once, like the log): one try at a time with growing waits, then a brand-new peer that opens and clears the note
    fake = """window.__rc = []; window.__peers = 0; window.__fail = true;
      window.Peer = class { constructor(id) { this.id = id; this.h = {}; this.open = false; this.disconnected = true; this.destroyed = false; this.n = ++window.__peers; this.connections = {};
          setTimeout(() => { if (this.n > 1 || !window.__dropAt) { this.open = true; this.disconnected = false; this.emit('open', id); } }, 50);
          if (this.n === 1) setTimeout(() => { this.open = true; this.disconnected = false; this.emit('open', id); setTimeout(() => this.drop(), 300); }, 50); }
        on(k, f) { (this.h[k] = this.h[k] || []).push(f); } emit(k, a) { (this.h[k] || []).forEach((f) => f(a)); }
        drop() { this.open = false; this.disconnected = true; this.emit('error', { type: 'network', message: 'Lost connection to server.' }); this.emit('disconnected'); }
        reconnect() { window.__rc.push(Date.now()); setTimeout(() => this.drop(), 200); }
        destroy() { this.destroyed = true; this.open = false; this.disconnected = true; this.emit('disconnected'); this.emit('close'); } };"""
    ctx, page, errs = await page_for(b, '/tachles', True, init="window.__tkNet = 'peer'; window.__graspNoAutoFs = true; sessionStorage.setItem('grasp.tk18', '1');" + fake); await wait(page, f"{TKH}.tk.scr === 'menu'", 6000)
    await click(page, '#tachles [data-a="m:create"]'); await page.fill('#tkMe', 'המארח'); await click(page, '#tachles [data-a="go:create"]')
    await page.wait_for_timeout(1500); msg = await page.evaluate(f"{TKH}.tk.netMsg")
    check('reconnect: a drop shows "מתחבר מחדש" on the room', 'מתחבר מחדש' in msg, msg)
    await page.wait_for_timeout(15000)
    r = await page.evaluate(f"(() => {{ const t = window.__rc, gaps = t.slice(1).map((x, i) => x - t[i]); return {{ n: t.length, minGap: gaps.length ? Math.min(...gaps) : 9999, peers: window.__peers, msg: {TKH}.tk.netMsg }}; }})()")
    check('reconnect: one try at a time, never a storm (the gaps grow, ≥ 0.9 s), then a fresh peer opens and the note goes', r['n'] >= 2 and r['n'] <= 6 and r['minGap'] >= 900 and r['peers'] >= 2 and r['msg'] == '', r)
    check('reconnect: no page errors', not errs, errs); await ctx.close()

async def mqtt_room(b):
    # the rooms over MQTT (the default since the owner's network blocks PeerJS), through a local broker (tests/mq_broker.py): a room, a phone joins
    # with the code and sees the room, the game starts on both
    import subprocess, sys as _s
    br = subprocess.Popen([_s.executable if 'websockets' in _s.modules else 'python3.13', 'tests/mq_broker.py', '8897'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); await asyncio.sleep(1.2)
    try:
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); errs = []; pages = []
        INIT = FAST + "window.__tkMQ = ['ws://localhost:8897/mqtt']; sessionStorage.setItem('grasp.tk18', '1'); localStorage.setItem('lang','he'); Object.defineProperty(navigator, 'wakeLock', { value: { request: () => { window.__wl = (window.__wl || 0) + 1; return Promise.resolve({ release: () => Promise.resolve(), addEventListener() {} }); } } });"
        for i in range(2):
            pg = await ctx.new_page(); await routes(pg); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script(INIT)
            await pg.goto(BASE + '/tachles'); await wait(pg, f"{TKH}.tk.scr === 'menu'", 8000); pages.append(pg)
        host, g = pages
        await click(host, '#tachles [data-a="m:create"]'); await host.fill('#tkMe', 'המארח'); await click(host, '#tachles [data-a="go:create"]'); await host.wait_for_timeout(1500)
        code = await host.evaluate(f"{TKH}.tk.code")
        await click(g, '#tachles [data-a="m:join"]'); await g.fill('#tkMe', 'אורח'); await g.fill('#tkCode', code); await click(g, '#tachles [data-a="go:join"]')
        ok = await wait(g, f"{TKH}.tk.scr === 'lobby'", 10000)
        check('MQTT: a phone joins the room with its code (through the broker): both see two players', ok and await host.evaluate(f"{TKH}.tk.lobby.length") == 2 and len(await g.evaluate(f"{TKH}.tk.lobbyView")) == 2, await host.evaluate("tkDbgL.slice(-6)"))
        await click(host, '#tachles [data-a="start"]'); ok2 = await wait(g, f"{TKH}.tk.scr === 'game' && {TKH}.tk.view && {TKH}.tk.view.round === 1", 8000)
        check('MQTT: the game starts on the phone too', ok2)
        check('screen on: the room and the game hold a wake lock (the screen does not go off)', await host.evaluate(f"!!{TKH}.tk.wake && window.__wl >= 1") and await g.evaluate(f"!!{TKH}.tk.wake"))
        # the owner: "the screen went off, the browser closed: the player can't get back in". A phone closes and opens again: "back to the game", same seat and cards
        hand, me = await g.evaluate(f"{TKH}.tk.view.hand.join('|')"), await g.evaluate(f"{TKH}.tk.view.me"); await g.close(); await host.wait_for_timeout(300)
        g = await ctx.new_page(); await routes(g); g.on('pageerror', lambda e: errs.append(str(e))); await g.add_init_script(INIT)
        await g.goto(BASE + '/tachles'); await wait(g, f"{TKH}.tk.scr === 'menu'", 8000)
        check('back in: the menu shows "↩️ חזרה למשחק" with the room code', await g.locator('#tachles [data-a="back:g"]').count() == 1 and code in await g.inner_text('#tachles [data-a="back:g"]'))
        await g.screenshot(path=OUT + 'tachles_back_in.png')
        await click(g, '#tachles [data-a="back:g"]'); ok3 = await wait(g, f"{TKH}.tk.scr === 'game' && {TKH}.tk.view && {TKH}.tk.view.me === '{me}'", 10000)
        check('back in: the same seat, the same cards, still two players', ok3 and await g.evaluate(f"{TKH}.tk.view.hand.join('|')") == hand and await host.evaluate(f"{TKH}.tk.g.players.length") == 2)
        # the host's browser closes: reopened, "back to your room" opens the same code with the game as it was, and the phone comes back on its own
        rnd, hh = await host.evaluate(f"{TKH}.tk.g.round"), await host.evaluate(f"{TKH}.tk.view.hand.join('|')"); await host.close(); await g.wait_for_timeout(300)
        host = await ctx.new_page(); await routes(host); host.on('pageerror', lambda e: errs.append(str(e))); await host.add_init_script(INIT)
        await host.goto(BASE + '/tachles'); await wait(host, f"{TKH}.tk.scr === 'menu'", 8000)
        check('room back: the menu shows "↩️ חזרה לחדר שלך"', await host.locator('#tachles [data-a="back:h"]').count() == 1)
        await click(host, '#tachles [data-a="back:h"]'); ok4 = await wait(host, f"{TKH}.tk.conns.size === 1 && {TKH}.tk.g.players.every((p) => p.on)", 12000)
        check('room back: the same code and round, the host\'s cards, the phone back in the room (asked "who is there?")', ok4 and await host.evaluate(f"{TKH}.tk.code") == code and await host.evaluate(f"{TKH}.tk.g.round") == rnd and await host.evaluate(f"{TKH}.tk.view.hand.join('|')") == hh and (await view(g))['scr'] == 'game', await host.evaluate("tkDbgL.slice(-8)"))
        await click(host, '#tachles [data-a="leave"]'); await click(host, '#tachles [data-a="leaveOk"]'); await wait(g, f"{TKH}.tk.scr === 'menu'", 8000)
        check('room closed: the guest is back at the menu, no "back" buttons left', (await view(g))['scr'] == 'menu' and await g.locator('#tachles .tkBackIn').count() == 0 and await host.evaluate("!localStorage.getItem('grasp.tkRoom') && !localStorage.getItem('grasp.tkLast')"))
        check('MQTT: no page errors', not errs, errs); await ctx.close()
    finally: br.terminate()

async def link_in(b):
    # the owner: the shared link (/tachles?room=CODE) opened the menu: the code was lost on the way in. Now: the 18+ gate, then the join form with the code
    ctx, page, errs = await page_for(b, '/tachles?room=ABCD', True, init=FAST); await wait(page, f"{TKH}.tk.scr === 'gate'", 8000)
    check('the link: the 18+ gate first, the room code kept', await page.evaluate(f"{TKH}.tk.code") == 'ABCD', await page.evaluate("location.href"))
    await click(page, '#tachles [data-a="gate"]')
    check('the link: after the gate, the join form with the code filled in and the name ready', (await view(page))['scr'] == 'form' and await page.evaluate(f"{TKH}.tk.form") == 'join' and await page.input_value('#tkCode') == 'ABCD' and await page.locator('#tkMe').count() == 1)
    await page.screenshot(path=OUT + 'tachles_link_join.png')
    ctx2, p2, e2 = await page_for(b, '/tachles?room=WXYZ', True, init=FAST + "sessionStorage.setItem('grasp.tk18', '1');"); await wait(p2, f"{TKH}.tk.scr === 'form'", 8000)
    check('the link, 18+ already confirmed: straight to the join form with the code', await p2.evaluate(f"{TKH}.tk.form") == 'join' and await p2.input_value('#tkCode') == 'WXYZ')
    check('the link: no page errors', not errs and not e2, errs + e2); await ctx.close(); await ctx2.close()

async def taps(b):
    # the owner: "a tap on a card sometimes takes, sometimes not": real touches (CDP) on the middle card of the hand: clean, quick, long, the finger
    # sliding a little, near the card's edges, while the screen re-renders (a message in), right after a swipe; each tap must pick / unpick it.
    # And 5 players (4 bots): the players' strip fits without scrolling
    ctx, page, errs = await page_for(b, '/tachles', True, init=FAST + "sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu' && {TKH}.tk.deck", 8000)
    await click(page, '#tachles [data-a="m:bots"]')
    for _ in range(2): await click(page, '#tachles [data-a="addBot"]')
    for _ in range(20):
        await click(page, '#tachles [data-a="start"]'); await page.wait_for_timeout(250)
        if await page.evaluate(f"{TKH}.tk.view.me !== {TKH}.tk.view.judge && {TKH}.tk.view.phase === 'pick'"): break
        await page.evaluate(f"{TKH}.tk.scr = 'lobby'; {TKH}.tk.g = null; {TKH}.render()")
    await page.evaluate(f"clearTimeout({TKH}.tk.botT); {TKH}.tk.g.timer = 0; {TKH}.tk.g.players.forEach((p) => {{ if (p.bot) p.on = false; }}); {TKH}.render()") # (the bots hold off: the hand stays)
    st = await page.evaluate("(() => { const s = document.querySelector('#tachles .tkScores'), r = s.getBoundingClientRect(); return [s.querySelectorAll('.tkSc').length, s.classList.contains('many'), s.scrollWidth <= s.clientWidth + 1, [...s.querySelectorAll('.tkSc')].every((c) => { const q = c.getBoundingClientRect(); return q.left >= r.left - 1 && q.right <= r.right + 1; })]; })()")
    await page.evaluate(f"{TKH}.tk.g.players.forEach((p) => {{ p.on = true; }}); {TKH}.render()"); await page.screenshot(path=OUT + 'tachles_strip5.png'); await page.evaluate(f"{TKH}.tk.g.players.forEach((p) => {{ if (p.bot) p.on = false; }}); {TKH}.render()")
    check('5 players: the strip shows them all (the avatar over the name), no scrolling', st[0] == 5 and all(st[1:]), st)
    cdp = await ctx.new_cdp_session(page)
    async def touch(typ, pts): await cdp.send('Input.dispatchTouchEvent', {'type': typ, 'touchPoints': [{'x': x, 'y': y, 'id': 1, 'radiusX': 8, 'radiusY': 8, 'force': 1} for x, y in pts]})
    MID = "(() => { const W = document.querySelector('#tachles .tkHandW').getBoundingClientRect(), mid = W.left + W.width / 2; let best = null, bd = 1e9; document.querySelectorAll('#tachles .tkHC').forEach((c, i) => { const r = c.getBoundingClientRect(), d = Math.abs(r.left + r.width / 2 - mid); if (d < bd) { bd = d; best = [i, r.left + r.width / 2, r.top + r.height / 2, r.width]; } }); return best; })()"
    async def tap1(jx=0, jy=0, hold=70, pos=0.5, storm=False, swipe=0):
        m = await page.evaluate(MID)
        if swipe:
            await touch('touchStart', [(200, m[2])])
            for k in range(1, 7): await touch('touchMove', [(200 + swipe * k / 6, m[2])]); await page.wait_for_timeout(12)
            await touch('touchEnd', []); await page.wait_for_timeout(1200); m = await page.evaluate(MID)
        if storm: await page.evaluate(f"window.__st = setInterval(() => {TKH}.render(), 60)")
        s0 = await page.evaluate(f"{TKH}.tk.sel.slice()"); x = m[1] + (pos - 0.5) * m[3] * 0.8
        await touch('touchStart', [(x, m[2])]); await page.wait_for_timeout(hold // 2)
        if jx or jy: await touch('touchMove', [(x + jx, m[2] + jy)])
        await page.wait_for_timeout(hold // 2); await touch('touchEnd', []); await page.wait_for_timeout(220)
        if storm: await page.evaluate("clearInterval(window.__st)")
        s1 = await page.evaluate(f"{TKH}.tk.sel.slice()"); return (m[0] in s1) != (m[0] in s0)
    await page.evaluate(f"(() => {{ const t = {TKH}.tk, g = t.g; g.black = g.deck.b.findIndex((c) => c[1] === 1); t.view = {TKH}.TK.view(g, t.me); t.sel = []; {TKH}.render(); }})()")
    res = {}
    for name, kw in (('clean', {}), ('quick', {'hold': 20}), ('long', {'hold': 400}), ('slide 10px', {'jx': 10}), ('slide up 10px', {'jy': -10}), ('edge', {'pos': 0.9}), ('other edge', {'pos': 0.1}), ('re-render', {'storm': True}), ('after a swipe', {'swipe': 120})):
        res[name] = sum([await tap1(**kw) for _ in range(6)])
    await page.evaluate(f"(() => {{ const t = {TKH}.tk, g = t.g; g.black = g.deck.b.findIndex((c) => c[1] === 2); t.view = {TKH}.TK.view(g, t.me); t.sel = [0, 1]; {TKH}.render(); document.querySelectorAll('#tachles .tkHC')[3].scrollIntoView({{ inline: 'center', block: 'nearest' }}); }})()"); await page.wait_for_timeout(300)
    m = await page.evaluate(MID); await touch('touchStart', [(m[1], m[2])]); await page.wait_for_timeout(40); await touch('touchEnd', []); await page.wait_for_timeout(250)
    check('taps: both picked (pick 2) and a third tapped: it takes the second one\'s place (it did nothing)', await page.evaluate(f"{TKH}.tk.sel.join()") == '0,%d' % m[0], [m[0], await page.evaluate(f"{TKH}.tk.sel")])
    check('taps on the middle card: every one takes (clean, quick, long, a sliding finger, the edges, mid re-render, after a swipe)', all(v == 6 for v in res.values()), res)
    check('taps: no page errors', not errs, errs); await ctx.close()

async def small_screen(b):
    # the UX pass on a short phone (360x640): Start stays on screen in the room, the game opens at the top (the host had scrolled down to Start:
    # the question was out of sight), and while picking the question card is not under the hand held at the bottom
    ctx = await b.new_context(viewport={'width': 360, 'height': 640}, is_mobile=True, has_touch=True); errs = []
    page = await ctx.new_page(); await routes(page); page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(FAST + "sessionStorage.setItem('grasp.tk18', '1'); localStorage.setItem('lang','he');"); await page.goto(BASE + '/tachles'); await wait(page, f"{TKH}.tk.scr === 'menu' && {TKH}.tk.deck", 8000)
    await click(page, '#tachles [data-a="m:bots"]')
    vis = "(() => { const r = document.querySelector('#tachles [data-a=\"start\"]').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; })()"
    check('short phone: the room\'s Start button is on screen without scrolling (held at the bottom)', await page.evaluate(vis))
    await page.evaluate("$('tachles').scrollTop = 1e5"); check('short phone: still on screen scrolled to the end', await page.evaluate(vis))
    await page.evaluate(f"{TKH}.TK.botMove = () => false")
    for _ in range(20):
        await page.evaluate("$('tachles').scrollTop = 1e5"); await click(page, '#tachles [data-a="start"]'); await page.wait_for_timeout(200)
        if await page.evaluate(f"{TKH}.tk.view.me !== {TKH}.tk.view.judge"): break
        await page.evaluate(f"{TKH}.tk.scr = 'lobby'; {TKH}.tk.g = null; {TKH}.render()")
    await page.evaluate(f"(() => {{ const t = {TKH}.tk, g = t.g, B = g.deck.b; let k = 0; B.forEach((c, i) => {{ if (c[1] === 1 && c[0].length > B[k][0].length) k = i; }}); g.black = k; t.view = {TKH}.TK.view(g, t.me); {TKH}.render(); }})()") # (the longest question in the deck)
    st = await page.evaluate("(() => { const q = document.querySelector('#tachles .tkBlackC').getBoundingClientRect(), h = document.querySelector('#tachles .tkHandBox').getBoundingClientRect(); return [$('tachles').scrollTop, Math.round(q.top), Math.round(q.bottom), Math.round(h.top)]; })()")
    await page.screenshot(path=OUT + 'tachles_small_pick.png')
    check('short phone: the game opens at the top, the question card whole and above the hand (the longest question)', st[0] == 0 and st[1] >= 0 and st[2] <= st[3] + 2, st)
    check('short phone: no page errors', not errs, errs); await ctx.close()

async def settings_way(b):
    # the owner's Android: the long press did nothing; Settings: 7 quick taps on the version show a "🔞 Tachles" row (it stays), a tap opens it
    ctx, page, errs = await page_for(b, '/', True, init="window.__graspNoAutoFs = true;"); await page.wait_for_timeout(700)
    await page.tap('#settingsBtn'); await page.wait_for_timeout(400)
    check('Settings: the version at the bottom, no Tachles row yet', await page.evaluate("$('moreVer').textContent.includes(APP_VERSION) && $('tkOpen').hidden"))
    for i in range(7): await page.tap('#moreVer'); await page.wait_for_timeout(90)
    check('7 quick taps on the version: the "🔞 תכל׳ס" row shows', await page.evaluate("!$('tkOpen').hidden && localStorage.getItem('grasp.tkShow') === '1'"))
    await page.screenshot(path=OUT + 'tachles_settings_he.png')
    await page.tap('#tkOpen'); ok = await wait(page, "gameMode === 'tachles' && !$('tachles').hidden", 5000)
    check('the row opens Tachles (behind the 18+ gate)', ok and await page.evaluate(f"{TKH}.tk.scr") == 'gate')
    await page.evaluate("goHome()"); await page.wait_for_timeout(400); await page.reload(); await page.wait_for_timeout(900)
    check('the row stays after a reload', await page.evaluate("!$('tkOpen').hidden"))
    check('settings: no page errors', not errs, errs); await ctx.close()

async def write_card(b):
    # write your own card (the owner: a wildcard idea; to his email for approval): a black one with two blanks is sent (FormSubmit, mocked here)
    ctx, page, errs = await page_for(b, '/tachles', True, init="window.__graspNoAutoFs = true; sessionStorage.setItem('grasp.tk18', '1');"); await wait(page, f"{TKH}.tk.scr === 'menu'", 6000)
    sent = []
    async def fs(route):
        sent.append(route.request.post_data); await route.fulfill(status=200, content_type='application/json', body='{"success":"true"}')
    await page.route('https://formsubmit.co/**', fs)
    await click(page, '#tachles [data-a="m:write"]'); check('the menu: "write your own card" opens the writer (answer / question)', (await view(page))['scr'] == 'write' and await page.locator('#tkWrT').count() == 1)
    await click(page, '#tachles [data-a="wr:b"]'); await page.fill('#tkWrT', 'מה עשה ___ עם ___?'); await page.wait_for_timeout(100)
    check('a question with two blanks says "pick 2"', '2' in await page.inner_text('#tkWrN'))
    await page.screenshot(path=OUT + 'tachles_write_he.png')
    await click(page, '#tachles [data-a="wr:send"]'); await page.wait_for_timeout(500)
    import json as _j
    d = _j.loads(sent[0]) if sent else {}
    check('sent for approval: the card and its deck line, a thank-you, listed as waiting', d.get('text') == 'מה עשה ___ עם ___?' and _j.loads(d.get('json', 'null')) == ['מה עשה ___ עם ___?', 2] and await page.locator('#tachles .tkOk').count() == 1 and len(await page.evaluate("JSON.parse(localStorage.getItem('grasp.tkMine'))")) == 1, d)
    await page.screenshot(path=OUT + 'tachles_write_sent_he.png')
    await click(page, '#tachles [data-a="wr:w"]'); await page.fill('#tkWrT', 'x'); await click(page, '#tachles [data-a="wr:send"]')
    check('too short: not sent', len(sent) == 1 and await page.locator('#tachles .tkErr').count() == 1)
    check('write: no page errors', not errs, errs); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for he in (True, False): await gate_and_bots(b, he)
        await link_in(b); await taps(b); await small_screen(b); await write_card(b); await rules(b); await reconnect(b); await mqtt_room(b); await style_packs(b); await settings_way(b); await pass_round(b); await online(b); await deck(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
