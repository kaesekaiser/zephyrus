word_list = []
with open("words.txt" if __name__ == '__main__' else "utilities/words.txt", "r") as r:
    for l in r.readlines():
        word_list.append(l.replace("\n", ""))
word_dict = {l: tuple(g for g in word_list if len(g) == l) for l in range(1, 23)}
anagrams_dist = [13, 5, 6, 7, 24, 6, 7, 6, 12, 2, 2, 8, 8, 11, 15, 4, 2, 12, 10, 10, 6, 2, 4, 2, 2, 2]
anagrams_dist = [g for sub in [[chr(j + 97)] * anagrams_dist[j] for j in range(26)] for g in sub]


def levenshtein(s1, s2, insert_cost: int = 1, delete_cost: int = 1, sub_cost: int = 1):  # ripped from Wikipedia
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


def next_lev_step(start: str, goal: str) -> str:
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


def full_lev_path(start: str, goal: str) -> list[str]:
    st, go, ret = start + "", goal + "", []
    while st != go:
        ret.append(next_lev_step(st, go))
        st = next_lev_step(st, go)
    ret[-1] = ret[-1].upper() + f" ({len(ret)})"
    return ret


def can_form(word: str, letters: str) -> bool:
    return False not in [word.count(c) <= letters.count(c) for c in word]


def spellable_words(letters: str) -> list[str]:
    return [g for g in word_list if all(c in letters for c in g)]


def subset_words(letters: str) -> list[str]:
    return [g for g in word_list if can_form(g, letters) and len(g) >= 3]


def pangrams(letters: str) -> list[str]:
    return [g for g in spellable_words(letters) if all(c in letters for c in g)]


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


def longest_common_subsequence(s1, s2):
    # taken from a website. i dont know how to code
    m = len(s1)
    n = len(s2)

    ret = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                ret[i][j] = 0
            elif s1[i - 1] == s2[j - 1]:
                ret[i][j] = ret[i - 1][j - 1] + 1
            else:
                ret[i][j] = max(ret[i - 1][j], ret[i][j - 1])

    return ret[m][n]
