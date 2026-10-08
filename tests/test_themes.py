# Strike themes (parent: "different themes for the breaking ball game like gym, basketball court, baseball"): a Themes section in the Shop
# (Classic owned + Gym 300 / Basketball court 400 / Baseball 500), buy once then equip, saved in the profile (validated on load), applied in
# Adventure, Endless, Frenzy and the daily. Covers: the Shop's cards (pictures, prices, buy deducts once, not enough coins, equip / persist),
# the profile's validation; each theme's arena in 2D (pixel checks of its floor and walls: maple, parquet, grass; per-world time of day; one
# cached background) and in 3D (its own surface pictures, pixels); the themed bricks with the special bricks still standing out (pixels,
# 2D and 3D); the theme ball (2D sprite pixels, the 3D ball's skin); the themed sounds (stubbed sfx: whistle, buzzer, sneaker, bat crack,
# organ, cheer, 'oooh'; rendered offline: audible, under the peak, silent when muted); the music variation; the mascot guests (art, bubble
# line, sound; EN / HE); the map footer's Theme chip opening the Shop's Themes section over the map; the daily / Frenzy / Endless use it.
# Screenshots: tests/out/theme_{gym,basketball,baseball}_{phone,desktop,3d}.png, theme_shop_{en,he}.png, theme_map_chip.png.
exec(open('tests/test_challenge.py').read().split('async def main')[0])
from io import BytesIO
from PIL import Image
TH = "__grasp.themes"; G3D = "{ pr: 0.5, shadows: false, auto: false }"
NAMES = {'gym': 'gym', 'court': 'basketball', 'baseball': 'baseball'}

def prof(th='classic', owned=None, coins=0, extra=''):
    owned = owned or ['classic', th]
    return "if (!localStorage.getItem('grasp.profile')) localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: %d, themes: %s, theme: '%s'%s }));" % (coins, json.dumps(owned), th, extra)

async def shot(page):
    return Image.open(BytesIO(await page.screenshot(scale='css'))).convert('RGB')

def mean(img, x0, y0, x1, y1):
    x0, y0, x1, y1 = [int(round(v)) for v in (x0, y0, x1, y1)]
    px = [img.getpixel((x, y)) for x in range(max(0, x0), min(img.width, x1)) for y in range(max(0, y0), min(img.height, y1))]
    n = max(1, len(px)); return tuple(round(sum(p[i] for p in px) / n) for i in range(3))

def dist(a, b): return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5
def grid(img, box, nx=10, ny=6):  # a box's pixels on a coarse grid (the brick's picture, not just its mean colour)
    x0, y0, x1, y1 = box; return [img.getpixel((min(img.width - 1, max(0, int(x0 + (x1 - x0) * (i + 0.5) / nx))), min(img.height - 1, max(0, int(y0 + (y1 - y0) * (j + 0.5) / ny))))) for j in range(ny) for i in range(nx)]
def gdist(a, b): return sum(dist(p, q) for p, q in zip(a, b)) / len(a)

def floor_ok(th, c):  # the floor's distinctive colour
    r, g, b = c
    if th == 'gym': return r > 110 and r > g > b and r - b > 40  # maple
    if th == 'court': return r > 95 and r > g * 1.25 and g > b and b < 110  # orange-brown parquet
    if th == 'baseball': return g > r + 25 and g > b + 20  # grass
    return b > r  # the classic corridor: blue-ish

async def to_stage(page, n=1):
    await stage(page, n)
    await page.evaluate(f"{S}.guestEvery = 0; __grasp.CONFIG.STRIKE_PU_RATE = 0; park(2300); hideHint()")

async def floor_px(page, img):  # the near floor's mean colour (css px), clear of the ball's shadow and the hint
    box = await page.evaluate("(() => { const c = corridor(), a = proj(c.L + (c.R - c.L) * 0.28, c.B, 20), b = proj(c.L + (c.R - c.L) * 0.38, c.B, 90); return [a.x, b.y, b.x, a.y]; })()")
    x0, y0, x1, y1 = box; y1 = min(y1, img.height - 2)
    return mean(img, x0 + 2, max(y0, y1 - 18), x1 - 2, y1)

