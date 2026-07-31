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

BASE_URL = "https://api.wavespeed.ai/api/v3"
IMAGE_MODEL = "google/nano-banana-2/edit"
ENHANCE_MODEL = "wavespeed-ai/image-enhancer"

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

    def poll(self, task_id, interval=3, timeout=600):
        deadline = time.time() + timeout
        while time.time() < deadline:
            data = self._request("GET", f"/predictions/{task_id}/result")
            status = data.get("status")
            if status == "completed":
                return data
            if status == "failed":
                raise WaveSpeedError(f"generation_failed: {data.get('error')}", code="generation_failed")
            time.sleep(interval)
        raise WaveSpeedError("polling_timeout", code="polling_timeout")

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
                 aspect_ratio="9:16"):
        payload = {
            "prompt": prompt,
            "images": [image_url],
            "resolution": resolution,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,
        }
        task_id = self.submit(payload, model=IMAGE_MODEL)
        result = self.poll(task_id, interval=3)
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
    def download(url, path):
        urllib.request.urlretrieve(url, path)
        return path

    @staticmethod
    def _lock_path(output_dir):
        return os.path.join(output_dir, ".batch.lock")

    def _acquire_lock(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        path = self._lock_path(output_dir)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(time.time()).encode())
            os.close(fd)
        except FileExistsError:
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
                       max_concurrent=5, progress_callback=None,
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

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as pool:
                fut_map = {}
                for job in pending:
                    fut = pool.submit(
                        self._generate_one, job, avatar_url, output_dir,
                        resolution, output_format, aspect_ratio, enhance,
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
        }

    def _generate_one(self, job, avatar_url, output_dir, resolution, output_format,
                       aspect_ratio, enhance):
        prompt = job["prompt"]
        filename = job["filename"]
        os.makedirs(output_dir, exist_ok=True)

        self.logger.info("generating %s", filename)
        result_url = self.generate(prompt, avatar_url, resolution=resolution,
                                    output_format=output_format, aspect_ratio=aspect_ratio)

        if enhance:
            self.logger.info("enhancing %s", filename)
            result_url = self.enhance(result_url, scale=4, output_format=output_format)

        self.logger.info("downloading %s", filename)
        path = os.path.join(output_dir, filename)
        self.download(result_url, path)
        return path
