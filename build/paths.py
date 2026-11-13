"""Where the build reads and writes (#787).

CODE_ROOT  the repository: src/, node_modules/, icons, lib/ (always the checkout).
DATA_ROOT  data/ and photos/: the repository by default; tests/fixtures for the fixture build.
OUT_ROOT   index.html, pilot/, sw.js, api/ and the copied libraries: the repository by default.

Set with `--data-root DIR` and `--out-root DIR` on build/build.py, or the environment variables
CE_DATA_ROOT and CE_OUT_ROOT. With neither set, nothing changes.
"""
import os

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.abspath(os.environ.get('CE_DATA_ROOT') or CODE_ROOT)
OUT_ROOT = os.path.abspath(os.environ.get('CE_OUT_ROOT') or CODE_ROOT)
