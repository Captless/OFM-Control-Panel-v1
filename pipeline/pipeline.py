"""
Photo generation pipeline — nano-banana-2 → upscale, 1K resolution.

All outputs land in outputs/<today>/.

Usage:
  py pipeline.py --prompts prompts.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "..", "api"))
from core.config import API_KEY, AVATAR_URL
from wavespeed_client import WaveSpeedClient as PhotoClient
sys.path.insert(0, BASE_DIR)

from core.daybatch import day_path

def _build_meta(jobs):
    """Build a meta dict {stem: {"labels": ..., "prompt": ..., "negative_prompt": ..., "guidance_scale": ...}} from a jobs list."""
    meta = {}
    for job in (jobs or []):
        fn = job.get("filename", "")
        stem = fn.rsplit(".", 1)[0] if "." in fn else fn
        if stem:
            meta[stem] = {
                "labels": job.get("labels", ""),
                "prompt": job.get("prompt", ""),
                "negative_prompt": job.get("negative_prompt", ""),
                "guidance_scale": job.get("guidance_scale", 0.55),
            }
    return meta


def _merge_meta(existing_path, new_meta):
    """Merge new_meta into existing meta.json (new keys win)."""
    meta = {}
    if existing_path.exists():
        try:
            meta = json.loads(existing_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    meta.update(new_meta)
    existing_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"meta.json: {len(meta)} entries")


def mode_photo(jobs, enhance=False):
    client = PhotoClient(API_KEY)
    output_dir = day_path(subdir="photos")
    checkpoint = output_dir.parent / "checkpoint_photo.json"
    if checkpoint.exists():
        checkpoint.unlink()

    result = client.batch_generate(
        jobs=jobs,
        avatar_url=AVATAR_URL,
        output_dir=str(output_dir),
        resolution="1k",
        output_format="png",
        aspect_ratio="9:16",
        enhance=enhance,
        max_concurrent=3,
        progress_callback=lambda d, t, last: print(f"[{d}/{t}] {last}", flush=True),
        checkpoint_path=str(checkpoint),
    )
    print(f"\nPhotos: {result['n_success']}/{result['n_total']} | Failed: {result['n_failed']} | {result['duration_s']:.0f}s")

    if result['n_failed'] > 0:
        first_err = result['failed'][0]['error']
        print(f"{result['n_failed']}/{result['n_total']} failed. First error: {first_err}", file=sys.stderr, flush=True)
        if result['n_success'] > 0:
            _merge_meta(output_dir.parent / "meta.json", _build_meta(jobs))
        sys.exit(1)

    if result['n_success'] > 0:
        _merge_meta(output_dir.parent / "meta.json", _build_meta(jobs))
        for job in jobs:
            fn = job.get("filename", "")
            stem = fn.rsplit(".", 1)[0] if "." in fn else fn
            prompt = job.get("prompt", "")
            if stem and prompt:
                prompt_path = Path(output_dir) / f"{stem}.prompt"
                if not prompt_path.exists():
                    prompt_path.write_text(prompt, encoding="utf-8")
    return result





def load_jobs(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alina Pipeline — photo-only")
    parser.add_argument("--prompts", required=True, help="Path to prompts JSON file")
    args = parser.parse_args()

    jobs = load_jobs(args.prompts)
    mode_photo(jobs)
