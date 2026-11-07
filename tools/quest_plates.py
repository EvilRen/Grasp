"""Quest's interface plates: cut the one Gemini sheet (art/QUEST_GEMINI_PROMPTS.md) into the pieces the game loads.

    python3 tools/quest_plates.py art/quest_plates_raw.png [--check] [--only panel_quiet,window]

The sheet is a 3 x 3 grid. Each cell holds one plate, centred, with flat magenta (#FF00FF) everywhere else. Each
cell is cut at exact thirds, the magenta keyed to transparency, the plate trimmed to its own bounds and written as
a compressed .webp to assets/quest/plates/.

A plate is used at many sizes — a button is 180 px wide on one screen and 260 on another — so the game draws it as
a nine-slice: four corners kept, four edges stretched along one axis, the middle stretched both ways. That only
works if every bit of ornament sits in a border band of constant width, so this tool MEASURES each plate's band,
on each of its four sides, and writes the four insets to assets/quest/plates.json. The game reads that file. The
art states its own geometry; the code adapts. Nothing here is hard-coded to a number in index.html.

--check measures and writes nothing. Run it first. Two defects make a plate unusable, and both are invisible until
it is stretched in the game:
  * a silhouette whose top or bottom edge is CURVED across the middle (an oval rather than a rounded rectangle).
    The middle is what gets stretched, so a curve there is stretched with it and the piece reads as a lens.
  * ornament that creeps inward past the band, which gets smeared across the stretched middle.
A smooth gradient across the middle is NOT a defect: a nine-slice scales the middle, it does not tile it, so a
gradient scales with it and the edges still meet. The first version of the prompt asked for a flat middle on that
mistaken ground; measuring showed the panels' strong top-to-bottom gradient is harmless.

Needs Pillow; numpy is used when present and is only a speed-up. Nothing else in the repo depends on this file:
the game paints its own plates in code until these exist, and picks them up without a code change once they do.
"""
import json, os, sys

# the grid, in reading order: the name each cell is written out as
CELLS = [['btn_gold', 'btn_jade', 'btn_steel'],
         ['panel_quiet', 'panel_chosen', 'panel_locked'],
         ['plaque', 'window', 'nameplate']]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'plates')
LAY = os.path.join(ROOT, 'assets', 'quest', 'plates.json')
KEY_T = 70        # how far the magenta score (min(r-g, b-g)) must reach for a pixel to be a hole
CORE = 0.62       # below KEY_T * CORE a pixel is fully a hole; above it, it fades out
EDGE = 8          # px of each cell ignored: Gemini tends to draw the cell boundaries in as thin dark lines
FLAT = 6          # px a silhouette's top edge may vary across its middle 60% before it counts as curved


def load(path):
    from PIL import Image
    return Image.open(path).convert('RGB')


def score(im):
    """The magenta score per pixel: high where the background is, low on the plate."""
    try:
        import numpy as np
        a = np.asarray(im).astype(np.int16)
        return np.minimum(a[:, :, 0] - a[:, :, 1], a[:, :, 2] - a[:, :, 1])
    except ImportError:
        raise SystemExit('numpy is needed to measure the sheet (pip install numpy)')


def bounds(solid, np):
    """The plate's own box inside a cell, ignoring specks and the drawn-in grid lines."""
    rows, cols = solid.mean(1) > 0.06, solid.mean(0) > 0.06
    if not rows.any() or not cols.any():
        return None
    y = np.where(rows)[0]
    x = np.where(cols)[0]
    return int(x[0]), int(y[0]), int(x[-1]) + 1, int(y[-1]) + 1


def flatness(solid, np):
    """How much the silhouette's top and bottom edges rise and fall across the middle 60% of the width."""
    h, w = solid.shape
    out = []
    for edge in (0, 1):
        at = []
        for x in range(int(w * 0.20), int(w * 0.80)):
            col = np.where(solid[:, x])[0]
            if len(col):
                at.append(col[0] if edge == 0 else h - 1 - col[-1])
        out.append(int(max(at) - min(at)) if at else 999)
    return out


