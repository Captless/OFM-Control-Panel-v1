"""
Prompt bank for Alina Sky photo generation.
v3 — two camera modes (handheld / mirror), no shake bank, torso-only poses.
"""

import random
import hashlib
import json
import os
import time

# ---------------------------------------------------------------------------
# SCENES
# ---------------------------------------------------------------------------

INDOOR_SCENES = [
    "standing casually near closet in a dim bedroom",
    "standing near bathroom sink area",
    "standing near couch in a dim living room",
    "standing near wardrobe",
    "standing near sofa in dim living room",
    "standing casually in bathroom with tiled background",
]

MIRROR_SCENES = [
    "standing near bathroom sink area",
    "standing near wardrobe",
]

OUTDOOR_SCENES = [
    "standing in a dim alley at dusk with brick walls behind",
    "standing on a quiet city street at night under a streetlamp",
    "standing near a graffiti wall in a dim city corner",
    "standing on a rooftop at night with city lights blurred behind",
    "standing by a parked car on a dim street at night",
    "standing in front of a dark storefront with soft neon glow",
]

# ---------------------------------------------------------------------------
# FRAMING
# ---------------------------------------------------------------------------

FRAMING = [
    "slight torso angle with uneven framing, head to waist composition",
    "slightly off-center framing, head to waist shot",
    "uneven framing with slight tilt, head to waist crop",
    "uneven framing, head to waist shot",
]

# ---------------------------------------------------------------------------
# HAIR
# ---------------------------------------------------------------------------

HAIR = [
    "damp half-up hairstyle with loose strands sticking flat to temples and neck",
    "wet side-parted hair clinging to one side of face and neck",
    "damp loose wavy hair with strands falling across cheeks",
    "wet tousled hair sticking unevenly to neck and shoulders",
    "damp low bun with loose strands around face",
    "natural messy slightly voluminous hair",
    "damp messy twin buns with loose strands sticking to forehead and jawline",
    "wet slick low bun with strands clinging to temples and neck",
]

# ---------------------------------------------------------------------------
# OUTFIT TOPS
# ---------------------------------------------------------------------------

OUTFIT_TOPS_POOLS = {
    "fem": [
        "black fitted micro tank top with ultra-thin straps, distressed edges, subtle faded gothic print text",
        "dark charcoal asymmetrical cut-out crop top with single-shoulder strap design, double-layer matte fabric with visible seam lines and subtle ribbed texture",
        "black halter-style fitted micro top with ultra-thin neck strap, contour stitching and matte stretch fabric with subtle tension lines",
        "black strappy bandeau micro top with multiple thin intersecting straps, layered construction with irregular cut panels, raw hems and distressed stitching, faint washed gothic symbol print across chest",
        "black fitted crop top with lace-trim neckline and sheer mesh overlay inserts, soft matte fabric with subtle shaping seams and delicate texture",
        "black fitted micro tank top with ultra-thin straps, irregular distressing and frayed seams, subtle faded attitude print across chest, uneven hemline",
    ],
    "street": [
        "oversized black graphic tee with faded vintage band print, worn collar, boxy relaxed fit hanging loose off one shoulder",
        "distressed grey washed hoodie with raw edges and oversized silhouette, layered over thin long-sleeved tee underneath",
        "loose charcoal crewneck sweatshirt with wide ribbed neck, relaxed street wear fit, over longline camisole tank",
        "black tech windbreaker vest over fitted torso top, visible crossbody bag strap, urban practical layering",
    ],
    "grunge": [
        "faded black band tee with barely readable graphic, worn thin fabric with small holes, uneven frayed hem",
        "dark plaid flannel shirt unbuttoned over a black fitted tank, rolled sleeves, silver chain layered visible",
        "distressed black cropped knit sweater with one loose sleeve thread trailing, uneven chunky texture, thrifted look",
        "grey washed vintage concert tee layered under slouchy charcoal knit cardigan, oversized sleeves bunched at wrists",
    ],
    "academia": [
        "black fitted turtleneck in fine ribbed knit, close-to-body cut, matte texture against skin",
        "dark forest green chunky knit sweater with wide ribbed collar, white collared blouse visible at neckline",
        "cream high-neck blouse with subtle eyelet embroidery along collar, small silver pendant at center front",
        "off-white relaxed fit soft blazer layered over black camisole top, visible silk texture at neckline",
        "deep wine tone slim-fit merino wool pullover with subtle stitch detail at shoulders",
    ],
}

# ---------------------------------------------------------------------------
# OUTFIT BOTTOMS
# ---------------------------------------------------------------------------

