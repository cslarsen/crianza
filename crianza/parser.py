from errors import ParseError
import StringIO
import string
import tokenize


def parse(source):
    """Parses source code returns an array of instructions suitable for
    optimization and execution by a Machine.

    Args:
        source: A string or stream containing source code.
    """
    if isinstance(source, str):
        return parse_stream(StringIO.StringIO(source))
    else:
        return parse_stream(source)

def parse_stream(stream):
    """Parse a Forth-like language and return code."""
    code = []
    tokens = tokenize.generate_tokens(stream.readline)

    def strip_whitespace(s):
        r = ""
        for ch in s:
            if not ch in string.whitespace:
                r += ch
            else:
                r += "\\x%x" % ord(ch)
        return r

    while True:
        for token, value, _, _, _ in tokens:
            if token == tokenize.NUMBER:
                try:
                    code.append(int(value))
                except ValueError, e:
                    raise ParseError(e)
            elif token in [tokenize.OP, tokenize.STRING, tokenize.NAME]:
                code.append(value)
            elif token in [tokenize.NEWLINE, tokenize.NL]:
                break
            elif token in [tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT]:
                pass
            elif token == tokenize.ENDMARKER:
                return code
            else:
                raise ParseError("Unknown token %s: '%s'" %
                        (tokenize.tok_name[token], strip_whitespace(value)))
    return code

