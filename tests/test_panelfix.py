exec(open('tests/test_challenge.py').read().split('async def main')[0])
# The 6-persona playtest fixes (see HANDOFF.md "Panel fixes").
# Batch 1 (bugs): 1 Slice: a bomb on the last heart shows the card and the frame loop keeps running (and one mode's exception never kills the
# loop); 2 Smash: a thing knocked off the screen is broken and credited (the wave completes), the speed clamp, the idle aid; 3 a canvas card's Home
# never taps through to the start screen; 4 the run-power title is its own i18n key; 5 the Replay pill's label clear of its thumb (HE); 6 touch
# wording under the cards (EN / HE) and the Daily panel's Play first; 7 no request for the missing monkey art; 8 toasts under an open sheet's
# header; 9 singular forms; 10 "Strike" translated in the HE Shop; 11 canvas bidi (+1, ×7 in Hebrew); 12 the sticker slot is no dark block;
# 13 the Frenzy card's Map; 14 the card's missions by the game played; 15 the meta pill's XP part opens the Road; 16 Tremorti: an 18 Hz rhythm
# is "unusual for tremor, possibly a measurement artefact".
# Batch 2 (feel): Strike's fingertip marker (touch) / ghost hand (camera) under the ball, labels off the ball, one serve instruction, Easy
# pacing (tests/strike_sim.js), Frenzy ramp, ranks; camera hand-loss (600 ms gap: no pause / no countdown in a free mode, a quiet chip in a timed
# one; the card's "More help"); the camera stays on at home and the hand dwells on tiles / map stops; drums (gentle strike, 2 samples, Harder!);
# paint's erase confirm; Busy Board (music on top, ~175 px cells, drag-scroll, a 3-word hint); Bubble Pop (the prompt once per device, no picker
# line, Calm keeps 5); Sandbox (mid-screen start, the toy box, the hint at the top); the pet (a starter snack, the Scarf at Baby); the economy
# (the welcome gift, a 150-coin theme, the map's next-purchase goal); Slice (2 s grace, 5 hearts in the first round, phone fruit, round length).
# Screenshots: tests/out/fix_*.png. State changes are polled (timing-independent).
import math
SIM = open('tests/strike_sim.js').read() + "\n;0"
SLSIM = open('tests/slice_sim.js').read() + "\n;0"
PF = "__grasp.panelfix"
CAMJS = open('tests/test_camgames.py').read().split('POINT_JS = """')[1].split('"""')[0]
FR = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
def overl(a, b): return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']

