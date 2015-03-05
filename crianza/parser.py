from errors import ParseError
from tokenizer import Tokenizer
import StringIO
import string


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

    for (line, col, (token, value)) in Tokenizer(stream).tokenize():
        if token == Tokenizer.STRING:
            value = '"' + value + '"'
        code.append(value)

    return code
