"""
Quick entry point — open the main dashboard or start a local server.
Usage:
  py open_dashboard.py          # open dashboard
  py open_dashboard.py --serve  # start local HTTP server (for phone)
"""

import argparse
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_SCRIPT = os.path.join(BASE, "webui", "dashboard.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open main dashboard")
    parser.add_argument("--serve", action="store_true", help="Start local HTTP server for phone access")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server")
    args = parser.parse_args()

    cmd = f'"{sys.executable}" "{DASHBOARD_SCRIPT}" --all'
    if args.serve:
        cmd += f" --serve --port {args.port}"
    print(f"Running: {cmd}")
    os.system(cmd)
