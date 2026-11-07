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

# Each sheet is a set: its grid in reading order, and the folder it is written to. --set picks one.
SETS = {
    'relics': ([['heart', 'book', 'core', 'clover', 'boot', 'whet'],        # the keys of RELICS in index.html
                ['pot', 'lantern', 'bag', 'feather', 'snail', 'thorn'],
                ['tea', 'map', 'star', 'magnet', 'egg', 'venom']], 'relics'),
    'icons1': ([['dmg', 'blk', 'heal', 'en'],                               # the keys of Q_IC: the fight and card ones
                ['str', 'weak', 'vul', 'poi'],
                ['thorns', 'draw', 'disc', 'loop']], 'icons'),
    'icons2': ([['all', 'call', 'gold', 'skull', 'crown'],                  # the rest of Q_IC: the screens and doors
                ['trophy', 'chest', 'shop', 'fire', 'lock'],
                ['cut', 'mystery', 'help']], 'icons'),
    'doors': ([['door_fight', 'door_elite', 'door_boss', 'door_rest'],
               ['door_shop', 'door_chest', 'door_event']], 'doors'),
    'knight4': ([['kn_idle', 'kn_breath', 'kn_atk', 'kn_hurt']], 'heroes/knight'),
    'door1': ([['door_event']], 'doors'),     # a one-piece sheet, for re-running a single doorway
    'events': ([['ev_well', 'ev_shrine', 'ev_merchant', 'ev_chest', 'ev_fountain'],   # the eight events, by EVENTS id
                ['ev_robot', 'ev_portal', 'ev_feast', 'map', 'door'],                 # then the how-to page symbols
                ['cards', 'hourglass', 'finger', 'monster']], 'icons'),
}
NAMES, COLS, ROWS, OUT = None, 0, 0, None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_T = 70        # how far the magenta score (min(r-g, b-g)) must reach for a pixel to be a hole
CORE = 0.62       # below KEY_T * CORE a pixel is fully a hole; above it, it fades out
RAMP = None       # set by --ramp: the width of that fade, in score, instead of deriving it from CORE
# --key raises the threshold for a sheet whose artwork is itself close to the keying colour. A violet glow scores
# high on min(r-g, b-g) — the mystery doorway's rim reached 150 against a background of 242 — so at the default 70
# fourteen thousand pixels of the glow were cut away and the land behind showed through as a thread along it.
# Measure the sheet before choosing one: the right value sits in the gap between the art's highest and the
# background's lowest.
LINE = 4          # px masked either side of each cell boundary: the generator draws the boundaries in as thin lines
SMALL = 18        # the size the check renders each object at


def score(im, np):
    a = np.asarray(im).astype(np.int16)
    return np.minimum(a[:, :, 0] - a[:, :, 1], a[:, :, 2] - a[:, :, 1])


def delines(sc, np):
    """Blank a thin line drawn along a cell boundary — but only where one is actually drawn.

    Blanking the boundaries unconditionally assumes every piece sits inside its own cell of an even grid, and that
    is not always true: the doors sheet puts three pieces across a four-column grid, so a boundary fell inside the
    treasure door and cut a third of it away. A drawn line is a narrow solid stripe with background either side of
    it, and only that is removed.
    """
    H, W = sc.shape
    sc = sc.copy()
    def isline(strip, left, right):
        return (strip <= KEY_T).mean() > 0.6 and (left > KEY_T).mean() > 0.7 and (right > KEY_T).mean() > 0.7
    for i in range(1, COLS):
        x = W * i // COLS
        a, b = max(0, x - LINE), min(W, x + LINE)
        if b - a < 2 or a - LINE * 5 < 0 or b + LINE * 5 > W:
            continue
        if isline(sc[:, a:b], sc[:, a - LINE * 5:a - LINE * 2], sc[:, b + LINE * 2:b + LINE * 5]):
            sc[:, a:b] = 255
    for i in range(1, ROWS):
        y = H * i // ROWS
        a, b = max(0, y - LINE), min(H, y + LINE)
        if b - a < 2 or a - LINE * 5 < 0 or b + LINE * 5 > H:
            continue
        if isline(sc[a:b, :], sc[a - LINE * 5:a - LINE * 2, :], sc[b + LINE * 2:b + LINE * 5, :]):
            sc[a:b, :] = 255
    return sc


def pick_set(flags):
    global NAMES, COLS, ROWS, OUT
    name = 'relics'
    for f in flags:
        if f.startswith('--set') and '=' in f:
            name = f.split('=', 1)[1]
    if name not in SETS:
        raise SystemExit('--set must be one of: ' + ', '.join(sorted(SETS)))
    NAMES, folder = SETS[name]
    ROWS = len(NAMES)
    COLS = max(len(r) for r in NAMES)
    OUT = os.path.join(ROOT, 'assets', 'quest', folder)
    return name


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


