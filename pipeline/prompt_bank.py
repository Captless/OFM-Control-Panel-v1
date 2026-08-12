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
    "in a dim bedroom near an open closet",
    "in a dim bathroom, background slightly cluttered",
    "in a dim living room, relaxed posture",
    "near a closet in a dim bedroom",
    "near a wardrobe in a dim bedroom, clothes visible behind",
    "in a cluttered bathroom, products on the counter, towel on the floor",
    "in a lived-in living room, throw blankets and coffee cups on the table, cozy chaos",
    "near a doorway, shoes and coats visible, everyday real-life clutter",
    "on the bedroom floor, laundry pile nearby, posters on the wall",
    "on a kitchen counter, appliances and fridge magnets behind, everyday morning mess",
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
    "mid shot level",
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
        "black fitted micro tank ultra-thin distressed straps, faded inverted cross sigil screen-print center chest, soft matte cotton, raw hem unfinished",
        "black ribbed tank thin straps, subtle bat-wing embroidery at sternum, sheer mesh side panels with burnt-edge detail, raw collar edges",
        "charcoal fitted tank deep scoop neck, thin straps, occult alchemical text running vertical spine in metallic silver thread, distressed banding",
        "black soft cotton tank dropped armholes, thin straps, large faded baphomet silhouette back print, loose threads at hem and armholes",
        "dark grey fitted tank high neck racerback, subtle metallic sigil woven through rib knit, banded edges with micro-fray",
        "black micro tank ultra-cropped, spaghetti straps, distressed edges throughout, faded occult band logo front and back, raw hem",
        "off-white fitted tank sheer black mesh yoke overlay, thin straps, black occult embroidery at neckline and strap anchors, raw edges",
        "black fitted tank wide rib knit, thin straps, subtle inverted pentagram embroidery at chest, raw hem unfinished with pulled threads",
        "charcoal tank thin straps, raw cut armholes, large faded baphomet silhouette center chest, soft worn cotton with mineral wash",
        "black fitted tank deep scoop back, thin straps criss-cross at spine, inverted cross charm at nape on delicate chain, matte finish",
    ],
    "tube": [
        "black fitted tube top ribbed knit, banded top edge with hidden O-ring at center front, slight stretch, clean silhouette",
        "white seamless tube top soft cotton modal, elasticized inner grip, minimal seams, subtle moon-phase embroidery at hem",
        "charcoal ribbed tube top wide band, subtle cable knit detail, fitted through torso, raw cut bottom edge",
        "black tube top smocked back panel, front smooth matte finish, elastic grip lining, single silver grommet at side",
        "dark green fitted tube top fine rib, elastic hem, single seam side, occult sigil burn-print at hip",
        "black tube top ruching center front, banded edges, stretch cotton blend, delicate chain strap anchors at shoulders",
        "cream fitted tube top subtle lace trim top edge with metallic thread, silicone grip, seamless body, raw hem",
        "black fitted tube top strategic cut-out side details, mesh insert panels, ribbed knit, O-ring hardware at cutouts",
        "black tube top wide rib, elasticized inner band, subtle bat charm at center front on jump ring, raw edges",
        "charcoal tube top fitted, raw hem bottom, single seam, minimalist goth with distressed neckline",
    ],
    "oversize_tee": [
        "oversized black graphic tee faded vintage occult band print, worn collar, boxy relaxed fit hanging off one shoulder, mineral wash",
        "loose charcoal crewneck sweatshirt wide ribbed neck, relaxed streetwear fit over longline camisole tank, distressed cuffs",
        "grey washed vintage concert tee layered under slouchy charcoal knit cardigan, oversized sleeves bunched at wrists, raw hems",
        "black oversized band tee distressed neck, mineral wash, boxy fit, single chest pocket with raw edge, occult back print",
        "dark grey oversized tee faded alchemical symbol print, raw collar, dropped shoulder, uneven hem with loose threads",
        "black oversized long-sleeve tee wide sleeves, boxy fit, slightly cropped, distressed cuffs, inverted cross at nape",
        "charcoal oversized sweatshirt raw neck, dropped shoulder, kangaroo pocket, mineral wash, subtle sigil embroidery pocket",
        "dark green oversized tee faded band logo, worn fabric, relaxed fit, raw hem, mesh panel insert at side seam",
        "black oversized tee strategic cut-out shoulder details, black mesh inserts, boxy silhouette, raw edges throughout",
        "grey vintage wash tee layered over black fitted tank, uneven hem, relaxed, occult text peeking at collar",
    ],
    "bralette": [
        "black lace harness bralette scalloped hem, multiple thin adjustable straps crossing chest with silver O-rings, sheer unlined cups, underband logo burn-print",
        "charcoal ribbed knit bralette square neck, wide straps with metal slider hardware, cropped, soft compressive fit, inverted cross embroidery at center",
        "black satin bralette thin straps, smooth drape, lace trim along neckline with metallic thread sigils, adjustable back with hook-and-eye",
        "cream mesh bralette flocked velvet inverted crosses, thin straps with delicate chain detail, elastic underband with silver grommets",
        "black micro triangle bralette minimal coverage, thin criss-cross back straps terminating in O-rings, adjustable, raw edges",
        "dark wine lace bralette high neck halter, keyhole back with strappy lace-up detail, scalloped edges, velvet burnout moon phases",
        "black cotton bralette wide elastic band with occult text, racerback with strappy cage detail, ribbed texture, metal hardware",
        "black cage-style bralette multiple thin straps crossing chest and torso in geometric pattern, adjustable at all points, hardware rings throughout",
        "charcoal lace bralette longline band, sheer cups with strategic opaque panels, strappy back with criss-cross chains, scalloped hem",
        "black crushed velvet bralette square neck, wide straps with burnished metal slides, hook back, subtle occult shine pattern",
    ],
    "bodysuit": [
        "black lace long-sleeve bodysuit strategic opaque panels with sigil embroidery, high neck with O-ring detail, snap closure",
        "black cut-out bodysuit geometric waist cutouts bound with black bias tape, high neck, snap crotch, matte stretch, metal grommets at cutouts",
        "charcoal ribbed knit bodysuit square neck, long sleeves, thong back, fitted silhouette, inverted cross burn-print at chest",
        "black velvet bodysuit long sleeves, deep v-neck with lace-up detail, snap closure, plush texture with crushed finish",
        "black mesh bodysuit lined bust with occult embroidery, sheer sleeves, high neck, snap crotch, strategic opaque panels",
        "dark green fitted bodysuit mock neck, long sleeves, subtle alchemical seam shaping, thong back, raw edges",
        "black leather-look bodysuit zip front with oversized pull, stand collar, long sleeves, snap closure, boned structure",
        "black sheer bodysuit flocked velvet bat-wing pattern, lined bust, long sleeves, high neck, raw hem",
        "black bodysuit cut-out sides with strappy lace-up detail, mesh panels, high neck, snap crotch, strappy harness back",
        "charcoal bodysuit mock neck, long sleeves, subtle occult embroidery across chest and sleeves, thong back, raw edges",
    ],
    "cardigan": [
        "cream knit crop cardigan open front, loose fit, wide ribbed cuffs, dropped shoulders, raw hem with pulled threads",
        "black oversized cardigan chunky cable knit with occult motif cables, open front, patch pockets with raw edges, mid-thigh length",
        "charcoal fine merino cardigan deep v-neck, single horn button, fitted sleeves, cropped hem, subtle sigil embroidery at hem",
        "black sheer cardigan floral burnout velvet pattern with moon phases, open front, raw edges throughout, draped silhouette",
        "dark grey cardigan oversized, raw hem, wide sleeves, dropped shoulder, distressed throughout, mineral wash",
        "black cardigan deconstructed, raw edges, draped front panels uneven length, single horn button, distressed collar",
        "charcoal cardigan chunky knit, open front, single patch pocket with raw edge, mineral wash, relaxed, loose threads",
        "black cardigan mesh panel sides with burnt edges, open front, wide sleeves, raw hem, oversized, distressed cuffs",
        "dark green cardigan fine knit, deep v-neck, single button, cropped, subtle texture with occult thread catch",
        "black cardigan burnout velvet pattern with sigils, open front, raw edges throughout, mid-thigh length, draped",
    ],
    "hoodie": [
        "black tech windbreaker vest over fitted torso top, visible crossbody bag strap, urban practical layering, raw edges",
        "black oversized hoodie dropped shoulders, raw hem, kangaroo pocket, mineral wash, inverted cross embroidery at pocket",
        "black cropped hoodie raw hem, wide drawstrings with metal tips, dropped shoulder, fleece back, faded occult print",
        "charcoal oversized hoodie distressed occult graphic print, worn fabric, kangaroo pocket, raw cuffs and hem",
        "black hoodie thumbhole cuffs, oversized, single front pocket, mineral wash, subtle sigil embroidery at sleeve",
        "dark green hoodie oversized, embroidered chest logo with alchemical symbols, raw hem, dropped shoulder",
        "black hoodie strategic cut-out shoulder details, black mesh inserts, oversized, raw hem, raw edges at cutouts",
        "charcoal oversized hoodie wide drawstrings, distressed cuffs and hem, kangaroo pocket, mineral wash, raw neckline",
        "black hoodie deconstructed zip, dropped shoulder, raw hem, oversized fit, raw edges",
        "dark grey hoodie oversized, burnout velvet pattern sleeves with occult motifs, kangaroo pocket, raw edges throughout",
    ],
    "blazer": [
        "off-white relaxed fit soft blazer layered over black camisole, visible silk texture at neckline, raw edges",
        "black structured blazer oversized, peak lapels, single horn button, padded shoulders, subtle sigil embroidery lapel",
        "charcoal tweed blazer relaxed fit, notch lapels, patch pockets with raw edges, subtle texture with metallic thread",
        "black velvet blazer cropped, shawl lapel, single button, smooth drape with crushed finish, raw hem",
        "dark grey unstructured blazer linen blend, relaxed, patch pockets, rolled sleeves, raw edges, distressed collar",
        "black blazer deconstructed, raw edges throughout, single horn button, oversized fit, draping front panels",
        "cream lightweight blazer open front, no lapels, long sleeves, fluid drape, raw hem and cuffs",
        "black blazer mesh inset panels at sides with burnt edges, oversized, notch lapels, single button, raw edges",
        "charcoal blazer oversized, raw edges, single button, dropped shoulder, deconstructed collar, loose threads",
        "black crushed velvet blazer cropped, shawl lapel, single button, subtle occult texture, raw hem and cuffs",
    ],
}

