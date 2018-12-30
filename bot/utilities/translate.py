from googletrans import Translator, LANGCODES, LANGUAGES
redirs = {"traditional-chinese": "zh-tw", "chinese": "zh-cn", "mandarin": "zh-cn", "detect": "auto",
          "auto": "auto"}
translator = Translator()


def specify(s):
    return LANGCODES.get(redirs.get(s, s), redirs.get(s, s))
