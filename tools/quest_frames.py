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
import os, sys

TYPES = ['attack', 'skill', 'power']          # the columns
RARITY = ['', '_u', '_r']                     # the rows
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest')
KEY = (255, 0, 255)                           # the chroma the prompt asks for
TOL = 90                                      # how far from pure magenta still counts as a hole (Gemini shades it)
CORE = 0.62                                   # below TOL * CORE a pixel is fully a hole; above it, it fades out
RATIO = 1.42                                  # the card's height / width, the same number as qLay() in index.html

# The openings, as fractions of the card box, straight out of qLay(w) in index.html.
# x, y, w, h — the cost socket as the square that bounds its circle.
SPEC = {
    'picture window': (0.115, 0.100, 0.770, 0.395),   # art: -.385w, -.400h, .770w, .395h
    'title plate':    (0.095, 0.535, 0.810, 0.100),   # nameY .085h is the plate's centre, nameH .100h
    'rules panel':    (0.100, 0.695, 0.800, 0.205),   # txtY .295h is the centre of a .205h panel
    'cost socket':    (0.017, 0.004, 0.296, 0.208),   # gem -.335w, -.392h, r .148w  (.296w = .208h)
}
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


def cell(im, col, row):
    w, h = im.size
    x0, x1 = round(w * col / 3), round(w * (col + 1) / 3)
    y0, y1 = round(h * row / 3), round(h * (row + 1) / 3)
    return im.crop((x0, y0, x1, y1))


def card_box(im):
    """The card's own bounds inside its cell, the keyed margin dropped.

    Read from the alpha channel explicitly: Pillow 9.2+ does this for RGBA anyway, older
    Pillow looks at all four bands and would hand back the whole cell."""
    return im.getchannel('A').getbbox()


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

    def region(name, grow=0.0):
        x, y, w, h = SPEC[name]
        if name == 'cost socket':                       # a disc, not a rectangle
            cx, cy, r = x + w / 2, y + h / 2, w / 2 + grow
            return ((fx - cx) ** 2 + ((fy - cy) * (w / h)) ** 2) <= r ** 2
        return (fx >= x - grow) & (fx <= x + w + grow) & (fy >= y - grow) & (fy <= y + h + grow)

    RING = 0.022
    out = {}
    for name in SPEC:
        inside = region(name)
        others = np.zeros_like(inside)
        for o in SPEC:
            if o != name:
                others |= region(o, RING)
        ring = region(name, RING) & ~region(name) & ~others
        out[name] = (hole[inside].mean() if inside.any() else 0.0,
                     solid[ring].mean() if ring.any() else 1.0)
    return out


def check(sheet, tol=TOL):
    """Measure the sheet against qLay() and report. Writes nothing."""
    print('sheet %dx%d' % sheet.size)
    want = sheet.size[0] / sheet.size[1]
    if abs(want - 1 / RATIO) > 0.02:
        print('  ! the sheet is %.3f wide-to-tall; nine 1:%.2f cards want %.3f (%+.1f%% off)'
              % (want, RATIO, 1 / RATIO, (want * RATIO - 1) * 100))
    bad = 0
    for row, rar in enumerate(RARITY):
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
            for label in SPEC:
                open_pct, solid_pct = got[label]
                mark = ''
                if open_pct < 0.96:
                    mark = '  <-- the opening is short, shifted or filled in'
                elif solid_pct < 0.85:
                    mark = '  <-- the opening spills past where the code draws'
                if mark:
                    bad += 1
                print('       %-15s %5.1f%% open inside   %5.1f%% solid around%s'
                      % (label, open_pct * 100, solid_pct * 100, mark))
    print()
    if bad:
        print('%d problem(s). Regenerate rather than patch: the layout in the code is fixed,' % bad)
        print('and a frame whose window is a few percent off will crop every illustration.')
    else:
        print('The sheet matches qLay(). Slice it without --check to write the nine files.')
    return 1 if bad else 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    size, tol = 512, TOL
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
    if abs(sheet.size[0] / sheet.size[1] - 1 / RATIO) > 0.08:
        print('note: the sheet is %dx%d; nine 1:%.2f cards want about %d:%d — check the grid is even'
              % (sheet.size[0], sheet.size[1], RATIO, 3, round(3 * RATIO)))
    os.makedirs(OUT, exist_ok=True)
    for row, rar in enumerate(RARITY):
        for col, t in enumerate(TYPES):
            im = key_out(cell(sheet, col, row), tol)
            box = card_box(im)                  # the card's own bounds, the magenta margin dropped
            if box:
                im = im.crop(box)
            im = im.resize((size, round(size * RATIO)), Image.LANCZOS)
            path = os.path.join(OUT, 'frame_%s%s.webp' % (t, rar))
            im.save(path, 'WEBP', quality=88, method=6)
            print('%-34s %5.1f KB' % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024))
    print('\nAdd them to git, bump sw.js VERSION so the offline cache picks them up, and reload.')


if __name__ == '__main__':
    main()
