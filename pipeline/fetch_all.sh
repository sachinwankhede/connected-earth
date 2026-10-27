#!/bin/sh
# fetch_all.sh: run the slow Wikimedia fetches, one after the other. Safe to stop and start again (both resume).
cd "$(dirname "$0")/.." || exit 1
python3 pipeline/photos.py photos/places data data-auto && python3 pipeline/about.py && python3 build/species.py about && python3 build/species.py pack && python3 build/build.py --all
