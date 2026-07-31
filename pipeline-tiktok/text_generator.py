"""Re-export from core.text_generator + TikTok-specific generate_jobs."""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.text_generator import *  # noqa: F401,F403


def generate_jobs(n, image_prompt_template=None):
    if image_prompt_template is None:
        image_prompt_template = (
            "Close-up candid shot, alt girl with dark hair and pale skin, "
            "wearing black, sitting in a dimly lit room, soft window light "
            "catching half her face, looking slightly off camera with a "
            "reflective expression. casual photo, casual lighting, "
            "iphone style photo, slightly grainy. "
            "Use the reference image to accurately reproduce her facial features, "
            "body shape, proportions, and curves."
        )
    texts = batch_texts(n)
    jobs = []
    for i, text in enumerate(texts):
        jobs.append({
            "image_prompt": image_prompt_template,
            "video_prompt": "auto",
            "paragraph_text": text,
            "filename": f"{i+1:03d}_tiktok.mp4",
            "metadata": {"tone": "altgirl", "topic": "mixed"},
        })
    return jobs
