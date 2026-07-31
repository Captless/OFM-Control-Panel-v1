"""Re-export from core.text_generator for backward compatibility."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.text_generator import *  # noqa: F401,F403
