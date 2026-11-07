"""Quest's interface plates: cut the one Gemini sheet (art/QUEST_GEMINI_PROMPTS.md) into the pieces the game loads.

    python3 tools/quest_plates.py art/quest_plates_raw.png [--check] [--only panel_quiet,window]

The sheet holds nine plates in three rows of three, with flat magenta (#FF00FF) everywhere else. The plates are
FOUND, not cut at fixed thirds: the magenta is keyed, the sheet is split into bands of rows that contain anything,
each band into runs of columns, and each piece trimmed to its own bounds and written as a compressed .webp to
assets/quest/plates/. Cutting at exact thirds looked right and was not — the generator does not centre a plate in
its third, so the line between rows two and three fell inside the lower plates and every piece in the middle row
came out with a slice of the plate below it attached. That is invisible in the file and obvious in the game, as a
stray ornamented strip under every button.

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
LINE = 3          # px masked either side of each cell boundary: Gemini draws the boundaries in as thin dark lines.
                  # Only the lines, not a fat margin: a plate may sit right up against the boundary, and an 8 px
                  # margin ate the top border off the plaque before this was measured.
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
    """The plate's own box inside a cell. A row counts once a real run of the plate is in it, so stray specks and
    the keyer's fringe do not widen the box."""
    rows, cols = solid.mean(1) > 0.04, solid.mean(0) > 0.04
    if not rows.any() or not cols.any():
        return None
    y = np.where(rows)[0]
    x = np.where(cols)[0]
    return int(x[0]), int(y[0]), int(x[-1]) + 1, int(y[-1]) + 1


def boxvar(lum, np, k=5):
    """Local variance in a k x k window, by summed-area table — how busy the surface is at each pixel."""
    pad = k // 2
    p = np.pad(lum, pad, mode='edge')
    c1 = p.cumsum(0).cumsum(1)
    c2 = (p * p).cumsum(0).cumsum(1)
    def win(c):
        return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k])
    p1 = np.pad(c1, ((1, 0), (1, 0)))
    p2 = np.pad(c2, ((1, 0), (1, 0)))
    n = k * k
    m = win(p1) / n
    return np.maximum(0.0, win(p2) / n - m * m)


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
    """The border band's thickness on each side. The ornament is busy and the inner face is calm, so the band is
    found from how much the surface varies locally — averaged across the middle 60% of the opposite axis, not read
    off one scan line. A single line runs through whatever rivet or gem happens to sit on the centre, which is how
    an earlier version measured the plaque's top border as nothing at all."""
    h, w = solid.shape
    lum = rgb.astype(float).mean(2)
    v = boxvar(lum, np)
    v = np.where(solid, v, np.nan)                  # outside the plate says nothing about its border
    def run(prof, n):
        # The baseline is the CALM interior, not the busy edge. Anchoring on the edge does not work: the keyed
        # boundary has the highest variance on the plate, so a threshold scaled from it is met immediately and
        # every border measures as a few pixels.
        if n < 16:
            return 0
        mid = prof[int(n * 0.35):int(n * 0.65)]
        mid = mid[~np.isnan(mid)]
        quiet = max(float(np.median(mid)) * 3.0 + 2.0, 3.0) if len(mid) else 3.0
        need = max(5, n // 40)
        calm = 0
        for i in range(n):
            v = prof[i]
            if np.isnan(v):                         # a row the plate's corner does not reach: not evidence either way
                calm = 0
                continue
            calm = calm + 1 if v <= quiet else 0
            if calm >= need:                        # a real stretch of calm: the inner face has started
                return max(0, i - calm + 1)
        return n // 6
    mid_x = slice(int(w * 0.20), int(w * 0.80))
    mid_y = slice(int(h * 0.20), int(h * 0.80))
    import warnings
    with np.errstate(invalid='ignore'), warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)   # rows a corner does not reach are all-NaN, and say nothing
        down = np.nanmean(v[:, mid_x], 1)           # how busy each row is, across the middle of the width
        across = np.nanmean(v[mid_y, :], 0)         # how busy each column is, down the middle of the height
    raw = {'l': run(across, w), 'r': run(across[::-1], w),
           't': run(down, h), 'b': run(down[::-1], h)}
    # One inset per axis. The plates are symmetric by design — and the game mirrors them for Hebrew — so a pair that
    # disagrees wildly is a mis-read, not a feature. A reading of nothing, or of more than a third of the dimension,
    # is thrown away: the first means the scan started inside a clipped edge, the second that a gradient in a dark
    # area kept the variance up (this sheet is a JPEG, and its dark halves are noisy).
    def pick(a, b, dim):
        ok = [v for v in (a, b) if 0 < v <= dim * 0.3]
        return int(max(ok)) if ok else int(round(dim * 0.14))
    x, y = pick(raw['l'], raw['r'], w), pick(raw['t'], raw['b'], h)
    return {'l': x, 'r': x, 't': y, 'b': y, 'raw': raw}


