"""
Backfill missing prompt fields in existing meta.json files.
Reconstructs prompts from labels (scene · pose) using prompt_bank pools.
Also writes companion .prompt files for durability.

Usage:
  py scripts/backfill_prompts.py
"""

import hashlib
import json
import os
import random
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "pipeline"))

from prompt_bank import (
    INDOOR_SCENES, MIRROR_SCENES, FRAMING,
    HAIR, OUTFIT_TOPS_POOLS, OUTFIT_BOTTOMS_POOLS,
    POSES, LIGHTING_POOLS, QUALITY,
    DEFAULT_NEGATIVE, MIRROR_NEGATIVE, IDENTITY_LOCK,
    _build_prompt,
)

OUTPUTS = Path(BASE) / "outputs"

DEFAULT_LIGHTING = "warm"
DEFAULT_OUTFIT = "fem"


def _scene_and_pose_from_labels(labels):
    """Extract scene and pose from labels string.
    Format: "scene · pose"  or  just "scene"
    """
    if "·" in labels:
        parts = labels.split("·", 1)
        scene = parts[0].strip()
        pose = parts[1].strip() if len(parts) > 1 else ""
    else:
        scene = labels.strip()
        pose = ""
    return scene, pose


def _match_scene_pool(scene):
    """Rough match scene string to a camera mode."""
    s = scene.lower()
    if "mirror" in s or "wardrobe" in s:
        return "mirror"
    return "handheld"


def _pick_deterministic(stem, pool):
    """Pick from pool deterministically using stem hash."""
    h = int(hashlib.md5(stem.encode()).hexdigest()[:8], 16)
    return pool[h % len(pool)]


def backfill_meta(meta_path):
    """Backfill a single meta.json, return count of entries fixed."""
    if not meta_path.exists():
        return 0

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    changed = 0
    output_dir = meta_path.parent

    for stem, entry in meta.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("prompt"):
            continue  # already has prompt

        labels = entry.get("labels", "")
        if not labels:
            continue

        scene, pose = _scene_and_pose_from_labels(labels)
        camera_mode = _match_scene_pool(scene)
        framing = _pick_deterministic(stem + "_fr", FRAMING)
        hair = _pick_deterministic(stem + "_ha", HAIR)
        top = _pick_deterministic(stem + "_to", OUTFIT_TOPS_POOLS[DEFAULT_OUTFIT])
        bottom = _pick_deterministic(stem + "_bo", OUTFIT_BOTTOMS_POOLS[DEFAULT_OUTFIT])
        if not pose:
            pose = _pick_deterministic(stem + "_po", POSES)
        light = _pick_deterministic(stem + "_li", LIGHTING_POOLS[DEFAULT_LIGHTING])
        quality = _pick_deterministic(stem + "_qu", QUALITY)

        prompt = _build_prompt(
            camera_mode=camera_mode,
            scene=scene,
            framing=framing,
            hair=hair,
            top=top,
            bottom=bottom,
            pose=pose,
            lighting=light,
            quality=quality,
            time_of_day=None,
        )

        entry["prompt"] = prompt
        entry["negative_prompt"] = DEFAULT_NEGATIVE
        entry["guidance_scale"] = 0.55
        changed += 1

        prompt_path = output_dir / f"{stem}.prompt"
        if not prompt_path.exists():
            prompt_path.write_text(prompt, encoding="utf-8")

    if changed:
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return changed


def main():
    total_fixed = 0
    total_files = 0

    for meta_path in sorted(OUTPUTS.rglob("meta.json")):
        c = backfill_meta(meta_path)
        if c:
            rel = os.path.relpath(str(meta_path), BASE)
            print(f"  {rel}: {c} entries")
        total_fixed += c
        total_files += 1

    print(f"\nDone: {total_files} meta.json files scanned, {total_fixed} entries backfilled.")


if __name__ == "__main__":
    main()
