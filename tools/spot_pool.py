#!/usr/bin/env python3
"""Spot the difference: a POOL of differences per scene, so every game is a new mix (the owner, Oct 2026: "at least 30 versions per picture").

  python3 tools/spot_pool.py                      (every scene in assets/spot/spot.json; run tools/spot_make.py first)
  python3 tools/spot_pool.py 06 07 --sheets DIR   (some scenes; DIR gets a review sheet per scene: each candidate before / after, by id)

Candidates, found automatically on the scene's original picture (assets/spot/<id>/a.webp), plus the 7 hand-made edits of its spec:
  r  recolor: a flat-coloured area (a shirt, a balloon, a roof) turns another hue. Found by flood-filling the picture's flat regions between
     its outlines; the hue is chosen far from the old one and from the colours around it.
  x  remove: a small thing on a plain background (a flower, a bird, a cloud) is filled in from its surroundings. Found as what a wide median
     blur takes away, kept only when the ring round it is plain.
  c  copy: one more of such a thing, a little to the side, where the background is the same and nothing else is.
  h  the spec's own edits (kept as they are: they were checked by eye).
A candidate the review rejected goes in the spec's "pool_skip" (its id: kind + x, y in thousandths, e.g. "r412_655").
Each candidate is rendered alone on the original; what changed is cut out as an RGBA patch and packed into assets/spot/<id>/p.webp. In
spot.json the scene gets "atlas" and "pool": [{ id, x, y, r, t (1 big, 2 medium, 3 small), what, do, p: [ax, ay, w, h] (in the atlas),
o: [px, py] (where it goes on the 1024 x 768 picture) }]. The game picks 3 / 5 / 7 of them that do not overlap and lays them on the original."""
import json, sys, os, glob, math
import numpy as np
from PIL import Image, ImageDraw
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spot_make as SM

W, H = SM.OUT_W, SM.OUT_H
ROOT = SM.ROOT

def hue_dist(a, b): d = abs(a - b) % 360; return min(d, 360 - d)

def region_at(img, pts):
    """the flat region(s) under the given points (fractions): for a hand-picked recolor ("pool_add": { "do": "recolor", "pt": [[x, y], ..] })"""
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR); f = cv2.pyrMeanShiftFiltering(bgr, 5, 14)
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); val = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[..., 2]
    mask = np.zeros((H + 2, W + 2), np.uint8); mask[1:-1, 1:-1] = (val < 70).astype(np.uint8)  # (only the dark outlines are walls: the fill is held to the seed's colour)
    for x, y in pts:
        px, py = min(W - 1, round(x * W)), min(H - 1, round(y * H))
        if mask[py + 1, px + 1]:  # (on an outline: the nearest open pixel)
            ys, xs = np.where(mask[max(1, py - 7) + 1:py + 9, max(1, px - 7) + 1:px + 9] == 0)
            if not len(xs): continue
            j = np.argmin((ys - (py - max(1, py - 7))) ** 2 + (xs - (px - max(1, px - 7))) ** 2); px, py = max(1, px - 7) + xs[j], max(1, py - 7) + ys[j]
        if mask[py + 1, px + 1]: continue
        for tol in (34, 24, 16, 10):  # (against the seed's colour; a fill that leaks into the background is retried tighter)
            mm = mask.copy(); n = cv2.floodFill(f, mm, (int(px), int(py)), 0, (tol,) * 3, (tol,) * 3, 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (2 << 8))[0]
            if n <= W * H * 0.03: mask = mm; break
    return ((mask[1:-1, 1:-1] == 2) * 255).astype(np.uint8)

def recolor_region(img, m, hue=None):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32); hh = hsv[..., 0] * 2
    ang = np.deg2rad(hh[m > 0]); mh = (math.degrees(math.atan2(np.sin(ang).mean(), np.cos(ang).mean())) + 360) % 360
    if hue is None:
        rg = ring_of(m, 25, 5); rs = hsv[..., 1][rg] / 255; rh_ = hh[rg][rs > 0.25]; ringh = None
        if len(rh_) > 50: a2 = np.deg2rad(rh_); ringh = (math.degrees(math.atan2(np.sin(a2).mean(), np.cos(a2).mean())) + 360) % 360
        hue = max((120, 150, 180, 210, 240), key=lambda sh: min(hue_dist((mh + sh) % 360, mh), hue_dist((mh + sh) % 360, ringh) if ringh is not None else 180) - (30 if 45 <= (mh + sh) % 360 <= 70 else 0))
    return apply_recolor(img, { 'mask': m, 'mh': mh, 'hue': hue })

