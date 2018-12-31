from random import choice

"""
A bit of an explanation - this oddly-named file contains a list of
out-of-touch ways to say no to drugs, specifically weed, found on a sign
likely produced by an equally out-of-touch DARE campaign. To be clear, I
do not condone dangerous drug use, I just thought these were funny.
"""

sayings = ["Are you kidding me? Grow up!", "I was raised right, I won't light.",
           "Ganja is for goons, no thanks.", "I'd like to keep my job, thanks.",
           "Get a job you hippie wastoid.", "You wish, pot junker! Back off!",
           "No thanks, I'm a good person.", "I'm calling the Coast Guard.",
           "You need to go to jail, hempo.", "No tokes for me. I'm cool.",
           "My dad told me better, no way.", "Leave me be, you blunt blazer!",
           "Grass is crass, also gross! No!", "No, I'm as clean as a whistle.",
           "Uhhh...no thanks loser!", "That's a death \"roach.\" No.",
           "Get away from me, THC addict.", "I'll pass on your pot offer.",
           "Yeah right, I'm way too smart.", "Cannabis is crap, you cretin!",
           "Let me think... No way, never.", "Pish posh, pot is for the birds!",
           "No. You are trash if you toke.", "Nope. THC is not for me.",
           "Back off, bucko. You're bad.", "Step out of my zone, now.",
           "I would rather not, okay?", "Get off my case, weed stoner.",
           "Injecting weed is for dummies.", "Nuh uh, I respect the police.",
           "I will never do one toke.", "Lay off, I listen to the law.",
           "Absolutely not, I love myself.", "NO! Blunts are for bad men.",
           "Get a grip you sativa snorter!", "I'd rather not die. Tokes kill.",
           "Bugger off, you bong addict!", "No, weeds are for whacking.",
           "I will use my taser on you.", "Marijuana is for morons, ok?",
           "What do I look like? A failure?", "Are you serious? Get a life.",
           "Nah, bongs are wrong.", "You're dumb if you do \"dank.\"",
           "No way! Hemp is horrible!", "Stoners are loners. I'm good.",
           "I'd rather not be a cannibal.", "Nope! Spliffs are for wimps!",
           "No, do I look like a hippie?", "Nope, smell ya later!",
           "Are you crazy?", "Be gone.",
           "No, grow up you addict.", "No thank you, I have a job.",
           "Uhh... let me think... No!", "I'll say it slowly for you, nooooooo.",
           "Absolutely not, I'm nice.", "Not now, not ever.",
           "Scamper off you junkie.", "Get away from me, I'm clean.",
           "No, I'm not a pot zombie.", "No thanks, dope heads suck.",
           "No way, Bob Marley is awful.", "No way, put it away.",
           "I obey the law, sorry.", "Ask me again in 10,000 years.",
           "I don't want red eyes.", "I don't think so, you lunatic.",
           "Sorry, I love my family.", "I said no, dude. Bugger off.",
           "I like my peaceful brain.", "No, grass is for mowing.",
           "No, I'm allergic to hate.", "I never smoke. Sorry bub!",
           "I never inject, weed sucks!", "Do you think I'm an idiot?!",
           "Get a life you ganja gremlin.", "Bongs are wrong, bro!",
           "Pot is pathetic, pal!", "Weed is wack, Wesley!",
           "I'm calling the cops on you.", "Absolutely not, weed fiend.",
           "No, I believe in MMYV.", "No, weed makes you mean."]


def sayno():
    return choice(sayings)
