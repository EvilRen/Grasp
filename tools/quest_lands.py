"""Quest's four land backdrops: cut the one Gemini sheet into the files the game loads.

    python3 tools/quest_lands.py art/quest_lands_raw.png [--quality 80]

The sheet is four portrait paintings butted together in one row, left to right, in the order the run
travels: the enchanted forest, the dragon castle, the star portal, the star throne. Each is cut at an
exact quarter and written to assets/quest/lands/<land id>.webp, where <land id> matches LANDS in
index.html. Nothing is keyed and nothing is measured: a backdrop has no openings and no geometry the
code has to line up with, so unlike the card frames these just need to be the right four pictures in
the right order.

A missing file is not an error: qBg() paints the land's gradient instead, as it always has.

Needs Pillow (pip install pillow).
"""
import os, sys

LANDS = ['forest', 'castle', 'space', 'throne']   # the order of LANDS in index.html, left to right
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'quest', 'lands')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    q = int(sys.argv[sys.argv.index('--quality') + 1]) if '--quality' in sys.argv else 80
    if not args:
        sys.exit(__doc__)
    try:
        from PIL import Image
    except ImportError:
        sys.exit('Pillow is needed: pip install pillow')
    sheet = Image.open(args[0]).convert('RGB')
    w, h = sheet.size
    if abs(w / h - 2.0) > 0.25:
        print('note: the sheet is %dx%d; four panels each about twice as tall as wide want roughly 2:1' % (w, h))
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for i, land in enumerate(LANDS):
        panel = sheet.crop((round(w * i / 4), 0, round(w * (i + 1) / 4), h))
        path = os.path.join(OUT, land + '.webp')
        panel.save(path, 'WEBP', quality=q, method=6)
        kb = os.path.getsize(path) / 1024
        total += kb
        print('%-34s %dx%d  %5.1f KB' % (os.path.relpath(path, ROOT), panel.width, panel.height, kb))
    print('\n%.0f KB for all four. Add them to git and bump sw.js VERSION so the offline cache picks them up.' % total)


if __name__ == '__main__':
    main()
