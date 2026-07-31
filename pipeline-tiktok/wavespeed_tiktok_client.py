"""
wavespeed_tiktok_client.py — Three-stage TikTok video pipeline with text overlay.

Stage 1: Generate first frame via google/nano-banana-2/edit (i2i)
Stage 2: Animate frame into video via kwaivgi/kling-video-o3-pro/image-to-video
Stage 3: Burn text overlays onto the video via FFmpeg drawtext

Version: 1.0.0
"""

import json
import os
import random
import shutil
import subprocess
import tempfile
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

import requests
import logging


BASE_URL = "https://api.wavespeed.ai"
API_PREFIX = "/api/v3"

IMAGE_MODEL = "google/nano-banana-2/edit"
VIDEO_MODEL = "kwaivgi/kling-v2.5-turbo-std/image-to-video"

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT     = 30
IMAGE_POLL_INTERVAL = 5
VIDEO_POLL_INTERVAL = 10
MAX_POLL_TIMEOUT    = 600
MAX_BACKOFF_RETRIES = 5


import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.errors import WaveSpeedError  # noqa: E402


# ------------------------------------------------------------------
# Cross-platform file locking
# ------------------------------------------------------------------

def _lock_file(fd):
    if sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(fd):
    if sys.platform == "win32":
        import msvcrt
        try:
            fd.seek(0)
            msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
    else:
        import fcntl
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass


# ------------------------------------------------------------------
# FFmpeg helpers
# ------------------------------------------------------------------

