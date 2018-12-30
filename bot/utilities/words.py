from random import sample, shuffle
wordList = []
with open("words.txt" if __name__ == '__main__' else "utilities/words.txt", "r") as r:
    for l in r.readlines():
        wordList.append(l[:-1])
wordDict = {l: tuple(g for g in wordList if len(g) == l) for l in range(1, 23)}
anagramsDist = [13, 5, 6, 7, 24, 6, 7, 6, 12, 2, 2, 8, 8, 11, 15, 4, 2, 12, 10, 10, 6, 2, 4, 2, 2, 2]
anagramsDist = [g for sub in [[chr(j + 97)] * anagramsDist[j] for j in range(26)] for g in sub]


def levenshtein(s1, s2):  # ripped from Wikipedia
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
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


def scramble(word):
    ret = [c.upper() for c in word]
    shuffle(ret)
    return ret


def canform(word, lets):
    return False not in [word.count(c) <= lets.count(c) for c in word]


def anagrams(word):
    return [i for i in wordList if canform(i, word)]


def letter_count(s: str):
    return {g: s.lower().count(g) for g in "qwertyuiopasdfghjklzxcvbnm"}


def format_letter_count(d: dict, length: int):
    print(length)
    print(d)
    return ", ".join([f"{g[0].upper()}: {round(100 * g[1] / length, 3)}%" for g in
                      sorted(d.items(), key=lambda it: it[1], reverse=True)])


if __name__ == "__main__":
    with open("basque.txt", "r") as r:
        ret = [g.lower() for g in "".join(r.readlines()) if g.lower() in "qwertyuiopasdfghjklzxcvbnm"]
        leg = len(ret)
        dic = letter_count("".join(ret))
        print(format_letter_count(dic, leg))
