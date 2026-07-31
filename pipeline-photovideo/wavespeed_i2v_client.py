"""
WaveSpeed Image-to-Video client — kling-v2.5-turbo-std direct image-to-video.

Matches the saved "Image to Video" workflow:
- Model: kwaivgi/kling-v2.5-turbo-std/image-to-video
- Guidance scale: 0.55
- Duration: 5s (or 10s)
- Input: reference image + prompt + optional negative prompt
- Output: MP4 video
"""

import json
import os
import time
import urllib.request
import urllib.error
import logging

BASE_URL = "https://api.wavespeed.ai/api/v3"
VIDEO_MODEL = "kwaivgi/kling-v2.5-turbo-std/image-to-video"

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.errors import WaveSpeedError  # noqa: E402

logger = logging.getLogger(__name__)


class WaveSpeedI2VClient:
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
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise WaveSpeedError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}", status=e.code)
        if body.get("code") not in (200, None):
            raise WaveSpeedError(body.get("message", "unknown error"), code=body.get("code"))
        return body.get("data", body)

    def get_balance(self):
        data = self._request("GET", "/balance")
        return data.get("balance", 0.0)

    def generate_video(self, image_url, prompt, negative_prompt="",
                       guidance_scale=0.55, duration=5):
        payload = {
            "image": image_url,
            "prompt": prompt,
            "guidance_scale": guidance_scale,
            "duration": duration,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        payload["model"] = VIDEO_MODEL
        data = self._request("POST", f"/{VIDEO_MODEL}", payload)
        task_id = data["id"]
        self.logger.debug("task %s submitted", task_id)

        deadline = time.time() + 600
        interval = 5
        while time.time() < deadline:
            result = self._request("GET", f"/predictions/{task_id}/result")
            status = result.get("status")
            if status == "completed":
                self.logger.debug("task %s completed", task_id)
                return result["outputs"][0]
            if status == "failed":
                self.logger.warning("task %s failed: %s", task_id, result.get("error"))
                raise WaveSpeedError(f"generation_failed: {result.get('error')}", code="generation_failed")
            time.sleep(interval)
        self.logger.error("task %s timed out", task_id)
        raise WaveSpeedError("polling_timeout", code="polling_timeout")

    @staticmethod
    def download(url, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
        return path

    def generate(self, image_url, prompt, negative_prompt="",
                 guidance_scale=0.55, duration=5, output_path=None):
        video_url = self.generate_video(
            image_url=image_url,
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            duration=duration,
        )
        self.logger.debug("video generated for prompt: %.50s", prompt)
        if output_path:
            self.download(video_url, output_path)
            return output_path
        return video_url