def regions(img):
    """the picture's flat regions: flood fills between the outlines (dark or sharp pixels are walls)"""
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR); f = cv2.pyrMeanShiftFiltering(bgr, 5, 14)
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); val = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[..., 2]
    wall = ((val < 75) | (grad > 110)).astype(np.uint8)
    mask = np.zeros((H + 2, W + 2), np.uint8); mask[1:-1, 1:-1] = wall
    out = []
    for y in range(2, H - 2, 4):
        for x in range(2, W - 2, 4):
            if mask[y + 1, x + 1]: continue
            n, _, _, rect = cv2.floodFill(f, mask, (x, y), 0, (5, 5, 5), (5, 5, 5), 4 | cv2.FLOODFILL_MASK_ONLY | (2 << 8))
            rx, ry, rw, rh = rect; sub = mask[ry + 1:ry + rh + 1, rx + 1:rx + rw + 1]; reg = sub == 2; sub[reg] = 1
            if n >= 600: out.append((rx, ry, rw, rh, reg.copy(), n))
    return out

def ring_of(m, a, b): return (cv2.dilate(m, np.ones((a, a), np.uint8)) > 0) & ~(cv2.dilate(m, np.ones((b, b), np.uint8)) > 0)

def recolor_cands(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32); hh = hsv[..., 0] * 2; ss = hsv[..., 1] / 255; vv = hsv[..., 2] / 255
    out = []
    for rx, ry, rw, rh, reg, n in regions(img):
        if not (W * H * 0.0012 <= n <= W * H * 0.035): continue
        if rx <= 1 or ry <= 1 or rx + rw >= W - 1 or ry + rh >= H - 1: continue  # (touching the edge: sky, grass, a wall)
        if n / (rw * rh) < 0.28 or max(rw, rh) > 260: continue  # (a thin band or a sprawling one: not a thing)
        m = np.zeros((H, W), np.uint8); m[ry:ry + rh, rx:rx + rw][reg] = 255
        s, v = ss[m > 0], vv[m > 0]
        if np.median(s) < 0.32 or np.median(v) < 0.3: continue
        h = hh[m > 0]; ang = np.deg2rad(h); mh = (math.degrees(math.atan2(np.sin(ang).mean(), np.cos(ang).mean())) + 360) % 360
        conc = math.hypot(np.sin(ang).mean(), np.cos(ang).mean())
        if conc < 0.9: continue  # (several hues: a gradient or a patterned area)
        ms, mv = float(np.median(s)), float(np.median(v))
        if 65 <= mh <= 170: continue  # (greens: grass, trees, hills are the background in these pictures)
        if (mh < 48 or mh > 345) and (ms < 0.55 or mv < 0.62) and not mh > 345: continue  # (browns, skin: trunks, faces)
        rg = ring_of(m, 25, 5); rs = ss[rg]; rh_ = hh[rg][rs > 0.25]
        ringh = None
        if len(rh_) > 50: a2 = np.deg2rad(rh_); ringh = (math.degrees(math.atan2(np.sin(a2).mean(), np.cos(a2).mean())) + 360) % 360
        best, bs = None, -1
        for sh in (120, 150, 180, 210, 240):
            nh = (mh + sh) % 360; sc = min(hue_dist(nh, mh), hue_dist(nh, ringh) if ringh is not None else 180)
            if 45 <= nh <= 70: sc -= 30  # (a yellow that turns ochre on dark colours)
            if sc > bs: best, bs = sh, sc
        if bs < 70: continue
        ys, xs = np.where(m > 0); cx, cy = xs.mean() / W, ys.mean() / H
        out.append({ 'kind': 'r', 'do': 'recolor', 'mask': m, 'hue': best, 'mh': mh, 'cx': cx, 'cy': cy, 'n': n })
    return out

def apply_recolor(img, c):
    """the region and its anti-aliased rim (same hue, coloured) turn by c['hue']"""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.int32); hh = hsv[..., 0] * 2; s = hsv[..., 1] / 255; v = hsv[..., 2] / 255
    near = cv2.dilate(c['mask'], np.ones((5, 5), np.uint8)) > 0
    d = np.abs(((hh - c['mh']) + 180) % 360 - 180)
    sel = (c['mask'] > 0) | (near & (d < 35) & (s > 0.12) & (v > 0.15))
    hsv[..., 0] = np.where(sel, (hsv[..., 0] + round(c['hue'] / 2)) % 180, hsv[..., 0])
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return SM.blend(img, out, cv2.GaussianBlur((sel * 255).astype(np.uint8), (0, 0), 0.7))

