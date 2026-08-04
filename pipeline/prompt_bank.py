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
    "standing casually near closet in a dim bedroom, facing camera",
    "standing near bathroom sink area, facing camera",
    "standing near couch in a dim living room, facing camera",
    "standing near wardrobe with slightly messy background, facing camera",
    "standing near sofa in dim living room, facing camera",
    "standing casually in bathroom with tiled background, facing camera",
]

MIRROR_SCENES = [
    "standing near bathroom sink area",
    "standing near wardrobe",
    "standing casually beside an open closet in a dim bedroom",
    "standing casually near bathroom sink area with tiled background",

]

OUTDOOR_SCENES = [
    "standing in a dim alley with brick walls behind",
    "standing on a quiet city street under a streetlamp",
    "standing near a graffiti wall in a dim city corner",
    "standing on a rooftop with city lights blurred behind",
    "standing by a parked car on a dim street",
]

# ---------------------------------------------------------------------------
# FRAMING
# ---------------------------------------------------------------------------

FRAMING = [
    "slight torso angle with uneven framing, head to waist composition, midshot",
    "slightly off-center framing, head to waist shot, midshot",
    "uneven framing with slight tilt, head to waist crop, midshot",
    "uneven framing, head to waist shot, midshot",
]

# ---------------------------------------------------------------------------
# HAIR
# ---------------------------------------------------------------------------

HAIR = [
    "damp half-up hairstyle with loose strands sticking flat to temples and neck",
    "wet side-parted hair clinging to one side of face and neck",
    "damp loose hair with strands falling across cheeks",
    "wet tousled hair sticking unevenly to neck and shoulders",
    "damp low bun with loose strands around face",
    "natural messy hair",
    "damp messy twin buns with loose strands sticking to forehead and jawline",
    "wet slick low bun with strands clinging to temples and neck",
]

# ---------------------------------------------------------------------------
# OUTFIT TOPS
# ---------------------------------------------------------------------------

OUTFIT_TOPS_POOLS = {
    "sexy": [
        "black fitted micro tank top with ultra-thin straps, distressed edges, subtle faded gothic print text",
        "black strappy bandeau crop top with multiple thin intersecting straps, layered construction with irregular cut panels, raw hems and distressed stitching, faint washed gothic symbol print across chest",
        "black fitted micro cami with ultra-thin straps, soft matte cotton blend, subtle lace trim along neckline, delicate seam shaping and slight stretch tension",
        "charcoal asymmetrical cut-out crop top with single-shoulder strap design, double-layer matte fabric with visible seam lines and subtle ribbed texture",
        "black soft crop top with one thin strap and lightly draped neckline, smooth stretch fabric with minimal seams",
        "black halter-neck micro top with thin strap around neck, cut-out back, fitted stretch fabric",
        "black fitted tube top with ribbed knit texture, slight stretch, banded top edge",
        "black off-shoulder fitted crop top with long sleeves, ruched elastic along neckline",
        "black bodycon crop top with square neckline, fitted through torso, thick straps",
    ],
    "date_night": [
        "cream silk camisole with adjustable spaghetti straps, subtle cowl neck, matte finish",
        "black fitted turtleneck in fine ribbed knit, close-to-body cut, matte texture against skin",
        "off-white relaxed fit soft blazer layered over black camisole top, visible silk texture at neckline",
        "deep wine tone slim-fit merino wool pullover with subtle stitch detail at shoulders",
        "dark forest green chunky knit sweater with wide ribbed collar, white collared blouse visible at neckline",
        "cream high-neck blouse with subtle eyelet embroidery along collar, small silver pendant at center front",
        "black satin wrap top with deep neckline, self-tie at waist, smooth drape",
        "pale ivory silk camisole with lace trim at hem, thin straps",
        "charcoal knit cardigan over white fitted blouse, structured layering",
    ],
    "night_club": [
        "black lace long-sleeve top with strategic opaque panels, high neck",
        "black corset-style top with visible boning, lace-up back, sweetheart neckline",
        "black sequin crop top with halter neck, open back, cropped to underbust",
        "charcoal cut-out bodysuit with geometric cutouts at waist, snap closure",
        "black velvet crop top with square neck, long fitted sleeves, cropped hem",
        "black leather-look fitted top with zip front, stand collar",
        "silver metallic halter top with ruched fabric, thin neck strap",
        "black fringe crop top with layered fringe hem, fitted bandeau base",
        "black sheer top with lined bodice, long sleeves",
    ],
    "baggy": [
        "oversized black graphic tee with faded vintage band print, worn collar, boxy relaxed fit hanging loose off one shoulder",
        "loose charcoal crewneck sweatshirt with wide ribbed neck, relaxed street wear fit, over longline camisole tank",
        "black tech windbreaker vest over fitted torso top, visible crossbody bag strap, urban practical layering",
        "grey washed vintage concert tee layered under slouchy charcoal knit cardigan, oversized sleeves bunched at wrists",
        "black oversized hoodie with dropped shoulders, raw hem, kangaroo pocket",
        "black oversized long-sleeve tee with wide sleeves, boxy fit, slightly cropped",
        "dark grey oversized flannel shirt worn open over black tank, rolled sleeves",
        "black puffer vest over baggy long-sleeve top, matte finish",
        "oversized black denim jacket over white graphic tee, relaxed unbuttoned",
    ],
    "lounge_sexy": [
        "black silk robe with kimono sleeves, self-tie belt, mid-thigh length",
        "white cotton bralette with delicate floral embroidery, thin straps",
        "oversized men's white dress shirt unbuttoned, worn off one shoulder",
        "black lace camisole with adjustable straps, scalloped hem",
        "charcoal ribbed knit bralette with square neck, wide straps, cropped",
        "black satin camisole with thin straps, smooth drape, lace trim",
        "white cotton bralette with delicate stitching, soft stretch fabric",
        "black satin slip top, deep v-neck, thin straps",
        "cream knit crop cardigan open, loose fit",
    ],
}

