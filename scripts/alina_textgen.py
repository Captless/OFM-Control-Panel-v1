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
        "i only feel this honest after midnight.",
        "soft isn't a weakness. it's my best-kept secret.",
        "nobody sees the quiet version of me.",
        "the dark always brings out what i hide.",
        "i feel things louder than i say them.",
        "some nights i'm just tired of pretending i'm fine.",
        "i hide my softness behind the black.",
        "people assume i don't care. they're wrong.",
    ],

    "confident": [
        "i stopped shrinking to make others comfortable.",
        "black looks better when you carry it like you own it.",
        "i don't chase attention. it finds me.",
        "knowing your worth changes everything.",
        "i'm not loud. i'm just impossible to ignore.",
        "i built this confidence myself.",
        "the mirror and i have an agreement.",
        "i'd rather be too much than never enough.",
    ],

    "playful": [
        "this was absolutely on purpose.",
        "don't act like you weren't about to double-tap.",
        "i dare you to say what you're thinking.",
        "catching you staring is my favorite hobby.",
        "i'm trouble with good lighting.",
        "one look was all it took. admit it.",
        "i know exactly what i'm doing. and i'm enjoying it.",
        "you're blushing through the screen. i can tell.",
    ],

    "aesthetic": [
        "low light was made for girls like me.",
        "this is more than a picture. it's a mood.",
        "dark rooms frame me better than anyone could.",
        "a little grain. a little shadow. a lot of me.",
        "i don't chase aesthetics. i am one.",
        "midnight just looks good on me.",
        "black is the only color i need.",
        "some looks are worth staying for.",
    ],

    "relatable": [
        "i got all dressed up to stay inside.",
        "the mirror is my main event tonight.",
        "my plan was chaos with good vibes.",
        "i took forty pictures to post one.",
        "sleep lost. the outfit won.",
        "i'm thriving in my delusion tonight.",
        "no plans, but i still got ready.",
        "this is my idea of a productive night.",
    ],

    "teasing": [
        "you keep pretending you're not looking. cute.",
        "i saw you stop scrolling. i'll allow it.",
        "go on. you can admit you stayed for me.",
        "curiosity looks good on you.",
        "i noticed you noticing me.",
        "you were about to comment. i felt it.",
        "one more glance and i'll make it count.",
        "deny it all you want. i saw you.",
    ],

    "seductive": [
        "i know the effect i have on you.",
        "the best part is what i'm not showing.",
        "attention from you feels different.",
        "i left just enough to keep you wondering.",
        "you can't look away and i love that.",
        "i know exactly what you're thinking.",
        "the way you watch me says everything.",
        "some girls tease. i make you stay.",
    ],

    "mysterious": [
        "you'll never get the whole story from me.",
        "the fun part is what i'm not telling you.",
        "i like that you're trying to figure me out.",
        "there's always more. that's the point.",
        "guess all you want. you won't get it right.",
        "i keep my best parts hidden.",
        "mystery is the most interesting thing i wear.",
        "you can wonder. i'll stay unknowable.",
    ],

    "dangerous": [
        "trouble looks this good for a reason.",
        "i'm the mistake you'll want to make again.",
        "you've been warned. still tempted.",
        "i look sweet until i don't.",
        "curiosity made you stay. bad call.",
        "i'm exactly the kind of danger you like.",
        "some lines you shouldn't cross. i dare you.",
        "you should run. but you won't.",
    ],

    "direct": [
        "be honest with me. i can take it.",
        "what's the first thing you'd say to me?",
        "would you actually approach me?",
        "don't overthink. just answer.",
        "i asked a question. i expect an answer.",
        "your turn. impress me.",
        "stop scrolling. you have something to say.",
        "tell me the truth once. just once.",
    ],
}


