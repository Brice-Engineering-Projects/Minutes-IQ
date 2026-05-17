"""Project-local import shim for the src layout.

This lets `python` run from the repository root without requiring callers to
set `PYTHONPATH=src` manually.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if SRC.is_dir():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