OUTFIT_BOTTOMS_POOLS = {
    "fem": [
        "high-waisted black tight shorts with contour stitching and slight shaping seams",
        "structured black cargo pants with oversized pockets, stitched panels and hanging strap details",
        "black slim joggers with tapered silhouette, seam detailing and soft folds at ankle",
        "high-waisted black micro shorts, smooth finish with subtle contour seams",
        "black cargo pants with structured pockets, stitched panel detailing and relaxed fit with soft folds",
        "high-waisted black cargo shorts with oversized flap pockets, reinforced side seams and subtle strap details",
    ],
    "street": [
        "black wide-leg cargo pants with oversized flap pockets, stacked and pooling slightly over shoes",
        "dark grey slim-fit chino style trousers with zip front, sharp contained silhouette",
        "distressed raw hem ripped denim jeans with loose boxy fit hanging around ankle",
        "black baggy basketball shorts double layered over sheer compression tights, hitting mid inner knee",
    ],
    "grunge": [
        "ripped black slim denim with vintage wash, tears just above the thighs, threads spilling off the hem",
        "black and grey distressed denim jeans with random pattern patch and elastic waistband",
        "heavy washed black jeans, whiskering folds with deep shadow indent, sharp fade on raw fabric",
        "black velvet thin fabric trousers with full-leg pinstripe, wrinkled slouch around the ankles",
    ],
    "academia": [
        "dark wool high-waist pleated trousers in soft black plaid, front crease straight from hip to foot",
        "dark wine wide-leg pleated trousers from waist, pooling slight break at top of shoe",
        "black full-length narrow pants with prominent central crease, ending straight with cuffs resting on ankle",
        "deep charcoal tailored trousers with subtle drape, fitted through seat, relaxed at hem",
    ],
}

# ---------------------------------------------------------------------------
# POSES — torso/hip/general only, no arms/hands/lean
# ---------------------------------------------------------------------------

POSES = [
    "natural fit-check posture, slight hip shift, relaxed stance",
    "slight torso shift, comfortable relaxed posture",
    "subtle weight shift, confident composed stance",
    "slight body angle shift, natural hip position",
    "subtle hip tilt, comfortable mid-frame posture",
    "relaxed stance, subtle shift in weight to one side",
    "slight lean forward, weight balanced on one foot, natural candid pause mid-movement",
    "subtle waist shift to one side, hip popped slightly higher, relaxed asymmetrical stance",
    "soft angle turn of torso, shoulders naturally uneven, casual mid-frame posture",
    "natural body weight rest with shoulders tilted slightly off-center, comfortable paused pose",
    "slight shift in stance with one foot forward, head straight, relaxed fit position",
    "subtle profile shift, body turned slightly sideways from the camera, natural frame direction",
]

# ---------------------------------------------------------------------------
# LIGHTING
# ---------------------------------------------------------------------------

LIGHTING_POOLS = {
    "warm": [
        "dim subtle warm indoor lighting, soft shadows",
        "dim subtle warm ambient light, soft natural shadows",
        "dim warm low light, moody shadows with soft falloff",
        "dim warm bathroom lighting, soft tile reflections",
        "subtle dim warm light, soft gentle shadows on face",
    ],
    "cool": [
        "cool soft window light, pale blue white wash, delicate shadows across features",
        "cool daylight bouncing off white walls, crisp clean natural tones, airy atmosphere",
        "overcast cool ambient light, soft blue grey shadow split across one side of face",
        "cool bathroom light, cold white tile bounce, sharp clean reflections on skin",
        "cool evening light through window, muted blue undertones, quiet still mood",
    ],
    "dimlit": [
        "very dim low light, deep shadows swallowing edges, barely lit, moody darkness",
        "single dim bulb overhead casting long shadows downward across features",
        "pitch black room, curtain filtered sliver of light, dark film noir atmosphere",
        "screen lit face, phone glow reflecting softly on skin, room nearly pitch black",
        "deep shadow heavy mood, only ambient bounce lighting dark corners, intimate gloom",
    ],
}

# ---------------------------------------------------------------------------
# QUALITY
# ---------------------------------------------------------------------------

QUALITY = [
    "imperfect composition, authentic amateur snapchat aesthetic, deep blacks, moody contrast, photorealistic skin texture, subtle film grain, high detail, non-AI aesthetic",
    "imperfect composition, snapchat realism, deep dark tones, moody atmosphere, photorealistic skin texture, subtle grain, high detail, authentic lifestyle feel",
]

# ---------------------------------------------------------------------------
# NEGATIVES
# ---------------------------------------------------------------------------

DEFAULT_NEGATIVE = (
    "smiling, phone visible, mirror selfie, lamp object visible, "
    "overly staged pose, studio lighting, perfect symmetry, unrealistic skin, CGI look, cleavage"
)

MIRROR_NEGATIVE = (
    "smiling, lamp object visible, "
    "overly staged pose, studio lighting, perfect symmetry, unrealistic skin, CGI look, cleavage"
)

# ---------------------------------------------------------------------------
# IDENTITY LOCK
# ---------------------------------------------------------------------------

IDENTITY_LOCK = "keep model identity/lip color consistent/accurate/similar"

# ---------------------------------------------------------------------------
# BUILD PROMPT
# ---------------------------------------------------------------------------