SPECIAL_WALL = """(() => { const s = __grasp.strike; s.walls.length = 0; const w = s.spawnWall('brick', 260); for (const k of w.bricks) { k.weak = k.key = k.gold = k.turret = k.armor = false; k.pu = null; k.hp = k.max = 1; k.tnt = false; k.hole = false; k.alive = true; }
  const set = [['armor', 0, 0], ['weak', 1, 0], ['key', 2, 1], ['gold', 0, 2], ['turret', 1, 2]], out = [];
  for (const [t, c, r] of set) { const k = w.bricks.find(q => q.col === c && q.row === r); if (!k) continue; if (t === 'armor') { k.armor = true; k.hp = k.max = 3; } else k[t] = true; }
  const cell = (c, r) => { const b = brickCell(w, c, r), a = proj(b.x - b.w * 0.3, b.y - b.h * 0.3, w.z), z = proj(b.x + b.w * 0.3, b.y + b.h * 0.3, w.z); return [a.x, a.y, z.x, z.y]; };
  const plain = w.bricks.filter(q => !brickSpecial(q)).map(q => ({ c: q.col, r: q.row, box: cell(q.col, q.row) }));
  return { specials: set.map(([t, c, r]) => ({ t, box: cell(c, r) })), plain, look: wallLv(w) }; })()"""

