"""
Standalone identity-locked caption generator for Alina Sky.

Zero-dependency, pool-based caption generator (no AI API).

Produces:
- On-screen captions: short, attention-grabbing hooks
- Post captions: longer, conversational/flirty captions
- CTA
- Hashtags

Captions are grounded in Alina's identity:
- goth / alt girl
- dark feminine energy
- seductive / teasing
- black outfits
- dark rooms
- mirror selfies
- wet/damp hair
- night drives
- late-night energy
- mysterious / confident / playful personality

The optional content_idea gives the generator visual context so captions
can better match the image/video being posted.

Usage:
    python scripts/alina_textgen.py 10
    python scripts/alina_textgen.py 5 --hook teasing
    python scripts/alina_textgen.py 5 --idea "mirror selfie, wet hair, black tee"
    python scripts/alina_textgen.py 5 --hook seductive --idea "night drive, leather jacket"
"""

import random
import re


# ---------------------------------------------------------------------------
# Caption pools
#
# Keep these short enough for 6-second on-screen captions.
# The voice should feel dark, feminine, confident, teasing, flirtatious,
# mysterious, and naturally conversational.
# ---------------------------------------------------------------------------

OPENERS = {
    "vulnerable": [
        "i only get this honest when the lights are off",
        "some nights i want to be understood without explaining myself",
        "there is a softer version of me nobody sees",
        "i hide a lot behind the black clothes and eyeliner",
        "maybe i only feel safe when the world is asleep",
        "3am always makes me say what i normally hide",
        "i look confident until you get close enough to notice",
        "the dark has always felt a little more like home",
        "some things are easier to admit after midnight",
        "i pretend i don't care a lot better than i actually do",
        "behind the attitude is a girl who still feels everything",
        "sometimes i just want someone to stay a little longer",
    ],

    "confident": [
        "i know exactly what you're looking at",
        "black looks better when you wear it like you mean it",
        "being intimidating was never something i planned to fix",
        "i stopped dressing for people who don't get it",
        "i don't need everyone's attention. just the right person's",
        "the mirror already told me what i needed to know",
        "i know my worth and apparently it shows",
        "not every girl is supposed to be easy to forget",
        "i was never interested in looking ordinary",
        "you can call it attitude. i call it knowing myself",
        "i don't chase attention. somehow it keeps finding me",
        "if i'm too much, you were probably looking for less",
    ],

    "playful": [
        "you looked a little too long, didn't you?",
        "be honest, you would have looked twice",
        "i was behaving until i took this picture",
        "this was supposed to be a normal selfie",
        "i blame the outfit for everything that happens next",
        "don't act innocent. i know you noticed",
        "i probably shouldn't be this good at distracting you",
        "caught you staring. cute.",
        "i could pretend this picture was accidental",
        "just giving you something to think about tonight",
        "i know exactly what kind of trouble this looks like",
        "you can stop scrolling now. i won't tell anyone",
    ],

    "aesthetic": [
        "black clothes, low light, and a little bit of trouble",
        "somewhere between pretty and slightly dangerous",
        "the darker the room, the better i look",
        "low light has always been kind to me",
        "messy hair, smudged liner, perfect mood",
        "there is something about midnight that suits me",
        "caught somewhere between a daydream and a bad idea",
        "dark rooms make everything feel more honest",
        "a little grain, a little shadow, a lot of mood",
        "the night always makes me look like a secret",
        "black on black never gets old",
        "this lighting understood the assignment",
    ],

    "relatable": [
        "spent way too long getting dressed just to take pictures at home",
        "my wardrobe is 90 percent black and somehow i need more",
        "i said one picture and took forty",
        "my sleep schedule has officially left the chat",
        "i get ready like i'm going somewhere and then stay in my room",
        "my camera roll is basically mirror checks",
        "i have no idea what i'm doing but at least the outfit looks good",
        "another night, another questionable decision",
        "i should probably be sleeping right now",
        "the outfit was too good to stay undocumented",
        "i said i was going to keep it casual",
        "somehow getting dressed became the main event",
    ],

    "teasing": [
        "you can look. i'm not going to stop you",
        "tell me you didn't pause on this one",
        "i wonder how long you stared before reading this",
        "don't be shy. i already noticed you",
        "you weren't supposed to like this one that much",
        "i know exactly where your eyes went",
        "keep looking. i won't judge",
        "you can pretend you were just scrolling",
        "i probably shouldn't make eye contact like this",
        "if you were hoping i'd notice you, i did",
        "go ahead. make your guess about me",
        "i think you're enjoying this a little too much",
    ],

    "seductive": [
        "some pictures are meant to be looked at twice",
        "i look better when the lights are low",
        "there's a reason i took this one after midnight",
        "maybe the dark brings out my favorite side",
        "i know what this picture does to your attention",
        "a little mystery makes everything more interesting",
        "i wasn't trying to be distracting. maybe that's the problem",
        "this is the version of me you don't get during the day",
        "if you like girls with a little edge, stay awhile",
        "the closer you look, the less innocent this feels",
        "i left just enough mystery for you to wonder",
        "you can keep staring. i'm enjoying the attention",
    ],

    "mysterious": [
        "you only get to see this side of me at night",
        "there's more to this picture than i'm going to explain",
        "some things are better left unanswered",
        "i could tell you what i was thinking here, but where's the fun?",
        "not everything about me needs an explanation",
        "the interesting part is what you can't see",
        "maybe i'm exactly what you think i am",
        "there's always a story behind the picture",
        "you can wonder. i won't correct you",
        "some secrets look better in black",
        "i'll let you decide what kind of girl i am",
        "the best part is what happens in your imagination",
    ],

    "dangerous": [
        "i have a feeling i'm someone's bad idea tonight",
        "i probably look like a decision you'd regret",
        "pretty girls can be terrible influences too",
        "you should probably know better than to trust this face",
        "i'm sweet until you give me a reason not to be",
        "i look harmless. that's the dangerous part",
        "some trouble happens to look really good in black",
        "i never said i was the good decision",
        "you can blame me when this becomes a bad idea",
        "i have exactly the kind of energy your friends warned you about",
        "maybe you should keep your distance",
        "curiosity has always been my favorite bad habit",
    ],

    "direct": [
        "be honest. would you look twice?",
        "tell me what you noticed first",
        "would you actually come say hi?",
        "if you saw me like this, what would you say?",
        "don't overthink it. would you approach me?",
        "your turn. what caught your attention?",
        "would you take me somewhere or just keep staring?",
        "if this showed up at 2am, would you keep scrolling?",
        "tell me the first thought that crossed your mind",
        "i know you have an answer. say it",
        "would you be brave enough to talk to me?",
        "so... are you going to say hi or not?",
    ],
}


