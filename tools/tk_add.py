#!/usr/bin/env python3
"""Add approved player cards to Tachles' deck (assets/tachles/deck.json).
Each card arrives by email (FormSubmit) with a "json" field; paste those values one per line into a text file, then:
    python3 tools/tk_add.py approved.txt
A line is either a white card: "text"  or a black card: ["text with ___", 2]. Optionally end the line with its level and packs,
e.g.  "text" #3sg  (level 1 light / 2 crude / 3 no limits; packs: s sex, g gross, r religion, p politics, a army, d death, x drugs,
c real people, h Holocaust/terror, e racism/edot, f family/food, t tech, i Israeli daily life). Without it: level 2, no packs.
Duplicates are skipped. Bump TK_V in index.html after."""
import json, sys
deck_path = 'assets/tachles/deck.json'
deck = json.load(open(deck_path))
have_w, have_b = set(deck['w']), {b[0] for b in deck['b']}
added = 0
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.strip()
    if not line: continue
    meta = '2'
    if ' #' in line and line.rsplit(' #', 1)[1][:1] in '123': line, meta = line.rsplit(' #', 1)
    v = json.loads(line)
    if isinstance(v, str):
        if v not in have_w: deck['w'].append(v); deck['wm'].append(meta); have_w.add(v); added += 1
    elif isinstance(v, list) and len(v) == 2 and '___' in v[0]:
        if v[0] not in have_b: deck['b'].append([v[0], max(1, min(3, int(v[1])))]); deck['bm'].append(meta); have_b.add(v[0]); added += 1
json.dump(deck, open(deck_path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('added', added, '-> black', len(deck['b']), 'white', len(deck['w']))
