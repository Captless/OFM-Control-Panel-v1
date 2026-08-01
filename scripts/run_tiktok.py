"""
Run N TikTok clips into outputs/<today>/ with auto-text & auto-meta.

Usage:
  py scripts/run_tiktok.py 5          # 5 clips
  py scripts/run_tiktok.py 10 --fast  # 10 clips, more aggressive prompts
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "webui"))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "api"))

from wavespeed_tiktok_client import WaveSpeedTikTokClient
from core.text_generator import batch_texts, random_text, TOPICS
from core.daybatch import day_path

IMAGE_MODEL = "google/nano-banana-2/edit"
VIDEO_MODEL = "kwaivgi/kling-v2.5-turbo-std/image-to-video"


def _load_active_key():
    """Load the active account key from settings.json only (no env/local fallback)."""
    settings_path = Path(__file__).parent.parent / "core" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            active = settings.get("active_wavespeed_account", "")
            return settings.get("wavespeed_accounts", {}).get(active, "")
        except Exception:
            return ""
    return ""


def _load_avatar_url():
    """Load avatar URL from identity file."""
    identity_path = Path(__file__).parent.parent / "docs" / "wavespeed_identity_alina.md"
    if identity_path.is_file():
        text = identity_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "**Avatar URL:**" in line:
                return line.split("**Avatar URL:**")[1].strip()
    return ""


BASE_IMAGE_PROMPT = (
    "Close-up candid shot, alt girl with dark hair and pale skin, "
    "wearing black, dimly lit room, soft window light "
    "catching half her face, looking slightly off camera, reflective expression. "
    "casual photo, casual lighting, iphone style photo, slightly grainy. "
    "Use the reference image to accurately reproduce her facial features, "
    "body shape, proportions, and curves."
)

BASE_VIDEO_PROMPT = (
    "9:16 handheld selfie, slow subtle micro-movements, "
    "barely-there breath, eyes drift then return to camera, "
    "consistent lighting and background, preserve original composition"
)


def make_jobs(n):
    """Generate n job dicts, each with a known topic label."""
    jobs = []
    topic_keys = list(TOPICS.keys())
    for i in range(n):
        topic = random.choice(topic_keys)
        text = random_text(topic)
        jobs.append({
            "image_prompt": BASE_IMAGE_PROMPT,
            "video_prompt": "auto",
            "paragraph_text": text,
            "filename": f"{i+1:03d}_tiktok.mp4",
            "metadata": {"topic": topic},
            "_topic": topic,
        })
    return jobs


def save_meta(output_dir, jobs):
    """Save meta.json: {stem: {"labels": "<topic>"}}."""
    meta = {}
    for job in jobs:
        fn = job["filename"]
        stem = fn.rsplit(".", 1)[0]
        topic = job.get("_topic", "")
        labels = f"altgirl · {topic.replace('alt_', '')}" if topic else ""
        meta[stem] = {"labels": labels}
    meta_path = Path(output_dir) / "meta.json"
    # Merge with existing
    existing = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(meta)
    meta_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"meta.json: {len(existing)} entries -> {meta_path}")


def main():
    parser = argparse.ArgumentParser(description="Run TikTok batch into daily folder")
    parser.add_argument("n", type=int, nargs="?", default=5, help="Number of clips (default 5)")
    parser.add_argument("--fast", action="store_true", help="Use faster video model / shorter duration")
    args = parser.parse_args()

    api_key = _load_active_key()
    if not api_key:
        print("No active API account. Add one via the API selector in the web UI.", file=sys.stderr)
        sys.exit(1)

    output_dir = day_path()
    print(f"Output: {output_dir}")

    jobs = make_jobs(args.n)
    print(f"Jobs: {len(jobs)}")

    client = WaveSpeedTikTokClient(api_key)
    avatar_url = _load_avatar_url()
    print(f"Balance: ${client.get_balance():.4f}")

    result = client.batch_generate(
        jobs=jobs,
        avatar_url=avatar_url,
        output_dir=str(output_dir),
        aspect_ratio="9:16",
        duration=5,
        max_concurrent=3,
        progress_callback=lambda d, t, last: print(f"[{d}/{t}] {last}", flush=True),
        checkpoint_path=str(output_dir / "checkpoint.json"),
    )

    print(f"\nDone: {result['n_success']}/{result['n_total']} success | {result['n_failed']} failed | {result['duration_s']:.0f}s")

    save_meta(output_dir, jobs)

    # Regenerate dashboard
    dashboard_py = os.path.join(BASE, "webui", "dashboard.py")
    os.system(f"py \"{dashboard_py}\" --all")


if __name__ == "__main__":
    main()
