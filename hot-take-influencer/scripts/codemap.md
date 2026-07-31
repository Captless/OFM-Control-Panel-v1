# hot-take-influencer/scripts/

## Responsibility
Minimal WaveSpeed REST client for the hot-take-influencer skill. Supports GPT Image 2 Edit (image-to-image) and Seedance 2.0 (image-to-video). Includes batch generation with environment distribution.

## Files
| File | Responsibility |
|------|---------------|
| `wavespeed_client.py` | 247-line minimal client — generate_scene, batch_generate, distribute_environments, download, get_balance |

## Key Methods
| Method | Purpose |
|--------|---------|
| `generate_scene(frame_prompt, motion_prompt, persona_reference_url, duration)` | Two-stage: first frame → video |
| `batch_generate(client, jobs, persona_reference_url, output_dir, ...)` | Concurrent video batch with checkpoint |
| `distribute_environments(n)` | Round-robins car/sidewalk/room evenly |
| `get_balance()` | Return USD balance |
| `download(url, path)` | File download helper |

## Integration
- **Depends on**: `core/errors.py` (WaveSpeedError)
- **Consumed by**: hot-take-influencer SKILL.md workflow (not used by other modules)
