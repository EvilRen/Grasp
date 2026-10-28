/* Grasp's service worker: the game installs as an app and plays offline.
   - The app shell (index.html, the manifest, the icons, the self-hosted Matter.js / three.js / GLTFLoader, the guest art, the pet's
     dragon models) is precached in a versioned cache
     (CACHE). Navigations to /, /index.html and the game links (/strike, /smash, ... /duel?...) answer from the cached index.html at once
     (stale-while-revalidate): the network copy is fetched in the background and, when it differs, the cache is updated and the pages are told
     ({ type: 'update' }), so they show "New version — tap to refresh".
   - A new sw.js (a new VERSION) installs in the background and waits; the page shows the same toast and sends { type: 'skip' } on the tap.
   - /tremorti/ is never touched (the network as before, fresh); Tremorti's own /tremorti/sw.js (scope /tremorti/) keeps working beside this one.
     Tremorti may also show its daily reminder through this registration (getRegistration() finds it first): a click on such a notification
     focuses an open Tremorti window or opens /tremorti/ (notificationclick below).
   - The CDN files (MediaPipe's tasks-vision bundle and wasm, the hand model, Google Fonts, the CDN fallbacks of Matter / three) are cached at
     run time, stale-while-revalidate; the big immutable ones (.wasm, the .task model: versioned URLs) are not re-downloaded once cached. */
const VERSION = 'grasp-2026-10-29e';
const CACHE = 'grasp-shell-' + VERSION, RUNTIME = 'grasp-runtime-v1';
const SHELL = ['/index.html', '/manifest.webmanifest', '/vendor/matter.min.js', '/vendor/three.min.js', '/vendor/GLTFLoader.js',
  '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-192.png', '/icons/icon-maskable-512.png', '/icons/apple-touch-icon.png', '/icons/favicon-32.png',
  '/icons/shortcut-strike.png', '/icons/shortcut-smash.png', '/icons/shortcut-shapes.png', '/icons/shortcut-camera.png',
  '/assets/guests/cow_in.png', '/assets/guests/cow_happy.png', '/assets/guests/cow_dizzy.png', '/assets/guests/cow_squash.png',
  '/assets/pet/Flying_Dragon.glb', '/assets/pet/Flying_Dragon_Evolved.glb'];
const GAME = /^\/(strike|smash|slice|busy|shapes|sandbox|frenzy|duel|drums|bubbles|paint|stars|animals|colors|peekaboo|feed|puzzle|sand|popit|spot|mix|quest|tachles|powder)\/?$/;
const CDN = ['cdn.jsdelivr.net', 'cdnjs.cloudflare.com', 'storage.googleapis.com', 'fonts.googleapis.com', 'fonts.gstatic.com'];
const IMMUTABLE = /\.(wasm|task)(\?|$)/;
let lastUpdate = 0; // when a new index.html was last cached (a page loaded before that runs the old one; it can ask)

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(SHELL.map((u) => new Request(u, { cache: 'reload' })));
    if (!self.registration.active) await self.skipWaiting(); // the very first install takes over at once (nothing older to replace)
  })());
});
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE && k !== RUNTIME && k.startsWith('grasp-')) await caches.delete(k); // the older versions' caches
    await self.clients.claim();
  })());
});
self.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.type === 'skip') self.skipWaiting();
  else if (d.type === 'version' && e.source) e.source.postMessage({ type: 'version', version: VERSION, cache: CACHE, updated: !!lastUpdate && lastUpdate > (+d.since || 0) });
});
async function tell(msg) { for (const c of await self.clients.matchAll({ includeUncontrolled: true, type: 'window' })) c.postMessage(msg); }
async function shell(e) { // the cached index.html now; the network copy in the background (an update is cached and announced)
  const c = await caches.open(CACHE), hit = await c.match('/index.html'), old = hit ? hit.clone() : null; // (cloned now: the page reads hit's body)
  const fresh = (async () => {
    try {
      const r = await fetch('/index.html', { cache: 'no-cache' }); if (!r.ok) return null;
      if (hit) { const [a, b] = await Promise.all([old.text(), r.clone().text()]); if (a === b) return r; await c.put('/index.html', r.clone()); lastUpdate = Date.now(); await tell({ type: 'update', version: VERSION }); }
      else await c.put('/index.html', r.clone());
      return r;
    } catch { return null; }
  })();
  if (hit) { e.waitUntil(fresh); return hit; }
  return (await fresh) || new Response('<!doctype html><meta charset="utf-8"><title>Grasp</title><p style="font:16px system-ui;padding:24px">Offline: open Grasp once online to install it.</p>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
async function cacheFirst(req, name) {
  const c = await caches.open(name), hit = await c.match(req, { ignoreSearch: name === CACHE });
  if (hit) return hit;
  const r = await fetch(req); if (r.ok) c.put(req, r.clone()).catch(() => {}); return r;
}
async function swr(e, req) { // stale-while-revalidate (an immutable big file: cached once, kept)
  const c = await caches.open(RUNTIME), hit = await c.match(req);
  const net = fetch(req).then((r) => { if (r.ok || r.type === 'opaque') c.put(req, r.clone()).catch(() => {}); return r; });
  if (hit) { if (!IMMUTABLE.test(req.url)) e.waitUntil(net.catch(() => {})); return hit; }
  return net;
}
self.addEventListener('fetch', (e) => {
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    const p = url.pathname;
    if (p.startsWith('/tremorti') || p === '/tremor' || p === '/sw.js' || p.startsWith('/_')) return; // Tremorti and the rest: the network as before
    if (p === '/' || p === '/index.html' || GAME.test(p)) { e.respondWith(shell(e)); return; }
    if (req.mode === 'navigate') { e.respondWith(fetch(req).catch(() => caches.open(CACHE).then((c) => c.match('/index.html')))); return; } // another page: the network, offline the start screen
    e.respondWith(cacheFirst(req, SHELL.includes(p) ? CACHE : RUNTIME).catch(() => Response.error()));
    return;
  }
  if (CDN.includes(url.hostname)) e.respondWith(swr(e, req));
});
self.addEventListener('notificationclick', (e) => { // Tremorti's reminder shown through this registration (or any other notification): back to its page
  e.notification.close();
  const d = e.notification.data || {}, tre = (e.notification.tag || '').startsWith('tremorti') || /tremorti/i.test(e.notification.title || ''), url = d.url || (tre ? '/tremorti/' : '/');
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    const open = list.find((c) => new URL(c.url).pathname.startsWith(new URL(url, self.location.origin).pathname) && (tre || !c.url.includes('/tremorti')));
    return open ? open.focus() : self.clients.openWindow(url);
  }));
});
