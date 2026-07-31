"""
Save meta.json (labels) into an output folder from a prompts JSON.
Run after pipeline:
  py save_meta.py prompts.json ../outputs/batch_name
"""

import json
import os
import sys
from pathlib import Path


def save_meta(prompts_path, output_dir):
    with open(prompts_path, encoding="utf-8") as f:
        data = json.load(f)

    meta = {}
    for mode in ["photo", "video", "photo+video"]:
        for job in data.get(mode, []):
            fn = job.get("filename", "")
            stem = fn.rsplit(".", 1)[0] if "." in fn else fn
            labels = job.get("labels", "")
            if stem:
                meta[stem] = {"labels": labels}

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta_path = out / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Saved {len(meta)} labels -> {meta_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: py save_meta.py <prompts.json> <output_dir>")
        sys.exit(1)
    save_meta(sys.argv[1], sys.argv[2])
