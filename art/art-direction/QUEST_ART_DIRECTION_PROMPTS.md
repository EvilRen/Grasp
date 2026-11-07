# Quest — Art Direction Board: Master Prompt Spec

Reusable prompt pack for the "Quest" art-direction board (fantasy-turning-cosmic rogue-like
deck-battler). Every panel shares one **Style Block** and one **Exclusion Block** so the set
reads as a single hand. Swap the *Subject Block* to extend the set to new cards, heroes or
enemies without drifting off-style.

Generated with: `Z-Image-Turbo` (diffusion transformer, flow-matching scheduler).
Settings used: `steps 14` (16 for the full board), `shift 3`, fixed seeds, `random_seed false`.

---

## 1. Style Block  (append to every panel prompt)

> AAA collectible card game key art, painterly digital illustration, oil and gouache brushwork
> with crisp rendered edges, dramatic rim lighting, soft volumetric glow, gentle
> bioluminescence, clean readable silhouette, rich but uncluttered, very high detail,
> cinematic contrast.

## 2. Palette Block

> Strict limited palette: deep dark base with teal, antique gold and crimson accents only.

Hex anchors used for the board chrome and compositing:

| Role | Hex | Use |
|---|---|---|
| Base / void | `#0B0D10` | board background, card bleed |
| Base raised | `#14181D` | section plates |
| Teal primary | `#2FD6C3` | energy, glyphs, rim light |
| Teal deep | `#0E5E5C` | armour enamel, jade frames |
| Antique gold | `#C9A227` | filigree, hairlines, strength arrow |
| Crimson | `#B5232B` | attack frame, heart, warm rim light |
| Moss green | `#4FD15A` | enemy bioluminescence, poison only |
| Royal violet | `#6B3FA0` | POWER card celestial frame only |

> **Palette note:** the brief's strict palette is teal / antique gold / crimson, but the POWER
> card is specified as royal violet + antique gold. Violet is therefore scoped **only** to the
> POWER frame and the cosmic backdrop, kept deep and desaturated so it sits inside the dark
> base rather than competing as a fourth accent. Same for the poison-droplet green.

## 3. Exclusion Block  (append to every panel prompt — this model has no negative-prompt field)

> Absolutely no text, no letters, no alphabet, no words, no numbers, no digits, no
> inscriptions, no calligraphy, no labels, no logos, no watermark, no signature anywhere in
> the image.