def _find_ffmpeg() -> str:
    """Return path to ffmpeg executable or raise."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    # Common Windows install locations
    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise WaveSpeedError(
        "FFmpeg not found. Install it and add it to PATH. "
        "Download: https://www.gyan.dev/ffmpeg/builds/ (Windows) or `brew install ffmpeg` (Mac).",
        code="ffmpeg_not_found",
    )


def _escape_ffmpeg_text(text: str) -> str:
    """Escape special chars for FFmpeg drawtext filter."""
    return (
        text
        .replace("\\", "\\\\")
        .replace("'", "’")   # replace smart apostrophe to avoid quoting hell
        .replace(":", "\\:")
        .replace(",", "\\,")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _wrap_text(text: str, max_chars: int = 38) -> list:
    """
    Word-wrap a paragraph into lines of at most max_chars characters.
    Returns list of line strings.
    """
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


FONT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fonts", "static", "TikTokSans-Bold.ttf"
)


def _safe_temp_dir() -> str:
    """Return a temp directory whose path contains no apostrophes (FFmpeg compat)."""
    candidates = [
        os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "Temp"),
        "C:\\Temp",
        "C:\\Windows\\Temp",
        tempfile.gettempdir(),
    ]
    for d in candidates:
        if os.path.isdir(d) and "'" not in d:
            return d
    return tempfile.gettempdir()


def _safe_font_path() -> str:
    """
    Return a font path FFmpeg can embed in a filter string (no apostrophes).
    If FONT_PATH contains an apostrophe, copies the font to a safe temp location.
    """
    if not os.path.isfile(FONT_PATH):
        return None
    if "'" not in FONT_PATH:
        return FONT_PATH
    safe_dir = _safe_temp_dir()
    safe_path = os.path.join(safe_dir, "TikTokSans-Bold.ttf")
    if not os.path.isfile(safe_path):
        shutil.copy2(FONT_PATH, safe_path)
    return safe_path


def _build_paragraph_filter(
    text: str,
    font_size: int = 44,
    color: str = "white",
    start_s: float = 0.0,
    end_s: float = 0.0,
    video_duration: float = 5.0,
    bottom_margin: int = 140,
    line_spacing: int = 8,
    max_chars: int = 38,
) -> str:
    """
    Build an FFmpeg drawtext filter for a wrapped paragraph sitting in the lower third.
    Each line is a separate drawtext layer stacked bottom-up.

    Style matches the reference: small white text, soft black shadow, TikTok Sans Bold.
    """
    lines = _wrap_text(text, max_chars)
    t_end = end_s if end_s > 0 else video_duration
    # Commas inside between() must be escaped so FFmpeg doesn't treat them as option separators
    enable = f"between(t\\,{start_s}\\,{t_end})"

    # Use TikTok Sans Bold if available via a path with no apostrophes
    font_arg = ""
    safe_fp = _safe_font_path()
    if safe_fp:
        fp = safe_fp.replace("\\", "/").replace(":", "\\:")
        font_arg = f":fontfile='{fp}'"

    line_h = font_size + line_spacing
    n = len(lines)

    filters = []
    for i, line in enumerate(lines):
        escaped = _escape_ffmpeg_text(line)
        line_index_from_bottom = (n - 1 - i)
        y = f"h-{bottom_margin + line_index_from_bottom * line_h}"
        x = "(w-text_w)/2"

        f = (
            f"drawtext=text='{escaped}'"
            f":fontsize={font_size}"
            f":fontcolor={color}"
            f":shadowcolor=black@0.85:shadowx=2:shadowy=2"
            f"{font_arg}"
            f":x={x}:y={y}"
            f":enable='{enable}'"
        )
        filters.append(f)

    return ",".join(filters)


def burn_paragraph_overlay(
    input_path: str,
    output_path: str,
    text: str,
    font_size: int = 44,
    color: str = "white",
    start_s: float = 0.3,
    end_s: float = 0.0,
    video_duration: float = 5.0,
    bottom_margin: int = 140,
    max_chars: int = 38,
    ffmpeg_path: str = None,
) -> str:
    """
    Burn a wrapped paragraph of text onto a video, TikTok lower-third style.
    Matches the reference: small font, soft shadow, centered, lower third, full duration.
    Returns output_path on success.
    """
    ffmpeg = ffmpeg_path or _find_ffmpeg()
    vf = _build_paragraph_filter(
        text=text,
        font_size=font_size,
        color=color,
        start_s=start_s,
        end_s=end_s,
        video_duration=video_duration,
        bottom_margin=bottom_margin,
        max_chars=max_chars,
    )

    # Write to a safe temp dir (no apostrophe in path) — FFmpeg rejects paths with apostrophes
    tmp_fd, tmp_output = tempfile.mkstemp(suffix=".mp4", dir=_safe_temp_dir())
    os.close(tmp_fd)
    try:
        cmd = [
            ffmpeg, "-y",
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "copy",
            tmp_output,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise WaveSpeedError(
                f"FFmpeg text burn failed:\n{result.stderr[-1000:]}",
                code="ffmpeg_error",
            )

        shutil.move(tmp_output, output_path)
    except Exception:
        try:
            os.remove(tmp_output)
        except Exception:
            pass
        raise

    return output_path


# ------------------------------------------------------------------
# Main client
# ------------------------------------------------------------------

class WaveSpeedTikTokClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        if not api_key:
            raise ValueError("API key is required.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}{API_PREFIX}/{path}"

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        self.logger.debug("request %s %s", method, url)
        delay = 1.0
        resp = None
        for attempt in range(MAX_BACKOFF_RETRIES):
            try:
                resp = self.session.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
            except requests.exceptions.RequestException as e:
                if attempt == MAX_BACKOFF_RETRIES - 1:
                    raise WaveSpeedError(str(e), code="network_error")
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2
                continue

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "0"))
                wait = max(retry_after, delay) + random.uniform(0, 0.3)
                if attempt == MAX_BACKOFF_RETRIES - 1:
                    self._raise_from_response(resp)
                time.sleep(wait)
                delay *= 2
                continue

            if 500 <= resp.status_code < 600:
                if attempt == MAX_BACKOFF_RETRIES - 1:
                    self._raise_from_response(resp)
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2
                continue

            if 400 <= resp.status_code < 500:
                self._raise_from_response(resp)

            return resp

        self._raise_from_response(resp)

    def _raise_from_response(self, resp: requests.Response):
        try:
            data = resp.json()
            raise WaveSpeedError(
                code=data.get("message", "unknown"),
                message=data.get("message", resp.text[:200]),
                status=resp.status_code,
            )
        except (ValueError, KeyError):
            raise WaveSpeedError(resp.text[:200], code="http_error", status=resp.status_code)

    def _poll(self, task_id: str, poll_interval: int, timeout: int = MAX_POLL_TIMEOUT) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self._request("GET", f"predictions/{task_id}/result")
            data = resp.json().get("data", {})
            status = data.get("status")

            if status == "completed":
                outputs = data.get("outputs", [])
                if not outputs:
                    self.logger.warning("task %s completed but no outputs", task_id)
                    raise WaveSpeedError("Completed but no output URL.", code="generation_failed")
                self.logger.debug("task %s completed", task_id)
                return outputs[0]

            if status == "failed":
                self.logger.warning("task %s failed: %s", task_id, data.get("error"))
                raise WaveSpeedError(data.get("error", "Generation failed"), code="generation_failed")

            time.sleep(poll_interval + random.uniform(0, 1.0))

        self.logger.error("task %s timed out after %ss", task_id, timeout)
        raise WaveSpeedError(f"Timeout after {timeout}s on task {task_id}", code="polling_timeout")

    def _download(self, url: str, dest_path: str) -> str:
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest_path

    def get_balance(self) -> float:
        resp = self._request("GET", "balance")
        return float(resp.json().get("data", {}).get("balance", 0))

    def generate_frame(self, image_prompt: str, avatar_url: str) -> str:
        body = {
            "images": [avatar_url],
            "prompt": image_prompt,
            "enable_sync_mode": False,
            "enable_base64_output": False,
        }
        resp = self._request("POST", IMAGE_MODEL, json=body)
        task_id = resp.json()["data"]["id"]
        self.logger.debug("frame task %s submitted", task_id)
        return self._poll(task_id, poll_interval=IMAGE_POLL_INTERVAL)

    def generate_video(
        self,
        frame_url: str,
        video_prompt: str,
        aspect_ratio: str = "9:16",
        duration: int = 5,
        guidance_scale: float = None,
    ) -> str:
        body = {
            "image": frame_url,
            "prompt": video_prompt,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
        }
        if guidance_scale is not None:
            body["guidance_scale"] = guidance_scale
        resp = self._request("POST", VIDEO_MODEL, json=body)
        task_id = resp.json()["data"]["id"]
        self.logger.debug("video task %s submitted", task_id)
        return self._poll(task_id, poll_interval=VIDEO_POLL_INTERVAL)

    def generate_one(
        self,
        image_prompt: str,
        video_prompt: str,
        paragraph_text: str,
        avatar_url: str,
        output_path: str,
        aspect_ratio: str = "9:16",
        duration: int = 5,
        guidance_scale: float = 0.55,
        font_size: int = 44,
        bottom_margin: int = 140,
        max_chars: int = 38,
    ) -> dict:
        """
        Full three-stage pipeline for 1 TikTok clip.

        paragraph_text: the full text to display as a wrapped paragraph in the lower third.
                        Leave empty "" to skip text overlay.

        Returns:
            { "ok": True, "output_path": "...", "duration_s": ... }
        or:
            { "ok": False, "error_code": ..., "error_message": ..., "stage": "image|video|text", "duration_s": ... }
        """
        t0 = time.time()
        stage = "image"
        try:
            frame_url = self.generate_frame(image_prompt, avatar_url)

            stage = "video"
            video_url = self.generate_video(frame_url, video_prompt, aspect_ratio, duration, guidance_scale)

            raw_path = output_path.replace(".mp4", "_raw.mp4")
            self._download(video_url, raw_path)

            stage = "text"
            if paragraph_text and paragraph_text.strip():
                txt_path = output_path.replace(".mp4", ".txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(paragraph_text.strip())
            os.rename(raw_path, output_path)

            return {
                "ok": True,
                "output_path": output_path,
                "duration_s": round(time.time() - t0, 1),
            }

        except WaveSpeedError as e:
            return {
                "ok": False,
                "error_code": e.code,
                "error_message": e.message,
                "stage": stage,
                "duration_s": round(time.time() - t0, 1),
            }
        except Exception as e:
            return {
                "ok": False,
                "error_code": "unexpected",
                "error_message": str(e),
                "stage": stage,
                "duration_s": round(time.time() - t0, 1),
            }

    def batch_generate(
        self,
        jobs: list,
        avatar_url: str,
        output_dir: str,
        aspect_ratio: str = "9:16",
        duration: int = 5,
        max_concurrent: int = 3,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        checkpoint_path: Optional[str] = None,
    ) -> dict:
        """
        Runs N three-stage TikTok clip generations concurrently.

        jobs: list of dicts:
            {
                "image_prompt":   str,   # first frame scene setup
                "video_prompt":   str,   # motion/action description
                "paragraph_text": str,   # full text to overlay (wrapped automatically)
                "filename":       str,   # e.g. "001_tiktok.mp4"
                "metadata":       {...}  # optional
            }

        Returns:
            { success, failed, duration_s, n_total, n_success, n_failed }
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        lock_path = Path(output_dir) / ".batch.lock"
        lock_fd = open(lock_path, "w")
        try:
            _lock_file(lock_fd)
        except (BlockingIOError, OSError):
            lock_fd.close()
            raise WaveSpeedError(
                code="batch_already_running",
                message=f"Another batch is running on '{output_dir}'. No requests sent.",
            )

        lock_fd.write(
            f"pid={os.getpid()}\n"
            f"started_at={datetime.now().isoformat()}\n"
            f"n_jobs={len(jobs)}\n"
        )
        lock_fd.flush()

        try:
            completed = {}
            if checkpoint_path and Path(checkpoint_path).exists():
                with open(checkpoint_path) as f:
                    completed = json.load(f)

            results = []
            done_count = [0]
            t0 = time.time()

            def _worker(job):
                filename = job["filename"]
                output_path = os.path.join(output_dir, filename)

                if filename in completed and Path(completed[filename].get("output_path", "")).exists():
                    return {"skipped": True, "filename": filename, **completed[filename]}

                r = self.generate_one(
                    image_prompt=job["image_prompt"],
                    video_prompt=job["video_prompt"],
                    paragraph_text=job.get("paragraph_text", ""),
                    avatar_url=avatar_url,
                    output_path=output_path,
                    aspect_ratio=aspect_ratio,
                    duration=duration,
                    guidance_scale=job.get("guidance_scale", 0.55),
                )
                r["filename"] = filename
                r["metadata"] = job.get("metadata", {})

                if checkpoint_path:
                    completed[filename] = r
                    with open(checkpoint_path, "w") as f:
                        json.dump(completed, f, indent=2)

                return r

            with ThreadPoolExecutor(max_workers=max_concurrent) as pool:
                futures = {pool.submit(_worker, j): j for j in jobs}
                for fut in as_completed(futures):
                    r = fut.result()
                    results.append(r)
                    done_count[0] += 1
                    if progress_callback:
                        label = r.get("filename", "?")
                        if r.get("ok"):
                            label = f"OK  {label}"
                        elif r.get("skipped"):
                            label = f"SKIP {label} (already done)"
                        else:
                            label = f"FAIL {label} [{r.get('stage','?')} stage]: {r.get('error_message','error')}"
                        try:
                            progress_callback(done_count[0], len(jobs), label)
                        except Exception:
                            pass

            success = [r for r in results if r.get("ok")]
            failed  = [r for r in results if not r.get("ok") and not r.get("skipped")]

            return {
                "success": success,
                "failed": failed,
                "duration_s": round(time.time() - t0, 1),
                "n_total": len(jobs),
                "n_success": len(success),
                "n_failed": len(failed),
            }

        finally:
            _unlock_file(lock_fd)
            try:
                lock_fd.close()
            except Exception:
                pass
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python wavespeed_tiktok_client.py <api_key> [balance]")
        sys.exit(1)

    key = sys.argv[1]
    client = WaveSpeedTikTokClient(key)
    cmd = sys.argv[2] if len(sys.argv) > 2 else "balance"

    if cmd == "balance":
        logger.info("Balance: $%.4f", client.get_balance())
    else:
        logger.error("Unknown command: %s", cmd)
