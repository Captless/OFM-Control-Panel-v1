---
name: pipeline-tiktok
description: "Pipeline for generating TikTok-style short-form videos with AI-generated paragraph text. Uses WaveSpeed AI: nano-banana-2 for first frame, kling-v2.5-turbo-std for video. All outputs go into daily batch folders (outputs/YYYY-MM-DD/)."
version: 2.0.0
---

# pipeline-tiktok

Three-stage pipeline: reference image → AI video → text saved as `.txt`.

1. **Stage 1 — First frame** (`google/nano-banana-2/edit`): generates the opening image
2. **Stage 2 — Video** (`kwaivgi/kling-video-o3-pro/image-to-video`): animates the frame (5s or 10s)
3. **Stage 3 — Text output**: saves `paragraph_text` as `{filename}.txt` next to the `.mp4`

## Daily batch folders

All runs go into `outputs/YYYY-MM-DD/` — generate in the morning, add more at night, same batch.

```powershell
py pipeline-tiktok/run.py 5    # 5 clips into today's folder
py pipeline-tiktok/run.py 10   # 10 clips
```

Auto-generates:
- `{filenum}_tiktok.mp4` + `{filenum}_tiktok.txt`
- `meta.json` with labels from topic banks
- Regenerates dashboard after completion

## Running manually (advanced)

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pipeline_tiktok.wavespeed_tiktok_client import WaveSpeedTikTokClient  # lives in pipeline-tiktok/
from pipeline_tiktok.daybatch import day_path  # re-export shim from core.daybatch

client = WaveSpeedTikTokClient("api_key")
result = client.batch_generate(
    jobs=[...],
    avatar_url="...",
    output_dir=str(day_path()),
    ...
)
```

## Dashboard

```powershell
py pipeline-tiktok/dashboard.py --all       # rebuild from all date folders
py pipeline-tiktok/dashboard.py --all --serve  # serve on phone
```

## Style guide (Alina — simple altgirl)

**Look:** dark hair, pale skin, dark clothes (black tops, oversized band shirts, dark jeans/leggings, simple jewelry like a choker or small silver ring). No tattoos, minimal piercings.

**Image prompt defaults:**
- Close-up or medium shot. Face in frame.
- Dim, moody, or natural window light.
- Settings: dim bedroom, gothic café, rooftop at night, cemetery, alley with brick wall, dark living room with fairy lights, balcony at dusk.
- Expression matches text tone (reflective, wistful, deadpan, soft).
- **Always include:** `casual photo, casual lighting, iphone style photo, slightly grainy.`
- **Always end with:** `Use the reference image to accurately reproduce her facial features, body shape, proportions, and curves.`

**Video prompt defaults:**
- Minimal motion. Slow breath, micro-expression, glance away.
- No big incidents. The video is background — text does the work.

## text_generator.py

10 altgirl topic banks: situationship, self_worth, late_nights, anxiety, identity, dark_humor, dating_take, music_obsession, soft_moments, rebellion.

```python
from text_generator import random_text, batch_texts
text = random_text("alt_situationship")
texts = batch_texts(5)  # 5 random paragraphs, mixed topics
```

> `text_generator.py` is now a re-export shim from `core.text_generator`.

## Output per job

- `{stem}.mp4` — video (no text burned in)
- `{stem}.txt` — paragraph text (copy-paste ready)

## Keys

- API Key + Avatar URL: `WAVESPEED_API_KEY` env var → `../core/config.py` → `.env` file
- `WaveSpeedError` is now imported from `core.errors` (no longer defined locally)
