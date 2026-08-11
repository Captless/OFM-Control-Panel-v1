"""
OFM Control Panel â€” local HTTP server with homepage UI.
Serves at http://localhost:8000

Run:  py server.py
"""

import concurrent.futures
import http.server
import json
import os
import queue
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
from core.config import PHOTO_PRICE, SETTINGS_PATH, list_wavespeed_accounts, set_wavespeed_account, remove_wavespeed_account, rename_wavespeed_account, get_active_wavespeed_key, set_active_wavespeed_account, test_wavespeed_account, get_identity, set_identity
from core.prompt_banks import list_banks, get_bank, create_bank, update_bank, delete_bank, clone_bank, get_active_bank_id, set_active_bank_id, export_banks, import_banks

sys.path.insert(0, str(PIPELINE_DIR))
from prompt_bank import list_presets, build_jobs_multi, get_builtin_pools

API_DIR = BASE / "api"
sys.path.insert(0, str(API_DIR))
from wavespeed_client import WaveSpeedClient

SCRIPTS_DIR = BASE / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from alina_textgen import batch_generate, PLATFORM_CONFIG

_balance_cache = {"time": 0, "value": None}

LOCK_STALE_SECONDS = 10 * 60

IDENTITY_UPLOAD_MAX = 5 * 1024 * 1024

_IDENTITY_MIME_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/bmp": "png",
}


def _extract_file_part(raw, boundary):
    """Pull the first multipart file part (name=file). Returns (bytes, content_type)."""
    parts = raw.split(b"--" + boundary)
    for part in parts:
        if part in (b"", b"--", b"--\r\n"):
            continue
        if part.startswith(b"\r\n"):
            part = part[2:]
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        headers = part[:header_end].decode("utf-8", "ignore")
        body = part[header_end + 4:]
        if body.endswith(b"\r\n"):
            body = body[:-2]
        if 'name="file"' not in headers:
            continue
        ct = "application/octet-stream"
        for line in headers.split("\r\n"):
            if line.lower().startswith("content-type:"):
                ct = line.split(":", 1)[1].strip()
        return body, ct
    return None, ""


def _handle_identity_upload(raw, content_type):
    """Validate + persist an uploaded identity image under outputs/identity/.
    Auto-uploads to WaveSpeed to obtain a public URL (required for generation
    reference). Returns {'ok', 'url', 'avatar_url', 'uploaded', 'warning'}."""
    m = re.match(r"multipart/form-data;\s*boundary=(.+)", content_type or "")
    if not m:
        return {"ok": False, "error": "expected multipart/form-data"}
    boundary = m.group(1).strip().strip('"')
    if not boundary:
        return {"ok": False, "error": "missing boundary"}
    file_bytes, file_ct = _extract_file_part(raw, boundary.encode("utf-8"))
    if file_bytes is None:
        return {"ok": False, "error": "no file part found"}
    if len(file_bytes) > IDENTITY_UPLOAD_MAX:
        return {"ok": False, "error": "file too large (max 5MB)"}
    if not file_ct.startswith("image/"):
        return {"ok": False, "error": "invalid file type: images only"}
    ext = _IDENTITY_MIME_EXT.get(file_ct.split(";")[0].strip().lower(), "png")
    out_dir = OUTPUTS / "identity"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = uuid.uuid4().hex[:12] + "." + ext
    local_path = out_dir / filename
    local_path.write_bytes(file_bytes)
    local_url = "identity/" + filename

    avatar_url = local_url
    uploaded = False
    warning = ""
    key = get_active_wavespeed_key()
    if key:
        try:
            client = WaveSpeedClient(key)
            avatar_url = client.upload_file(str(local_path))
            uploaded = True
        except Exception as e:
            warning = f"WaveSpeed upload failed ({e}); saved locally only. Paste a public URL for generation."
    set_identity(avatar_url=avatar_url)
    return {
        "ok": True,
        "url": local_url,
        "avatar_url": avatar_url,
        "uploaded": uploaded,
        "warning": warning,
    }


