"""Quest's card frames: cut the one Gemini sheet (art/QUEST_GEMINI_PROMPTS.md) into the nine files the game loads.

    python3 tools/quest_frames.py art/quest_frames_raw.png [--size 512] [--tol 90] [--check]

The sheet is a 3 x 3 grid: the columns are the card types (attack, skill, power), the rows are the rarities
(common, uncommon, rare). Each cell is cut at exact thirds, the magenta (#FF00FF) keyed out to transparency —
the picture window, the title plate, the rules panel, the cost socket and everything around the card — the card
trimmed to its own bounds and resized to the game's 1 : 1.42, then written as a compressed .webp to assets/quest/.

--check measures the sheet against the rectangles qLay() draws to and writes nothing. Run it first: a frame whose
window is a few percent off crops every illustration, and that is invisible until the art is in the game.

Needs Pillow (pip install pillow); numpy is used when present and is only a speed-up. Nothing else in the repo
depends on it: the game paints the same frames in code until these files are there, and drops them in without a
code change once they are.
"""
import json, os, sys

TYPES = ['attack', 'skill', 'power']          # the columns
RARITY = ['', '_u', '_r']                     # the rows
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest')
LAY = os.path.join(OUT, 'frames.json')        # what each frame actually measures; the game reads it
KEY = (255, 0, 255)                           # the chroma the prompt asks for
TOL = 90                                      # how far from pure magenta still counts as a hole (Gemini shades it)
CORE = 0.62                                   # below TOL * CORE a pixel is fully a hole; above it, it fades out
RATIO = 1.42                                  # the card's height / width, the same number as qLay() in index.html
ROWS = {'common': 0, 'uncommon': 1, 'rare': 2}  # --row <name>: the sheet is that one rarity, three cards across
ROW = None                                    # set from the command line; None means a whole 3 x 3 sheet

# The openings, as fractions of the card box, straight out of qLay(w) in index.html.
# x, y, w, h — the cost socket as the square that bounds its circle.
# Only ONE of the three is a hole. qCard draws the picture, then the frame over it, then the title and
# the rules text on top of the frame — so the picture window must be cut out, while the title plate and the
# rules panel must be painted metal the text can sit on. A plate cut to magenta would show the card's own
# shadow through it behind the words.
SPEC = {
    'picture window': (0.115, 0.100, 0.770, 0.395),   # art: -.385w, -.400h, .770w, .395h
}
PLATES = {
    'title plate':    (0.095, 0.535, 0.810, 0.100),   # nameY .085h is the plate's centre, nameH .100h
    'rules panel':    (0.100, 0.695, 0.800, 0.205),   # txtY .295h is the centre of a .205h panel
}
# The cost gem is NOT an opening. qPaintGem() paints an opaque gem of exactly the gem radius over
# the frame, so a socket cut in the art would be completely hidden: measured, cutting it changes
# 2.06% of the pixels in that corner, which is only the semi-transparent shadow ring at 1.04r.
# Worse, a socket makes the frame asymmetric, and qLay puts the gem in the corner the language
# starts from — so an asymmetric frame has to be mirrored per language, which mirrors its light.
# Keep the frame symmetric and both top corners plain, and none of that arises.
SOCKET = (0.017, 0.004, 0.296, 0.208)             # where the gem lands; must be SOLID in the art
TOLERANCE = 0.02                              # how far an opening may drift before --check calls it out


