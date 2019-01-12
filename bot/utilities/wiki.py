from html.parser import HTMLParser
from pyquery import PyQuery
wikilink = "https://en.wikipedia.org/wiki/{}"
wikiSearch = "https://en.wikipedia.org/w/index.php?search={}&title=Special%3ASearch&fulltext=1&limit=100"


def readurl(url):
    return str(PyQuery(url, {'title': 'CSS', 'printable': 'yes'}, encoding="utf8"))


def remove_paren(s: str):
    while s.count("(") > 0:
        s = s.split("(")[0][:-1] + ")".join("(".join(s.split("(")[1:]).split(")")[1:])
    return s


class Result:
    def __init__(self):
        self.title = ""
        self.desc = ""
        self.link = ""

    def __str__(self):
        return self.title + "\n" + self.desc


class WikiParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titling = False
        self.describing = False
        self.makingBold = False
        self.results = []

    def bold(self, s: str):
        return f"**{s}**" if self.makingBold else s

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get("data-serp-pos"):
            self.results.append(Result())
            self.titling = True
        if dict(attrs).get("class") == "searchresult":
            self.describing = True
        if tag == "span" and dict(attrs).get("class") == "searchmatch":
            self.makingBold = True

    def handle_data(self, data):
        if self.titling:
            self.results[-1].title += self.bold(data)
            self.results[-1].link += data.replace("\\", "")
        elif self.describing:
            self.results[-1].desc += self.bold(data)

    def handle_endtag(self, tag):
        if tag == "span" and self.makingBold:
            self.makingBold = False
        if tag == "div" and self.titling:
            self.titling = False
        if tag == "div" and self.describing:
            self.describing = False
            self.results[-1].desc += " ..."


class ForeignParser(HTMLParser):
    def __init__(self):
        self.recording = False
        self.title = ""
        self.titling = False
        self.lang_title = {}  # titles in languages. {language name: title}
        self.code_lang = {}  # language codes. {code: language name}
        self.lang_code = {}  # inverse of redirects. {language name: code}
        self.lang_link = {}  # links to pages. {language name: link}
        self.lang_form = {}  # links to pages, with close-parens backslashed out for markdown {language name: link}
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "h1" and dict(attrs).get("id") == "firstHeading":
            self.titling = True
        if tag == "li" and "interlanguage-link interwiki-" in dict(attrs).get("class", ""):
            self.recording = True
        if self.recording and "hreflang" in dict(attrs) and "title" in dict(attrs):
            splitter = " – "
            name = dict(attrs)["title"].split(splitter)[1]
            try:
                self.lang_title[name] = dict(attrs)["title"].split(splitter)[0]
                self.lang_link[name] = dict(attrs)["href"]
                self.lang_form[name] = dict(attrs)["href"].replace(')', '\)')
                self.code_lang[dict(attrs)["lang"]] = name
            except ValueError:
                pass

    def handle_data(self, data):
        if self.titling:
            self.title = data
            self.titling = False

    def handle_endtag(self, tag):
        if self.recording:
            self.recording = False
            self.lang_code = {j: g for g, j in self.code_lang.items()}

    def form(self, lang):  # for use in lists of foreign articles
        return f"{lang} - [{self.lang_title[lang]}]({self.lang_form[lang]})"


if __name__ == "__main__":
    html = readurl(wikilink.format("asodijfaiosdjfoasidjfoaisjdf"))
    parser = ForeignParser()
    parser.feed(html)
    for lang, link in parser.lang_link.items():
        print(lang, "-", link)
        print(parser.form(lang))
