"""Quest's monsters: cut a Gemini character sheet into the files the game draws.

    python3 tools/quest_enemies.py art/quest_forest_raw.png --land forest [--size 512]

One sheet per land, the creatures in a grid, left to right, top row first, in the order LANDS lists
them in index.html. Each cell is cut, the magenta (#FF00FF) keyed to transparency, the creature trimmed
to its own outline and written to assets/quest/enemies/<monster id>.webp.

The cell is inset slightly before keying: a generator often draws faint lines along the grid it was
asked for, and those are not magenta, so without the inset each creature keeps a hairline of border.

A missing file is not an error: the fight draws the monster's emoji instead, as it always has.

Needs Pillow (pip install pillow).
"""
import os, sys

# the monsters of each land, in the order LANDS gives them in index.html
ORDER = {
    'forest': ['slime', 'mushroom', 'wolf', 'goblin', 'bee', 'spider', 'bear', 'ent', 'troll'],
    'castle': ['skeleton', 'bat', 'knightm', 'ghost', 'mimic', 'snake', 'golem', 'witch', 'dragon'],
    'space': ['drone', 'alien', 'bot', 'octo', 'comet', 'saucer', 'mech', 'brain', 'mother'],
    'throne': ['wisp', 'golemx', 'phoenix', 'robo2', 'hydra', 'shadow'],
    'heroes': ['knight', 'wizard', 'robot'],  # not a land: the three the player picks, in HEROES order
}
GRID = {9: (3, 3), 6: (3, 2), 3: (3, 1)}      # how many across, how many down
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'enemies')
OUT_HERO = os.path.join(ROOT, 'assets', 'quest', 'heroes')
KEY = (255, 0, 255)
TOL = 90
INSET = 0.02                                  # of the cell, dropped on every side before keying


def key_out(im, tol=TOL):
    """Magenta to transparency, by hue rather than by distance from pure #FF00FF.

    The old test measured how far a pixel sat from pure magenta, which misses magenta that has been
    SHADED: a generator that draws a cast shadow under a figure paints it as darker magenta, and at 60%
    brightness that is already too far from #FF00FF to key, so the shadow survived as a bright pink
    ellipse under the moon golem and the star hydra.

    Scoring min(r - g, b - g) instead catches magenta at any brightness, because the background is the
    only thing on the sheet with red and blue both far above green. Measured on the star throne sheet:
    the background scores 248-251, the surviving shadow 155, and the golem's own grey body 3. Teal,
    gold, crimson and indigo art all score near zero, so there is a wide gap to put a threshold in.

    Edge pixels then get the magenta pulled back out of them, so a soft outline does not keep a pink
    fringe when it is drawn over something dark. Only partly-transparent pixels are touched; art that
    is genuinely violet or pink keeps its colour.
    """
    im = im.convert('RGBA')
    try:
        import numpy as np
    except ImportError:
        return im
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    score = np.minimum(r - g, b - g)
    hi, lo = 130, 60                                  # above hi it is background; below lo it is art
    al = a[..., 3].astype(float)
    al[score >= hi] = 0
    band = (score > lo) & (score < hi)
    al[band] *= 1 - (score[band] - lo) / (hi - lo)
    spill = band & (al > 0)                           # take the magenta back out of what is left
    if spill.any():
        cut = (score[spill] * 0.75).astype(int)
        a[..., 0][spill] = np.clip(r[spill] - cut, 0, 255)
        a[..., 2][spill] = np.clip(b[spill] - cut, 0, 255)
    a[..., 3] = np.clip(al, 0, 255)
    from PIL import Image
    return Image.fromarray(a.astype('uint8'), 'RGBA')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    land = sys.argv[sys.argv.index('--land') + 1] if '--land' in sys.argv else None
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 512
    if not args or land not in ORDER:
        sys.exit(__doc__ + '\n--land takes one of: ' + ', '.join(ORDER))
    try:
        from PIL import Image
    except ImportError:
        sys.exit('Pillow is needed: pip install pillow')
    sheet = Image.open(args[0])
    ids = ORDER[land]
    cols, rows = GRID[len(ids)]
    W, H = sheet.size
    out = OUT_HERO if land == 'heroes' else OUT
    os.makedirs(out, exist_ok=True)
    total = 0
    for i, mid in enumerate(ids):
        c, r = i % cols, i // cols
        x0, x1 = W * c / cols, W * (c + 1) / cols
        y0, y1 = H * r / rows, H * (r + 1) / rows
        dx, dy = (x1 - x0) * INSET, (y1 - y0) * INSET
        cell = sheet.crop((round(x0 + dx), round(y0 + dy), round(x1 - dx), round(y1 - dy)))
        im = key_out(cell)
        box = im.getbbox()
        if not box:
            print('  ! %-10s nothing left after keying: is the background flat #FF00FF?' % mid)
            continue
        im = im.crop(box)
        k = size / max(im.size)
        if k < 1:
            im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        path = os.path.join(out, mid + '.webp')
        im.save(path, 'WEBP', quality=86, method=6)
        kb = os.path.getsize(path) / 1024
        total += kb
        print('%-38s %dx%d  %5.1f KB' % (os.path.relpath(path, ROOT), im.width, im.height, kb))
    print('\n%.0f KB for %s. Add them to git and bump sw.js VERSION.' % (total, land))


if __name__ == '__main__':
    main()