def key_out(im, tol=TOL):
    """Magenta -> transparent, with the halo around each hole faded instead of left as a purple fringe."""
    im = im.convert('RGBA')
    try:
        import numpy as np
    except ImportError:
        return _key_out_slow(im, tol)
    a = np.asarray(im).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # distance from the key, weighted so a reddish or bluish pixel is not eaten
    d = np.maximum(np.maximum(np.abs(r - KEY[0]), np.abs(g - KEY[1])), np.abs(b - KEY[2]))
    core, edge = tol * CORE, float(tol)
    k = np.clip((d - core) / max(1.0, edge - core), 0.0, 1.0)      # 0 = hole, 1 = card
    out = a.copy()
    out[..., 3] = (a[..., 3] * k).astype(np.int16)
    # despill only the half-transparent rim, so a violet or crimson frame is never touched
    rim = (k > 0.0) & (k < 1.0)
    if rim.any():
        mid = ((g + np.minimum(r, b)) // 2).astype(np.int16)
        out[..., 0] = np.where(rim, np.minimum(r, np.maximum(mid, g)), r)
        out[..., 2] = np.where(rim, np.minimum(b, np.maximum(mid, g)), b)
    from PIL import Image
    return Image.fromarray(out.astype('uint8'), 'RGBA')


def _key_out_slow(im, tol=TOL):
    px = im.load()
    w, h = im.size
    core = tol * CORE
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                continue
            d = max(abs(r - KEY[0]), abs(g - KEY[1]), abs(b - KEY[2]))
            if d <= core:
                px[x, y] = (r, g, b, 0)
            elif d <= tol:
                px[x, y] = (r, g, b, int(a * (d - core) / (tol - core)))
    return im


_GRID = {}


def _bands(mask, axis, n=3):
    """Where the n solid stripes sit along an axis, from the gaps of keyed background between them."""
    try:
        import numpy as np
    except ImportError:
        return None
    hit = mask.any(axis=axis)
    n = 1 if (axis == 1 and ROW is not None) else n   # --row: one band of rows, three of columns
    runs, start = [], None
    for i, v in enumerate(hit):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i)); start = None
    if start is not None:
        runs.append((start, len(hit)))
    runs = [r for r in runs if r[1] - r[0] > len(hit) * 0.04]       # ignore specks
    return runs if len(runs) == n else None


def grid(im, tol=TOL):
    """The nine cards' boxes, found rather than assumed.

    A generated sheet rarely lands its cards on exact thirds — the one that prompted this had 113px
    outer margins and 36px gutters, so the left card crossed the first third line and the middle cell
    measured the full cell width. Reading the gutters instead removes the even-grid requirement: the
    columns and rows are wherever the keyed background runs clear through the sheet. Falls back to
    thirds when the sheet has no clean gutters (one blended sheet, a card touching its neighbour).
    """
    key = id(im)
    if key in _GRID:
        return _GRID[key]
    out = None
    try:
        import numpy as np
        a = np.asarray(im.convert('RGB')).astype(int)
        solid = ~((np.abs(a[..., 0] - KEY[0]) < tol) & (a[..., 1] < tol) & (np.abs(a[..., 2] - KEY[2]) < tol))
        cols, rows = _bands(solid, 0), _bands(solid, 1)
        if cols and rows:
            out = [[(cols[c][0], rows[r][0], cols[c][1], rows[r][1]) for c in range(3)] for r in range(len(rows))]
    except ImportError:
        pass
    _GRID[key] = out
    return out


def cell(im, col, row, tol=TOL):
    g = grid(im, tol)
    if g:
        return im.crop(g[0 if ROW is not None else row][col])
    w, h = im.size
    n, r = (1, 0) if ROW is not None else (3, row)
    x0, x1 = round(w * col / 3), round(w * (col + 1) / 3)
    y0, y1 = round(h * r / n), round(h * (r + 1) / n)
    return im.crop((x0, y0, x1, y1))


def rows_wanted():
    """Which (index, suffix) pairs this run touches: every rarity, or just the one --row names."""
    return list(enumerate(RARITY)) if ROW is None else [(ROWS[ROW], RARITY[ROWS[ROW]])]


def card_box(im):
    """The card's own bounds inside its cell, the keyed margin dropped.

    Read from the alpha channel explicitly: Pillow 9.2+ does this for RGBA anyway, older
    Pillow looks at all four bands and would hand back the whole cell."""
    return im.getchannel('A').getbbox()