MIDDLES = {
    "vulnerable": [
        "i don't show that side of myself very often",
        "but somehow the quiet always brings it back",
        "and maybe being soft isn't something i need to apologize for",
        "i just don't always know how to say what i mean",
        "the people who understand don't usually need an explanation",
        "sometimes being alone is easier than pretending",
        "i think everyone has a side they keep hidden",
        "and mine always seems to come out after midnight",
    ],

    "confident": [
        "and i'm finally comfortable being exactly who i am",
        "i stopped trying to make myself easier to understand",
        "there's nothing wrong with knowing what you want",
        "i'd rather stand out than disappear into the crowd",
        "the right people won't need me to tone it down",
        "i don't need permission to take up space",
        "confidence looks especially good in black",
        "i've spent too long becoming someone i'm proud of",
    ],

    "playful": [
        "and yes, i knew exactly what i was doing",
        "don't make me pretend this wasn't intentional",
        "i'll let you decide whether that was an accident",
        "honestly, i just wanted to see who would notice",
        "you probably should have kept scrolling",
        "but apparently neither of us is very good at behaving",
        "i'm innocent until proven otherwise",
        "and i'm not answering questions without a lawyer",
    ],

    "aesthetic": [
        "the shadows made everything feel a little more cinematic",
        "the low light somehow made the whole mood better",
        "there's something about nighttime that makes everything softer",
        "the grain makes it feel more real",
        "black, silver, and a little bit of darkness is usually enough",
        "the mirror caught the mood better than i expected",
        "the night always seems to know how to frame me",
        "some moods don't need much explaining",
    ],

    "relatable": [
        "and somehow i still thought i needed another outfit",
        "because apparently taking pictures is now part of getting ready",
        "which is probably why i never actually go to bed on time",
        "and yes, i took another picture before putting my phone down",
        "i'll call it productive if anyone asks",
        "at least one thing in my life is coordinated",
        "and honestly, that's good enough for tonight",
        "this is what passes for having my life together",
    ],

    "teasing": [
        "and i can tell you noticed",
        "but i'm curious if you're brave enough to admit it",
        "don't worry, your secret is safe with me",
        "i'm giving you one chance to be honest",
        "you can keep pretending you're here for the aesthetic",
        "i won't embarrass you if you tell the truth",
        "something tells me you're still looking",
        "and i'm not exactly complaining about that",
    ],

    "seductive": [
        "the fun part is knowing you can't quite look away",
        "there's something addictive about a little mystery",
        "i think the right amount of temptation is healthy",
        "sometimes attention feels better when you know you earned it",
        "i like leaving a little something to the imagination",
        "not everything needs to be shown to be noticed",
        "the best kind of flirting is the kind you can deny",
        "maybe i wanted you to notice",
    ],

    "mysterious": [
        "i'll let your imagination fill in the rest",
        "you can decide what was happening before the picture",
        "some answers are more fun when you never get them",
        "i think wondering is half the fun",
        "there's always another side you haven't seen",
        "maybe i'll explain it eventually",
        "or maybe i'll let you keep guessing",
        "you don't need to know everything about me yet",
    ],

    "dangerous": [
        "and somehow that usually ends exactly how you'd expect",
        "i've never been particularly good at making sensible choices",
        "the warning signs are probably already there",
        "but you were curious enough to stay",
        "i don't think you're looking for the safe option anyway",
        "some mistakes are worth making once",
        "you knew what kind of energy you were getting into",
        "i'm starting to think you like trouble",
    ],

    "direct": [
        "i'm actually curious what you'd say to me in person",
        "don't give me the safe answer",
        "you can be honest here",
        "i promise i won't judge your answer",
        "there's no wrong answer, just boring ones",
        "i'm reading the comments, so choose carefully",
        "you've already looked, so you might as well answer",
        "now i'm waiting for your answer",
    ],
}


