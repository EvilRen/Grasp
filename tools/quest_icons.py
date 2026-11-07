"""Quest's relic pictures: cut the one Gemini sheet (art/QUEST_GEMINI_PROMPTS.md) into the files the game loads.

    python3 tools/quest_icons.py art/quest_relics_raw.jpg [--check] [--only heart,pot]

The sheet holds eighteen objects in three rows of six, on flat magenta (#FF00FF). The objects are FOUND rather
than cut at fixed sixths — the generator does not centre an object in its cell, and the plates sheet taught what
that costs: cut at fixed fractions, a piece comes out with a slice of its neighbour attached, which is invisible
in the file and obvious in the game. So the magenta is keyed, the sheet split into bands of rows that hold
anything, each band into runs of columns, and each object trimmed to its own bounds and written as a compressed
.webp to assets/quest/relics/.

--check measures and writes nothing. It reports each object's size and, for every one, how much of it survives at
18 px — the size the top bar draws a relic at when the player holds a collection. That number is the whole test:
the first icon sheet looked superb on screen and went to mush at the size the game actually uses, and nothing but
rendering it small says so.

Needs Pillow and numpy.
"""
import os
import sys

# three rows of six, in reading order; these are the keys of RELICS in index.html
NAMES = [['heart', 'book', 'core', 'clover', 'boot', 'whet'],
         ['pot', 'lantern', 'bag', 'feather', 'snail', 'thorn'],
         ['tea', 'map', 'star', 'magnet', 'egg', 'venom']]
COLS, ROWS = 6, 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'relics')
KEY_T = 70        # how far the magenta score (min(r-g, b-g)) must reach for a pixel to be a hole
CORE = 0.62       # below KEY_T * CORE a pixel is fully a hole; above it, it fades out
LINE = 4          # px masked either side of each cell boundary: the generator draws the boundaries in as thin lines
SMALL = 18        # the size the check renders each object at


def score(im, np):
    a = np.asarray(im).astype(np.int16)
    return np.minimum(a[:, :, 0] - a[:, :, 1], a[:, :, 2] - a[:, :, 1])


def delines(sc, np):
    """Blank the thin lines drawn along the cell boundaries; left alone they join every object into one band."""
    H, W = sc.shape
    sc = sc.copy()
    for i in range(1, COLS):
        x = W * i // COLS
        sc[:, max(0, x - LINE):x + LINE] = 255
    for i in range(1, ROWS):
        y = H * i // ROWS
        sc[max(0, y - LINE):y + LINE, :] = 255
    return sc


def runs(mask, gap=10, least=40):
    """The runs of true in a 1-D mask, bridging gaps shorter than `gap` and dropping anything under `least`."""
    out, start, blank = [], None, 0
    for i, v in enumerate(mask):
        if v:
            if start is None:
                start = i
                if out and i - out[-1][1] <= gap:
                    start = out.pop()[0]
            blank = 0
        else:
            blank += 1
            if start is not None and blank > gap:
                out.append((start, i - blank + 1)); start = None
    if start is not None:
        out.append((start, len(mask)))
    return [(a, b) for a, b in out if b - a >= least]


def find(sc, np):
    """Where the objects actually are: bands of rows that hold anything, then runs of columns inside each band."""
    solid = ~(sc > KEY_T)
    grid = []
    for y0, y1 in runs(solid.sum(1) > 4):
        strip = solid[y0:y1]
        row = []
        for x0, x1 in runs(strip.sum(0) > 4):
            sub = strip[:, x0:x1]
            ys, xs = np.where(sub.sum(1) > 4)[0], np.where(sub.sum(0) > 4)[0]
            if len(ys) and len(xs):
                row.append((x0 + int(xs[0]), y0 + int(ys[0]), x0 + int(xs[-1]) + 1, y0 + int(ys[-1]) + 1))
        grid.append(row)
    return grid


def despill(rgb, a, np):
    """Pull the magenta back out of the half-covered pixels at an object's edge."""
    r, g, b = rgb[:, :, 0].astype(float), rgb[:, :, 1].astype(float), rgb[:, :, 2].astype(float)
    k = ((np.minimum(r, b) - g) > 10) & (a > 0.15)
    cap = g + 12
    return np.stack([np.where(k, np.minimum(r, cap), r), g, np.where(k, np.minimum(b, cap), b)], 2)


def legible(img, np):
    """How much of an object is still there at 18 px: the share of its pixels that keep a strong edge. A bold shape
    holds its contrast when shrunk; fine detail averages into one flat tone and this number collapses."""
    from PIL import Image
    sm = img.convert('RGBA').resize((SMALL, SMALL), Image.LANCZOS)
    a = np.asarray(sm).astype(float)
    al = a[:, :, 3] / 255.0
    lum = a[:, :, :3].mean(2)
    inside = al > 0.5
    if inside.sum() < 8:
        return 0.0
    v = lum[inside]
    return float(v.max() - v.min())          # the tonal range left inside the shape


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    flags = [x for x in sys.argv[1:] if x.startswith('--')]
    if not args:
        raise SystemExit(__doc__)
    only = None
    for f in flags:
        if f.startswith('--only') and '=' in f:
            only = set(f.split('=', 1)[1].split(','))
    check = '--check' in flags
    import numpy as np
    from PIL import Image
    im = Image.open(args[0]).convert('RGB')
    sc = delines(score(im, np), np)
    grid = find(sc, np)
    print('sheet %d x %d' % im.size)
    if len(grid) != ROWS or any(len(r) != COLS for r in grid):
        print('found %s, expected %d rows of %d — the sheet is not laid out as asked'
              % ([len(r) for r in grid], ROWS, COLS))
    print('%-9s %-11s %-7s %s' % ('relic', 'size', 'range', 'at %d px' % SMALL))
    files = []
    arr = np.asarray(im).astype(np.int16)
    for ry, row in enumerate(grid[:ROWS]):
        for rx, box in enumerate(row[:COLS]):
            name = NAMES[ry][rx]
            if only and name not in only:
                continue
            x0, y0, x1, y1 = box
            sub = sc[y0:y1, x0:x1]
            al = np.clip((KEY_T - sub) / max(1e-6, KEY_T * (1 - CORE)), 0, 1)
            px = despill(arr[y0:y1, x0:x1], al, np)
            out = np.concatenate([np.clip(px, 0, 255), (al * 255)[:, :, None]], 2).astype('uint8')
            img = Image.fromarray(out, 'RGBA')
            rng = legible(img, np)
            print('%-9s %4dx%-6d %-7.0f %s' % (name, x1 - x0, y1 - y0, rng,
                                               'reads' if rng >= 60 else 'FLAT — check it by eye'))
            if check:
                continue
            os.makedirs(OUT, exist_ok=True)
            p = os.path.join(OUT, name + '.webp')
            img.save(p, 'WEBP', quality=90, method=6)
            files.append((name, os.path.getsize(p)))
    if check:
        print('\n--check: nothing written.')
        return
    print('\nwrote %d files to %s' % (len(files), os.path.relpath(OUT, ROOT)))
    print('  %.1f KB in all' % (sum(s for _, s in files) / 1024))


if __name__ == '__main__':
    main()
