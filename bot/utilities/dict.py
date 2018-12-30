from html.parser import HTMLParser
import urllib.request as req
from urllib.error import HTTPError
deflink = "https://www.vocabulary.com/dictionary/{}"


def readurl(url):
    return str(req.urlopen(url).read())


def shave(s):
    split = s.split(" ")
    last = [i for i in range(len(split)) if split[i] == ""][-1]
    return " ".join(split[last + 1:])


class DictParser(HTMLParser):
    def __init__(self):
        self.definition = ""
        self.defining = False
        self.defined = False
        self.defineBreak = False
        self.part = ""
        self.word = ""
        self.wording = False
        self.worded = False
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "h3" and ("class", "definition") in attrs and not self.defined:
            self.defining = True
        if tag == "a" and self.defining:
            self.defineBreak = True
        if tag == "h1" and ("class", "dynamictext") in attrs and not self.worded:
            self.wording = True

    def handle_data(self, data):
        if self.defining and not self.defineBreak:
            self.definition = data
        if self.defineBreak:
            self.part = data.split(" ")[-1]
        if self.wording:
            self.word = data

    def handle_endtag(self, tag):
        if self.defineBreak and tag == "a":
            self.defineBreak = False
        elif self.defining:
            self.defining = False
            self.defined = True
            self.definition = shave(self.definition)
        if self.wording:
            self.wording = False
            self.worded = True