CLOSERS = {
    "vulnerable": [
        "maybe that's enough honesty for one night.",
        "the dark makes it easier to be myself.",
        "some nights i just need a little quiet.",
        "maybe someone out there understands.",
        "i'll figure the rest out tomorrow.",
        "for tonight, this version of me is enough.",
    ],

    "confident": [
        "and i'm not changing that for anyone.",
        "take it or leave it. i'm still going to be me.",
        "the edge stays.",
        "i like myself exactly like this.",
        "consider that your warning.",
        "i'm only getting harder to forget.",
    ],

    "playful": [
        "anyway, you didn't see anything.",
        "now pretend you weren't staring.",
        "okay, i'll behave. probably.",
        "don't make me post the other one.",
        "that's enough trouble for one night.",
        "you can thank me later.",
    ],

    "aesthetic": [
        "some moods are better left in the dark.",
        "the night understood the assignment.",
        "darkness looks good on me.",
        "that's the mood for tonight.",
        "some pictures just feel like midnight.",
        "i think i'll keep this one.",
    ],

    "relatable": [
        "anyway, i'm going back to bed.",
        "tomorrow i'll pretend i'm responsible again.",
        "that's enough productivity for tonight.",
        "same girl, different night.",
        "at least the picture turned out good.",
        "now i'm actually going to sleep. maybe.",
    ],

    "teasing": [
        "don't worry, i'll give you something else to stare at later.",
        "you can admit you liked it.",
        "i'll leave you with that thought.",
        "maybe i'll give you another reason to stay.",
        "you'll have to wait for the next one.",
        "i think you know exactly what i mean.",
    ],

    "seductive": [
        "some things are better when they're left unfinished.",
        "i think i'll let you wonder about the rest.",
        "maybe i'll give you another look tomorrow.",
        "for now, this is all you're getting.",
        "a little temptation never hurt anyone.",
        "you can keep that thought for later.",
    ],

    "mysterious": [
        "maybe you'll figure me out eventually.",
        "or maybe you never will.",
        "i'll let you keep guessing.",
        "some secrets are more fun this way.",
        "that's all i'm telling you tonight.",
        "the rest stays between me and the dark.",
    ],

    "dangerous": [
        "you were warned.",
        "don't say i didn't tell you.",
        "somewhere along the way, this became your problem.",
        "i never promised to be good for you.",
        "you can blame your curiosity later.",
        "good luck behaving now.",
    ],

    "direct": [
        "so tell me.",
        "i'm waiting.",
        "your move.",
        "don't leave me guessing.",
        "say it.",
        "i want the honest answer.",
    ],
}


