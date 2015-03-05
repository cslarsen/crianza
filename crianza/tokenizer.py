"""
Contains a simple recursive-descent tokenizer.

Copyright (C) 2015 Christian Stigen Larsen
Distributed under the BSD 3-Clause license.
"""

from errors import ParseError

class Tokenizer:
    # TODO: Require the "enum32" package, then to
    #       from enum import Enum, Tokens = Enum(INTEGER=0, FLOAT=1, ...)
    INTEGER = 0
    FLOAT = 1
    BOOLEAN = 2
    STRING = 3
    COLON = 5
    SEMICOLON = 6
    WORD = 7

    def __init__(self, stream):
        self.stream = stream
        self.lineno = 1
        self.column = 0

    def split(self, s):
        """Splits a string into a list of (start_column, substring) tuples."""

        normalized = "".join(map(lambda c: " " if c.isspace() else c, s))

        string = False
        quote = False
        v = []
        for col, char in enumerate(normalized.rstrip(), 1):
            if char == '\\':
                quote = True
            if char == '"' and not quote:
                if string:
                    v[-1] = (v[-1][0], v[-1][1] + '"')
                string = not string

            if char.isspace() and not string:
                v.append((col, ""))
            else:
                if len(v) == 0:
                    v.append((col, char))
                else:
                    col, part = v[-1]
                    v[-1] = (col, part + char)

            if char != '\\' and quote:
                quote = False

        return filter(lambda (t,p): p!="", v)

    def parse_number(self, s):
        """Parses integers in bases 10 and 16 and floats."""
        start = 1 if s[0] in ["-","+"] else 0

        all_digits = lambda x: all(map(lambda c: c.isdigit(), x))
        ishex = lambda c: c.isdigit() or ord(c.lower()) in range(ord("a"), ord("f"))
        all_hex = lambda x: all(map(ishex, x))

        if all_digits(s[start:]):
            try:
                return (Tokenizer.INTEGER, int(s))
            except ValueError:
                raise ParseError("%d:%d: Invalid integer '%s'" % (self.lineno,
                    self.column, s))

        if s[start:].startswith("0x") and all_hex(s[start+2:]):
            try:
                return (Tokenizer.INTEGER, int(s, base=16))
            except ValueError:
                raise ParseError("%d:%d: Invalid hexadecimal integer '%s'" %
                        (self.lineno, self.column, s))

        if any(map(lambda c: c==".", s)) or any(map(lambda c: c=="e", s)):
            try:
                return (Tokenizer.FLOAT, float(s))
            except ValueError:
                raise ParseError("%d:%d: Invalid float '%s'" % (self.lineno,
                    self.column, s))

        raise ParseError("%d:%d: Invalid number '%s'" % (self.lineno,
            self.column, s))

    def parse_string(self, s):
        unescape = {
           "\\'": "'",
           "\\\\": "\\",
           "\\a": "\a",
           "\\b": "\b",
           "\\c": "\c",
           "\\f": "\f",
           "\\n": "\n",
           "\\r": "\r",
           "\\t": "\t",
           "\\v": "\v",
           '\\"': '"',
        }

        if not (s[0]=='"' and s[-1]=='"'):
            raise ParseError("%d:%d Invalid string: %s" % (self.lineno,
                self.column, s))
        else:
            s = s[1:-1]

        out = ""
        quote = ""

        for c, (a, b) in enumerate(zip(s,s[1:])):
            if a == "\\" and quote == "":
                quote += a
            else:
                if quote != "":
                    if (quote+a) not in unescape:
                        raise ParseError("%d:%d Invalid escape sequence: %s" %
                                (self.lineno, self.column+c, quote+a))
                    out += unescape[quote + a]
                else:
                    out += a
                quote = ""

        return (Tokenizer.STRING, out)

    def parse_colon(self, s):
        if s != ":":
            raise ParseError("%d:%d Invalid word prefix: %s" %
                    (self.lineno, self.column, s))
        else:
            return (Tokenizer.COLON, ":")

    def parse_semicolon(self, s):
        if s != ";":
            raise ParseError("%d:%d Invalid word suffix: %s" %
                    (self.lineno, self.column, s))
        else:
            return (Tokenizer.SEMICOLON, ";")

    def tokentype(self, s):
        """Parses string and returns a (Tokenizer.TYPE, value) tuple."""
        a = s[0] if len(s)>0 else ""
        b = s[1] if len(s)>1 else ""

        if a.isdigit() or (a in ["+","-"] and b.isdigit()):
            return self.parse_number(s)
        elif a == '"': return self.parse_string(s)
        elif a == ':': return self.parse_colon(s)
        elif a == ';': return self.parse_semicolon(s)
        else:
            return self.parse_word(s)

    def parse_word(self, s):
        return (Tokenizer.WORD, s)

    def tokenize(self):
        """Breaks a stream up into tokens.

        Yields tuples of the form (line_number, column, Tokenizer.TOKEN).
        """
        def readlines(s):
            while True:
                line = s.readline()
                if line != "":
                    yield line.rstrip()
                else:
                    break

        for self.lineno, line in enumerate(readlines(self.stream), 1):
            for self.column, part in self.split(line):
                if part[0] == "#": # COMMENT
                    break
                yield (self.lineno, self.column, self.tokentype(part))
