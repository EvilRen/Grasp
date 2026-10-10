exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The pet: the egg on the start screen and its hatch (taps, cracks, the burst, the name sheet), snacks from every finished round (Slice, Strike
# Endless / Adventure incl. a boss stage, Smash stage, Shapes; the bonuses for 3 stars / a boss / a record; the snack box's cap), feeding (food,
# the growth bar, the daily cap of 5, a new day), the stage thresholds and the evolve celebration (rays, size pulses, the banner, confetti, the
# spoken line; quiet when muted / voice off), the mood by date (__grasp.setDate: happy / full / hungry / sleepy, a tap wakes it; never anything
# sad), the wardrobe (unlocks by stage, equip / unequip, locked taps), the end cards' 'Yum! +2 snacks' line (Slice, Adventure, Smash, Shapes;
# phone EN / HE; inside the screen, clear of the card's pills / title / buttons), the profile's validation, the start screen (phone 360x740 and
# desktop 1280x800, EN / HE: no scroll, the corner clear of the tiles / toggle / link / top bar), the loop stopping in a game / a hidden tab.
# Screenshots: tests/out/pet_*.png (each stage, the room EN / HE, the hatch, the evolve, the cards, the start screens).
P = "__grasp.pet"; A = "__grasp.adventure"; S = "__grasp.strike"; SMH = "__grasp.smash"; SMK = "__grasp.sm"
SFX_JS = "(() => { window.__sfx = []; const o = sfx; sfx = (k, a) => { __sfx.push(k); o(k, a); }; })()"
SPEECH = ("window.__spoken = []; try { const ss = { speaking: false, speak(u) { __spoken.push({ text: u.text, lang: u.lang }); setTimeout(() => { try { u.onend && u.onend(); } catch (e) {} }, 300); }, cancel() {}, getVoices() { return [{ lang: 'en-US', name: 'E' }, { lang: 'he-IL', name: 'H' }]; } };"
          " Object.defineProperty(window, 'speechSynthesis', { configurable: true, get: () => ss }); } catch (e) {}")
OUT = 'tests/out/'

def rects_overlap(a, b, pad=0):
    return a['l'] < b['r'] - pad and b['l'] < a['r'] - pad and a['t'] < b['b'] - pad and b['t'] < a['b'] - pad

async def fresh(b, mobile=True, he=False, init='', date='2026-10-02', pet=None, scale=2):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=scale, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    ctx = await b.new_context(**opts); page = await ctx.new_page(); await routes(page); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    seed = ''
    if pet is not None or init:
        prof = {'v': 1, 'coins': 0, 'xp': 0}
        if pet is not None: prof['pet'] = pet
        seed = "if (!sessionStorage.getItem('__seeded')) { localStorage.setItem('grasp.profile', " + json.dumps(json.dumps(prof)) + "); sessionStorage.setItem('__seeded', '1'); }"
    await page.add_init_script(INIT + SPEECH + "localStorage.setItem('lang','" + ('he' if he else 'en') + "');" + ("sessionStorage.setItem('grasp.testDate','" + date + "');" if date else '') + seed + init)
    await page.goto('http://localhost:8765/index.html'); await page.wait_for_function("window.__grasp && __grasp.pet && document.readyState === 'complete'", timeout=10000)
    await page.wait_for_timeout(300); await page.evaluate(SFX_JS)
    return ctx, page, errs

async def tap(page, mobile, sel):
    if mobile: await page.tap(sel)
    else: await page.click(sel)

def hatched(food=0, pantry=0, **kw):
    d = dict(hatched=True, food=food, pantry=pantry, born='2026-10-01', last='2026-10-01', seen=None); d.update(kw)
    if d['seen'] is None: del d['seen']
    return d

LAYOUT = """(() => { const r = (e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }, st = $('start');
  const tiles = [...document.querySelectorAll('.modes > button[data-mode]')].map(r), pc = r($('petCorner'));
  return { pet: pc, cv: r($('petCv')), feed: $('petFeedBtn').hidden ? null : r($('petFeedBtn')), tiles, seg: r(document.querySelector('#start .seg')), link: r(document.querySelector('#start a.link')), row: r(document.querySelector('#start .metaRow')),
    pill: r($('metaPill')), habit: r($('habitBar')), hint: $('flameHint').hidden ? null : r($('flameHint')), W: innerWidth, H: innerHeight,
    noScroll: document.documentElement.scrollHeight <= innerHeight + 1 && st.scrollHeight <= st.clientHeight + 1, noX: document.documentElement.scrollWidth <= innerWidth + 1 && st.scrollWidth <= st.clientWidth + 1,
    name: $('petNm').textContent, line: $('petLine').textContent, st: $('petSt').hidden ? '' : $('petSt').textContent, feedTx: $('petFeedBtn').textContent.trim(), dir: document.documentElement.dir }; })()"""

def card_tag_ok(tag, q, he):
    T = q['tag']; c = q['card']
    if not T: return check(tag + ': the snack line is on the card', False, q)
    tr = {'l': T['x'], 'r': T['x'] + T['w'], 't': T['y'] - 6, 'b': T['y'] + T['h']}  # (the face pokes 6 px above the pill)
    others = [x for x in q['others'] if x]
    check(tag + ': the snack line straddles the card\'s top edge, centred, inside the screen', T['y'] < c['y'] < T['y'] + T['h'] and abs(T['x'] + T['w'] / 2 - (c['x'] + c['w'] / 2)) < 1 and tr['l'] >= 0 and tr['r'] <= q['W'] and tr['t'] >= 0, [T, c])
    check(tag + ': clear of the card\'s title, pills and buttons', not any(rects_overlap(tr, {'l': o['x'], 'r': o['x'] + o['w'], 't': o['y'], 'b': o['y'] + o['h']}, 1) for o in others), [T, others])
    return True

CARD = """((E) => { const u = E.ui; const bs = u.buttons ? Object.values(u.buttons) : [], shared = E !== __grasp.smash && !(E === __grasp.strike && __grasp.adventure.on); // (the shared round-over card's title / pills; the stage cards draw theirs inside, under the title)
  return { tag: u.petTag, card: u.card, W: innerWidth, H: innerHeight, others: [...(shared ? [u.titleBox, u.coinBox, u.xpBox, u.streakChip] : []), ...bs] }; })"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the egg and the hatch (phone EN), the name sheet ----
        ctx, page, errs = await fresh(b)
        st = await page.evaluate(P + ".state")
        check('a new player: an egg (stage 0), nothing in the snack box, nothing eaten', not st['hatched'] and st['stage'] == 0 and st['pantry'] == 0 and st['mood'] == 'egg' and st['canFeed'] == 'egg', st)
        L = await page.evaluate(LAYOUT)
        check('the corner: "Mystery egg", "Tap the egg to hatch it!", no Feed button / stage chip', L['name'] == 'Mystery egg' and L['line'] == 'Tap the egg to hatch it!' and L['feed'] is None and L['st'] == '', L)
        await page.wait_for_function(P + ".frames > 5 && " + P + ".running", timeout=5000)
        await page.screenshot(path=OUT + 'pet_egg_phone_en.png')
        for i in range(4): await tap(page, True, '#petPetBtn'); await page.wait_for_timeout(80)
        st = await page.evaluate(P + ".state"); L = await page.evaluate(LAYOUT)
        check('4 taps: 4 cracks, still an egg; "One more tap!"', st['cracks'] == 4 and not st['hatched'] and L['line'] == 'One more tap!', [st['cracks'], L['line']])
        check('each tap: the egg crack sound', (await page.evaluate("__sfx.filter(k => k === 'eggTap').length")) == 4)
        await page.screenshot(path=OUT + 'pet_egg_cracked.png')
        await tap(page, True, '#petPetBtn')
        st = await page.evaluate(P + ".state")
        check('the 5th tap hatches it: a Baby, born today, its default name (Bubu)', st['hatched'] and st['stage'] == 1 and st['stageId'] == 'baby' and st['food'] == 0 and st['shownName'] == 'Bubu' and await page.evaluate(P + ".p.born") == '2026-10-02', st)
        check('the hatch: its sound, the bubble "Hello! I\'m Bubu!", the spoken "Hello!"', 'hatch' in await page.evaluate("__sfx") and await page.evaluate("$('petBub').textContent") == "Hello! I'm Bubu!" and any(s['text'] == 'Hello!' for s in await page.evaluate("__spoken")), await page.evaluate("__spoken"))
        await page.wait_for_timeout(350); await page.screenshot(path=OUT + 'pet_hatch.png')
        await page.wait_for_function(P + ".state.nameOpen", timeout=4000)
        check('then the name sheet (optional; the default as its placeholder)', await page.evaluate("$('petNameIn').placeholder") == 'Bubu')
        await page.screenshot(path=OUT + 'pet_name_en.png')
        await page.fill('#petNameIn', '  Pip<3!! ')
        await tap(page, True, '#petNameGo')
        st = await page.evaluate(P + ".state")
        check('a name typed (cleaned: letters / digits only): "Pip3"; shown in the corner', st['name'] == 'Pip3' and (await page.evaluate(LAYOUT))['name'] == 'Pip3' and not st['nameOpen'], st)
        L = await page.evaluate(LAYOUT)
        check('after the hatch: the stage chip "Baby", hungry ("Play a game for snacks!" with an empty box), Feed shows 0 / "No snacks"', L['st'] == 'Baby' and L['line'] == 'Play a game for snacks!' and L['feed'] and await page.evaluate("$('petFeedBtn').disabled") and await page.evaluate("$('petFeedBtn').dataset.why") == 'empty', L)
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.pet", timeout=8000)
        st = await page.evaluate(P + ".state")
        check('it survives a reload (hatched, its name)', st['hatched'] and st['name'] == 'Pip3', st)
        await page.evaluate("__grasp.pet.askName()"); await page.fill('#petNameIn', 'Bubu'); await page.press('#petNameIn', 'Enter')
        check('renamed to the default word: stored as "" (so it follows the language)', await page.evaluate(P + ".p.name") == '' and await page.evaluate(P + ".state.shownName") == 'Bubu')
        await page.evaluate(SFX_JS); await tap(page, True, '#petPetBtn')
        check('a tap on the pet: a giggle, a wiggle, "Hee hee!"', 'giggle' in await page.evaluate("__sfx") and await page.evaluate("$('petBub').textContent") == 'Hee hee!' and await page.evaluate("performance.now() - __grasp.pet.ui.wigAt < 1000"))
        check('no page errors (hatch)', not errs, errs); await ctx.close()

        # ---- snacks from real rounds: Slice, Endless, Adventure (a 3-star clear, a boss stage), a fail; the bonuses; the box's cap ----
        ctx, page, errs = await fresh(b, mobile=True, pet=hatched(), init="")
        await page.evaluate("profile.adv.unlocked = 8; saveProfile(); setInputPref('mouse')")
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && __grasp.slice.ui.buttons", timeout=5000)
        e = await page.evaluate(P + ".earnLast")
        check('a Slice round (no record): 1 snack', e and e['n'] == 1 and e['got'] == 1 and await page.evaluate(P + ".p.pantry") == 1, e)
        await page.wait_for_function("performance.now() - __grasp.slice.overAt > 900 && __grasp.slice.ui.petTag", timeout=4000)
        q = await page.evaluate(CARD + "(__grasp.slice)")
        check('Slice card: "Yum! +1 snack"', q['tag']['text'] == 'Yum! +1 snack', q['tag'])
        card_tag_ok('Slice card (phone EN)', q, False)
        await page.wait_for_timeout(500); await page.screenshot(path=OUT + 'pet_card_slice_en.png')
        await page.evaluate("goHome()"); await page.wait_for_timeout(150)
        check('back home: the box shows 1 on the Feed button', '1' in (await page.evaluate(LAYOUT))['feedTx'])
        # Adventure stage 1, cleared without losing a heart: 3 stars -> 2 snacks
        await page.evaluate(f"{A}.start(1, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 1 && {A}.phase === 'play' && !{S}.over", timeout=8000)
        await page.evaluate(f"{A}.finishTest(0)")
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.buttons && {S}.ui.buttons.next && {S}.ui.petTag && performance.now() - {S}.overAt > 900", timeout=12000)
        e = await page.evaluate(P + ".earnLast")
        check('an Adventure 3-star clear: 1 + 1 (stars) = 2 snacks', e['n'] == 2 and e['why']['star'] and not e['why']['boss'], e)
        q = await page.evaluate(CARD + "(__grasp.strike)")
        check('Adventure card: "Yum! +2 snacks"', q['tag']['text'] == 'Yum! +2 snacks', q['tag'])
        card_tag_ok('Adventure clear card (phone EN)', q, False)
        await page.wait_for_timeout(700); await page.screenshot(path=OUT + 'pet_card_adv_en.png')
        # a fail: still 1
        await page.evaluate("goHome()"); await page.wait_for_timeout(150)
        await page.evaluate(f"{A}.start(2, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 2 && {A}.phase === 'play' && !{S}.over", timeout=8000)
        await page.evaluate(f"{A}.failTest()"); await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.petTag && performance.now() - {S}.overAt > 900", timeout=10000)
        e = await page.evaluate(P + ".earnLast")
        check('a failed stage still gives 1 snack (never punishing)', e['n'] == 1 and not any(e['why'].values()), e)
        await page.wait_for_function(f"performance.now() - {S}.overAt > 1200", timeout=5000)
        q = await page.evaluate(CARD + "(__grasp.strike)"); card_tag_ok('Adventure fail card (phone EN)', q, False)
        await page.screenshot(path=OUT + 'pet_card_adv_fail_en.png')
        # the boss stage 8, cleared with 1 heart lost: boss -> 2
        await page.evaluate("goHome()"); await page.wait_for_timeout(150)
        await page.evaluate(f"{A}.start(8, 'mouse')"); await page.wait_for_function(f"{A}.on && {A}.stage === 8 && {A}.phase === 'play' && !{S}.over", timeout=8000)
        await page.evaluate(f"{A}.finishTest(1)")
        await page.wait_for_function(f"{S}.over && {A}.phase === 'card' && {S}.ui.petTag && performance.now() - {S}.overAt > 900", timeout=20000)
        e = await page.evaluate(P + ".earnLast")
        check('a boss stage (2 stars): 1 + 1 (boss) = 2 snacks', e['n'] == 2 and e['why']['boss'] and not e['why']['star'], e)
        # Endless: a round over
        await page.evaluate("goHome()"); await page.wait_for_timeout(150)
        await page.evaluate(f"{A}.endless('mouse')"); await page.wait_for_function(f"mode === 'mouse' && !{A}.on && !{S}.over", timeout=8000)
        await page.evaluate(f"(() => {{ const s = {S}; s.lives = 1; s.setBallZ(-500); }})()")
        await page.wait_for_function(f"{S}.over && {S}.ui.buttons && {S}.ui.buttons.again && {S}.ui.petTag && performance.now() - {S}.overAt > 900", timeout=12000)
        e = await page.evaluate(P + ".earnLast")
        check('an Endless round: 1 snack', e['n'] == 1, e)
        q = await page.evaluate(CARD + "(__grasp.strike)"); card_tag_ok('Endless card (phone EN)', q, False)
        check('the box: 1 + 2 + 1 + 2 + 1 = 7, all counted as earned', await page.evaluate(P + ".p.pantry") == 7 and await page.evaluate(P + ".p.earned") == 7, await page.evaluate(P + ".p"))
        # the bonus rule and the cap
        r = await page.evaluate(f"[{P}.earn({{}}).n, {P}.earn({{ boss: true }}).n, {P}.earn({{ star: true, record: true }}).n, {P}.earn({{ star: true, boss: true, record: true }}).n]")
        check('the rule: 1, +1 boss, +1 star +1 record, all three capped at 3', r == [1, 2, 3, 3], r)
        await page.evaluate(f"{P}.set({{ pantry: 29 }})"); e1 = await page.evaluate(f"{P}.earn({{ star: true }})"); e2 = await page.evaluate(f"{P}.earn({{}})")
        check('the snack box holds 30: 29 + 2 = 30 (got 1), then nothing more (got 0)', e1['got'] == 1 and e2['got'] == 0 and await page.evaluate(P + ".p.pantry") == 30, [e1, e2])
        await page.evaluate("goHome()"); await page.wait_for_timeout(100)
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && performance.now() - __grasp.slice.overAt > 900 && __grasp.slice.ui.petTag", timeout=5000)
        check('a full box: the card says "Snack box full!"', (await page.evaluate("__grasp.slice.ui.petTag"))['text'] == 'Snack box full!')
        check('coins untouched by snacks (the economy is separate)', await page.evaluate("Object.keys(ECONOMY).every(k => k !== 'pet') && typeof PET.perDay === 'number'"))
        check('no page errors (rounds)', not errs, errs); await ctx.close()

        # ---- Smash stage + Shapes rounds, Hebrew cards (phone HE), an egg's card line ----
        ctx, page, errs = await fresh(b, mobile=True, he=True, pet=hatched())
        await page.evaluate("profile.smash.unlocked = 20; saveProfile(); setInputPref('mouse')")
        await page.evaluate(f"{SMK}.stage(1)"); await page.wait_for_function(f"{SMH}.n === 1 && {SMH}.phase === 'play' && !{SMH}.over && mode === 'mouse'", timeout=10000)
        await page.evaluate(f"{SMH}.banner = null"); await page.evaluate(f"{SMK}.win()")
        await page.wait_for_function(f"{SMH}.over && {SMH}.result && {SMH}.ui.petTag && performance.now() - {SMH}.overAt > 900", timeout=20000)
        e = await page.evaluate(P + ".earnLast"); res = await page.evaluate(f"{SMH}.result")
        check('a Smash stage cleared: 1 + boss (+1 if 3 stars)', e['why']['boss'] and e['n'] == (3 if res['stars'] == 3 else 2), [e, res['stars']])
        q = await page.evaluate(CARD + "(__grasp.smash)")
        check('Smash card (HE): "יאמי! עוד ... חטיפים"', q['tag']['text'] == 'יאמי! עוד %d חטיפים' % e['n'], q['tag'])
        card_tag_ok('Smash card (phone HE)', q, True)
        await page.wait_for_timeout(600); await page.screenshot(path=OUT + 'pet_card_smash_he.png')
        await page.evaluate("goHome()"); await page.wait_for_timeout(150)
        await page.evaluate("__grasp.setGameMode('shapes')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse' && __grasp.shapes.phase === 'play'", timeout=8000)
        await page.wait_for_function("__grasp.shapes.placeTest(0)", timeout=5000); await page.evaluate("__grasp.shapes.finish()"); await page.wait_for_function("__grasp.shapes.over && __grasp.shapes.ui.petTag && performance.now() - shapes.overAt > 900", timeout=8000)
        e = await page.evaluate(P + ".earnLast")
        check('a Shapes round ended (a shape sorted, no level done): 1 snack', e['n'] == 1, e)
        q = await page.evaluate(CARD + "(__grasp.shapes)"); card_tag_ok('Shapes card (phone HE)', q, True)
        check('Shapes card (HE): "יאמי! עוד חטיף"', q['tag']['text'] == 'יאמי! עוד חטיף', q['tag'])
        await page.wait_for_timeout(600); await page.screenshot(path=OUT + 'pet_card_shapes_he.png')
        check('no page errors (smash / shapes HE)', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=True)
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000)
        await page.evaluate("sliceLoseLife(performance.now()); sliceLoseLife(performance.now()); sliceLoseLife(performance.now())")
        await page.wait_for_function("__grasp.slice.over && performance.now() - __grasp.slice.overAt > 900 && __grasp.slice.ui.petTag", timeout=5000)
        T = await page.evaluate("__grasp.slice.ui.petTag")
        check('before the hatch: the card says "+1 snack for your egg" (snacks wait in the box)', T['egg'] and T['text'] == '+1 snack for your egg' and await page.evaluate(P + ".p.pantry") == 1, T)
        await page.wait_for_timeout(500); await page.screenshot(path=OUT + 'pet_card_egg_en.png')
        check('no page errors (egg card)', not errs, errs); await ctx.close()

        # ---- feeding: food, the bar, the daily cap of 5, a new day; the stage thresholds; the evolve celebration ----
        ctx, page, errs = await fresh(b, mobile=True, pet=hatched(food=7, pantry=9))
        th = await page.evaluate(f"[0, 9, 10, 24, 25, 44, 45, 74, 75, 500].map(f => {P}.stageOf(f))")
        check('stages: Baby 0, Kid 10, Teen 25, Grown-up 45, Legend 75', th == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5], th)
        check('the egg is stage 0 whatever the food', await page.evaluate(f"{P}.stageOf(99, false)") == 0)
        st = await page.evaluate(P + ".state")
        check('food 7 (Baby): the bar 70%, 3 more snacks to Kid', st['stage'] == 1 and abs(st['frac'] - 0.7) < 1e-9 and st['left'] == 3, st)
        w0 = await page.evaluate("$('petBar').querySelector('i').style.width")
        await tap(page, True, '#petFeedBtn')
        st = await page.evaluate(P + ".state")
        check('Feed: one snack eaten (box 9 -> 8, food 7 -> 8, today 1/5), happy now', st['pantry'] == 8 and st['food'] == 8 and st['ate'] == 1 and st['mood'] == 'happy', st)
        check('the bar grows (70% -> 80%); the munch sound; "Yum, thank you!"', w0 == '70%' and await page.evaluate("$('petBar').querySelector('i').style.width") == '80%' and await page.evaluate("$('petBub').textContent") == 'Yum, thank you!', w0)
        await page.wait_for_function("__sfx.includes('munch')", timeout=3000)
        await page.wait_for_timeout(1200)
        await tap(page, True, '#petFeedBtn'); await page.wait_for_timeout(200)
        check('food 9: still a Baby', await page.evaluate(P + ".state.stage") == 1)
        await page.wait_for_timeout(1000)
        await tap(page, True, '#petFeedBtn')
        st = await page.evaluate(P + ".state")
        check('food 10: a Kid', st['stage'] == 2 and st['food'] == 10, st)
        await page.wait_for_function(P + ".state.roomOpen && " + P + ".ui.evo", timeout=4000)
        await page.wait_for_timeout(1200); await page.screenshot(path=OUT + 'pet_evolve.png')
        ev = await page.evaluate("({ shown: !$('petEvo').hidden, b: $('petEvo').querySelector('b').textContent, s: $('petEvo').querySelector('small').textContent, cel: __grasp.pet.ui.celebrations, seen: __grasp.pet.p.seen, cf: document.querySelectorAll('#petRoom .cf').length })")
        check('the evolve: the room opens with the celebration ("Bubu is a Kid now!", the new things: Pink, Bow, Scarf), seen = 2', ev['shown'] and ev['b'] == 'Bubu is a Kid now!' and ev['s'] == 'New for Bubu: Pink, Bow, Scarf' and ev['cel'] == 1 and ev['seen'] == 2, ev)
        check('...with the fanfare, confetti and the spoken "Yay! I grew!"', 'fanfare' in await page.evaluate("__sfx") and any(s['text'] == 'Yay! I grew!' for s in await page.evaluate("__spoken")), await page.evaluate("__spoken"))
        await page.wait_for_function("!__grasp.pet.ui.evo", timeout=5000)
        await page.screenshot(path=OUT + 'pet_room_en.png')
        await page.click('#petFeedBig', force=True); await page.wait_for_timeout(300); await page.click('#petFeedBig', force=True); await page.wait_for_timeout(300)
        st = await page.evaluate(P + ".state")
        check('the room\'s Feed twice: the 5th snack today (5/5): full', st['ate'] == 5 and st['mood'] == 'full' and st['canFeed'] == 'full', st)
        rr = await page.evaluate("({ dis: $('petFeedBig').disabled, lb: $('petFeedBig').querySelector('.lb').textContent, slots: document.querySelectorAll('#petTummy .slots i.on').length, tl: document.querySelector('#petTummy .tl').textContent })")
        check('the cap: Feed disabled "Full today", the tummy 5/5', rr['dis'] and rr['lb'] == 'Full today' and rr['slots'] == 5 and rr['tl'] == 'Ate today: 5/5', rr)
        r = await page.evaluate(P + ".feedUi()")
        check('a 6th snack today is refused ("full"): nothing eaten, "So full! See you tomorrow"', not r['ok'] and r['why'] == 'full' and (await page.evaluate(P + ".state"))['food'] == 12 and await page.evaluate("$('petRoomBub').textContent") == 'So full! See you tomorrow', r)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
        check('Escape closes the room', not await page.evaluate(P + ".state.roomOpen"))
        await page.evaluate("__grasp.setDate('2026-10-03')"); st = await page.evaluate(P + ".state")
        check('the next day: hungry again, 0/5 eaten, it can eat', st['mood'] == 'hungry' and st['ate'] == 0 and st['canFeed'] == 'ok', st)
        check('...and the corner says so ("Snack time?"), Feed ready', (await page.evaluate(LAYOUT))['line'] == 'Snack time?' and await page.evaluate("$('petFeedBtn').classList.contains('ready')"))
        await page.evaluate(f"{P}.set({{ pantry: 0 }})"); r = await page.evaluate(P + ".feed()")
        check('an empty box: nothing to eat ("empty")', not r['ok'] and r['why'] == 'empty', r)
        # muted: the celebration is silent
        await page.evaluate(f"__grasp.muted = true; {P}.set({{ pantry: 3, food: 24, seen: 2 }}); window.__spoken.length = 0")
        r = await page.evaluate(P + ".feed()"); await page.evaluate(f"{P}.evolve({r['from']}, {r['evolved']})")
        check('muted: the evolve says nothing (skipped: muted)', r['evolved'] == 3 and not await page.evaluate("__spoken.length") and (await page.evaluate(P + ".skipped"))[-1]['why'] == 'muted', r)
        await page.evaluate(f"__grasp.muted = false; profile.grippy = false; {P}.set({{ food: 44, seen: 3 }})")
        r = await page.evaluate(P + ".feed()"); await page.evaluate(f"{P}.evolve({r['from']}, {r['evolved']})")
        check('the voice off (Collection): silent too', r['evolved'] == 4 and not await page.evaluate("__spoken.length") and (await page.evaluate(P + ".skipped"))[-1]['why'] == 'off', r)
        check('no page errors (feeding)', not errs, errs); await ctx.close()

        # ---- the mood by date (hatched on 10-02) ----
        ctx, page, errs = await fresh(b, mobile=True, pet=dict(hatched=True, food=3, pantry=10, born='2026-10-02', last='2026-10-02'))
        moods = {}
        moods['hatch day, not fed'] = await page.evaluate(P + ".mood()")
        await page.evaluate(P + ".feed()"); moods['fed once'] = await page.evaluate(P + ".mood()")
        for _ in range(4): await page.evaluate(P + ".feed()")
        moods['fed 5'] = await page.evaluate(P + ".mood()")
        moods['next day'] = await page.evaluate(P + ".mood('2026-10-03')")
        moods['2 days away'] = await page.evaluate(P + ".mood('2026-10-04')")
        moods['a week away'] = await page.evaluate(P + ".mood('2026-10-09')")
        moods['clock back'] = await page.evaluate(P + ".mood('2026-09-20')")
        check('moods: hungry (hatch day) -> happy (fed) -> full (5) -> hungry (next day) -> sleepy (2+ days) ; a clock gone back: hungry',
              moods == {'hatch day, not fed': 'hungry', 'fed once': 'happy', 'fed 5': 'full', 'next day': 'hungry', '2 days away': 'sleepy', 'a week away': 'sleepy', 'clock back': 'hungry'}, moods)
        await page.evaluate("__grasp.setDate('2026-10-09')"); await page.wait_for_timeout(200)
        L = await page.evaluate(LAYOUT); st = await page.evaluate(P + ".state")
        check('a week away: sleepy ("Zzz… tap to wake me"), never lost a thing (food, box, stage kept)', st['mood'] == 'sleepy' and L['line'] == 'Zzz… tap to wake me' and st['food'] == 8 and st['pantry'] == 5 and st['stage'] == 1, [st, L['line']])
        await page.screenshot(path=OUT + 'pet_sleepy.png')
        await tap(page, True, '#petPetBtn'); st = await page.evaluate(P + ".state")
        check('a tap wakes it (shown hungry: "Snack time?"; the date mood stays sleepy until it eats)', st['shown'] == 'hungry' and st['mood'] == 'sleepy' and (await page.evaluate(LAYOUT))['line'] == 'Snack time?', st)
        await page.evaluate(P + ".feedUi()"); check('fed: happy', await page.evaluate(P + ".state.mood") == 'happy')
        allm = await page.evaluate("Object.keys(I18N.en).filter(k => k.startsWith('petM_'))")
        check('no sad mood exists (only happy / full / hungry / sleepy / giggle / egg lines)', sorted(allm) == sorted(['petM_happy', 'petM_full', 'petM_hungry', 'petM_hungryNo', 'petM_sleepy', 'petM_giggle', 'petM_egg']), allm)
        check('no page errors (mood)', not errs, errs); await ctx.close()

        # ---- the wardrobe: unlocks by stage, equip / unequip, a locked tap ----
        ctx, page, errs = await fresh(b, mobile=True, pet=hatched(food=0))
        r = await page.evaluate(f"[{P}.equip('head', 'bow'), {P}.equip('color', 'pink'), {P}.equip('color', 'sky'), {P}.equip('eyes', 'glasses'), {P}.equip('head', 'nope'), {P}.equip('tail', 'bow')]")
        check('a Baby: only Mint / Sky; no accessories yet', r == [False, False, True, False, False, False] and await page.evaluate(P + ".p.color") == 'sky', r)
        check('the unlocks by stage', await page.evaluate(f"[2, 3, 4, 5].map(s => {P}.unlocks(s).join(','))") == ['Pink,Bow,Scarf', 'Sunny,Glasses,Cap', 'Lilac,Bow tie', 'Gold,Crown'])
        await page.evaluate(f"{P}.set({{ food: 10, seen: 2 }})"); await page.evaluate(P + ".open(true)"); await page.wait_for_timeout(300)
        await page.click('#petItems .pitem[data-id=bow]')
        w = await page.evaluate("({ head: __grasp.pet.p.head, pressed: document.querySelector('#petItems .pitem[data-id=bow]').getAttribute('aria-pressed') })")
        check('a Kid: tap Bow = worn (pressed)', w == {'head': 'bow', 'pressed': 'true'}, w)
        await page.click('#petItems .pitem[data-id=scarf]'); await page.click('#petCols .pcol[data-id=pink]')
        check('Scarf + Pink too (one per slot)', await page.evaluate("[__grasp.pet.p.head, __grasp.pet.p.neck, __grasp.pet.p.color]") == ['bow', 'scarf', 'pink'])
        await page.evaluate(SFX_JS); await page.click('#petItems .pitem[data-id=glasses]')
        check('a locked item (Glasses: Teen): not worn, a whiff, "Grows into a Teen first"', await page.evaluate(P + ".p.eyes") == '' and 'whiff' in await page.evaluate("__sfx") and await page.evaluate("$('petRoomBub').textContent") == 'Grows into a Teen first')
        await page.click('#petItems .pitem[data-id=bow]')
        check('Bow again = off', await page.evaluate(P + ".p.head") == '')
        await page.evaluate(f"{P}.set({{ food: 80, seen: 5 }})"); await page.evaluate(f"{P}.equip('head', 'crown'); {P}.equip('eyes', 'glasses'); {P}.equip('color', 'gold')")
        check('a Legend wears the Crown, Glasses, Gold', await page.evaluate("[__grasp.pet.p.head, __grasp.pet.p.eyes, __grasp.pet.p.color]") == ['crown', 'glasses', 'gold'])
        await page.reload(); await page.wait_for_function("window.__grasp && __grasp.pet", timeout=8000)
        check('the wardrobe survives a reload', await page.evaluate("[__grasp.pet.p.head, __grasp.pet.p.eyes, __grasp.pet.p.neck, __grasp.pet.p.color]") == ['crown', 'glasses', 'scarf', 'gold'])
        check('no page errors (wardrobe)', not errs, errs); await ctx.close()

        # ---- each stage in its room (screenshots), the room in Hebrew ----
        looks = [('egg', None), ('baby', dict(food=2, color='mint')), ('kid', dict(food=12, color='pink', head='bow')), ('teen', dict(food=30, color='sky', eyes='glasses', neck='scarf')),
                 ('grown', dict(food=50, color='lilac', head='cap', neck='bowtie')), ('legend', dict(food=90, color='gold', head='crown'))]
        for name, kw in looks:
            pet = None if kw is None else dict(hatched(**kw), seen=5)
            ctx, page, errs = await fresh(b, mobile=True, pet=pet)
            await page.evaluate(P + ".open(true)"); await page.wait_for_function(P + ".state.roomOpen", timeout=3000); await page.wait_for_timeout(700)
            st = await page.evaluate(P + ".state")
            px = await page.evaluate("(() => { const c = $('petRoomCv'), g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 16) if (d[i] > 200) n++; return n * 4 / (c.width * c.height); })()")
            check('room: the %s drawn (stage %s, %.0f%% of the scene painted)' % (name, st['stageId'], px * 100), st['stageId'] == name and px > 0.03, px)
            await page.screenshot(path=OUT + 'pet_stage_' + name + '.png')
            check('no page errors (stage %s)' % name, not errs, errs); await ctx.close()
        sizes = {}
        ctx, page, errs = await fresh(b, mobile=True, pet=hatched(food=0))
        for f in (0, 10, 25, 45, 75):
            await page.evaluate(f"{P}.set({{ food: {f}, seen: 5 }})"); sizes[f] = await page.evaluate("(() => { const c = $('petCv'); const g = c.getContext('2d'); __grasp.pet.ui.hopAt = -1e9; __grasp.pet.ui.hopNext = 1e12; return 0; })()")
            await page.wait_for_timeout(250)
            sizes[f] = await page.evaluate("(() => { const c = $('petCv'), g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 200) n++; return n; })()")
        v = [sizes[f] for f in (0, 10, 25, 45, 75)]
        check('each stage is visibly bigger in the corner (painted pixels grow)', all(v[i] < v[i + 1] for i in range(4)), v)
        check('no page errors (sizes)', not errs, errs); await ctx.close()
        ctx, page, errs = await fresh(b, mobile=True, he=True, pet=hatched(food=30, pantry=6, color='sky', eyes='glasses', neck='scarf', seen=3))
        await page.evaluate(P + ".open(true)"); await page.wait_for_timeout(600)
        R = await page.evaluate("(() => { const s = $('petRoom').querySelector('.sheet').getBoundingClientRect(); return { title: $('petRoomT').textContent, steps: [...document.querySelectorAll('#petSteps li span')].map(x => x.textContent), grow: $('petGrowLine').textContent, feed: $('petFeedBig').textContent.trim(), inside: s.left >= 0 && s.right <= innerWidth + 0.5 && s.top >= 0 && s.bottom <= innerHeight + 0.5, noX: document.documentElement.scrollWidth <= innerWidth + 1, dir: document.documentElement.dir, now: document.querySelector('#petSteps li.now span').textContent }; })()")
        check('room HE: the name + stage, the steps, "עוד 15 חטיפים עד בוגר", RTL, inside the phone', R['title'] == 'בובונער' and R['steps'] == ['תינוק', 'ילד', 'נער', 'בוגר', 'אגדה'] and R['grow'] == 'עוד 15 חטיפים עד בוגר' and R['now'] == 'נער' and R['inside'] and R['noX'] and R['dir'] == 'rtl', R)
        await page.screenshot(path=OUT + 'pet_room_he.png')
        check('no page errors (room HE)', not errs, errs); await ctx.close()

        # ---- the profile's validation ----
        ctx, page, errs = await fresh(b, mobile=False, pet={'hatched': 'yes', 'name': 'Rex<script>alert(1)</script>', 'food': -5, 'pantry': 999, 'ate': {'date': 'bad', 'n': 50}, 'color': 'gold', 'head': 'crown', 'eyes': 'laser', 'neck': 'scarf', 'seen': 9, 'earned': -3})
        v = await page.evaluate(P + ".p")
        check('a broken pet: not hatched (only true counts), name cleaned + cut to 12, box capped at 30, food 0, locked / unknown looks dropped, seen 0',
              v['hatched'] is False and v['name'] == 'Rexscriptale' and v['pantry'] == 30 and v['food'] == 0 and v['color'] == 'mint' and v['head'] == '' and v['eyes'] == '' and v['neck'] == '' and v['seen'] == 0 and v['earned'] == 0 and v['ate'] == {'date': '', 'n': 0}, v)
        cases = await page.evaluate(f"""[{P}.validate('junk'), {P}.validate(null), {P}.validate([1]),
          {P}.validate({{ hatched: true, food: 50.7, pantry: 3.7, color: 'lilac', head: 'cap', eyes: 'glasses', neck: 'bowtie', ate: {{ date: '2026-10-01', n: 9 }}, last: '2026-10-01', born: 'x', seen: 2 }}),
          {P}.validate({{ hatched: true, food: 12, color: 'sun', head: 'eyes', neck: 'glasses', ate: {{ date: '2026-10-01', n: -2 }} }})]""")
        check('junk / null / an array: the default pet', all(c == cases[0] for c in cases[:3]) and cases[0]['hatched'] is False and cases[0]['pantry'] == 0)
        g = cases[3]
        check('a good Grown-up kept (food 50, box 3, lilac + cap + glasses + bow tie, today\'s count capped at 5, a bad born date dropped, seen 2)',
              g['hatched'] and g['food'] == 50 and g['pantry'] == 3 and g['color'] == 'lilac' and g['head'] == 'cap' and g['eyes'] == 'glasses' and g['neck'] == 'bowtie' and g['ate'] == {'date': '2026-10-01', 'n': 5} and g['last'] == '2026-10-01' and g['born'] == '' and g['seen'] == 2, g)
        h = cases[4]
        check('a Kid: Sunny (a Teen colour) back to mint, items in the wrong slot dropped, a negative count = 0', h['color'] == 'mint' and h['head'] == '' and h['neck'] == '' and h['ate']['n'] == 0 and h['seen'] == 2, h)
        check('no page errors (validation)', not errs, errs); await ctx.close()

        # ---- the start screen: phone + desktop, EN / HE, the egg and a hatched pet with the flame hint: no scroll, no overlap ----
        for mobile in (True, False):
            for he in (False, True):
                for kind in ('egg', 'pet'):
                    tag = ('phone ' if mobile else 'desktop ') + ('he ' if he else 'en ') + kind
                    pet = None if kind == 'egg' else hatched(food=30, pantry=4, color='pink', neck='scarf', seen=3)
                    init = '' if kind == 'egg' else "localStorage.setItem('grasp.profile', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('grasp.profile')), { habit: { play: ['2026-09-30', '2026-10-01'] } })));"
                    ctx, page, errs = await fresh(b, mobile, he, pet=pet if pet else ({} if kind == 'egg' else None), init=init)
                    await page.wait_for_timeout(1300)
                    L = await page.evaluate(LAYOUT)
                    blocks = L['tiles'] + [L['seg'], L['link'], L['row'], L['pill'], L['habit']] + ([L['hint']] if L['hint'] else [])
                    check(tag + ': no scrolling (either way); the pet corner fully on screen', L['noScroll'] and L['noX'] and L['pet']['l'] >= 0 and L['pet']['r'] <= L['W'] + 0.5 and L['pet']['t'] >= 0 and L['pet']['b'] <= L['H'], L)
                    check(tag + ': the corner overlaps nothing (tiles, toggle, link, icon row, pill, top bar' + (', flame hint' if L['hint'] else '') + ')', not any(rects_overlap(L['pet'], x, 1) for x in blocks), [L['pet'], blocks])
                    check(tag + ': under the Camera | Touch toggle, above the Tremorti link; as wide as the tiles\' grid', L['pet']['t'] >= L['seg']['b'] and L['pet']['b'] <= L['link']['t'] and abs(L['pet']['w'] - L['seg']['w']) < 2, [L['pet'], L['seg']])
                    pet_end = L['cv']['l'] > L['pet']['l'] + L['pet']['w'] / 2
                    check(tag + ': the pet at the start side (' + ('right' if he else 'left') + ')', pet_end == he, L['cv'])
                    if kind == 'pet':
                        check(tag + ': name, stage, mood line, Feed (4) shown in ' + ('HE' if he else 'EN'), L['name'] == ('בובו' if he else 'Bubu') and L['st'] == ('נער' if he else 'Teen') and L['line'] == ('זמן לחטיף?' if he else 'Snack time?') and '4' in L['feedTx'] and L['hint'] is not None, L)
                        check(tag + ': Feed inside the corner, a big target (>= 60 x 70)', L['feed']['w'] >= 60 and L['feed']['h'] >= 70 and L['feed']['l'] >= L['pet']['l'] and L['feed']['r'] <= L['pet']['r'], L['feed'])
                    await page.screenshot(path=OUT + 'pet_start_%s_%s_%s.png' % ('phone' if mobile else 'desktop', 'he' if he else 'en', kind))
                    check(tag + ': no page errors', not errs, errs); await ctx.close()

        # ---- the loop: runs on the start screen, stops in a game and in a hidden tab ----
        ctx, page, errs = await fresh(b, mobile=False, pet=hatched(food=3))
        await page.wait_for_function(P + ".running", timeout=3000); f0 = await page.evaluate(P + ".frames"); await page.wait_for_timeout(400); f1 = await page.evaluate(P + ".frames")
        check('the start screen: the pet animates (~30 fps, not more)', 6 <= f1 - f0 <= 16, f1 - f0)
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=5000); await page.wait_for_timeout(150)
        f2 = await page.evaluate(P + ".frames"); await page.wait_for_timeout(300)
        check('in a game: the pet loop stops', not await page.evaluate(P + ".running") and await page.evaluate(P + ".frames") == f2)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        check('home: it runs again', await page.evaluate(P + ".running"))
        await page.evaluate("Object.defineProperty(document, 'hidden', { get: () => true, configurable: true }); document.dispatchEvent(new Event('visibilitychange'))"); await page.wait_for_timeout(200)
        f3 = await page.evaluate(P + ".frames"); await page.wait_for_timeout(300)
        check('a hidden tab: it stops', await page.evaluate(P + ".frames") == f3 and not await page.evaluate(P + ".running"))
        check('no page errors (loop)', not errs, errs); await ctx.close()
        await b.close()
    print('FAILURES:', check.fails)
asyncio.run(main()); srv.terminate()
if check.fails: sys.exit(1)