# ---------------------------------------------------------------------------
# Unified CTA pool.
#
# CTAs are designed around curiosity, flirtation, conversation, and
# low-friction interaction instead of generic engagement bait.
# ---------------------------------------------------------------------------

CTA_POOL = [
    "be honest... would you look twice?",
    "tell me what you noticed first",
    "would you actually come say hi?",
    "what would you say to me?",
    "pick one: sweet or trouble?",
    "don't be shy. i'm reading.",
    "tell me your first thought",
    "would you approach me in person?",
    "what caught your attention?",
    "give me your honest answer",
    "should i post the other one?",
    "tell me what kind of mood this gives you",
    "would you stay or keep scrolling?",
    "which detail did you notice first?",
    "i want to know what you'd say",
    "your turn. make me curious.",
]


# ---------------------------------------------------------------------------
# Hashtag pool.
#
# Keep hashtags niche/identity focused. Avoid platform-specific tags so
# the same generated content can be reused across platforms.
# ---------------------------------------------------------------------------

HASHTAG_POOL = [
    "#altgirl",
    "#gothgirl",
    "#goth",
    "#altmodel",
    "#altstyle",
    "#gothstyle",
    "#darkaesthetic",
    "#darkfeminine",
    "#gothic",
    "#egirl",
    "#alternativegirl",
    "#darkgirl",
    "#altfashion",
    "#gothicstyle",
    "#darkstyle",
]


# ---------------------------------------------------------------------------
# Content idea helpers.
#
# This is intentionally simple. No AI, vision model, API, or external
# dependency is required.
# ---------------------------------------------------------------------------

CONTEXT_KEYWORDS = {
    "mirror": ["mirror", "reflection", "bathroom selfie", "mirror selfie"],
    "bedroom": ["bedroom", "bed", "room", "pillow"],
    "night": ["night", "midnight", "3am", "late night", "dark"],
    "car": ["car", "drive", "driving", "night drive"],
    "leather": ["leather", "leather jacket"],
    "dress": ["dress", "black dress", "mini dress"],
    "skirt": ["skirt", "mini skirt"],
    "tee": ["tee", "t-shirt", "shirt", "band tee", "oversized tee"],
    "hoodie": ["hoodie", "oversized hoodie"],
    "hair": ["hair", "wet hair", "damp hair", "messy hair"],
    "makeup": ["makeup", "eyeliner", "liner", "lipstick"],
    "flash": ["flash", "phone flash", "camera flash"],
    "neon": ["neon", "neon lights", "city lights"],
    "rain": ["rain", "rainy", "wet street"],
    "coffee": ["coffee", "cafe", "café"],
    "concert": ["concert", "show", "gig", "band"],
}


