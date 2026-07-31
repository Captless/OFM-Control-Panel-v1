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

from core.config import API_KEY, AVATAR_URL
from wavespeed_tiktok_client import WaveSpeedTikTokClient
from core.text_generator import batch_texts, random_text, TOPICS
from core.daybatch import day_path
IMAGE_MODEL = "google/nano-banana-2/edit"
VIDEO_MODEL = "kwaivgi/kling-v2.5-turbo-std/image-to-video"


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

    if not API_KEY:
        print("Set API_KEY in run.py or load from identity file")
        sys.exit(1)

    output_dir = day_path()
    print(f"Output: {output_dir}")

    jobs = make_jobs(args.n)
    print(f"Jobs: {len(jobs)}")

    client = WaveSpeedTikTokClient(API_KEY)
    print(f"Balance: ${client.get_balance():.4f}")

    result = client.batch_generate(
        jobs=jobs,
        avatar_url=AVATAR_URL,
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
