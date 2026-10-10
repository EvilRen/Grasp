"""Draws Grasp's app icons (PWA manifest, Apple touch icon, shortcuts) in headless Chromium and saves them as PNGs in icons/.
   python3 art/make_icons.py   (needs playwright + chromium; no network)"""
import asyncio, base64, os
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'icons')
JS = r"""
const HAND = 'M44 118 L36 96 L36 84 L13 60 Q6 52 13 47 Q19 43 25 50 L36 62 L36 30 Q36 22 42 22 Q48 22 48 30 L48 66 L51 66 L51 14 Q51 6 57 6 Q63 6 63 14 L63 66 L66 66 L66 20 Q66 12 72 12 Q78 12 78 20 L78 68 L81 68 L81 38 Q81 31 86.5 31 Q92 31 92 38 L92 96 L84 118 Z';
function bg(g, S, round) {
  const q = g.createLinearGradient(0, 0, S, S); q.addColorStop(0, '#2c3a7c'); q.addColorStop(1, '#121833');
  g.beginPath(); if (round) g.roundRect(0, 0, S, S, S * 0.22); else g.rect(0, 0, S, S); g.fillStyle = q; g.fill();
  const r = g.createRadialGradient(S * 0.3, S * 0.25, 0, S * 0.3, S * 0.25, S * 0.8); r.addColorStop(0, 'rgba(169,139,255,0.35)'); r.addColorStop(1, 'rgba(169,139,255,0)'); g.fillStyle = r; g.fill();
}
function ballAt(g, x, y, R, only) { // only: 'lines' (the speed lines) / 'ball' / both
  g.save(); g.lineCap = 'round'; if (only !== 'ball')
  for (const [dy, len, a] of [[-0.45, 1.5, 0.5], [0, 2.1, 0.7], [0.45, 1.4, 0.5]]) { const q = g.createLinearGradient(x - R * len - R, 0, x, 0); q.addColorStop(0, 'rgba(255,194,75,0)'); q.addColorStop(1, 'rgba(255,214,120,' + a + ')'); g.strokeStyle = q; g.lineWidth = R * 0.28; g.beginPath(); g.moveTo(x - R * len - R * 0.6, y + dy * R); g.lineTo(x - R * 0.7, y + dy * R); g.stroke(); }
  if (only === 'lines') { g.restore(); return; }
  g.shadowColor = 'rgba(255,140,60,0.7)'; g.shadowBlur = R * 0.6;
  const q = g.createRadialGradient(x - R * 0.35, y - R * 0.4, R * 0.08, x, y, R); q.addColorStop(0, '#fff3b8'); q.addColorStop(0.45, '#ffc24b'); q.addColorStop(1, '#ff6f59');
  g.beginPath(); g.arc(x, y, R, 0, Math.PI * 2); g.fillStyle = q; g.fill(); g.shadowBlur = 0;
  g.fillStyle = 'rgba(255,255,255,0.7)'; g.beginPath(); g.ellipse(x - R * 0.38, y - R * 0.42, R * 0.28, R * 0.14, -0.7, 0, Math.PI * 2); g.fill(); g.restore();
}
function hand(g, x, y, s, rot) { g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s); g.translate(-52, -62); const p = new Path2D(HAND);
  g.shadowColor = 'rgba(0,0,0,0.35)'; g.shadowBlur = 6; g.fillStyle = '#f1e9da'; g.fill(p); g.shadowBlur = 0; g.lineWidth = 4; g.strokeStyle = '#c9b89a'; g.stroke(p); g.restore(); }
function logo(g, S, k) { // k: the content's scale (maskable icons keep it in the safe zone)
  g.save(); g.translate(S / 2, S / 2); g.scale(k, k); g.translate(-S / 2, -S / 2);
  ballAt(g, S * 0.68, S * 0.34, S * 0.16, 'lines'); hand(g, S * 0.4, S * 0.6, S / 150, -0.28); ballAt(g, S * 0.68, S * 0.34, S * 0.16, 'ball'); g.restore();
}
function shortcut(g, S, kind) {
  bg(g, S, true); const c = S / 2;
  if (kind === 'strike') ballAt(g, c + S * 0.1, c, S * 0.22);
  else if (kind === 'smash') { for (let r = 0; r < 4; r++) for (let i = 0; i < 3; i++) { const w = S * 0.2, h = S * 0.11, x = S * 0.2 + i * w + (r % 2 ? w / 2 : 0), y = S * 0.28 + r * h; if (x + w > S * 0.85) continue; g.fillStyle = r % 2 ? '#d9573c' : '#f07a50'; g.fillRect(x + 1, y + 1, w - 2, h - 2); } }
  else if (kind === 'shapes') { g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? S * 0.14 : S * 0.32; g.lineTo(c + Math.cos(a) * r, c + Math.sin(a) * r); } g.closePath(); g.fillStyle = '#ffc24b'; g.fill(); g.lineWidth = S * 0.03; g.strokeStyle = '#b8730f'; g.stroke(); }
  else { g.fillStyle = '#a98bff'; g.beginPath(); g.roundRect(S * 0.18, S * 0.32, S * 0.64, S * 0.44, S * 0.08); g.fill(); g.fillRect(S * 0.36, S * 0.24, S * 0.28, S * 0.12); g.beginPath(); g.arc(c, S * 0.54, S * 0.14, 0, Math.PI * 2); g.fillStyle = '#1d2547'; g.fill(); g.beginPath(); g.arc(c, S * 0.54, S * 0.08, 0, Math.PI * 2); g.fillStyle = '#54c6eb'; g.fill(); }
}
window.make = (S, kind) => { const c = document.createElement('canvas'); c.width = c.height = S; const g = c.getContext('2d');
  if (kind === 'any') { bg(g, S, true); logo(g, S, 1); } else if (kind === 'maskable' || kind === 'apple') { bg(g, S, false); logo(g, S, kind === 'maskable' ? 0.78 : 0.92); } else shortcut(g, S, kind);
  return c.toDataURL('image/png'); };
"""
async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); page = await b.new_page(); await page.set_content('<html><body></body></html>'); await page.evaluate(JS)
        for name, S, kind in [('icon-192.png', 192, 'any'), ('icon-512.png', 512, 'any'), ('icon-maskable-512.png', 512, 'maskable'), ('icon-maskable-192.png', 192, 'maskable'), ('apple-touch-icon.png', 180, 'apple'),
                              ('shortcut-strike.png', 96, 'strike'), ('shortcut-smash.png', 96, 'smash'), ('shortcut-shapes.png', 96, 'shapes'), ('shortcut-camera.png', 96, 'camera'), ('favicon-32.png', 32, 'any')]:
            url = await page.evaluate(f"make({S}, '{kind}')")
            open(os.path.join(OUT, name), 'wb').write(base64.b64decode(url.split(',', 1)[1])); print('wrote icons/' + name)
        await b.close()
asyncio.run(main())
