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
from wavespeed_client import WaveSpeedClient as PhotoClient, _is_explicit_flag
sys.path.insert(0, BASE_DIR)

from core.daybatch import day_path


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
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core"))
    from core.config import _parse_identity_file  # noqa: E402
    identity = _parse_identity_file()
    return identity.get("avatar_url", "")


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
    print("@P starting|Initializing pipeline\u2026", flush=True)
    api_key = _load_active_key()
    if not api_key:
        print("ERROR: No active API account. Add one via the API selector in the web UI.", file=sys.stderr)
        sys.exit(1)
    
    client = PhotoClient(api_key)
    avatar_url = _load_avatar_url()
    output_dir = day_path(subdir="photos")
    checkpoint = output_dir.parent / "checkpoint_photo.json"
    if checkpoint.exists():
        checkpoint.unlink()

    result = client.batch_generate(
        jobs=jobs,
        avatar_url=avatar_url,
        output_dir=str(output_dir),
        resolution="1k",
        output_format="png",
        aspect_ratio="9:16",
        enhance=enhance,
        max_concurrent=3,
        progress_callback=lambda d, t, last: print(f"[{d}/{t}] {last}", flush=True),
        status_callback=lambda status, elapsed: print(f"@P processing|WaveSpeed {status} {elapsed}s", flush=True),
        checkpoint_path=str(checkpoint),
    )
    print(f"\nPhotos: {result['n_success']}/{result['n_total']} | Failed: {result['n_failed']} | {result['duration_s']:.0f}s")

    if result['n_failed'] > 0:
        first_err = result['failed'][0]['error']
        if result.get('explicit_hit'):
            for f in result['failed']:
                if _is_explicit_flag(str(f['error'])):
                    first_err = f['error']
                    break
            msg = f"explicit_content_flagged: {first_err}"
            print(f"@P failed|explicit_content|{msg}", flush=True)
            print(f"@P failed|explicit_content|{msg}", file=sys.stderr, flush=True)
            sys.exit(1)
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
    try:
        mode_photo(jobs)
    except SystemExit:
        raise
    except Exception as e:
        print(f"@P failed|{e}", flush=True)
        print(f"@P failed|{e}", file=sys.stderr, flush=True)
        sys.exit(1)
