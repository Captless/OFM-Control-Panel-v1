"""Shared helper — daily batch folder: outputs/YYYY-MM-DD/"""

from datetime import date
from pathlib import Path


def day_path(root=None, subdir=None):
    """Return outputs/<today>[/<subdir>] as absolute Path, creating if needed."""
    root = Path(root or Path(__file__).resolve().parent.parent / "outputs")
    today = date.today().isoformat()  # YYYY-MM-DD
    p = root / today
    if subdir:
        p = p / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p