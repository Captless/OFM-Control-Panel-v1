"""
OFM Control Panel â€” local HTTP server with homepage UI.
Serves at http://localhost:8000

Run:  py server.py
"""

import concurrent.futures
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE = Path(__file__).resolve().parent.parent      # OFM root
OUTPUTS = BASE / "outputs"
PIPELINE_DIR = BASE / "pipeline"
WEBUI_DIR = BASE / "webui"
ACTIVITY_LOG = WEBUI_DIR / "activity.json"
PORT = 8000

sys.path.insert(0, str(BASE))
from core.config import PHOTO_PRICE, SETTINGS_PATH, list_wavespeed_accounts, set_wavespeed_account, remove_wavespeed_account, rename_wavespeed_account, get_active_wavespeed_key, set_active_wavespeed_account, test_wavespeed_account

sys.path.insert(0, str(PIPELINE_DIR))
from prompt_bank import list_presets, build_jobs, build_jobs_multi

API_DIR = BASE / "api"
sys.path.insert(0, str(API_DIR))
from wavespeed_client import WaveSpeedClient

_balance_cache = {"time": 0, "value": None}

def _get_balance(account_label=None):
    now = time.time()
    if account_label is None and now - _balance_cache["time"] < 60 and _balance_cache["value"] is not None:
        return _balance_cache["value"]
    try:
        if account_label:
            # look up raw key for the given account label from settings
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            settings = json.loads(raw)
            key = settings.get("wavespeed_accounts", {}).get(account_label)
            if not key:
                return 0.0
        else:
            key = get_active_wavespeed_key()
        if not key:
            return 0.0
        client = WaveSpeedClient(key)
        bal = client.get_balance()
        if account_label is None:
            _balance_cache["time"] = now
            _balance_cache["value"] = bal
        return bal
    except Exception:
        return 0.0