# ---------------------------------------------------------------------------
# OUTFIT BOTTOMS — category -> detailed designs
# ---------------------------------------------------------------------------

OUTFIT_BOTTOMS_POOLS = {
    "miniskirt": [
        "black leather mini skirt zipped hem bound in black bias tape, low-rise fit, structured waistband with D-ring belt loops",
        "black high-waisted vinyl shorts side zip with oversized pull, structured waistband, subtle sheen, raw cut hem",
        "black mini skirt patent leather straight silhouette, high waist, hidden back zip, inverted cross burn-print at hem",
        "black pleated mini skirt tennis-inspired, hidden shorts liner, contrast piping with occult sigil embroidery",
        "dark charcoal mini skirt faux leather, exposed zip front with metal grommets, high waist, slight flare",
        "black sequin mini skirt high waist, short length, lined, subtle inverted pentagram shimmer pattern",
        "black mini skirt structured wool blend, box pleats with raw edges, high waist, clean lines, distressed hem",
        "black cut-out mini skirt side zip with strappy lace-up detail, high-waisted, structured fit, O-ring hardware",
        "black leather mini skirt raw hem distressed, low-rise, D-ring belt loops, occult embroidery at waistband",
        "charcoal mini skirt vinyl, high waist, side zip, subtle flare, structured, moon-phase burn-print at hip",
    ],
    "cargo_pants": [
        "black wide-leg cargo pants oversized flap pockets with metal snap closures, stacked and pooling over shoes, occult embroidery at pocket flaps",
        "black cargo pants slim tapered, multiple flap pockets with D-ring utility loops, adjustable ankle straps with buckles, matte finish",
        "charcoal cargo pants relaxed fit, oversized side pockets button flaps with silver hardware, stacked hem raw edges",
        "black cargo pants high waist, D-ring details at hips, utility loops with chain accents, straight leg, raw hem distressed",
        "dark green cargo pants wide leg, oversized pockets with magnetic snaps, drawstring waist metal tips, gathered ankles",
        "black tech cargo pants water-repellent nylon, zip pockets with leather pulls, tapered leg, inverted cross reflective piping",
        "charcoal cargo pants slim, magnetic snap flaps with occult sigil deboss, clean lines, cropped ankle raw hem",
        "black cargo pants distressed knee panels with mesh backing, flap pockets, relaxed fit, stacked hem loose threads",
        "dark grey cargo pants oversized, multiple zip pockets with oversized pulls, elastic waist, tapered, raw edges",
        "black cargo pants utility straps crossing thighs with O-rings, oversized pockets, gathered ankles, matte cotton",
    ],
    "sweatpants": [
        "black oversized joggers elastic waist with internal drawstring metal tips, dropped crotch, cuffed ankles, brushed fleece, occult embroidery at hip",
        "grey sweatpants ribbed ankle cuffs, relaxed fit, side pockets with hidden zips, faded mineral wash, subtle sigil print at calf",
        "black baggy basketball shorts double-layered over sheer compression tights with occult mesh pattern, hitting mid inner knee, raw hem",
        "black cargo joggers oversized pockets with flap snaps, drawstring waist, baggy leg, raw hem, inverted cross burn-print",
        "charcoal sweatpants high waist, wide elastic band with metal grommets, straight leg, subtle alchemical embroidery at pocket",
        "black tech windbreaker pants over fitted leggings, visible crossbody bag strap, urban layering, raw hem, reflective occult piping",
        "dark grey joggers tapered leg, zip ankles with leather pulls, elastic waist, minimal seams, moon-phase print at thigh",
        "black sweatpants distressed knee details with mesh inserts, relaxed fit, raw hem, mineral wash, loose threads throughout",
        "charcoal joggers oversized, raw hem, wide cuffs with snap buttons, dropped crotch, fleece back, distressed neckline",
        "black sweatpants cut-out knee mesh panels with harness strapping, elastic waist, tapered leg, raw hem, metal rings",
    ],
    "pajama_shorts": [
        "pale pink silk pajama shorts hello kitty embroidery with inverted cross detail, contrast white piping, elastic waist, mid-thigh",
        "baby blue satin shorts sanrio characters print with subtle bat wings, lace trim hem, drawstring waist with metal tips",
        "lavender cotton shorts cute ghost/bats print with occult symbols, ruffled hem, relaxed fit, raw edges",
        "cream silk shorts lace trim with metallic thread sigils, small bow detail front, elastic waist, smooth drape",
        "soft pink modal shorts heart lace trim with inverted cross cutouts, scalloped hem, high waist, ultra-soft",
        "mint green satin shorts cherry embroidery with skull detail, contrast piping, relaxed fit, raw hem",
        "white cotton shorts pastel rainbow stitching with sigil accents, ruffled edges, elastic waist, distressed hem",
        "pale yellow silk shorts tiny strawberry print with bat motifs, lace hem, drawstring, mid-thigh, raw edges",
        "baby pink satin shorts bunny embroidery with moon phases, lace trim, elastic waist, mid-thigh, subtle sheen",
        "lavender modal shorts moon/stars print with alchemical symbols, scalloped hem, drawstring, relaxed, raw edges",
    ],
    "leggings": [
        "black high-waisted biker shorts ruched side seams with metal grommets, tight fit, compressive, mid-thigh, occult embroidery at hem",
        "black fitted leggings high waist, seamless construction, matte finish, ankle length, subtle inverted cross texture at calf",
        "charcoal ribbed leggings high waist, 7/8 length, compressive, subtle texture with sigil burn-print at hip",
        "black leather-look leggings high waist, four-way stretch, ankle length, subtle sheen, boned side seams",
        "dark green compressive leggings high waist, mesh side panels with flocked velvet bats, 7/8 length, raw hem",
        "black leggings high waist, ruched back seam with chain detail, silicone grip hem, ankle length, O-ring at waist",
        "charcoal leggings high waist, wide waistband with metal hardware, subtle rib texture, compressive, raw hem",
        "black mesh-panel leggings high waist, sheer calf inserts with occult embroidery, compressive, ankle length",
        "black leggings high waist, cut-out knee details with strappy lace-up mesh backing, compressive, raw edges",
        "dark grey leggings high waist, subtle occult print side panel, compressive, 7/8 length, distressed hem",
    ],
    "denim_shorts": [
        "black high-waisted distressed denim shorts raw hem, classic five-pocket, slight whiskering, inverted cross embroidery at pocket",
        "dark wash denim shorts high waist, clean hem, slight distressing at pockets, occult sigil rivets at coin pocket",
        "black denim shorts panelled construction, raw hem with loose threads, high waist, hardware D-rings at hips",
        "light wash denim shorts oversized leg opening, slouchy fit, rolled hem, faded occult print at thigh",
        "black denim shorts zip front with oversized pull, high waist, structured, minimal distressing, moon-phase burn-print",
        "charcoal denim shorts raw hem, high waist, subtle whiskering, relaxed fit, inverted cross embroidery at hem",
        "black denim shorts distressed thigh with mesh backing, raw hem, high waist, five-pocket, loose threads",
        "dark blue denim shorts high waist, rolled hem, relaxed fit, subtle fading, alchemical symbol embroidery at pocket",
        "black denim shorts cut-out sides with strappy harness detail, raw hem, high waist, O-ring hardware at cutouts",
        "charcoal denim shorts panelled with raw edges, high waist, subtle distressing, occult thread catch at seams",
    ],
    "midi_skirt": [
        "black fitted midi skirt thigh-high slit with metal zipper guard, hidden side zip, structured waistband, raw hem",
        "black satin midi skirt smooth drape with crushed texture, elastic waist with metal grommets, high slit, bias cut",
        "black high-waisted pleated midi skirt structured wool blend, clean lines, side zip, occult embroidery at pleat edges",
        "black leather midi skirt raw hem with loose threads, high waist, concealed zip, structured, distressed throughout",
        "dark charcoal midi skirt knife pleats with raw edges, high waist, side zip, swing silhouette, sigil burn-print",
        "black velvet midi skirt high waist, subtle flare, hidden zip, plush texture crushed finish, occult shine pattern",
        "black midi skirt wrap-style with strappy tie waist, high slit, fluid drape, metal D-rings at wrap closure",
        "charcoal midi skirt paneled construction with exposed seams, high waist, side zip, architectural seams raw edges",
        "black midi skirt leather, high slit front with zipper guard, raw hem, structured waistband, distressed",
        "charcoal midi skirt pleated with raw edges, high waist, side zip, swing movement, moon-phase embroidery at hem",
    ],
    "biker_shorts": [
        "black high-waisted biker shorts ruched side seams with metal grommets, tight fit, compressive, mid-thigh, occult embroidery",
        "black biker shorts high waist, wide elastic band with D-ring hardware, silicone grip hem, 7-inch inseam, raw edges",
        "charcoal biker shorts high waist, contrast stitching with metallic thread, compressive, reflective inverted cross logo",
        "black leather-look biker shorts high waist, zip pockets with leather pulls, structured, mid-thigh, boned seams",
        "dark green biker shorts high waist, mesh side panels with flocked velvet bats, compressive, 8-inch inseam",
        "black biker shorts high waist, ruched back seam with chain detail, silicone grip, matte finish, O-ring at waist",
        "charcoal biker shorts high waist, wide waistband with metal grommets, subtle rib texture, compressive, raw hem",
        "black biker shorts high waist, cut-out side panels with strappy harness lace-up, mesh inserts, compressive",
        "black biker shorts high waist, reflective piping with occult sigils, silicone grip, 7-inch inseam, raw edges",
        "charcoal biker shorts high waist, ruched sides with grommets, wide band, compressive, matte, distressed hem",
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