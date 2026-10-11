exec(open('tests/test_sandbox.py').read().split('async def boot')[0])
# The installable app: manifest.webmanifest (valid, icons on disk and served, shortcuts), sw.js (registers, precaches the shell, works offline for /
# and the game links, versioned cache, "New version — tap to refresh" for a new index.html and for a new sw.js, /tremorti/ untouched), the Install
# chip (a stubbed beforeinstallprompt; iOS: the how-to sheet; snooze; hidden in the installed app), vercel.json's headers.
# The service worker runs only with window.__graspSW (navigator.webdriver otherwise keeps it off for every other suite), on its own server
# (a copy of the site in a temp dir, port 8799) so the test can take it offline and change files.
import os, shutil, tempfile, threading, functools, importlib.util, http.server
from PIL import Image
OUT = 'tests/out/'; os.makedirs(OUT, exist_ok=True)
PORT = 8799; BASE = f'http://localhost:{PORT}'
spec = importlib.util.spec_from_file_location('graspserve', 'tests/serve.py'); serve = importlib.util.module_from_spec(spec); spec.loader.exec_module(serve)
SITE = tempfile.mkdtemp(prefix='grasp_pwa_')
for f in ['index.html', 'sw.js', 'manifest.webmanifest', 'vercel.json']: shutil.copy(f, SITE)
for d in ['icons', 'vendor', 'assets', 'tremorti']: shutil.copytree(d, os.path.join(SITE, d), ignore=shutil.ignore_patterns('tests'))

class Srv:  # the test's own server, started / stopped at will (offline = stopped)
    def __init__(self): self.h = None
    def start(self):
        http.server.ThreadingHTTPServer.allow_reuse_address = True
        self.h = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(serve.Handler, directory=SITE)); threading.Thread(target=self.h.serve_forever, daemon=True).start()
    def stop(self):
        if self.h: self.h.shutdown(); self.h.server_close(); self.h = None
own = Srv()
SWI = "window.__graspSW = true;"
BIP = """window.__bip = (outcome) => { const e = new Event('beforeinstallprompt', { cancelable: true }); window.__prompted = 0; e.prompt = () => { window.__prompted++; return Promise.resolve(); }; e.userChoice = Promise.resolve({ outcome, platform: 'web' }); window.dispatchEvent(e); return e.defaultPrevented; };"""
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
R = "(e) => { const q = e.getBoundingClientRect(); return { l: q.left, r: q.right, t: q.top, b: q.bottom, w: q.width, h: q.height }; }"
def rects_overlap(a, b, slack=0): return a['l'] < b['r'] - slack and b['l'] < a['r'] - slack and a['t'] < b['b'] - slack and b['t'] < a['b'] - slack

async def ctx_page(b, mobile=False, he=False, ua=None, init='', sw=True, perms=None):
    opts = dict(viewport={'width': 360, 'height': 740}, device_scale_factor=2, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 800})
    if ua: opts['user_agent'] = ua
    if perms: opts['permissions'] = perms
    ctx = await b.new_context(**opts); page = await ctx.new_page(); errs = []
    async def fonts(route): await route.fulfill(status=200, body='', content_type='text/css')
    await ctx.route('**/fonts.g*/**', fonts)
    page.on('pageerror', lambda e: errs.append(str(e)))
    await ctx.add_init_script(INIT + (SWI if sw else '') + BIP + ("localStorage.setItem('lang','he');" if he else "localStorage.setItem('lang','en');") + "sessionStorage.setItem('grasp.testDate', '2026-10-10');" + init)
    return ctx, page, errs

async def ready(page): await page.wait_for_function("window.__grasp && __grasp.pwa && __grasp.event", timeout=20000)

