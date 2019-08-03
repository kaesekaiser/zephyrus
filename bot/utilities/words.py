wordList = []
with open("words.txt" if __name__ == '__main__' else "utilities/words.txt", "r") as r:
    for l in r.readlines():
        wordList.append(l.replace("\n", ""))
wordDict = {l: tuple(g for g in wordList if len(g) == l) for l in range(1, 23)}
anagramsDist = [13, 5, 6, 7, 24, 6, 7, 6, 12, 2, 2, 8, 8, 11, 15, 4, 2, 12, 10, 10, 6, 2, 4, 2, 2, 2]
anagramsDist = [g for sub in [[chr(j + 97)] * anagramsDist[j] for j in range(26)] for g in sub]


def levenshtein(s1, s2, insert_cost: int=1, delete_cost: int=1, sub_cost: int=1):  # ripped from Wikipedia
    if len(s1) < len(s2):
        return levenshtein(s2, s1, insert_cost, delete_cost, sub_cost)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + insert_cost
            deletions = current_row[j] + delete_cost
            substitutions = previous_row[j] + (c1 != c2) * sub_cost
            current_row.append(min((insertions, deletions, substitutions)))
        previous_row = current_row

    return previous_row[-1]


def levpath(start, goal):
    if start[:len(goal)] == goal:
        return start[:len(goal)] + start[len(goal) + 1:]
    if goal[:len(start)] == start:
        return start + goal[len(start)]
    ignore = min([g for g in range(len(goal)) if
                  g in range(len(start)) and g in range(len(goal)) and start[g] != goal[g]])
    if levenshtein(start[:ignore] + goal[ignore] + start[ignore:], goal) < levenshtein(start, goal):
        return start[:ignore] + goal[ignore] + start[ignore:]
    if levenshtein(start[:ignore] + start[ignore + 1:], goal) < levenshtein(start, goal):
        return start[:ignore] + start[ignore + 1:]
    if levenshtein(start[:ignore] + goal[ignore] + start[ignore + 1:], goal) < levenshtein(start, goal):
        return start[:ignore] + goal[ignore] + start[ignore + 1:]


def fullpath(start, goal):
    st, go, ret = start + "", goal + "", []
    while st != go:
        ret.append(levpath(st, go))
        st = levpath(st, go)
    ret[-1] = ret[-1].upper() + f" ({len(ret)})"
    return ret


def canform(word, lets):
    return False not in [word.count(c) <= lets.count(c) for c in word]


def anagrams(word):
    return [i for i in wordList if canform(i, word) and len(i) >= 3]


def format_letter_count(d: dict, length: int):
    print(length)
    print(d)
    return ", ".join([f"{g[0].upper()}: {round(100 * g[1] / length, 3)}%" for g in
                      sorted(d.items(), key=lambda it: it[1], reverse=True)])


def match_position(iter1: iter, iter2: iter):
    if len(iter2) < len(iter1):
        return match_position(iter2, iter1)

    ret = []
    for i in range(len(iter2) - len(iter1) + 1):
        ret.append(len([n for n in range(len(iter1)) if iter1[n] == iter2[n + i]]))
    return max(ret)


def find_name(s: str, names: list):
    s = s.casefold()
    tests = [
        lambda p: s == p,
        lambda p: s in p and p.index(s) == 0,
        lambda p: s in p,
    ]
    for test in tests:
        if [g for g in names if test(g.casefold())]:
            return sorted([g for g in names if test(g.casefold())])[0]
    else:
        # return sorted(names, key=lambda p: match_position(s, p.casefold()), reverse=True)[0]
        return sorted(names, key=lambda p: levenshtein(s, p.casefold(), 0, 2, 1))


if __name__ == "__main__":
    listOfNames = """Karch#2675
Snake#0000
litten8#2372
rantonels#8376
melop#3400
nana#6497
pebble#9519
Baloung#9887
Breadcrumbs#1207
Brunch#9226
janKala#8374
pecan#1321
ಠಠ 乃モれム工れ丹ㄥ刀 ಠರೃ#2659
creepyeyes#5370
Salgado#1575
Fargie#6711
bbbourq#4561
Nake#0615
Dandvadan#8083
DzêtaRedfang#9616
Lily#6359
Anaïs#3185
jan Kola#1217
barbecube#4760
EineKatze#3828
Kelema#9301
Petitioner#6230
rubberized#8170
xithi#0996
BᶦˢᵐᵘᵗʰBᵒʳᵉᵃᶫᶦˢ#4319
echethesi#8274
salp#2753
Ryώko#5626
eeeeeee#6757
Tyrdrasil#3126
m0ssb3rg 935#9713
Ramu#0148
Nudl#9532
pantumbra#1040
upallday_allen#2196
Luke#8356
Tymewalk#7073
need new name cant decide what#9946
Kitulous#3691
Theplayer78#4172
Taraiph#4438
miles#5030
Acrux#7807
Gufferdk#7786
Maikasavaila#2305
Keyvine#4275
red herring#5078
Sascha Baer#6416
Fia#2143
portland#3305
MADMac#1816
Klaus#0247
felipesnark#7259
Planita#3079
Ceneij#7448
kaesekaiser#2178
merc#3589
Swamp Dragon#7615
Zeuêp#4773
Redark#5163
Kurt Gyrozen#1572
tryddle#9377
Janos13#5234
digigon#6256
Ghalt#7469
kozet#8409"""
    listOfNames = [g[:-5].strip() for g in listOfNames.splitlines()]
    while True:
        putin = input("name test: ").lower()
        print(find_name(putin, listOfNames))