def object_cands(img):
    """small things on a plain background: what a wide median blur takes away, with a plain ring round it"""
    bg = cv2.medianBlur(img, 61); diff = np.abs(img.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    obj = (diff > 38).astype(np.uint8); obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(obj, 8)
    lab_f = img.astype(np.float32); out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if not (W * H * 0.0004 <= a <= W * H * 0.012) or max(w, h) > 150 or x < 6 or y < 6 or x + w > W - 6 or y + h > H - 6: continue
        m = (lab == i).astype(np.uint8) * 255; m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); m = np.zeros_like(m); cv2.drawContours(m, cs, -1, 255, -1)  # (holes filled)
        rg = ring_of(m, 31, 9)
        if obj[rg].mean() > 0.06: continue  # (other things right next to it)
        if lab_f[rg].std(axis=0).max() > 16: continue  # (not a plain background)
        out.append({ 'kind': 'x', 'mask': m, 'cx': (x + w / 2) / W, 'cy': (y + h / 2) / H, 'bw': w, 'bh': h, 'n': int(a), 'ringc': lab_f[rg].mean(axis=0), 'obj': obj })
    return out

def apply_remove(img, c):
    m = cv2.dilate(c['mask'], np.ones((5, 5), np.uint8))
    e = { 'do': 'remove', '_mask': m, 'at': [c['cx'], c['cy'], (c['bw'] / 2 + 4) / W, (c['bh'] / 2 + 4) / H] }
    return SM.apply(img, e)[0]

def copy_spot(img, c):
    """where one more of it fits: a few sizes to the side, the same plain background, nothing else there"""
    f = img.astype(np.float32); obj = c['obj']; bw, bh = c['bw'], c['bh']; x0, y0 = round(c['cx'] * W - bw / 2), round(c['cy'] * H - bh / 2)
    for k in (1.6, 2.2, 2.9):
        for ang in (0, 180, 45, 135, 225, 315, 90, 270):
            dx, dy = round(math.cos(math.radians(ang)) * bw * k), round(math.sin(math.radians(ang)) * bh * k)
            tx, ty = x0 + dx, y0 + dy; pad = 16
            if tx - pad < 6 or ty - pad < 6 or tx + bw + pad > W - 6 or ty + bh + pad > H - 6: continue
            win = (slice(ty - pad, ty + bh + pad), slice(tx - pad, tx + bw + pad))
            if obj[win].mean() > 0.01: continue
            if f[win].std(axis=(0, 1)).max() > 14 or np.abs(f[win].mean(axis=(0, 1)) - c['ringc']).max() > 14: continue
            return dx, dy
    return None

def apply_copy(img, c, dx, dy):
    m = cv2.GaussianBlur(cv2.dilate(c['mask'], np.ones((3, 3), np.uint8)), (0, 0), 1.0)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    src = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE); mm = cv2.warpAffine(m, M, (W, H))
    return SM.blend(img, src, mm)

def cid(kind, x, y): return '%s%03d_%03d' % (kind, round(x * 1000), round(y * 1000))