async def main():
    own.start()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'])

        # ---- the manifest, the icons, the headers ----
        M = json.load(open('manifest.webmanifest'))
        check('manifest: name Grasp, start_url /, scope /, display standalone, theme / background colours', M['name'] == 'Grasp' and M['short_name'] == 'Grasp' and M['start_url'] == '/' and M['scope'] == '/' and M['display'] == 'standalone' and M['theme_color'].startswith('#') and M['background_color'].startswith('#'), M)
        icons = {(i['sizes'], i['purpose']): i['src'] for i in M['icons']}
        check('manifest icons: 192 + 512 (any) and 192 + 512 maskable', set(icons) >= {('192x192', 'any'), ('512x512', 'any'), ('512x512', 'maskable'), ('192x192', 'maskable')}, icons)
        sizes_ok = all(os.path.exists('.' + src) and Image.open('.' + src).size == tuple(int(x) for x in sz.split('x')) and Image.open('.' + src).format == 'PNG' for (sz, _), src in icons.items())
        check('every icon is a PNG on disk with its declared size', sizes_ok)
        mk = Image.open('icons/icon-maskable-512.png').convert('RGBA'); corner = mk.getpixel((3, 3)); centre = mk.getpixel((256, 256))
        check('the maskable icon is full-bleed (opaque corners) with the logo in the middle', corner[3] == 255 and centre[3] == 255, [corner, centre])
        sc = {s['url']: s['name'] for s in M['shortcuts']}
        check('shortcuts: Strike, Smash, Shapes, Camera games (with icons on disk)', sc == {'/strike': 'Strike', '/smash': 'Smash', '/shapes': 'Shapes', '/?open=camera': 'Camera games'} and all(os.path.exists('.' + s['icons'][0]['src']) for s in M['shortcuts']), sc)
        V = json.load(open('vercel.json')); H = {h['source']: {x['key'].lower(): x['value'] for x in h['headers']} for h in V.get('headers', [])}
        check('vercel.json: sw.js no-cache (+ JS type, Service-Worker-Allowed /), the manifest as application/manifest+json', 'no-cache' in H['/sw.js']['cache-control'] and 'javascript' in H['/sw.js']['content-type'] and H['/sw.js']['service-worker-allowed'] == '/' and H['/manifest.webmanifest']['content-type'].startswith('application/manifest+json'), H)
        ctx, page, errs = await ctx_page(b, sw=False)
        await page.goto(BASE + '/'); await ready(page)
        q = await page.evaluate("""(async () => { const get = async (u) => { const r = await fetch(u, { cache: 'no-store' }); return { s: r.status, t: r.headers.get('content-type'), c: r.headers.get('cache-control'), n: (await r.arrayBuffer()).byteLength }; };
          const m = document.querySelector('link[rel=manifest]'); const out = { link: m && m.getAttribute('href'), theme: document.querySelector('meta[name=theme-color]').content, apple: !!document.querySelector('link[rel=apple-touch-icon]') };
          for (const u of ['/manifest.webmanifest', '/sw.js', '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png', '/vendor/matter.min.js', '/vendor/three.min.js']) out[u] = await get(u); return out; })()""")
        check('the page links the manifest, a theme colour and the Apple touch icon', q['link'] == '/manifest.webmanifest' and q['theme'] and q['apple'], q)
        check('served: the manifest as application/manifest+json, sw.js no-cache as JS, the icons and the self-hosted libraries', q['/manifest.webmanifest']['t'].startswith('application/manifest+json') and 'no-cache' in (q['/sw.js']['c'] or '') and 'javascript' in q['/sw.js']['t'] and all(q[u]['s'] == 200 and q[u]['n'] > 1000 for u in ['/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png', '/vendor/matter.min.js', '/vendor/three.min.js']), q)
        q = await page.evaluate("[!!window.Matter, __grasp.pwa.state.allowed, __grasp.pwa.state.log, navigator.serviceWorker.controller]")
        check('Matter.js loads from this site; under automation (no __graspSW) no service worker at all', q[0] and q[1] is False and 'off' in q[2] and q[3] is None, q)
        check('manifest / headers: no page errors', not errs, errs); await ctx.close()

        # ---- the service worker: registers, precaches, takes over; offline: /, the game links, an unknown path; Tremorti untouched ----
        ctx, page, errs = await ctx_page(b, perms=['notifications'])
        await page.goto(BASE + '/'); await ready(page)
        await page.wait_for_function("navigator.serviceWorker.controller && __grasp.pwa.state.version", timeout=20000)
        q = await page.evaluate("""(async () => { const ks = await caches.keys(), shell = ks.find((k) => k.startsWith('grasp-shell-')), c = await caches.open(shell), keys = (await c.keys()).map((r) => new URL(r.url).pathname);
          return { ks, shell, keys, st: __grasp.pwa.state, scope: (await navigator.serviceWorker.getRegistration()).scope }; })()""")
        need = ['/index.html', '/manifest.webmanifest', '/vendor/matter.min.js', '/vendor/three.min.js', '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png', '/assets/guests/cow_in.png']
        check('the service worker registers (scope /), takes over the first visit, reports its version', q['st']['controlled'] and q['scope'] == BASE + '/' and q['st']['version'].startswith('grasp-') and 'registered' in q['st']['log'], q['st'])
        check('the shell is precached in a versioned cache (index.html, the manifest, Matter.js, three.js, the icons, the guest art)', q['shell'] == 'grasp-shell-' + q['st']['version'] and all(k in q['keys'] for k in need), q)
        await page.goto(BASE + '/tremorti/'); await page.wait_for_load_state('load')
        q = await page.evaluate("({ title: document.title, grasp: !!window.__grasp, ctl: !!navigator.serviceWorker.controller })")
        check('/tremorti/ still loads its own page (Tremorti, not the game) while the service worker runs', 'tremorti' in q['title'].lower() and not q['grasp'], q)
        # Tremorti's reminders: it reuses the site's registration when one exists (showNotification works through it; sw.js has a notificationclick
        # that brings back /tremorti/), or registers its own tiny /tremorti/sw.js (scope /tremorti/), which then controls Tremorti alone
        await ctx.grant_permissions(['notifications'], origin=BASE)
        q = await page.evaluate("(async () => { const r = await navigator.serviceWorker.getRegistration(); let n = -1, err = ''; try { await r.showNotification('Tremorti', { body: 'test', tag: 'tremorti-daily' }); const l = await r.getNotifications({ tag: 'tremorti-daily' }); l.forEach((x) => x.close()); n = l.length; } catch (e) { err = String(e.message || e); } return { scope: r.scope, n, err, perm: Notification.permission }; })()")
        check('/tremorti/ finds the site\'s registration (scope /) and can show its reminder through it (where this browser allows notifications)', q['scope'] == BASE + '/' and (q['n'] == 1 or (q['n'] == -1 and 'permission' in q['err'])), q)
        check('the site\'s sw.js handles a click on such a reminder (focus / open /tremorti/)', "notificationclick" in open('sw.js').read() and "'/tremorti/'" in open('sw.js').read())
        if os.path.exists(os.path.join(SITE, 'tremorti', 'sw.js')):
            await page.evaluate("navigator.serviceWorker.register('sw.js').then(() => navigator.serviceWorker.getRegistration('/tremorti/'))")
            await page.wait_for_function("navigator.serviceWorker.getRegistration('/tremorti/').then((r) => !!(r && r.active && r.scope.endsWith('/tremorti/')))", timeout=15000)
            await page.reload(); await page.wait_for_load_state('load'); await page.wait_for_function("!!navigator.serviceWorker.controller", timeout=10000)
            q = await page.evaluate("({ title: document.title, ctl: navigator.serviceWorker.controller.scriptURL })")
            check('Tremorti\'s own sw.js (scope /tremorti/) installs beside the site\'s and controls Tremorti; the page still loads fresh', 'tremorti' in q['title'].lower() and q['ctl'].endswith('/tremorti/sw.js'), q)
            await page.goto(BASE + '/'); await ready(page)
            q = await page.evaluate("navigator.serviceWorker.controller.scriptURL")
            check('... and the game is still controlled by the site\'s sw.js', q == BASE + '/sw.js', q)
        own.stop(); await ctx.set_offline(True)
        await page.goto(BASE + '/'); await ready(page); await page.wait_for_timeout(500)
        q = await page.evaluate("({ matter: !!window.Matter, start: !$('start').hidden, tiles: document.querySelectorAll('#start .modes button').length, ev: document.querySelector('#eventBtn .evName').textContent, online: navigator.onLine })")
        check('offline: / loads from the cache (Matter.js too), the start screen with its tiles and the event banner', q['matter'] and q['start'] and q['tiles'] == 7 and q['ev'] and q['online'] is False, q)
        await page.screenshot(path=OUT + 'pwa_offline_start.png')
        await page.goto(BASE + '/strike'); await ready(page)
        await page.wait_for_function("!$('advMap').hidden", timeout=10000)
        check('offline: /strike opens the Adventure map', True)
        await page.evaluate("$('advEndless').click()"); await page.wait_for_function("mode === 'mouse' && gameMode === 'strike' && __grasp.strike.ball", timeout=15000)
        check('offline: Strike plays', True)
        await page.goto(BASE + '/smash/'); await ready(page); await page.wait_for_function("!$('smashMap').hidden", timeout=10000)
        check('offline: /smash/ (trailing slash) opens the Smash map', True)
        await page.goto(BASE + '/duel?m=adv&s=1&score=50'); await ready(page); await page.wait_for_function("__grasp.duel.on || mode !== 'none'", timeout=15000)
        check('offline: a challenge link (/duel?...) opens the challenge', await page.evaluate("location.pathname + location.search") == '/duel?m=adv&s=1&score=50')
        q = await page.evaluate("(async () => { const r = await fetch('/vendor/three.min.js'); return [r.status, (await r.text()).length]; })()")
        check('offline: three.js (the 3D renderer) served from the cache', q[0] == 200 and q[1] > 500000, q)
        await page.goto(BASE + '/no-such-page'); await ready(page)
        check('offline: an unknown page falls back to the start screen', await page.evaluate("!$('start').hidden"))
        await ctx.set_offline(False); own.start()
        check('offline: no page errors', not errs, errs)

        # ---- updates: a new index.html (the cached page first, then "New version — tap to refresh") and a new sw.js (it waits; the tap takes it) ----
        html = open(os.path.join(SITE, 'index.html')).read()
        open(os.path.join(SITE, 'index.html'), 'w').write(html.replace('</body>', '<script>window.__v2 = true;</script></body>'))
        await page.goto(BASE + '/'); await ready(page)
        q = await page.evaluate("!!window.__v2")
        check('a new index.html: this visit still shows the cached one (instant, offline-safe)', q is False, q)
        await page.wait_for_function("!$('pwaUpdate').hidden", timeout=15000); await page.wait_for_timeout(600)  # (it springs in)
        q = await page.evaluate(f"({{ st: __grasp.pwa.state, r: ({R})($('pwaUpdate')), W: innerWidth, H: innerHeight, txt: $('pwaUpdate').textContent }})")
        check('then the toast "New version — tap to refresh", on screen at the bottom', q['st']['update'] and q['st']['why'] == 'page' and q['txt'] == 'New version — tap to refresh' and q['r']['b'] <= q['H'] and q['r']['t'] > q['H'] * 0.75 and q['r']['l'] >= 0 and q['r']['r'] <= q['W'], q)
        await page.screenshot(path=OUT + 'pwa_update_toast.png')
        await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=10000)
        check('the toast hides while a game is played (never mid-round)', await page.evaluate("getComputedStyle($('pwaUpdate')).display === 'none'"))
        await page.evaluate("goHome()"); await page.wait_for_function("mode === 'none' && getComputedStyle($('pwaUpdate')).display !== 'none'", timeout=5000)
        async with page.expect_navigation(): await page.click('#pwaUpdate')
        await ready(page)
        check('tapped: the page reloads with the new version', await page.evaluate("!!window.__v2 && $('pwaUpdate').hidden"))
        sw = open(os.path.join(SITE, 'sw.js')).read(); v1 = await page.evaluate("__grasp.pwa.state.version")
        open(os.path.join(SITE, 'sw.js'), 'w').write(sw.replace("const VERSION = '", "const VERSION = 'v2-"))
        await page.evaluate("navigator.serviceWorker.getRegistration().then((r) => r.update())")
        await page.wait_for_function("!$('pwaUpdate').hidden && __grasp.pwa.state.why === 'sw'", timeout=20000)
        check('a new sw.js installs in the background and waits: the same toast', True)
        async with page.expect_navigation(): await page.click('#pwaUpdate')
        await ready(page); await page.wait_for_function("__grasp.pwa.state.version.startsWith('v2-')", timeout=15000)
        q = await page.evaluate("(async () => ({ v: __grasp.pwa.state.version, ks: await caches.keys() }))()")
        check('tapped: the new worker takes over, the page reloads; the old version\'s cache is deleted', q['v'] == 'v2-' + v1 and ('grasp-shell-' + v1) not in q['ks'] and ('grasp-shell-v2-' + v1) in q['ks'], [v1, q])
        check('updates: no page errors', not errs, errs); await ctx.close()

        # ---- the Install chip: a stubbed beforeinstallprompt (Android / desktop Chrome) ----
        for mobile in (True, False):
            for he in (False, True):
                tag = ('phone ' if mobile else 'desktop ') + ('he' if he else 'en')
                ctx, page, errs = await ctx_page(b, mobile, he, sw=False)
                await page.goto(BASE + '/'); await ready(page); await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true")
                q0 = await page.evaluate("__grasp.pwa.state")
                pre = await page.evaluate("__bip('accepted')"); await page.wait_for_timeout(1300)
                await (page.tap('#moreBtn') if mobile else page.click('#moreBtn')); await page.wait_for_function("!$('moreSheet').hidden", timeout=3000); await page.wait_for_timeout(450)  # (home2: Install is a row of the More sheet, behind ⋯)
                L = await page.evaluate(f"""(() => {{ const r = {R}; return {{ chip: r($('installBtn')), sheet: r($('moreSheet').querySelector('.sheet')), others: [...document.querySelectorAll('#moreSheet .moreRow')].filter(e => e !== $('installBtn') && !e.hidden).map(r), W: innerWidth, H: innerHeight, label: getComputedStyle($('installBtn').querySelector('.lb')).display !== 'none', aria: $('installBtn').getAttribute('aria-label'), onStart: !!$('installBtn').closest('#start'), noScroll: $('start').scrollHeight <= $('start').clientHeight + 1 }}; }})()""")
                check(tag + ': no chip until the browser offers the install; then the chip shows (the event default prevented: no mini-infobar)', not q0['chip'] and pre and await page.evaluate("__grasp.pwa.state.chip"), q0)
                check(tag + ': the Install row sits in the More sheet (not on the start screen), labelled, a big target, inside the sheet, overlapping nothing', L['chip']['l'] >= L['sheet']['l'] and L['chip']['r'] <= L['sheet']['r'] + 0.5 and L['chip']['b'] <= L['H'] and L['chip']['h'] >= 44 and not L['onStart'] and not any(rects_overlap(L['chip'], o, 1) for o in L['others']) and L['label'] and L['aria'] == ('להתקין את Grasp כאפליקציה' if he else 'Install Grasp as an app') and L['noScroll'], L)
                await page.screenshot(path=OUT + 'pwa_install_chip_%s_%s.png' % ('phone' if mobile else 'desktop', 'he' if he else 'en'))
                await page.keyboard.press('Escape'); await page.wait_for_timeout(150)
                if mobile and not he:
                    await page.evaluate("__grasp.setGameMode('slice')"); await page.evaluate(START_MOUSE); await page.wait_for_function("mode === 'mouse'", timeout=10000)
                    await page.tap('#pauseBtn'); await page.wait_for_function("menu.open", timeout=4000)
                    q = await page.evaluate(f"(() => {{ const r = ({R})($('menuInstall')); return {{ r, vis: getComputedStyle($('menuInstall')).display !== 'none', txt: $('menuInstall').textContent.trim() }}; }})()")
                    check(tag + ': the pause sheet has "Install app" too', q['vis'] and q['r']['h'] > 30 and q['txt'] == 'Install app', q)
                    await page.screenshot(path=OUT + 'pwa_install_menu.png')
                    await page.tap('#menuInstall'); await page.wait_for_function("__grasp.pwa.state.log.includes('choice:accepted')", timeout=5000)
                    q = await page.evaluate("[window.__prompted, __grasp.pwa.state.chip, __grasp.pwa.state.menu, __grasp.pwa.state.snoozed]")
                    check(tag + ': tapped: the browser\'s prompt (once); accepted: no chip anywhere, no snooze', q == [1, False, False, False], q)
                    await page.evaluate("window.dispatchEvent(new Event('appinstalled'))")
                    check(tag + ': appinstalled: "Grasp is installed!"', await page.evaluate("meta.toasts.some((t) => t.key === 'pwaInstalled')"))
                check(tag + ': no page errors', not errs, errs); await ctx.close()
        # dismissed: snoozed for 14 days on the start screen (the pause sheet would still offer a new prompt)
        ctx, page, errs = await ctx_page(b, mobile=True, sw=False)
        await page.goto(BASE + '/'); await ready(page); await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true")
        await page.evaluate("__bip('dismissed')"); await page.tap('#moreBtn'); await page.wait_for_timeout(450); await page.tap('#installBtn'); await page.wait_for_function("__grasp.pwa.state.log.includes('choice:dismissed')", timeout=5000)
        q = await page.evaluate("[__grasp.pwa.state.snoozed, __grasp.pwa.state.chip, localStorage.getItem('grasp.installSnooze')]")
        check('dismissed: snoozed (the date kept), the Install row gone', q == [True, False, '2026-10-10'], q)
        await page.evaluate("__bip('accepted')")
        q = await page.evaluate("[__grasp.pwa.state.chip, __grasp.pwa.state.menu]")
        check('offered again within 14 days: the start-screen chip stays away (not nagging), the pause sheet has it', q == [False, True], q)
        await page.evaluate("__grasp.setDate('2026-10-25'); __grasp.pwa.sync()")
        check('15 days later the chip comes back', await page.evaluate("__grasp.pwa.state.chip"))
        check('snooze: no page errors', not errs, errs); await ctx.close()
        # the installed app (standalone): never a chip
        ctx, page, errs = await ctx_page(b, mobile=True, sw=False, init="Object.defineProperty(navigator, 'standalone', { get: () => true });")
        await page.goto(BASE + '/'); await ready(page); await page.evaluate("__bip('accepted')")
        q = await page.evaluate("[__grasp.pwa.state.standalone, __grasp.pwa.state.chip, __grasp.pwa.state.menu]")
        check('in the installed app: no Install chip (start screen or pause sheet)', q == [True, False, False], q)
        await ctx.close()

        # ---- iOS: no beforeinstallprompt; the chip opens a small "Add to Home Screen" how-to ----
        for he in (False, True):
            ctx, page, errs = await ctx_page(b, mobile=True, he=he, ua=IPHONE, sw=False)
            await page.goto(BASE + '/'); await ready(page); await page.evaluate("for (const o of document.querySelectorAll('.ov')) o.hidden = true")
            check('iOS%s: the chip shows without a browser prompt' % (' HE' if he else ''), await page.evaluate("__grasp.pwa.state.ios && __grasp.pwa.state.chip"))
            await page.tap('#moreBtn'); await page.wait_for_timeout(450); await page.tap('#installBtn'); await page.wait_for_function("!$('iosInstall').hidden", timeout=3000); await page.wait_for_timeout(450)
            q = await page.evaluate(f"(() => {{ const P = $('iosInstall'), r = ({R})(P.querySelector('.sheet')); return {{ steps: [...P.querySelectorAll('.iosSteps li')].map((l) => l.textContent.trim()), title: $('iosTitle').textContent, r, W: innerWidth, H: innerHeight, icon: P.querySelector('.iosIcon').naturalWidth }}; }})()")
            check('iOS%s: the how-to sheet: the title, 3 steps (Share, Add to Home Screen, Add), the icon, on screen' % (' HE' if he else ''), len(q['steps']) == 3 and q['title'] == ('הוספת Grasp למסך הבית' if he else 'Add Grasp to your Home Screen') and q['icon'] == 180 and q['r']['t'] >= 0 and q['r']['b'] <= q['H'] and q['r']['r'] <= q['W'], q)
            await page.screenshot(path=OUT + 'pwa_ios_%s.png' % ('he' if he else 'en'))
            await page.tap('#iosLater'); await page.wait_for_function("$('iosInstall').hidden", timeout=3000)
            q = await page.evaluate("[__grasp.pwa.state.snoozed, __grasp.pwa.state.chip, __grasp.pwa.state.menu]")
            check('iOS%s: Not now: snoozed (the start chip hides, the pause sheet keeps it)' % (' HE' if he else ''), q == [True, False, True], q)
            check('iOS: no page errors', not errs, errs); await ctx.close()

        # ---- the Camera games shortcut: /?open=camera opens the picker on the start screen ----
        ctx, page, errs = await ctx_page(b, mobile=True, sw=False)
        await page.goto(BASE + '/?open=camera'); await ready(page)
        await page.wait_for_function("!$('cgPick').hidden", timeout=5000)
        check('the shortcut /?open=camera: the camera games picker opens, the address becomes /', await page.evaluate("location.pathname + location.search") == '/' and await page.evaluate("$('gifts').hidden"))
        check('shortcut: no page errors', not errs, errs); await ctx.close()
        await b.close()
    own.stop(); shutil.rmtree(SITE, ignore_errors=True)
    srv.terminate()
    print('\n' + ('ALL PASS' if check.fails == 0 else f'{check.fails} FAILED'))
    sys.exit(1 if check.fails else 0)

asyncio.run(main())