# â”€â”€ Activity log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _load_activity():
    if ACTIVITY_LOG.exists():
        try:
            return json.loads(ACTIVITY_LOG.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _log_activity(message):
    entries = _load_activity()
    entries.insert(0, {
        "time": datetime.now().strftime("%H:%M"),
        "message": message,
    })
    # keep last 50
    ACTIVITY_LOG.write_text(json.dumps(entries[:50], indent=2), encoding="utf-8")


# â”€â”€ Collect outputs grouped by date â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

from collections import defaultdict

def _collect():
    if not OUTPUTS.is_dir():
        return []
    entries = sorted(OUTPUTS.iterdir())
    entries = [e for e in entries if e.is_dir() and (list(e.rglob("*.mp4")) or list(e.rglob("*.png")) or list(e.rglob("*.jpg")))]
    date_groups = defaultdict(list)
    for entry in sorted(entries, key=lambda e: e.stat().st_mtime, reverse=True):
        dt = datetime.fromtimestamp(entry.stat().st_mtime)
        date_key = dt.strftime("%Y-%m-%d")
        date_groups[date_key].append({"entry": entry, "mtime": entry.stat().st_mtime, "dt": dt})

    sorted_dates = sorted(date_groups.keys(), reverse=True)
    batches = []
    for date_key in sorted_dates:
        group = date_groups[date_key]
        date_label = group[0]["dt"].strftime("%B %d, %Y")
        all_items = []
        stem_counts = {}
        for g in sorted(group, key=lambda x: x["mtime"], reverse=True):
            entry = g["entry"]
            mp4s = sorted(entry.rglob("*.mp4"))
            pngs = sorted(entry.rglob("*.png"))
            jpgs = sorted(entry.rglob("*.jpg"))
            txts = {f.stem: f for f in entry.rglob("*.txt")}
            prompt_files = {f.stem: f for f in entry.rglob("*.prompt")}
            meta = {}
            meta_path = entry / "meta.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            seen = set()
            for path in sorted(mp4s + pngs + jpgs, key=lambda p: p.stat().st_mtime, reverse=True):
                stem = path.stem
                if stem in seen:
                    continue
                seen.add(stem)
                unique_stem = stem
                if stem_counts.get(stem, 0) > 0:
                    unique_stem = f"{stem}_{stem_counts[stem] + 1}"
                stem_counts[stem] = stem_counts.get(stem, 0) + 1
                txt = txts.get(stem)
                txt_content = txt.read_text(encoding="utf-8").strip() if txt else ""
                meta_val = meta.get(stem)
                if not isinstance(meta_val, dict):
                    prefix = stem.split("_")[0]
                    candidates = [(k, v) for k, v in meta.items() if k.startswith(prefix + "_")]
                    labeled = [(k, v) for k, v in candidates if v.get("labels")]
                    meta_val = (labeled[0][1] if labeled else (candidates[0][1] if candidates else {}))
                if isinstance(meta_val, dict):
                    labels = meta_val.get("labels", "")
                    prompt = meta_val.get("prompt", "")
                    prompt_file = prompt_files.get(stem)
                    if prompt_file:
                        try:
                            prompt = prompt_file.read_text(encoding="utf-8").strip()
                        except Exception:
                            pass
                    negative_prompt = meta_val.get("negative_prompt", "")
                    guidance_scale = meta_val.get("guidance_scale", 0.55)
                else:
                    labels = prompt = negative_prompt = ""
                    guidance_scale = 0.55
                rel = os.path.relpath(str(path), str(OUTPUTS))
                src = rel.replace("\\", "/")
                all_items.append({
                    "stem": unique_stem, "src": src, "is_video": path.suffix == ".mp4",
                    "txt_content": txt_content, "filename": path.name, "labels": labels,
                    "prompt": prompt, "negative_prompt": negative_prompt, "guidance_scale": guidance_scale,
                })
        if all_items:
            batches.append({"id": date_key, "name": date_label, "items": all_items})
    return batches


# â”€â”€ Pipeline subprocess â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_pipeline_runs = {}
_state_lock = threading.Lock()


def _prune_pipeline_runs(max_keep=50):
    """Drop oldest completed runs to bound memory (done entries only)."""
    if len(_pipeline_runs) <= max_keep:
        return
    done_runs = sorted(
        (rid for rid, st in _pipeline_runs.items() if st.get("done")),
        key=lambda rid: _pipeline_runs[rid].get("updated_at", 0),
    )
    for rid in done_runs[: len(_pipeline_runs) - max_keep]:
        _pipeline_runs.pop(rid, None)


def _update_progress(run_id, line):
    """Parse a single stdout line into _pipeline_runs state."""
    with _state_lock:
        state = _pipeline_runs.get(run_id)
        if state is None:
            return
        state["updated_at"] = time.time()
        if line.startswith("@P "):
            parts = line[3:].split("|", 1)
            if len(parts) == 2:
                state["stage"] = parts[0]
                state["detail"] = parts[1]
        m = re.match(r"^\[(\d+)/(\d+)\]\s+(.*)", line)
        if m:
            state["current"] = int(m.group(1))
            state["total"] = int(m.group(2))
            if not line.startswith("@P "):
                state["stage"] = "processing"
                state["detail"] = m.group(3)


def _start_pipeline(mode, prompts, with_text=False):
    """Start pipeline in a daemon thread. Returns run_id for progress polling."""
    run_id = uuid.uuid4().hex[:8]
    cmd = [sys.executable, str(PIPELINE_DIR / "pipeline.py"), "--prompts", prompts]
    if with_text:
        cmd.append("--with-text")

    with _state_lock:
        _pipeline_runs[run_id] = {
            "stage": "starting", "detail": "",
            "current": 0, "total": 0,
            "done": False, "ok": None, "duration_s": 0,
            "updated_at": time.time(),
        }

    def _run():
        t0 = time.time()
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            for line in proc.stdout:
                _update_progress(run_id, line.rstrip())
            proc.wait()
            duration = round(time.time() - t0, 1)
            ok = proc.returncode == 0
            stderr = proc.stderr.read().strip()
            msg = "Done" if ok else ((stderr.split("\n")[-1] if stderr else "") or f"Exit code {proc.returncode}")
            with _state_lock:
                _pipeline_runs[run_id].update(
                    stage="done" if ok else "failed", detail=msg,
                    done=True, ok=ok, duration_s=duration,
                    updated_at=time.time(),
                )
                _prune_pipeline_runs()
        except Exception as e:
            with _state_lock:
                _pipeline_runs[run_id].update(
                    stage="failed", detail=str(e),
                    done=True, ok=False, duration_s=round(time.time() - t0, 1),
                    updated_at=time.time(),
                )
                _prune_pipeline_runs()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return run_id


def _run_dashboard():
    cmd = [sys.executable, str(WEBUI_DIR / "dashboard.py"), "--all"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        ok = proc.returncode == 0
        return {"ok": ok, "output": proc.stdout.strip() if ok else proc.stderr.strip()}
    except Exception as e:
        return {"ok": False, "output": str(e)}


# â”€â”€ HTTP Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        # Serve static assets (CSS, JS, images)
        if self.path.startswith("/static/"):
            file_path = STATIC_DIR / self.path[8:]  # strip "/static/"
            if file_path.is_file():
                content_types = {".css": "text/css", ".js": "text/javascript", ".html": "text/html", ".png": "image/png", ".jpg": "image/jpeg"}
                ct = content_types.get(file_path.suffix, "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_error(404)
            return

        if path == "/" or path == "/index.html":
            self._serve_homepage()
        elif path == "/api/ping":
            self._json({"ok": True})
        elif path == "/api/activity":
            self._json(_load_activity())
        elif path == "/api/outputs":
            self._json(_collect())
        elif path == "/api/presets":
            self._json(list_presets())
        elif path.startswith("/api/balance/account"):
            qs = parse_qs(parsed.query)
            account_label = qs.get("account", [None])[0]
            if account_label:
                bal = _get_balance(account_label)
            else:
                bal = _get_balance()
            self._json({"balance": bal})
        elif path == "/api/balance":
            self._json({"balance": _get_balance(), "per_photo": PHOTO_PRICE})

        elif path == "/api/balance/total":
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            settings = json.loads(raw)
            accounts = settings.get("wavespeed_accounts", {})
            total = 0.0
            for label in accounts:
                try:
                    total += _get_balance(label)
                except Exception:
                    pass
            self._json({"total": total, "count": len(accounts)})

        elif path == "/api/dashboard/refresh":
            self._json({"ok": True, "outputs": _collect(), "msg": "ok"})
        elif path == "/api/progress":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]
            if not run_id:
                self._json({"error": "missing run_id"}, 400)
                return
            with _state_lock:
                state = _pipeline_runs.get(run_id)
            if state is None:
                # Terminal shape so clients stop polling instead of looping forever
                self._json({
                    "done": True, "ok": False, "stage": "failed",
                    "detail": "run not found (server restarted?)",
                    "current": 0, "total": 0,
                })
                return
            self._json(dict(state))

        elif path == "/api/wavespeed/status":
            key = get_active_wavespeed_key()
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            owner = json.loads(raw).get("active_wavespeed_account", "") if key else ""
            self._json({"connected": bool(key), "owner": owner})

        elif path == "/api/settings/key/status":
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            settings = json.loads(raw)
            active_label = settings.get("active_wavespeed_account", "")
            accounts = list_wavespeed_accounts()
            self._json({
                "ok": True,
                "wavespeed_accounts": accounts,
                "active_wavespeed_account": active_label,
                "count": len(accounts),
            })

        elif path == "/api/settings/wavespeed/accounts":
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            settings = json.loads(raw)
            active_label = settings.get("active_wavespeed_account", "")
            self._json({
                "ok": True,
                "accounts": list_wavespeed_accounts(),
                "active": active_label,
            })

        elif path == "/api/settings/wavespeed/accounts/validate-all":
            raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
            settings = json.loads(raw)
            accounts = settings.get("wavespeed_accounts", {})
            
            def validate_account(label, key):
                try:
                    client = WaveSpeedClient(key)
                    client.validate()
                    return label, True
                except Exception:
                    return label, False
            
            results = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(validate_account, label, key): label for label, key in accounts.items()}
                for fut in concurrent.futures.as_completed(futures):
                    label, ok = fut.result()
                    results[label] = ok
            
            self._json({"ok": True, "results": results})

        else:
            # Try static file from outputs/
            static = OUTPUTS / parsed.path.lstrip("/")
            if static.exists() and static.is_file():
                self._serve_file(static)
            else:
                self._json({"error": "not found"}, 404)

    @staticmethod
    def _resolve_prompts(path):
        """Resolve prompts path: bare filename â†’ relative to PIPELINE_DIR."""
        p = Path(path)
        if not p.is_absolute() and p.parent == Path("."):
            p = PIPELINE_DIR / p
        return str(p.resolve())

    def do_POST(self):
        parsed = urlparse(self.path)
        body = self._read_body()

        if parsed.path == "/api/run/photo":
            prompts_data = body.get("prompts", "prompts_alina_b1.json")
            if isinstance(prompts_data, list):
                stem = f"edited_prompts_{uuid.uuid4().hex[:8]}"
                prompts_path = PIPELINE_DIR / f"{stem}.json"
                prompts_path.write_text(json.dumps(prompts_data, indent=2), encoding="utf-8")
                prompts = str(prompts_path.resolve())
            else:
                prompts = self._resolve_prompts(prompts_data)
            run_id = _start_pipeline("photo", prompts)
            _log_activity(f"Photo pack started: {prompts} [{run_id}]")
            self._json({"ok": True, "run_id": run_id})

        elif parsed.path == "/api/dashboard/refresh":
            _log_activity("Dashboard refreshed")
            self._json({"ok": True, "outputs": _collect(), "msg": "ok"})

        elif parsed.path == "/api/prompts/generate":
            vibe = body.get("vibe", "indoor")
            camera_style = body.get("camera_style", "handheld")
            lighting = body.get("lighting", "warm")
            time_of_day = body.get("time_of_day", "day")
            outfit_style = body.get("outfit_style", "any")
            count = int(body.get("count", 6))
            try:
                jobs = build_jobs_multi(
                    count=count, vibe=vibe,
                    camera_style=camera_style, lighting=lighting,
                    time_of_day=time_of_day,
                    outfit_style=outfit_style,
                )
                stem = f"promptbank_{vibe}_{camera_style}_{lighting}_{time_of_day}_{outfit_style}_{count}"
                prompts_path = PIPELINE_DIR / f"{stem}.json"
                prompts_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
                _log_activity(
                    f"Prompt bank: {stem}.json ({len(jobs)} jobs, vibe={vibe}, "
                    f"camera={camera_style}, light={lighting}, time={time_of_day}, outfit={outfit_style})"
                )
                self._json({"ok": True, "jobs": jobs, "file": str(prompts_path.name), "count": len(jobs)})
            except Exception as e:
                self._json({"ok": False, "error": str(e)})

        elif parsed.path == "/api/caption/edit":
            src = body.get("src", "")
            text = body.get("text", "")
            if not src:
                self._json({"ok": False, "error": "missing src"}, 400)
            else:
                try:
                    media_path = (OUTPUTS / src).resolve()
                    media_path.relative_to(OUTPUTS.resolve())
                    txt_path = media_path.with_suffix(".txt")
                    txt_path.write_text(text, encoding="utf-8")
                    self._json({"ok": True})
                except ValueError:
                    self._json({"ok": False, "error": "invalid path"}, 400)
                except Exception as e:
                    self._json({"ok": False, "error": str(e)}, 500)

        elif parsed.path == "/api/media/delete":
            src = body.get("src", "")
            if not src:
                self._json({"ok": False, "error": "missing src"}, 400)
            else:
                try:
                    media_path = (OUTPUTS / src).resolve()
                    media_path.relative_to(OUTPUTS.resolve())
                    if media_path.exists() and media_path.is_file():
                        # Also delete companion .txt file if exists
                        txt_path = media_path.with_suffix(".txt")
                        if txt_path.exists():
                            txt_path.unlink()
                        media_path.unlink()
                        self._json({"ok": True})
                    else:
                        self._json({"ok": False, "error": "file not found"}, 404)
                except ValueError:
                    self._json({"ok": False, "error": "invalid path"}, 400)
                except Exception as e:
                    self._json({"ok": False, "error": str(e)}, 500)

        elif parsed.path == "/api/settings/wavespeed/test":
            label = body.get("label", "").strip()
            if not label:
                self._json({"ok": False, "error": "missing label"}, 400)
            else:
                result = test_wavespeed_account(label)
                self._json(result)

        elif parsed.path == "/api/settings/wavespeed/active":
            label = body.get("label", "").strip()
            if not label:
                self._json({"ok": False, "error": "missing label"}, 400)
            else:
                set_active_wavespeed_account(label)
                _balance_cache["time"] = 0
                _balance_cache["value"] = None
                _log_activity(f"Active WaveSpeed account set to: {label}")
                self._json({"ok": True, "label": label})

        elif parsed.path == "/api/settings/wavespeed/accounts/set":
            label = body.get("label", "").strip()
            key = body.get("key", "").strip()
            if not label:
                self._json({"ok": False, "error": "missing label"}, 400)
            elif not key:
                self._json({"ok": False, "error": "missing key"}, 400)
            else:
                set_wavespeed_account(label, key)
                raw = SETTINGS_PATH.read_text(encoding="utf-8") if SETTINGS_PATH.exists() else "{}"
                active_label = json.loads(raw).get("active_wavespeed_account", "")
                if not active_label:
                    set_active_wavespeed_account(label)
                    active_label = label
                preview = (key[:4] + "****" + key[-4:]) if len(key) > 8 else "****"
                _log_activity(f"WaveSpeed account saved: {label} {preview}")
                self._json({"ok": True, "label": label, "preview": preview, "active": active_label})

        elif parsed.path == "/api/settings/wavespeed/accounts/remove":
            label = body.get("label", "").strip()
            if not label:
                self._json({"ok": False, "error": "missing label"}, 400)
            else:
                remove_wavespeed_account(label)
                _log_activity(f"WaveSpeed account removed: {label}")
                self._json({"ok": True})

        elif parsed.path == "/api/settings/wavespeed/accounts/rename":
            old_label = body.get("old_label", "").strip()
            new_label = body.get("new_label", "").strip()
            if not old_label or not new_label:
                self._json({"ok": False, "error": "missing old_label or new_label"}, 400)
            else:
                result = rename_wavespeed_account(old_label, new_label)
                if result.get("ok"):
                    _log_activity(f"WaveSpeed account renamed: {old_label} -> {new_label}")
                    self._json({"ok": True, "old_label": old_label, "new_label": new_label})
                else:
                    self._json({"ok": False, "error": result.get("error", "unknown")}, 400)

        else:
            self._json({"error": "not found"}, 404)

    def _serve_homepage(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(HOMEPAGE_HTML.encode("utf-8"))

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def _serve_file(self, path):
        ext = path.suffix.lower()
        mime = {
            ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".mp4": "video/mp4", ".json": "application/json", ".txt": "text/plain",
        }.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        with open(path, "rb") as f:
            self.wfile.write(f.read())

    def log_message(self, fmt, *args):
        pass  # quieter


# â”€â”€ Homepage HTML â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

STATIC_DIR = WEBUI_DIR / "static"


def _load_homepage():
    """Load homepage HTML from static/index.html."""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>OFM Control Panel</h1><p>Error: static/index.html not found</p>"


HOMEPAGE_HTML = _load_homepage()
# â”€â”€ Run â”€â”€
if __name__ == "__main__":
    port = 8000
    # Free port if stale
    import subprocess, sys
    try:
        subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)
        kill = subprocess.run(
            f'netstat -ano | findstr :{port} | findstr LISTENING',
            capture_output=True, text=True, shell=True, timeout=5
        )
        if kill.stdout.strip():
            pid = kill.stdout.strip().split()[-1]
            if pid != str(os.getpid()):
                try: os.kill(int(pid), 9)
                except: pass
    except:
        pass

    # Enable ANSI colors on Windows
    if sys.platform == 'win32':
        os.system('')

    # Color codes
    class Colors:
        GREEN = '\033[92m'
        BLUE = '\033[94m'
        YELLOW = '\033[93m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        END = '\033[0m'
        GRAY = '\033[37m'

    webbrowser.open(f"http://localhost:{port}")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    
    # Enhanced startup display
    print(f"\n{Colors.GRAY}{'=' * 50}{Colors.END}")
    print(f"{Colors.BOLD}>> OFM Control Panel Server{Colors.END}")
    print(f"{Colors.GRAY}{'=' * 50}{Colors.END}")
    print(f"URL:  {Colors.YELLOW}http://localhost:{port}{Colors.END}")
    print(f"Status: {Colors.GREEN}{Colors.BOLD}ONLINE{Colors.END}")
    print(f"Dir:    {Colors.CYAN}{os.getcwd()}{Colors.END}")
    print(f"{Colors.GRAY}{'=' * 50}{Colors.END}")
    print(f"{Colors.YELLOW}Tip: Press Ctrl+C to stop server{Colors.END}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}! Shutdown signal received...{Colors.END}")
        server.shutdown()
        print(f"{Colors.GREEN}+ Server stopped gracefully.{Colors.END}")