def measure_frame(im):
    """Where this frame's window and two plates really sit, as fractions of the frame image.

    Three sheets drifted three different ways, so the code reads the art rather than the art obeying
    the code. Returns None when the frame does not look like a card; the game then keeps its constants.

    Measured: the window as a full rectangle, and the two plates as vertical bands only. The widths are
    left to qLay, because the title and the rules are centred and scaled to fit a width anyway — only
    their height on the card has ever been wrong, and detecting a plate's edges by colour is the part
    that would not hold (the rules tablet is nearly the colour of the frame's own body beneath it).

    The window is the largest transparent region not touching the image border. The title bar is found
    by comparing the middle of each row with that row's outer edges: across the bar the middle is a
    different colour from the metal beside it, across the frame's body the two match. The rules tablet
    is then the darkest wide band below the bar — it does not separate by colour, but it does by tone.
    """
    try:
        import numpy as np
    except ImportError:
        return None
    a = np.asarray(im.convert('RGBA')).astype(int)
    H, W, _ = a.shape
    if H < 40 or W < 40:
        return None
    clear = a[..., 3] < 24

    seen = np.zeros_like(clear)
    stack = [(0, x) for x in range(W) if clear[0, x]] + [(H - 1, x) for x in range(W) if clear[H - 1, x]]
    stack += [(y, 0) for y in range(H) if clear[y, 0]] + [(y, W - 1) for y in range(H) if clear[y, W - 1]]
    for y, x in stack:
        seen[y, x] = True

    def flood(st):
        px = []
        while st:
            y, x = st.pop()
            px.append((y, x))
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < H and 0 <= nx < W and clear[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    st.append((ny, nx))
        return px

    flood(stack)                                 # the holes touching the border are the outside
    best = []
    for y in range(H):
        for x in range(W):
            if clear[y, x] and not seen[y, x]:
                seen[y, x] = True
                px = flood([(y, x)])
                if len(px) > len(best):
                    best = px
    if len(best) < W * H * 0.02:
        return None
    ys = np.array([p[0] for p in best]); xs = np.array([p[1] for p in best])
    ax0, ax1, ay0, ay1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    if ay1 > H * 0.85:
        return None

    rgb, op = a[..., :3], a[..., 3] > 200
    mid = slice(int(W * 0.30), int(W * 0.70))
    edge = np.r_[np.arange(int(W * 0.04), int(W * 0.14)), np.arange(int(W * 0.86), int(W * 0.96))]
    diff, tone = np.full(H, np.nan), np.full(H, np.nan)
    for y in range(ay1, H):
        m, e = op[y, mid], op[y, edge]
        if m.sum() < (mid.stop - mid.start) * 0.6:
            continue
        tone[y] = rgb[y, mid][m].mean()
        if e.sum() >= len(edge) * 0.5:
            diff[y] = np.abs(rgb[y, mid][m].mean(axis=0) - rgb[y, edge][e].mean(axis=0)).mean()
    if np.isnan(diff).all() or np.isnan(tone).all():
        return None

    def runs_over(v, thr, lo, hi):
        out, start = [], None
        for y in range(lo, hi):
            on = not np.isnan(v[y]) and v[y] > thr
            if on and start is None:
                start = y
            elif not on and start is not None:
                out.append((start, y - 1)); start = None
        if start is not None:
            out.append((start, hi - 1))
        return [r for r in out if r[1] - r[0] > H * 0.012]

    thr = np.nanmin(diff) + (np.nanmax(diff) - np.nanmin(diff)) * 0.40
    bars = runs_over(diff, thr, ay1, H)
    if not bars:
        return None
    name = max(bars, key=lambda r: np.nanmean(diff[r[0]:r[1] + 1]) * (r[1] - r[0]))

    sub = tone[name[1] + 1:]                      # the tablet: the darkest wide band under the bar
    if np.isnan(sub).all():
        return None
    lo_t, hi_t = np.nanmin(sub), np.nanmax(sub)
    if hi_t - lo_t < 6:
        return None
    dark = runs_over(-tone, -(lo_t + (hi_t - lo_t) * 0.45), name[1] + 1, H)
    if not dark:
        return None
    txt = max(dark, key=lambda r: r[1] - r[0])
    if txt[1] - txt[0] < H * 0.08 or name[1] - name[0] < H * 0.02:
        return None
    f4 = lambda v: round(v, 4)
    return {'art': [f4(ax0 / W), f4(ay0 / H), f4((ax1 - ax0) / W), f4((ay1 - ay0) / H)],
            'nameY': f4((name[0] + name[1] + 1) / 2 / H), 'nameH': f4((name[1] + 1 - name[0]) / H),
            'txtY': f4((txt[0] + txt[1] + 1) / 2 / H), 'txtH': f4((txt[1] + 1 - txt[0]) / H)}


def probe(im):
    """How well each opening lands where qLay() expects it.

    The cost socket overlaps the picture window's corner and pokes over the card's edge, so
    after keying those holes are one connected region and cannot be told apart by shape. So
    measure coverage instead: how much of the expected opening is actually open, and how much
    of a thin ring just outside it is actually solid. Both near 100% means the opening is the
    right size in the right place; either one dropping means it has drifted or resized.
    """
    try:
        import numpy as np
    except ImportError:
        return None
    al = np.asarray(im.getchannel('A'))
    H, W = al.shape
    hole, solid = al < 24, al > 200
    yy, xx = np.mgrid[0:H, 0:W]
    fx, fy = xx / W, yy / H

    ALL = {**SPEC, **PLATES}   # the three rectangles qLay draws to; only the window is a hole

    def region(name, grow=0.0):
        x, y, w, h = ALL[name]
        if name == 'cost socket':                       # a disc, not a rectangle
            cx, cy, r = x + w / 2, y + h / 2, w / 2 + grow
            return ((fx - cx) ** 2 + ((fy - cy) * (w / h)) ** 2) <= r ** 2
        return (fx >= x - grow) & (fx <= x + w + grow) & (fy >= y - grow) & (fy <= y + h + grow)

    RING = 0.022
    out = {}
    for name in ALL:
        inside = region(name)
        others = np.zeros_like(inside)
        for o in ALL:
            if o != name:
                others |= region(o, RING)
        ring = region(name, RING) & ~region(name) & ~others
        out[name] = (hole[inside].mean() if inside.any() else 0.0,
                     solid[ring].mean() if ring.any() else 1.0)

    x, y, w, h = SOCKET                                  # both top corners, where the gem may land
    cx, cy, r = x + w / 2, y + h / 2, w / 2
    disc = ((fx - cx) ** 2 + ((fy - cy) * (w / h)) ** 2) <= r ** 2
    disc |= ((fx - (1 - cx)) ** 2 + ((fy - cy) * (w / h)) ** 2) <= r ** 2
    # qLay overlaps the gem onto the picture window's corner on purpose, so only judge the
    # part of the disc that is supposed to be metal
    metal = disc & ~region('picture window') & ~region('title plate') & ~region('rules panel')
    out['cost gem corners'] = (0.0, solid[metal].mean() if metal.any() else 1.0)

    mirror = al[:, ::-1]                                 # the frame must read the same flipped
    same = (np.abs(al.astype(np.int16) - mirror.astype(np.int16)) < 40).mean()
    out['left-right symmetry'] = (same, 1.0)
    return out


def check(sheet, tol=TOL):
    """Measure the sheet against qLay() and report. Writes nothing."""
    print('sheet %dx%d' % sheet.size)
    got = sheet.size[0] / sheet.size[1]
    want = (3 / RATIO) if ROW is not None else (1 / RATIO)
    if abs(got - want) > 0.02 * max(1, want):
        print('  ! the sheet is %.3f wide-to-tall; %s 1:%.2f cards want %.3f (%+.1f%% off)'
              % (got, 'three' if ROW else 'nine', RATIO, want, (got / want - 1) * 100))
    bad = 0
    for row, rar in rows_wanted():
        for col, t in enumerate(TYPES):
            name = t + (rar or '')
            im = key_out(cell(sheet, col, row), tol)
            box = card_box(im)
            if not box:
                print('  %-12s ! nothing but holes in this cell' % name)
                bad += 1
                continue
            im = im.crop(box)
            w, h = im.size
            ar = h / w
            line = '  %-12s card %dx%d  h/w %.3f' % (name, w, h, ar)
            if abs(ar / RATIO - 1) > 0.03:
                line += '  ! %+.1f%% off 1:%.2f' % ((ar / RATIO - 1) * 100, RATIO)
                bad += 1
            print(line)
            got = probe(im)
            if got is None:
                print('       (install numpy to measure the openings)')
                continue
            for label in list(SPEC) + list(PLATES) + ['cost gem corners', 'left-right symmetry']:
                open_pct, solid_pct = got[label]
                if label == 'cost gem corners':
                    # Never "cut a socket": the frame carries none. This only warns if the corner is SO open
                    # that the gem would hang over nothing. Some openness is by design — qLay overlaps the gem
                    # onto the picture window's corner, so part of its disc always lands on the hole.
                    mark = '' if solid_pct > 0.55 else '  <-- the top corners are too open: the gem would float'
                    if mark:
                        bad += 1
                    print('       %-18s %5.1f%% solid where the gem lands (both corners; ~65-75%% is normal,'
                          ' the rest overlaps the window by design)%s' % (label, solid_pct * 100, mark))
                    continue
                if label == 'left-right symmetry':
                    mark = '' if open_pct > 0.97 else '  <-- asymmetric: it would have to be mirrored per language'
                    if mark:
                        bad += 1
                    print('       %-18s %5.1f%% of the card matches its own mirror%s'
                          % (label, open_pct * 100, mark))
                    continue
                if label in PLATES: # painted, not cut: the words go on top of it, so it must be metal
                    mark = '' if open_pct < 0.04 else '  <-- cut to magenta: the words would sit on a hole'
                    if mark:
                        bad += 1
                    print('       %-18s %5.1f%% solid where the words go%s' % (label, (1 - open_pct) * 100, mark))
                    continue
                mark = ''
                if open_pct < 0.96:
                    mark = '  <-- the opening is short, shifted or filled in'   # metal over the picture: fatal
                if mark:
                    bad += 1
                note = '' if solid_pct >= 0.85 else '  (note: the hole is wider than the code draws to;'
                note += '' if solid_pct >= 0.85 else ' harmless, qPaintArt overfills it)'
                print('       %-18s %5.1f%% open inside   %5.1f%% solid around%s%s'
                      % (label, open_pct * 100, solid_pct * 100, mark, note))
    print()
    if bad:
        print('%d problem(s). Regenerate rather than patch: the layout in the code is fixed,' % bad)
        print('and a frame whose window is a few percent off will crop every illustration.')
    else:
        print('The sheet matches qLay(). Slice it without --check to write the nine files.')
    return 1 if bad else 0


def main():
    global ROW
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    size, tol = 512, TOL
    if '--row' in sys.argv:                     # a re-run of one rarity: the sheet is three cards across
        ROW = sys.argv[sys.argv.index('--row') + 1]
        if ROW not in ROWS:
            sys.exit('--row takes one of: ' + ', '.join(ROWS))
        args = [a for a in args if a != ROW]
    if '--size' in sys.argv:
        size = int(sys.argv[sys.argv.index('--size') + 1])
    if '--tol' in sys.argv:
        tol = int(sys.argv[sys.argv.index('--tol') + 1])
    if not args:
        sys.exit(__doc__)
    src = args[0]
    try:
        from PIL import Image
    except ImportError:
        sys.exit('Pillow is needed: pip install pillow')
    sheet = Image.open(src)
    if '--check' in sys.argv:
        sys.exit(check(sheet, tol))
    want = (3 / RATIO) if ROW is not None else (1 / RATIO)   # three across, one or three down
    if abs(sheet.size[0] / sheet.size[1] - want) > 0.08 * max(1, want):
        print('note: the sheet is %dx%d (%.3f wide-to-tall); %s 1:%.2f cards want %.3f'
              % (sheet.size + (sheet.size[0] / sheet.size[1], 'three' if ROW else 'nine', RATIO, want)))
    os.makedirs(OUT, exist_ok=True)
    try:                                        # --row rewrites three entries and leaves the other six
        lay = json.load(open(LAY))
    except Exception:
        lay = {}
    for row, rar in rows_wanted():
        for col, t in enumerate(TYPES):
            im = key_out(cell(sheet, col, row), tol)
            box = card_box(im)                  # the card's own bounds, the magenta margin dropped
            if box:
                im = im.crop(box)
            ar = im.size[1] / im.size[0]
            if abs(ar / RATIO - 1) > 0.03:      # resizing keeps every opening at its own percentage of the
                off = (ar / RATIO - 1) * 100    # card, so the layout still lines up -- but the art is stretched
                print('  ! %-12s is h/w %.3f, %+.1f%% off 1:%.2f: the frame will be squeezed to fit.'
                      % (t + (rar or ''), ar, off, RATIO))
                print('    Regenerate the sheet at 1:%.2f. Do not crop to fit -- cropping is what would move'
                      % RATIO)
                print('    the openings off the rectangles qLay() draws to.')
            im = im.resize((size, round(size * RATIO)), Image.LANCZOS)
            path = os.path.join(OUT, 'frame_%s%s.webp' % (t, rar))
            im.save(path, 'WEBP', quality=88, method=6)
            m = measure_frame(Image.open(path))
            key = 'frame_%s%s' % (t, rar)
            if m:
                lay[key] = m
                print('%-34s %5.1f KB   window %.3f,%.3f,%.3f,%.3f  name y%.3f  rules y%.3f'
                      % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024,
                         m['art'][0], m['art'][1], m['art'][2], m['art'][3], m['nameY'], m['txtY']))
            else:
                lay.pop(key, None)
                print('%-34s %5.1f KB   ! could not be measured: the game keeps its own layout for it'
                      % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024))
    with open(LAY, 'w') as fh:
        json.dump(lay, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('\n%s: where %d frame(s) really put their window and plates.' % (os.path.relpath(LAY, ROOT), len(lay)))
    print('qLay() reads it per frame, and keeps its own constants for any frame missing from it.')
    print('Add them to git, bump sw.js VERSION so the offline cache picks them up, and reload.')


if __name__ == '__main__':
    main()
