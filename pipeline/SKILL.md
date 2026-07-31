---
name: pipeline
description: "3-mode pipeline for Alina Sky: photo, video, or photo+video packs. All outputs go into daily batch folders (outputs/YYYY-MM-DD/)."
version: 2.1.0
---

# pipeline

Three modes — all output to `outputs/YYYY-MM-DD/` daily folders:

| Mode | Subfolder | What it does |
|------|-----------|-------------|
| `photo` | `photos/` | Generate photos only (nano-banana-2 + upscale) |
| `video` | `videos/` | Animate from an existing image (kling) |
| `photo+video` | `photos/` + `videos/` | Generate photo then animate it |

## Usage

```powershell
py pipeline.py photo       --prompts prompts.json
py pipeline.py video       --prompts prompts.json
py pipeline.py photo+video --prompts prompts.json  [--with-text]
```

- All outputs go to today's folder: `outputs/YYYY-MM-DD/`
- `meta.json` auto-generated from `labels` field in prompts JSON
- `--with-text` generates altgirl paragraph text from `text_generator.py`

## Prompts JSON format

Each mode reads from the same file — the mode key determines which list is used:

```json
{
  "photo": [
    { "filename": "001_scene.png", "prompt": "...", "labels": "bedroom · mirror" }
  ],
  "video": [
    { "filename": "002_clip.mp4", "image_url": "...", "labels": "street · evening" }
  ],
  "photo+video": [
    { "filename": "003_scene.png", "prompt": "...", "labels": "cafe · window light" }
  ]
}
```

## Dashboard

```powershell
py webui/dashboard.py --all
py webui/dashboard.py --all --serve
```

## Configuration

API key and avatar URL are centralized in `core/config.py`:
- `WAVESPEED_API_KEY` env var → `core/config.py` → `.env` file (fallback to `docs/wavespeed_identity_alina.md`)
- `WAVESPEED_AVATAR_URL` env var → fallback to `docs/wavespeed_identity_alina.md`
- `WaveSpeedError` is now imported from `core.errors`

## Identity reference

API key and avatar URL are loaded from `core/config.py` (or `WAVESPEED_API_KEY` / `WAVESPEED_AVATAR_URL` env var → `.env` file).
See `docs/wavespeed_identity_alina.md` for identity details.