CLOSERS = {
    "vulnerable": [
        "this version of me is the one nobody gets.",
        "the quiet version of me stays hidden.",
        "i feel more than i'll ever say.",
        "softness is my secret weapon.",
        "the night knows who i really am.",
        "i'm more than the black i hide behind.",
    ],

    "confident": [
        "you can look. you just can't forget me.",
        "i'd rather be unforgettable than easy.",
        "the confidence is permanent.",
        "i'm exactly who i decided to be.",
        "black looks best when i wear it like a crown.",
        "you'll remember this one.",
    ],

    "playful": [
        "caught you. don't pretend you didn't enjoy it.",
        "behave, or i'll post more.",
        "you're welcome for the smile.",
        "that was me being on my best behavior.",
        "one like and i'll keep 'em coming.",
        "don't blame me if you smirked.",
    ],

    "aesthetic": [
        "this mood is living rent-free in your head now.",
        "darkness and i get along great.",
        "some vibes you just don't scroll past.",
        "midnight has a favorite. it's me.",
        "this look did what needed to be done.",
        "the aesthetic stays.",
    ],

    "relatable": [
        "anyway, sleep can wait.",
        "this is my idea of self care.",
        "at least the outfit was a win.",
        "chaos, but make it fashionable.",
        "tomorrow's problem. tonight's good time.",
        "my life is organized chaos. it works.",
    ],

    "teasing": [
        "you'll think about this one later. i know it.",
        "admit you've already replayed it.",
        "i'll leave you curious on purpose.",
        "your attention is officially mine.",
        "don't worry, i'll keep you hooked.",
        "bet you're still here. good.",
    ],

    "seductive": [
        "i'll leave you wanting the rest.",
        "some things are better left unfinished.",
        "you can keep that thought. i meant it.",
        "for now, i'll let you wonder.",
        "temptation is kind to me.",
        "come back when you're ready.",
    ],

    "mysterious": [
        "wonder all you want. i'll stay a secret.",
        "the best part is what you'll never know.",
        "keep guessing. i'm not telling.",
        "i always leave something unanswered.",
        "that's all you're getting for now.",
        "even the dark doesn't know it all.",
    ],

    "dangerous": [
        "you were warned. and you stayed.",
        "i told you i was trouble.",
        "your curiosity chose this.",
        "don't say i didn't warn you.",
        "this was your idea too.",
        "good luck getting over it.",
    ],

    "direct": [
        "so, are you going to say hi or not?",
        "answer me. i'm still waiting.",
        "now it's your move.",
        "be honest. i know you have an answer.",
        "don't leave me hanging.",
        "say it. i'm listening.",
    ],
}


# ---------------------------------------------------------------------------
# Unified CTA pool.
#
# CTAs are designed around curiosity, flirtation, conversation, and
# low-friction interaction instead of generic engagement bait.
# ---------------------------------------------------------------------------