async def specials_check(page, tag):
    sp = await page.evaluate(SPECIAL_WALL)
    await page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 120))))")
    img = await shot(page)
    plain = [grid(img, q['box']) for q in sp['plain']]
    ds = {q['t']: round(min(gdist(grid(img, q['box']), p) for p in plain)) for q in sp['specials']}
    check(f'{tag}: every special brick (armor, weak spot, keystone, gold, turret) stands out from every themed plain brick (pixel by pixel on a 10 x 6 grid: mean colour distance >= 55)', all(d >= 55 for d in ds.values()) and len(ds) == 5, ds)
    return img

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ===== T1: the Shop's Themes section: cards, prices, buy once, equip, persist =====
        ctx, page, errs = await fresh(b, init=prof('classic', ['classic'], 350))
        await page.evaluate("openPanel('collection')"); await page.wait_for_timeout(300)
        cards = await page.evaluate("[...document.querySelectorAll('#thms .thm')].map(e => ({ id: e.dataset.id, st: e.dataset.st, nm: e.querySelector('.nm').textContent, pr: e.querySelector('.st').textContent, lock: !!e.querySelector('.lk'), pic: (() => { const c = e.querySelector('canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 40) if (d[i] > 200) n++; return n; })() }))")
        check('the Shop has a Themes section with 4 cards: Classic, Gym, Basketball court, Baseball', [c['id'] for c in cards] == ['classic', 'gym', 'court', 'baseball'] and [c['nm'] for c in cards] == ['Classic', 'Gym', 'Basketball court', 'Baseball'], cards)
        check('prices on the scarce economy: Gym 300, Basketball court 400, Baseball 500 (locked, a lock icon); Classic owned and equipped', [c['pr'] for c in cards[1:]] == ['300', '400', '500'] and all(c['lock'] for c in cards[1:]) and cards[0]['st'] == 'equipped' and await page.evaluate(f"{TH}.prices.gym === 300 && {TH}.prices.court === 400 && {TH}.prices.baseball === 500"), cards)
        check('every card has a picture of its arena (drawn, not empty)', all(c['pic'] > 2000 for c in cards), [c['pic'] for c in cards])
        th_y = await page.evaluate("[document.querySelector('#cpower').getBoundingClientRect().top, document.querySelector('#cthemes').getBoundingClientRect().top, document.querySelector('#ctypes').getBoundingClientRect().top]")
        check('the Themes section sits after Power (forever), before the looks', th_y[0] < th_y[1] < th_y[2], th_y)
        await page.click('#thms .thm[data-id=gym]'); await page.wait_for_timeout(250)
        st = await page.evaluate(f"({{ coins: profile.coins, owned: {TH}.owned, now: {TH}.now, st: document.querySelector('#thms .thm[data-id=gym]').dataset.st, toast: meta.toasts.map(t => t.text).slice(-2) }})")
        check('buying Gym: 300 coins off once, owned and worn at once (Equipped), a toast', st['coins'] == 50 and 'gym' in st['owned'] and st['now'] == 'gym' and st['st'] == 'equipped', st)
        again = await page.evaluate(f"(() => {{ const r = {TH}.buy('gym'); return {{ r, coins: profile.coins }}; }})()")
        check('buying it again does nothing (no second charge)', again == {'r': False, 'coins': 50}, again)
        await page.click('#thms .thm[data-id=court]'); await page.wait_for_timeout(200)
        poor = await page.evaluate(f"({{ coins: profile.coins, owned: {TH}.owned, now: {TH}.now, toast: meta.toasts.slice(-1)[0].key, shake: document.querySelector('#thms .thm[data-id=court]').classList.contains('shake') }})")
        check('not enough coins: nothing bought, a "need N more" toast, the card shakes', poor['coins'] == 50 and 'court' not in poor['owned'] and poor['now'] == 'gym' and poor['toast'] == 'notEnough' and poor['shake'], poor)
        await page.click('#thms .thm[data-id=classic]'); await page.wait_for_timeout(150)
        check('tapping an owned theme equips it (Classic again), free', await page.evaluate(f"{TH}.now === 'classic' && profile.coins === 50"))
        await page.click('#thms .thm[data-id=gym]'); await page.wait_for_timeout(150)
        await page.screenshot(path='tests/out/theme_shop_en.png')
        await page.reload(); await page.wait_for_timeout(700)
        check('the equipped theme and the owned list persist (reload)', await page.evaluate(f"{TH}.now === 'gym' && JSON.stringify({TH}.owned) === '[\"classic\",\"gym\"]' && profile.coins === 50"))
        check('no page errors (shop)', not errs, errs); await ctx.close()

        # ===== T2: the profile's validation =====
        for stored, want in [("themes: ['gym', 'zzz', 5, 'court'], theme: 'baseball'", (['classic', 'gym', 'court'], 'classic')), ("themes: 'gym', theme: 'gym'", (['classic'], 'classic')), ("themes: ['baseball'], theme: 'baseball'", (['classic', 'baseball'], 'baseball')), ("theme: 'zzz'", (['classic'], 'classic'))]:
            ctx, page, errs = await fresh(b, init="localStorage.setItem('grasp.profile', JSON.stringify({ v: 1, coins: 3, " + stored + " }));")
            got = await page.evaluate("[profile.themes, profile.theme]")
            check(f'validation: {{{stored}}} loads as owned {want[0]}, equipped {want[1]} (unknown ids dropped, Classic always owned, an unowned theme never worn)', got == [want[0], want[1]], got)
            await ctx.close()

        # ===== T3: each theme in 2D: the arena, the bricks + specials, the ball, the sounds, the guests (desktop + phone screenshots) =====
        base = {}
        for th in ['classic', 'gym', 'court', 'baseball']:
            ctx, page, errs = await fresh(b, init=prof(th, coins=10))
            await to_stage(page, 1); await page.wait_for_timeout(400)
            img = await shot(page); fc = await floor_px(page, img)
            check(f'{th} (2D): its floor colour on screen ({"maple" if th == "gym" else "parquet" if th == "court" else "grass" if th == "baseball" else "the blue corridor"})', floor_ok(th, fc), fc)
            keys = await page.evaluate("[...SPRITES.keys()].filter(k => k.startsWith('bg|strike|'))")
            check(f'{th}: the arena is one cached background layer (keyed by world + theme)', keys == ['bg|strike|w1|' + th], keys)
            base[th] = fc
            if th == 'classic': await ctx.close(); continue
            wall = await page.evaluate("(() => { const c = corridor(), P = (x, y, z) => proj(x, y, z), a = P(c.L, c.B - (c.B - c.T) * 0.03, 25); return [a.x, a.y]; })()")
            wc = mean(img, wall[0] + 2, wall[1] - 4, wall[0] + 12, wall[1] + 4)
            ok = {'gym': wc[2] > wc[0] + 40, 'court': True, 'baseball': wc[1] > wc[0] + 15}[th]  # gym: blue crash mats; baseball: the green outfield fence
            check(f'{th}: its side walls ({"blue crash mats" if th == "gym" else "LED boards / bleachers" if th == "court" else "the green outfield fence"}) at the bottom near the player', ok, wc)
            look = await page.evaluate(f"(() => {{ const w = __grasp.strike.walls[0], lv = wallLv(w); return {{ look: {TH}.look('{th}', lv), key: strikeBrickSprite(lv, 120, 60).c === themeBrickSprite('{th}', lv, 120, 60).c }}; }})()")
            check(f'{th}: the walls\' bricks are the theme\'s ({look["look"]})', look['key'] and look['look'] in {'gym': ['mat', 'locker', 'crate'], 'court': ['backboard', 'panel'], 'baseball': ['fence', 'board']}[th], look)
            await specials_check(page, th + ' 2D')
            # the ball
            bl = await page.evaluate("""(() => { const sk = __grasp.themes.ballSkin(), sp = strikeBallSprite(false, false), R = 64, g = sp.c.getContext('2d'), x = Math.round((sp.ox + 0.3 * R) * SS), y = Math.round((sp.oy + 0.42 * R) * SS), d = g.getImageData(x - 3, y - 3, 7, 7).data; let r = 0, gg = 0, bb = 0;
              for (let i = 0; i < d.length; i += 4) { r += d[i]; gg += d[i + 1]; bb += d[i + 2]; } return { sk, c: [r / 49, gg / 49, bb / 49].map(Math.round) }; })()""")
            c = bl['c']; okb = {'gym': c[0] > 150 and c[1] < 90 and c[2] < 90, 'court': c[0] > 170 and 70 < c[1] < 150 and c[2] < 80, 'baseball': min(c) > 170}[th]
            check(f'{th}: the theme\'s ball ({bl["sk"]}: {"red rubber" if th == "gym" else "orange" if th == "court" else "white leather"}) replaces the ball skin while the theme is on', bl['sk'] == {'gym': 'dodge', 'court': 'bball', 'baseball': 'baseball'}[th] and okb, bl)
            # sounds (stubbed sfx)
            snd = await page.evaluate("""(() => { const s = __grasp.strike, now = performance.now(); for (const k in themeSfxAt) delete themeSfxAt[k]; __sfx.length = 0; __sfxa.length = 0; resetStrike(now); const start = __sfx.slice();
              __sfx.length = 0; s.setBallZ(200, innerWidth / 2, innerHeight * 0.45); strikeHit(s.ball, performance.now(), 'super', null); const sup = __sfx.slice(); park();
              __sfx.length = 0; s.setBallZ(200, innerWidth / 2, innerHeight * 0.45); strikeHit(s.ball, performance.now(), 'soft', null); const soft = __sfx.slice(); park();
              for (const k in themeSfxAt) delete themeSfxAt[k]; __sfx.length = 0; s.setBallZ(200, innerWidth / 2, innerHeight * 0.45); closeOne(s.ball, performance.now(), 'late'); const near = __sfx.slice(); park();
              for (const k in themeSfxAt) delete themeSfxAt[k]; __sfx.length = 0; s.setBallZ(200, innerWidth / 2, innerHeight * 0.45); timingFx({ grade: 'perfect', err: 0, v: 3 }, ballScreen(s.ball), performance.now(), false); const perf = __sfx.slice(); park();
              for (const k in themeSfxAt) delete themeSfxAt[k]; __sfx.length = 0; __sfxa.length = 0; themeSfx('clear'); const clear = __sfxa.slice(); return { start, sup, soft, near, perf, clear }; })()""")
            if th == 'gym':
                check('gym: the referee\'s whistle on the stage start; the dodgeball\'s own hit sound', 'refWhistle' in snd['start'] and 'tBall' in snd['soft'], snd)
            elif th == 'court':
                check('court: the horn on the stage start and the clear (buzzer); sneaker squeaks on hard hits; the basketball\'s bounce', 'buzzer' in snd['start'] and ['buzzer', 1] in snd['clear'] and 'sneaker' in snd['sup'] and 'tBall' in snd['soft'], snd)
            else:
                check('baseball: the bat crack on a SUPER hit (not a soft one), the organ\'s charge on a clear', 'batCrack' in snd['sup'] and 'batCrack' not in snd['soft'] and ['organ', 'charge'] in snd['clear'], snd)
            check(f'{th}: the crowd cheers a SUPER hit, a PERFECT and a clear; an "oooh" on a near miss', 'cheer' in snd['sup'] and 'cheer' in snd['perf'] and any(q[0] == 'cheer' for q in snd['clear']) and 'ooh' in snd['near'], snd)
            # guests: the mascots in the cow / monkey slots
            gs = await page.evaluate("""(() => { const s = __grasp.strike, out = {}; for (const kind of ['cow', 'monkey']) { __sfx.length = 0; s.floaters.length = 0; const b = s.spawnGuest(kind); const lk = guestLook(kind), sp = guestSprite(lk, 'in'), d = sp.c.getContext('2d').getImageData(0, 0, sp.c.width, sp.c.height).data; let n = 0; for (let i = 3; i < d.length; i += 16) if (d[i] > 200) n++;
              guestHit(b, ballScreen(b), performance.now()); out[kind] = { lk, px: n, sfx: __sfx.slice(), say: s.floaters.map(f => f.text) }; park(); } return out; })()""")
            want = {'gym': ('coach', 'medball'), 'court': ('foamfinger', 'hoopmonkey'), 'baseball': ('hotdog', 'glove')}[th]
            check(f'{th}: the flying guests are its mascots ({want[0]}, {want[1]}), drawn in code (not empty), each with its own bubble line and sound', (gs['cow']['lk'], gs['monkey']['lk']) == want and all(g['px'] > 800 for g in gs.values()) and gs['cow']['say'][-1:] != gs['monkey']['say'][-1:] and 'moo' not in gs['cow']['sfx'], gs)
            # the per-world time of day
            br = await page.evaluate("[1, 4].map(w => { const c = bgSprite('strike', w).c, d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let s = 0, n = 0; for (let i = 0; i < d.length; i += 400) { s += d[i] + d[i + 1] + d[i + 2]; n++; } return Math.round(s / n); })")
            check(f'{th}: the worlds still differ: world 4 is later in the day (darker) than world 1', br[1] < br[0] - 15, br)
            # screenshots: desktop with a guest flying in
            await page.evaluate(f"(() => {{ const s = {S}; s.spawnGuest('monkey'); s.setBallZ(700, innerWidth * 0.4, innerHeight * 0.42); s.ball.speed = 0; hideHint(); }})()"); await page.wait_for_timeout(300)
            await page.screenshot(path=f'tests/out/theme_{NAMES[th]}_desktop.png')
            check(f'{th}: no page errors (2D desktop)', not errs, errs); await ctx.close()
            # phone, EN / HE for the mascot line
            he = th == 'court'
            ctx, page, errs = await fresh(b, mobile=True, he=he, init=prof(th, coins=10))
            await to_stage(page, 9); await page.wait_for_timeout(400)
            img = await shot(page); fc = await floor_px(page, img)
            check(f'{th} (phone{" HE" if he else ""}): the floor colour on a phone too', floor_ok(th, fc), fc)
            say = await page.evaluate("(() => { const s = __grasp.strike, b = s.spawnGuest('monkey'); s.floaters.length = 0; guestHit(b, ballScreen(b), performance.now()); return s.floaters.map(f => f.text); })()")
            check(f'{th}: the mascot\'s bubble line in {"Hebrew" if he else "English"}', say[-1:] == [{'gym': 'OOF!', 'court': 'סוויש!', 'baseball': 'CAUGHT IT!'}[th]], say)
            await page.evaluate(f"(() => {{ const s = {S}; park(2300); s.setBallZ(520, innerWidth / 2, innerHeight * 0.45); s.ball.speed = 0; hideHint(); }})()"); await page.wait_for_timeout(300)
            await page.screenshot(path=f'tests/out/theme_{NAMES[th]}_phone.png')
            check(f'{th}: no page errors (phone)', not errs, errs); await ctx.close()

        # ===== T4: 3D: the arena's own surfaces, the bricks + specials, the ball =====
        for th in ['gym', 'court', 'baseball']:
            ctx, page, errs = await fresh(b, init=prof(th, coins=10), gfx=G3D)
            await to_stage(page, 1)
            try: await page.wait_for_function(f"{S}.gfx === '3d' && {TH}.g3 && {TH}.g3.shown === '{th}'", timeout=15000)
            except Exception: pass
            g3 = await page.evaluate(f"({{ gfx: {S}.gfx, g3: {TH}.g3, ball: G3.balls[0] && G3.balls[0].skin, mats: Object.keys(G3.mats).filter(k => k.startsWith('th:')) }})")
            check(f'{th} (3D): the corridor wears the theme\'s own surface pictures (Phong + map), its bricks use the theme\'s looks, the ball is the theme\'s', g3['gfx'] == '3d' and g3['g3'] and g3['g3']['shown'] == th and g3['g3']['floorMap'] and g3['g3']['corMat'] == 'MeshPhongMaterial' and len(g3['mats']) >= 1 and g3['ball'] == {'gym': 'dodge', 'court': 'bball', 'baseball': 'baseball'}[th], g3)
            await page.evaluate("hideHint()"); await page.wait_for_timeout(500)
            img = await shot(page); fc = await floor_px(page, img)
            check(f'{th} (3D): its floor colour on screen', floor_ok(th, fc), fc)
            await specials_check(page, th + ' 3D')
            await page.evaluate(f"(() => {{ const s = {S}; s.walls.length = 0; [0, 1, 2, 3].forEach(i => s.spawnWall('brick', wallSlotZ(i))); s.setBallZ(560, innerWidth / 2, innerHeight * 0.45); s.ball.speed = 0; hideHint(); }})()"); await page.wait_for_timeout(500)
            await page.screenshot(path=f'tests/out/theme_{NAMES[th]}_3d.png')
            check(f'{th}: no page errors (3D)', not errs, errs); await ctx.close()

        # ===== T5: the sounds really play (offline render): audible, under the peak, silent when muted; classic has none; the music's variation =====
        ctx, page, errs = await fresh(b, init=prof('court', coins=10))
        rd = await page.evaluate("""(async () => { const real = audio, out = {};
          for (const k of [['refWhistle', 2], ['buzzer', 1], ['sneaker'], ['batCrack', 1], ['organ', 'charge'], ['cheer', 1], ['ooh'], ['tBall', 'dodge'], ['tBall', 'bball'], ['tBall', 'baseball'], ['glovePop']]) {
            for (const m of [false, true]) { const oc = new OfflineAudioContext(1, 44100 * 2.4, 44100); Object.defineProperty(oc, 'state', { get: () => 'running' }); audio = oc; noiseBuf = null; muted = m;
              sfx(k[0], k[1]); const buf = await oc.startRendering(), d = buf.getChannelData(0); let pk = 0; for (let i = 0; i < d.length; i++) pk = Math.max(pk, Math.abs(d[i])); out[k.join(':') + (m ? ':muted' : '')] = +pk.toFixed(3); } }
          audio = real; noiseBuf = null; muted = false; return out; })()""")
        loud = {k: v for k, v in rd.items() if not k.endswith(':muted')}
        check('every themed sound is generated (Web Audio, no files) and audible: whistle, buzzer, sneaker, bat crack, organ, cheer, "oooh", the three balls, the glove', all(v > 0.02 for v in loud.values()), loud)
        check('...never louder than the game\'s other sounds (peak <= 0.3)', all(v <= 0.3 for v in loud.values()), loud)
        check('...and silent when muted', all(v == 0 for k, v in rd.items() if k.endswith(':muted')), {k: v for k, v in rd.items() if k.endswith(':muted')})
        cl = await page.evaluate(f"(() => {{ profile.theme = 'classic'; __sfx.length = 0; const r = {TH}.sfx('clear'); const s = __sfx.slice(); profile.theme = 'court'; return {{ r, s }}; }})()")
        check('Classic keeps the old sounds (no themed sounds)', cl == {'r': None, 's': []}, cl)
        mu = await page.evaluate(f"(() => {{ const t = (th) => {{ profile.theme = th; const q = {TH}.track(1); return {{ lead: q.lead, bpm: q.bpm, mel: q.mel.join(','), s: q.s }}; }}; const r = {{ classic: t('classic'), gym: t('gym'), court: t('court'), baseball: t('baseball') }}; profile.theme = 'court'; return r; }})()")
        check('the world music has a themed variation (its own lead / drums / tempo: the organ at the ballpark, claps), the world\'s melody kept', mu['baseball']['lead'] == 'organ' and mu['gym']['lead'] == 'whistle' and mu['court']['s'] != mu['classic']['s'] and mu['court']['bpm'] != mu['classic']['bpm'] and len({m['mel'] for m in mu.values()}) == 1 and mu['classic']['lead'] == 'square', mu)
        # the daily, Frenzy and Endless use the theme
        await page.evaluate("startDaily('mouse')"); await page.wait_for_function(f"daily.on && gameMode === 'strike' && {S}.walls.length > 0", timeout=10000); await page.wait_for_timeout(200)
        dk = await page.evaluate("[...SPRITES.keys()].filter(k => k.startsWith('bg|strike|'))")
        check('the daily uses the theme too (cosmetic only: the same seeded run)', dk == ['bg|strike|w1|court'], dk)
        await page.evaluate("goHome()"); await page.wait_for_timeout(300)
        await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.click('#advFrenzy'); await page.wait_for_function(f"frenzy.on && {S}.walls.length > 0", timeout=10000); await page.wait_for_timeout(200)
        check('Frenzy uses the theme (its arena and ball)', await page.evaluate("[...SPRITES.keys()].includes('bg|strike|w1|court') && ballSkinNow() === 'bball'"))
        check('no page errors (sounds, modes)', not errs, errs); await ctx.close()

        # ===== T6: the map footer's Theme chip opens the Shop's Themes section over the map (phone EN / HE) =====
        for he in (False, True):
            ctx, page, errs = await fresh(b, mobile=True, he=he, init=prof('baseball', coins=320, extra=", adv: { stars: { 1: 3, 2: 2 }, best: { 1: 4000, 2: 3000 }, unlocked: 3 }"))
            await page.evaluate("openAdvMap({ how: 'mouse' })"); await page.wait_for_timeout(500)
            chip = await page.evaluate("(() => { const b = $('advTheme'), r = b.getBoundingClientRect(), f = [...document.querySelectorAll('.amFoot > *')].filter(e => !e.hidden && e !== b).map(e => e.getBoundingClientRect()), ov = f.some(q => q.left < r.right && r.left < q.right && q.top < r.bottom && r.top < q.bottom); return { th: b.dataset.theme, aria: b.getAttribute('aria-label'), w: r.width, h: r.height, l: Math.min(...f.map(q => q.left)), r: Math.max(...f.map(q => q.right)), cl: r.left, cr: r.right, ct: r.top, cb: r.bottom, ov }; })()")
            check(f'the map footer has a small Theme chip (the equipped theme\'s ball; {"HE" if he else "EN"} label) and the footer\'s buttons still fit a phone (on a phone the chip floats just above the footer\'s corner, overlapping nothing)', chip['th'] == 'baseball' and (('בייסבול' in chip['aria']) if he else ('Baseball' in chip['aria'])) and chip['w'] >= 40 and chip['h'] >= 40 and chip['l'] >= 0 and chip['r'] <= 360 and chip['cl'] >= 0 and chip['cr'] <= 360 and chip['cb'] <= 740 and not chip['ov'], chip)
            if not he: await page.screenshot(path='tests/out/theme_map_chip.png')
            await page.click('#advTheme'); await page.wait_for_timeout(500)
            sh = await page.evaluate("(() => { const P = $('collection'), sec = $('cthemes').getBoundingClientRect(), sheet = P.querySelector('.sheet').getBoundingClientRect(), card = document.querySelector('#thms .thm[data-id=court]').getBoundingClientRect(), hit = document.elementFromPoint(card.left + card.width / 2, card.top + card.height / 2); return { open: !P.hidden, over: P.classList.contains('overMap'), map: advMapOpen(), secTop: sec.top - sheet.top, onTop: !!(hit && hit.closest('#thms')), h3: $('cthemes').querySelector('h3').textContent }; })()")
            check(f'the chip opens the Shop over the map, scrolled to the Themes section ({sh["h3"]}), its cards on top and tappable', sh['open'] and sh['over'] and sh['map'] and sh['onTop'] and -2 <= sh['secTop'] <= 60 and sh['h3'] == ('מגרשים' if he else 'Themes'), sh)
            await page.screenshot(path=f'tests/out/theme_shop_{"he" if he else "en"}.png')
            await page.click('#thms .thm[data-id=court]'); await page.wait_for_timeout(250)
            check('buying from there: 400 > 320 coins, so not bought; then with coins: bought, worn, the chip follows', await page.evaluate("profile.theme === 'baseball' && profile.coins === 320"))
            await page.evaluate("profile.coins = 900; saveProfile(); renderCollection()")
            await page.click('#thms .thm[data-id=court]'); await page.wait_for_timeout(250)
            ch2 = await page.evaluate("({ th: $('advTheme').dataset.theme, coins: profile.coins, now: profile.theme })")
            check('...bought for 400, worn, the map chip now shows the court', ch2 == {'th': 'court', 'coins': 500, 'now': 'court'}, ch2)
            await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
            check('Escape closes the Shop and leaves the map open', await page.evaluate("$('collection').hidden && advMapOpen() && !$('collection').classList.contains('overMap')"))
            check(f'no page errors (map chip {"HE" if he else "EN"})', not errs, errs); await ctx.close()

        await b.close()
    srv.terminate()
    print('\nTHEMES:', 'ALL PASS' if check.fails == 0 else f'{check.fails} FAILED')
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
