#!/usr/bin/env python3
"""Composite the Quest art-direction panels into one 9:16 presentation board.

Reads art/art-direction/panels/*.webp and writes quest_art_direction_board.png.
Adds no text, glyphs or logos of any kind -- only dark grading, hairline rules and
soft shadows, so the finished board stays strictly type-free.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
PANELS = ROOT / "panels"
OUT = ROOT / "quest_art_direction_board.png"

W, H = 1200, 2133
MARGIN, GAP = 48, 28
BASE_TOP, BASE_BOT = (14, 18, 22), (7, 9, 11)
GOLD = (201, 162, 39)
TEAL = (47, 214, 195)


def load(name):
    p = PANELS / name
    return Image.open(p).convert("RGB") if p.exists() else None


def trim(img, tol=18, pad=2):
    """Trim the flat dark bleed a generator leaves around an isolated subject."""
    bg = img.crop((0, 0, 8, 8)).resize((1, 1)).getpixel((0, 0))
    mask = ImageChops.difference(img, Image.new("RGB", img.size, bg)).convert("L")
    box = mask.point(lambda v: 255 if v > tol else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad),
                     min(img.width, r + pad), min(img.height, b + pad)))


def contain(img, cw, ch):
    s = min(cw / img.width, ch / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


def precrop(img, frac):
    """Keep the top `frac` of the frame -- forces a true half-body crop."""
    return img.crop((0, 0, img.width, round(img.height * frac)))


def cover(img, cw, ch):
    s = max(cw / img.width, ch / img.height)
    r = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    # bias the crop upward so heads and card tops are never clipped
    x = (r.width - cw) // 2
    y = min(max(0, (r.height - ch) // 4), max(0, r.height - ch))
    return r.crop((x, y, x + cw, y + ch))


def background():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        f = y / (H - 1)
        g.putpixel((0, y), tuple(round(BASE_TOP[i] + (BASE_BOT[i] - BASE_TOP[i]) * f) for i in range(3)))
    bg = g.resize((W, H), Image.BILINEAR)
    # soft teal bloom behind the card row, barely there
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((-240, -340, W + 240, 700), fill=17)
    bg = Image.composite(Image.new("RGB", (W, H), TEAL), bg, glow.filter(ImageFilter.GaussianBlur(200)))
    # vignette
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).rectangle((90, 90, W - 90, H - 90), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(150)).point(lambda v: 255 - round((255 - v) * 0.55))
    return Image.composite(bg, Image.new("RGB", (W, H), (4, 5, 7)), vig)


def paste(board, img, x, y, shadow=26, radius=16):
    if shadow:
        sh = Image.new("L", (img.width + radius * 4, img.height + radius * 4), 0)
        ImageDraw.Draw(sh).rectangle((radius * 2, radius * 2,
                                      radius * 2 + img.width, radius * 2 + img.height), fill=shadow * 4)
        sh = sh.filter(ImageFilter.GaussianBlur(radius))
        board.paste(Image.new("RGB", sh.size, (0, 0, 0)), (x - radius * 2, y - radius * 2 + 6), sh)
    board.paste(img, (x, y))


def rule(board, y, inset=MARGIN, alpha=34):
    strip = Image.new("RGB", (W - inset * 2, 1), GOLD)
    mask = Image.new("L", (W - inset * 2, 1), 0)
    d = ImageDraw.Draw(mask)
    n = W - inset * 2
    for x in range(n):                       # fade the rule out at both ends
        f = min(x, n - 1 - x) / (n * 0.30)
        d.point((x, 0), fill=round(alpha * min(1.0, f)))
    board.paste(strip, (inset, y), mask)


def main():
    board = background()
    y = MARGIN

    # --- Row 1: three card frames -------------------------------------------------
    cw = (W - MARGIN * 2 - GAP * 2) // 3
    ch = 524
    cards = [load(n) for n in ("card_attack.webp", "card_skill.webp", "card_power.webp")]
    for i, c in enumerate(cards):
        x = MARGIN + i * (cw + GAP)
        if c is None:
            continue
        im = contain(trim(c), cw, ch)
        paste(board, im, x + (cw - im.width) // 2, y + (ch - im.height) // 2, shadow=30)
    y += ch + 36
    rule(board, y - 18)

    # --- Row 2: hero + enemy ------------------------------------------------------
    pw = (W - MARGIN * 2 - GAP) // 2
    ph = 760
    for i, (n, frac) in enumerate((("hero.webp", 0.60), ("enemy.webp", 1.0))):
        im = load(n)
        if im is None:
            continue
        if frac < 1.0:
            im = precrop(im, frac)
        paste(board, cover(im, pw, ph), MARGIN + i * (pw + GAP), y, shadow=24)
    y += ph + 36
    rule(board, y - 18)

    # --- Row 3: UI icon row -------------------------------------------------------
    iw, ih = W - MARGIN * 2, 340
    icons = load("icons.webp")
    if icons is not None:
        paste(board, cover(icons, iw, ih), MARGIN, y, shadow=20)
    y += ih + 36
    rule(board, y - 18)

    # --- Row 4: backdrop strip ----------------------------------------------------
    bw = (W - MARGIN * 2 - GAP) // 2
    bh = round(bw * 9 / 16)
    for i, n in enumerate(("bg_forest.webp", "bg_cosmic.webp")):
        im = load(n)
        x = MARGIN + i * (bw + GAP)
        if im is None:                        # reserved plate until the panel exists
            ph_ = Image.new("RGB", (bw, bh), (17, 21, 25))
            ImageDraw.Draw(ph_).rectangle((0, 0, bw - 1, bh - 1), outline=(34, 42, 48))
            paste(board, ph_, x, y, shadow=18)
            continue
        paste(board, cover(im, bw, bh), x, y, shadow=22)

    board.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT}  {board.size[0]}x{board.size[1]}")


if __name__ == "__main__":
    main()