CTA_POOL = {
    "vulnerable": [
        "would you still notice me if i wasn't dressed like this?",
        "gentle, i'm being honest tonight.",
        "what do you do with all the quiet parts of you?",
        "tell me what makes you stay up late.",
        "does it scare you that i feel things this much?",
        "would you hold the attention if i let it slip?",
        "be honest — what do you see when you really look?",
        "i'm soft tonight. don't make me regret it.",
        "it's 2am and my guard is down. take care of that.",
        "i only say this stuff when the lights are low.",
        "does anyone else feel everything this loudly?",
        "i'm scared of how much i care.",
        "tell me i'm not alone in this.",
        "some nights i just want to feel understood.",
        "be the one who actually stays, not just watches.",
        "i hold the dark close so you don't have to.",
    ],
    "confident": [
        "you already know you'd look twice.",
        "admit it — i look expensive.",
        "some girls beg for attention. i don't have to.",
        "tell me i'm wrong and we'll both know you're lying.",
        "i know my worth, i'm just checking if you do too.",
        "eyes up here, you're losing your focus.",
        "you're not ready for the full package.",
        "take a picture, it lasts longer than your excuse.",
        "i walk in like i own the room. because i do.",
        "black is loyalty and i wear it like a crown.",
        "i'm the girl your friends warned you about.",
        "i'm expensive but i'm worth every cent.",
        "be honest — you'd clear your schedule for me.",
        "i don't chase. i get chosen. lucky you.",
        "my confidence isn't loud. it's certain.",
        "you can look, just don't forget who you're looking at.",
        "i look good and i know it. that's not arrogance.",
    ],
    "playful": [
        "i dare you to say hi first.",
        "behave, or i'll post the other one.",
        "caught you staring. don't stop.",
        "you can run, but you'll look twice before you do.",
        "one tiny comment. just one.",
        "admit it — you're a little curious.",
        "don't act like you weren't about to like this.",
        "i'll let you decide if i'm trouble or fun.",
        "wanna guess what i'm thinking? spoiler: chaotic.",
        "i bite. but mostly when you deserve it.",
        "me and my eyeliner are up to something.",
        "come a little closer. i don't bite. usually.",
        "who's braver — you or the comment box?",
        "i'm flattered you're still here.",
        "don't blame me if you smile.",
        "first one to comment gets a prize. good luck.",
    ],
    "aesthetic": [
        "tell me which detail caught your eye first.",
        "does this vibe live in your head rent free?",
        "rate this mood from one to 'stay a while'.",
        "name one thing this photo isn't saying.",
        "which shadow do you keep coming back to?",
        "this is aesthetic. get used to it.",
        "guess my favorite part of this look.",
        "you looked longer than this photo deserves.",
        "dark rooms love a girl like me.",
        "the lighting did half the work. i did the rest.",
        "does this feel like a movie to you too?",
        "one word: what does this say?",
        "i curate moods like someone's paying me.",
        "the vibe is the whole personality.",
        "tell me what aesthetic this gives you.",
        "some things look better in black and mystery.",
    ],
    "relatable": [
        "rate the outfit, not the chaos.",
        "my sleep schedule wants your opinion.",
        "accidentally dressed like i have my life together.",
        "you're judging me, aren't you. good.",
        "i got ready for the camera, not for plans.",
        "one like = you felt seen.",
        "tell me you've done the exact same thing.",
        "who else is up way too late?",
        "the mirror lied to me today too.",
        "i made plans and nothing cancelled them.",
        "being unhinged is exhausting, but cute.",
        "give me a reason to get dressed properly tomorrow.",
        "my confidence and my life are in different zip codes.",
        "same energy, different day.",
        "you get the outfit, i get the chaos.",
        "being alive is expensive but i look affordable.",
    ],
    "teasing": [
        "you're still looking, aren't you?",
        "go on. say what you're thinking.",
        "your secret's safe with me. for now.",
        "i saw you scroll back. don't lie.",
        "curious, are we? i'm flattered.",
        "bet you won't comment. prove me wrong.",
        "you keep staring like i owe you an answer.",
        "don't be shy — i already know you noticed.",
        "i have your attention. now what?",
        "you act like you're not curious. cute.",
        "one more glance and i'll believe you.",
        "wanna tell me why you're still here?",
        "i'm counting how long you look.",
        "go ahead. you're playing along so well.",
        "i'd tease you more but you're already blushing.",
        "get caught up in this, i dare you.",
    ],
    "seductive": [
        "tell me the part you can't look away from.",
        "i know you're staying for me.",
        "what's the first thing you'd say to me?",
        "some girls are a distraction. i'm a destination.",
        "i can feel your attention from here.",
        "bet you're imagining things. good.",
        "come closer. the screen won't bite.",
        "tell me what this outfit does to you.",
        "your eyes are giving you away.",
        "i like the way you're watching me.",
        "say less. let the tension talk.",
        "i know what you liked about this. tell me i'm wrong.",
        "slow down. enjoy the view.",
        "you're trying to play it cool. it's not working.",
        "i left all the best parts unseen.",
        "whisper what you'd do if i were there.",
    ],
    "mysterious": [
        "what's your guess about me?",
        "i'll let you wonder — that's the fun part.",
        "some answers i'll keep to myself.",
        "do you want the truth or the interesting version?",
        "i like that you're trying to figure me out.",
        "there's a story here. i'm not telling it.",
        "guess wrong. you'll never know for sure.",
        "what do you think my deal is?",
        "i'm exactly what you think. maybe. or not.",
        "the more you watch, the less you'll know.",
        "i laugh at secrets. and i keep mine.",
        "you'll never get the full picture. that's the point.",
        "guess my type. you won't get it right.",
        "the interesting part is what i'm not showing.",
        "wonder all you want. i'm not explaining.",
        "some mysteries are worth staying for.",
    ],
    "dangerous": [
        "dare you to approach.",
        "your curiosity is showing.",
        "you've been warned. still here?",
        "some girls look good in trouble.",
        "i look like trouble.",
        "bet you love a bad decision.",
        "come any closer and it's your choice.",
        "you've been told about girls like me.",
        "i dare you to find out.",
        "i'm the night you'll always blame.",
        "this isn't a warning. it's an invitation.",
        "danger looks good on me.",
        "you seem curious. i've been called a bad idea.",
        "i agree. watch yourself.",
        "or don't. i like risk.",
        "some things you should leave alone. this isn't one.",
        "i'm not the safe option. that's the fun part.",
    ],
    "direct": [
        "would you actually come say hi?",
        "be honest — what caught your attention?",
        "answer me: sweet or trouble?",
        "don't overthink it. what would you say?",
        "your turn — impress me.",
        "say the first thing that comes to mind.",
        "be real, would you approach me?",
        "no filter. what are you thinking?",
        "stop scrolling. you have something to say.",
        "i'm listening. make it worth my time.",
        "be honest with me, i can take it.",
        "what's stopping you from commenting?",
        "don't overthink. just say it.",
        "i asked a question. i expect an answer.",
        "tell me the truth, not the polite version.",
    ],
}


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


def _resolve_pools(pools):
    """Return a full 7-key pool dict. Missing keys fall back to built-ins."""
    defaults = {
        "OPENERS": OPENERS,
        "MIDDLES": MIDDLES,
        "CLOSERS": CLOSERS,
        "CTA_POOL": CTA_POOL,
        "HASHTAG_POOL": HASHTAG_POOL,
        "CONTEXT_KEYWORDS": CONTEXT_KEYWORDS,
        "CONTEXT_PHRASES": CONTEXT_PHRASES,
    }
    if not pools:
        return defaults
    merged = {}
    for key, val in defaults.items():
        merged[key] = pools.get(key, val)
    return merged


