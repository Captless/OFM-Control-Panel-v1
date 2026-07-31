# hot-take-influencer/

## Responsibility
Opinion/talking-head video persona workflow for TikTok/Reels/Shorts. Supports dating positivity (older men) and controversial hot takes. GPT Image 2 Edit for stills, Seedance 2.0 for lip-synced video.

## Files
| File | Responsibility |
|------|---------------|
| `SKILL.md` | Full workflow: persona setup → scripting → scene prompts → WaveSpeed generation |
| `scripts/wavespeed_client.py` | Minimal WaveSpeed client for GPT Image 2 + Seedance 2.0, with `distribute_environments()` + `batch_generate()` |

## Key Concepts
- 3 fixed environments: Car (driver/passenger), Sidewalk (urban walking), Room (lived-in indoor)
- Two-stage gen: still first frame (GPT Image 2 Edit) → animated clip (Seedance 2.0 i2v)
- Scripts: hook → body (2-3 beats) → CTA, each line in quotes for lip-sync

## Integration
- **Depends on**: `core/errors.py` (WaveSpeedError), `wavespeed_client.py` (local)
- **Not consumed by**: Other modules (independent skill workflow)
