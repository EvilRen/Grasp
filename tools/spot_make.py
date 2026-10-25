#!/usr/bin/env python3
"""Spot the difference: make a scene's pictures and its answer key from ONE base image and a list of edits.

  python3 tools/spot_make.py tools/spot_specs/01.json            (one scene)
  python3 tools/spot_make.py tools/spot_specs/*.json             (all of them; then the index assets/spot/spot.json is rebuilt)

A spec (tools/spot_specs/<id>.json):
  { "id": "01", "src": "assets/spot/raw/01.png", "crop": [x0, y0, x1, y1] (fractions, optional: e.g. to cut Gemini's corner mark),
    "edits": [ { "lvl": 1, "do": "remove" | "recolor" | "flip" | "copy", "at": [cx, cy, rx, ry] (fractions of the cropped picture),
                 "hue": 120 (recolor: degrees), "to": [cx, cy] (copy: where the copy goes), "min_sat": 0.25 (recolor: only coloured pixels) } ] }
Levels are nested: level 1 = the edits with lvl 1 (3 big ones), level 2 = lvl <= 2 (5), level 3 = all (7).
Out: assets/spot/<id>/a.webp (the original) and l1.webp, l2.webp, l3.webp (the changed pictures), 1024 x 768; each difference's
hit circle (x, y, r as fractions of the width / height; r of the width) goes into assets/spot/spot.json."""
import json, sys, os, glob
import numpy as np
from PIL import Image
import cv2

OUT_W, OUT_H = 1024, 768
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(spec):
    im = Image.open(os.path.join(ROOT, spec['src'])).convert('RGB')
    if spec.get('crop'):
        x0, y0, x1, y1 = spec['crop']; w, h = im.size
        im = im.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)))
    return np.array(im.resize((OUT_W, OUT_H), Image.LANCZOS))

def ellipse_mask(cx, cy, rx, ry, feather=0):
    m = np.zeros((OUT_H, OUT_W), np.uint8)
    cv2.ellipse(m, (round(cx * OUT_W), round(cy * OUT_H)), (max(1, round(rx * OUT_W)), max(1, round(ry * OUT_H))), 0, 0, 360, 255, -1)
    if feather: m = cv2.GaussianBlur(m, (0, 0), feather)
    return m

