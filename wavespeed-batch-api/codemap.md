# wavespeed-batch-api/

## Responsibility
Reusable WaveSpeed AI REST client. Handles image generation (nano-banana-2/edit), enhancement (image-enhancer), and concurrent batch processing with checkpoint/resume.

## Files
| File | Responsibility |
|------|---------------|
| `wavespeed_client.py` | Full REST client — generate, enhance, batch_generate, get_balance, file lock for batch safety |

## Key Methods (WaveSpeedClient)
| Method | Purpose |
|--------|---------|
| `generate(prompt, image_url, resolution, format, aspect_ratio)` | Submit + poll single image gen |
| `enhance(image_url, scale, format)` | Upscale 4x |
| `get_balance()` | Return USD balance (float) |
| `batch_generate(jobs, avatar_url, output_dir, ...)` | Concurrent batch with checkpoint/resume + lock file |

## API Details
- Base URL: `https://api-ondemand.wavespeed.ai/api/v3`
- Image model: `google/nano-banana-2/edit`
- Enhance model: `wavespeed-ai/image-enhancer`
- Auth: Bearer token in `Authorization` header

## Integration
- **Depends on**: `core/errors.py` (WaveSpeedError)
- **Consumed by**: `pipeline-photovideo/pipeline.py`, `pipeline-tiktok/server.py`, `pipeline-tiktok/run.py`
