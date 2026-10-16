"""The pet's 3D room, measured (not a test): python3 tests/pet3d_measure.py [port] (default 8765; a server must be running, e.g. tests/serve.py).
Phone viewport 390 x 844 at DPR 2, CDP CPU throttling x4 (Emulation.setCPUThrottlingRate 4). Prints per run: the time from opening the room to the
first 3D frame (cold: three.js + GLTFLoader + the .glb fetched and parsed; warm: the room reopened), pet3d's own JS per frame (the mixer, effects,
the render call), the frames the room drew per second while idle (capped ~24) and during a tap's action, and the main thread's long tasks.
Headless Chromium draws WebGL with SwiftShader (a CPU rasterizer, also used for compositing the page): the fps here are far below a phone GPU's."""
import asyncio, json, sys
from playwright.async_api import async_playwright
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
PET = dict(hatched=True, food=12, pantry=5, born='2026-10-01', last='2026-10-01', seen=2, color='sky', head='bow', egg=True, eggSeen=True, asked=True)
LT = "window.__lt = []; try { new PerformanceObserver((l) => { for (const e of l.getEntries()) __lt.push(Math.round(e.duration)); }).observe({ entryTypes: ['longtask'] }); } catch (e) {}"

async def run(b, rate=4, off=False):
    ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = await ctx.new_page(); errs = []; page.on('pageerror', lambda e: errs.append(str(e)))
    cdp = await ctx.new_cdp_session(page); await cdp.send('Emulation.setCPUThrottlingRate', {'rate': rate})
    await page.add_init_script("window.__graspPet3d = " + json.dumps({'off': True} if off else {'lowFps': 0}) + "; localStorage.setItem('lang','en'); sessionStorage.setItem('grasp.testDate','2026-10-02');"
                               "localStorage.setItem('grasp.profile', " + json.dumps(json.dumps({'v': 1, 'pet': PET})) + ");" + LT)
    await page.goto(f'http://127.0.0.1:{PORT}/index.html'); await page.wait_for_function("window.__grasp && __grasp.pet", timeout=60000)
    await page.wait_for_timeout(1000)
    out = {'renderer': '2d (off)' if off else '3d', 'cpu_throttle': rate}
    t0 = await page.evaluate("performance.now()"); await page.evaluate("__grasp.pet.open(true)")
    if not off:
        await page.wait_for_function("__grasp.pet3d.info.shown", timeout=90000, polling=10); out['first_frame_cold_ms'] = await page.evaluate("__grasp.pet3d.stats.first")
        await page.wait_for_function("!__grasp.pet3d.p3.queue.length && !__grasp.pet3d.p3.pumping", timeout=120000, polling=200)
        await page.evaluate("__grasp.pet.close()"); await page.wait_for_timeout(500); await page.evaluate("__grasp.pet.open(true)")
        await page.wait_for_function("__grasp.pet3d.info.shown", timeout=60000, polling=10); out['first_frame_warm_ms'] = await page.evaluate("__grasp.pet3d.stats.first")
    await page.wait_for_timeout(1500)
    for name, js, ms in (('idle', '', 4000), ('tap', '__grasp.pet.tap()', 2000)):
        f0 = await page.evaluate("__grasp.pet.frames"); await page.evaluate("__lt.length = 0; " + js); await page.wait_for_timeout(ms)
        f1 = await page.evaluate("__grasp.pet.frames"); lt = await page.evaluate("__lt")
        out[name] = {'room_fps': round((f1 - f0) * 1000 / ms, 1), 'long_tasks': len(lt), 'long_task_med_ms': sorted(lt)[len(lt) // 2] if lt else 0}
    if not off: out['pet3d_js_ms_per_frame'] = round(await page.evaluate("__grasp.pet3d.stats.ms"), 2); out['render_call_ms'] = round(await page.evaluate("__grasp.pet3d.stats.render"), 2)
    out['errors'] = errs; print(json.dumps(out)); await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await run(b, 4, off=True); await run(b, 4); await run(b, 1)
        await b.close()
asyncio.run(main())
