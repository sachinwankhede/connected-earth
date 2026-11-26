#!/usr/bin/env python3
"""droporphans.py (#1183, owner 26 Nov): delete the node picture entries no place shows (a row was removed, so its concept has no node), with their files and their missing and tried records.
Through lib/node_photos.py. A concept some node shows is never touched.
  python3 jobs/droporphans.py [--apply]"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import node_photos

def drop(root, write=True):
    np = node_photos.NodePhotos(root); orphans = sorted({n for _, n in np.orphans(node_photos.concepts(root))}); gone = []
    for nid in orphans:
        if nid in np.pics: np._delete.append(np._path(np.pics.pop(nid)['f']))
        np.miss_.pop(nid, None); np.tried.pop(nid, None); gone.append(nid)
    if write and gone: np.commit()
    return gone

if __name__ == '__main__':
    g = drop(ROOT, '--apply' in sys.argv); print(len(g), 'orphan node pictures', 'dropped' if '--apply' in sys.argv else 'found')
