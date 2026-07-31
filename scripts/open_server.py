"""Start OFM Control Panel server and open browser."""

import os
import subprocess
import sys
import webbrowser

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(BASE, "webui", "server.py")

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8000")
    proc = subprocess.Popen(
        [sys.executable, "-u", SERVER],
        cwd=BASE,
    )
    print(f"Server started (PID {proc.pid})")
    print(f"Open: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nStopped")
