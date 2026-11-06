"""Quest's card frames: cut the one Gemini sheet (art/QUEST_GEMINI_PROMPTS.md) into the nine files the game loads.

    python3 tools/quest_frames.py art/quest_frames_raw.png [--size 512] [--check]

The sheet is a 3 x 3 grid: the columns are the card types (attack, skill, power), the rows are the rarities
(common, uncommon, rare). Each cell is cut at exact thirds, the magenta (#FF00FF) keyed out to transparency —
the picture window, the title plate, the rules panel, the cost socket and everything around the card — the card
trimmed to its own bounds and resized to the game's 1 : 1.42, then written as a compressed .webp to assets/quest/.

Needs Pillow (pip install pillow). Nothing else in the repo depends on it: the game paints the same frames in
code until these files are there, and drops them in without a code change once they are.
"""
import os, sys

TYPES = ['attack', 'skill', 'power']          # the columns
RARITY = ['', '_u', '_r']                     # the rows
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest')
KEY = (255, 0, 255)                           # the chroma the prompt asks for
TOL = 72                                      # how far from pure magenta still counts as a hole (JPEG-ish edges)
RATIO = 1.42                                  # the card's height / width, the same number as qLay() in index.html


def key_out(im):
    """Magenta -> transparent, with the halo around each hole faded instead of left as a purple fringe."""
    im = im.convert('RGBA')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                continue
            # distance from the key, weighted so a reddish or bluish pixel is not eaten
            d = max(abs(r - KEY[0]), abs(g - KEY[1]), abs(b - KEY[2]))
            if d <= TOL * 0.45:
                px[x, y] = (r, g, b, 0)
            elif d <= TOL:                      # the edge of a hole: fade it out instead of leaving a purple fringe
                k = (d - TOL * 0.45) / (TOL * 0.55)
                px[x, y] = (r, g, b, int(a * k))
    return im


def cell(im, col, row):
    w, h = im.size
    x0, x1 = round(w * col / 3), round(w * (col + 1) / 3)
    y0, y1 = round(h * row / 3), round(h * (row + 1) / 3)
    return im.crop((x0, y0, x1, y1))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    size = 512
    if '--size' in sys.argv:
        size = int(sys.argv[sys.argv.index('--size') + 1])
    if not args:
        sys.exit(__doc__)
    src = args[0]
    try:
        from PIL import Image
    except ImportError:
        sys.exit('Pillow is needed: pip install pillow')
    sheet = Image.open(src)
    if abs(sheet.size[0] / sheet.size[1] - 1 / RATIO) > 0.08:
        print('note: the sheet is %dx%d; nine 1:%.2f cards want about %d:%d — check the grid is even'
              % (sheet.size[0], sheet.size[1], RATIO, 3, round(3 * RATIO)))
    os.makedirs(OUT, exist_ok=True)
    for row, rar in enumerate(RARITY):
        for col, t in enumerate(TYPES):
            im = key_out(cell(sheet, col, row))
            box = im.getbbox()                  # the card's own bounds, the magenta margin dropped
            if box:
                im = im.crop(box)
            im = im.resize((size, round(size * RATIO)), Image.LANCZOS)
            path = os.path.join(OUT, 'frame_%s%s.webp' % (t, rar))
            im.save(path, 'WEBP', quality=88, method=6)
            print('%-34s %5.1f KB' % (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024))
    print('\nAdd them to git, bump sw.js VERSION so the offline cache picks them up, and reload.')


if __name__ == '__main__':
    main()
