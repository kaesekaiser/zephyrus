from html.parser import HTMLParser
import urllib.request as req
from urllib.error import HTTPError
wikilink = "https://en.wikipedia.org/wiki/{}"


def readurl(url):
    return str(req.urlopen(url).read())


def remove_paren(s: str):
    while s.count("(") > 0:
        s = s.split("(")[0][:-1] + ")".join("(".join(s.split("(")[1:]).split(")")[1:])
    return s


def utfasc(s: str):  # converts only \x part of string. use utfs() for a full string that needs conversion
    return str(bytes([int(x, 0) for x in [f"0x{s[g+2:g+4]}" for g in range(0, len(s), 4)]]), "utf-8")


def utfs(s: str, remove=()):  # converts entire string
    if "\\\"" in s:
        s = "\"".join(s.split("\\\""))
    if "\\\'" in s:
        s = "\'".join(s.split("\\\'"))
    for i in remove:
        s = "".join(s.split(i))
    n, ret = 0, ""
    while n < len(s):
        if s[n:n+2] == "\\x":
            x = ""
            while True:
                x += s[n:n+4]
                n += 4
                if n >= len(s) or s[n] != "\\":
                    break
            ret += utfasc(x)
        else:
            ret += s[n]
            n += 1
    return ret


class WikiParser(HTMLParser):
    def __init__(self):
        self.titling = False
        self.title = ""
        self.describing = False
        self.stoppedDesc = False
        self.breakDesc = 0
        self.tableBreak = False
        self.desc = ""
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "h1" and ("id", "firstHeading") in attrs:
            self.titling = True
        if tag == "p" and self.stoppedDesc is False and self.tableBreak is False:
            self.describing = True
        if tag == "table":
            self.tableBreak = True
        if self.describing is True:
            if tag == "sup" or (tag == "span" and ("class", "nowrap") not in attrs and ("class", "IPA") not in attrs
                                and ("class", "IPA nopopups excerpt") not in attrs):
                self.breakDesc += 1
            if tag == "b":
                self.desc += "**"
            if tag == "i":
                self.desc += "*"

    def handle_data(self, data):
        if self.titling is True:
            self.title = utfs(data)
        if self.describing is True and self.breakDesc == 0 and self.tableBreak is False:
            try:
                self.desc += utfs(data)
            except ValueError:
                print("Some character on that page couldn't be handled.")

    def handle_endtag(self, tag):
        if tag == "h1" and self.titling is True:
            self.titling = False
        if tag == "table":
            if self.describing is True:
                self.desc = ""
            self.tableBreak = False
        if self.describing is True:
            if tag == "p":
                if len(self.desc) < 15:
                    self.desc = ""
                else:
                    self.stoppedDesc = True
                    self.describing = False
                    self.desc = remove_paren(utfs(self.desc, ["()", "\\n"]))
                    s = self.desc.split(" ")
                    if len(s) > 75:
                        self.desc = " ".join(s[:75]) + " ..."
            if tag in ["span", "sup"]:
                self.breakDesc -= 1
            if tag == "b":
                self.desc += "**"
            if tag == "i":
                self.desc += "*"
        if self.breakDesc < 0:
            self.breakDesc = 0


class ForeignParser(HTMLParser):
    def __init__(self):
        self.recording = False
        self.title = ""
        self.titling = False
        self.languages = {}  # titles in languages. {language name: title}
        self.redirects = {}  # language codes. {code: language name}
        self.reverse = {}  # inverse of redirects. {language name: code}
        self.links = {}  # links to pages. {language name: link}
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "h1" and ("id", "firstHeading") in attrs:
            self.titling = True
        if tag == "li" and "interlanguage-link interwiki-" in dict(attrs).get("class", ""):
            self.recording = True
        if self.recording and "hreflang" in dict(attrs) and "title" in dict(attrs):
            splitter = " \\xe2\\x80\\x93 "
            name = utfs(dict(attrs)["title"].split(splitter)[1])
            try:
                self.languages[name] = utfs(dict(attrs)["title"].split(splitter)[0])
                self.links[name] = dict(attrs)["href"]
                self.redirects[dict(attrs)["lang"]] = name
            except ValueError:
                pass

    def handle_data(self, data):
        if self.titling:
            self.title = utfs(data)
            self.titling = False

    def handle_endtag(self, tag):
        if self.recording:
            self.recording = False
            self.reverse = dict(zip(self.redirects.values(), self.redirects.keys()))

    def form(self, lang):
        return f"\u001b[34m{lang}\u001b[0m [\u001b[36m{self.reverse[lang]}\u001b[0m]"


if __name__ == "__main__":
    langs = ["it", "scn", "nap", "vec", "sc", "lij", "pms", "lmo"]
    while True:
        fp = ForeignParser()
        cmd = input("z!fw ").split()
        try:
            fp.feed(readurl(wikilink.format(" ".join(cmd[1:]))))
        except HTTPError:
            print("\u001b[31mArticle not found in English.\u001b[0m")
        else:
            if cmd[0] == "all":
                print(" / ".join([f"{fp.form(g)}: {fp.languages[g]}" for g in fp.languages]))
                print("\u001b[33mTotal\u001b[0m:", len(fp.languages))
            elif cmd[0] == "multi":
                modLangs = [fp.redirects.get(g) for g in langs if g in fp.redirects]
                print("\n".join([f"{fp.form(g)}: {fp.languages[g]} -=- {fp.links[g]}" for g in modLangs]))
            elif cmd[0] in fp.redirects:
                lang = fp.redirects[cmd[0]]
                print(f"{fp.form(lang)}: {fp.languages[lang]} -=- {fp.links[lang]}")
            else:
                print("\u001b[31mArticle not found in that language.\u001b[31m")
