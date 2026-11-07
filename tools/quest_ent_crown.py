"""Grow the ent's canopy back by cloning its own leaves.

The sheet it was cut from is gone, so nothing can be recovered — but the tree still carries plenty
of painted foliage below the cut. The crown is rebuilt by stamping those leaf clusters above the
cut line under a lobed mask, so the new growth is the same paint, the same light and the same leaf
texture as the old, rather than an invented green blob.
"""
import math, random
from PIL import Image, ImageFilter, ImageChops, ImageDraw

random.seed(11)
# the cut original, kept aside: this script must never be run against its own output
src = Image.open('art/quest_ent_cut.webp').convert('RGBA')
W, H = src.size
sp = src.load()

# --- find leafy patches: fully opaque, green, no trunk brown, no glowing mushroom ---
def leafy(cx, cy, r):
    n = good = 0
    for yy in range(cy - r, cy + r + 1, 3):
        for xx in range(cx - r, cx + r + 1, 3):
            if not (0 <= xx < W and 0 <= yy < H): return False
            px = sp[xx, yy]
            if px[3] < 250: return False
            n += 1
            rr, gg, bb = px[:3]
            if gg >= rr - 6 and gg > bb + 10 and gg < 190 and not (bb > gg + 20): good += 1
    return n and good / n > 0.90

R = 34
patches = []
for cy in range(R, 190, 7):
    for cx in range(R, W - R, 7):
        if leafy(cx, cy, R):
            patches.append((cx, cy))
print('leaf patches found:', len(patches))

GROW = 74
out = Image.new('RGBA', (W, H + GROW), (0, 0, 0, 0))
out.paste(src, (0, GROW))
y0 = GROW

xs = [x for x in range(W) if sp[x, 0][3] > 200]
x1, x2 = min(xs), max(xs)
cx0 = (x1 + x2) / 2
rx = (x2 - x1) / 2

def blob(r):
    """a soft round mask with a wobbly edge, for one stamped cluster"""
    m = Image.new('L', (r * 2, r * 2), 0)
    d = ImageDraw.Draw(m)
    steps = 26
    pts = []
    for i in range(steps):
        a = i / steps * math.tau
        rr = r * random.uniform(0.76, 0.99)
        pts.append((r + math.cos(a) * rr, r + math.sin(a) * rr))
    d.polygon(pts, fill=255)
    return m.filter(ImageFilter.GaussianBlur(r * 0.10))

# the crown grows in clumps, not as one even dome: three masses, each a cloud of small blobs
lobes = []
CL = ((0.16, 0.56), (0.42, 1.00), (0.70, 0.78), (0.90, 0.40))
for (t, hgt) in CL:
    ccx = x1 + t * (x2 - x1)
    n = 6 if hgt > 0.5 else 4
    for i in range(n):
        lx = ccx + random.uniform(-0.085, 0.085) * (x2 - x1)
        up = (GROW - 18) * hgt * random.uniform(0.42, 1.0)
        r = int(random.uniform(19, 33) * (0.85 + 0.35 * hgt))
        ly = y0 - up + r * 0.5
        lobes.append((lx, ly, r))
# a continuous course of leaves lying ACROSS the old cut, so the chopped band is covered rather
# than left showing as a flat strip under the new growth
step = 22
lx = x1 + 6
while lx <= x2 - 6:
    r = int(random.uniform(27, 37))
    lobes.append((lx + random.uniform(-5, 5), y0 + random.uniform(2, 12), r))
    lx += step
lobes.sort(key=lambda L: -L[1])

crown = Image.new('RGBA', (W, H + GROW), (0, 0, 0, 0))
for (lx, ly, r) in lobes:
    px_, py_ = random.choice(patches)
    patch = src.crop((px_ - r, py_ - r, px_ + r, py_ + r))
    if patch.size != (r * 2, r * 2):
        patch = patch.resize((r * 2, r * 2), Image.LANCZOS)
    if random.random() < 0.5:
        patch = patch.transpose(Image.FLIP_LEFT_RIGHT)
    m = blob(r)
    crown.paste(patch, (int(lx - r), int(ly - r)), m)