def cap(ins, w, h, name):
    """A button is a bar with a half-circle at each end, so its left and right slices must take the WHOLE round
    end — at least half the height. Measured from the ornament alone the inset comes out narrower, the middle
    slice then contains part of the curve, and stretching it flattens one end and not the other."""
    if not name.startswith('btn_'):
        return ins
    want = min(int(round(h * 0.52)), (w - 2) // 2)
    return dict(ins, l=max(ins['l'], want), r=max(ins['r'], want))


def delines(sc, np):
    """Mark the thin dark lines Gemini draws along the cell boundaries as background, so they do not read as part
    of a plate — left alone they join every piece into one band. Only the lines, nothing wider."""
    H, W = sc.shape
    sc = sc.copy()
    for x in (W // 3, 2 * (W // 3)):
        sc[:, max(0, x - LINE):x + LINE] = 255
    for y in (H // 3, 2 * (H // 3)):
        sc[max(0, y - LINE):y + LINE, :] = 255
    return sc


def runs(mask, gap=6):
    """The runs of true in a 1-D mask, ignoring gaps shorter than `gap` (the keyer leaves specks)."""
    out, start, blank = [], None, 0
    for i, v in enumerate(mask):
        if v:
            if start is None:
                start = i - blank if blank and out and out[-1][1] == i - blank else i
                if out and i - out[-1][1] <= gap:
                    start = out.pop()[0]
            blank = 0
        else:
            blank += 1
            if start is not None and blank > gap:
                out.append((start, i - blank + 1)); start = None
    if start is not None:
        out.append((start, len(mask)))
    return [(a, b) for a, b in out if b - a > 24]


def find(sc, np):
    """Where the plates actually are: bands of rows that hold anything, and within each band, runs of columns."""
    solid = ~(sc > KEY_T)
    boxes = []
    for y0, y1 in runs(solid.sum(1) > 4):
        strip = solid[y0:y1]
        row = []
        for x0, x1 in runs(strip.sum(0) > 4):
            sub = strip[:, x0:x1]
            ys = np.where(sub.sum(1) > 4)[0]
            xs = np.where(sub.sum(0) > 4)[0]
            if len(ys) and len(xs):
                row.append((x0 + int(xs[0]), y0 + int(ys[0]), x0 + int(xs[-1]) + 1, y0 + int(ys[-1]) + 1))
        boxes.append(row)
    return boxes


def cut(im, sc, box, np):
    """One plate: its pixels, its alpha, and everything measured about it."""
    x0, y0, x1, y1 = box
    sub = sc[y0:y1, x0:x1]
    sol = sub <= KEY_T
    rgb = np.asarray(im).astype(np.int16)[y0:y1, x0:x1]
    # alpha: fully opaque below KEY_T * CORE, fading to clear at KEY_T, so the keyed edge is not a hard stair
    al = np.clip((KEY_T - sub) / max(1e-6, KEY_T * (1 - CORE)), 0, 1)
    return {'rgb': rgb, 'a': al, 'solid': sol, 'tight': '',
            'w': int(x1 - x0), 'h': int(y1 - y0),
            'flat': flatness(sol, np), 'band': band(rgb, sol, np)}


# A cell boundary that the generator drew ACROSS a plate cannot be repaired here, and the attempt did harm: the
# line is soft-edged in a JPEG, so a threshold loose enough to catch it also caught every plate's own dark bands,
# and repainting those smeared the filigree on all nine pieces while the line itself survived. The one plate that
# was crossed, the tall green window, is simply not used; its neighbours were never crossed and are clean.


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
    sc = delines(score(im), np)
    grid = find(sc, np)
    if len(grid) == 1 and len(grid[0]) == 3:
        print('one row of three: reading it as the button row')   # the re-run sheet holds only the top row
        grid = [grid[0], [], []]
    elif len(grid) != 3 or any(len(r) != 3 for r in grid):
        print('found %s, expected three rows of three — the sheet is not laid out as asked' %
              ([len(r) for r in grid],))
    print('sheet %d x %d' % im.size)
    print('%-13s %-11s %-7s %-30s %s' % ('piece', 'size', 'ratio', 'border x / y (raw l/r t/b)', 'top/bottom edge'))
    lay, files = {}, []
    for ry, row in enumerate(grid[:3]):
        for rx, box in enumerate(row[:3]):
            name = CELLS[ry][rx]
            if only and name not in only:
                continue
            c = cut(im, sc, box, np)
            if not c:
                print('%-13s EMPTY' % name)
                continue
            w, h = c['w'], c['h']
            bd = cap(c['band'], w, h, name)
            ft, fb = c['flat']
            ok = ft <= FLAT and fb <= FLAT
            print('%-13s %4dx%-6d %-7.2f x%-5d y%-5d (raw %d/%d %d/%d)  %s' % (
                name, w, h, w / h, bd['l'], bd['t'],
                bd['raw']['l'], bd['raw']['r'], bd['raw']['t'], bd['raw']['b'],
                'flat (%d/%d px)' % (ft, fb) if ok else 'CURVED (%d/%d px) — will not stretch' % (ft, fb)))
            lay[name] = {'w': w, 'h': h, 'ins': [bd['l'], bd['t']], 'flat': bool(ok)}
            if c['tight']:
                print('%-13s   ^ reaches its cell boundary on %s — its outer border may be clipped in the sheet' % ('', c['tight']))
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
    # Merge, do not replace. The plates arrived on two sheets — the panels on one, the buttons on another — and a
    # run with --only used to write a file holding just what that run cut, silently dropping the rest.
    old = {}
    if os.path.exists(LAY):
        try:
            with open(LAY) as f:
                old = json.load(f) or {}
        except (ValueError, OSError):
            old = {}
    old.update(lay)
    with open(LAY, 'w') as f:
        json.dump(old, f, indent=1, sort_keys=True)
    print('\nwrote %s' % os.path.relpath(LAY, ROOT))
    for n, sz in files:
        print('  %-13s %6.1f KB' % (n, sz / 1024))
    print('  %-13s %6.1f KB total' % ('', sum(s for _, s in files) / 1024))


if __name__ == '__main__':
    main()