def _clean_stale_locks():
    """Remove orphaned .batch.lock files older than LOCK_STALE_SECONDS."""
    if not OUTPUTS.is_dir():
        return 0
    now = time.time()
    removed = 0
    for lock in OUTPUTS.rglob("*.batch.lock"):
        try:
            if now - lock.stat().st_mtime > LOCK_STALE_SECONDS:
                lock.unlink()
                removed += 1
        except OSError:
            pass
    return removed


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
    entries = [e for e in OUTPUTS.iterdir() if e.is_dir() and (list(e.rglob("*.mp4")) or list(e.rglob("*.png")) or list(e.rglob("*.jpg")))]
    date_groups = defaultdict(list)
    for entry in entries:
        try:
            dt = datetime.strptime(entry.name, "%Y-%m-%d")
            date_key = dt.strftime("%Y-%m-%d")
        except ValueError:
            dt = datetime.fromtimestamp(entry.stat().st_mtime)
            date_key = dt.strftime("%Y-%m-%d")
        date_groups[date_key].append({"entry": entry, "mtime": entry.stat().st_mtime, "dt": dt})

    sorted_dates = sorted(date_groups.keys(), reverse=True)
    batches = []
    for date_key in sorted_dates:
        group = date_groups[date_key]
        date_label = datetime.strptime(date_key, "%Y-%m-%d").strftime("%B %d, %Y")
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
                    "created_at": datetime.fromtimestamp(path.stat().st_mtime).strftime("%I:%M %p").lstrip("0"),
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
    """Parse a single stdout/stderr line into _pipeline_runs state."""
    with _state_lock:
        state = _pipeline_runs.get(run_id)
        if state is None:
            return
        state["updated_at"] = time.time()
        state["elapsed"] = int(time.time() - state.get("started_at", time.time()))
        if line.startswith("@P image|"):
            parts = line[len("@P image|"):].split("|", 4)
            if len(parts) >= 3:
                fn, status, elapsed_raw = parts[0], parts[1], parts[2]
                detail = parts[3] if len(parts) == 4 else ""
                try:
                    elapsed = int(elapsed_raw.rstrip("s"))
                except ValueError:
                    elapsed = 0
                images = state.setdefault("images", {})
                images[fn] = {"filename": fn, "status": status, "elapsed": elapsed, "detail": detail}
        elif line.startswith("@P "):
            parts = line[3:].split("|", 2)
            state["stage"] = parts[0]
            if len(parts) == 2:
                state["detail"] = parts[1]
            elif len(parts) == 3:
                state["error_type"] = parts[1]
                state["detail"] = parts[2]
            if parts[0] == "failed":
                state["done"] = True
                state["ok"] = False
        elif line.strip():
            state["detail"] = line.strip()
        m = re.match(r"^\[(\d+)/(\d+)\]\s+(.*)", line)
        if m:
            state["current"] = int(m.group(1))
            state["total"] = int(m.group(2))
            if not line.startswith("@P "):
                state["stage"] = "processing"
                state["detail"] = m.group(3)