def band(rgb, solid, np):
    """The border band's thickness on each side: scan in from the edge along the plate's own centre line and stop
    where the surface stops changing — the ornament is busy, the inner face is calm."""
    h, w = solid.shape
    lum = rgb.astype(float).mean(2)
    def run(vals):
        d = np.abs(np.diff(vals))
        if len(d) < 8:
            return 0
        quiet = max(2.0, float(np.median(d[len(d) // 3: 2 * len(d) // 3])) * 3 + 1.5)
        calm = 0
        for i, v in enumerate(d):
            calm = calm + 1 if v <= quiet else 0
            if calm >= max(6, len(d) // 25):        # a stretch of calm pixels: the inner face has started
                return max(0, i - calm + 1)
        return len(d) // 6
    row, col = lum[h // 2], lum[:, w // 2]
    return {'l': run(row), 'r': run(row[::-1]), 't': run(col), 'b': run(col[::-1])}


def cut(im, sc, ry, rx, np):
    """One cell: the plate's pixels, its alpha, and everything measured about it."""
    H, W = sc.shape
    ch, cw = H // 3, W // 3
    y0, x0 = ry * ch + EDGE, rx * cw + EDGE
    cell_s = sc[y0:(ry + 1) * ch - EDGE, x0:(rx + 1) * cw - EDGE]
    solid = ~(cell_s > KEY_T)
    bb = bounds(solid, np)
    if bb is None:
        return None
    bx0, by0, bx1, by1 = bb
    import numpy as _np
    rgb = _np.asarray(im).astype(_np.int16)[y0 + by0:y0 + by1, x0 + bx0:x0 + bx1]
    s = cell_s[by0:by1, bx0:bx1]
    # alpha: fully opaque below KEY_T * CORE, fading to clear at KEY_T, so the keyed edge is not a hard stair
    al = _np.clip((KEY_T - s) / max(1e-6, KEY_T * (1 - CORE)), 0, 1)
    sol = s <= KEY_T
    return {'rgb': rgb, 'a': al, 'solid': sol,
            'w': int(bx1 - bx0), 'h': int(by1 - by0),
            'flat': flatness(sol, _np), 'band': band(rgb, sol, _np)}


def despill(rgb, a, np):
    """Pull the magenta back out of the half-covered pixels at the plate's edge."""
    r, g, b = rgb[:, :, 0].astype(float), rgb[:, :, 1].astype(float), rgb[:, :, 2].astype(float)
    over = np.minimum(r, b) - g
    k = (over > 10) & (a > 0.15)
    cap = g + 10
    r = np.where(k, np.minimum(r, cap), r)
    b = np.where(k, np.minimum(b, cap), b)
    return np.stack([r, g, b], 2)


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    flags = [x for x in sys.argv[1:] if x.startswith('--')]
    if not args:
        raise SystemExit(__doc__)
    only = None
    for f in flags:
        if f.startswith('--only'):
            only = set(f.split('=', 1)[1].split(',')) if '=' in f else None
    check = '--check' in flags
    import numpy as np
    from PIL import Image
    im = load(args[0])
    sc = score(im)
    print('sheet %d x %d' % im.size)
    print('%-13s %-11s %-7s %-26s %s' % ('piece', 'size', 'ratio', 'border l/r/t/b', 'top/bottom edge'))
    lay, files = {}, []
    for ry in range(3):
        for rx in range(3):
            name = CELLS[ry][rx]
            if only and name not in only:
                continue
            c = cut(im, sc, ry, rx, np)
            if not c:
                print('%-13s EMPTY' % name)
                continue
            w, h, bd = c['w'], c['h'], c['band']
            ft, fb = c['flat']
            ok = ft <= FLAT and fb <= FLAT
            print('%-13s %4dx%-6d %-7.2f l%-4d r%-4d t%-4d b%-4d      %s' % (
                name, w, h, w / h, bd['l'], bd['r'], bd['t'], bd['b'],
                'flat (%d/%d px)' % (ft, fb) if ok else 'CURVED (%d/%d px) — will not stretch' % (ft, fb)))
            lay[name] = {'w': w, 'h': h, 'ins': [bd['l'], bd['r'], bd['t'], bd['b']], 'flat': bool(ok)}
            if check:
                continue
            px = despill(c['rgb'], c['a'], np)
            out = np.concatenate([np.clip(px, 0, 255), (c['a'] * 255)[:, :, None]], 2).astype('uint8')
            os.makedirs(OUT, exist_ok=True)
            p = os.path.join(OUT, name + '.webp')
            Image.fromarray(out, 'RGBA').save(p, 'WEBP', quality=92, method=6)
            files.append((name, os.path.getsize(p)))
    if check:
        print('\n--check: nothing written.')
        return
    with open(LAY, 'w') as f:
        json.dump(lay, f, indent=1, sort_keys=True)
    print('\nwrote %s' % os.path.relpath(LAY, ROOT))
    for n, sz in files:
        print('  %-13s %6.1f KB' % (n, sz / 1024))
    print('  %-13s %6.1f KB total' % ('', sum(s for _, s in files) / 1024))


if __name__ == '__main__':
    main()
