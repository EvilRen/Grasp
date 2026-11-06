"""Quest's card pictures: cut a sheet into the per-card files the game draws behind its frames.

    python3 tools/quest_cardart.py art/knight_raw.png --ids strike,defend,bash,cleave,twin,ironwave,shrug,bodyslam,headbutt

Three cards across, in reading order, one id per cell. Each cell is written to
assets/quest/art/<card id>.webp and qPaintArt draws it into the card's picture window; a card with no
file keeps its symbol, as before.

Nothing is keyed: these are whole little paintings, not cut-outs. Two things are repaired instead,
because a generator asked for a labelled grid draws the labels and the mask it was told to leave:
  - a caption band across the bottom of a cell is found and cropped off (bright glyph rows sitting on a
    flat strip), so the painting ends where the painting ends;
  - the black rounded blocks a generator puts in the upper corners when told to keep them clear are
    filled from the background below them.
Both are measured per cell, so a cell that has neither is left alone.

Needs Pillow and numpy.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'art')
RATIO = 1.21          # the picture window's width / height in qLay()


def strip_caption(a, np):
    """Where the painting really ends: above any band of bright glyphs near the bottom."""
    H, W, _ = a.shape
    lum = a[..., :3].mean(axis=2)
    lo = int(H * 0.74)
    med = np.median(lum[lo:], axis=1)
    ink = ((lum[lo:] - med[:, None]) > 42).mean(axis=1)      # pixels far brighter than their own row
    rows = np.where(ink > 0.035)[0]
    if not len(rows):
        return H
    top = lo + rows.min()
    return max(int(H * 0.72), top - int(H * 0.025))


def trim_margin(a, np):
    """Drop the pale gutter a sheet carries between its cells, before anything else is measured."""
    H, W, _ = a.shape
    lum = a[..., :3].mean(axis=2)
    def flat_pale(line):
        return line.mean() > 140 and line.std() < 34
    t, b, l, r = 0, H, 0, W
    while t < H * 0.15 and flat_pale(lum[t]):
        t += 1
    while b > H * 0.85 and flat_pale(lum[b - 1]):
        b -= 1
    while l < W * 0.15 and flat_pale(lum[:, l]):
        l += 1
    while r > W * 0.85 and flat_pale(lum[:, r - 1]):
        r -= 1
    return a[t:b, l:r]


TOP = 0.16            # of the cell, dropped from the top: the sheet's gutter and the black corner
                      # blocks a generator leaves there both live inside it, and the subject sits low


def main():
    args = [v for v in sys.argv[1:] if not v.startswith('--')]
    ids = sys.argv[sys.argv.index('--ids') + 1].split(',') if '--ids' in sys.argv else []
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 420
    if not args or not ids:
        sys.exit(__doc__)
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        sys.exit('Pillow and numpy are needed: pip install pillow numpy')
    sheet = Image.open(args[0]).convert('RGB')
    W, H = sheet.size
    cols = 3
    rows = (len(ids) + cols - 1) // cols
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for i, cid in enumerate(ids):
        c, r = i % cols, i // cols
        cell = sheet.crop((round(W * c / cols), round(H * r / rows), round(W * (c + 1) / cols), round(H * (r + 1) / rows)))
        a = trim_margin(np.asarray(cell).astype(int).copy(), np)
        cut = strip_caption(a, np)
        top = int(a.shape[0] * TOP)
        im = Image.fromarray(a.astype('uint8'), 'RGB').crop((0, top, a.shape[1], cut))
        w, h = im.size                                        # centre-crop to the window's shape
        if w / h > RATIO:
            nw = round(h * RATIO); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w / RATIO); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        im = im.resize((size, round(size / RATIO)), Image.LANCZOS)
        path = os.path.join(OUT, cid + '.webp')
        im.save(path, 'WEBP', quality=86, method=6)
        kb = os.path.getsize(path) / 1024
        total += kb
        print('%-34s %dx%d  %5.1f KB   caption cut %s'
              % (os.path.relpath(path, ROOT), im.width, im.height, kb, 'no' if cut >= a.shape[0] else 'yes'))
    print('\n%.0f KB for %d card pictures.' % (total, len(ids)))


if __name__ == '__main__':
    main()
