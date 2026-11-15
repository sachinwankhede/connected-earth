#!/usr/bin/env python3
"""cleanauthors.py: write the one stored form of the author into the place and species pictures (#887, #934; owner, 15 Nov: "treat email as no author").
Usage: cleanauthors.py [--dry]   (run from the repository root; --dry lists and changes nothing). No network.
Every stored place picture whose author text lib/author_clean.py would change (an email, a talk-page stamp, a web address, an "original uploader" sentence, camera boilerplate)
gets the cleaned text. A CC BY / CC BY-SA picture whose author is only an email is NOT given "Unknown author" here: it is listed as `needs-author`, left as it is, and
jobs/dropunnamed.py (which asks Commons again and removes what has no author) deals with it. Goes through lib/place_photos.py and, once photos/species_pictures.json exists (keyed by sid, #934), lib/species_photos.py.
Prints one `cleaned <id>: <old> -> <new>` line each (species lines read `cleaned species <sid>`)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'lib'))
from place_photos import PlacePhotos
from species_photos import SpeciesPhotos
import species_pics
import author_clean as ac

def clean_rows(w, dry=False):
    """Returns (cleaned [(id, old, new)], needs_author [id])."""
    cleaned, needs = [], []
    for pid in w.dirty_authors():
        e = w.pics[pid]; old = e.get('a') or ''; new = ac.clean_author(old)
        if not new:
            if (e.get('l') or '').upper().startswith('CC BY'): needs.append(pid)
            else: cleaned.append((pid, old, 'Unknown author')); e['a'] = e['a'] if dry else 'Unknown author'
            continue
        cleaned.append((pid, old, new))
        if not dry: e['a'] = new
    if cleaned and not dry: w.commit()
    return cleaned, needs

def main():
    dry = '--dry' in sys.argv; tc = tn = 0
    for kind, w in (('place', PlacePhotos(ROOT)), ('species', SpeciesPhotos(ROOT) if species_pics.new_shape(ROOT) else None)):
        if w is None: print('species pictures are not keyed by species id yet: skipped (migration #934)'); continue
        cleaned, needs = clean_rows(w, dry); tc += len(cleaned); tn += len(needs); tag = '' if kind == 'place' else 'species '
        for pid, old, new in cleaned: print('cleaned %s%s: %s -> %s' % (tag, pid, old[:80], new))
        for pid in needs: print('needs-author %s%s: %s' % (tag, pid, (w.pics[pid].get('a') or '')[:80]))
    print(tc, 'authors', 'to clean' if dry else 'cleaned', '|', tn, 'need an author (run data-dropunnamed)')
if __name__ == '__main__': main()
