# pipeline-photovideo/

## Responsibility
Photo and video generation pipelines using WaveSpeed AI. Generates alt-girl aesthetic images (nano-banana-2/edit → upscale) and animates them (kling-v2.5-turbo-std i2v).

## Files
| File | Responsibility |
|------|---------------|
| `pipeline.py` | Entry point — `mode_photo()` for photo generation, optional enhance pass, writes `.prompt` companion files |
| `prompt_bank.py` | `build_jobs_multi()` — randomized prompt builder with scene/framing/hair/top/bottom/pose/lighting pools |
| `text_generator.py` | Local text generator (alt-girl paragraphs), parallel to `core.text_generator` |
| `wavespeed_i2v_client.py` | Image-to-video client (kling-v2.5-turbo-std) |
| `alina_video_guide.md` | Video prompt style guide for Alina |
| `promptbank_1.json` | Sample generated prompt bank (kept as reference) |

## Prompt Generation (prompt_bank.py)
- 6 scene types (indoor scenes, mirror scenes, outdoor, cafe, bathroom, bedroom)
- Camera modes: handheld selfie OR mirror selfie (with phone token)
- Outfit styles: fem, street, grunge, academia + fallback
- Lighting pools: warm, cool, dimlit
- Poses: 12 torso-only positions
- Filenames: `{index:03d}_{time-md5-6}.png`

## Integration
- **Depends on**: `core/config.py`, `core/errors.py`, `core/daybatch.py`, `wavespeed-batch-api/wavespeed_client.py`
- **Consumed by**: `server.py` (imports `build_jobs_multi`, runs pipeline as subprocess), `scripts/backfill_prompts.py`
