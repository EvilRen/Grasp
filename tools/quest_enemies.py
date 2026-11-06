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
}
GRID = {9: (3, 3), 6: (3, 2)}                 # how many across, how many down
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'enemies')
KEY = (255, 0, 255)
TOL = 90
INSET = 0.02                                  # of the cell, dropped on every side before keying


def key_out(im, tol=TOL):
    im = im.convert('RGBA')
    try:
        import numpy as np
    except ImportError:
        return im
    a = np.asarray(im).astype(int)
    d = np.maximum(np.abs(a[..., 0] - KEY[0]), np.maximum(a[..., 1] - KEY[1], np.abs(a[..., 2] - KEY[2])))
    al = a[..., 3].copy()
    al[d <= tol * 0.55] = 0
    edge = (d > tol * 0.55) & (d <= tol)
    al[edge] = (al[edge] * ((d[edge] - tol * 0.55) / (tol * 0.45))).astype(int)
    a[..., 3] = al
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
    os.makedirs(OUT, exist_ok=True)
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
        path = os.path.join(OUT, mid + '.webp')
        im.save(path, 'WEBP', quality=86, method=6)
        kb = os.path.getsize(path) / 1024
        total += kb
        print('%-38s %dx%d  %5.1f KB' % (os.path.relpath(path, ROOT), im.width, im.height, kb))
    print('\n%.0f KB for %s. Add them to git and bump sw.js VERSION.' % (total, land))


if __name__ == '__main__':
    main()
