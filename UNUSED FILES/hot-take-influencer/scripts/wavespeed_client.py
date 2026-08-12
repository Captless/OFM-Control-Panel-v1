"""
Minimal WaveSpeed AI REST client used by the hot-take-influencer skill.

Docs: https://wavespeed.ai/docs
Auth: Authorization: Bearer <WAVESPEED_API_KEY>
Submit:  POST https://api.wavespeed.ai/api/v3/{model}
Poll:    GET  https://api.wavespeed.ai/api/v3/predictions/{task_id}/result
Balance: GET  https://api.wavespeed.ai/api/v3/balance
"""

import concurrent.futures
import json
import logging
import os
import time
import urllib.request
import urllib.error

BASE_URL = "https://api.wavespeed.ai/api/v3"

IMAGE_TEXT_TO_IMAGE_MODEL = "openai/gpt-image-2/text-to-image"
IMAGE_EDIT_MODEL = "openai/gpt-image-2/edit"
VIDEO_IMAGE_TO_VIDEO_MODEL = "bytedance/seedance-2.0/image-to-video"

ENVIRONMENTS = ["car", "sidewalk", "room"]

logger = logging.getLogger(__name__)


def distribute_environments(n):
    """Even round-robin assignment across the fixed car/sidewalk/room set."""
    return [ENVIRONMENTS[i % len(ENVIRONMENTS)] for i in range(n)]


import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from core.errors import WaveSpeedError  # noqa: E402


class WaveSpeedClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _request(self, method, path, payload=None):
        url = f"{BASE_URL}{path}"
        data = None
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        self.logger.debug("request %s %s", method, url)
        delay = 1.0
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if attempt == 2:
                    raise WaveSpeedError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}", status=e.code)
                if e.code == 429 or 500 <= e.code < 600:
                    self.logger.warning("retrying %s %s after HTTP %s (attempt %d)", method, url, e.code, attempt + 1)
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise WaveSpeedError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}", status=e.code)
        if body.get("code") not in (200, None):
            raise WaveSpeedError(body.get("message", "unknown error"), code=body.get("code"))
        return body.get("data", body)

    def get_balance(self):
        data = self._request("GET", "/balance")
        return data.get("balance")

    def upload_file(self, file_path):
        """Upload a local reference image so it has a public download_url.
        WaveSpeed keeps uploads for 7 days. Requires the `requests` package."""
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

    def submit(self, model, payload):
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

    def generate_image(self, prompt, model=IMAGE_TEXT_TO_IMAGE_MODEL, image_url=None,
                        aspect_ratio="9:16", extra=None):
        payload = {"prompt": prompt, "aspect_ratio": aspect_ratio}
        if image_url:
            payload["images"] = [image_url]
        if extra:
            payload.update(extra)
        task_id = self.submit(model, payload)
        result = self.poll(task_id, interval=2)
        return result["outputs"][0]

    def generate_video(self, prompt, image_url, model=VIDEO_IMAGE_TO_VIDEO_MODEL,
                        duration=8, aspect_ratio="9:16", resolution="720p", extra=None):
        payload = {
            "prompt": prompt,
            "image": image_url,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if extra:
            payload.update(extra)
        task_id = self.submit(model, payload)
        result = self.poll(task_id, interval=5)
        return result["outputs"][0]

    @staticmethod
    def download(url, path):
        urllib.request.urlretrieve(url, path)
        return path

    def generate_scene(self, frame_prompt, motion_prompt, persona_reference_url,
                        duration=8, aspect_ratio="9:16", resolution="720p"):
        """Two-stage pipeline: GPT Image 2 Edit first frame -> Seedance 2.0 clip."""
        frame_url = self.generate_image(
            prompt=frame_prompt, model=IMAGE_EDIT_MODEL,
            image_url=persona_reference_url, aspect_ratio=aspect_ratio,
        )
        return self.generate_video(
            prompt=motion_prompt, image_url=frame_url,
            duration=duration, aspect_ratio=aspect_ratio, resolution=resolution,
        )

    def generate_video_job(self, job, persona_reference_url, output_dir):
        """job = {"id": "video_01", "environment": "car",
                   "scenes": [{"frame_prompt": ..., "motion_prompt": ..., "duration": 6}, ...]}"""
        job_dir = os.path.join(output_dir, job["id"])
        os.makedirs(job_dir, exist_ok=True)
        scene_paths = []
        for i, scene in enumerate(job["scenes"], start=1):
            video_url = self.generate_scene(
                frame_prompt=scene["frame_prompt"],
                motion_prompt=scene["motion_prompt"],
                persona_reference_url=persona_reference_url,
                duration=scene.get("duration", 6),
            )
            path = os.path.join(job_dir, f"scene_{i}.mp4")
            self.download(video_url, path)
            scene_paths.append(path)
        return {"id": job["id"], "environment": job.get("environment"), "scene_paths": scene_paths}


def _lock_path(output_dir):
    return os.path.join(output_dir, ".batch.lock")


def acquire_lock(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = _lock_path(output_dir)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(time.time()).encode())
        os.close(fd)
    except FileExistsError:
        raise WaveSpeedError(
            f"batch_already_running: lock file already exists at {path}. "
            "Check whether a batch is already running against this output_dir "
            "(and check the checkpoint file) before removing it.",
            code="batch_already_running",
        )
    return path


def release_lock(lock_path):
    if os.path.exists(lock_path):
        os.remove(lock_path)


def batch_generate(client, jobs, persona_reference_url, output_dir,
                    max_concurrent=3, progress_callback=None, checkpoint_path=None):
    """Run N full videos (jobs) concurrently, evenly spread across environments
    by whatever `environment` each job was already assigned upstream.

    Resumable: jobs whose id is already in checkpoint_path are skipped, so a
    killed/interrupted batch can be relaunched without re-paying for finished videos.
    Raises WaveSpeedError(code="batch_already_running") if this output_dir already
    has a batch in flight — do not delete the lock file without checking first.
    """
    os.makedirs(output_dir, exist_ok=True)
    lock_path = acquire_lock(output_dir)

    done_ids = set()
    if checkpoint_path and os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            done_ids = set(json.load(f))

    pending = [j for j in jobs if j["id"] not in done_ids]
    results = {"success": [], "failed": []}
    total = len(jobs)

    def _save_checkpoint():
        if checkpoint_path:
            with open(checkpoint_path, "w") as f:
                json.dump(sorted(done_ids), f)

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as pool:
            futures = {
                pool.submit(client.generate_video_job, job, persona_reference_url, output_dir): job
                for job in pending
            }
            for future in concurrent.futures.as_completed(futures):
                job = futures[future]
                try:
                    result = future.result()
                    results["success"].append(result)
                    done_ids.add(job["id"])
                    _save_checkpoint()
                except WaveSpeedError as e:
                    results["failed"].append({"ok": False, "id": job["id"], "error_code": e.code, "error_message": str(e.message)})
                except Exception as e:
                    results["failed"].append({"ok": False, "id": job["id"], "error_code": "unexpected", "error_message": str(e)})
                if progress_callback:
                    progress_callback(len(done_ids) + len(results["failed"]), total, job["id"])
    finally:
        release_lock(lock_path)

    return results