def _hook_keys(pools):
    """Hook types available in the (resolved) OPENERS pool."""
    openers = pools.get("OPENERS", OPENERS)
    if isinstance(openers, dict):
        return list(openers.keys())
    return list(OPENERS.keys())


def _detect_context(content_idea, pools=None):
    """Return simple visual/context tags detected from the content idea."""
    if not content_idea:
        return []

    keywords_pool = (pools or {}).get("CONTEXT_KEYWORDS", CONTEXT_KEYWORDS)
    text = content_idea.lower()
    found = []

    for tag, keywords in keywords_pool.items():
        if any(keyword in text for keyword in keywords):
            found.append(tag)

    return found


def _context_phrase(content_idea, rng, pools=None):
    """Return one short phrase connected to the content idea."""
    tags = _detect_context(content_idea, pools)

    if not tags:
        return None

    phrases_pool = (pools or {}).get("CONTEXT_PHRASES", CONTEXT_PHRASES)
    tag = rng.choice(tags)
    if tag not in phrases_pool or not phrases_pool[tag]:
        return None
    return rng.choice(phrases_pool[tag])


def _make_contextual_on_screen(opener, content_idea, hook_type, rng, pools=None):
    """
    Keep most captions clean and natural.

    Occasionally incorporate a visual cue directly into the on-screen
    caption. This prevents every generated caption from sounding like a
    template while still making the idea influence the output.
    """
    if not content_idea:
        return opener.strip().rstrip(".").strip()

    context = _context_phrase(content_idea, rng, pools)

    if not context:
        return opener.strip().rstrip(".").strip()

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
        return rng.choice(contextual_templates[hook_type]).rstrip(".").strip()

    return opener.strip().rstrip(".").strip()


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
    pools=None,
):
    """
    Generate one caption dict.

    hook_type:
        One of the supported hook keys. None/unknown -> random hook.

    content_idea:
        Optional short description of the image/video.
        Used as creative context for the generated captions.

    pools:
        Optional dict overriding OPENERS/MIDDLES/CLOSERS/CTA_POOL/
        HASHTAG_POOL/CONTEXT_KEYWORDS/CONTEXT_PHRASES. Missing keys fall
        back to built-in pools. None -> built-in pools.

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

    resolved = _resolve_pools(pools)
    openers = resolved["OPENERS"]
    middles = resolved["MIDDLES"]
    closers = resolved["CLOSERS"]

    if hook_type not in openers:
        hook_type = rng.choice(_hook_keys(resolved))

    # Single on-screen line, picked at random from the selected hook type's
    # OPENERS ∪ MIDDLES ∪ CLOSERS (not just openers).
    combo = list(openers.get(hook_type, [])) \
        + list(middles.get(hook_type, [])) \
        + list(closers.get(hook_type, []))
    line = rng.choice(combo) if combo else rng.choice(openers[hook_type])

    on_screen = _make_contextual_on_screen(
        line,
        content_idea,
        hook_type,
        rng,
        resolved,
    )

    # CTA
    cta_pool = resolved["CTA_POOL"]
    if isinstance(cta_pool, dict):
        candidates = cta_pool.get(hook_type) or []
        if not candidates:
            for v in cta_pool.values():
                candidates += v
        cta = rng.choice(candidates) if candidates else rng.choice(CTA_POOL.get(hook_type, list(CTA_POOL.values())[0]))
    else:
        cta = rng.choice(cta_pool if cta_pool else list(CTA_POOL.values())[0])

    # Hashtags
    hashtag_pool = resolved["HASHTAG_POOL"]
    pool = hashtag_pool if hashtag_pool else HASHTAG_POOL
    if len(pool) >= 3:
        num_hashtags = rng.randint(3, min(5, len(pool)))
    else:
        num_hashtags = len(pool)
    hashtags = rng.sample(pool, num_hashtags) if pool else []

    return {
        "on_screen": on_screen,
        "hook_type": hook_type,
        "cta": cta,
        "hashtags": hashtags,
    }


def batch_generate(
    count,
    hook_types=None,
    seed=None,
    content_idea=None,
    pools=None,
):
    """
    Generate `count` unique captions.

    hook_types:
        List of hook keys to pick from.
        None -> random selection from all hook types.

    content_idea:
        Optional visual/content description.

    pools:
        Optional dict overriding pool structures. Missing keys fall back to
        built-in pools.

    seed:
        Private Random(seed) for reproducibility.

    Deduplicates by on-screen text.
    """
    if count <= 0:
        return []

    rng = random.Random(seed) if seed is not None else random

    resolved = _resolve_pools(pools)
    valid_hooks = _hook_keys(resolved)

    if hook_types:
        hook_types = [
            hook for hook in hook_types
            if hook in valid_hooks
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
            pools=resolved,
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