def _start_pipeline(prompts):
    """Start pipeline in a daemon thread. Returns run_id for progress polling."""
    run_id = uuid.uuid4().hex[:8]
    cmd = [sys.executable, str(PIPELINE_DIR / "pipeline.py"), "--prompts", prompts]

    with _state_lock:
        _pipeline_runs[run_id] = {
            "stage": "starting", "detail": "",
            "current": 0, "total": 0,
            "done": False, "ok": None, "duration_s": 0,
            "error_type": "",
            "images": {},
            "elapsed": 0,
            "started_at": time.time(),
            "updated_at": time.time(),
        }

    def _run():
        t0 = time.time()
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            stderr_q = queue.Queue()

            def _read_stderr():
                try:
                    for line in proc.stderr:
                        stderr_q.put(line)
                        _update_progress(run_id, line.rstrip())
                except Exception:
                    pass
                finally:
                    stderr_q.put(None)

            stderr_t = threading.Thread(target=_read_stderr, daemon=True)
            stderr_t.start()

            for line in proc.stdout:
                _update_progress(run_id, line.rstrip())
            proc.wait()

            stderr_lines = []
            while True:
                item = stderr_q.get()
                if item is None:
                    break
                stderr_lines.append(item.rstrip())

            duration = round(time.time() - t0, 1)
            ok = proc.returncode == 0
            msg = "Done" if ok else ((stderr_lines[-1] if stderr_lines else "") or f"Exit code {proc.returncode}")
            with _state_lock:
                _pipeline_runs[run_id].update(
                    stage="done" if ok else "failed", detail=msg,
                    done=True, ok=ok, duration_s=duration,
                    elapsed=int(duration),
                    updated_at=time.time(),
                )
                _prune_pipeline_runs()
        except Exception as e:
            with _state_lock:
                _pipeline_runs[run_id].update(
                    stage="failed", detail=str(e),
                    done=True, ok=False, duration_s=round(time.time() - t0, 1),
                    elapsed=int(round(time.time() - t0, 1)),
                    updated_at=time.time(),
                )
                _prune_pipeline_runs()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return run_id


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

        elif path == "/api/settings/identity":
            self._json({"ok": True, "identity": get_identity()})

        elif path == "/api/settings/banks":
            banks = dict(list_banks())
            banks.setdefault("builtin", {"id": "builtin", "name": "Built-in", "description": "", "pools": {}})
            self._json({"ok": True, "banks": banks})

        elif path == "/api/settings/banks/export":
            payload = json.dumps(export_banks(), indent=2).encode("utf-8")
            filename = f"prompt_banks_{datetime.now().strftime('%Y-%m-%d')}.json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return

        elif path == "/api/settings/banks/view":
            bank_id = parse_qs(parsed.query).get("id", [None])[0]
            if not bank_id:
                self._json({"ok": False, "error": "missing id"}, 400)
                return
            bank = get_bank(bank_id)
            if bank is None:
                self._json({"ok": False, "error": "bank not found"}, 404)
                return
            self._json({"ok": True, "bank": bank})

        elif path == "/api/settings/banks/active":
            self._json({"ok": True, "active": get_active_bank_id()})

        elif path == "/api/settings/banks/pools/defaults":
            self._json({"ok": True, "pools": get_builtin_pools()})

        elif path == "/api/settings/banks/active/pools":
            pools = dict(get_builtin_pools())
            bank_id = get_active_bank_id()
            bank = get_bank(bank_id) if bank_id else None
            if bank:
                for k, v in (bank.get("pools") or {}).items():
                    pools[k] = v
            self._json({"ok": True, "pools": pools, "bank_id": bank_id, "bank_name": (bank or {}).get("name", "")})

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
        if parsed.path == "/api/settings/identity/upload":
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length)
            try:
                result = _handle_identity_upload(raw, self.headers.get("Content-Type", ""))
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
                return
            if result.get("ok"):
                _log_activity(f"Identity avatar uploaded: {result.get('url')} (wavespeed_public={bool(result.get('uploaded'))})")
            self._json(result)
            return
        body = self._read_body()

        if parsed.path == "/api/captions/generate":
            count = body.get("count", 10)
            if not isinstance(count, int) or isinstance(count, bool):
                self._json({"ok": False, "error": "count must be an integer"}, 400)
                return
            count = max(1, min(20, count))

            platform = (body.get("platform") or "tiktok").strip()
            if platform not in PLATFORM_CONFIG:
                self._json({"ok": False, "error": "unknown platform"}, 400)
                return

            hook_types = body.get("hook_types")
            if hook_types is not None and not isinstance(hook_types, list):
                self._json({"ok": False, "error": "hook_types must be a list"}, 400)
                return

            seed = body.get("seed")
            if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
                self._json({"ok": False, "error": "seed must be an integer"}, 400)
                return

            try:
                caps = batch_generate(count, platforms=[platform], hook_types=hook_types, seed=seed)
                self._json({"ok": True, "captions": caps})
            except ValueError as e:
                self._json({"ok": False, "error": str(e)}, 400)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            return

        if parsed.path == "/api/settings/identity":
            avatar_url = (body.get("avatar_url") or "").strip()
            if not avatar_url:
                self._json({"ok": False, "error": "missing avatar_url"}, 400)
            else:
                set_identity(avatar_url=avatar_url)
                _log_activity("Identity avatar URL updated")
                self._json({"ok": True, "identity": get_identity()})

        elif parsed.path == "/api/settings/banks/import":
            data = body.get("data")
            if data is None:
                data = body
            try:
                result = import_banks(data)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
            else:
                self._json(result)

        elif parsed.path == "/api/run/photo":
            prompts_data = body.get("prompts", "prompts_alina_b1.json")
            if isinstance(prompts_data, list):
                stem = f"edited_prompts_{uuid.uuid4().hex[:8]}"
                prompts_path = PIPELINE_DIR / f"{stem}.json"
                prompts_path.write_text(json.dumps(prompts_data, indent=2), encoding="utf-8")
                prompts = str(prompts_path.resolve())
            else:
                prompts = self._resolve_prompts(prompts_data)
            run_id = _start_pipeline(prompts)
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
            outfit_style = body.get("outfit_style", "sexy")
            count = int(body.get("count", 6))
            bank_id = (body.get("bank_id") or "").strip()
            if not bank_id:
                bank_id = get_active_bank_id()
            bank = None
            if bank_id:
                found = get_bank(bank_id)
                if found:
                    bank = found.get("pools") or {}
            try:
                jobs = build_jobs_multi(
                    count=count, vibe=vibe,
                    camera_style=camera_style, lighting=lighting,
                    time_of_day=time_of_day,
                    outfit_style=outfit_style,
                    bank=bank,
                )
                stem = f"promptbank_{vibe}_{camera_style}_{lighting}_{time_of_day}_{outfit_style}_{count}"
                if bank_id:
                    stem += f"_{bank_id}"
                prompts_path = PIPELINE_DIR / f"{stem}.json"
                prompts_path.write_text(json.dumps(jobs, indent=2), encoding="utf-8")
                _log_activity(
                    f"Prompt bank: {stem}.json ({len(jobs)} jobs, vibe={vibe}, "
                    f"camera={camera_style}, light={lighting}, time={time_of_day}, outfit={outfit_style}, bank={bank_id or 'builtin'})"
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

        elif parsed.path == "/api/settings/banks/create":
            result = create_bank(body)
            if result.get("ok"):
                _log_activity(f"Prompt bank created: {result['bank']['name']}")
                self._json(result)
            else:
                self._json({"ok": False, "error": result.get("error", "unknown")}, 400)

        elif parsed.path == "/api/settings/banks/update":
            bank_id = (body.get("id") or "").strip()
            if not bank_id:
                self._json({"ok": False, "error": "missing id"}, 400)
            else:
                result = update_bank(bank_id, body)
                if result.get("ok"):
                    _log_activity(f"Prompt bank updated: {result['bank']['name']}")
                    self._json(result)
                else:
                    self._json({"ok": False, "error": result.get("error", "unknown")}, 400)

        elif parsed.path == "/api/settings/banks/active":
            bank_id = (body.get("id") or "").strip()
            result = set_active_bank_id(bank_id)
            if result.get("ok"):
                _log_activity(f"Active prompt bank set to: {bank_id or 'builtin'}")
                self._json(result)
            else:
                self._json({"ok": False, "error": result.get("error", "unknown")}, 400)

        elif parsed.path == "/api/settings/banks/clone":
            source_id = (body.get("source_id") or "").strip()
            new_name = (body.get("name") or "").strip()
            if not new_name:
                self._json({"ok": False, "error": "missing bank name"}, 400)
            elif source_id and not get_bank(source_id):
                self._json({"ok": False, "error": f"bank '{source_id}' not found"}, 400)
            else:
                if not source_id:
                    source_id = get_active_bank_id()
                result = clone_bank(source_id, new_name)
                if result.get("ok"):
                    _log_activity(f"Prompt bank cloned: {result['bank']['name']} (from {source_id or 'builtin'})")
                    self._json(result)
                else:
                    self._json({"ok": False, "error": result.get("error", "unknown")}, 400)

        elif parsed.path == "/api/settings/banks/delete":
            bank_id = (body.get("id") or "").strip()
            if not bank_id:
                self._json({"ok": False, "error": "missing id"}, 400)
            else:
                result = delete_bank(bank_id)
                if result.get("ok"):
                    _log_activity(f"Prompt bank deleted: {bank_id}")
                    self._json(result)
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
        self.wfile.write(_load_homepage().encode("utf-8"))

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
            ".webp": "image/webp", ".gif": "image/gif",
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


# â”€â”€ Run â”€â”€
if __name__ == "__main__":
    port = 8000
    _clean_stale_locks()
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


