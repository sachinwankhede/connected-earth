#!/usr/bin/env python3
"""One-off (#648): write the source name `s` into the species credits that point at GBIF or Openverse, so the build no longer derives it.
New credits get `s` from the job that writes them. Commons credits have none (the app default is Wikimedia Commons).
Run: python3 jobs/credit_source_backfill.py [--dry]"""
import json, os, sys, urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
META = os.path.join(ROOT, 'photos', 'species_metadata.json')
SOURCES = (('www.gbif.org', 'GBIF'), ('openverse.org', 'Openverse'))   # where the credit page is, for the pictures that are not from Commons


def source_of(page):
    try: u = urllib.parse.urlsplit(page or '')
    except ValueError: return ''
    return next((n for h, n in SOURCES if u.scheme == 'https' and u.hostname == h), '')


def backfill(meta):
    """Returns the number of credits that got `s`."""
    n = 0
    for c in meta.values():
        if isinstance(c, dict) and 's' not in c and source_of(c.get('p')): c['s'] = source_of(c['p']); n += 1
    return n


def main():
    meta = json.load(open(META))
    n = backfill(meta)
    print('credits that got a source name:', n)
    if n and '--dry' not in sys.argv:
        json.dump(meta, open(META, 'w'), ensure_ascii=False, indent=0, sort_keys=True)


if __name__ == '__main__':
    main()
