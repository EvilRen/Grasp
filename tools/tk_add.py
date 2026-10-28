#!/usr/bin/env python3
"""Add approved player cards to Tachles' deck (assets/tachles/deck.json).
Each card arrives by email (FormSubmit) with a "json" field; paste those values one per line into a text file, then:
    python3 tools/tk_add.py approved.txt
A line is either a white card: "text"  or a black card: ["text with ___", 2]. Duplicates are skipped. Bump TK_V in index.html after."""
import json, sys
deck_path = 'assets/tachles/deck.json'
deck = json.load(open(deck_path))
have_w, have_b = set(deck['w']), {b[0] for b in deck['b']}
added = 0
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.strip()
    if not line: continue
    v = json.loads(line)
    if isinstance(v, str):
        if v not in have_w: deck['w'].append(v); have_w.add(v); added += 1
    elif isinstance(v, list) and len(v) == 2 and '___' in v[0]:
        if v[0] not in have_b: deck['b'].append([v[0], max(1, min(3, int(v[1])))]); have_b.add(v[0]); added += 1
json.dump(deck, open(deck_path, 'w'), ensure_ascii=False, separators=(',', ':'))
print('added', added, '-> black', len(deck['b']), 'white', len(deck['w']))
