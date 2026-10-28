exec(open('tests/test_toddler.py').read().split('# ---------------- Animal sounds')[0])
# Tachles (/tachles, adults only; the owner's party card game without its database): a long press on the copyright line opens it behind an
# 18+ gate; one phone passed round (a pass screen hides each hand), against bots, each on their own phone (a room code; here over a
# BroadcastChannel instead of PeerJS); a round: the black card, picks, the judge's choice, the point; a game played to its end; the deck ships
# without the two dropped groups. Screenshots: tests/out/tachles_*.png
TKH = '__grasp.tk'
async def click(page, sel): await page.click(sel); await page.wait_for_timeout(120)
async def view(page): return await page.evaluate(f"(() => {{ const t = {TKH}.tk; return {{ scr: t.scr, mode: t.mode, phase: t.view && t.view.phase, round: t.view && t.view.round, players: t.view && t.view.players.map((p) => p.score), log: t.log.slice(-4) }}; }})()")
async def step_local(page):
    # whatever this phone shows: a pass screen, cards to pick, answers to judge (the reveal moves on by itself)
    if await page.locator('#tachles [data-a^="iam:"]').count(): await click(page, '#tachles [data-a^="iam:"]'); return True
    if await page.locator('#tachles [data-a^="judge:"]').count(): await click(page, '#tachles [data-a^="judge:"] >> nth=0'); return True
    n = await page.locator('#tachles .tkHC').count()
    if n:
        need = await page.evaluate(f"{TKH}.tk.view ? (({TKH}.tk.mode === 'local' && {TKH}.tk.g) ? {TKH}.TK.view({TKH}.tk.g, 'x').pick : {TKH}.tk.view.pick) : 1")
        await page.evaluate(f"{TKH}.tk.sel = []")
        for i in range(need): await page.evaluate("document.querySelectorAll('#tachles .tkHC')[%d].scrollIntoView({ inline: 'center', block: 'nearest' })" % i); await page.wait_for_timeout(120); await click(page, '#tachles .tkHC >> nth=%d' % i)
        await click(page, '#tachles [data-a="send"]'); return True
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
        fill = await page.evaluate(f"(() => {{ const m = document.querySelector('#tachles .tkBlackC mark'), c = {TKH}.tk.view.hand[1]; return [m ? m.textContent : null, c]; }})()")
        check(tag + ': the picked card shows inside the question, as one whole sentence', fill[0] and fill[1].startswith(fill[0].split(' ')[0]) and fill[0].rstrip('.') == fill[1].rstrip('.!'), fill)
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
            mk = await page.evaluate("[document.querySelectorAll('#tachles .tkSub').length, document.querySelectorAll('#tachles .tkSub .tkSent mark').length, document.querySelectorAll('#tachles .tkBlackC mark').length, document.querySelectorAll('#tachles .tkSub.stag').length]")
            await page.screenshot(path=OUT + 'tachles_reveal_%s.png' % tag.lower()); shot = True
            check(tag + ': the reveal: every answer is a whole sentence (the question with the answer marked in it), all at once; the winner\'s sentence in the question card', mk[0] >= 1 and mk[1] >= mk[0] and mk[2] >= 1 and mk[3] == 0, mk)
        if not await step_local(page): await page.wait_for_timeout(80)
    await page.wait_for_timeout(200); v = await view(page)
    check(tag + ': the game played to the end (3 points), round after round on its own; the win screen (trophy, podium, New game)', v['phase'] == 'over' and max(v['players']) == 3 and await page.locator('#tachles .tkMedal').count() == 3 and await page.locator('#tachles [data-a="again"]').count() == 1, v)
    await page.screenshot(path=OUT + 'tachles_over_%s.png' % tag.lower())
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
    await click(host, '#tachles [data-a="start"]'); await host.wait_for_timeout(400); pages = [host, g1, g2]
    vs = [await view(p) for p in pages]; check('online: the host starts: every phone in the game, round 1', all(v['scr'] == 'game' and v['round'] == 1 for v in vs), vs)
    hands = [await p.evaluate(f"{TKH}.tk.view.hand.join('|')") for p in pages]; check('online: each phone sees only its own hand (three different hands)', len(set(hands)) == 3, [h[:30] for h in hands])
    J = await host.evaluate(f"{TKH}.tk.view.judge"); pick = [p for p in pages if await p.evaluate(f"{TKH}.tk.view.me") != J]
    await step_local(pick[0]); await host.wait_for_timeout(200)
    check('online: one answered, one left: the status chips (a tick, a pulsing avatar) and a tease line for the last one', await pick[1].locator('#tachles .tkTick').count() == 1 and await pick[1].locator('#tachles .tkTease').count() == 1)
    await pick[1].screenshot(path=OUT + 'tachles_guest_he.png')
    for k in range(30):
        if (await view(host))['phase'] == 'reveal': break
        for p in pages:
            if (await view(host))['phase'] == 'reveal' or (await view(host))['round'] > 1: break
            await step_local(p)
        await host.wait_for_timeout(150)
    v = await view(host); check('online: everyone answers, the czar picks: a point, every phone sees the trophy on the winning answer', v['phase'] == 'reveal' and sum(v['players']) == 1 and (await view(g2))['phase'] == 'reveal' and await g2.locator('#tachles .tkSub.win .tkTrophy').count() == 1, [v, await view(g2)])
    await g2.screenshot(path=OUT + 'tachles_online_reveal_he.png')
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
    await click(page, '#tachles [data-a="packs"]'); check('packs: a sheet of 13 packs, each with ⚠️ a warning and a card count, all on', await page.locator('#tachles .tkPk').count() == 13 and await page.locator('#tachles .tkPk.on').count() == 13 and await page.locator('#tachles .tkPk small:has-text("⚠️")').count() == 13)
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
    await click(page, '#tachles [data-a="start"]'); await page.wait_for_timeout(300)
    r = await page.evaluate(f"""(() => {{ const g = {TKH}.tk.g, d = g.deck, ws = g.players.flatMap((p) => p.hand).concat(g.wd), bs = g.bd.concat([g.black]);
      const bad = (m) => +m[0] > 1 || m.includes('s', 1) || m.includes('f', 1); return {{ n: ws.length, badW: ws.filter((i) => bad(d.wm[i])).length, badB: bs.filter((i) => bad(d.bm[i])).length }}; }})()""")
    check('style: the game at 🟢 without sex and family: every card in the hands, the pile and the questions passes', r['n'] > 50 and r['badW'] == 0 and r['badB'] == 0, r)
    check('style: no page errors', not errs, errs); await ctx.close()

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
    # write your own card (the owner: Evil Apples' wildcards; to his email for approval): a black one with two blanks is sent (FormSubmit, mocked here)
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
        await write_card(b); await rules(b); await style_packs(b); await settings_way(b); await pass_round(b); await online(b); await deck(b)
        await b.close()
    print('FAILURES:', check.fails)
try: asyncio.run(main())
finally: srv.terminate()
if check.fails: sys.exit(1)
