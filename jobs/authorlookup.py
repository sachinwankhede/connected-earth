#!/usr/bin/env python3
"""authorlookup.py: a READ-ONLY report on pictures whose author is unknown (#887).
Usage: authorlookup.py   (run from the repository root; changes nothing, writes only to stdout and the run summary)

A CC BY or CC BY-SA picture needs a named author. Some of ours say "Unknown author" (places) or "Unknown" (species): the writers took the Commons "Artist" field
and, when it was empty, wrote that text, and nothing refused the picture. This job asks Commons about each such picture and says, for each, whether an author can be
found and where from, so the owner can see the numbers before deciding to fill them in, remove them or hide them:
  artist       the Commons Artist field now has a real name (the stored credit is out of date)
  attribution  the file's own Attribution field names someone
  own-work     the Artist field is empty, the Credit says "own work", so the uploader (first revision) is the author; the name is the uploader's
  none         nothing usable: the picture cannot be credited
It never proposes an uploader's name unless the credit says own work (an uploader is not always the author). Host: commons.wikimedia.org (already allowed)."""
import json, os, re, sys, urllib.parse, html
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib')); import wm, author_clean
from author_lookup import API, UNKNOWN, strip, unknown, clean, by_licence, file_of, classify, lookup   # the rules live in lib/author_lookup.py (moved unchanged)







def candidates(places, species):
    """CC BY / CC BY-SA pictures with an unknown author: [{'kind', 'key', 'file', 'licence', 'author'}] in a stable order."""
    out = []
    for kind, rows in (('place', places), ('species', species)):
        for key in sorted(rows):
            r = rows[key]
            if isinstance(r, dict) and by_licence(r.get('l')) and unknown(r.get('a')) and file_of(r.get('p')):
                out.append(dict(kind=kind, key=key, file=file_of(r['p']), licence=r.get('l'), author=r.get('a') or ''))
    return out



def report(rows):
    """Markdown: counts by kind and class, then one line per picture."""
    lines = ['| kind | CC BY / BY-SA with unknown author | artist | attribution | own-work | none |', '|---|---|---|---|---|---|']
    for kind in ('place', 'species'):
        mine = [r for r in rows if r['kind'] == kind]
        lines.append('| %s | %d | %s |' % (kind, len(mine), ' | '.join(str(sum(1 for r in mine if r['class'] == c)) for c in ('artist', 'attribution', 'own-work', 'none'))))
    lines += ['', '| kind | picture | licence | stored author | class | author found |', '|---|---|---|---|---|---|']
    for r in rows:
        lines.append('| %s | %s | %s | %s | %s | %s |' % (r['kind'], r['key'].replace('|', '/'), r['licence'], r['author'], r['class'], r['name'].replace('|', '/')))
    return '\n'.join(lines)

def main():
    load = lambda p: json.load(open(p)) if os.path.exists(p) else {}
    cands = candidates(load('photos/places/places.json'), load('photos/species_metadata.json'))
    print(len(cands), 'pictures to look up', flush=True)
    rows = []
    for k, c in enumerate(cands, 1):
        c['class'], c['name'] = lookup(c['file']); rows.append(c)
        if k % 10 == 0: print(k, 'of', len(cands), flush=True)
    text = report(rows); print(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'): open(os.environ['GITHUB_STEP_SUMMARY'], 'a').write('### Unknown-author pictures (read-only)\n\n' + text + '\n')
if __name__ == '__main__': main()