def find(sc, np, cols, want=None):
    """Where the objects actually are: bands of rows that hold anything, then runs of columns inside each band.

    Runs are then snapped to cells, because one object is not always one run: a sword snapped in half is two
    separate blades with magenta between them, and read as two pieces it pushed every name in its row along by
    one. Each run is assigned to the cell its centre falls in, and runs sharing a cell become one box."""
    solid = ~(sc > KEY_T)
    H, W = solid.shape
    # A column counts as holding a piece once a real run of it is there. The old flat four was below the noise:
    # a handful of stray pixels in the gap between two figures bridged them into one run, and a sheet of four
    # knights came through as two. The floor is a small share of the sheet instead, which no real piece is under.
    VR, VC = max(4, int(W * 0.012)), max(4, int(H * 0.012))
    grid = []
    for bi, (y0, y1) in enumerate(runs(solid.sum(1) > VR)):
        strip = solid[y0:y1]
        # When the row's piece count is known, look for the threshold that yields it rather than trusting one
        # number. A sheet's gaps carry different amounts of stray colour, and a single floor either welds two
        # pieces together or splits one in half; this finds the floor that fits the sheet in hand.
        colsum = strip.sum(0)
        cols_here = runs(colsum > VC)
        exp0 = want[bi] if want and bi < len(want) else None
        if exp0 is not None and len(cols_here) != exp0:
            for t in (VC, VC * 2, VC * 4, VC * 8, VC * 16, VC * 32):
                cand = runs(colsum > t)
                if len(cand) == exp0:
                    cols_here = cand; break
        # Snap to cells only when there are MORE runs than pieces expected — that is the case snapping is for, a
        # piece drawn in two parts. When the count already matches, the runs ARE the pieces, and snapping can only
        # do harm: this sheet spaces its four figures unevenly, two of them fall in one quarter, and snapping
        # welded them into a single box.
        exp = want[bi] if want and bi < len(want) else None
        if exp is not None and len(cols_here) == exp:
            row = []
            for x0, x1 in cols_here:
                sub = strip[:, x0:x1]
                ys, xs = np.where(sub.sum(1) > 0)[0], np.where(sub.sum(0) > 0)[0]
                if len(ys) and len(xs):
                    row.append((x0 + int(xs[0]), y0 + int(ys[0]), x0 + int(xs[-1]) + 1, y0 + int(ys[-1]) + 1))
            grid.append(row)
            continue
        cells = {}
        for x0, x1 in cols_here:
            sub = strip[:, x0:x1]
            ys, xs = np.where(sub.sum(1) > 0)[0], np.where(sub.sum(0) > 0)[0]
            if not (len(ys) and len(xs)):
                continue
            b = (x0 + int(xs[0]), y0 + int(ys[0]), x0 + int(xs[-1]) + 1, y0 + int(ys[-1]) + 1)
            c = min(cols - 1, max(0, int((b[0] + b[2]) / 2 * cols // W)))
            if c in cells:
                o = cells[c]
                ao = (o[2] - o[0]) * (o[3] - o[1])
                ab = (b[2] - b[0]) * (b[3] - b[1])
                # Two runs in one cell are two halves of one thing — a sword snapped in two — only if they are of
                # comparable size. A speck beside the artwork is not part of it: told not to number the positions,
                # the generator numbered them, and unioning a door with the digit under it dragged the digit in.
                if min(ao, ab) >= max(ao, ab) * 0.15:
                    cells[c] = (min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3]))
                elif ab > ao:
                    cells[c] = b
            else:
                cells[c] = b
        grid.append([cells[c] for c in sorted(cells)])
    # Drop a band of stray marks. Told not to number the positions, the generator numbered them anyway, and a row
    # of small digits under the artwork reads as a band of its own — four bands where the sheet has two, and every
    # name after the first row lands on the wrong piece. Anything far shorter than the real rows is not a piece.
    tall = max((b[3] - b[1] for row in grid for b in row), default=0)
    grid = [row for row in grid if row and max(b[3] - b[1] for b in row) > tall * 0.35]
    return grid


def trimstray(box, sc, np):
    """Pull a box in to the piece itself, dropping anything hanging off it across a clear gap.

    The size rule above separates a speck from a piece only when the two are separate runs. A digit printed right
    under a door touches its shadow, so they come through as one run and one box. Here the box's own rows and
    columns are read: the piece is the largest unbroken block of them, and a blob beyond a gap of empty ones is not
    part of it.
    """
    x0, y0, x1, y1 = box
    sub = ~(sc[y0:y1, x0:x1] > KEY_T)
    # The cut must be at a real gap, not merely a thin part. At 6% a door's ragged stone edge counted as empty and
    # half the treasure door was trimmed away; a stray mark is separated by rows that are empty, not sparse.
    def block(fill, lo_frac=0.015):
        on = fill > lo_frac
        best, start = (0, 0), None          # empty to begin with: seeded with the full range it can never shrink
        for i, v in enumerate(on):
            if v and start is None:
                start = i
            elif not v and start is not None:
                if i - start > best[1] - best[0]:
                    best = (start, i)
                start = None
        if start is not None and len(on) - start > best[1] - best[0]:
            best = (start, len(on))
        return best if best[1] > best[0] else (0, len(fill))
    ry0, ry1 = block(sub.mean(1))
    rx0, rx1 = block(sub.mean(0))
    return (x0 + rx0, y0 + ry0, x0 + rx1, y0 + ry1)


def closeslits(rgb, a, np):
    """Fill a narrow band of background left inside a piece.

    The mystery doorway was painted as two pieces with a slit of the background colour running between them, so the
    cut-out let the land behind it show through as a thin line. A gap this narrow with artwork on both sides is
    never wanted, so it is closed and its colour taken from the pixels either side of it.
    """
    rgb = rgb.astype(float).copy()
    a = a.copy()
    h, w = a.shape
    for axis in (1, 0):
        n = w if axis == 1 else h
        lim = max(2, int(n * 0.03))
        lines = range(h) if axis == 1 else range(w)
        for i in lines:
            al = a[i] if axis == 1 else a[:, i]
            px = rgb[i] if axis == 1 else rgb[:, i]
            j = 0
            while j < n:
                if al[j] > 0.35:
                    j += 1; continue
                k = j
                while k < n and al[k] <= 0.35:
                    k += 1
                if 0 < j and k < n and (k - j) <= lim:      # a gap, with the piece on both sides of it
                    lo, hi = px[j - 1].copy(), px[k].copy()
                    for t in range(j, k):
                        f = (t - j + 1) / (k - j + 1)
                        px[t] = lo * (1 - f) + hi * f
                        al[t] = 1.0
                j = k
    return rgb, a


def despill(rgb, a, np):
    """Recover each pixel's own colour from its blend with the magenta behind it.

    A half-covered rim pixel is observed = a * object + (1 - a) * magenta, and alpha already says what a is, so the
    object's colour is (observed - (1 - a) * magenta) / a. A fully opaque pixel is left exactly as it is.

    The rule this replaces was wrong and silently destroyed artwork: it pulled red and blue down to green wherever
    both exceeded it, on every pixel rather than only on the rim. That is what a crimson red looks like, so the
    heart came out of the sheet at (164, 21, 66) and was written to disk at (32, 21, 32) — black. Nothing in the
    file said so; it took rendering the icon and looking at it.
    """
    out = np.empty(rgb.shape, dtype=float)
    al = np.clip(a, 0, 1)
    safe = np.maximum(al, 0.05)[:, :, None]
    mag = np.array([255.0, 0.0, 255.0])
    out = (rgb.astype(float) - (1 - al)[:, :, None] * mag) / safe
    return np.where((al > 0.98)[:, :, None], rgb.astype(float), np.clip(out, 0, 255))

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
    which = pick_set(flags)
    global KEY_T, RAMP
    for f in flags:
        if f.startswith('--key') and '=' in f:
            KEY_T = int(f.split('=', 1)[1])
        if f.startswith('--ramp') and '=' in f:
            RAMP = int(f.split('=', 1)[1])
    import numpy as np
    from PIL import Image
    im = Image.open(args[0]).convert('RGB')
    sc = delines(score(im, np), np)
    grid = find(sc, np, COLS, [len(r) for r in NAMES])
    print('sheet %d x %d' % im.size)
    want = [len(r) for r in NAMES]
    if [len(r) for r in grid] != want:
        print('found rows of %s, expected %s — the sheet is not laid out as asked'
              % ([len(r) for r in grid], want))
    print('set: %s -> %s' % (which, os.path.relpath(OUT, ROOT)))
    print('%-9s %-11s %-7s %s' % ('relic', 'size', 'range', 'at %d px' % SMALL))
    files = []
    arr = np.asarray(im).astype(np.int16)
    for ry, row in enumerate(grid[:ROWS]):
        for rx, box in enumerate(row[:len(NAMES[ry])]):
            name = NAMES[ry][rx]
            if only and name not in only:
                continue
            x0, y0, x1, y1 = trimstray(box, sc, np)
            sub = sc[y0:y1, x0:x1]
            al = np.clip((KEY_T - sub) / max(1e-6, RAMP if RAMP else KEY_T * (1 - CORE)), 0, 1)
            px, al = closeslits(arr[y0:y1, x0:x1], al, np)
            px = despill(px, al, np)
            out = np.concatenate([np.clip(px, 0, 255), (al * 255)[:, :, None]], 2).astype('uint8')
            img = Image.fromarray(out, 'RGBA')
            rng = legible(img, np)
            print('%-9s %4dx%-6d %-7.0f %s' % (name, x1 - x0, y1 - y0, rng,
                                               'reads' if rng >= 60 else 'one flat tone — reads by shape, check by eye'))
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
