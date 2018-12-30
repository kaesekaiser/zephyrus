import math
from inspect import signature
from utils import *
'''
ops = "+-*/^,"
nums = "0123456789."
ans = {}


def add(a, b):
    return a + b


def sub(a, b):
    return a - b


def mul(a, b):
    return a * b


def div(a, b):
    return a / b


def exp(a, b):
    return a ** b


def log(a, b):  # b is base
    return math.log(a, b)


def sin(a):
    return math.sin(a)


def cos(a):
    return math.cos(a)


def arcsin(a):
    return math.asin(a)


def arccos(a):
    return math.acos(a)


def neg(a):
    return -a


def ln(a):
    return math.log(a)


def epower(a):
    return math.e ** a


def sqrt(a):
    return a ** 0.5


def square(a):
    return a * a


funcs = [add, sub, mul, div, sin, cos, arcsin, arccos, exp, log, neg, ln, epower, sqrt, square]
mainFuncs = [func.__name__ for func in [sin, cos, arcsin, arccos, log, ln, sqrt]]
strings = {func.__name__: func for func in funcs}
inverse = {add: sub, mul: div, sin: arcsin, cos: arccos, exp: log, neg: neg, ln: epower, sqrt: square}
inverse = {**inverse, **{v: k for k, v in inverse.items()}}
orderOps = [add, sub, mul, div, exp]
posFuncs = [add, mul, exp]
params = {func: len(signature(func).parameters) for func in funcs}
convertOps = {"+": add, "-": sub, "*": mul, "/": div, "^": exp}


def invert(f, a, b, c):
    if params[f] == 2:
        return inverse[f](c, a) if f in posFuncs else inverse[f](b, c)
    else:
        return inverse[f](c)


def parsed(t):
    if type(t) in [float, int]:
        return True
    if type(t) == str:
        return t in strings
    if type(t) != tuple:
        return False
    if t[0] in strings:
        if len(t) != params[strings[t[0]]] + 1:
            return False
        for i in t:
            if not parsed(i):
                return False
        return True
    return False


def evaluate(t):
    if type(t) != tuple:
        return t
    ret = [t[0]]
    for i in t[1:]:
        ret.append(evaluate(i))
    return strings[ret[0]](ret[1]) if params[strings[ret[0]]] == 1 else strings[ret[0]](ret[1], ret[2])


def splitList(l, it):
    if type(l) == str:
        return [l]
    rt, lis = [], []
    for j in range(len(l)):
        if l[j] == it:
            rt.append(lis)
            lis = []
        else:
            lis.append(l[j])
    rt.append(lis)
    return rt


def joinList(ls, s):
    ret = ls[0]
    if len(ls) > 1:
        for i in ls[1:]:
            ret.append(s)
            ret.append(i)
    return ret


def turn(l):
    if type(l) == str:
        return l
    if len(l) == 1:
        return l[0]
    ret, n = [], 0
    if type(l) == tuple and l[0] in strings:
        ret = [l[0]]
        for i in l[1:]:
            ret.append(turn(i))
        return tuple(ret)
    if len(l) == 3 and l[1] in ops[:-1]:
        return convertOps[l[1]].__name__, turn(l[0]), turn(l[2])
    if len(l) == 3 and l[0] in ["add", "sub", "mul", "div", "exp"]:
        try:
            float(l[1])
            float(l[2])
        except ValueError:
            pass
        else:
            return l
    while n < len(l):
        d = 0
        if type(l[n]) == str and l[n] in strings:
            s = splitList(l[n+1], ",")
            if len(s) != params[strings[l[n]]]:
                raise ValueError(f"invalid number of parameters for {l[n]}")
            else:
                ret.append((l[n], turn(s[0])) if params[strings[l[n]]] == 1 else (l[n], turn(s[0]), turn(s[1])))
                d += 1
        if l[n-1] == "-" and ((type(l[n-2]) == str and l[n-2] in ops) or n == 1):
            if ret[-2] == "-":
                ret[-1] = ("neg", ret[-1])
                del ret[-2]
            else:
                ret[-1] = ("neg", l[n])
        elif not (type(l[n]) == str and l[n] in strings):
            ret.append(l[n])
        n += 1 + d
    true = [turn(i) for i in ret]
    return true


def funk(l):
    if type(l) not in (list, tuple):
        return l
    if len(l) == 1:
        return funk(l[0]) if type(l[0]) == tuple else l[0]
    if len(l) == 2 and type(l[0]) == str and l[0] in strings:
        return l[0], funk(l[1])
    if len(l) == 3 and type(l[0]) == str and l[0] in strings:
        return l[0], funk(l[1]), funk(l[2])
    if False in [c in ops for c in l[1::2]]:
        raise ValueError(f"Something didn't parse correctly: {l}")
    ret, old = [], None
    for char in ops[:-1]:
        if char in l:
            ret = (convertOps[char].__name__, ) + tuple(funk(i) for i in splitList(l, char)[:2])
            if l.count(char) != 1:
                n = 2
                while True:
                    try:
                        nl = [ret, char] + joinList(splitList(l, char)[n:], char)
                    except IndexError:
                        break
                    else:
                        ret = (convertOps[char].__name__,) + tuple(funk(i) for i in splitList(nl, char)[:2])
                        n += 1
            break
    return ret


class Parser:
    def __init__(self, server):
        self.server = server
        self.rawdata = None
        self.data = None

    def feed(self, s):
        self.rawdata = "".join("".join(s.split()).split("\\"))
        self.data = self.funk(self.rawdata)

    def parse(self, s):
        s = str(math.pi).join([g for g in s.split("pi")])
        s = str(math.e).join([g for g in s.split("e")])
        s = ans[self.server].join([g for g in s.split("ans")])
        if s[0] == "-":
            raise ValueError("please don't make the first character a dash")
        level, ret, lis = 0, "", []
        for n in range(len(s)):
            char = s[n]
            ret += char
            if char == ")":
                level -= 1
                if level == 0:
                    ret = ret[1:-1]
            if char == "(":
                level += 1
            if level == 0:
                if char in nums and len(lis) > 0 and lis[-1][-1] in nums:
                    lis[-1] += char
                elif char in lets:
                    mayFunc = s[n:s.find("(", n)]
                    if mayFunc in strings:
                        lis.append(mayFunc)
                    else:
                        try:
                            float(lis[-1])
                        except ValueError:
                            if lis[-1] in ops:
                                lis.append(char)
                        else:
                            lis[-1] += char
                else:
                    lis.append(ret)
                ret = ""
        if level != 0:
            raise ValueError("missing close-paren" if level > 0 else "too many parentheses")
        ret = []
        for i in lis:
            try:
                float(i)
            except ValueError:
                if i in ops or i in strings:
                    ret.append(i)
                else:
                    ret.append(Parser(self.server).parse(i))
            else:
                ret.append(i)
        return turn(ret)

    def funk(self, s):
        def conFloat(l):
            if type(l) == tuple:
                return tuple(conFloat(i) for i in l)
            try:
                return float(l)
            except ValueError:
                return l
        return conFloat(funk(Parser(self.server).parse(s)))


@client.command(pass_context=True)
async def calc(ctx, *args):
    s = "".join(args)
    if s == "help":
        return await emolsay(":1234:", "HELP", hexcol("5177ca"),
                             d="``z!calc`` evaluates a given string of calculations, rounding the result to 15 digits."
                             "\nThe command reads ``+`` for addition, ``-`` for subtraction, ``*`` for multiplication,"
                             " ``/`` for division, and ``^`` for exponentiation.\n"
                             "All terms should be numbers; however, the command interprets the mathematical constants "
                             "``e`` and ``pi`` as their respective values.\n"
                             f"The command also understands the following functions: ``{', '.join(mainFuncs)}``\n"
                             "    *e.g.* ``z!calc 2+2`` -> ``4.0``\n"
                             "    *e.g.* ``z!calc sqrt(3)/2`` -> ``0.866025403784439``\n"
                             "    *e.g.* ``z!calc sin(pi)`` -> ``0.0``", footer="Note: do NOT rely on z!calc to "
                                                                                "evaluate very small numbers.")
    if ctx.message.server.id not in ans:
        ans[ctx.message.server.id] = "0"
    parser = Parser(ctx.message.server.id)
    try:
        parser.feed(s)
    except ValueError as v:
        return await errsay(str(v))
    except IndexError as i:
        return await errsay(str(i))
    except SyntaxError as y:
        return await errsay(str(y))
    try:
        res = evaluate(parser.data)
    except ValueError as v:
        return await errsay(str(v))
    except ZeroDivisionError:
        return await errsay("division by zero")
    except OverflowError:
        return await errsay("overflow error")
    try:
        float(res)
    except ValueError:
        s = "undefined"
    except TypeError:
        if type(res) == complex:
            res = complex(round(res.real, 15), round(res.imag, 15))
            if str(res)[0] == "(":
                s = " + ".join((str(res)[1:-2] + chr(int("1D456", 16))).split("+"))
            else:
                s = str(res)[:-1] + chr(int("1D456", 16))
    else:
        s = str(round(float(res), 15))
        if s == "-0.0":
            s = "0.0"
    ans[ctx.message.server.id] = s
    await emolsay(":1234:", s, hexcol("5177ca"))'''