def shape_mask(e, cx, cy, rx, ry, feather=0):
    if e.get('shape') != 'rect': return ellipse_mask(cx, cy, rx, ry, feather)
    m = np.zeros((OUT_H, OUT_W), np.uint8); x0, x1 = round((cx - rx) * OUT_W), round((cx + rx) * OUT_W); y0, y1 = round((cy - ry) * OUT_H), round((cy + ry) * OUT_H)
    r = max(2, min(x1 - x0, y1 - y0) // 4); cv2.rectangle(m, (x0 + r, y0), (x1 - r, y1), 255, -1); cv2.rectangle(m, (x0, y0 + r), (x1, y1 - r), 255, -1)
    for px, py in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(m, (px, py), r, 255, -1)
    if feather: m = cv2.GaussianBlur(m, (0, 0), feather)
    return m

def row_fill(img, hole):
    """each row of the hole: a straight blend from the colour just left of it to the colour just right of it (horizons, the sea's lines, stripes stay straight)"""
    out = img.astype(np.float32).copy(); src = cv2.GaussianBlur(img.astype(np.float32), (0, 0), 1.2); Hh, Ww = hole.shape
    ys = np.where(hole.any(axis=1))[0]
    for y in ys:
        row = hole[y] > 0; x = 0
        while x < Ww:
            if not row[x]: x += 1; continue
            x0 = x
            while x < Ww and row[x]: x += 1
            l, r = max(0, x0 - 3), min(Ww - 1, x + 2); n = x - x0
            t = (np.arange(n, dtype=np.float32) + 1) / (n + 1)
            out[y, x0:x] = src[y, l][None, :] * (1 - t[:, None]) + src[y, r][None, :] * t[:, None]
    return out

def blend(dst, src, m):
    a = (m.astype(np.float32) / 255.0)[..., None]
    return (dst.astype(np.float32) * (1 - a) + src.astype(np.float32) * a).round().clip(0, 255).astype(np.uint8)

def regrain(out, base, m):
    """put back the fine texture an inpaint smoothed away (the picture's own grain, from around the hole)"""
    k = cv2.GaussianBlur(base.astype(np.float32), (0, 0), 2.2); hi = base.astype(np.float32) - k   # the high frequencies
    ring = cv2.dilate(m, np.ones((41, 41), np.uint8)) & ~cv2.dilate(m, np.ones((9, 9), np.uint8))
    if ring.sum() == 0: return out
    v = hi[ring > 0]; sd = 1.4826 * np.median(np.abs(v - np.median(v, axis=0)), axis=0)  # (robust: the plain texture, not the outlines of things nearby)
    noise = np.random.default_rng(7).normal(0, 1, out.shape).astype(np.float32) * sd * 0.8
    noise = cv2.GaussianBlur(noise, (0, 0), 0.6)
    a = (m.astype(np.float32) / 255.0)[..., None]
    return (out.astype(np.float32) + noise * a).round().clip(0, 255).astype(np.uint8)

def apply(img, e):
    cx, cy, rx, ry = e['at']
    if e['do'] == 'remove':  # gone: the object filled in from its surroundings
        m = shape_mask(e, cx, cy, rx, ry); hole = cv2.dilate(m, np.ones((7, 7), np.uint8))
        known = (hole == 0).astype(np.float32); f = img.astype(np.float32)
        # only the background feeds the fill: not the outlines (dark) or the edges (sharp) of other things touching the hole
        g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1)
        grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); val = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)[..., 2]
        bad = cv2.dilate(((grad > e.get('edge', 60)) | (val < 90)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        known[bad] = 0
        # a smooth fill from the colours round the hole (normalized convolution: no streaks); near the rim a tight blur, inside a wide one
        def nc(sig): return cv2.GaussianBlur(f * known[..., None], (0, 0), sig) / np.maximum(cv2.GaussianBlur(known, (0, 0), sig)[..., None], 1e-4)
        R = max(rx * OUT_W, ry * OUT_H); near, far = nc(max(3, R * 0.12)), nc(max(8, R * 0.45))
        dist = cv2.distanceTransform(hole, cv2.DIST_L2, 5); w = np.clip(dist / max(4, R * 0.25), 0, 1)[..., None]
        fill = (near * (1 - w) + far * w)
        if e.get('fill') == 'rows': fill = row_fill(img, hole)  # (sky over sea, stripes: straight rows)
        fill = fill.clip(0, 255).astype(np.uint8)
        if e.get('inpaint'): fill = cv2.cvtColor(cv2.inpaint(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), hole, 9, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
        fill = regrain(fill, img, m)
        return blend(img, fill, cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)), (0, 0), 1.5)), (cx, cy, max(rx, ry * OUT_H / OUT_W))
    if e['do'] == 'recolor':  # another colour: only the coloured pixels turn (the outlines and the whites stay)
        m = ellipse_mask(cx, cy, rx, ry)
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.int32)
        sat = hsv[..., 1] / 255.0; val = hsv[..., 2] / 255.0
        sel = (m > 0) & (sat >= e.get('min_sat', 0.25)) & (val >= 0.2)
        if 'from' in e:  # (only one hue range: e.g. the red stripes of an umbrella, not its pole)
            h0, h1 = e['from']; hh = hsv[..., 0] * 2; sel &= ((hh >= h0) & (hh <= h1)) if h0 <= h1 else ((hh >= h0) | (hh <= h1))
        hsv[..., 0] = np.where(sel, (hsv[..., 0] + round(e['hue'] / 2)) % 180, hsv[..., 0])
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        soft = cv2.GaussianBlur((sel * 255).astype(np.uint8), (0, 0), 0.8)
        return blend(img, out, soft), (cx, cy, max(rx, ry * OUT_H / OUT_W))
    if e['do'] == 'flip':  # turned the other way
        x0, x1 = round((cx - rx) * OUT_W), round((cx + rx) * OUT_W); y0, y1 = round((cy - ry) * OUT_H), round((cy + ry) * OUT_H)
        out = img.copy(); out[y0:y1, x0:x1] = img[y0:y1, x0:x1][:, ::-1]
        m = ellipse_mask(cx, cy, rx * 0.98, ry * 0.98, feather=2)
        return blend(img, out, m), (cx, cy, max(rx, ry * OUT_H / OUT_W))
    if e['do'] == 'copy':  # one more: the object copied to another spot
        tx, ty = e['to']; dx, dy = round((tx - cx) * OUT_W), round((ty - cy) * OUT_H)
        shifted = np.roll(np.roll(img, dy, axis=0), dx, axis=1)
        m = ellipse_mask(tx, ty, rx, ry, feather=2)
        return blend(img, shifted, m), (tx, ty, max(rx, ry * OUT_H / OUT_W))
    raise ValueError(e['do'])

def make(path):
    spec = json.load(open(path)); sid = spec['id']; out = os.path.join(ROOT, 'assets', 'spot', sid); os.makedirs(out, exist_ok=True)
    base = load(spec); Image.fromarray(base).save(os.path.join(out, 'a.webp'), quality=84, method=6)
    levels = []
    for L in (1, 2, 3):
        img = base.copy(); diffs = []
        for e in spec['edits']:
            if e['lvl'] > L: continue
            img, (x, y, r) = apply(img, e)
            diffs.append({ 'x': round(x, 4), 'y': round(y, 4), 'r': round(max(r * 1.15, 0.045), 4), 'do': e['do'], 'what': e.get('what', '') })
        Image.fromarray(img).save(os.path.join(out, 'l%d.webp' % L), quality=84, method=6)
        levels.append({ 'img': 'l%d.webp' % L, 'diffs': diffs })
    want = [3, 5, 7]
    for i, L in enumerate(levels):
        if len(L['diffs']) != want[i]: print('  ! %s level %d has %d differences (want %d)' % (sid, i + 1, len(L['diffs']), want[i]))
    return { 'id': sid, 'name': spec.get('name', {}), 'w': OUT_W, 'h': OUT_H, 'a': 'a.webp', 'levels': levels }

def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'tools', 'spot_specs', '*.json')))
    idx_path = os.path.join(ROOT, 'assets', 'spot', 'spot.json')
    idx = json.load(open(idx_path)) if os.path.exists(idx_path) else { 'scenes': [] }
    by = { s['id']: s for s in idx['scenes'] }
    for p in paths: s = make(p); by[s['id']] = s; print('made', s['id'], [len(L['diffs']) for L in s['levels']])
    idx['scenes'] = [by[k] for k in sorted(by)]
    json.dump(idx, open(idx_path, 'w'), ensure_ascii=False, indent=1)
    print('index:', idx_path, len(idx['scenes']), 'scenes')

if __name__ == '__main__': main()