def build(sid, sheets=None):
    spec_p = os.path.join(ROOT, 'tools', 'spot_specs', sid + '.json'); spec = json.load(open(spec_p)); skip = set(spec.get('pool_skip', []))
    base = SM.load(spec); cands = []
    for e in spec['edits']:  # the hand-made ones
        out, (x, y, r) = SM.apply(base.copy(), e); cands.append({ 'id': cid('h', x, y), 'img': out, 'do': e['do'], 'what': e.get('what', ''), 't': e['lvl'] })
    for e in spec.get('pool_add', []):  # hand-picked extras (their size class comes from the area they change)
        if 'pt' in e:
            m = region_at(base, e['pt'])
            if m.sum() < 255 * 150: print('  ! nothing under', e['pt']); continue
            out = recolor_region(base, m, e.get('hue'))
        else: out = SM.apply(base.copy(), e)[0]
        cands.append({ 'id': cid('a', *(e['pt'][0] if 'pt' in e else e['to'] if e['do'] == 'copy' else e['at'][:2])), 'img': out, 'do': e['do'], 'what': e.get('what', '') })
    for c in recolor_cands(base):
        cands.append({ 'id': cid('r', c['cx'], c['cy']), 'img': apply_recolor(base, c), 'do': 'recolor', 'what': '' })
    for c in object_cands(base):
        cands.append({ 'id': cid('x', c['cx'], c['cy']), 'img': apply_remove(base, c), 'do': 'remove', 'what': '' })
        cp = copy_spot(base, c)
        if cp: cands.append({ 'id': cid('c', c['cx'] + cp[0] / W, c['cy'] + cp[1] / H), 'img': apply_copy(base, c, *cp), 'do': 'copy', 'what': '' })
    pool, seen = [], []
    for c in cands:
        d = np.abs(c['img'].astype(np.int16) - base.astype(np.int16)).max(axis=2) > 6
        d = cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        ys, xs = np.where(d > 0)
        if len(xs) < 150: print('  - too small', c['id'], len(xs)); continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        cx, cy = (x0 + x1) / 2 / W, (y0 + y1) / 2 / H
        strong = np.abs(c['img'].astype(np.int16) - base.astype(np.int16)).sum(axis=2) > 30; sy, sx = np.where(strong)  # (the circle holds what a tap would look for)
        dd = np.hypot(sx - cx * W, sy - cy * H) if len(sx) else np.array([max(x1 - x0, y1 - y0) / 2])
        r = max(0.045, float(np.percentile(dd, 99.5)) * 1.06 / W)
        if any(math.hypot((cx - p['x']) * W, (cy - p['y']) * H) < 0.25 * (r + p['r']) * W and max(r, p['r']) < 1.6 * min(r, p['r']) for p in seen): print('  - same spot', c['id']); continue  # (the same spot again)
        area = len(xs) / (W * H); t = c.get('t') or (1 if area >= 0.006 else 2 if area >= 0.0022 else 3)
        a = (cv2.dilate(d, np.ones((5, 5), np.uint8)) * 255)[y0:y1, x0:x1]
        x0, y0 = max(0, x0 - 2), max(0, y0 - 2); x1, y1 = min(W, x1 + 2), min(H, y1 + 2)
        a = (cv2.dilate(d, np.ones((5, 5), np.uint8)) * 255)[y0:y1, x0:x1]
        rgba = np.dstack([c['img'][y0:y1, x0:x1], a])
        p = { 'id': c['id'], 'x': round(cx, 4), 'y': round(cy, 4), 'r': round(r, 4), 't': t, 'do': c['do'], 'what': c['what'], 'o': [int(x0), int(y0)], '_rgba': rgba, '_img': c['img'] }
        seen.append(p)
        if c['id'] not in skip: pool.append(p)
    # the atlas: shelves, 1024 wide
    pool.sort(key=lambda p: -p['_rgba'].shape[0]); X = Y = sh = 0; AW = 1024
    for p in pool:
        h, w = p['_rgba'].shape[:2]
        if X + w > AW: X, Y, sh = 0, Y + sh + 1, 0
        p['p'] = [X, Y, w, h]; X += w + 1; sh = max(sh, h)
    AH = Y + sh; atlas = np.zeros((max(1, AH), AW, 4), np.uint8)
    for p in pool: X, Y, w, h = p['p']; atlas[Y:Y + h, X:X + w] = p['_rgba']
    out = os.path.join(ROOT, 'assets', 'spot', sid); Image.fromarray(atlas, 'RGBA').save(os.path.join(out, 'p.webp'), quality=86, method=6)
    if sheets: sheet(sid, base, seen, skip, sheets)
    pool.sort(key=lambda p: p['id'])
    return [{ k: v for k, v in p.items() if not k.startswith('_') } for p in pool], len(seen)

def sheet(sid, base, cands, skip, d):
    os.makedirs(d, exist_ok=True); cw, chh, cols = 300, 150, 6
    rows = math.ceil(len(cands) / cols); im = Image.new('RGB', (cols * cw, rows * (chh + 18)), (30, 30, 40)); dr = ImageDraw.Draw(im)
    for i, p in enumerate(sorted(cands, key=lambda p: p['id'])):
        R = max(40, p['r'] * W * 1.5); x, y = p['x'] * W, p['y'] * H; box = (int(x - R * 1.33), int(y - R), int(x + R * 1.33), int(y + R))
        a = Image.fromarray(base).crop(box).resize((cw // 2 - 2, chh)); b = Image.fromarray(p['_img']).crop(box).resize((cw // 2 - 2, chh))
        gx, gy = (i % cols) * cw, (i // cols) * (chh + 18); im.paste(a, (gx, gy + 18)); im.paste(b, (gx + cw // 2, gy + 18))
        dr.text((gx + 4, gy + 3), '%s t%d %s%s' % (p['id'], p['t'], p['do'], ' SKIP' if p['id'] in skip else ''), fill=(255, 120, 120) if p['id'] in skip else (255, 255, 255))
    im.save(os.path.join(d, 'pool_%s.png' % sid))

def main():
    args = [a for a in sys.argv[1:]]; sheets = None
    if '--sheets' in args: i = args.index('--sheets'); sheets = args[i + 1]; del args[i:i + 2]
    idx_p = os.path.join(ROOT, 'assets', 'spot', 'spot.json'); idx = json.load(open(idx_p))
    for s in idx['scenes']:
        if args and s['id'] not in args: continue
        pool, n = build(s['id'], sheets); s['atlas'] = 'p.webp'; s['pool'] = pool
        print(s['id'], 'pool', len(pool), 'of', n, 'by size', [sum(1 for p in pool if p['t'] == t) for t in (1, 2, 3)])
    json.dump(idx, open(idx_p, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__': main()