CONTEXT_PHRASES = {
    "mirror": [
        "this mirror selfie",
        "the mirror caught me",
        "this reflection",
    ],
    "bedroom": [
        "this little bedroom moment",
        "being alone in my room",
        "this late-night room mood",
    ],
    "night": [
        "the late-night mood",
        "being up this late",
        "midnight energy",
    ],
    "car": [
        "this night drive",
        "being out after midnight",
        "the drive home",
    ],
    "leather": [
        "this leather jacket",
        "wearing leather at midnight",
        "the leather look",
    ],
    "dress": [
        "this black dress",
        "wearing this dress",
        "the black dress",
    ],
    "skirt": [
        "this little skirt",
        "the outfit tonight",
        "this look",
    ],
    "tee": [
        "this oversized tee",
        "the band tee",
        "this black tee",
    ],
    "hoodie": [
        "this oversized hoodie",
        "the hoodie",
        "this lazy-night look",
    ],
    "hair": [
        "the messy hair",
        "this wet-hair moment",
        "the hair and the mood",
    ],
    "makeup": [
        "the eyeliner",
        "the makeup tonight",
        "this look",
    ],
    "flash": [
        "the phone flash",
        "this flash-lit moment",
        "the camera flash",
    ],
    "neon": [
        "the neon lights",
        "this city glow",
        "the lights tonight",
    ],
    "rain": [
        "the rain outside",
        "this rainy night",
        "the wet streets",
    ],
    "coffee": [
        "this little coffee run",
        "the coffee and the mood",
        "this café moment",
    ],
    "concert": [
        "the show tonight",
        "being around live music",
        "this concert mood",
    ],
}


def _detect_context(content_idea):
    """Return simple visual/context tags detected from the content idea."""
    if not content_idea:
        return []

    text = content_idea.lower()
    found = []

    for tag, keywords in CONTEXT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(tag)

    return found


def _context_phrase(content_idea, rng):
    """Return one short phrase connected to the content idea."""
    tags = _detect_context(content_idea)

    if not tags:
        return None

    tag = rng.choice(tags)
    return rng.choice(CONTEXT_PHRASES[tag])


def _make_contextual_on_screen(opener, content_idea, hook_type, rng):
    """
    Keep most captions clean and natural.

    Occasionally incorporate a visual cue directly into the on-screen
    caption. This prevents every generated caption from sounding like a
    template while still making the idea influence the output.
    """
    if not content_idea:
        return opener.strip().rstrip(".") + "."

    context = _context_phrase(content_idea, rng)

    if not context:
        return opener.strip().rstrip(".") + "."

    contextual_templates = {
        "teasing": [
            f"{context} and you still looked twice.",
            f"{context}. be honest, you stared.",
        ],
        "seductive": [
            f"{context} hits different after midnight.",
            f"{context}. maybe that's why you can't look away.",
        ],
        "mysterious": [
            f"{context}, and i'm still not telling you the story.",
            f"{context}. i'll let you wonder why.",
        ],
        "dangerous": [
            f"{context} looks like a bad idea.",
            f"{context}. you were warned.",
        ],
        "direct": [
            f"{context}. would you come say hi?",
            f"{context}. what would you say to me?",
        ],
        "confident": [
            f"{context}. i know it looks good.",
            f"{context}. exactly how i wanted it.",
        ],
        "playful": [
            f"{context}. this was definitely intentional.",
            f"{context}. don't act like you didn't notice.",
        ],
        "aesthetic": [
            f"{context}, but make it midnight.",
            f"{context}. the lighting did the rest.",
        ],
        "vulnerable": [
            f"{context}. somehow this felt like the right moment.",
            f"{context}. maybe the quiet made me honest.",
        ],
        "relatable": [
            f"{context}. obviously i had to take a picture.",
            f"{context}. because apparently that's productive now.",
        ],
    }

    # Contextual wording is used often enough to matter, but not every time.
    if rng.random() < 0.65:
        return rng.choice(contextual_templates[hook_type])

    return opener.strip().rstrip(".") + "."


# ---------------------------------------------------------------------------
# Caption generation.
# ---------------------------------------------------------------------------

_HOOK_KEYS = list(OPENERS.keys())
_MAX_DEDUP_ATTEMPTS = 5000