def _build_prompt(camera_mode, scene, framing, hair, top, bottom, pose, lighting, quality, time_of_day=None):
    camera_intro = "Front-facing handheld selfie"

    if camera_mode == "mirror":
        phone_token = "mirror selfie"
        negative = MIRROR_NEGATIVE
    else:
        phone_token = "no phone visible"
        negative = DEFAULT_NEGATIVE

    parts = [
        camera_intro,
        "vertical 9:16",
        phone_token,
        scene,
        framing,
        hair,
        top,
        bottom,
        "candid and unposed",
        pose,
        lighting,
    ]

    if time_of_day == "day":
        parts.append("natural daylight")
    elif time_of_day == "night":
        parts.append("natural night vibe")

    parts.append(quality)

    prompt = ", ".join(parts)

    result = f"{prompt}\n"
    if camera_mode == "mirror":
        result += "black iPhone\n"
    result += f"\nnegative prompt: {negative}\n"
    result += IDENTITY_LOCK
    return result


# ---------------------------------------------------------------------------
# JOB BUILDER
# ---------------------------------------------------------------------------

def build_jobs_multi(count=1, vibe=None, outfit_style=None, camera_style=None, lighting=None, time_of_day=None):
    if vibe == "indoor":
        if camera_style == "mirror":
            scene_pool = MIRROR_SCENES
        else:
            scene_pool = INDOOR_SCENES
    elif vibe == "outdoor":
        scene_pool = OUTDOOR_SCENES
    else:
        if camera_style == "mirror":
            scene_pool = MIRROR_SCENES
        else:
            scene_pool = INDOOR_SCENES

    # Lighting pool selection
    if lighting in LIGHTING_POOLS:
        light_pool = LIGHTING_POOLS[lighting]
    else:
        light_pool = []
        for v in LIGHTING_POOLS.values():
            light_pool.extend(v)

    # Outfit pool selection
    if outfit_style in OUTFIT_TOPS_POOLS:
        top_pool = OUTFIT_TOPS_POOLS[outfit_style]
        bottom_pool = OUTFIT_BOTTOMS_POOLS.get(outfit_style, [])
    else:
        top_pool = []
        for v in OUTFIT_TOPS_POOLS.values():
            top_pool.extend(v)
        bottom_pool = []
        for v in OUTFIT_BOTTOMS_POOLS.values():
            bottom_pool.extend(v)

    jobs = []
    for _ in range(count):
        scene = random.choice(scene_pool)
        framing = random.choice(FRAMING)
        hair = random.choice(HAIR)
        top = random.choice(top_pool)
        bottom = random.choice(bottom_pool)
        pose = random.choice(POSES)
        light = random.choice(light_pool)
        quality = random.choice(QUALITY)

        camera_mode = "mirror" if camera_style == "mirror" else "handheld"
        prompt = _build_prompt(camera_mode, scene, framing, hair, top, bottom, pose, light, quality, time_of_day)

        short_id = hashlib.md5((str(len(jobs)) + str(time.time())).encode()).hexdigest()[:6]
        filename = f"{len(jobs)+1:03d}_{short_id}.png"

        jobs.append({
            "prompt": prompt,
            "filename": filename,
            "labels": f"{scene.split(',')[0]} · {pose}",
            "video_prompt": "auto",
            "negative_prompt": DEFAULT_NEGATIVE,
            "guidance_scale": 0.55,
            "duration": 5,
        })

    return jobs


# ---------------------------------------------------------------------------
# SAVE HELPER
# ---------------------------------------------------------------------------

def save_promptbank(jobs, vibe=None, lighting_label=None, suffix=""):
    base = os.path.dirname(os.path.abspath(__file__))
    parts = ["promptbank"]
    if vibe:
        parts.append(vibe)
    if lighting_label:
        parts.append(lighting_label)
    if suffix:
        parts.append(suffix)
    parts.append("1")
    filename = "_".join(parts) + ".json"
    path = os.path.join(base, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(jobs)} jobs -> {path}")
    return path


# ---------------------------------------------------------------------------
# BACKWARDS-COMPAT EXPORTS FOR SERVER
# ---------------------------------------------------------------------------

def list_presets():
    return {
        "vibes": ["indoor", "outdoor"],
        "camera_styles": ["handheld", "mirror"],
        "outfit_styles": ["any", "fem", "street", "grunge", "academia"],
        "lighting": ["warm", "cool", "dimlit"],
        "time_of_day": ["day", "night"],
    }


def build_jobs(*args, **kwargs):
    return build_jobs_multi(*args, **kwargs)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    vibe = sys.argv[2] if len(sys.argv) > 2 else None
    camera = sys.argv[3] if len(sys.argv) > 3 else None
    tod = sys.argv[4] if len(sys.argv) > 4 else None

    jobs = build_jobs_multi(count=n, vibe=vibe, camera_style=camera, time_of_day=tod)
    for i, job in enumerate(jobs, 1):
        print(f"\n{'='*60}")
        print(f"JOB {i} — {job['filename']}")
        print(f"{'='*60}")
        print(job["prompt"])
        print(f"labels: {job['labels']}")

    save_promptbank(jobs, vibe=vibe)