# ---------------------------------------------------------------------------
# OUTFIT BOTTOMS
# ---------------------------------------------------------------------------

OUTFIT_BOTTOMS_POOLS = {
    "sexy": [
        "high-waisted beige cargo pants with smooth finish and subtle contour seams",
        "high-waisted sweatpants slight shaping seams",
        "black high-waisted micro shorts",
        "structured black cargo pants with oversized flap pockets, reinforced side seams and subtle strap details",
        "black fitted lounge shorts with subtle stitching and soft fabric folds",
        "black high-waisted biker shorts with ruched side seams, tight fit",
        "black denim pants with distressed hem, high-waisted fit",
        "black satin mini skirt with high waist, short length",
        "black bodycon skirt, mid-thigh length, fitted through hips",
    ],
    "date_night": [
        "dark wine wide-leg pleated trousers",
        "dark wool high-waist pleated trousers in soft black plaid, front crease",
        "black full-length narrow pants with prominent central crease",
        "deep charcoal tailored trousers with subtle drape, fitted through seat, relaxed at hem",
        "black high-waisted pleated midi skirt in structured wool blend, clean lines",
        "black satin midi skirt with slit, smooth drape, elastic waist",
        "dark grey slim-fit trousers with zip front, sharp contained silhouette",
        "black fitted pencil skirt, knee length, back slit",
        "navy tailored trousers with subtle pinstripe",
    ],
    "night_club": [
        "black leather mini skirt with asymmetrical zip hem, low-rise fit",
        "black high-waisted vinyl shorts with side zip, structured waistband",
        "black wide-leg trousers with metallic thread woven through, dramatic flare",
        "black fitted midi skirt with thigh-high slit, hidden side zip",
        "black cargo pants with chain details, oversized pockets",
        "black sequin mini skirt, high waist, short length",
        "black mini skirt in patent leather, straight silhouette",
        "black skinny trousers with side stripe detail",
        "black cut-out shorts with side zip, high-waisted, structured fit",
    ],
    "baggy": [
        "black wide-leg cargo pants with oversized flap pockets, stacked and pooling slightly over shoes",
        "distressed raw hem ripped denim jeans with loose boxy fit hanging around ankle",
        "black baggy basketball shorts double layered over sheer compression tights, hitting mid inner knee",
        "black oversized joggers with elastic waist, dropped crotch, cuffed ankles",
        "dark grey wide-leg trousers with pleated front, relaxed through hip",
        "black parachute pants with gathered ankles, loose leg",
        "baggy light-wash denim jeans with oversized leg opening, slouchy fit",
        "black cargo joggers with oversized pockets, drawstring waist, baggy leg",
        "grey sweatpants with ribbed ankle cuffs, relaxed fit",
    ],
    "lounge_sexy": [
        "black lace-trim short shorts, high-waisted, elastic waist",
        "black satin high-waisted shorts with side slit, relaxed fit",
        "black high-cut briefs, minimal coverage",
        "black boy-short lounge pants, elastic waist, mid-calf length",
        "black silk pajama shorts with drawstring waist, contrast piping",
        "white lace-trim cotton shorts, elastic waist, relaxed",
        "black high-waisted lace shorts, delicate panels",
        "black satin boxer shorts, elastic waist, loose fit",
        "black lounge shorts with ruched side seams, high-waisted, soft fabric",
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
        "dim subtle warm lamp indoor lighting, soft shadows",
        "dim subtle warm lamp ambient light, soft natural shadows",
        "dim warm low light, moody shadows with soft falloff",
        "dim warm bathroom lighting, soft tile reflections",
        "subtle dim warm lamp light, soft gentle shadows on face",
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
#    "imperfect composition, snapchat realism, deep dark tones, moody atmosphere, photorealistic skin texture, subtle grain, high detail, authentic lifestyle feel, shot on iPhone 15 Pro Max",
#    "imperfect composition, authentic amateur snapchat-style quality, deep blacks, moody contrast, photorealistic skin texture, subtle film grain, high detail, non-AI aesthetic, shot on iPhone 15 Pro Max",
    "imperfect composition, snapchat realism, photorealistic skin texture, subtle grain, high detail, instagram-style iphone photo quality, natural lighting falloff with soft shadows and warm tone balance, realistic dynamic range with muted highlights and deep blacks, authentic unfiltered look"
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

IDENTITY_LOCK = "keep model identity, hair/lip color consistent/accurate/similar"

# ---------------------------------------------------------------------------
# BUILD PROMPT
# ---------------------------------------------------------------------------

def _build_prompt(camera_mode, scene, framing, hair, top, bottom, pose, lighting, quality, time_of_day=None, identity_lock=None):
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
    result += identity_lock if identity_lock else IDENTITY_LOCK
    return result


# ---------------------------------------------------------------------------
# JOB BUILDER
# ---------------------------------------------------------------------------

def _resolve_pool(name, default, bank=None):
    """Return a custom bank override for a pool, else the built-in default."""
    if bank and isinstance(bank, dict) and name in bank:
        val = bank[name]
        if isinstance(val, list) and val:
            return val
        if isinstance(val, str) and val:
            return val
    return default


def build_jobs_multi(count=1, vibe=None, outfit_style=None, camera_style=None, lighting=None, time_of_day=None, bank=None):
    bank = bank or {}
    scenes_map = {
        "indoor": _resolve_pool("INDOOR_SCENES", INDOOR_SCENES, bank),
        "outdoor": _resolve_pool("OUTDOOR_SCENES", OUTDOOR_SCENES, bank),
        "mirror": _resolve_pool("MIRROR_SCENES", MIRROR_SCENES, bank),
    }
    framing_pool = _resolve_pool("FRAMING", FRAMING, bank)
    hair_pool = _resolve_pool("HAIR", HAIR, bank)
    pose_pool = _resolve_pool("POSES", POSES, bank)
    quality_pool = _resolve_pool("QUALITY", QUALITY, bank)
    tops_pools = _resolve_pool("OUTFIT_TOPS_POOLS", OUTFIT_TOPS_POOLS, bank)
    bottoms_pools = _resolve_pool("OUTFIT_BOTTOMS_POOLS", OUTFIT_BOTTOMS_POOLS, bank)
    lighting_pools = _resolve_pool("LIGHTING_POOLS", LIGHTING_POOLS, bank)
    default_negative = _resolve_pool("DEFAULT_NEGATIVE", DEFAULT_NEGATIVE, bank)
    mirror_negative = _resolve_pool("MIRROR_NEGATIVE", MIRROR_NEGATIVE, bank)

    if vibe == "outdoor":
        scene_pool = scenes_map["outdoor"]
    elif camera_style == "mirror":
        scene_pool = scenes_map["mirror"]
    else:
        scene_pool = scenes_map["indoor"]

    # Lighting pool selection
    if lighting in lighting_pools:
        light_pool = lighting_pools[lighting]
    else:
        light_pool = []
        for v in lighting_pools.values():
            light_pool.extend(v)

    # Outfit pool selection
    if outfit_style in tops_pools:
        top_pool = tops_pools[outfit_style]
        bottom_pool = bottoms_pools.get(outfit_style, [])
    else:
        top_pool = []
        for v in tops_pools.values():
            top_pool.extend(v)
        bottom_pool = []
        for v in bottoms_pools.values():
            bottom_pool.extend(v)

    jobs = []
    for _ in range(count):
        scene = random.choice(scene_pool)
        framing = random.choice(framing_pool)
        hair = random.choice(hair_pool)
        top = random.choice(top_pool)
        bottom = random.choice(bottom_pool)
        pose = random.choice(pose_pool)
        light = random.choice(light_pool)
        quality = random.choice(quality_pool)

        camera_mode = "mirror" if camera_style == "mirror" else "handheld"
        negative = mirror_negative if camera_mode == "mirror" else default_negative
        identity_lock = _resolve_pool("IDENTITY_LOCK", IDENTITY_LOCK, bank)
        prompt = _build_prompt(camera_mode, scene, framing, hair, top, bottom, pose, light, quality, time_of_day, identity_lock)

        short_id = hashlib.md5((str(len(jobs)) + str(time.time())).encode()).hexdigest()[:6]
        filename = f"{len(jobs)+1:03d}_{short_id}.png"

        jobs.append({
            "prompt": prompt,
            "filename": filename,
            "labels": f"{scene.split(',')[0]} · {pose}",
            "video_prompt": "auto",
            "negative_prompt": negative,
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

OVERRIDABLE_POOLS = (
    "INDOOR_SCENES",
    "MIRROR_SCENES",
    "OUTDOOR_SCENES",
    "FRAMING",
    "HAIR",
    "POSES",
    "QUALITY",
    "OUTFIT_TOPS_POOLS",
    "OUTFIT_BOTTOMS_POOLS",
    "LIGHTING_POOLS",
    "DEFAULT_NEGATIVE",
    "MIRROR_NEGATIVE",
    "IDENTITY_LOCK",
)


def get_builtin_pools() -> dict:
    """Return every overridable pool with its built-in default value."""
    return {
        "INDOOR_SCENES": INDOOR_SCENES,
        "MIRROR_SCENES": MIRROR_SCENES,
        "OUTDOOR_SCENES": OUTDOOR_SCENES,
        "FRAMING": FRAMING,
        "HAIR": HAIR,
        "POSES": POSES,
        "QUALITY": QUALITY,
        "OUTFIT_TOPS_POOLS": OUTFIT_TOPS_POOLS,
        "OUTFIT_BOTTOMS_POOLS": OUTFIT_BOTTOMS_POOLS,
        "LIGHTING_POOLS": LIGHTING_POOLS,
        "DEFAULT_NEGATIVE": DEFAULT_NEGATIVE,
        "MIRROR_NEGATIVE": MIRROR_NEGATIVE,
        "IDENTITY_LOCK": IDENTITY_LOCK,
    }


def list_presets():
    return {
        "vibes": ["indoor", "outdoor"],
        "camera_styles": ["handheld", "mirror"],
        "outfit_styles": ["sexy", "date_night", "night_club", "baggy", "lounge_sexy"],
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