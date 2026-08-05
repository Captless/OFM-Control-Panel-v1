"""
WaveSpeed AI REST client for Alina SFW workflow — nano-banana-2/edit + image upscaler.

Docs: https://wavespeed.ai/docs
"""

import concurrent.futures
import json
import os
import time
import urllib.request
import urllib.error
import logging

import requests  # noqa: E402

BASE_URL = "https://api.wavespeed.ai/api/v3"
IMAGE_MODEL = "google/nano-banana-2/edit"
ENHANCE_MODEL = "wavespeed-ai/image-enhancer"

EXPLICIT_FLAG_MARKERS = ("sensitive", "explicit", "flagged")


def _is_explicit_flag(msg):
    m = (msg or "").lower()
    return any(k in m for k in EXPLICIT_FLAG_MARKERS)

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.errors import WaveSpeedError  # noqa: E402

logger = logging.getLogger(__name__)


class WaveSpeedClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _request(self, method, path, payload=None, timeout=10):
        url = f"{BASE_URL}{path}"
        data = None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        self.logger.debug("request %s %s", method, url)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise WaveSpeedError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}", status=e.code)
        if body.get("code") not in (200, None):
            raise WaveSpeedError(body.get("message", "unknown error"), code=body.get("code"))
        return body.get("data", body)

    def get_balance(self):
        data = self._request("GET", "/balance")
        return data.get("balance", 0.0)

    def validate(self):
        """Check whether the API key is valid. GET /models returns 401 for bad keys."""
        self._request("GET", "/models", timeout=5)
        return True

    def submit(self, payload, model=None):
        model = model or IMAGE_MODEL
        payload = {**payload, "model": model}
        data = self._request("POST", f"/{model}", payload)
        return data["id"]

    def poll(self, task_id, interval=3, timeout=600, status_callback=None):
        deadline = time.time() + timeout
        t0 = time.time()
        while time.time() < deadline:
            data = self._request("GET", f"/predictions/{task_id}/result")
            status = data.get("status")
            elapsed = int(time.time() - t0)
            if status == "completed":
                if status_callback:
                    status_callback(status, elapsed, data)
                return data
            if status == "failed":
                if status_callback:
                    status_callback(status, elapsed, data)
                err = data.get("error") or "unknown error"
                if _is_explicit_flag(err):
                    raise WaveSpeedError(f"explicit_content_flagged: {err}", code="explicit_content_flagged")
                raise WaveSpeedError(f"generation_failed: {err}", code="generation_failed")
            if status_callback:
                status_callback(status, elapsed, data)
            time.sleep(interval)
        raise WaveSpeedError("polling_timeout", code="polling_timeout")

    def _parse_sse_stream(self, response):
        """Parse an SSE (text/event-stream) response into a sequence of event dicts.

        Handles incomplete lines split across network chunks. Each `data:` line is
        parsed as JSON; non-JSON payloads are passed through as {"raw": text}.
        """
        buffer = ""
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.rstrip("\r")
            if not line.startswith("data:"):
                continue
            payload = line[5:].lstrip()
            if not payload:
                continue
            try:
                event = json.loads(payload)
            except (ValueError, TypeError):
                event = {"raw": payload}
            yield event

    def generate_stream(self, prompt, image_url, resolution="1k", output_format="png",
                        aspect_ratio="9:16", timeout=600, on_event=None):
        """Stream generation over SSE, yielding real-time API events.

        Events are model-specific. Typical fields: status, progress, error.
        Returns the final output URL when the stream completes.
        """
        payload = {
            "prompt": prompt,
            "images": [image_url],
            "resolution": resolution,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        stream_url = f"{BASE_URL}/{IMAGE_MODEL}/stream"
        self.logger.debug("stream %s", stream_url)
        with requests.post(
            stream_url, headers=headers, json=payload, stream=True,
            timeout=(10, timeout),
        ) as resp:
            if resp.status_code != 200:
                raise WaveSpeedError(
                    f"HTTP {resp.status_code}: {resp.text[:500]}",
                    status=resp.status_code,
                )
            final_output = None
            for event in self._parse_sse_stream(resp):
                if on_event:
                    on_event(event)
                status = event.get("status")
                if status == "completed" and event.get("outputs"):
                    final_output = event["outputs"][0]
                if status == "failed":
                    err = event.get("error") or "stream generation failed"
                    if _is_explicit_flag(str(err)):
                        raise WaveSpeedError(
                            f"explicit_content_flagged: {err}",
                            code="explicit_content_flagged",
                        )
                    raise WaveSpeedError(f"generation_failed: {err}", code="generation_failed")
            if final_output:
                return final_output
            raise WaveSpeedError("stream_no_output", code="stream_no_output")


    def upload_file(self, file_path):
        import requests
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/media/upload/binary",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": f},
            )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") not in (200, None):
            raise WaveSpeedError(body.get("message", "upload failed"), code=body.get("code"))
        return body["data"]["download_url"]

    def generate(self, prompt, image_url, resolution="1k", output_format="png",
                 aspect_ratio="9:16", stream=False, status_callback=None,
                 on_event=None):
        """Generate an image. Uses SSE streaming when stream=True, else polls.

        - status_callback(status, elapsed, data): called during polling fallback.
        - on_event(event): called for each raw SSE event during streaming.
        In batch_generate, both callbacks are job-bound: the first arg becomes
        the job dict (status_callback(job, status, elapsed, data), on_event(job, event)).
        Falls back to polling automatically if the stream endpoint fails.
        """
        if stream:
            try:
                return self.generate_stream(
                    prompt, image_url, resolution=resolution,
                    output_format=output_format, aspect_ratio=aspect_ratio,
                    on_event=on_event,
                )
            except WaveSpeedError as e:
                if e.code in ("stream_no_output", "stream_generation_failed"):
                    self.logger.warning("stream failed (%s); falling back to polling", e.code)
                else:
                    raise
        payload = {
            "prompt": prompt,
            "images": [image_url],
            "resolution": resolution,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,
        }
        task_id = self.submit(payload, model=IMAGE_MODEL)
        result = self.poll(task_id, interval=3, status_callback=status_callback)
        self.logger.debug("generate completed for task %s", task_id)
        return result["outputs"][0]

    def enhance(self, image_url, scale=4, output_format="png"):
        payload = {
            "image": image_url,
            "scale": scale,
            "output_format": output_format,
        }
        task_id = self.submit(payload, model=ENHANCE_MODEL)
        result = self.poll(task_id, interval=2)
        self.logger.debug("enhance completed for task %s", task_id)
        return result["outputs"][0]

    @staticmethod
    def download(url, path, timeout=120):
        with urllib.request.urlopen(url, timeout=timeout) as resp, open(path, "wb") as f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
        return path

    @staticmethod
    def _lock_path(output_dir):
        return os.path.join(output_dir, ".batch.lock")

    LOCK_STALE_SECONDS = 10 * 60

    def _acquire_lock(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        path = self._lock_path(output_dir)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(time.time()).encode())
            os.close(fd)
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(path)
            except OSError:
                age = float("inf")
            if age > self.LOCK_STALE_SECONDS:
                try:
                    os.remove(path)
                except OSError:
                    pass
                try:
                    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(fd, str(time.time()).encode())
                    os.close(fd)
                except FileExistsError:
                    raise WaveSpeedError(
                        f"batch_already_running: lock file exists at {path}",
                        code="batch_already_running",
                    )
            else:
                raise WaveSpeedError(
                    f"batch_already_running: lock file exists at {path}",
                    code="batch_already_running",
                )
        return path

    def _release_lock(self, lock_path):
        if os.path.exists(lock_path):
            os.remove(lock_path)

    def batch_generate(self, jobs, avatar_url, output_dir, resolution="1k",
                       output_format="png", aspect_ratio="9:16", enhance=False,
                       stream=False, max_concurrent=5, progress_callback=None,
                       status_callback=None, on_event=None,
                       checkpoint_path=None):
        lock_path = self._acquire_lock(output_dir)
        done_ids = set()
        if checkpoint_path and os.path.exists(checkpoint_path):
            with open(checkpoint_path) as f:
                done_ids = set(json.load(f))

        pending = [j for j in jobs if j["filename"] not in done_ids]

        n_total = len(jobs)
        n_success = 0
        n_failed = 0
        t0 = time.time()

        def _save_checkpoint():
            if checkpoint_path:
                with open(checkpoint_path, "w") as f:
                    json.dump(sorted(done_ids), f)

        success_list = []
        failed_list = []
        explicit_hit = False

        def _wrap_status(job):
            if not status_callback:
                return None

            def _cb(status, elapsed, data=None):
                status_callback(job, status, elapsed, data)
            return _cb

        def _wrap_event(job):
            if not on_event:
                return None

            def _cb(event):
                on_event(job, event)
            return _cb

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as pool:
                fut_map = {}
                for job in pending:
                    fut = pool.submit(
                        self._generate_one, job, avatar_url, output_dir,
                        resolution, output_format, aspect_ratio, enhance,
                        stream, _wrap_status(job), _wrap_event(job),
                    )
                    fut_map[fut] = job

                for fut in concurrent.futures.as_completed(fut_map):
                    job = fut_map[fut]
                    try:
                        path = fut.result()
                        success_list.append({"filename": job["filename"], "path": path})
                        n_success += 1
                        done_ids.add(job["filename"])
                        _save_checkpoint()
                        last = job["filename"]
                    except Exception as e:
                        failed_list.append({"filename": job["filename"], "error": str(e)})
                        n_failed += 1
                        last = f"{job['filename']} FAILED: {e}"
                        if _is_explicit_flag(str(e)):
                            explicit_hit = True
                            for f in fut_map:
                                f.cancel()
                    if progress_callback:
                        progress_callback(n_success + n_failed, n_total, last)
        finally:
            self._release_lock(lock_path)

        duration_s = time.time() - t0
        return {
            "success": success_list,
            "failed": failed_list,
            "duration_s": duration_s,
            "n_total": n_total,
            "n_success": n_success,
            "n_failed": n_failed,
            "explicit_hit": explicit_hit,
        }

    def _generate_one(self, job, avatar_url, output_dir, resolution, output_format,
                      aspect_ratio, enhance, stream, status_callback=None,
                      on_event=None):
        prompt = job["prompt"]
        filename = job["filename"]
        os.makedirs(output_dir, exist_ok=True)
        t0 = time.time()

        self.logger.info("generating %s", filename)
        if status_callback:
            status_callback("submitting", 0, None)
        result_url = self.generate(prompt, avatar_url, resolution=resolution,
                                   output_format=output_format, aspect_ratio=aspect_ratio,
                                   stream=stream, status_callback=status_callback,
                                   on_event=on_event)

        if enhance:
            self.logger.info("enhancing %s", filename)
            if status_callback:
                status_callback("enhancing", int(time.time() - t0), None)
            result_url = self.enhance(result_url, scale=4, output_format=output_format)

        self.logger.info("downloading %s", filename)
        path = os.path.join(output_dir, filename)
        self.download(result_url, path)
        if status_callback:
            status_callback("saved", int(time.time() - t0), None)
        return path