def generate_caption(
    hook_type=None,
    seed=None,
    _rng=None,
    content_idea=None,
):
    """
    Generate one caption dict.

    hook_type:
        One of the supported hook keys. None/unknown -> random hook.

    content_idea:
        Optional short description of the image/video.
        Used as creative context for the generated captions.

    seed:
        Private Random(seed) for reproducible output.

    _rng:
        Internal random instance used by batch_generate.

    Returns:
        {
            "on_screen": "...",
            "post": "...",
            "hook_type": "...",
            "cta": "...",
            "hashtags": [...]
        }
    """
    rng = _rng or random

    if _rng is None and seed is not None:
        rng = random.Random(seed)

    if hook_type not in OPENERS:
        hook_type = rng.choice(_HOOK_KEYS)

    opener = rng.choice(OPENERS[hook_type])

    num_middles = rng.randint(0, 2)
    middles = rng.sample(MIDDLES[hook_type], num_middles)

    closer = rng.choice(CLOSERS[hook_type])

    # On-screen caption:
    # Short, punchy, attention-focused.
    on_screen = _make_contextual_on_screen(
        opener,
        content_idea,
        hook_type,
        rng,
    )

    # Post caption:
    # More conversational and personality-driven.
    parts = [opener] + middles + [closer]

    # If there is a content idea, occasionally reference its visual context
    # in the post without simply repeating the entire user input.
    context = _context_phrase(content_idea, rng)

    if context and rng.random() < 0.55:
        context_lines = [
            f"{context} just felt right tonight.",
            f"something about {context} made me want to take another picture.",
            f"i don't know why, but {context} had me feeling myself.",
            f"maybe it was {context}, maybe it was the mood.",
        ]
        parts.insert(1, rng.choice(context_lines))

    post = ". ".join(p.rstrip(".") for p in parts)

    if not post.endswith((".", "!", "?")):
        post += "."

    # CTA
    cta = rng.choice(CTA_POOL)

    # Hashtags
    num_hashtags = rng.randint(3, 5)
    hashtags = rng.sample(HASHTAG_POOL, num_hashtags)

    return {
        "on_screen": on_screen,
        "post": post,
        "hook_type": hook_type,
        "cta": cta,
        "hashtags": hashtags,
    }


def batch_generate(
    count,
    hook_types=None,
    seed=None,
    content_idea=None,
):
    """
    Generate `count` unique captions.

    hook_types:
        List of hook keys to pick from.
        None -> random selection from all hook types.

    content_idea:
        Optional visual/content description.

    seed:
        Private Random(seed) for reproducibility.

    Deduplicates by on-screen text.
    """
    if count <= 0:
        return []

    rng = random.Random(seed) if seed is not None else random

    if hook_types:
        hook_types = [
            hook for hook in hook_types
            if hook in OPENERS
        ]

    seen = set()
    results = []
    attempts = 0

    while len(results) < count and attempts < _MAX_DEDUP_ATTEMPTS:
        attempts += 1

        hook = rng.choice(hook_types) if hook_types else None

        cap = generate_caption(
            hook_type=hook,
            _rng=rng,
            content_idea=content_idea,
        )

        key = cap["on_screen"]

        if key in seen:
            continue

        seen.add(key)
        results.append(cap)

    if len(results) < count:
        raise ValueError(
            f"dedup cap {_MAX_DEDUP_ATTEMPTS} exhausted: "
            f"only {len(results)}/{count} unique captions generated — "
            f"pools too small for count"
        )

    return results


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Alina Sky content-aware captions."
    )

    parser.add_argument(
        "n",
        type=int,
        nargs="?",
        default=10,
        help="Number of captions (default 10)",
    )

    parser.add_argument(
        "--hook",
        choices=_HOOK_KEYS,
        default=None,
        help="Hook type (default: random)",
    )

    parser.add_argument(
        "--idea",
        "--content-idea",
        dest="content_idea",
        default=None,
        help="Short image/video content idea",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )

    args = parser.parse_args()

    hook_types = [args.hook] if args.hook else None

    for i, cap in enumerate(
        batch_generate(
            args.n,
            hook_types=hook_types,
            seed=args.seed,
            content_idea=args.content_idea,
        ),
        1,
    ):
        print(f"--- {i} [{cap['hook_type']}] ---")
        print(f"On-screen: {cap['on_screen']}")
        print(f"Post:      {cap['post']}")
        print(f"CTA:       {cap['cta']}")

        if cap["hashtags"]:
            print(" ".join(cap["hashtags"]))

        print()


if __name__ == "__main__":
    main()