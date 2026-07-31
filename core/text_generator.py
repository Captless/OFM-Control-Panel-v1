"""
Random paragraph text generator — altgirl leaning.
Shared with pipeline-tiktok. Same topics, same tones.
"""

import random

TOPICS = {
    "alt_situationship": {
        "feeling": "dark haired girl left on read, over-analyzing in a dim room",
        "openers": [
            "you ever let someone treat you like an option while you sat in the dark replaying every word they said",
            "there is something about being an alt girl that makes men think you will tolerate being treated like a side character",
            "the worst part is not that they left. its that you saw it coming and stayed anyway.",
            "you ever catch yourself romanticizing a person who never even romanticized you back",
        ],
        "middles": [
            "and you still catch yourself checking your phone like the outcome will magically change",
            "while theyre out there acting like you were just a phase they went through",
            "and you sat there in your room with the lights off thinking maybe if you were softer they would have stayed",
            "and the silence after they leave is louder than any music you put on to drown it out",
        ],
        "closers": [
            "but you were never the problem. you were just too much for someone who wanted less.",
            "and honestly? the peace after they are gone is better than the anxiety while they were here.",
            "but thats what happens when you give your darkness to someone who is scared of the dark.",
            "next time. you will choose someone who chooses all of you. not just the parts they liked.",
        ],
    },
    "alt_self_worth": {
        "feeling": "choosing yourself in fishnets and dark lipstick",
        "openers": [
            "you have spent so long being told you are too intense too dark too much that you forgot you were never meant to be consumed by people who cant handle the full picture",
            "the moment you stop apologizing for the way you exist is the moment you actually start living",
            "there is power in being the girl who walks away first. especially when no one expects her to.",
            "being called intimidating is just another word for being too real for people who live in surface level conversations",
        ],
        "middles": [
            "and you kept shrinking yourself to fit into spaces that were never designed to hold someone like you",
            "and people mistake your quiet for weakness until you prove them wrong",
            "and the same people who called you weird are the ones who will watch you glow from a distance",
            "and you finally realized that being too much for the wrong people means you are exactly enough for the right ones",
        ],
        "closers": [
            "dont dim yourself so others can feel comfortable. let them adjust to your brightness.",
            "your darkness is not a flaw. it is the reason you see the world differently. and that is your superpower.",
            "stop asking for permission to exist the way you are. just exist. loudly if you want to.",
            "the right people will not make you feel like you have to be smaller. they will make room.",
        ],
    },
    "alt_late_nights": {
        "feeling": "alt girl 3am thoughts, quiet and heavy",
        "openers": [
            "its 2am and im sitting here in an oversized band shirt wondering why the quiet hours hit different when youre the type of person who feels everything too deeply",
            "there is a specific kind of loneliness that only hits when you are the only one awake and the whole world feels like it is moving without you",
            "night time is when the thoughts you drown out all day crawl back up and demand to be heard",
            "laying in the dark with music so loud it drowns out your own brain but somehow the thoughts still cut through",
        ],
        "middles": [
            "and im not sad. just heavy. like my bones remember things my brain tried to forget.",
            "and you start questioning if you are actually okay or just really good at pretending for everyone else",
            "and the moon is the only witness to the version of you that comes out when no one is watching",
            "and you wonder if anyone else feels this hollow or if it is just you and your four walls",
        ],
        "closers": [
            "but morning always comes. and so do you. even when you did not want to.",
            "one more night survived. one more sunrise i didnt think id see. still here. still fighting.",
            "and somehow the darkness always feels less suffocating when you accept it as part of you.",
            "the night is heavy but so are you. and you are still standing. so thats something.",
        ],
    },
    "alt_anxiety": {
        "feeling": "overthinking in dark clothes, exhausting inner world",
        "openers": [
            "being an overthinker with an alt aesthetic is a weird combo because you look like you dont care but your brain has been running a marathon since 6am",
            "nobody talks about how exhausting it is to be hyperaware of everything. the energy in the room. the tone of a text. the silence between words.",
            "the worst part about anxiety is that your brain never takes a day off. not on weekends. not on holidays. not ever.",
            "having a brain that analyzes every single interaction until you have replayed it seven different ways is genuinely exhausting",
        ],
        "middles": [
            "and you have perfected the art of looking calm while your insides are a full emergency",
            "and by the time you finally relax your brain reminds you of something embarrassing you did 6 years ago",
            "and people tell you to just relax as if that wasnt literally the first thing you tried before the spiral started",
            "and the worst part is you cant even explain it without sounding dramatic but it feels like drowning in plain sight",
        ],
        "closers": [
            "but you are still here. still breathing. still trying. and that counts for something.",
            "one day at a time. or one panic at a time. we take what we can get.",
            "your brain might be loud but you are louder. keep going.",
            "and somehow you always make it through. even when you think you wont. that has to mean something.",
        ],
    },
    "alt_identity": {
        "feeling": "growing up different, embracing the dark aesthetic",
        "openers": [
            "growing up as the dark haired girl in a world that wanted you blonde and quiet teaches you early that you were never going to fit in and honestly that was the gift",
            "the version of you from high school who felt like an outsider would not believe the person you became",
            "being the weird girl who wore black and kept to herself was not a phase. it was the foundation of who you were always meant to be.",
            "there is a unique strength in growing up feeling like you dont belong anywhere and building your own world anyway",
        ],
        "middles": [
            "and the same people who didnt get you back then are the ones who want to know you now",
            "and you spent years trying to be palatable until you realized palatable is just another word for invisible",
            "and the things that made you feel alienated are the same things that make you unforgettable now",
            "and you finally stopped apologizing for taking up space in a world that told you to shrink",
        ],
        "closers": [
            "stay dark. stay weird. stay you. the world will catch up eventually.",
            "you were never meant to fit in. you were meant to stand out and make others feel less alone for being different too.",
            "your aesthetic is not a costume. it is armor. and you have earned every piece of it.",
            "embracing who you are is the most rebellious thing you can do in a world that wants everyone the same.",
        ],
    },
    "alt_dark_humor": {
        "feeling": "deadpan, dark jokes, coping through sarcasm",
        "openers": [
            "my personality is just dark humor and the inability to process my emotions in a healthy way",
            "people ask why i always look so serious and i say its because i have already mentally planned my exit from 3 different situations",
            "my toxic trait is thinking i can fix everyone while my own life is a dumpster fire but at least the aesthetic is good",
            "i am not emotionally unavailable i am just selectively present and right now i choose to be anywhere else",
        ],
        "middles": [
            "and somehow sarcasm is my primary love language and self deprecation is my comfort zone",
            "and people say cheer up as if i have not already calculated the exact amount of energy i have left for the day",
            "and i laugh at things i probably should not but that is how i survive so mind your business",
            "and my therapist would have a lot to say but i keep forgetting to book the appointment so here we are",
        ],
        "closers": [
            "anyway. the chaos is intentional. mostly.",
            "dark humor is just coping with a punchline. and honestly? it works.",
            "if i didnt laugh i would cry. and i already ran out of tears last week.",
            "and thats just how it is. take it or leave it. preferably take it so i dont have to explain myself again.",
        ],
    },
    "alt_dating_take": {
        "feeling": "dating preferences unapologetic, alt girl standards",
        "openers": [
            "the dating scene when you are an alt girl is wild because you either attract guys who want a project or guys who are intimidated by the fact that you have your own personality",
            "i am tired of men who think liking a girl in black lipstick makes them deep. liking me and romanticizing me are two different things.",
            "the bar for men is underground and they are still bringing a shovel",
            "i am not looking for someone who tolerates my aesthetic. i am looking for someone who actually sees me beyond the dark hair and the resting sad face.",
        ],
        "middles": [
            "and somehow basic respect is considered going above and beyond these days",
            "and men will call you a walking red flag just because you have boundaries and know what you want",
            "and the same guys who say they want a girl with personality cannot handle it when you actually have one",
            "and i am not here to be someones alt girl fantasy. i am here to be someones actual partner.",
        ],
        "closers": [
            "dont settle for someone who makes you feel like you are too much. find someone who wonders how they got so lucky.",
            "being alone is better than being with someone who makes you feel lonely in their presence.",
            "i would rather be alone with my music and my thoughts than fake smiles for someone who doesnt deserve them.",
            "the right person wont romanticize your darkness. they will sit in it with you until the light comes back.",
        ],
    },
    "alt_music_obsession": {
        "feeling": "music as identity, finding yourself in songs",
        "openers": [
            "my entire personality is just songs that make me feel like i am in a movie montage of my own life",
            "there is something about finding a song that perfectly describes the feeling you could not put into words",
            "music is the only thing that has never made me feel like i was too much",
            "my playlist history is basically a map of every emotional breakdown i have ever had and honestly it is the most honest documentation of my life",
        ],
        "middles": [
            "and you know a song hits different when you have to stop what you are doing and just sit with it",
            "and the right song at the wrong time can ruin your whole night in the best way",
            "and you build entire memories around specific songs and years later they still hit you with the same feeling",
            "and there are songs that feel like they were written specifically for the version of you that no one else sees",
        ],
        "closers": [
            "music is not just sound. it is proof that someone else out there felt the same way you do.",
            "let the music hit. let yourself feel it. that is what it is there for.",
            "the right playlist can save your life. or at least get you through the night. and that is enough.",
            "and somehow a song you have heard a hundred times can hit completely different on the right night.",
        ],
    },
    "alt_soft_moments": {
        "feeling": "quiet softness behind the dark exterior",
        "openers": [
            "people see the dark hair and the black clothes and assume i am cold but the truth is i feel everything way too deeply",
            "there is a softness to alt girls that people rarely get to see because we keep it guarded behind layers of sarcasm and dark humor",
            "being soft in a world that wants you hard is actually the bravest thing you can do",
            "i think the misconception about girls who dress dark is that we dont have feelings. we just have better walls.",
        ],
        "middles": [
            "and the few people who get past the walls are the ones who matter most because they took the time to actually see",
            "and underneath the dark aesthetic is someone who just wants to be understood without having to explain everything",
            "and the quiet moments alone where you let yourself be soft without judgment are the most healing",
            "and you learn that protecting your softness is not weakness. it is survival.",
        ],
        "closers": [
            "softness is not a flaw. it is proof that you still have a heart despite everything.",
            "let yourself be soft. even if only in the dark. even if only for yourself.",
            "the world will try to harden you. dont let it. keep your softness like a secret weapon.",
            "being soft and being strong are not opposites. they are the same thing worn at different times.",
        ],
    },
    "alt_rebellion": {
        "feeling": "quiet defiance, being yourself unapologetically",
        "openers": [
            "the most rebellious thing you can do as a woman is take up space without apologizing for it",
            "i spent so long trying to be palatable for people who were never going to accept me anyway and i am done with that",
            "there is a specific freedom that comes when you stop caring about what people think of your existence",
            "being yourself in a world that constantly tells you to be someone else is the most punk thing you can do",
        ],
        "middles": [
            "and every time they tell you to tone it down you turn it up louder because your existence is not up for negotiation",
            "and the people who told you to be quiet are the same ones who will try to claim they knew you when you succeed",
            "and you realize that their approval was never the prize you thought it was",
            "and the moment you stop performing for others is the moment you actually start living for yourself",
        ],
        "closers": [
            "be unapologetically yourself. the right people will stay. the wrong ones will filter themselves out.",
            "your existence is not a debate. you do not need to justify who you are to anyone.",
            "let them talk. you are not here to be liked by everyone. you are here to be real.",
            "the loudest statement you can make is simply existing as yourself without explanation.",
        ],
    },
}

TONES = [
    "dark and introspective",
    "deadpan alt humor",
    "raw unfiltered thought",
    "quiet realization in the dark",
    "second-person address like talking to your past self",
    "soft vulnerability behind the armor",
    "tired but still standing",
    "quiet defiance",
]


def random_text(topic_key=None):
    if topic_key:
        topic = TOPICS.get(topic_key)
        if not topic:
            raise ValueError(f"Unknown topic: {topic_key}. Available: {list(TOPICS.keys())}")
    else:
        topic = random.choice(list(TOPICS.values()))

    num_middles = random.randint(0, 2)
    opener = random.choice(topic["openers"])
    middle_parts = random.sample(topic["middles"], min(num_middles, len(topic["middles"])))
    closer = random.choice(topic["closers"])

    parts = [opener] + middle_parts + [closer]
    return ". ".join(parts) + "."


def batch_texts(n, topics_list=None):
    if topics_list is None:
        topics_list = list(TOPICS.keys())
    texts = []
    for _ in range(n):
        topic_key = random.choice(topics_list)
        texts.append(random_text(topic_key))
    return texts


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    for i, text in enumerate(batch_texts(n), 1):
        print(f"\n--- {i} ---")
        print(text)