# nothing below the cut, and nothing outside the old silhouette's span
# The crown laps over the old cut and then fades out into the canopy below along a wavy, feathered
# line, so that nowhere does the new growth end on a straight edge against the old.
cut = Image.new('L', crown.size, 0)
cpx_ = cut.load()
jit = [sum((1.0 / (i + 1)) * math.sin(xx / (5.0 + i * 9) + i * 2.1) for i in range(4)) * 6 for xx in range(W)]
for xx in range(W):
    a_ = y0 + 2 + jit[xx]          # fully opaque until here
    b_ = y0 + 34 + jit[xx]         # gone by here
    for yy in range(0, min(crown.size[1], int(b_) + 2)):
        if yy <= a_: cpx_[xx, yy] = 255
        else: cpx_[xx, yy] = max(0, int(255 * (1 - (yy - a_) / (b_ - a_))))
cut = cut.filter(ImageFilter.GaussianBlur(1.5))
crown.putalpha(ImageChops.multiply(crown.split()[3], cut))

# the light: above and a little to the left, so the new growth is lit on top
cpx = crown.load()
for yy in range(y0 + 31):
    for xx in range(W):
        a = cpx[xx, yy][3]
        if not a: continue
        t = 1 - yy / y0
        f = 0.30 * max(0.0, t - 0.25) / 0.75
        f *= 0.45 + 0.55 * (1 - abs(xx - cx0) / max(1.0, rx))
        r_, g_, b_ = cpx[xx, yy][:3]
        cpx[xx, yy] = (int(min(255, r_ + (255 - r_) * f * 0.55)),
                       int(min(255, g_ + (255 - g_) * f * 0.60)),
                       int(min(255, b_ + (255 - b_) * f * 0.30)), a)

out = Image.alpha_composite(out, crown)

# Whatever of the old flat cut is still exposed is bitten into with a wavy edge, so that no straight
# run of it survives. Taking leaves away cannot look pasted on the way adding them can.
al = out.split()[3]
apx = al.load()
notch = Image.new('L', out.size, 255)
npx = notch.load()
ph = [random.uniform(0, math.tau) for _ in range(5)]
for xx in range(W):
    # the top of the silhouette in this column
    top = None
    for yy in range(out.size[1]):
        if apx[xx, yy] > 150: top = yy; break
    if top is None: continue
    run = 0
    for yy in range(top, min(top + 40, out.size[1])):
        if apx[xx, yy] > 150: run += 1
        else: break
    if run < 12: continue                       # a thin wisp: leave it be
    d = 0.0
    for i, a_ in enumerate(ph):                 # a few waves of different lengths, summed
        d += (1.0 / (i + 1)) * (0.5 + 0.5 * math.sin(xx / (7.0 + i * 11) + a_))
    d = d / 2.28                                 # 0..1
    bite = int(d * 13)
    for yy in range(top, top + bite):
        npx[xx, yy] = 0
notch = notch.filter(ImageFilter.GaussianBlur(0.8))
out.putalpha(ImageChops.multiply(out.split()[3], notch))

# the dark rim, laid along the finished outline of the new growth only
al = out.split()[3].point(lambda v: 255 if v > 150 else 0)
rim = ImageChops.subtract(al, al.filter(ImageFilter.MinFilter(7))).filter(ImageFilter.GaussianBlur(1.1))
rpx = rim.load(); opx = out.load()
for yy in range(y0 + 34):
    for xx in range(W):
        k = rpx[xx, yy] / 255 * 0.78
        if k > 0.03 and opx[xx, yy][3]:
            r_, g_, b_, a = opx[xx, yy]
            opx[xx, yy] = (int(r_ * (1 - k)), int(g_ * (1 - k)), int(b_ * (1 - k)), a)

out = out.crop(out.getbbox())
print('grown ->', out.size)
out.save('assets/quest/enemies/ent.webp', 'WEBP', quality=92, method=6)
