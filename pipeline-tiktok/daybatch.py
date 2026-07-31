"""daybatch — re-export from core.daybatch for backward compatibility."""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from core.daybatch import *  # noqa: F401,F403
from core.daybatch import day_path  # noqa: F401 — explicit for clarity