**Why it is phrased this way:** "no runes" alone fails — the model renders decorative glyphs
that read as pseudo-script. Naming the *ornament you do want* ("concentric circles, spirals,
chevrons and interlocking knotwork, purely ornamental geometry with no writing of any kind")
suppresses lettering far more reliably than negation alone. Same trick for blank nameplates:
describe them as "a perfectly smooth polished metal nameplate that is completely empty and
unmarked" rather than "a banner with no text on it".

---

## 4. Panel prompts

Each entry: `file` · `resolution` · `seed`. Full prompt = Subject + Style + Palette + Exclusion.

### 4.1 ATTACK card — `panels/card_attack.webp` · 832x1248 (2:3) · seed `710401`
A single vertical fantasy collectible trading card, isolated and centered on a deep near-black
charcoal background. The card has an ornate rectangular border made of molten crimson lava
veins glowing through dark forged black-iron filigree, with small antique gold rivets. Inside
the border is a finished painted illustration: a knight in weathered silver-and-teal plate
armour delivering a powerful downward sword strike, the blade trailing a brilliant glowing teal
energy arc, crimson embers and sparks flying. Near the top of the card there is a blank empty
ornamental title banner plate, a perfectly smooth polished metal nameplate that is completely
empty with nothing written on it. Set into the top-left corner of the frame is a small empty
circular energy-gem socket, a plain recessed round bezel.

### 4.2 SKILL card — `panels/card_skill.webp` · 832x1248 (2:3) · seed `710422`
A single vertical fantasy collectible trading card, isolated and centered on a deep near-black
charcoal background. The card has an ornate rectangular border of polished teal jade inlay and
brushed antique silver filigree with delicate antique gold trim and small scrollwork corners.
Inside the border is a finished painted illustration: a radiant heater-shaped runic shield
floating in darkness, its surface decorated with glowing abstract concentric circles, spirals,
chevrons and interlocking knotwork patterns, purely ornamental geometry with no writing of any
kind, wrapped in a soft protective dome of luminous teal energy, motes of light drifting around
it. Near the top of the card there is a blank empty ornamental title banner plate, a perfectly
smooth polished metal nameplate that is completely empty and unmarked. Set into the top-left
corner of the frame is a small empty circular energy-gem socket, a plain recessed round bezel.

> Seed `710402` was the first attempt and was rejected: the shield glyphs resolved into
> letter-like forms. The "purely ornamental geometry" clause fixed it on seed `710422`.

### 4.3 POWER card — `panels/card_power.webp` · 832x1248 (2:3) · seed `710403`
A single vertical fantasy collectible trading card, isolated and centered on a deep near-black
charcoal background. The card has an ornate celestial rectangular border of deep royal violet
enamel and antique gold scrollwork, studded with tiny constellations and star points. Inside
the border is a finished painted illustration: a floating glowing arcane sigil, an intricate
circular geometric mandala of light hovering in cosmic void, radiating soft violet and antique
gold energy, faint nebula mist and star dust swirling behind it. Near the top of the card there
is a blank empty ornamental title banner plate, a perfectly smooth polished metal nameplate that
is completely empty with nothing written on it. Set into the top-left corner of the frame is a
small empty circular energy-gem socket, a plain recessed round bezel.

### 4.4 Hero — `panels/hero.webp` · 1104x1472 (3:4) · seed `710424`
Half-body portrait, cropped at the waist, close framing of head chest and shoulders only, of a
brave fantasy knight hero, centered on a deep near-black charcoal background with soft teal
atmospheric haze. He wears weathered silver plate armour with teal enamelled panels, deeply
scratched and battle-worn, antique gold edging on the pauldrons, and a ragged tattered dark teal
cloak frayed and torn. He raises a glowing runic shield engraved with luminous abstract spiral
and knotwork patterns. His face is calm, determined and resolute, lit by cool teal bounce light
from the shield and a warm crimson rim light from behind.

> Seed `710404` without the "cropped at the waist, close framing" clause returned a full-body
> figure. Z-Image reads "half-body" as a weak hint; the explicit crop instruction is required.

### 4.5 Enemy — `panels/enemy.webp` · 1024x1536 (2:3) · seed `710405`
Menacing full-body fantasy enemy creature, a towering thorned forest-guardian beast, standing
centered in full view on a deep near-black charcoal background with faint teal mist at its feet.
Its hide is twisted bark and gnarled heartwood crusted with moss and pale lichen, long cruel
thorns bristling along its spine and shoulders, a crown of antler-like thorn branches, heavy
clawed root-like limbs. Its deep-set eyes blaze with glowing toxic green light, and a faint
bioluminescent green glow seeps from cracks between the bark plates. Hostile, hulking,
predatory stance.

### 4.6 UI icon row — `panels/icons.webp` · 1680x720 (21:9) · seed `710406`
A tidy horizontal row of exactly six separate glowing fantasy mobile game user interface icons,
evenly spaced in a single straight line on a plain deep near-black charcoal background. From
left to right: a faceted glowing teal energy crystal; an antique silver and teal heraldic
shield; a crimson-hilted steel sword pointing upward; a glowing toxic green poison droplet; a
bold antique gold upward arrow; a glowing crimson heart. Each icon is a compact chunky emblem
with a bold, simple, instantly readable silhouette, soft volumetric glow, teal and gold rim
light, and a subtle dark base. All six share one identical painterly style, game asset sheet,
clean and uncluttered.

### 4.7 Backdrop A, enchanted forest — `panels/bg_forest.webp` · 1280x720 (16:9) · seed `710407`
Atmospheric fantasy battle backdrop environment, wide cinematic shot of a luminous enchanted
forest at night: colossal ancient trees with gnarled roots, drifting bioluminescent teal spores
and glowing motes in the air, patches of softly glowing moss and pale mushrooms, a faint shaft
of warm antique gold light breaking through the dense canopy, low teal ground mist, an empty
clear foreground arena with no characters.

### 4.8 Backdrop B, cosmic star-portal — `panels/bg_cosmic.webp` · 1280x720 (16:9) · seed `710408`
Atmospheric cosmic battle backdrop environment, wide cinematic shot of a vast swirling
star-portal in deep space: a great circular rift of radiant antique gold and teal energy,
swirling violet and crimson nebula clouds spiralling inward, scattered brilliant stars and
drifting stone fragments catching rim light, an empty clear foreground platform with no
characters.

### 4.9 Single-shot whole board — `quest_board_singleshot.webp` · 1152x2048 (9:16) · seed `710409` · steps 16
A single tall vertical art direction style board for a premium fantasy mobile card game, neatly
arranged as one elegant presentation sheet on a deep near-black charcoal background with
generous dark spacing between sections. TOP ROW: three ornate vertical collectible card frames
side by side, each with a finished painted inner illustration, a blank empty title banner plate
and a small empty circular gem socket in the top-left corner; the left card has a molten crimson
and dark iron border with a knight making a glowing teal sword strike inside, the middle card
has a teal jade and silver border with a radiant runic shield inside, the right card has a royal
violet and antique gold celestial border with a floating glowing arcane sigil inside. MIDDLE
ROW: on the left a half-body portrait of a brave knight in weathered silver and teal plate
armour with a tattered cloak and glowing runic shield; on the right a menacing full-body thorned
forest guardian beast with bark and moss hide and glowing green eyes. LOWER ROW: a tidy
horizontal row of six small glowing game interface icons with bold readable silhouettes, a teal
energy crystal, a shield, a sword, a green poison droplet, a gold upward arrow and a crimson
heart. BOTTOM: a thin horizontal strip of two atmospheric battle backdrops side by side, a
luminous enchanted forest and a cosmic star portal with swirling nebula. One single consistent
painterly art style throughout, cohesive.

---

## 5. Porting to other models

| Model | Changes needed |
|---|---|
| **Midjourney v6/v7** | Drop the Exclusion Block into `--no text, letters, numbers, watermark, signature, logo`. Add `--ar 9:16 --style raw --s 250`. Keep Style Block as prose before the flags. |
| **FLUX.1 dev / Krea** | Works as-is; FLUX respects long prose. Use guidance 3.5, 28–40 steps. Exclusion Block still goes in the positive prompt (FLUX has no true negative). |
| **SDXL / Illustrious** | Move the Exclusion Block to the negative prompt verbatim and add `text, watermark, signature, jpeg artifacts, extra limbs, blurry`. CFG 6–7, 30+ steps, and add `score_9, score_8_up` style tags if using a Pony derivative. |
| **Qwen-Image** | Strong at text rendering, so it *will* invent lettering. Double the Exclusion Block and add "blank unmarked surfaces". |

## 6. Reproducing the board

```bash
python3 art/art-direction/build_board.py          # composites panels/ -> quest_art_direction_board.png
```

The build script trims the dark bleed around each card, normalises card heights, cover-crops the
hero and enemy to a shared cell, and lays everything on a 1200x2133 (9:16) graded dark board.

---

## 7. Provenance of the shipped panels

The board mixes two generators. Panels 4.1–4.5 came from Z-Image-Turbo at the seeds listed
above. The Hugging Face ZeroGPU quota ran out before the backdrops and the icon re-roll, so
those three were finished in Gemini from `QUEST_GEMINI_BOARD_PROMPTS.md`:

| Panel | Generator | File |
|---|---|---|
| ATTACK / SKILL / POWER cards | Z-Image-Turbo, seeds 710401 / 710422 / 710403 | `panels/card_*.webp` |
| Hero, enemy | Z-Image-Turbo, seeds 710424 / 710405 | `panels/hero.webp`, `panels/enemy.webp` |
| Icon row | Gemini, prompt C | `panels/icons.jpg` |
| Forest, cosmic backdrops | Gemini, prompts A and B | `panels/bg_forest.jpg`, `panels/bg_cosmic.jpg` |

The two hands sit together because both were given the same Style, Palette and Exclusion
blocks. Gemini's output runs a touch smoother in the brushwork and a touch cooler in the
shadows; at panel size on a dark board that reads as depth rather than as a seam. If the set
is ever extended, matching Z-Image is the harder of the two to hit — generate new character
and card art there first, and let Gemini fill environments and icons around it.

The single-shot whole-board comparison was never generated; the quota ran out before it. The
composited board is the only version, which is the one worth keeping anyway — a single pass
over a layout this dense loses the card borders and the icon silhouettes.