async def camfresh(b, mobile=False, he=False, init=''):  # a page with the camera stub, the camera chosen
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(permissions=['camera'], **opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    await page.add_init_script(INIT + HAND_JS + CAMJS + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');localStorage.setItem('inputPref','camera');" + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("typeof __grasp !== 'undefined' && !!__grasp.panelfix", timeout=10000); await page.wait_for_timeout(500)
    await page.evaluate(SFX_JS)
    return ctx, page, errs

async def tap_at(page, mobile, x, y):
    if mobile: await page.touchscreen.tap(x, y)
    else: await page.mouse.click(x, y)

async def slice_start(page, mobile):
    await (page.tap if mobile else page.click)('.modes button[data-mode=slice]')
    await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=10000)

async def slice_end(page):  # three misses (the suites' 3-heart rounds)
    for _ in range(8):
        if await page.evaluate("__grasp.slice.over"): break
        await page.evaluate("(() => { __grasp.CONFIG.SLICE_GRAVITY = 0; const f = __grasp.slice; f.nextSpawn = 1e12; f.fruits.push({ x: 300, y: innerHeight + 100, vx: 0, vy: 0.5, r: 40, rot: 0, vr: 0, kind: {rind:'#ffc24b', flesh:'#ffe3a1', seed:null}, born: 0 }); })()")
        await page.wait_for_timeout(120)
    await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=4000); await page.wait_for_timeout(650)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ================= 1. Slice: a bomb on the last heart: the card, and the frame loop goes on =================
        ctx, page, errs = await fresh(b)
        await slice_start(page, False)
        await page.evaluate("(() => { __grasp.CONFIG.SLICE_GRAVITY = 0; const s = __grasp.slice; s.lives = 1; s.fruits.length = 0; s.nextSpawn = 1e12; s.fruits.push({ x: 640, y: 400, vx: 0, vy: 0, r: 40, rot: 0, vr: 0, kind: BOMB, bomb: true, born: 0 }); })()")
        await page.mouse.move(380, 400); await page.mouse.down()
        for i in range(1, 13): await page.mouse.move(380 + i * 45, 400); await page.wait_for_timeout(16)
        await page.mouse.up()
        await page.wait_for_function("__grasp.slice.over", timeout=3000)
        await page.wait_for_function("__grasp.slice.ui.buttons", timeout=4000); f0 = await page.evaluate("__grasp.gfx.fxp.frame")
        try: await page.wait_for_function(f"__grasp.gfx.fxp.frame > {f0} + 5", timeout=4000)
        except Exception: pass
        f1 = await page.evaluate("__grasp.gfx.fxp.frame")
        st = await page.evaluate(f"({{ over: __grasp.slice.over, lives: __grasp.slice.lives, bombs: __grasp.slice.bombsHit, btn: Object.keys(__grasp.slice.ui.buttons || {{}}), err: {PF}.frameErr.n }})")
        check('1 Slice: slicing a bomb on the last heart ends the round: the round-over card (Play again / Home), no exception', st['over'] and st['lives'] == 0 and st['bombs'] == 1 and 'again' in st['btn'] and 'home' in st['btn'] and st['err'] == 0 and not errs, [st, errs])
        check('1 Slice: the frame loop keeps running after it (frames advance)', f1 > f0 + 5, [f0, f1])
        await page.evaluate("window.__boom = 1; window.__rs = renderSlice; renderSlice = (n) => { if (window.__boom) { window.__boom = 0; throw new Error('panelfix boom'); } window.__rs(n); }; 0")
        g0 = await page.evaluate("__grasp.gfx.fxp.frame"); await page.wait_for_function(f"{PF}.frameErr.n >= 1 && __grasp.gfx.fxp.frame > {g0} + 10", timeout=4000)
        await page.evaluate("renderSlice = window.__rs; 0")
        check('1 the frame loop survives an exception in a mode (caught, reported once as a page error, frames go on)', await page.evaluate(f"{PF}.frameErr.n") == 1 and sum('panelfix boom' in e for e in errs) == 1, errs)
        await ctx.close()

        # ================= 2. Smash: a thing knocked off the screen is credited; the wave completes =================
        ctx, page, errs = await fresh(b)
        await page.click('.modes button[data-mode=smash]'); await page.wait_for_function("!$('smashMap').hidden", timeout=6000); await page.click('#smashFree')
        await page.wait_for_function("gameMode === 'smash' && mode === 'mouse' && __grasp.smash.phase === 'play'", timeout=10000)
        await page.evaluate("__grasp.sm.build('room')"); await page.wait_for_timeout(200)
        r = await page.evaluate("""(() => { const S = __grasp.smash, dyn = S.objs.filter(o => o.alive && !o.stat && o.kind !== 'boss' && o.wave === S.wave).sort((a, b) => b.value - a.value), a = dyn[0], c = dyn[1], now = performance.now();
          M.Body.setPosition(a.body, { x: innerWidth / 2, y: innerHeight + 5000 }); M.Body.setPosition(c.body, { x: -300, y: innerHeight / 2 });
          for (const T of S.tiles) for (let i = 0; i < T.cells.length; i++) if (T.cells[i]) smTileKnock(T, i, Math.floor(i / T.nc), i % T.nc, 0, 0, 1, now, false);
          for (const o of S.objs) if (o.alive && o !== a && o !== c && o.kind !== 'boss') smBreak(o, o.body.position.x, o.body.position.y, 0, 0, 0.4, now);
          return { meter: smMeter(), lost0: S.lost || 0, wave: S.wave, kinds: [a.kind, c.kind] }; })()""")
        await page.wait_for_function(f"(__grasp.smash.lost || 0) >= {r['lost0'] + 2}", timeout=4000)
        await page.wait_for_function(f"__grasp.smash.phase === 'scroll' || __grasp.smash.wave > {r['wave']}", timeout=5000)
        q = await page.evaluate("({ lost: __grasp.smash.lost, wave: __grasp.smash.wave, phase: __grasp.smash.phase })")
        check('2 Smash: things knocked out of the screen (below the floor, past the side) are broken and credited, so the wave completes (it stalled at 70-80%)', q['lost'] >= r['lost0'] + 2 and (q['phase'] == 'scroll' or q['wave'] > r['wave']), [r, q])
        await page.wait_for_function("__grasp.smash.phase === 'play'", timeout=6000)
        v = await page.evaluate("(() => { const o = __grasp.smash.objs.find(o => o.alive && !o.stat && o.kind !== 'boss'); if (!o) return null; M.Body.setVelocity(o.body, { x: 400, y: 300 }); return o.id; })()")
        await page.evaluate(FR)
        sp = await page.evaluate(f"(() => {{ const o = __grasp.smash.objs.find(o => o.id === {v or 0}); return o ? Math.hypot(o.body.velocity.x, o.body.velocity.y) : 0; }})()")
        check('2 Smash: a thing hit very hard is clamped (no tunnelling through the 400 px walls)', v is not None and sp <= 38.5, [v, sp])
        await page.evaluate("__grasp.sm.build('room')"); await page.wait_for_timeout(200)
        mt = await page.evaluate("(() => { const m = __grasp.sm.breakTo(0.66); const S = __grasp.smash; S.lastHitAt = performance.now() - 9000; S.phaseAt = performance.now() - 9000; S.aidAt = -1e9; return { m, seg: S.seg, phase: S.phase, run: S.run }; })()")
        await page.wait_for_function("(__grasp.smash.autoNext || 0) >= 1", timeout=4000)
        check('2 Smash: nothing hit for 8 s: the things left tremble, and free play rolls on with most of the wave smashed', 0.6 <= mt['m'] < 0.85 and await page.evaluate("__grasp.smash.aids >= 1 && __grasp.smash.autoNext >= 1"), mt)
        check('2 Smash: no page errors', not errs, errs); await ctx.close()

        # ================= 3. tap-through: a card's Home on the phone never lands on the start screen under it =================
        for he in (False, True):
            ctx, page, errs = await fresh(b, mobile=True, he=he, init="localStorage.setItem('inputPref','mouse');")
            await slice_start(page, True); await slice_end(page)
            h = await page.evaluate("__grasp.slice.ui.buttons.home"); x, y = h['x'] + h['w'] / 2, h['y'] + h['h'] / 2
            await page.evaluate("window.__clicks = []; document.addEventListener('click', (e) => { if (e.isTrusted) __clicks.push(e.target.id || e.target.className || e.target.tagName); });")
            await page.touchscreen.tap(x, y)
            await page.wait_for_function("mode === 'none' && !$('start').hidden", timeout=4000); await page.wait_for_timeout(600)
            o = await page.evaluate(f"(() => {{ const el = document.elementFromPoint({x}, {y}), btn = el && el.closest && el.closest('button'); return {{ under: btn ? (btn.id || btn.dataset.mode || btn.className) : (el && el.id), clicks: __clicks, room: !$('petRoom').hidden, ov: [...document.querySelectorAll('.ov')].filter(e => !e.hidden).map(e => e.id), pick: !$('cgPick').hidden, mode, gm: gameMode, guard: {PF}.cguard.until > 0 }}; }})()")
            check(f'3 tap-through ({"HE" if he else "EN"} phone): the card\'s Home goes home and its tap reaches nothing under it (was: the pet room opened)', not o['clicks'] and not o['room'] and not o['ov'] and not o['pick'] and o['mode'] == 'none' and o['gm'] == 'slice' and o['guard'], o)
            await page.wait_for_timeout(200); await page.tap('#petInfoBtn'); await page.wait_for_timeout(300)
            check(f'3 ...a real tap afterwards still works (the pet room opens)', await page.evaluate("!$('petRoom').hidden"))
            check('3 no page errors', not errs, errs); await ctx.close()

        # ================= 4 + 5. the run-power title's own key; the Replay pill (HE) =================
        ctx, page, errs = await fresh(b, mobile=True)
        k = await page.evaluate("({ rp: t('rpTitle'), run: t('runPowTitle'), rpHe: I18N.he.rpTitle, runHe: I18N.he.runPowTitle })")
        check('4 i18n: the replay title and the run-power title are separate keys (EN / HE)', k == {'rp': 'Your best moment', 'run': 'Power for the next stage!', 'rpHe': 'הרגע הכי טוב שלכם', 'runHe': 'כוח לשלב הבא!'}, k)
        await stage(page, 3); await page.evaluate(f"{A}.finishTest(0)")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.next && performance.now() - {S}.overAt > 600", timeout=10000)
        r = await page.evaluate(f"{S}.ui.buttons.next"); await page.touchscreen.tap(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
        await page.wait_for_function(f"{S}.perkOffer && {S}.ui.perkCards && {S}.ui.perkCards.length === 3 && {S}.ui.perkTitle", timeout=6000); await page.wait_for_timeout(400)
        check('4 the run-power cards say "Power for the next stage!" (not the replay\'s "Your best moment")', await page.evaluate(f"{S}.ui.perkTitle") == 'Power for the next stage!')
        await page.screenshot(path='tests/out/fix_runpower_title.png')
        check('4 no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, he=True)
        await slice_start(page, False)
        await page.evaluate("__grasp.replay.rp.noGate = true"); c0 = await page.evaluate("__grasp.replay.state.caps"); await page.wait_for_function(f"__grasp.replay.state.caps >= {c0 + 70}", timeout=30000)
        await page.evaluate("(() => { const c = __grasp.slice.combo; c.n = 5; c.t = performance.now(); })()"); await page.wait_for_timeout(1800)
        await slice_end(page)
        await page.wait_for_function("__grasp.slice.ui.rpBtn && performance.now() - __grasp.slice.overAt > 900", timeout=15000)
        q = await page.evaluate("__grasp.slice.ui.rpBtn")
        ok = q['lab']['x'] + q['lab']['w'] <= q['thumb']['x'] - 2 and q['lab']['x'] >= q['play']['x'] + q['play']['w'] + 2
        check('5 the Replay pill in Hebrew: the label "הילוך חוזר" sits between the ▶ and the thumbnail, overlapping neither', q['label'] == 'הילוך חוזר' and ok, q)
        await page.screenshot(path='tests/out/fix_replay_pill_he.png')
        check('5 no page errors', not errs, errs); await ctx.close()

        # ================= 6. the cards' lines in touch wording (EN / HE); the Daily panel's Play first =================
        for he in (False, True):
            tag = 'he' if he else 'en'
            ctx, page, errs = await fresh(b, mobile=True, he=he)
            await stage(page, 1); await page.evaluate(f"{A}.finishTest(0)")
            await page.wait_for_function(f"{S}.over && {S}.ui.againLine && performance.now() - {S}.overAt > 1100", timeout=10000)
            ln = await page.evaluate(f"{S}.ui.againLine")
            check(f'6 {tag}: a stage clear by touch says "Tap Next…", not "Wave…"', ln == ('הקישו על „הבא” לשלב הבא' if he else 'Tap Next for the next stage'), ln)
            await page.wait_for_timeout(300); await page.screenshot(path=f'tests/out/fix_card_touch_{tag}.png')
            await page.evaluate(f"{A}.start(1)"); await page.wait_for_function(f"{A}.phase === 'play'", timeout=8000); await page.evaluate(f"{A}.failTest()")
            await page.wait_for_function(f"{S}.over && {S}.ui.againLine && performance.now() - {S}.overAt > 1100 && {A}.result && !{A}.result.clear", timeout=10000)
            ln2 = await page.evaluate(f"{S}.ui.againLine")
            check(f'6 {tag}: a fail by touch says "Tap Try again"', ln2 == ('הקישו על „שוב” כדי לנסות שוב' if he else 'Tap Try again'), ln2)
            ks = await page.evaluate("(() => { const m0 = mode; const a = againKey('playAgainWave'); mode = 'camera'; const c = [againKey('playAgainWave'), againKey('advWaveNext')]; mode = m0; return [a, ...c]; })()")
            check(f'6 {tag}: Endless / camera games by touch "Tap Play again"; with the camera "Wave…" stays', ks == ['playAgainTap', 'playAgainCam', 'advWaveNext'], ks)
            check(f'6 {tag}: no page errors', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=True)
        await page.tap('#dailyBtn'); await page.wait_for_function("!$('daily').hidden", timeout=4000)
        d = await page.evaluate("(() => { const a = $('daily').querySelector('.dActs'), bs = [...a.children]; return { ids: bs.map(x => x.id), cls: bs.map(x => x.className), txt: bs.map(x => x.textContent) }; })()")
        check('6 the Daily panel: "Play" (touch) is the primary button, the camera the secondary one', d['ids'] == ['dailyMouse', 'dailyCam'] and d['cls'] == ['primary', 'secondary'] and d['txt'][0] == 'Play', d)
        await ctx.close()

        # ================= 7. no request for the missing monkey art =================
        ctx, page, errs = await fresh(b)
        bad = []; page.on('response', lambda r: bad.append(r.url + ' ' + str(r.status)) if '/assets/guests/' in r.url and r.status >= 400 else None)
        reqs = []; page.on('request', lambda r: reqs.append(r.url) if '/assets/guests/' in r.url else None)
        await endless(page); await page.wait_for_function("['in', 'happy', 'dizzy', 'squash'].every(f => GUEST_ART['cow_' + f] && GUEST_ART['cow_' + f].state !== 'loading')", timeout=10000)
        ms = await page.evaluate("['in', 'happy', 'dizzy', 'squash'].map(f => GUEST_ART['monkey_' + f].state)")
        check('7 Strike loads the cow art but never asks for monkey_*.png (no 404s); the monkey is drawn', not bad and not any('monkey_' in u for u in reqs) and any('cow_in' in u for u in reqs) and ms == ['none'] * 4, [bad, reqs, ms])
        await ctx.close()

        # ================= 8. a toast never covers an open sheet's header (the pet room's title and X) =================
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('grasp.profile.pet', '1');")
        await page.evaluate("__grasp.pet.set({ hatched: true, food: 3, pantry: 2, born: '2026-10-01', last: '2026-10-01' }); __grasp.pet.open(true)"); await page.wait_for_timeout(400)
        await page.evaluate("toast('unlockedToast', { n: 'Beach ball' }, 'star')"); await page.wait_for_timeout(500)
        o = await page.evaluate("(() => { const h = $('petRoom').querySelector('header').getBoundingClientRect(), x = $('petRoom').querySelector('.xBtn').getBoundingClientRect(), t = $('metaToast').querySelector('.mt').getBoundingClientRect(); return { h: [h.top, h.bottom], x: [x.top, x.bottom, x.left, x.right], t: [t.top, t.bottom, t.left, t.right] }; })()")
        check('8 a toast while the pet room is open sits under its header (the title and the X stay clear)', o['t'][0] >= o['h'][1] and (o['t'][0] >= o['x'][1] or o['t'][3] <= o['x'][2] or o['t'][2] >= o['x'][3]), o)
        await page.screenshot(path='tests/out/fix_toast_petroom.png')
        await ctx.close()

        # ================= 9-11. singular forms; "Strike" in the HE Shop; canvas bidi in Hebrew =================
        ctx, page, errs = await fresh(b, he=True)
        tx = await page.evaluate("(() => { const L = lang, r = {}; lang = 'en'; r.en1 = t('dayChestNeed', { n: 1 }); r.en2 = t('dayChestNeed', { n: 2 }); r.coins1 = t('coinsN', { n: 1 }); lang = 'he'; r.he1 = t('dayChestNeed', { n: 1 }); r.he2 = t('dayChestNeed', { n: 2 }); r.sub = t('themesSub'); lang = L; return r; })()")
        check('9 plurals: "Clear 1 more stage today…" (not "1 more stages"), 2 = plural; Hebrew too', tx['en1'] == 'Clear 1 more stage today to open the chest' and tx['en2'] == 'Clear 2 more stages today to open the chest' and tx['coins1'] == '1 coin' and tx['he1'] == 'סיימו עוד שלב אחד היום כדי לפתוח את התיבה' and 'שלבים' in tx['he2'], tx)
        check('10 the HE Shop\'s Themes subtitle has no English "Strike"', 'Strike' not in tx['sub'] and 'מכה' in tx['sub'], tx['sub'])
        bd = await page.evaluate(f"""(() => {{ const P = {PF}, a = P.bidiDir('+1'), b = P.bidiDir('רצף ×7!'), c = P.bidiText('רצף ‎×7!'), d = P.bidiText('+5');
          const sp = (txt) => {{ TEXTS.clear(); return textSprite(txt, 20, '#ffffff', null).c.toDataURL(); }}; const he = sp('+1'); const L = lang; lang = 'en'; const en = sp('+1'); lang = L;
          return {{ a, b, c, d, same: he === en }}; }})()""")
        check('11 canvas bidi (HE): "+1" is drawn left-to-right (the same pixels as in English, not "1+"); "×7" in "רצף ×7!" is an LTR isolate', bd['a'] == 'ltr' and bd['b'] == 'rtl' and '⁦×7⁩' in bd['c'] and bd['d'] == '+5' and bd['same'], bd)
        await ctx.close()

        # ================= 12. the sticker slot on the card is no dark block =================
        ctx, page, errs = await fresh(b, mobile=True)
        await stage(page, 1)
        await page.evaluate("window.__sil = 0; const o = stickerSprite; stickerSprite = (n, sil, R) => { if (sil) __sil++; return o(n, sil, R); }; 0")
        await page.evaluate(f"{A}.finishTest(0)")
        await page.wait_for_function(f"{S}.over && {S}.ui.advSticker", timeout=10000); await page.wait_for_timeout(300)
        await page.screenshot(path='tests/out/fix_sticker_slot.png')
        await page.wait_for_function(f"{S}.ui.advSticker && {S}.ui.advSticker.landed", timeout=8000)
        check('12 the new sticker\'s slot on the card is a faint ring (the dark silhouette, a black block while the card came in, is not drawn)', await page.evaluate("__sil") == 0)
        await ctx.close()

        # ================= 13 + 14. the Frenzy card's Map; the card's missions by the game =================
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate("(() => { profile.missions = { date: missionDay(), list: [{ id: 'cars', goal: 2, progress: 0, reward: 15, done: false, claimed: false }, { id: 'walls', goal: 6, progress: 1, reward: 22, done: false, claimed: false }, { id: 'fruit', goal: 15, progress: 0, reward: 15, done: false, claimed: false }] }; saveProfile(); })()")
        await page.click('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen", timeout=8000); await page.click('#advFrenzy')
        await page.wait_for_function("__grasp.frenzy.on && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.shield = 0; s.serve(); s.setBallZ(-__grasp.CONFIG.STRIKE_HIT_Z * 0.9, 30, 30); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.map && performance.now() - {S}.overAt > 600", timeout=8000)
        fc = await page.evaluate(f"({{ btn: Object.keys({S}.ui.buttons), rows: {S}.ui.missionRow.map(r => r.id), tz: {S}.ui.teaser && {S}.ui.teaser.kind }})")
        check('13 the Frenzy card has a Map button beside Home', 'map' in fc['btn'] and 'home' in fc['btn'] and 'again' in fc['btn'], fc)
        check('14 the Frenzy card lists only the missions Frenzy can move on (walls; not "Crumple 2 cars" or fruit)', fc['rows'] == ['walls'], fc)
        await page.screenshot(path='tests/out/fix_frenzy_card.png')
        r = await page.evaluate(f"{S}.ui.buttons.map"); await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
        await page.wait_for_function(A + ".mapOpen", timeout=4000)
        check('13 its Map opens the Adventure map', await page.evaluate(A + ".mapOpen"))
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.click('.modes button[data-mode=slice]'); await page.wait_for_function("gameMode === 'slice' && mode === 'mouse'", timeout=8000); await slice_end(page)
        sr = await page.evaluate("__grasp.slice.ui.missionRow.map(r => r.id)")
        check('14 a Slice card lists the fruit mission only', sr == ['fruit'], [sr, await page.evaluate("profile.missions")])
        check('13/14 no page errors', not errs, errs); await ctx.close()

        # ================= 15. the meta pill: coins open the Shop, the XP part opens the Road =================
        ctx, page, errs = await fresh(b)
        await page.evaluate("__grasp.addXp(60)"); await page.wait_for_timeout(200)
        await page.click('#metaPill .lvl'); await page.wait_for_timeout(200)
        a1 = await page.evaluate("({ road: !$('road').hidden, shop: !$('collection').hidden })"); await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        nx = await page.evaluate("!$('metaPill').querySelector('.nx').hidden")
        if nx: await page.click('#metaPill .nx'); await page.wait_for_timeout(200)
        a2 = await page.evaluate("({ road: !$('road').hidden })") if nx else {'road': True}; await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
        await page.click('#metaPill .coins'); await page.wait_for_timeout(200)
        a3 = await page.evaluate("({ road: !$('road').hidden, shop: !$('collection').hidden })")
        check('15 the meta pill: the level / "… XP to: …" part opens the Road, the coins the Shop', a1 == {'road': True, 'shop': False} and a2['road'] and a3 == {'road': False, 'shop': True}, [a1, a2, a3, nx])
        await ctx.close()

        # ================= 16. Tremorti: an unusual rate is not called a tremor pattern =================
        ctx = await b.new_context(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True); page = await ctx.new_page(); terrs = []
        page.on('pageerror', lambda e: terrs.append(str(e)))
        await page.add_init_script("localStorage.setItem('tremor.lang','en'); try { localStorage.setItem('lang','en'); } catch (e) {}")
        await page.goto('http://localhost:8765/tremorti/index.html'); await page.wait_for_function("typeof __tremor !== 'undefined'", timeout=10000); await page.wait_for_timeout(300)
        T = """((hz) => { const s = []; for (let i = 0; i < 1200; i++) { const t = i * 1000 / 60; s.push({ t, v: [2 * Math.sin(2 * Math.PI * hz * t / 1000) + 0.05 * Math.sin(i * 1.7)] }); }
          const r = __tremor.analyze(s, { unit: 'mm', posture: 'hold' }); Object.assign(r, { sensor: 'motion', limb: 'hand', posture: 'hold', side: '', ts: Date.now(), plannedS: 20, notes: {} }); renderResult(r);
          return { f: +r.f0.toFixed(1), s: r.strength, odd: $('resHead').dataset.odd, head: $('resHead').textContent, none: $('interpNone').hidden ? '' : $('interpNone').textContent, matches: $('matchList').children.length }; })"""
        o18 = await page.evaluate(T + "(18.2)"); o6 = await page.evaluate(T + "(6)")
        check('16 Tremorti: an 18 Hz rhythm in a hand held out: "Unusual rhythm", "unusual for tremor, possibly a measurement artefact", no tremor-type matches', abs(o18['f'] - 18.2) < 0.4 and o18['odd'] == '1' and o18['head'] == 'Unusual rhythm' and 'possibly a measurement artefact' in o18['none'] and o18['matches'] == 0, o18)
        check('16 Tremorti: a 6 Hz rhythm keeps its usual reading and pattern matches', o6['odd'] == '' and o6['head'] != 'Unusual rhythm' and o6['matches'] >= 1, o6)
        sp = await page.evaluate("""((hz) => { const g = __tremor.spiralGeom(), b = 4, pts = []; for (let i = 0; i < 600; i++) { const u = i / 599, th = u * 3 * 2 * Math.PI, t = 1000 + i * 1000 / 60, r = b * th + 1.5 * Math.sin(2 * Math.PI * hz * t / 1000); pts.push({ t, x: g.cx + r * Math.cos(th), y: g.cy + r * Math.sin(th) }); }
          const res = __tremor.analyzeSpiral(pts, { cx: g.cx, cy: g.cy, mmPerPx: 0.16 }); if (res.error) return { err: res.error }; Object.assign(res, { side: '', notes: {}, ts: Date.now(), tags: [] }); spiralShowResult(res);
          return { f: +res.f0.toFixed(1), s: res.strength, odd: $('spNote').dataset.odd, note: $('spNote').textContent, rate: $('spDetails').textContent }; })(18.2)""")
        check('16 Tremorti spiral: an 18 Hz line rhythm says "unusual for tremor, possibly a measurement artefact", not the action-tremor note', sp.get('s') == 'none' or (sp.get('odd') == '1' and 'possibly a measurement artefact' in sp['note'] and 'unusual for tremor' in sp['rate'] and 'essential tremor' not in sp['note']), sp)
        await page.screenshot(path='tests/out/fix_tremorti_spiral_odd.png', full_page=True)
        check('16 Tremorti: no page errors', not terrs, terrs); await ctx.close()

        # ======================= Batch 2 =======================
        # ---- Strike on touch: the small fingertip marker under the ball; labels off the ball; one serve instruction ----
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('inputPref','mouse');")
        await page.evaluate(SIM)
        await page.tap('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen", timeout=8000)
        await page.tap('#advPath .anode[data-n="1"]'); await page.wait_for_function(f"{A}.on && {A}.phase === 'play' && {S}.ui.levelBanner && {S}.ui.serve", timeout=10000)
        s1 = await page.evaluate(f"({{ shown: {S}.ui.serve.shown, hint: getComputedStyle($('hint')).opacity, tips: __grasp.grippy.tips.map(x => x.id), ptips: profile.tips.slice() }})")
        check('Strike: one serve instruction: under the stage banner the "Pull back, then flick!" line waits; no how-to toast, no flick tip toast', s1['shown'] is False and float(s1['hint']) < 0.05 and 'flick' not in s1['tips'], s1)
        await page.wait_for_function(f"!{S}.ui.levelBanner && {S}.ui.serve && {S}.ui.serve.shown", timeout=8000)
        check('Strike: then the line over the ball is the one instruction (the flick tip recorded, never toasted)', await page.evaluate("profile.tips.includes('flick') && !__grasp.grippy.tips.some(x => x.id === 'flick')"))
        await page.evaluate("hideHint()")
        bx = await page.evaluate(f"{S}.ui.serve"); await page.touchscreen.tap(10, 10)
        await page.evaluate(f"""(() => {{ const c = document.getElementById('stage'), ev = (t, x, y) => c.dispatchEvent(new PointerEvent(t, {{ pointerId: 3, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }})); ev('pointerdown', {bx['x'] + 30}, {bx['y'] + 70}); window.__tp = ev; }})()""")
        await page.wait_for_function(f"{S}.ui.handDraw && {S}.ui.handDraw.kind === 'tip'", timeout=4000)
        hd = await page.evaluate(f"{S}.ui.handDraw")
        check('Strike touch: the big see-through hand is gone: a small fingertip ring (r ~11 px), drawn under the ball and walls', hd['kind'] == 'tip' and hd['r'] <= 16 and hd['under'], hd)
        await page.screenshot(path='tests/out/fix_strike_touch_tip.png')
        await page.evaluate(f"__tp('pointerup', {bx['x'] + 30}, {bx['y'] + 70})")
        await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.setBallZ(300, innerWidth / 2, innerHeight * 0.55); s.ball.speed = 0; s.floaters.length = 0; const sc = ballScreen(s.ball); addFloater({{ text: 'SUPER!', x: sc.x, y: sc.y, big: true }}); addFloater({{ text: 'Hard', x: sc.x, y: sc.y }}); }})()")
        await page.evaluate(FR); await page.wait_for_timeout(100)
        fl = await page.evaluate(f"(() => {{ const sc = ballScreen({S}.ball); return {{ ball: {{ x: sc.x - sc.r, y: sc.y - sc.r, w: 2 * sc.r, h: 2 * sc.r }}, rects: {S}.ui.floaterRects }}; }})()")
        check('Strike: floating labels ("SUPER!", "Hard") never sit on the ball', fl['rects'] and not any(overl(r, fl['ball']) for r in fl['rects']), fl)
        check('Strike touch: no page errors', not errs, errs); await ctx.close()

        # ---- Easy pacing: stage 1 with a still finger (the sim), the soft hit, the Frenzy ramp, the ranks ----
        ctx, page, errs = await fresh(b, mobile=True)
        await page.evaluate(SIM); await stage(page, 1)
        pl = await page.evaluate(f"({{ plan: {A}.plan(1), plan4: {A}.plan(4), plan5: {A}.plan(5) }})")
        check('pacing: world 1\'s gentle stages: faster (x1.4 tapering), aim help, soft hits break 2 on stages 1-3', abs(pl['plan']['paceK'] - 1.4) < 1e-9 and pl['plan']['assist'] and pl['plan']['soft2'] and not pl['plan4']['soft2'] and pl['plan4']['assist'] and not pl['plan5']['assist'], pl)
        await page.evaluate(f"{S}.noRally = false")
        r = await page.evaluate("advSim({ player: 'still', seed: 1, maxS: 200 })")
        print('     strike stage 1 (still finger, phone, Easy): %s s, %s hits' % (r['t'], r['hits']))
        check('pacing: stage 1 with a still finger (every ball back, soft hits) takes 30-45 s (was ~95 s)', r['t'] is not None and 30 <= r['t'] <= 45, r)
        rk = await page.evaluate("({ par: stagePar(1), r1: rankFor(1, 99999, 1), r2: rankFor(1, 99999, 2), r3: rankFor(1, 99999, 3), d: rankFor(1, Math.round(3 * stagePar(1)) + 5, 3), th: rankThresholds(1) })")
        check('ranks: par doubled (stage 1: 320), a rank above Bronze needs 2 stars (a 1-star clear = Bronze whatever the score)', rk['par'] == 320 and rk['r1'] == 0 and rk['r2'] == 4 and rk['r3'] == 4 and rk['d'] == 3, rk)
        fz = await page.evaluate("(() => { frenzy.on = true; const k = [1, 2, 5, 10, 11, 20].map(n => +rallyK(n).toFixed(4)); frenzy.on = false; return k; })()")
        check('Frenzy: +9% a hit for the first 10 hits, then +4%', fz == [1.09, 1.18, 1.45, 1.9, 1.94, 2.3], fz)
        check('pacing: no page errors', not errs, errs); await ctx.close()

        # ---- Slice: 2 s grace, 5 hearts in the session's first round, bigger / slower phone fruit, round length ----
        ctx, page, errs = await fresh(b, mobile=True, init="window.__graspSlice3 = false;")
        await page.evaluate(SLSIM)
        await slice_start(page, True)
        s0 = await page.evaluate("({ lives: __grasp.slice.lives, max: __grasp.slice.maxLives, wait: __grasp.slice.nextSpawn - performance.now(), r: sliceScale().r, g: sliceScale().g, base: Math.max(28, Math.min(60, Math.min(innerWidth, innerHeight) * 0.085)), g0: __grasp.CONFIG.SLICE_GRAVITY * innerHeight / 800 })")
        check('Slice: the first round of a visit has 5 hearts; the first fruit waits ~2 s', s0['lives'] == 5 and s0['max'] == 5 and 1500 < s0['wait'] <= 2000, s0)
        check('Slice on a phone: fruit ~22% bigger and slower (gravity x0.78)', abs(s0['r'] / s0['base'] - 1.22) < 0.01 and abs(s0['g'] / s0['g0'] - 0.78) < 0.01, s0)
        await page.wait_for_timeout(300); await page.screenshot(path='tests/out/fix_slice_hearts5.png')
        r1 = [await page.evaluate(f"sliceSim({{ seed: {sd}, first: true }})") for sd in range(1, 7)]
        r2 = [await page.evaluate(f"sliceSim({{ seed: {sd} }})") for sd in range(1, 7)]
        t1 = sorted(x['t'] for x in r1); t2 = sorted(x['t'] for x in r2)
        print('     slice rounds (simulated child, phone): first %s (median %.1f s), later %s (median %.1f s)' % (t1, t1[3], t2, t2[3]))
        check('Slice: later rounds have 3 hearts; a simulated child\'s first round lasts ~15+ s (median; was ~10 s with 3 hearts)', all(x['lives0'] == 5 for x in r1) and all(x['lives0'] == 3 for x in r2) and t1[3] >= 15, [t1, t2])
        check('Slice: no page errors', not errs, errs); await ctx.close()

        # ---- the camera: a short gap (600 ms) in a free mode: no pause, no countdown; in a timed mode: a quiet chip, no pause ----
        ctx, page, errs = await camfresh(b)
        await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)")
        await page.click('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.click('#cgPick [data-cg=drums]')
        await page.wait_for_function("mode === 'camera' && gameMode === 'drums' && __grasp.panelfix.handNow(performance.now())", timeout=15000); await page.wait_for_timeout(500)
        WATCH = "window.__w = { pause: false, count: false, card: false, chip: false }; (function f() { const w = window.__w; if (pause.on) w.pause = true; if (pause.resumeT) w.count = true; if (!statusEl.hidden) w.card = true; if (!$('handChip').hidden) w.chip = true; if (!w.stop) requestAnimationFrame(f); })();"
        await page.evaluate(WATCH); await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(600); await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)")
        await page.wait_for_function(f"{PF}.handNow(performance.now())", timeout=4000); await page.wait_for_timeout(400); w = await page.evaluate("__w.stop = true, __w")
        gap = await page.evaluate(f"{PF}.nh.lastGap")
        check('camera: a 600 ms gap in a free mode (Air Drums): no pause, no countdown, no card', 450 <= gap < 1100 and not w['pause'] and not w['count'] and not w['card'], [gap, w])
        await page.evaluate("window.__handFor = null"); await page.wait_for_timeout(1500)
        fm = await page.evaluate("({ pause: pause.on, card: !statusEl.hidden, chip: !$('handChip').hidden })")
        check('camera: a longer gap in a free mode never pauses (a quiet "Hand?" chip)', not fm['pause'] and fm['chip'], fm)
        await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)"); await page.wait_for_timeout(500)
        # a timed mode: Bubble Pop's 60 s round
        await page.evaluate("$('pauseBtn').click()"); await page.wait_for_timeout(100); await page.evaluate("$('homeBtn').click()"); await page.wait_for_function("mode === 'none'", timeout=4000)
        await page.evaluate("localStorage.setItem('bubblesCalm', '0'); __grasp.cg.bubbles.calm = false")
        await page.click('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.click('#cgPick [data-cg=bubbles]')
        await page.wait_for_function("mode === 'camera' && gameMode === 'bubbles' && __grasp.panelfix.handNow(performance.now())", timeout=15000); await page.wait_for_timeout(500)
        await page.evaluate(WATCH); await page.evaluate("window.__handFor = null"); await page.wait_for_function("!$('handChip').hidden", timeout=3000)
        await page.screenshot(path='tests/out/fix_nohand_chip.png')
        l0 = await page.evaluate("__grasp.cg.bubbles.left"); await page.wait_for_timeout(150); await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)")
        await page.wait_for_function(f"{PF}.handNow(performance.now())", timeout=4000); await page.wait_for_timeout(400); w = await page.evaluate("__w.stop = true, __w")
        gap = await page.evaluate(f"{PF}.nh.lastGap")
        check('camera: a 600 ms gap in a timed mode (Bubble Pop): a quiet "Hand?" chip, the game coasts on (no pause, no 3-2-1, no card)', 450 <= gap < 1100 and w['chip'] and not w['pause'] and not w['count'] and not w['card'], [gap, w])
        await page.evaluate("window.__handFor = null"); await page.wait_for_function("pause.on", timeout=4000)
        await page.wait_for_function("!statusEl.hidden", timeout=5000)
        nc = await page.evaluate("({ title: statusEl.querySelector('h2').textContent, more: !$('nhMore').hidden, swapVis: $('swapBtn').getBoundingClientRect().height, tips: [...statusEl.querySelectorAll('.tips li')].some(li => li.getBoundingClientRect().height > 0), big: preview.classList.contains('big') })")
        check('camera: a long gap in a timed mode pauses; the card: "Show me your hand 👋" + the picture; tips and the tracker switch behind "More help"', nc['title'] == 'Show me your hand 👋' and not nc['more'] and nc['swapVis'] == 0 and not nc['tips'] and nc['big'], nc)
        await page.screenshot(path='tests/out/fix_nohand_card.png')
        await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)"); await page.wait_for_function("pause.resumeT > 0", timeout=4000)
        check('camera: after a gap over 2 s the 3-2-1 runs', await page.evaluate("pause.on && pause.resumeT > 0"))
        await page.wait_for_function("!pause.on", timeout=6000)

        # ---- the camera stays on at home: the hand dwells on a start tile / the picker / a map stop ----
        await page.evaluate("$('pauseBtn').click()"); await page.wait_for_timeout(100); await page.evaluate("$('homeBtn').click()"); await page.wait_for_function("mode === 'none'", timeout=4000); await page.wait_for_timeout(300)
        hc = await page.evaluate("({ on: __grasp.panelfix.homeCam.on, live: !!stream && stream.getTracks().every(t => t.readyState === 'live'), lm: !!landmarker })")
        check('camera: Home keeps the camera on (the stream live, the tracker kept)', hc['on'] and hc['live'] and hc['lm'], hc)
        tile = await page.evaluate("(() => { const r = document.querySelector('.modes button[data-mode=slice]').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
        await page.evaluate(f"window.__handFor = () => handAt({tile['x']}, {tile['y']}, 0.8)")
        await page.wait_for_function("!$('homeDwell').hidden && __grasp.panelfix.homeCam.q > 0.3", timeout=5000)
        await page.screenshot(path='tests/out/fix_home_dwell.png')
        await page.wait_for_function("mode === 'camera' && gameMode === 'slice'", timeout=8000)
        check('camera: the hand held on the Slice tile starts it, straight in with the camera (no checks card)', await page.evaluate("mode === 'camera' && gameMode === 'slice' && $('checks').hidden && __grasp.panelfix.homeCam.clicks.includes('slice')"))
        await page.evaluate("$('pauseBtn').click()"); await page.wait_for_timeout(100); await page.evaluate("$('homeBtn').click()"); await page.wait_for_function("mode === 'none'", timeout=4000)
        await page.evaluate("window.__handFor = () => handAt(10, 10, 0.8)")
        st = await page.evaluate("(() => { const r = document.querySelector('.modes button[data-mode=strike]').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
        await page.wait_for_timeout(300); await page.evaluate(f"window.__handFor = () => handAt({st['x']}, {st['y']}, 0.8)")
        await page.wait_for_function(A + ".mapOpen", timeout=6000)
        await page.evaluate("window.__handFor = () => handAt(10, 10, 0.8)"); await page.wait_for_timeout(300)
        nd = await page.evaluate("(() => { const n = document.querySelector('#advPath .anode[data-n=\"1\"]'); n.scrollIntoView({ block: 'center' }); const r = n.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()")
        await page.wait_for_timeout(200); await page.evaluate(f"window.__handFor = () => handAt({nd['x']}, {nd['y']}, 0.8)")
        await page.wait_for_function(f"{A}.on && {A}.stage === 1 && mode === 'camera'", timeout=8000)
        check('camera: the Strike tile and then a map stop, by hand: stage 1 starts with the camera', await page.evaluate(f"{A}.on && mode === 'camera'"))
        await page.evaluate("$('pauseBtn').click()"); await page.wait_for_timeout(100); await page.evaluate("$('homeBtn').click()"); await page.wait_for_function("mode === 'none'", timeout=4000)
        await page.evaluate("setInputPref('mouse')"); await page.wait_for_timeout(200)
        check('camera: choosing Touch on the start screen turns the home camera off', await page.evaluate("!__grasp.panelfix.homeCam.on && !stream"))
        check('camera: no page errors', not errs, errs); await ctx.close()

        # ---- Strike with the camera: the hand as a faint ghost ----
        ctx, page, errs = await camfresh(b, mobile=True)
        await page.evaluate("window.__handFor = () => handAt(innerWidth * 0.5, innerHeight * 0.7, 0.8)")
        await page.tap('.modes button[data-mode=strike]'); await page.wait_for_function(A + ".mapOpen", timeout=8000)
        await page.evaluate("profile.adv.unlocked = 40; saveProfile()"); await page.tap('#advEndless')
        await page.wait_for_function(f"mode === 'camera' && gameMode === 'strike' && {S}.ui.handDraw", timeout=15000); await page.wait_for_timeout(600)
        hd = await page.evaluate(f"{S}.ui.handDraw")
        check('Strike camera: the hand is a faint ghost (<= 35% opaque), drawn under the ball', hd['kind'] == 'ghost' and hd['alpha'] <= 0.35 and hd['under'], hd)
        await page.evaluate(f"(() => {{ const s = {S}; s.serve(); s.setBallZ(500, innerWidth * 0.5, innerHeight * 0.62); s.ball.speed = 0; }})()"); await page.evaluate(FR)
        await page.screenshot(path='tests/out/fix_strike_camera_hand.png')
        check('Strike camera: no page errors', not errs, errs); await ctx.close()

        # ---- drums: a gentle strike now counts (and a downward move over 2 samples); a near miss: "Harder!" ----
        ctx, page, errs = await fresh(b, init="localStorage.setItem('inputPref','mouse'); localStorage.setItem('cgTouchOk','1');")
        await page.click('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.click('#cgPick [data-cg=drums]')
        await page.wait_for_function("gameMode === 'drums' && mode === 'mouse'", timeout=8000); await page.evaluate(FR)
        dr = await page.evaluate("""(() => { const D = __grasp.cg.drums, P = D.pads[2], V = H / 800, mk = (pts) => ({ id: 'tst' + Math.random(), samples: pts.map(([y, t]) => ({ x: P.x, y: P.y + y, t })) }), n0 = D.hits;
          const t0 = performance.now(); D.hs = {};
          drumsStrike(mk([[-40, t0], [-40 + 0.39 * V * 100, t0 + 100]]), t0 + 100); const gentle = D.hits - n0;   // 0.39 px/ms: under the old gate (0.42), over the new (0.36)
          const n1 = D.hits; drumsStrike(mk([[-90, t0], [-30, t0 + 70], [-24, t0 + 140]]), t0 + 140); const two = D.hits - n1; // the last step slow (0.09 px/ms), the two steps together fast (0.47)
          const n2 = D.hits; D.cue = null; drumsStrike(mk([[-40, t0], [-40 + 0.25 * V * 100, t0 + 100]]), t0 + 100); return { gentle, two, near: D.hits - n2, cue: !!D.cue, gate: __grasp.panelfix.DRUM.hitV }; })()""")
        check('drums: a gentle strike (0.39 px/ms) hits; a strike spread over 2 samples hits; a near miss shows "Harder!" (no hit)', dr == {'gentle': 1, 'two': 1, 'near': 0, 'cue': True, 'gate': 0.36}, dr)
        await page.evaluate(FR); await page.screenshot(path='tests/out/fix_drums_harder.png')
        await ctx.close()

        # ---- paint: the fist-shake erase needs a second shake ----
        ctx, page, errs = await camfresh(b)
        await page.evaluate("window.__handFor = () => handAt(640, 300, 0.8)")
        await page.click('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.click('#cgPick [data-cg=paint]')
        await page.wait_for_function("mode === 'camera' && gameMode === 'paint'", timeout=15000)
        await page.evaluate("__grasp.cg.paint.ink = 999; __grasp.cg.paint.strokes = 3")
        await page.evaluate("shakeFist(640, 300, 160, 500)")
        await page.wait_for_function("__grasp.cg.paint.fist.stage === 1", timeout=8000)
        c1 = await page.evaluate("__grasp.cg.paint.cleared")
        await page.screenshot(path='tests/out/fix_paint_confirm.png')
        await page.wait_for_function("__grasp.cg.paint.cleared === 1", timeout=8000)
        check('paint: one fist shake only asks "Shake again to erase it all" (nothing erased); the second shake erases', c1 == 0 and await page.evaluate("__grasp.cg.paint.cleared") == 1)
        check('paint: no page errors', not errs, errs); await ctx.close()

        # ---- Busy Board for a toddler (phone) ----
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('inputPref','mouse');" + CAMJS)
        await page.tap('.modes button[data-mode=busy]'); await page.wait_for_function("gameMode === 'busy' && mode === 'mouse'", timeout=8000); await page.evaluate(FR)
        bz = await page.evaluate("(() => { const B = __grasp.busy, w = B.widgets.slice().sort((a, b) => a.by - b.by); return { cell: w[0].cell, top3: w.slice(0, 3).map(x => x.kind), hint: $('hint').querySelector('.tx').textContent, max: B.maxScroll }; })()")
        check('Busy Board: ~175 px cells filling a phone\'s width; the piano, xylophone and guitar on top; a 3-word hint', bz['cell'] >= 165 and set(bz['top3']) == {'piano', 'xylophone', 'guitar'} and bz['hint'] == 'Tap and drag!', bz)
        await page.screenshot(path='tests/out/fix_busy_top.png')
        bt = await page.evaluate("(() => { const B = __grasp.busy, w = B.widgets.find(x => x.kind === 'button' && x.y > 200 && x.y < innerHeight - 200) || B.widgets.find(x => x.kind === 'switch' && x.y > 200 && x.y < innerHeight - 200); return w ? { x: w.x, y: w.y, k: w.kind } : null; })()")
        if bt is None:
            await page.evaluate("__grasp.busy.scroll = 600; applyBusyScroll()"); await page.evaluate(FR)
            bt = await page.evaluate("(() => { const w = __grasp.busy.widgets.find(x => (x.kind === 'button' || x.kind === 'switch') && x.y > 200 && x.y < innerHeight - 200); return w ? { x: w.x, y: w.y, k: w.kind } : null; })()")
        s0 = await page.evaluate("__grasp.busy.scroll")
        await page.evaluate(f"touchDrag({bt['x']}, {bt['y'] + 60}, {bt['x']}, {bt['y'] - 120}, 12, 25)"); await page.wait_for_timeout(500)
        s1 = await page.evaluate("({ s: __grasp.busy.scroll, n: __grasp.busy.dragScrolls || 0 })")
        check('Busy Board: a vertical drag starting on a button scrolls the board (no widget gesture there)', s1['n'] >= 1 and s1['s'] > s0 + 60, [bt, s0, s1])
        check('Busy Board: no page errors', not errs, errs); await ctx.close()

        # ---- Bubble Pop for a toddler: the camera prompt once per device, no picker line, Calm keeps 5 bubbles ----
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('inputPref','mouse');")
        await page.tap('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000)
        check('Bubble Pop: the picker has no extra "Best with the camera!" banner', await page.evaluate("$('cgPickCam').hidden"))
        await page.tap('#cgPick [data-cg=bubbles]'); await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse'", timeout=8000)
        a1 = await page.evaluate("__grasp.cg.asking"); await page.tap('#cgCamTouch')
        await page.evaluate("goHome()"); await page.wait_for_timeout(300); await page.reload(); await page.wait_for_timeout(700)
        await page.tap('#camGamesBtn'); await page.wait_for_function("!$('cgPick').hidden", timeout=4000); await page.tap('#cgPick [data-cg=bubbles]'); await page.wait_for_function("gameMode === 'bubbles' && mode === 'mouse'", timeout=8000)
        a2 = await page.evaluate("__grasp.cg.asking")
        check('Bubble Pop: the camera prompt shows once per device (not again after a reload): 1 tap to the bubbles', a1 and not a2, [a1, a2])
        await page.evaluate("__grasp.cg.calm(true)"); await page.wait_for_timeout(100)
        n0 = await page.evaluate("__grasp.cg.bubbles.list.length")
        await page.evaluate("(() => { const B = __grasp.cg.bubbles; B.list.splice(0, B.list.length - 2); })()"); await page.wait_for_timeout(1400)
        n1 = await page.evaluate("__grasp.cg.bubbles.list.length")
        check('Bubble Pop Calm: remembered, and at least 5 bubbles about (from the start, and back to 5 after popping)', await page.evaluate("localStorage.getItem('bubblesCalm') === '1'") and n0 >= 5 and n1 >= 5, [n0, n1])
        await page.screenshot(path='tests/out/fix_bubbles_calm.png')
        check('Bubble Pop: no page errors', not errs, errs); await ctx.close()

        # ---- Sandbox: things start mid-screen, a toy box to fill, the hint at the top ----
        ctx, page, errs = await fresh(b, mobile=True, init="localStorage.setItem('inputPref','mouse');")
        await page.tap('.modes button[data-mode=sandbox]'); await page.wait_for_function("gameMode === 'sandbox' && mode === 'mouse'", timeout=8000); await page.wait_for_timeout(300)
        sb = await page.evaluate("(() => { const h = $('hint').getBoundingClientRect(), T = __grasp.panelfix.toyBox; return { hintB: h.bottom, H: innerHeight, parts: T.parts.length, box: [T.x, T.y, T.w, T.h], xs: bodies.map(b => b.position.x) }; })()")
        check('Sandbox: the hint sits at the top (clear of the things on the floor); a toy box (3 walls) in the corner', sb['hintB'] < sb['H'] * 0.45 and sb['parts'] == 3, sb)
        await page.evaluate("(() => { const T = __grasp.panelfix.toyBox, b = bodies[1]; M.Body.setPosition(b, { x: T.x + T.w / 2, y: T.y + T.h * 0.4 }); M.Body.setVelocity(b, { x: 0, y: 0 }); })()")
        await page.wait_for_function("__grasp.panelfix.toyBox.count >= 1", timeout=5000)
        check('Sandbox: a thing put in the toy box counts (chime, the number on the box)', await page.evaluate("__grasp.panelfix.toyBox.inside.size >= 1 && __sfx.includes('chime')"))
        await page.screenshot(path='tests/out/fix_sandbox_toybox.png')
        check('Sandbox: no page errors', not errs, errs); await ctx.close()

        # ---- the pet: a starter snack at the hatch (the first Feed works), the Scarf at Baby ----
        ctx, page, errs = await fresh(b, mobile=True)
        for _ in range(5): await page.evaluate("__grasp.pet.eggTap()")
        await page.wait_for_timeout(300)
        pt = await page.evaluate("({ h: __grasp.pet.p.hatched, pantry: __grasp.pet.p.pantry, scarf: __grasp.pet.equip('neck', 'scarf'), bow: __grasp.pet.equip('head', 'bow') })")
        f = await page.evaluate("__grasp.pet.feed()")
        check('pet: hatching gives 1 starter snack, so the first Feed works; a Baby can wear the Scarf (the Bow waits for Kid)', pt['h'] and pt['pantry'] == 1 and pt['scarf'] and not pt['bow'] and f and f.get('ok') and await page.evaluate("__grasp.pet.p.food") == 1, [pt, f])
        await ctx.close()

        # ---- the economy: the welcome gift, a 150-coin theme, the map's next-purchase goal ----
        ctx, page, errs = await fresh(b, mobile=True, init="window.__graspStarter = true; localStorage.setItem('inputPref','mouse');")
        await slice_start(page, True); await slice_end(page)
        ec = await page.evaluate("({ coins: profile.coins, starter: profile.starter, toast: __grasp.toasts.some(x => x.key === 'starterGift'), gym: __grasp.themes.prices.gym })")
        await page.evaluate("__grasp.slice && endCardAction('again', performance.now())"); await slice_end(page)
        c2 = await page.evaluate("profile.coins")
        check('economy: the first finished round brings a welcome gift of 80 coins (once); the first theme costs 150', ec['coins'] >= 80 and ec['starter'] and ec['toast'] and ec['gym'] == 150 and c2 - ec['coins'] < 80, [ec, c2])
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.evaluate("profile.coins = 50; saveProfile(); openAdvMap({ how: 'mouse' })"); await page.wait_for_timeout(400)
        g1 = await page.evaluate("({ hid: $('advGoal').hidden, txt: $('advGoal').textContent, q: __grasp.panelfix.nextPurchase() })")
        await page.evaluate("profile.coins = 85; saveProfile(); renderAdvMap()"); await page.wait_for_timeout(100)
        g2 = await page.evaluate("$('advGoal').textContent")
        check('economy: the map shows the next purchase as a goal ("Cool hands: 30 more"), then "You can buy: Cool hands!"', not g1['hid'] and g1['txt'] == 'Cool hands: 30 more' and g2 == 'You can buy: Cool hands!', [g1, g2])
        await page.screenshot(path='tests/out/fix_map_goal.png')
        check('economy: no page errors', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('ALL PASSED' if check.fails == 0 else f'{check.fails} FAILED'); sys.exit(1 if check.fails else 0)

asyncio.run(main())
