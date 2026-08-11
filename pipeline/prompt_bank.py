"""
Prompt bank for Alina Sky photo generation.
v5 — handheld keeps phone OUT of frame ("no phone visible", working-example style),
concise dim/moody lighting + iPhone amateur quality, no quality-per-lighting pools.
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
    "standing casually in a dim bedroom near an open closet",
    "standing casually in a dim bathroom, background slightly cluttered",
    "standing in a dim living room, relaxed posture",
    "sitting or leaning near a closet in a dim bedroom",
    "standing near a wardrobe in a dim bedroom, clothes visible behind",
    "standing in a cluttered bathroom, products on the counter, towel on the floor",
    "standing in a lived-in living room, throw blankets and coffee cups on the table, cozy chaos",
    "standing near a doorway, shoes and coats visible, everyday real-life clutter",
    "sitting on the bedroom floor, laundry pile nearby, posters on the wall",
    "leaning on a kitchen counter, appliances and fridge magnets behind, everyday morning mess",
]

MIRROR_SCENES = [
    "standing at a bathroom mirror, tiled wall behind, phone covering part of the face",
    "standing in front of a full-length mirror in a dim bedroom",
    "standing near a wardrobe mirror, room dim behind",
    "standing at a bathroom mirror, sink cluttered, phone held up covering the face",
]

OUTDOOR_SCENES = [
    "standing in a dim alley with brick walls behind",
    "standing on a quiet city street under a streetlamp",
    "standing near a graffiti wall in a dim city corner",
    "standing on a rooftop with city lights blurred behind",
    "standing by a parked car on a dim street",
    "standing on a sidewalk with trash bins and parked bikes, dusk",
    "standing near a convenience store entrance, neon sign glow, evening",
    "standing at a bus stop with posters and litter, night street lamps",
    "standing on apartment stairs, graffiti and cigarette butts, dim",
    "standing near a chain-link fence, overgrown weeds, golden hour",
]

# ---------------------------------------------------------------------------
# FRAMING
# ---------------------------------------------------------------------------

FRAMING = [
    "mid-shot crop, waist-up framing",
]

# ---------------------------------------------------------------------------
# HAIR
# ---------------------------------------------------------------------------

HAIR = [
    "messy damp hair loosely tied, loose strands sticking to face and neck",
    "wet slicked-back hair, dripping strands sticking to temples and cheeks",
    "natural slightly messy air-dried hair, soft frizz and uneven strands framing the face",
    "damp loose braid with strands falling out around the face, slightly messy texture",
    "wet loose hair hanging straight, heavy strands clinging to face and collarbone",
    "damp half-up hairstyle with loose strands sticking flat to temples and neck",
    "wet side-parted hair clinging to one side of face and neck",
    "damp loose hair with strands falling across cheeks",
    "wet tousled hair sticking unevenly to neck and shoulders",
    "damp low bun with loose strands around face",
    "natural messy hair",
    "messy bedhead hair, strands sticking up randomly, flattened on one side from sleep",
    "loose low ponytail with face-framing pieces escaped, slightly greasy roots",
    "air-dried natural waves, frizzy ends, slightly uneven middle part, no product",
    "messy bun falling apart, loose strands around face and neck, just rolled out of bed",
]

# ---------------------------------------------------------------------------
# OUTFIT TOPS — category -> detailed alt/goth designs
# ---------------------------------------------------------------------------

OUTFIT_TOPS_POOLS = {
    "tank": [
        "black fitted micro tank ultra-thin distressed straps, faded gothic sigil print, soft matte cotton, raw hem",
        "black ribbed tank thin straps, subtle inverted cross stitch at chest, sheer mesh side panels, raw edges",
        "charcoal fitted tank deep scoop neck, thin straps, occult text running vertical spine, distressed collar",
        "black soft cotton tank dropped armholes, thin straps, large faded pentagram back print, loose threads hem",
        "dark grey fitted tank high neck racerback, subtle metallic thread sigil woven through rib, banded edges",
        "black micro tank ultra-cropped, spaghetti straps, distressed edges, faded band logo front/back",
        "off-white fitted tank sheer mesh yoke overlay, thin straps, black occult embroidery at neckline",
        "black fitted tank wide rib knit, thin straps, subtle bat-wing embroidery chest, raw hem unfinished",
        "charcoal tank thin straps, raw cut armholes, large faded baphomet silhouette center, soft worn cotton",
        "black fitted tank deep scoop back, thin straps criss-cross, inverted cross charm at nape, matte finish",
    ],
    "tube": [
        "black fitted tube top ribbed knit texture, banded top edge, slight stretch, clean silhouette",
        "white seamless tube top soft cotton modal, elasticized inner grip, minimal seams",
        "charcoal ribbed tube top wide band, subtle cable knit detail, fitted through torso",
        "black tube top smocked back panel, front smooth matte finish, elastic grip lining",
        "dark green fitted tube top fine rib, elastic hem, single seam side",
        "black tube top ruching center front, banded edges, stretch cotton blend",
        "cream fitted tube top subtle lace trim top edge, silicone grip, seamless body",
        "black fitted tube top cut-out side details, mesh insert panels, ribbed knit",
        "black tube top wide rib, elasticized inner band, subtle bat charm at center front",
        "charcoal tube top fitted, raw hem bottom, single seam, minimalist goth",
    ],
    "oversize_tee": [
        "oversized black graphic tee faded vintage band print, worn collar, boxy relaxed fit hanging off one shoulder",
        "loose charcoal crewneck sweatshirt wide ribbed neck, relaxed streetwear fit over longline camisole tank",
        "grey washed vintage concert tee layered under slouchy charcoal knit cardigan, oversized sleeves bunched at wrists",
        "black oversized band tee distressed neck, mineral wash, boxy fit, single chest pocket",
        "dark grey oversized tee faded occult print, raw collar, dropped shoulder, uneven hem",
        "black oversized long-sleeve tee wide sleeves, boxy fit, slightly cropped, distressed cuffs",
        "charcoal oversized sweatshirt raw neck, dropped shoulder, kangaroo pocket, mineral wash",
        "dark green oversized tee faded band logo, worn fabric, relaxed fit, raw hem",
        "black oversized tee cut-out shoulder details, mesh inserts, boxy silhouette",
        "grey vintage wash tee layered over black fitted tank, uneven hem, relaxed",
    ],
    "bralette": [
        "black lace bralette scalloped hem, adjustable straps, sheer unlined panels, subtle underband logo",
        "charcoal ribbed knit bralette square neck, wide straps, cropped, soft compressive fit",
        "black satin bralette thin straps, smooth drape, lace trim along neckline, adjustable back",
        "cream mesh bralette flocked velvet polka dots, thin straps, elastic underband",
        "black micro bralette triangle cups, thin criss-cross back straps, minimal coverage",
        "dark wine lace bralette high neck halter, keyhole back, scalloped edges",
        "black cotton bralette wide elastic band logo, racerback, ribbed texture",
        "black harness-style bralette multiple thin straps crossing chest, adjustable, hardware rings",
        "charcoal lace bralette longline band, sheer cups, strappy back, scalloped hem",
        "black velvet bralette square neck, wide straps, hook back, subtle shine",
    ],
    "bodysuit": [
        "black lace long-sleeve bodysuit strategic opaque panels, high neck, snap closure",
        "black cut-out bodysuit geometric waist cutouts, high neck, snap crotch, matte stretch",
        "charcoal ribbed knit bodysuit square neck, long sleeves, thong back, fitted silhouette",
        "black velvet bodysuit long sleeves, deep v-neck, snap closure, plush texture",
        "black mesh bodysuit lined bust, sheer sleeves, high neck, snap crotch",
        "dark green fitted bodysuit mock neck, long sleeves, subtle seam shaping, thong back",
        "black leather-look bodysuit zip front, stand collar, long sleeves, snap closure",
        "black sheer bodysuit flocked floral pattern, lined bust, long sleeves, high neck",
        "black bodysuit cut-out sides, mesh panels, high neck, snap crotch, strappy back",
        "charcoal bodysuit mock neck, long sleeves, subtle occult embroidery chest, thong back",
    ],
    "cardigan": [
        "cream knit crop cardigan open front, loose fit, wide ribbed cuffs, dropped shoulders",
        "black oversized cardigan chunky cable knit, open front, patch pockets, mid-thigh length",
        "charcoal fine merino cardigan deep v-neck, single button, fitted sleeves, cropped hem",
        "black sheer cardigan floral burnout pattern, open front, raw edges, draped",
        "dark grey cardigan oversized, raw hem, wide sleeves, dropped shoulder, distressed",
        "black cardigan deconstructed, asymmetrical hem, raw edges, single button, draped",
        "charcoal cardigan chunky knit, open front, single pocket, mineral wash, relaxed",
        "black cardigan mesh panel sides, open front, wide sleeves, raw hem, oversized",
        "dark green cardigan fine knit, deep v-neck, single button, cropped, subtle texture",
        "black cardigan burnout velvet pattern, open front, raw edges, mid-thigh length",
    ],
    "hoodie": [
        "black tech windbreaker vest over fitted torso top, visible crossbody bag strap, urban practical layering",
        "black oversized hoodie dropped shoulders, raw hem, kangaroo pocket, mineral wash",
        "black cropped hoodie raw hem, wide drawstrings, dropped shoulder, fleece back",
        "charcoal oversized hoodie distressed graphic print, worn fabric, kangaroo pocket",
        "black hoodie thumbhole cuffs, oversized, single front pocket, mineral wash",
        "dark green hoodie oversized, embroidered chest logo, raw hem, dropped shoulder",
        "black hoodie cut-out shoulder details, mesh inserts, oversized, raw hem",
        "charcoal oversized hoodie wide drawstrings, distressed cuffs, kangaroo pocket, mineral wash",
        "black hoodie asymmetrical zip, dropped shoulder, raw hem, oversized fit",
        "dark grey hoodie oversized, burnout pattern sleeves, kangaroo pocket, raw edges",
    ],
    "blazer": [
        "off-white relaxed fit soft blazer layered over black camisole, visible silk texture at neckline",
        "black structured blazer oversized, peak lapels, single button, padded shoulders",
        "charcoal tweed blazer relaxed fit, notch lapels, patch pockets, subtle texture",
        "black velvet blazer cropped, shawl lapel, single button, smooth drape",
        "dark grey unstructured blazer linen blend, relaxed, patch pockets, rolled sleeves",
        "black blazer deconstructed, raw edges, asymmetrical closure, oversized fit",
        "cream lightweight blazer open front, no lapels, long sleeves, fluid drape",
        "black blazer mesh inset panels at sides, oversized, notch lapels, single button",
        "charcoal blazer oversized, raw edges, single button, dropped shoulder, deconstructed",
        "black velvet blazer cropped, shawl lapel, single button, subtle crushed texture",
    ],
}

# ---------------------------------------------------------------------------
# OUTFIT BOTTOMS — category -> detailed designs
# ---------------------------------------------------------------------------

OUTFIT_BOTTOMS_POOLS = {
    "miniskirt": [
        "black leather mini skirt asymmetrical zip hem, low-rise fit, structured waistband",
        "black high-waisted vinyl shorts side zip, structured waistband, subtle sheen",
        "black mini skirt patent leather straight silhouette, high waist, hidden back zip",
        "black pleated mini skirt tennis-inspired, hidden shorts liner, contrast piping",
        "dark charcoal mini skirt faux leather, exposed zip front, high waist, slight flare",
        "black sequin mini skirt high waist, short length, lined, subtle shimmer",
        "black mini skirt in structured wool blend, box pleats, high waist, clean lines",
        "black cut-out mini skirt side zip, high-waisted, structured fit, hardware detail",
        "black leather mini skirt raw hem, low-rise, D-ring belt loops, asymmetrical",
        "charcoal mini skirt vinyl, high waist, side zip, subtle flare, structured",
    ],
    "cargo_pants": [
        "black wide-leg cargo pants oversized flap pockets, stacked and pooling slightly over shoes",
        "black cargo pants slim tapered, multiple flap pockets, adjustable ankle straps, matte finish",
        "charcoal cargo pants relaxed fit, oversized side pockets with button flaps, stacked hem",
        "black cargo pants high waist, D-ring details, utility loops, straight leg, raw hem",
        "dark green cargo pants wide leg, oversized pockets, drawstring waist, gathered ankles",
        "black tech cargo pants water-repellent, zip pockets, tapered leg, nylon sheen",
        "charcoal cargo pants slim, magnetic snap flaps, clean lines, cropped ankle",
        "black cargo pants distressed knee panels, flap pockets, relaxed fit, stacked hem",
        "dark grey cargo pants oversized, multiple zip pockets, elastic waist, tapered",
        "black cargo pants utility straps, oversized pockets, gathered ankles, matte cotton",
    ],
    "sweatpants": [
        "black oversized joggers elastic waist, dropped crotch, cuffed ankles, brushed fleece",
        "grey sweatpants ribbed ankle cuffs, relaxed fit, side pockets, faded wash",
        "black baggy basketball shorts double-layered over sheer compression tights, hitting mid inner knee",
        "black cargo joggers oversized pockets, drawstring waist, baggy leg, raw hem",
        "charcoal sweatpants high waist, wide elastic band, straight leg, subtle logo embroidery",
        "black tech windbreaker pants over fitted leggings, visible crossbody bag strap, urban layering",
        "dark grey joggers tapered leg, zip ankles, elastic waist, minimal seams",
        "black sweatpants distressed knee details, relaxed fit, raw hem, mineral wash",
        "charcoal joggers oversized, raw hem, wide cuffs, dropped crotch, fleece back",
        "black sweatpants cut-out knee mesh panels, elastic waist, tapered leg, raw hem",
    ],
    "pajama_shorts": [
        "pale pink silk pajama shorts hello kitty embroidery, contrast white piping, elastic waist, mid-thigh",
        "baby blue satin shorts sanrio characters print, lace trim hem, drawstring waist",
        "lavender cotton shorts cute ghost/bats print, ruffled hem, relaxed fit",
        "cream silk shorts lace trim, small bow detail front, elastic waist, smooth drape",
        "soft pink modal shorts heart lace trim, scalloped hem, high waist, ultra-soft",
        "mint green satin shorts cherry embroidery, contrast piping, relaxed fit",
        "white cotton shorts pastel rainbow stitching, ruffled edges, elastic waist",
        "pale yellow silk shorts tiny strawberry print, lace hem, drawstring, mid-thigh",
        "baby pink satin shorts bunny embroidery, lace trim, elastic waist, mid-thigh",
        "lavender modal shorts moon/stars print, scalloped hem, drawstring, relaxed",
    ],
    "leggings": [
        "black high-waisted biker shorts ruched side seams, tight fit, compressive, mid-thigh",
        "black fitted leggings high waist, seamless construction, matte finish, ankle length",
        "charcoal ribbed leggings high waist, 7/8 length, compressive, subtle texture",
        "black leather-look leggings high waist, four-way stretch, ankle length, subtle sheen",
        "dark green compressive leggings high waist, mesh side panels, 7/8 length",
        "black leggings high waist, ruched back seam, silicone grip hem, ankle length",
        "charcoal leggings high waist, wide waistband, subtle rib texture, compressive",
        "black mesh-panel leggings high waist, sheer calf inserts, compressive, ankle length",
        "black leggings high waist, cut-out knee details, mesh backing, compressive",
        "dark grey leggings high waist, subtle occult print side, compressive, 7/8 length",
    ],
    "denim_shorts": [
        "black high-waisted distressed denim shorts raw hem, classic five-pocket, slight whiskering",
        "dark wash denim shorts high waist, clean hem, slight distressing at pockets",
        "black denim shorts panelled construction, asymmetrical hem, high waist, hardware",
        "light wash denim shorts oversized leg opening, slouchy fit, rolled hem",
        "black denim shorts zip front, high waist, structured, minimal distressing",
        "charcoal denim shorts raw hem, high waist, subtle whiskering, relaxed fit",
        "black denim shorts distressed thigh, raw hem, high waist, five-pocket",
        "dark blue denim shorts high waist, rolled hem, relaxed fit, subtle fading",
        "black denim shorts cut-out sides, raw hem, high waist, hardware details",
        "charcoal denim shorts panelled, raw hem, high waist, subtle distressing",
    ],
    "midi_skirt": [
        "black fitted midi skirt thigh-high slit, hidden side zip, structured waistband",
        "black satin midi skirt smooth drape, elastic waist, high slit, bias cut",
        "black high-waisted pleated midi skirt structured wool blend, clean lines, side zip",
        "black leather midi skirt asymmetrical hem, high waist, concealed zip, structured",
        "dark charcoal midi skirt knife pleats, high waist, side zip, swing silhouette",
        "black velvet midi skirt high waist, subtle flare, hidden zip, plush texture",
        "black midi skirt wrap-style, tie waist, high slit, fluid drape",
        "charcoal midi skirt paneled construction, high waist, side zip, architectural seams",
        "black midi skirt leather, high slit front, asymmetrical hem, structured waist",
        "charcoal midi skirt pleated, high waist, side zip, swing movement",
    ],
    "biker_shorts": [
        "black high-waisted biker shorts ruched side seams, tight fit, compressive, mid-thigh",
        "black biker shorts high waist, wide elastic band, silicone grip hem, 7-inch inseam",
        "charcoal biker shorts high waist, contrast stitching, compressive, reflective logo",
        "black leather-look biker shorts high waist, zip pockets, structured, mid-thigh",
        "dark green biker shorts high waist, mesh side panels, compressive, 8-inch inseam",
        "black biker shorts high waist, ruched back seam, silicone grip, matte finish",
        "charcoal biker shorts high waist, wide waistband, subtle rib texture, compressive",
        "black biker shorts high waist, cut-out side panels, mesh inserts, compressive",
        "black biker shorts high waist, reflective piping, silicone grip, 7-inch inseam",
        "charcoal biker shorts high waist, ruched sides, wide band, compressive, matte",
    ],
}


# ---------------------------------------------------------------------------
# POSES — subtle torso/weight only, phone stays out of frame, no arm-in-frame
# ---------------------------------------------------------------------------

POSES = [
    "subtle torso angle, candid and unposed",
    "relaxed posture, torso angled slightly away",
    "natural fit-check posture, slight hip shift, relaxed stance",
    "slight weight shift, comfortable relaxed posture",
    "subtle weight shift, confident relaxed stance",
    "slight body angle shift, natural hip position",
    "relaxed stance, weight shifted to one side",
    "subtle hip tilt, comfortable mid-frame posture",
    "soft angle turn of torso, shoulders naturally uneven, casual",
    "slight lean forward, weight on one foot, candid pause mid-movement",
    "one hand resting lightly on the hip, soft shoulder tilt, natural",
    "fingertips resting near collarbone, chin slightly lowered, quiet gaze",
    "hand grazing through hair at the temple, slight head tilt, relaxed",
    "natural body weight rest, shoulders tilted slightly off-center, comfortable pause",
    "slight shift in stance with one foot forward, relaxed fit position",
]

# ---------------------------------------------------------------------------
# HANDHELD_POSES — candid handheld-selfie angles/gestures only (mirror uses POSES)
# ---------------------------------------------------------------------------

HANDHELD_POSES = [
    "chin tucked toward collarbone, gaze lifted to meet lens at slight downward angle, head tilted 15 degrees right creating natural jawline shadow, shoulders relaxed and uneven",
    "camera held at sternum height angled upward, eyes tracking just left of center as if noticing something beyond frame, weight shifted onto back leg with front knee softly bent",
    "device at jawline distance, extreme close framing cutting top of forehead, head canted right exposing neck line, lower lip caught between teeth, free hand hovering near collarbone",
    "gaze directed downward toward palm as if reading screen reflection, brow arched inquisitively, chin slightly lowered creating double-chin compression, posture upright but not stiff",
    "body captured mid-step, weight fully on trailing leg with leading foot lifted, camera at hip angled up 45 degrees, torso rotated toward leading side creating dynamic diagonal line",
    "thumb grazing lower frame edge creating organic vignette, chin dropped toward chest, eyes tilted upward beneath lashes at extreme angle, neck elongated, shoulders rolled forward",
    "torso rotated 60 degrees away from lens, head swiveled 120 degrees back over left shoulder creating spinal twist, gaze sharp over collarbone, free arm hanging loose at side",
    "device resting on clavicle pointing nearly vertical, chin pressed to chest forcing eyes upward through lowered lashes, forehead dominating upper frame, intimate vulnerable perspective",
    "right hand mid-motion tucking loose strands behind ear, elbow lifted to shoulder height, head tilted toward working hand exposing jawline, left shoulder dropped in counterbalance",
    "face angled 30 degrees toward floor, eyes tracking invisible screen held at waist, jaw relaxed with slight parting, neck extended forward in tech-neck curve, shoulders rounded inward",
]

# ---------------------------------------------------------------------------
# LIGHTING
# ---------------------------------------------------------------------------

LIGHTING_POOLS = {
    "warm": [
        "subtle warm dim indoor lighting, soft shadows, deep blacks, moody atmosphere, slight yellow/orange warmth",
        "dim warm lamp light, soft shadows, moody warm tones, imperfect exposure",
        "dim warm indoor lighting, soft shadows, deep blacks, slight amber warmth, moody",
    ],
    "cool": [
        "cool soft window light, pale blue-white wash, delicate shadows across features",
        "cool daylight bouncing off white walls, crisp clean tones, airy atmosphere",
        "overcast cool ambient light, soft blue-grey shadow across one side of face",
    ],
    "dimlit": [
        "very dim low light, deep shadows swallowing edges, barely lit, moody darkness",
        "single dim bulb overhead casting long shadows downward across features",
        "dim ambient light, deep shadows, intimate gloom, imperfect exposure",
    ],
    "flash": [
        "harsh direct on-camera flash, blown highlights on forehead and nose, sharp falloff into darkness, authentic amateur night photo",
        "direct phone flash straight on, overexposed forehead and cheekbones, hard shadow under chin, raw unedited night selfie",
        "built-in phone flash, cool white blast, shiny nose highlight, dark background, authentic low-light phone photo",
    ],
    "screen": [
        "illuminated only by phone screen glow, cool blue light on face, deep surrounding darkness, intimate night atmosphere",
        "face lit by phone display, cyan-blue cast, dramatic soft shadows, pitch black room, raw amateur night shot",
        "phone screen glow as the only light source, cool cast on face, high contrast, unposed night capture",
    ],
    "mixed": [
        "mixed warm lamp and cool window light, conflicting color temperatures, skin tones split warm and cool, messy real-world lighting",
        "warm bedside lamp plus cool phone screen glow, dual color cast, competing shadows, uneven lighting",
        "dim neon or street glow mixing with indoor lamp, color contamination, urban night mood",
    ],
}

# ---------------------------------------------------------------------------
# QUALITY
# ---------------------------------------------------------------------------

QUALITY = [
    "imperfect composition, shaky handheld iPhone 15 Pro Max feel, natural skin texture, authentic amateur snapchat-style photo, subtle film grain, slight oversharpening, non-AI aesthetic, photorealistic, hyperrealistic"
]

# ---------------------------------------------------------------------------
# NEGATIVES
# ---------------------------------------------------------------------------

DEFAULT_NEGATIVE = (
    "phone visible, mirror selfie, lamp visible, smiling, overly posed, studio lighting, "
    "symmetry, CGI skin, unrealistic texture, accessories, jewelry, necklaces, earrings, cleavage"
)

MIRROR_NEGATIVE = (
    "lamp visible, smiling, overly posed, studio lighting, symmetry, CGI skin, "
    "unrealistic texture, accessories, jewelry, necklaces, earrings, cleavage"
)

# ---------------------------------------------------------------------------
# IDENTITY LOCK
# ---------------------------------------------------------------------------

IDENTITY_LOCK = "keep model identity, choker, hair, lips color consistent/accurate/similar"

# ---------------------------------------------------------------------------
# BUILD PROMPT
# ---------------------------------------------------------------------------

def _build_prompt(camera_mode, scene, framing, hair, top, bottom, pose, lighting, quality, time_of_day=None, identity_lock=None):
    if camera_mode == "mirror":
        negative = MIRROR_NEGATIVE
        parts = [
            "Front-facing mirror selfie",
            "vertical 9:16",
            "black iPhone visible in hand",
        ]
    else:
        negative = DEFAULT_NEGATIVE
        parts = [
            "Front-facing handheld selfie, vertical 9:16, no phone visible",
        ]

    parts += [
        scene,
        framing,
        hair,
        top,
        bottom,
        "candid and unposed",
        pose,
        "neutral expression, not smiling",
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


def build_jobs_multi(count=1, vibe=None, top_category=None, bottom_category=None, camera_style=None, lighting=None, time_of_day=None, bank=None):
    bank = bank or {}
    scenes_map = {
        "indoor": _resolve_pool("INDOOR_SCENES", INDOOR_SCENES, bank),
        "outdoor": _resolve_pool("OUTDOOR_SCENES", OUTDOOR_SCENES, bank),
        "mirror": _resolve_pool("MIRROR_SCENES", MIRROR_SCENES, bank),
    }
    framing_pool = _resolve_pool("FRAMING", FRAMING, bank)
    hair_pool = _resolve_pool("HAIR", HAIR, bank)
    handheld_pose_pool = _resolve_pool("HANDHELD_POSES", HANDHELD_POSES, bank)
    mirror_pose_pool = _resolve_pool("POSES", POSES, bank)
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
    if top_category in tops_pools:
        top_pool = tops_pools[top_category]
    else:
        top_pool = []
        for v in tops_pools.values():
            top_pool.extend(v)
    if bottom_category in bottoms_pools:
        bottom_pool = bottoms_pools[bottom_category]
    else:
        bottom_pool = []
        for v in bottoms_pools.values():
            bottom_pool.extend(v)

    camera_mode = "mirror" if camera_style == "mirror" else "handheld"
    pose_pool = mirror_pose_pool if camera_mode == "mirror" else handheld_pose_pool

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

        # flash/screen lighting implies night — avoid "natural daylight" conflict
        if lighting in ("flash", "screen") and time_of_day == "day":
            time_of_day = "night"

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
    "HANDHELD_POSES",
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
        "HANDHELD_POSES": HANDHELD_POSES,
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
        "top_categories": list(OUTFIT_TOPS_POOLS.keys()),
        "bottom_categories": list(OUTFIT_BOTTOMS_POOLS.keys()),
        "lighting": ["warm", "cool", "dimlit", "flash", "screen", "mixed"],
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