#!/bin/sh
# fetch_all.sh: run the slow Wikimedia fetches, one after the other. Safe to stop and start again (both resume).
cd "$(dirname "$0")/.." || exit 1
python3 jobs/photos.py photos/places data/places data-auto && python3 jobs/about.py && python3 build/species.py about && python3 build/species.py pack && python3 build/build.py --all
